# 🚀 빠른 시작 가이드

## 1. 설치

```bash
cd stock-analyzer
pip install -r requirements.txt
```

## 2. 첫 실행

```bash
cd src
python main.py -m kr
```

출력 예시:
```
============================================================
📊 KR 시장 분석 시작 (2026-02-10)
============================================================

🔍 [005930] 삼성전자 분석 중...
📥 [005930] 데이터 수집 중... (2025-12-12 ~ 2026-02-10)
✅ [005930] 60건 수집 완료
✅ [005930] 평가 완료: 👌

...

============================================================
✅ KR 시장 분석 완료!
📄 리포트: reports/kr_2026-02-10.md
============================================================
```

## 3. 리포트 확인

```bash
# Markdown 리포트 보기
cat ../reports/kr_2026-02-10.md

# HTML 리포트는 브라우저에서 열기
# reports/kr_2026-02-10.html
```

## 4. 설정 커스터마이징

### 종목 추가하기

`config/stocks.yml` 편집:

```yaml
kr_stocks:
  - code: "005930"
    name: "삼성전자"
    market: "KRX"
    note: "반도체/전자"
  
  # 새 종목 추가
  - code: "035720"
    name: "카카오"
    market: "KRX"
    note: "IT/플랫폼"
```

### 리포트 형식 변경

`config/report.yml` 편집:

```yaml
format: html  # markdown → html로 변경
```

### 평가 도구 설정

`config/evaluators.yml` 편집:

```yaml
bollinger:
  period: 20        # 기간 변경
  std_multiplier: 2.0
  weight: 1.0

ichimoku:
  conversion_period: 9
  base_period: 26
  span_b_period: 52
  weight: 1.0
```

## 5. 일일 실행 자동화 (Cron)

### Linux/Mac

```bash
# crontab 편집
crontab -e

# 한국 주식: 매일 오후 4시 (장 마감 후)
0 16 * * 1-5 cd /path/to/stock-analyzer/src && python main.py -m kr

# 미국 주식: 매일 오전 6시 (전날 장 마감 후)
0 6 * * 1-5 cd /path/to/stock-analyzer/src && python main.py -m us
```

### Windows (작업 스케줄러)

1. 작업 스케줄러 실행
2. "기본 작업 만들기" 선택
3. 트리거: 매일, 시간 설정
4. 동작: 프로그램 시작
   - 프로그램: `python`
   - 인수: `main.py -m kr`
   - 시작 위치: `C:\path\to\stock-analyzer\src`

## 6. 고급 사용법

### 강제 데이터 업데이트

```bash
# 캐시 무시하고 최신 데이터 수집
python main.py -m kr -f
```

### 과거 날짜 분석

```bash
# 특정 날짜로 분석 (백테스팅)
python main.py -m kr -d 2026-02-01
```

### 전체 시장 분석

```bash
# 한국 + 미국 모두 분석
python main.py -m all
```

### 데이터베이스 직접 조회

```python
from database import StockDatabase

db = StockDatabase("../data/stock_data.db")

# 삼성전자 최근 10일 데이터
data = db.get_price_data("005930", limit=10)
print(data)

# 특정 날짜 평가 결과
evals = db.get_evaluations("005930", "2026-02-10")
print(evals)

db.close()
```

## 7. 문제 해결

### FinanceDataReader 오류

```bash
# 재설치
pip uninstall finance-datareader
pip install finance-datareader --upgrade
```

### 데이터베이스 초기화

```bash
# DB 삭제 후 재생성
rm ../data/stock_data.db
python main.py -m kr
```

### 의존성 문제

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 8. 다음 단계

- [ ] 새로운 평가 도구 추가 (RSI, MACD 등)
- [ ] 리포트에 차트 추가
- [ ] 알림 기능 (이메일, 텔레그램)
- [ ] 웹 대시보드 구축
- [ ] 백테스팅 기능

---

**도움이 필요하면 README.md를 참고하세요!**
