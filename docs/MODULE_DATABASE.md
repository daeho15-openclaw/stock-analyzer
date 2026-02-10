# 데이터베이스 모듈 (Database)

## 개요

SQLite를 사용하여 주가 데이터, 평가 결과, 리포트 히스토리를 저장하고 관리하는 모듈입니다. 캐싱을 통해 중복 수집을 방지하고 히스토리 관리를 지원합니다.

## 위치
```
src/database.py
data/stock_data.db  # 자동 생성됨
```

## 아키텍처

### 데이터 흐름
```
외부 데이터
    │
    ▼
Collector
    │
    ▼
Database.save_price_data()
    │
    ▼
SQLite DB
    │
    ▼
Database.get_price_data()
    │
    ▼
Evaluator
    │
    ▼
Database.save_evaluation()
    │
    ▼
SQLite DB
```

## StockDatabase 클래스

### 파일
`src/database.py`

### 초기화
```python
from database import StockDatabase

db = StockDatabase("data/stock_data.db")
```

**파라미터**:
- `db_path`: 데이터베이스 파일 경로 (기본: "data/stock_data.db")

**동작**:
- 파일이 없으면 자동 생성
- 테이블 및 인덱스 자동 생성

### Context Manager 지원
```python
with StockDatabase("data/stock_data.db") as db:
    data = db.get_price_data("005930")
    # 자동으로 close() 호출됨
```

## 데이터베이스 스키마

### 1. stock_prices (주가 데이터)

```sql
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    market TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, date)
)

CREATE INDEX idx_stock_code_date ON stock_prices(code, date)
```

**컬럼 설명**:
- `id`: 기본 키 (자동 증가)
- `code`: 종목 코드 (예: "005930", "NVDA")
- `market`: 시장 (KRX, NASDAQ, NYSE 등)
- `date`: 날짜 (YYYY-MM-DD)
- `open`: 시가
- `high`: 고가
- `low`: 저가
- `close`: 종가
- `volume`: 거래량
- `created_at`: 데이터 생성 시간

**제약조건**:
- `UNIQUE(code, date)`: 같은 종목, 같은 날짜 중복 방지

### 2. evaluations (평가 결과)

```sql
CREATE TABLE evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    date TEXT NOT NULL,
    evaluator TEXT NOT NULL,
    score REAL NOT NULL,
    details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, date, evaluator)
)

CREATE INDEX idx_eval_code_date ON evaluations(code, date)
```

**컬럼 설명**:
- `id`: 기본 키
- `code`: 종목 코드
- `date`: 평가 날짜
- `evaluator`: 평가 도구 이름 (bollinger, ichimoku 등)
- `score`: 점수 (1.0~4.0)
- `details`: 상세 정보 (JSON 문자열)
- `created_at`: 평가 생성 시간

**제약조건**:
- `UNIQUE(code, date, evaluator)`: 같은 종목, 같은 날짜, 같은 평가 도구 중복 방지

### 3. reports (리포트 히스토리)

```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market TEXT NOT NULL,
    date TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market, date, format)
)
```

**컬럼 설명**:
- `id`: 기본 키
- `market`: 시장 (kr, us)
- `date`: 리포트 날짜
- `content`: 리포트 내용 (전체 텍스트)
- `format`: 형식 (markdown, html 등)
- `created_at`: 리포트 생성 시간

**제약조건**:
- `UNIQUE(market, date, format)`: 같은 시장, 같은 날짜, 같은 형식 중복 방지

## 주요 메서드

### 주가 데이터 관리

#### save_price_data()
```python
def save_price_data(self, code: str, market: str, data: List[Dict])
```

**목적**: 주가 데이터를 DB에 저장

**파라미터**:
- `code`: 종목 코드
- `market`: 시장
- `data`: 주가 데이터 리스트

**예시**:
```python
data = [
    {'date': '2026-02-10', 'open': 167400, 'high': 168100, 
     'low': 165500, 'close': 165800, 'volume': 19157551}
]

db.save_price_data("005930", "KRX", data)
```

**동작**:
- `INSERT OR REPLACE` 사용 (중복 시 업데이트)
- 개별 행별로 저장
- 오류 발생 시 해당 행만 스킵

**구현**:
```python
for row in data:
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO stock_prices 
            (code, market, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code, market, row['date'],
            row.get('open'), row.get('high'), row.get('low'),
            row.get('close'), row.get('volume')
        ))
    except Exception as e:
        print(f"⚠️  데이터 저장 오류 ({code}, {row.get('date')}): {e}")

self.conn.commit()
```

#### get_price_data()
```python
def get_price_data(self, code: str, start_date: Optional[str] = None, 
                   end_date: Optional[str] = None, limit: int = 60) -> List[Dict]
```

**목적**: DB에서 주가 데이터 조회

