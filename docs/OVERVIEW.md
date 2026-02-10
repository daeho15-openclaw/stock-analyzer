# 주식 분석 프로그램 - 전체 개요

## 📋 프로젝트 개요

### 목적
한국 및 미국 주식 시장의 종목들을 기술적 분석 지표를 활용하여 자동으로 분석하고 일일 리포트를 생성하는 시스템

### 핵심 특징
- **확장 가능한 아키텍처**: 새로운 평가 도구를 독립적인 모듈로 추가 가능
- **데이터 캐싱**: SQLite DB를 통한 히스토리 관리 및 중복 수집 방지
- **설정 기반**: YAML/JSON 설정 파일로 종목, 평가 도구, 리포트 형식 관리
- **유연한 데이터 소스**: FinanceDataReader 또는 기존 JSON 파일에서 데이터 로드

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    설정 파일 (YAML)                      │
│  - stocks.yml: 종목 목록                                │
│  - evaluators.yml: 평가 도구 설정                        │
│  - report.yml: 리포트 설정                               │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  메인 프로그램 (main.py)                 │
│  - 설정 로드                                             │
│  - 모듈 초기화                                           │
│  - 워크플로우 조정                                       │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 데이터 수집   │  │  평가 모듈    │  │ 리포트 생성   │
│  Collectors  │  │  Evaluators  │  │  Reporters   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                ┌──────────────────┐
                │  데이터베이스     │
                │  (SQLite)        │
                │  - 주가 데이터    │
                │  - 평가 결과      │
                │  - 리포트 히스토리 │
                └──────────────────┘
```

## 📂 디렉토리 구조

```
stock-analyzer/
├── config/                    # 설정 파일
│   ├── stocks.yml            # 종목 목록
│   ├── evaluators.yml        # 평가 도구 설정
│   └── report.yml            # 리포트 설정
│
├── data/                      # 데이터 저장소
│   └── stock_data.db         # SQLite 데이터베이스
│
├── src/                       # 소스 코드
│   ├── collectors/           # 데이터 수집 모듈
│   │   ├── __init__.py
│   │   ├── fdr_collector.py # FinanceDataReader 수집기
│   │   └── json_collector.py # JSON 파일 수집기
│   │
│   ├── evaluators/           # 평가 도구 모듈
│   │   ├── __init__.py
│   │   ├── base.py          # 베이스 클래스
│   │   ├── bollinger.py     # 볼린저 밴드
│   │   └── ichimoku.py      # 일목균형표
│   │
│   ├── reporters/            # 리포트 생성 모듈
│   │   ├── __init__.py
│   │   ├── markdown.py      # Markdown 리포터
│   │   └── html.py          # HTML 리포터
│   │
│   ├── database.py           # DB 관리 모듈
│   └── main.py               # 메인 프로그램
│
├── reports/                   # 생성된 리포트
│   ├── kr_2026-02-10.md
│   └── us_2026-02-10.md
│
├── docs/                      # 프로그램 문서
│   ├── OVERVIEW.md
│   ├── MODULE_COLLECTORS.md
│   ├── MODULE_EVALUATORS.md
│   ├── MODULE_REPORTERS.md
│   ├── MODULE_DATABASE.md
│   └── REQUIREMENTS.md
│
├── requirements.txt           # Python 의존성
├── README.md                  # 사용자 가이드
├── QUICKSTART.md             # 빠른 시작 가이드
└── run_analysis.sh           # 실행 스크립트
```

## 🔄 워크플로우

### 1. 초기화 단계
1. 설정 파일 로드 (YAML)
2. 데이터베이스 연결
3. 데이터 수집기 초기화
4. 평가 도구 초기화
5. 리포터 초기화

### 2. 데이터 수집 단계
```
종목 리스트 순회
  └─> 캐시 확인 (DB에 최신 데이터 존재?)
       ├─> 있음: DB에서 로드
       └─> 없음: 외부 API에서 수집
            └─> DB에 저장
```

### 3. 분석 단계
```
각 종목별로:
  └─> 활성화된 평가 도구 순회
       ├─> 볼린저 밴드 평가 (점수, emoji, 코멘트)
       ├─> 일목균형표 평가 (점수, emoji, 코멘트)
       └─> 평가 결과 DB 저장
  └─> 종합 평가 계산 (평균 점수, 종합 emoji)
```

### 4. 리포트 생성 단계
```
리포트 템플릿 생성
  ├─> 테이블 생성 (종목명, 평가 결과)
  ├─> 종합 평가 섹션 (최고/긍정적/중립/부정적)
  ├─> 시황 요약 (통계)
  └─> 파일 저장 (Markdown 또는 HTML)
       └─> DB에 리포트 히스토리 저장
