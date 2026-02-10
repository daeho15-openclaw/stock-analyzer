# 평가 도구 모듈 (Evaluators)

## 개요

주가 데이터를 분석하여 매수/매도 신호를 평가하는 모듈입니다. 각 평가 도구는 독립적인 클래스로 구현되며, 확장이 용이한 구조를 가집니다.

## 위치
```
src/evaluators/
├── __init__.py
├── base.py           # 베이스 클래스
├── bollinger.py      # 볼린저 밴드
└── ichimoku.py       # 일목균형표
```

## 아키텍처

### 데이터 흐름
```
주가 데이터
List[Dict]
    │
    ▼
 Evaluator
(기술적 분석)
    │
    ├─> Score (1.0~4.0)
    ├─> Emoji (🟢🟡🟠🔴)
    └─> Comment (분석 코멘트)
    │
    ▼
 Database
(평가 결과 저장)
```

## BaseEvaluator (추상 클래스)

### 파일
`src/evaluators/base.py`

### 목적
모든 평가 도구가 상속받아야 하는 추상 베이스 클래스. 공통 인터페이스 정의.

### 추상 메서드

#### evaluate()
```python
@abstractmethod
def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
    """
    주가 데이터를 평가하여 점수와 시그널 반환
    
    Args:
        data: 주가 데이터 리스트 (최신순)
              [{'date': '2026-02-10', 'open': ..., 'high': ..., 
                'low': ..., 'close': ..., 'volume': ...}, ...]
    
    Returns:
        (score, emoji, comment)
        - score: 1.0~4.0 점수
        - emoji: 시그널 emoji (🟢, 🟡, 🟠, 🔴)
        - comment: 분석 코멘트 (간략)
    """
    pass
```

#### get_details()
```python
@abstractmethod
def get_details(self, data: List[Dict]) -> Dict:
    """
    상세 분석 정보 반환 (DB 저장용)
    
    Args:
        data: 주가 데이터 리스트
    
    Returns:
        상세 정보 딕셔너리
        {
            'score': float,
            'emoji': str,
            'comment': str,
            ... (평가 도구별 추가 정보)
        }
    """
    pass
```

### 공통 메서드

#### get_weight()
```python
def get_weight(self) -> float:
    """
    종합 평가 시 가중치 반환
    
    Returns:
        가중치 (기본값 1.0)
    """
    return self.config.get('weight', 1.0)
```

#### get_name()
```python
def get_name(self) -> str:
    """평가 도구 이름 반환"""
    return self.name  # 클래스명에서 자동 추출
```

#### get_overall_emoji() (정적 메서드)
```python
@staticmethod
def get_overall_emoji(avg_score: float) -> str:
    """
    평균 점수에 따른 종합 평가 emoji 반환
    
    Args:
        avg_score: 평균 점수
    
    Returns:
        종합 평가 emoji
    """
    if avg_score >= 3.5:
        return '🔥🔥'
    elif avg_score >= 3.25:
        return '🔥'
    elif avg_score >= 2.75:
        return '👍'
    elif avg_score >= 2.5:
        return '👌'
    elif avg_score >= 2.0:
        return '🧐'
    elif avg_score >= 1.5:
        return '👎'
    else:
        return '💣'
```

### 초기화
```python
def __init__(self, config: Dict = None):
    """
    Args:
        config: 평가 도구 설정 딕셔너리
    """
    self.config = config or {}
    self.name = self.__class__.__name__.replace('Evaluator', '').lower()
```

## BollingerEvaluator (볼린저 밴드)

### 파일
`src/evaluators/bollinger.py`

### 목적
볼린저 밴드를 계산하여 과매수/과매도 구간 판단

### 초기화
```python
evaluator = BollingerEvaluator({
    'period': 20,           # 이동평균 기간
    'std_multiplier': 2.0,  # 표준편차 배수
    'weight': 1.0           # 가중치
})
```