**파라미터**:
- `code`: 종목 코드
- `start_date`: 시작 날짜 (YYYY-MM-DD) (선택)
- `end_date`: 종료 날짜 (YYYY-MM-DD) (선택)
- `limit`: 조회 건수 제한 (기본: 60)

**반환값**:
```python
[
    {
        'id': 1,
        'code': '005930',
        'market': 'KRX',
        'date': '2026-02-10',
        'open': 167400.0,
        'high': 168100.0,
        'low': 165500.0,
        'close': 165800.0,
        'volume': 19157551,
        'created_at': '2026-02-10 09:58:00'
    },
    ...
]
```

**예시**:
```python
# 최근 60일 데이터
data = db.get_price_data("005930", limit=60)

# 기간 지정
data = db.get_price_data("005930", start_date="2026-01-01", end_date="2026-02-10")
```

**동작**:
- 최신 데이터가 앞에 오도록 정렬 (`ORDER BY date DESC`)
- `sqlite3.Row` → `dict` 변환

**구현**:
```python
query = "SELECT * FROM stock_prices WHERE code = ?"
params = [code]

if start_date:
    query += " AND date >= ?"
    params.append(start_date)

if end_date:
    query += " AND date <= ?"
    params.append(end_date)

query += " ORDER BY date DESC LIMIT ?"
params.append(limit)

cursor.execute(query, params)
rows = cursor.fetchall()

return [dict(row) for row in rows]
```

#### get_latest_date()
```python
def get_latest_date(self, code: str) -> Optional[str]
```

**목적**: 종목의 최신 데이터 날짜 조회 (캐싱 판단용)

**파라미터**:
- `code`: 종목 코드

**반환값**:
- 최신 날짜 (YYYY-MM-DD) 또는 None

**예시**:
```python
latest = db.get_latest_date("005930")
if latest == "2026-02-10":
    print("오늘 데이터 이미 있음, 캐시 사용")
else:
    print("새 데이터 수집 필요")
```

**구현**:
```python
cursor.execute(
    "SELECT MAX(date) as latest FROM stock_prices WHERE code = ?",
    (code,)
)
row = cursor.fetchone()
return row['latest'] if row else None
```

### 평가 결과 관리

#### save_evaluation()
```python
def save_evaluation(self, code: str, date: str, evaluator: str, 
                   score: float, details: Dict)
```

**목적**: 평가 결과를 DB에 저장

**파라미터**:
- `code`: 종목 코드
- `date`: 날짜
- `evaluator`: 평가 도구 이름 (bollinger, ichimoku 등)
- `score`: 점수 (1.0~4.0)
- `details`: 상세 정보 딕셔너리

**예시**:
```python
details = {
    'sma': 167000,
    'upper': 170000,
    'lower': 164000,
    'position': 80.5,
    'emoji': '🔴',
    'comment': '과매수 80%, 매도 고려'
}

db.save_evaluation("005930", "2026-02-10", "bollinger", 1.0, details)
```

**동작**:
- `details` Dict → JSON 문자열 변환 (`json.dumps`)
- `INSERT OR REPLACE` 사용

**구현**:
```python
cursor.execute("""
    INSERT OR REPLACE INTO evaluations 
    (code, date, evaluator, score, details)
    VALUES (?, ?, ?, ?, ?)
""", (
    code, date, evaluator, score,
    json.dumps(details, ensure_ascii=False)
))

self.conn.commit()
```

#### get_evaluations()
```python
def get_evaluations(self, code: str, date: str) -> List[Dict]
```

**목적**: 특정 종목, 날짜의 모든 평가 결과 조회

**파라미터**:
- `code`: 종목 코드
- `date`: 날짜

**반환값**:
```python
[
    {
        'id': 1,
        'code': '005930',
        'date': '2026-02-10',
        'evaluator': 'bollinger',
        'score': 1.0,
        'details': {
            'sma': 167000,
            'upper': 170000,
            'lower': 164000,
            'position': 80.5,
            'emoji': '🔴',
            'comment': '과매수 80%, 매도 고려'
        },
        'created_at': '2026-02-10 09:58:00'
    },
    {
        'id': 2,
        'evaluator': 'ichimoku',
        'score': 4.0,
        'details': {...}
    }
]
```

**예시**:
```python
evals = db.get_evaluations("005930", "2026-02-10")
for e in evals:
    print(f"{e['evaluator']}: {e['score']}점")
```

**동작**:
- JSON 문자열 → Dict 변환 (`json.loads`)

**구현**:
```python
cursor.execute("""
    SELECT * FROM evaluations 
    WHERE code = ? AND date = ?
""", (code, date))

rows = cursor.fetchall()
results = []

for row in rows:
    data = dict(row)
    data['details'] = json.loads(data['details'])
    results.append(data)

return results
```

### 리포트 관리

#### save_report()
```python
def save_report(self, market: str, date: str, content: str, format: str)
```

