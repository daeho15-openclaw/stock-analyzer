# 📊 Stock Analyzer - 주식 분석 자동화 프로그램

확장 가능한 모듈형 주식 분석 시스템

## ✨ 주요 기능

- **데이터 수집**: FinanceDataReader를 사용한 주가 데이터 자동 수집
- **캐싱/DB**: SQLite를 사용한 데이터 캐싱 및 히스토리 관리
- **확장 가능한 평가 도구**: 독립적인 모듈로 구성된 기술적 분석 도구
  - 볼린저 밴드 (Bollinger Bands)
  - 일목균형표 (Ichimoku Cloud)
  - 추가 도구 확장 가능
- **리포트 생성**: Markdown 또는 HTML 형식 리포트
- **LLM 기반 해설** (선택): Claude API를 통한 자연어 분석 코멘트
- **설정 기반**: YAML 설정 파일로 간편한 커스터마이징

## 🚦 LLM 기능 관련 안내

이 프로그램은 **LLM 없이도 완벽히 작동**합니다!

- **기본 모드** (LLM 비활성화): 기술 지표 분석 + 템플릿 코멘트 제공
- **LLM 모드** (선택): 위 기능 + Claude API 기반 자연어 해설 추가
  - Anthropic API 키 필요 ([발급 방법](docs/LLM_GUIDE.md))
  - $5 무료 크레딧 제공 (가입 시)
  - 예상 비용: ~$0.003/종목 (claude-3-5-haiku 기준)
- 자세한 내용: [LLM 기능 가이드](docs/LLM_GUIDE.md)

## 📁 프로젝트 구조

```
stock-analyzer/
├── config/                 # 설정 파일
│   ├── stocks.yml         # 주식 목록
│   ├── evaluators.yml     # 평가 도구 설정
│   └── report.yml         # 리포트 설정 (LLM 활성화 여부 포함)
├── data/                   # 데이터베이스
│   └── stock_data.db      # SQLite DB (자동 생성)
├── src/                    # 소스 코드
│   ├── collectors/        # 데이터 수집
│   │   └── fdr_collector.py
│   ├── evaluators/        # 평가 도구
│   │   ├── base.py
│   │   ├── bollinger.py
│   │   └── ichimoku.py
│   ├── reporters/         # 리포트 생성
│   │   ├── markdown.py
│   │   ├── html.py
│   │   └── llm_generator.py  # LLM 해설 생성
│   ├── database.py        # DB 관리
│   └── main.py            # 메인 프로그램
├── reports/                # 생성된 리포트
├── docs/                   # 상세 문서
├── requirements.txt        # 의존성
└── README.md
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
cd stock-analyzer
pip install -r requirements.txt
```

### 2. 설정 파일 편집

#### config/stocks.yml
분석할 주식 종목 목록을 추가/수정합니다.

```yaml
kr_stocks:
  - code: "005930"
    name: "삼성전자"
    market: "KRX"
    note: "반도체/전자"

us_stocks:
  - code: "NVDA"
    name: "NVIDIA"
    market: "NASDAQ"
    note: "반도체/AI"
```

#### config/evaluators.yml
평가 도구를 활성화하고 파라미터를 조정합니다.

```yaml
enabled_evaluators:
  - bollinger
  - ichimoku

bollinger:
  period: 20
  std_multiplier: 2.0
  weight: 1.0
```

#### config/report.yml
리포트 형식과 출력 설정을 지정합니다.

```yaml
format: markdown  # markdown 또는 html
output_dir: "../reports"

# LLM 기반 해설 (선택)
use_llm: false  # true로 변경 시 ANTHROPIC_API_KEY 필요
llm_model: "claude-3-5-haiku-20241022"
```