### 계산 로직

#### 볼린저 밴드 계산
```python
def calculate_bollinger(self, closes: List[float]) -> Dict:
    recent = closes[:self.period]  # 최근 N일
    
    # 중심선 (SMA)
    sma = sum(recent) / self.period
    
    # 표준편차
    std = statistics.stdev(recent)
    
    # 상단/하단 밴드
    upper = sma + (std * self.std_multiplier)
    lower = sma - (std * self.std_multiplier)
    
    # 현재가
    current = closes[0]
    
    # 밴드 내 위치 (0~100%)
    position = ((current - lower) / (upper - lower)) * 100
    
    return {
        'sma': sma,
        'upper': upper,
        'lower': lower,
        'current': current,
        'position': position
    }
```

### 평가 기준

| 밴드 내 위치 | 점수 | Emoji | 코멘트 | 해석 |
|-------------|------|-------|--------|------|
| 0~25% | 4.0 | 🟢 | 하단 근처, 반등 기대 | 과매도, 강한 매수 |
| 25~50% | 3.0 | 🟡 | 중립, 관망 | 중립, 약한 매수 |
| 50~80% | 2.0 | 🟠 | 과열, 조정 주의 | 과열, 약한 매도 |
| 80~100% | 1.0 | 🔴 | 과매수, 매도 고려 | 과매수, 강한 매도 |

### 평가 로직
```python
def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
    if len(data) < self.period:
        return 2.0, '🟡', '데이터 부족'
    
    closes = [d['close'] for d in data]
    bb = self.calculate_bollinger(closes)
    
    pos = bb['position']
    
    if pos <= 25:
        return 4.0, '🟢', f"하단 근처 {pos:.0f}%, 반등 기대"
    elif pos <= 50:
        return 3.0, '🟡', f"중립 {pos:.0f}%, 관망"
    elif pos <= 80:
        return 2.0, '🟠', f"과열 {pos:.0f}%, 조정 주의"
    else:
        return 1.0, '🔴', f"과매수 {pos:.0f}%, 매도 고려"
```

### 상세 정보
```python
def get_details(self, data: List[Dict]) -> Dict:
    closes = [d['close'] for d in data]
    bb = self.calculate_bollinger(closes)
    score, emoji, comment = self.evaluate(data)
    
    return {
        'sma': bb['sma'],
        'upper': bb['upper'],
        'lower': bb['lower'],
        'current': bb['current'],
        'position': bb['position'],
        'score': score,
        'emoji': emoji,
        'comment': comment
    }
```

### 예시
```python
from evaluators import BollingerEvaluator

data = [
    {'date': '2026-02-10', 'close': 165800},
    {'date': '2026-02-07', 'close': 167400},
    # ... 60일치 데이터
]

evaluator = BollingerEvaluator({'period': 20, 'std_multiplier': 2.0})
score, emoji, comment = evaluator.evaluate(data)

print(f"점수: {score}, Emoji: {emoji}, 코멘트: {comment}")
# 출력: 점수: 1.0, Emoji: 🔴, 코멘트: 과매수 80%, 매도 고려
```

## IchimokuEvaluator (일목균형표)

### 파일
`src/evaluators/ichimoku.py`

### 목적
일목균형표 지표를 계산하여 추세 및 지지/저항 분석

### 초기화
```python
evaluator = IchimokuEvaluator({
    'conversion_period': 9,   # 전환선 (단기)
    'base_period': 26,        # 기준선 (중기)
    'span_b_period': 52,      # 선행스팬 B (장기)
    'weight': 1.0
})
```

### 계산 로직

