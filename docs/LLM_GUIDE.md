# 🤖 LLM 기능 가이드

## 📌 중요: LLM은 선택 기능입니다

이 프로그램은 **LLM 없이도 완벽히 작동**합니다!

- **LLM 비활성화** (기본): 기술 지표 분석 + 템플릿 코멘트 제공
- **LLM 활성화**: 위 기능 + Claude API 기반 자연어 해설 추가

## 🚀 빠른 시작

### 1단계: API 키 발급

1. [Anthropic Console](https://console.anthropic.com/) 방문
2. 회원가입 (이메일 인증 필요)
3. **$5 무료 크레딧** 자동 제공
4. API Keys 메뉴에서 새 키 생성
5. `sk-ant-api...` 형식의 키 복사

**예상 비용:**
- claude-3-5-haiku: ~$0.003/종목
- 10개 종목 일일 분석: ~$0.03/일 = ~$0.90/월
- $5 크레딧으로 약 5-6개월 사용 가능

### 2단계: 환경변수 설정

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY=sk-ant-api-여기에-당신의-키-입력
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-api-여기에-당신의-키-입력"
```

**영구 설정 (Linux/Mac ~/.bashrc 또는 ~/.zshrc):**
```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-api-여기에-당신의-키-입력' >> ~/.bashrc
source ~/.bashrc
```

### 3단계: 설정 파일 수정

`config/report.yml` 편집:

```yaml
# LLM 기반 해설 생성 (Claude API)
use_llm: true  # false → true로 변경

llm_model: "claude-3-5-haiku-20241022"  # 빠르고 저렴한 모델 (권장)
# llm_model: "claude-3-5-sonnet-20241022"  # 더 정확하지만 15배 비싼 모델
```

### 4단계: 실행

```bash
cd src
python main.py -m kr
```

LLM이 활성화되면 리포트에 자연어 해설이 추가됩니다.

## 🔍 LLM 활성화 전/후 비교

### 기본 모드 (LLM 비활성화)

```markdown
| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |
|--------|-----------|-----------|------|------|
| 삼성전자 | 🔴 | 🟢 | 👌 | 💰 165,800원 | 과매수 80%, 매도 고려 | 골든크로스, 강세 |
```

### LLM 모드 (활성화)

```markdown
| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |
|--------|-----------|-----------|------|------|
| 삼성전자 | 🔴 | 🟢 | 👌 | 💰 165,800원 |

💬 **AI 분석:**
주가가 볼린저 밴드 상단(80%)에 위치하여 단기 과열 신호가 감지됩니다. 
일목균형표는 골든크로스와 구름 위 위치로 중장기 상승 추세를 시사하지만, 
단기적으로는 조정 가능성을 염두에 두어야 합니다. 
현재가 근처에서 일부 차익실현 후 재진입 타이밍을 노리는 전략을 고려해볼 수 있습니다.
```

## ⚙️ 설정 옵션

### config/report.yml

```yaml
# LLM 기능 활성화/비활성화
use_llm: false

# 사용할 모델 선택
llm_model: "claude-3-5-haiku-20241022"

# ⚠️ 사용 불가 (Anthropic API 정책)
use_openclaw_token: false  # OpenClaw OAuth 토큰은 지원 안 함
```

### 모델 선택 가이드

| 모델 | 속도 | 비용 | 품질 | 추천 |
|------|------|------|------|------|
| claude-3-5-haiku-20241022 | 빠름 | $0.003 | 좋음 | ⭐ 일일 분석 |
| claude-3-5-sonnet-20241022 | 느림 | $0.045 | 매우 좋음 | 특별 분석 |

**권장:** haiku 모델이 가성비가 뛰어나며, 주식 분석에 충분한 품질을 제공합니다.

## 🛠️ 구현 세부사항

### LLM 호출 흐름

1. **데이터 수집**: FinanceDataReader → 주가 데이터
2. **기술 분석**: BollingerEvaluator, IchimokuEvaluator → 점수/코멘트
3. **LLM 해설 생성** (활성화 시):
   - `ClaudeCommentGenerator.generate_comment()` 호출
   - 종목 정보 + 평가 결과를 구조화된 프롬프트로 변환
   - Claude API 호출 (anthropic SDK)
   - 자연어 해설 생성
4. **리포트 작성**: Markdown/HTML 리포터 → 최종 리포트

### 프롬프트 구조

```python
# reporters/llm_generator.py의 _build_prompt()
f"""당신은 전문 주식 애널리스트입니다.
다음 종목의 기술적 분석 결과를 바탕으로 간결하고 명확한 해설을 작성하세요.

종목: {stock_name} ({stock_code})
현재가: {price}원

볼린저밴드 분석:
- 점수: {bb_score}
- 평가: {bb_emoji} {bb_comment}

일목균형표 분석:
- 점수: {ichi_score}
- 평가: {ichi_emoji} {ichi_comment}

요구사항:
1. 2-3문장으로 간결하게 작성
2. 투자 관점에서 실용적인 인사이트 제공
3. 기술적 용어는 쉽게 풀어서 설명
4. 면책 조항 불필요 (이미 리포트에 포함)
"""
```

### 에러 핸들링

```python
try:
    # Claude API 호출
    response = client.messages.create(...)
    return response.content[0].text
except Exception as e:
    # LLM 실패 시 자동으로 기본 템플릿 코멘트 사용
    return self._fallback_comment(stock_info, eval_results)
```

**Fallback 동작:**
- API 키 없음 → 기본 템플릿 사용
- API 호출 실패 → 기본 템플릿 사용
- 네트워크 오류 → 기본 템플릿 사용
- **프로그램은 중단되지 않고 계속 실행됩니다**

## ❓ 자주 묻는 질문

### Q1: OpenClaw OAuth 토큰을 사용할 수 없나요?

**A:** 아니요, 사용할 수 없습니다.

**이유:**
- Anthropic의 공개 API는 OAuth 토큰을 지원하지 않습니다
- OpenClaw 내부에서는 OAuth 토큰으로 Claude API를 호출하지만, 이는 OpenClaw의 자체 OAuth 인프라를 통해서만 가능합니다
- 외부 Python 스크립트는 반드시 API 키를 사용해야 합니다

**OpenClaw 내부 vs 외부:**
```
OpenClaw 내부 (OK):
  agent.getAuthenticatedAPI("anthropic") → OAuth 토큰 사용
  
외부 Python (NO):
  anthropic.Anthropic(api_key=...) → API 키만 가능
```

**해결책:**
1. Anthropic Console에서 API 키 발급 (권장 ⭐)
2. OpenClaw의 sessions_spawn을 통해 LLM 호출 위임 (고급)

### Q2: 비용이 얼마나 드나요?

**A:** 매우 저렴합니다.

**실제 사용량 (claude-3-5-haiku 기준):**
- 1개 종목 분석: ~$0.003
- 10개 종목 일일 분석: ~$0.03
- 월간 (30일): ~$0.90
- **$5 무료 크레딧으로 약 5-6개월 사용 가능**

**sonnet 모델 사용 시:**
- 1개 종목: ~$0.045
- 10개 종목 일일: ~$0.45
- 월간: ~$13.50

**권장:** haiku로 충분합니다.

### Q3: LLM 없이 사용해도 괜찮나요?

**A:** 네, 완벽히 괜찮습니다!

LLM 비활성화 시에도:
- ✅ 볼린저밴드 분석
- ✅ 일목균형표 분석
- ✅ 점수 기반 종합 평가
- ✅ 기본 템플릿 코멘트
- ✅ Markdown/HTML 리포트

**LLM은 "nice-to-have"** 추가 기능입니다.

### Q4: API 키를 코드에 하드코딩해도 되나요?

**A:** 절대 안 됩니다! ⚠️

```python
# ❌ 나쁜 예
client = anthropic.Anthropic(api_key="sk-ant-api-...")

# ✅ 좋은 예
import os
api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)
```

**이유:**
- Git에 실수로 푸시될 수 있음
- 키가 노출되면 누구나 당신의 크레딧 사용 가능
- 보안 모범 사례: 환경변수 사용

### Q5: API 키가 유출되었어요!

**A:** 즉시 조치:

1. [Anthropic Console](https://console.anthropic.com/settings/keys) 접속
2. 해당 키 삭제 (Revoke)
3. 새 키 생성
4. 환경변수 업데이트

## 🔐 보안 권장사항

1. **환경변수 사용**: 코드에 절대 하드코딩 금지
2. **Git 제외**: `.gitignore`에 키 파일 추가
3. **권한 관리**: 키를 파일로 저장 시 `chmod 600` 설정
4. **정기 교체**: 3-6개월마다 키 교체
5. **모니터링**: 사용량 주기적 확인

## 📊 성능 최적화

### 병렬 처리 (향후 구현)

현재는 종목별로 순차 처리하지만, 다음과 같이 개선 가능:

```python
# 미래 개선안
import asyncio
from anthropic import AsyncAnthropic