**LLM 활성화 방법:**
1. [Anthropic Console](https://console.anthropic.com/)에서 API 키 발급
2. API 키 설정 (택 1):
   - **방법 A (권장)**: 환경변수 - `export ANTHROPIC_API_KEY=sk-ant-...`
   - **방법 B**: 설정파일 - `config/report.yml`에 `api_key: "sk-ant-..."` 입력
     - ⚠️ 주의: Git에 API 키가 올라가지 않도록 주의! 환경변수 사용 권장
3. `config/report.yml`에서 `use_llm: true`로 변경
4. 자세한 내용: [LLM 가이드](docs/LLM_GUIDE.md)

### 3. 실행

```bash
cd src

# 한국 주식 분석
python main.py -m kr

# 미국 주식 분석
python main.py -m us

# 전체 시장 분석
python main.py -m all

# 캐시 무시하고 강제 업데이트
python main.py -m kr -f

# 특정 날짜 분석
python main.py -m kr -d 2026-02-10
```

### 4. 리포트 확인

생성된 리포트는 `reports/` 디렉토리에 저장됩니다.

- Markdown: `reports/kr_2026-02-10.md`
- HTML: `reports/kr_2026-02-10.html`

## 📊 분석 결과 예시

### 기본 모드 (LLM 비활성화)
```markdown
| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |
|--------|-----------|-----------|------|------|
| 삼성전자 | 🔴 | 🟢 | 👌 | 💰 165,800원 | 과매수 80%, 매도 고려 | 골든크로스, 강세 |
```

### LLM 모드 (활성화 시)
위 기본 정보 + 추가 해설:
```
💬 주가가 볼린저 밴드 상단에 위치하여 단기 과열 가능성이 있습니다. 
   일목균형표는 긍정적이나 매도 타이밍 고려가 필요합니다...
```

## 🔧 커스터마이징

### 새로운 평가 도구 추가하기

1. `src/evaluators/` 에 새 파일 생성 (예: `rsi.py`)

```python
from .base import BaseEvaluator
from typing import List, Dict, Tuple

class RSIEvaluator(BaseEvaluator):
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.period = self.config.get('period', 14)
    
    def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
        # RSI 계산 및 평가 로직
        score = 3.0
        emoji = '🟡'
        comment = 'RSI 분석 결과'
        return score, emoji, comment
    
    def get_details(self, data: List[Dict]) -> Dict:
        # 상세 정보 반환
        return {'rsi': 50.0}
```

2. `config/evaluators.yml`에 설정 추가

```yaml
enabled_evaluators:
  - bollinger
  - ichimoku
  - rsi

rsi:
  period: 14
  weight: 1.0
```

3. `src/evaluators/__init__.py`에 등록

```python
from .rsi import RSIEvaluator
__all__ = ['BaseEvaluator', 'BollingerEvaluator', 'IchimokuEvaluator', 'RSIEvaluator']
```

4. `src/main.py`의 `init_evaluators()` 메서드에 추가

```python
if 'rsi' in enabled:
    config = self.evaluators_config.get('rsi', {})
    evaluators.append(RSIEvaluator(config))
```

### 새로운 리포터 추가하기

1. `src/reporters/` 에 새 파일 생성 (예: `pdf.py`)
2. `generate()` 와 `save()` 메서드 구현
3. `src/main.py`에서 리포터 선택 로직 수정

## 📊 평가 기준

### 볼린저 밴드
- 🟢 4점: 하단 근처 (0~25%), 강한 매수
- 🟡 3점: 중립 (25~50%), 약한 매수
- 🟠 2점: 과열 (50~80%), 약한 매도
- 🔴 1점: 과매수 (80~100%), 강한 매도

### 일목균형표
- 🟢 4점: 골든크로스 + 구름 위, 강한 매수
- 🟡 3점: 중립, 추세 전환 중
- 🟠 2점: 하락 조짐
- 🔴 1점: 데드크로스 + 구름 아래, 강한 매도

### 종합 평가
- 🔥🔥: 3.5~4.0점 (매우 좋음)
- 🔥: 3.25~3.5점 (좋음)
- 👍: 2.75~3.25점 (긍정적)
- 👌: 2.5~2.75점 (중립)
- 🧐: 2.0~2.5점 (주의)
- 👎: 1.5~2.0점 (부정적)
- 💣: 1.0~1.5점 (매우 나쁨)

## 🗄️ 데이터베이스 스키마

### stock_prices
주가 데이터 저장

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | 기본 키 |
| code | TEXT | 종목 코드 |
| market | TEXT | 시장 |
| date | TEXT | 날짜 |
| open | REAL | 시가 |
| high | REAL | 고가 |
| low | REAL | 저가 |
| close | REAL | 종가 |
| volume | INTEGER | 거래량 |
| created_at | TEXT | 생성 시간 |

### evaluations
평가 결과 저장

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | 기본 키 |
| code | TEXT | 종목 코드 |
| date | TEXT | 날짜 |
| evaluator | TEXT | 평가 도구 |
| score | REAL | 점수 |
| details | TEXT | 상세 정보 (JSON) |
| created_at | TEXT | 생성 시간 |

### reports
생성된 리포트 저장

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | 기본 키 |
| market | TEXT | 시장 |
| date | TEXT | 날짜 |
| content | TEXT | 리포트 내용 |
| format | TEXT | 형식 (markdown/html) |
| created_at | TEXT | 생성 시간 |

## 📖 상세 문서

- [빠른 시작 가이드](QUICKSTART.md)
- [프로젝트 개요](docs/OVERVIEW.md)
- [설치 요구사항](docs/REQUIREMENTS.md)
- [LLM 기능 가이드](docs/LLM_GUIDE.md) ⭐ **API 키 발급 방법 포함**
- 모듈별 문서:
  - [데이터 수집](docs/MODULE_COLLECTORS.md)
  - [평가 도구](docs/MODULE_EVALUATORS.md)
  - [리포터](docs/MODULE_REPORTERS.md)
  - [데이터베이스](docs/MODULE_DATABASE.md)

## 💡 사용 팁

- **일일 분석 자동화**: 크론잡으로 매일 아침 실행
- **HTML 리포트**: 모바일에서 보기 편함
- **비용 절감**: LLM 없이 사용하면 완전 무료
- **캐싱 활용**: 같은 날 재실행 시 빠른 속도

## ⚠️ 주의사항

- 이 프로그램은 기술적 분석 참고 자료를 제공하는 도구입니다.
- 실제 투자 결정은 본인의 판단과 책임하에 진행하세요.
- FinanceDataReader API 사용 시 과도한 요청을 피하세요. (내장된 딜레이: 0.5초)

## 📝 라이선스

MIT License

## 🤝 기여

이슈 제보 및 풀 리퀘스트 환영합니다!

---

**Happy Trading! 📈**