#### 일목균형표 계산
```python
def calculate_ichimoku(self, highs, lows, closes) -> Dict:
    # 전환선 (9일)
    conv_high = max(highs[:9])
    conv_low = min(lows[:9])
    conversion = (conv_high + conv_low) / 2
    
    # 기준선 (26일)
    base_high = max(highs[:26])
    base_low = min(lows[:26])
    baseline = (base_high + base_low) / 2
    
    # 선행스팬 A
    span_a = (conversion + baseline) / 2
    
    # 선행스팬 B (52일)
    span_b_high = max(highs[:52])
    span_b_low = min(lows[:52])
    span_b = (span_b_high + span_b_low) / 2
    
    # 구름대
    cloud_top = max(span_a, span_b)
    cloud_bottom = min(span_a, span_b)
    
    return {
        'conversion': conversion,
        'baseline': baseline,
        'span_a': span_a,
        'span_b': span_b,
        'cloud_top': cloud_top,
        'cloud_bottom': cloud_bottom,
        'current': closes[0]
    }
```

### 평가 기준

| 조건 | 점수 | Emoji | 코멘트 | 해석 |
|-----|------|-------|--------|------|
| 전환선 > 기준선 AND 현재가 > 구름대 | 4.0 | 🟢 | 골든크로스, 강세 | 강한 매수 |
| 전환선 > 기준선 OR 현재가 > 구름대 | 3.0 | 🟡 | 중립, 추세 전환 중 | 약한 매수 |
| 전환선 < 기준선 OR 현재가 < 구름대 | 2.0 | 🟠 | 하락 조짐 | 약한 매도 |
| 전환선 < 기준선 AND 현재가 < 구름대 | 1.0 | 🔴 | 데드크로스, 약세 | 강한 매도 |

### 평가 로직
```python
def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
    if len(data) < self.base_period:
        return 2.0, '🟡', '데이터 부족'
    
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    closes = [d['close'] for d in data]
    
    ich = self.calculate_ichimoku(highs, lows, closes)
    
    conv_above = ich['conversion'] > ich['baseline']
    price_above = ich['current'] > ich['cloud_top']
    price_below = ich['current'] < ich['cloud_bottom']
    
    if conv_above and price_above:
        return 4.0, '🟢', "골든크로스, 강세"
    elif conv_above or price_above:
        return 3.0, '🟡', "중립, 추세 전환 중"
    elif not conv_above and price_below:
        return 1.0, '🔴', "데드크로스, 약세"
    else:
        return 2.0, '🟠', "하락 조짐"
```

### 상세 정보
```python
def get_details(self, data: List[Dict]) -> Dict:
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    closes = [d['close'] for d in data]
    
    ich = self.calculate_ichimoku(highs, lows, closes)
    score, emoji, comment = self.evaluate(data)
    
    return {
        'conversion': ich['conversion'],
        'baseline': ich['baseline'],
        'span_a': ich['span_a'],
        'span_b': ich['span_b'],
        'cloud_top': ich['cloud_top'],
        'cloud_bottom': ich['cloud_bottom'],
        'current': ich['current'],
        'score': score,
        'emoji': emoji,
        'comment': comment
    }
```

## 종합 평가

### 평균 점수 계산
```python
# main.py에서
scores = []
for evaluator in self.evaluators:
    score, emoji, comment = evaluator.evaluate(data)
    weight = evaluator.get_weight()
    scores.append(score * weight)

# 가중 평균
overall_score = sum(scores) / sum([e.get_weight() for e in self.evaluators])
overall_emoji = BaseEvaluator.get_overall_emoji(overall_score)
```

### 종합 Emoji 기준
- 🔥🔥: 3.5~4.0점 (매우 좋음, 강한 매수)
- 🔥: 3.25~3.5점 (좋음, 매수)
- 👍: 2.75~3.25점 (긍정적, 약한 매수)
- 👌: 2.5~2.75점 (중립)
- 🧐: 2.0~2.5점 (주의, 관망)
- 👎: 1.5~2.0점 (부정적, 약한 매도)
- 💣: 1.0~1.5점 (매우 나쁨, 강한 매도)

## 새 Evaluator 추가 방법

