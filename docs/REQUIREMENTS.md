# 프로그램 요구사항

## 1. 전체 요구사항

### 1.1 기본 요구사항
- **목적**: 최근 60일의 종가, 저가, 고가 데이터를 기반으로 각 주식의 오늘 장마감 데이터를 바탕으로 데일리 리포트 생성
- **평가 기준**: 각 평가 도구를 기반으로 scoring을 할 것이며, 평가 도구는 추가 가능한 구조
- **확장성**: 모듈화된 구조로 새로운 평가 도구, 데이터 소스, 리포트 형식 추가 용이

### 1.2 초기 평가 도구
- 볼린저 밴드 (Bollinger Bands)
- 일목균형표 (Ichimoku Cloud)

## 2. 데이터 수집 및 캐싱

### 2.1 데이터 소스
- **Primary**: FinanceDataReader 사용
- **Fallback**: JSON 파일에서 로드

### 2.2 데이터 기간
- **기본**: 최근 60일치 데이터
- **설정 가능**: `config/stocks.yml`에서 `data_config.days`로 조정

### 2.3 캐싱 전략
- **날마다 실행**될 것이기 때문에 이전 데이터도 저장 후 캐싱 적용
- **캐시 체크**: 
  - DB에서 최신 데이터 날짜 확인
  - 오늘 날짜의 데이터가 있으면 DB에서 로드
  - 없으면 외부 API에서 수집 후 DB 저장
- **중복 방지**: 동일 종목, 동일 날짜 데이터 중복 저장 방지 (UNIQUE 제약)

### 2.4 데이터베이스 (선택 사항: 심층)
- **SQLite**: 매우 가벼운 내장 DB 사용
- **테이블 구조**:
  - `stock_prices`: 주가 데이터
  - `evaluations`: 평가 결과
  - `reports`: 리포트 히스토리

## 3. 평가 도구 (Evaluators)

### 3.1 구조
- **독립적인 .py 파일**로 구성
- 각 종목마다 평가를 진행하며 **score를 출력**
- `BaseEvaluator` 추상 클래스 상속

### 3.2 평가 도구 인터페이스
```python
class BaseEvaluator(ABC):
    def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
        """
        Returns:
            (score, emoji, comment)
            - score: 1.0~4.0
            - emoji: 🟢, 🟡, 🟠, 🔴
            - comment: 분석 코멘트
        """
        pass
    
    def get_details(self, data: List[Dict]) -> Dict:
        """상세 분석 정보 (DB 저장용)"""
        pass
```

### 3.3 점수 체계
- **1.0점**: 강한 매도 신호
- **2.0점**: 약한 매도 신호
- **3.0점**: 약한 매수 신호
- **4.0점**: 강한 매수 신호

### 3.4 볼린저 밴드 평가 기준
- **계산**: 20일 이동평균 ± 2σ
- **평가**:
  - 🟢 4점: 밴드 내 위치 0~25% (하단 근처, 반등 기대)
  - 🟡 3점: 밴드 내 위치 25~50% (중립)
  - 🟠 2점: 밴드 내 위치 50~80% (과열, 조정 주의)
  - 🔴 1점: 밴드 내 위치 80~100% (과매수, 매도 고려)

### 3.5 일목균형표 평가 기준
- **계산**:
  - 전환선: 9일
  - 기준선: 26일
  - 선행스팬 B: 52일
- **평가**:
  - 🟢 4점: 골든크로스 + 구름 위 (강한 매수)
  - 🟡 3점: 중립 (추세 전환 중)
  - 🟠 2점: 하락 조짐
  - 🔴 1점: 데드크로스 + 구름 아래 (강한 매도)

### 3.6 종합 평가
- **평균 점수** 계산: (볼린저 점수 + 일목균형표 점수) / 2
- **가중치** 지원: `config/evaluators.yml`에서 `weight` 설정
- **Emoji 매핑**:
  - 🔥🔥: 3.5~4.0점 (매우 좋음)
  - 🔥: 3.25~3.5점 (좋음)
  - 👍: 2.75~3.25점 (긍정적)
  - 👌: 2.5~2.75점 (중립)
  - 🧐: 2.0~2.5점 (주의)
  - 👎: 1.5~2.0점 (부정적)
  - 💣: 1.0~1.5점 (매우 나쁨)

## 4. 리포트 생성

### 4.1 리포트 형식
- **Markdown** (기본)
- **HTML** (선택)
- 날마다의 리포트를 출력 가능

### 4.2 리포트 구조
```markdown
# 📊 [시장명] 주식 분석 리포트
**날짜**: YYYY-MM-DD

| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |
|--------|-----------|-----------|------|------|
| 삼성전자 | 🟠 | 🟢 | 👍 | 💰 현재가, 밴드 위치, 코멘트 |

## 📈 종합 평가
- **최고 평가**: ...
- **긍정적**: ...
- **중립**: ...

## 💡 시황 요약
- 총 N개 종목 분석
- 강한 매수 신호: M개
```