```

## 🎯 핵심 설계 원칙

### 1. 모듈 독립성
- 각 모듈은 독립적으로 동작
- 인터페이스를 통한 느슨한 결합
- 새로운 모듈 추가 시 기존 코드 수정 최소화

### 2. 확장성
- 새로운 평가 도구: `evaluators/` 디렉토리에 파일 추가
- 새로운 데이터 소스: `collectors/` 디렉토리에 파일 추가
- 새로운 리포트 형식: `reporters/` 디렉토리에 파일 추가

### 3. 설정 기반
- 하드코딩 최소화
- YAML/JSON 설정 파일로 동작 제어
- 코드 수정 없이 동작 변경 가능

### 4. 데이터 영속성
- SQLite를 통한 데이터 캐싱
- 히스토리 관리 및 추적
- 중복 수집 방지로 API 효율성 향상

## 📊 데이터 흐름

```
외부 데이터 소스
(FinanceDataReader, JSON)
        │
        ▼
  데이터 수집기
    (Collector)
        │
        ▼
    SQLite DB
  (캐시 레이어)
        │
        ▼
    평가 도구
  (Evaluators)
        │
        ▼
   평가 결과 저장
   (DB + 메모리)
        │
        ▼
    리포터
  (Reporter)
        │
        ▼
   리포트 파일
  (MD/HTML)
```

## 🔧 기술 스택

### 언어 및 프레임워크
- **Python 3.12+**

### 라이브러리
- **FinanceDataReader**: 주가 데이터 수집
- **Pandas/NumPy**: 데이터 처리 및 계산
- **PyYAML**: 설정 파일 파싱
- **SQLite3**: 데이터베이스 (내장)

### 데이터베이스
- **SQLite**: 경량 내장 DB, 파일 기반

## 🎯 현재 기능

### 지원 시장
- ✅ 한국 주식 (KRX)
- ✅ 미국 주식 (NASDAQ, NYSE)

### 지원 평가 도구
- ✅ 볼린저 밴드 (Bollinger Bands)
- ✅ 일목균형표 (Ichimoku Cloud)

### 지원 리포트 형식
- ✅ Markdown
- ✅ HTML

## 🚀 향후 확장 가능 기능

### 평가 도구
- [ ] RSI (Relative Strength Index)
- [ ] MACD (Moving Average Convergence Divergence)
- [ ] 이동평균선 (Moving Average)
- [ ] 스토캐스틱 (Stochastic)
- [ ] 거래량 분석

### 리포트
- [ ] PDF 리포트
- [ ] 차트 포함 리포트
- [ ] 이메일 자동 발송
- [ ] Telegram 봇 연동

### 기능
- [ ] 알림 시스템 (특정 조건 만족 시)
- [ ] 백테스팅 기능
- [ ] 포트폴리오 관리
- [ ] 웹 대시보드

## 📝 사용 시나리오

### 시나리오 1: 일일 정기 분석
```bash
# Cron으로 매일 자동 실행
0 16 * * 1-5 cd /path/to/stock-analyzer/src && python main.py -m kr
0 6 * * 1-5 cd /path/to/stock-analyzer/src && python main.py -m us
```

### 시나리오 2: 종목 추가
1. `config/stocks.yml` 편집
2. 종목 코드 및 정보 추가
3. 프로그램 실행 (자동으로 새 종목 분석)

### 시나리오 3: 새 평가 도구 추가
1. `src/evaluators/new_evaluator.py` 생성
2. `BaseEvaluator` 상속받아 구현
3. `config/evaluators.yml`에 설정 추가
4. `src/main.py`의 `init_evaluators()`에 등록

## ⚠️ 제약사항 및 주의사항

### 데이터 소스
- FinanceDataReader는 무료 API이지만 과도한 요청 시 제한될 수 있음
- 실시간 데이터가 아닌 장 종료 후 데이터

### 평가 결과
- 기술적 분석만 제공 (펀더멘탈 분석 미포함)
- 투자 조언이 아닌 참고 자료
- 백테스팅 미검증

### 성능
- 종목 수가 많을 경우 수집 시간 증가
- 캐싱을 통해 반복 실행 시 성능 향상

## 📞 지원 및 문서

- **README.md**: 전체 사용 가이드
- **QUICKSTART.md**: 빠른 시작 가이드
- **docs/**: 모듈별 상세 문서
- **소스 코드**: Docstring으로 상세 설명

---

**문서 버전**: 1.0  
**최종 수정**: 2026-02-10  
**작성자**: Stock Analyzer Project