### 1. 새 파일 생성
```python
# src/evaluators/rsi.py

from typing import List, Dict, Tuple
from .base import BaseEvaluator

class RSIEvaluator(BaseEvaluator):
    """RSI (Relative Strength Index) 평가 도구"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.period = self.config.get('period', 14)
    
    def calculate_rsi(self, closes: List[float]) -> float:
        """RSI 계산"""
        changes = [closes[i] - closes[i+1] for i in range(len(closes)-1)]
        gains = [c if c > 0 else 0 for c in changes[:self.period]]
        losses = [-c if c < 0 else 0 for c in changes[:self.period]]
        
        avg_gain = sum(gains) / self.period
        avg_loss = sum(losses) / self.period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
        """
        RSI 평가 기준:
        - 0~30: 과매도 (4점, 🟢)
        - 30~50: 약한 매도 (3점, 🟡)
        - 50~70: 약한 매수 (2점, 🟠)
        - 70~100: 과매수 (1점, 🔴)
        """
        if len(data) < self.period + 1:
            return 2.0, '🟡', '데이터 부족'
        
        closes = [d['close'] for d in data]
        rsi = self.calculate_rsi(closes)
        
        if rsi <= 30:
            return 4.0, '🟢', f"RSI {rsi:.0f}, 과매도"
        elif rsi <= 50:
            return 3.0, '🟡', f"RSI {rsi:.0f}, 중립"
        elif rsi <= 70:
            return 2.0, '🟠', f"RSI {rsi:.0f}, 주의"
        else:
            return 1.0, '🔴', f"RSI {rsi:.0f}, 과매수"
    
    def get_details(self, data: List[Dict]) -> Dict:
        """상세 정보"""
        closes = [d['close'] for d in data]
        rsi = self.calculate_rsi(closes)
        score, emoji, comment = self.evaluate(data)
        
        return {
            'rsi': rsi,
            'score': score,
            'emoji': emoji,
            'comment': comment
        }
```

### 2. __init__.py에 등록
```python
# src/evaluators/__init__.py

from .base import BaseEvaluator
from .bollinger import BollingerEvaluator
from .ichimoku import IchimokuEvaluator
from .rsi import RSIEvaluator

__all__ = ['BaseEvaluator', 'BollingerEvaluator', 'IchimokuEvaluator', 'RSIEvaluator']
```

### 3. 설정 파일에 추가
```yaml
# config/evaluators.yml

enabled_evaluators:
  - bollinger
  - ichimoku
  - rsi

rsi:
  period: 14
  weight: 1.0
```

### 4. main.py에서 초기화
```python
# src/main.py

def init_evaluators(self):
    evaluators = []
    enabled = self.evaluators_config.get('enabled_evaluators', [])
    
    if 'rsi' in enabled:
        config = self.evaluators_config.get('rsi', {})
        evaluators.append(RSIEvaluator(config))
    
    return evaluators
```

## 테스트

### 단위 테스트
```python
def test_bollinger_evaluate():
    data = [{'close': 100 + i} for i in range(30)]
    evaluator = BollingerEvaluator({'period': 20})
    
    score, emoji, comment = evaluator.evaluate(data)
    assert 1.0 <= score <= 4.0
    assert emoji in ['🟢', '🟡', '🟠', '🔴']
```

### 통합 테스트
```python
def test_multiple_evaluators():
    data = load_test_data("005930")
    
    bb = BollingerEvaluator({'period': 20})
    ich = IchimokuEvaluator({'conversion_period': 9})
    
    bb_score, _, _ = bb.evaluate(data)
    ich_score, _, _ = ich.evaluate(data)
    
    avg_score = (bb_score + ich_score) / 2
    overall_emoji = BaseEvaluator.get_overall_emoji(avg_score)
    
    print(f"종합 평가: {avg_score:.2f} {overall_emoji}")
```

---

**문서 버전**: 1.0  
**최종 수정**: 2026-02-10