async def generate_comments_batch(stocks):
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    tasks = [generate_single(client, stock) for stock in stocks]
    return await asyncio.gather(*tasks)
```

### 캐싱

LLM 호출 결과도 데이터베이스에 캐싱하여 재실행 시 비용 절감:

```sql
-- 미래 개선안
CREATE TABLE llm_comments (
    id INTEGER PRIMARY KEY,
    code TEXT,
    date TEXT,
    comment TEXT,
    model TEXT,
    created_at TEXT
);
```

## 📚 추가 자료

- [Anthropic API 문서](https://docs.anthropic.com/claude/reference/)
- [Claude 모델 가격](https://www.anthropic.com/api)
- [Python SDK 저장소](https://github.com/anthropics/anthropic-sdk-python)

## 🤝 문제 해결

### LLM 호출이 실패해요

**체크리스트:**
1. API 키가 올바른지 확인: `echo $ANTHROPIC_API_KEY`
2. 인터넷 연결 확인
3. Anthropic 서비스 상태 확인: [status.anthropic.com](https://status.anthropic.com/)
4. 크레딧 잔액 확인: [console.anthropic.com](https://console.anthropic.com/settings/credits)

**디버그 모드:**
```python
# reporters/llm_generator.py에 추가
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 비용이 예상보다 많이 나와요

**원인:**
1. sonnet 모델 사용 (haiku의 15배)
2. 과도한 재실행 (캐시 미사용)
3. 많은 종목 분석

**해결:**
1. haiku 모델로 변경
2. 캐시 활용 (강제 새로고침 `-f` 플래그 최소화)
3. 종목 수 줄이기

---

**추가 질문이 있으시면 이슈를 열어주세요!** 🙋‍♂️