### 4.3 리포트 저장
- **파일명 형식**: `{market}_{date}.{ext}` (예: `kr_2026-02-10.md`)
- **저장 위치**: `reports/` 디렉토리
- **DB 저장** (선택): 리포트 히스토리 관리

### 4.4 리포트 내용
- ✅ 종합 요약
- ✅ 종목별 표
- ✅ 상세 분석
- ⏳ 차트 데이터 (추후 구현)

## 5. 설정 파일

### 5.1 stocks.yml
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

data_config:
  days: 60
  cache_days: 7
```

### 5.2 evaluators.yml
```yaml
enabled_evaluators:
  - bollinger
  - ichimoku

bollinger:
  period: 20
  std_multiplier: 2.0
  weight: 1.0

ichimoku:
  conversion_period: 9
  base_period: 26
  span_b_period: 52
  weight: 1.0
```

### 5.3 report.yml
```yaml
format: markdown  # markdown 또는 html
output_dir: "reports"
filename_format: "{market}_{date}.{ext}"

include:
  summary: true
  table: true
  details: true
  chart_data: false

language: "ko"
timezone: "Asia/Seoul"
```

## 6. 아키텍처 요구사항

### 6.1 모듈 구성
- **데이터 수집 모듈**: `src/collectors/`
- **평가 모듈**: `src/evaluators/`
- **리포트 생성 모듈**: `src/reporters/`
- **DB 관리 모듈**: `src/database.py`
- **메인 프로그램**: `src/main.py`

### 6.2 각 모듈은 확장과 수정이 용이하도록 적당히 분리
- 독립적인 파일로 구성
- 인터페이스를 통한 느슨한 결합
- 새 모듈 추가 시 기존 코드 최소 수정

### 6.3 의존성
- Python 3.12+
- FinanceDataReader
- PyYAML (설정 파일)
- Pandas, NumPy (데이터 처리)
- SQLite3 (내장)

## 7. 실행 요구사항

### 7.1 CLI 인터페이스
```bash
python main.py -m kr              # 한국 주식 분석
python main.py -m us              # 미국 주식 분석
python main.py -m all             # 전체 시장 분석
python main.py -m kr -f           # 강제 업데이트
python main.py -m kr -d 2026-02-10  # 특정 날짜
```

### 7.2 출력
- 진행 상황 콘솔 출력
- 리포트 파일 경로 출력
- 오류 시 명확한 메시지

## 8. 성능 요구사항

### 8.1 데이터 수집
- API 호출 간 딜레이: 0.5초
- 타임아웃: 10초
- 재시도: 3회

### 8.2 캐싱
- DB 조회 우선
- 최신 데이터 존재 시 외부 API 호출 생략

### 8.3 확장성
- 종목 수 증가에도 선형 시간 복잡도 유지
- 병렬 처리 고려 (추후)

## 9. 품질 요구사항

### 9.1 정확성
- 기술적 지표 계산 정확도
- 데이터 무결성 (DB 제약조건)

### 9.2 신뢰성
- 외부 API 장애 시 Fallback (JSON)
- 부분 실패 시에도 나머지 종목 처리 계속

### 9.3 유지보수성
- 명확한 코드 구조
- Docstring으로 문서화
- 설정 기반 동작 (하드코딩 최소화)

## 10. 보안 요구사항

### 10.1 데이터 보호
- API 키는 환경 변수 또는 설정 파일 (Git 제외)
- DB 파일 적절한 권한 설정

### 10.2 입력 검증
- 설정 파일 파싱 시 검증
- 외부 데이터 Sanitization

## 11. 제약사항

### 11.1 현재 제약
- 실시간 데이터 미지원 (장 종료 후 데이터)
- 기술적 분석만 지원 (펀더멘탈 미포함)
- 백테스팅 미검증

### 11.2 API 제약
- FinanceDataReader 무료 API 사용
- 과도한 요청 시 제한 가능

## 12. 향후 확장 요구사항

### 12.1 우선순위 높음
- [ ] RSI, MACD 등 추가 지표
- [ ] 알림 시스템 (Telegram, Email)
- [ ] 백테스팅 기능

### 12.2 우선순위 중간
- [ ] 차트 생성 및 리포트 포함
- [ ] 웹 대시보드
- [ ] 포트폴리오 관리

### 12.3 우선순위 낮음
- [ ] 실시간 데이터 지원
- [ ] 머신러닝 예측 모델
- [ ] 다중 사용자 지원

---

**문서 버전**: 1.0  
**최종 수정**: 2026-02-10  
**작성자**: Stock Analyzer Project
