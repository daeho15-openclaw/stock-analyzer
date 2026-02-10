# 🚀 빠른 시작 가이드

5분 안에 첫 주식 분석 리포트를 생성해보세요!

## 📋 사전 준비

- Python 3.8 이상
- pip (Python 패키지 관리자)
- 인터넷 연결 (주가 데이터 수집용)

## 1️⃣ 설치

```bash
# 저장소 클론
git clone https://github.com/daeho15-openclaw/stock-analyzer.git
cd stock-analyzer

# 의존성 설치
pip install -r requirements.txt
```

**설치되는 패키지:**
- `FinanceDataReader`: 주가 데이터 수집
- `pandas`, `numpy`: 데이터 처리
- `pyyaml`: 설정 파일 파싱
- `anthropic`: Claude API (LLM 기능용, 선택)

## 2️⃣ 첫 실행 (LLM 없이)

```bash
cd src
python main.py -m kr
```

**출력 예시:**
```
📥 FinanceDataReader 사용
ℹ️  LLM 기능이 비활성화되었습니다.

============================================================
📊 KR 시장 분석 시작 (2026-02-10)
============================================================

🔍 [005930] 삼성전자 분석 중...
📦 [005930] 캐시에서 로드
✅ [005930] 평가 완료: 👌

🔍 [042660] 한화오션 분석 중...
📦 [042660] 캐시에서 로드
✅ [042660] 평가 완료: 🔥🔥

✅ 리포트 저장: ../reports/kr_2026-02-10.md

============================================================
✅ KR 시장 분석 완료!
📄 리포트: ../reports/kr_2026-02-10.md
============================================================
```

## 3️⃣ 리포트 확인

```bash
# Markdown 리포트 보기
cat ../reports/kr_2026-02-10.md

# HTML 리포트 보려면 config/report.yml 수정
# format: markdown → format: html
# 그 후 재실행하면 ../reports/kr_2026-02-10.html 생성
```

**리포트 예시:**

```markdown
# 📊 한국 주식 분석 리포트
**날짜**: 2026-02-10

---

| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |
|--------|-----------|-----------|------|------|
| 삼성전자 | 🔴 | 🟢 | 👌 | 💰 165,800원 | 과매수 80%, 매도 고려 | 골든크로스, 강세 |
| 한화오션 | 🟢 | 🟡 | 🔥🔥 | 💰 130,900원 | 하단 근처 7%, 반등 기대 | 중립, 추세 전환 중 |

---

## 📈 종합 평가

- **최고 평가** 🔥🔥: 한화오션
- **긍정적** 👍: 한화오션
- **중립** 👌: 삼성전자
```

## 4️⃣ 커스터마이징

### 분석 종목 변경

`config/stocks.yml` 편집:

```yaml
kr_stocks:
  - code: "005930"
    name: "삼성전자"
    market: "KRX"
    note: "반도체"
  
  - code: "000660"
    name: "SK하이닉스"
    market: "KRX"
    note: "메모리 반도체"
  
  # 원하는 종목 추가
  - code: "035720"
    name: "카카오"
    market: "KRX"
    note: "인터넷 플랫폼"
```

**종목 코드 찾는 법:**
- 네이버 증권에서 종목 검색 → URL의 code 파라미터
- 예: `https://finance.naver.com/item/main.naver?code=005930`
  - 종목 코드 = `005930`

### 평가 지표 조정

`config/evaluators.yml` 편집:

```yaml
enabled_evaluators:
  - bollinger
  - ichimoku

bollinger:
  period: 20          # 20일 이동평균 (기본값)
  std_multiplier: 2.0 # 표준편차 배수 (기본값)
  weight: 1.0         # 가중치

ichimoku:
  tenkan_period: 9    # 전환선 기간
  kijun_period: 26    # 기준선 기간
  senkou_span_b: 52   # 선행스팬B 기간
  weight: 1.0
```

### 리포트 형식 변경

`config/report.yml` 편집:

```yaml
# Markdown 또는 HTML
format: markdown  # 또는 html

# 출력 디렉토리
output_dir: "../reports"

# LLM 기능 (나중에 설정 가능)
use_llm: false
```

## 5️⃣ 고급 사용법

### 다른 시장 분석

```bash
# 미국 주식 (config/stocks.yml에 us_stocks 섹션 필요)
python main.py -m us

# 전체 시장
python main.py -m all
```

### 강제 데이터 업데이트

```bash
# 캐시 무시하고 새로 데이터 수집
python main.py -m kr -f
```

### 과거 날짜 분석

```bash
# 특정 날짜의 데이터로 분석
python main.py -m kr -d 2026-02-08
```

### 자동화 (크론잡)

매일 오전 9시에 자동 분석:

```bash
# crontab -e
0 9 * * 1-5 cd ~/stock-analyzer/src && /usr/bin/python3 main.py -m kr
```

## 6️⃣ LLM 기능 활성화 (선택)

LLM 없이도 완벽히 작동하지만, 자연어 해설을 원한다면:

### 단계 1: API 키 발급
1. [Anthropic Console](https://console.anthropic.com/) 가입
2. API Keys 메뉴에서 키 생성
3. `sk-ant-api...` 형식의 키 복사

### 단계 2: API 키 설정

**방법 A (권장)**: 환경변수
```bash
export ANTHROPIC_API_KEY=sk-ant-api-여기에-당신의-키
```

**방법 B**: 설정파일
```yaml
# config/report.yml
api_key: "sk-ant-api-여기에-당신의-키"
```
⚠️ Git에 올라가지 않도록 주의! 환경변수 권장

### 단계 3: 설정 활성화
`config/report.yml`:
```yaml
use_llm: true
llm_model: "claude-haiku-4-5"
```

### 단계 4: 실행
```bash
python main.py -m kr
```

자세한 내용: [LLM 기능 가이드](docs/LLM_GUIDE.md)

## 🎯 다음 단계

- [프로젝트 개요](docs/OVERVIEW.md) - 전체 아키텍처 이해
- [모듈 문서](docs/) - 각 모듈 상세 설명
- [평가 도구 추가하기](docs/MODULE_EVALUATORS.md) - RSI, MACD 등 추가
- [LLM 가이드](docs/LLM_GUIDE.md) - AI 해설 기능 심화

## ❓ 문제 해결

### "ModuleNotFoundError: No module named 'FinanceDataReader'"

```bash
pip install -r requirements.txt
```

### "FileNotFoundError: config/stocks.yml"

`src/` 디렉토리에서 실행했는지 확인:
```bash
cd src
python main.py -m kr
```

### 리포트가 생성되지 않아요

1. `reports/` 디렉토리 확인
2. 에러 메시지 확인
3. 인터넷 연결 확인 (데이터 수집 필요)

### 데이터 수집이 느려요

**정상입니다!**
- FinanceDataReader는 종목당 ~0.5초 딜레이
- 10개 종목 = 약 5초 소요
- 캐시 사용 시 재실행은 빠름

## 💡 팁

- **처음 실행**: 모든 데이터를 새로 수집하므로 시간이 걸림
- **재실행**: 캐시를 사용하여 빠름 (같은 날짜)
- **HTML 리포트**: 모바일에서 보기 편리
- **LLM 비용**: haiku 모델 사용 시 매우 저렴 (~$0.003/종목)

## 📖 추가 자료

- [GitHub 저장소](https://github.com/daeho15-openclaw/stock-analyzer)
- [상세 문서](docs/OVERVIEW.md)
- [이슈 제보](https://github.com/daeho15-openclaw/stock-analyzer/issues)

---

**Happy Trading! 📈**