**목적**: 생성된 리포트를 DB에 저장 (히스토리 관리)

**파라미터**:
- `market`: 시장 (kr, us)
- `date`: 날짜
- `content`: 리포트 전체 내용
- `format`: 형식 (markdown, html)

**예시**:
```python
report_content = "# 주식 분석 리포트\n..."
db.save_report("kr", "2026-02-10", report_content, "markdown")
```

**구현**:
```python
cursor.execute("""
    INSERT OR REPLACE INTO reports 
    (market, date, content, format)
    VALUES (?, ?, ?, ?)
""", (market, date, content, format))

self.conn.commit()
```

## 캐싱 전략

### 데이터 수집 시 캐시 체크
```python
# main.py의 collect_and_cache_data()

def collect_and_cache_data(self, stock: Dict, force_update: bool = False):
    code = stock['code']
    market = stock.get('market', 'KRX')
    
    # 강제 업데이트가 아니면 캐시 확인
    if not force_update:
        latest_date = self.db.get_latest_date(code)
        if latest_date:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 최신 데이터가 오늘이면 DB에서 로드
            if latest_date >= today:
                print(f"📦 [{code}] 캐시에서 로드")
                return self.db.get_price_data(code, limit=60)
    
    # 캐시 미스 → 외부에서 수집
    print(f"📥 [{code}] 데이터 수집 중...")
    data = self.collector.collect(code, market)
    
    # DB 저장
    if data:
        self.db.save_price_data(code, market, data)
    
    return data
```

### 캐시 장점
- 중복 API 호출 방지
- 빠른 응답 속도
- 오프라인 작업 가능 (데이터가 있으면)

## 연결 관리

### 명시적 종료
```python
db = StockDatabase("data/stock_data.db")
# ... 작업
db.close()
```

### Context Manager 사용 (권장)
```python
with StockDatabase("data/stock_data.db") as db:
    data = db.get_price_data("005930")
    # 블록 종료 시 자동 close()
```

**구현**:
```python
def __enter__(self):
    return self

def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()
```

## 트랜잭션

### 자동 커밋
- 각 메서드 종료 시 `self.conn.commit()` 호출
- 개별 작업 단위로 커밋

### 수동 트랜잭션 (추후 지원)
```python
db.conn.execute("BEGIN")
try:
    db.save_price_data(...)
    db.save_evaluation(...)
    db.conn.commit()
except:
    db.conn.rollback()
```

## 성능 최적화

### 인덱스
```python
# 코드+날짜 조회 최적화
CREATE INDEX idx_stock_code_date ON stock_prices(code, date)

# 평가 결과 조회 최적화
CREATE INDEX idx_eval_code_date ON evaluations(code, date)
```

### 배치 삽입 (추후)
```python
cursor.executemany("""
    INSERT OR REPLACE INTO stock_prices (...)
    VALUES (?, ?, ...)
""", [(code, market, ...) for data in batch])
```

## 데이터 마이그레이션

### 스키마 버전 관리 (추후)
```python
# 버전 테이블
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT
)

# 마이그레이션 함수
def migrate_v1_to_v2(db):
    db.conn.execute("ALTER TABLE stock_prices ADD COLUMN adjusted_close REAL")
    db.conn.execute("INSERT INTO schema_version VALUES (2, CURRENT_TIMESTAMP)")
```

## 백업 및 복구

### 백업
```python
import shutil

shutil.copy2("data/stock_data.db", "data/stock_data_backup.db")
```

### SQLite 내장 백업
```python
import sqlite3

src = sqlite3.connect("data/stock_data.db")
dst = sqlite3.connect("data/stock_data_backup.db")

src.backup(dst)
dst.close()
src.close()
```

## 테스트

### 단위 테스트
```python
def test_save_and_get_price_data():
    db = StockDatabase(":memory:")  # 인메모리 DB
    
    data = [
        {'date': '2026-02-10', 'open': 100, 'high': 110, 
         'low': 95, 'close': 105, 'volume': 1000000}
    ]
    
    db.save_price_data("TEST", "KRX", data)
    
    loaded = db.get_price_data("TEST", limit=10)
    assert len(loaded) == 1
    assert loaded[0]['close'] == 105
    
    db.close()
```

### 통합 테스트
```python
def test_full_workflow():
    db = StockDatabase("test.db")
    
    # 데이터 저장
    data = [...]
    db.save_price_data("005930", "KRX", data)
    
    # 평가 결과 저장
    db.save_evaluation("005930", "2026-02-10", "bollinger", 1.0, {...})
    
    # 조회
    loaded = db.get_price_data("005930")
    evals = db.get_evaluations("005930", "2026-02-10")
    
    assert len(loaded) > 0
    assert len(evals) > 0
    
    db.close()
    os.remove("test.db")
```

---

**문서 버전**: 1.0  
**최종 수정**: 2026-02-10
