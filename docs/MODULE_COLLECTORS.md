# 데이터 수집 모듈 (Collectors)

## 개요

주가 데이터를 외부 소스에서 수집하는 모듈입니다. 다양한 데이터 소스를 지원하며, 각 소스는 독립적인 Collector 클래스로 구현됩니다.

## 위치
```
src/collectors/
├── __init__.py
├── fdr_collector.py      # FinanceDataReader 수집기
└── json_collector.py     # JSON 파일 수집기
```

## 아키텍처

### 데이터 흐름
```
외부 데이터 소스
(API, File, DB 등)
        │
        ▼
    Collector
  (데이터 수집)
        │
        ▼
  표준화된 형식
  List[Dict]
        │
        ▼
   Database.py
  (DB 저장)
```

## 공통 인터페이스

모든 Collector는 다음 메서드를 구현해야 합니다:

### collect()
```python
def collect(self, code: str, market: str = "KRX", 
            start_date: Optional[str] = None,
            end_date: Optional[str] = None) -> List[Dict]
```

**파라미터**:
- `code`: 종목 코드 (예: "005930", "NVDA")
- `market`: 시장 (KRX, NASDAQ, NYSE 등)
- `start_date`: 시작 날짜 (YYYY-MM-DD)
- `end_date`: 종료 날짜 (YYYY-MM-DD)

**반환값**:
```python
[
    {
        'date': 'YYYY-MM-DD',
        'open': float,
        'high': float,
        'low': float,
        'close': float,
        'volume': int
    },
    ...
]
```
- **최신 데이터가 앞에 오도록 정렬** (최신 → 과거)

### collect_multiple()
```python
def collect_multiple(self, stocks: List[Dict]) -> Dict[str, List[Dict]]
```

**파라미터**:
```python
stocks = [
    {'code': '005930', 'market': 'KRX', 'name': '삼성전자'},
    ...
]
```

**반환값**:
```python
{
    '005930': [data, ...],
    '042660': [data, ...],
    ...
}
```

## FDRCollector (FinanceDataReader)

### 파일
`src/collectors/fdr_collector.py`

### 목적
FinanceDataReader 라이브러리를 사용하여 실시간 주가 데이터 수집

### 초기화
```python
collector = FDRCollector(days=60, delay=0.5)
```

**파라미터**:
- `days`: 수집할 과거 데이터 일수 (기본: 60)
- `delay`: API 호출 간 대기 시간 (초, 기본: 0.5)

### 동작 방식

1. **날짜 계산**
   - `end_date`: 기본값 오늘
   - `start_date`: end_date - days

2. **데이터 수집**
   ```python
   df = fdr.DataReader(code, start_date, end_date)
   ```

3. **DataFrame → List[Dict] 변환**
   - 컬럼명 표준화 (Open → open, Close → close 등)
   - 날짜 형식 통일 (YYYY-MM-DD)

4. **정렬**
   - 최신 데이터가 앞에 오도록 `reverse()`

5. **Rate Limiting**
   - 각 종목 수집 후 `time.sleep(delay)` 적용

### 예시
```python
from collectors import FDRCollector

collector = FDRCollector(days=60)

# 삼성전자 데이터 수집
data = collector.collect("005930", "KRX")
print(f"수집 건수: {len(data)}")
print(f"최신 데이터: {data[0]}")

# 여러 종목 일괄 수집
stocks = [
    {'code': '005930', 'market': 'KRX'},
    {'code': 'NVDA', 'market': 'NASDAQ'}
]
results = collector.collect_multiple(stocks)
```

### 장점
- 실시간 최신 데이터 수집
- 여러 시장 지원 (한국, 미국, 일본 등)
- 자동 데이터 정제

### 단점
- 인터넷 연결 필요
- API rate limit 존재
- 외부 서비스 의존

### 에러 처리
```python
try:
    df = fdr.DataReader(code, start_date, end_date)
    if df is None or df.empty:
        print(f"⚠️  [{code}] 데이터 없음")
        return []
except Exception as e:
    print(f"❌ [{code}] 수집 실패: {e}")
    return []
```

## JSONCollector (JSON 파일)

### 파일
`src/collectors/json_collector.py`

### 목적
미리 저장된 JSON 파일에서 주가 데이터 로드 (Fallback 또는 오프라인 테스트용)

### 초기화
```python
collector = JSONCollector(data_dir="../../stock-data")
```

**파라미터**:
- `data_dir`: JSON 파일이 있는 디렉토리 경로

### 파일 구조
```
stock-data/
├── kr/
│   ├── 005930.json    # 삼성전자
│   └── 042660.json    # 한화오션
└── us/
    ├── NVDA.json      # NVIDIA
    └── VLO.json       # Valero Energy
```

### JSON 형식
```json
{
  "code": "005930",
  "name": "삼성전자",
  "lastUpdate": "2026-02-10T09:52:00",
  "data": [
    {
      "date": "2026.02.10",
      "open": 167400,
      "high": 168100,
      "low": 165500,
      "close": 165800,
      "volume": 19157551
    },
    ...
  ]
}
```

### 동작 방식

1. **파일 경로 결정**
   ```python
   if market == "KRX":
       filepath = data_dir / "kr" / f"{code}.json"
   else:
       filepath = data_dir / "us" / f"{code}.json"
   ```

2. **JSON 로드**
   ```python
   with open(filepath, 'r', encoding='utf-8') as f:
       json_data = json.load(f)
   data = json_data.get('data', [])
   ```

3. **데이터 반환**
   - 이미 최신순으로 정렬된 상태로 저장되어 있음

### 예시
```python
from collectors.json_collector import JSONCollector

collector = JSONCollector("../stock-data")

# 삼성전자 데이터 로드
data = collector.collect("005930", "KRX")
print(f"로드 건수: {len(data)}")
```

### 장점
- 오프라인 동작 가능
- 빠른 로드 속도
- API 의존성 없음

### 단점
- 수동 업데이트 필요
- 최신 데이터 부족 가능성

### 에러 처리
```python
if not filepath.exists():
    print(f"⚠️  [{code}] 파일 없음: {filepath}")
    return []
```

## 메인 프로그램 연동

### Collector 선택 로직
```python
# main.py
if HAS_FDR:
    self.collector = FDRCollector(days=60, delay=0.5)
    print("📥 FinanceDataReader 사용")
else:
    self.collector = JSONCollector()
    print("📦 JSON 파일에서 데이터 로드")
```

### 캐싱과 연동
```python
def collect_and_cache_data(self, stock: Dict, force_update: bool = False):
    code = stock['code']
    
    # 캐시 확인
    if not force_update:
        latest_date = self.db.get_latest_date(code)
        if latest_date >= today:
            print(f"📦 [{code}] 캐시에서 로드")
            return self.db.get_price_data(code, limit=60)
    
    # 데이터 수집
    data = self.collector.collect(code, market)
    
    # DB 저장
    if data:
        self.db.save_price_data(code, market, data)
    
    return data
```

## 새 Collector 추가 방법

### 1. 새 파일 생성
```python
# src/collectors/my_collector.py

from typing import List, Dict

class MyCollector:
    def __init__(self, **kwargs):
        pass
    
    def collect(self, code: str, market: str = "KRX", 
                start_date: str = None, end_date: str = None) -> List[Dict]:
        # 데이터 수집 로직 구현
        data = []
        # ...
        return data
    
    def collect_multiple(self, stocks: List[Dict]) -> Dict[str, List[Dict]]:
        results = {}
        for stock in stocks:
            code = stock['code']
            data = self.collect(code, stock.get('market', 'KRX'))
            if data:
                results[code] = data
        return results
```

### 2. __init__.py에 등록
```python
# src/collectors/__init__.py

try:
    from .my_collector import MyCollector
    __all__.append('MyCollector')
except ImportError:
    pass
```

### 3. main.py에서 사용
```python
# src/main.py

from collectors import MyCollector

self.collector = MyCollector()
```

## 데이터 검증

### 필수 필드 체크
```python
required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
for field in required_fields:
    if field not in row:
        raise ValueError(f"필수 필드 누락: {field}")
```

### 데이터 타입 변환
```python
data.append({
    'date': date.strftime('%Y-%m-%d'),
    'open': float(row.get('Open', 0)),
    'high': float(row.get('High', 0)),
    'low': float(row.get('Low', 0)),
    'close': float(row.get('Close', 0)),
    'volume': int(row.get('Volume', 0))
})
```

### 정렬 확인
```python
# 최신 데이터가 앞에 있어야 함
assert data[0]['date'] >= data[-1]['date'], "데이터가 최신순으로 정렬되지 않음"
```

## 성능 최적화

### Rate Limiting
```python
import time

for stock in stocks:
    data = self.collect(stock['code'])
    time.sleep(self.delay)  # API 부하 방지
```

### 병렬 처리 (추후)
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(self.collect, stock['code']) for stock in stocks]
    results = [future.result() for future in futures]
```

## 테스트

### 단위 테스트
```python
def test_collect():
    collector = FDRCollector(days=10)
    data = collector.collect("005930", "KRX")
    
    assert len(data) > 0, "데이터 수집 실패"
    assert 'date' in data[0], "date 필드 없음"
    assert data[0]['date'] >= data[-1]['date'], "정렬 오류"
```

### 통합 테스트
```python
def test_with_database():
    collector = FDRCollector()
    db = StockDatabase("test.db")
    
    data = collector.collect("005930", "KRX")
    db.save_price_data("005930", "KRX", data)
    
    loaded = db.get_price_data("005930", limit=10)
    assert len(loaded) == min(len(data), 10)
```

---

**문서 버전**: 1.0  
**최종 수정**: 2026-02-10
