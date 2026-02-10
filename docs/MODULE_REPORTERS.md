# 리포트 생성 모듈 (Reporters)

## 개요

분석 결과를 사용자가 읽기 쉬운 형식의 리포트로 생성하는 모듈입니다. Markdown, HTML 등 다양한 형식을 지원하며, 확장이 용이합니다.

## 위치
```
src/reporters/
├── __init__.py
├── markdown.py       # Markdown 리포터
└── html.py          # HTML 리포터
```

## 공통 인터페이스

모든 Reporter는 다음 메서드를 구현해야 합니다:

### generate()
```python
def generate(self, market: str, date: str, results: List[Dict]) -> str
```

**파라미터**:
- `market`: 시장 (kr, us)
- `date`: 날짜 (YYYY-MM-DD)
- `results`: 분석 결과 리스트

**반환값**:
- 리포트 문자열 (Markdown, HTML 등)

### save()
```python
def save(self, market: str, date: str, content: str) -> str
```

**파라미터**:
- `market`: 시장
- `date`: 날짜
- `content`: 리포트 내용

**반환값**:
- 저장된 파일 경로

## 분석 결과 형식

Reporter가 받는 `results` 리스트의 구조:

```python
[
    {
        'code': '005930',
        'name': '삼성전자',
        'current_price': 165800,
        'evaluations': {
            'bollinger': {
                'score': 1.0,
                'emoji': '🔴',
                'comment': '과매수 80%, 매도 고려'
            },
            'ichimoku': {
                'score': 4.0,
                'emoji': '🟢',
                'comment': '골든크로스, 강세'
            }
        },
        'overall_score': 2.5,
        'overall_emoji': '👌'
    },
    ...
]
```

## MarkdownReporter

### 파일
`src/reporters/markdown.py`

### 목적
분석 결과를 Markdown 형식의 리포트로 생성

### 초기화
```python
reporter = MarkdownReporter({
    'output_dir': 'reports'
})
```

### 리포트 구조

```markdown
# 📊 한국 주식 분석 리포트
**날짜**: 2026-02-10

---

| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |
|--------|-----------|-----------|------|------|
| 삼성전자 | 🔴 | 🟢 | 👌 | 💰 165,800원 | 과매수 80% | 골든크로스 |
| 한화오션 | 🟢 | 🟡 | 🔥🔥 | 💰 130,900원 | 하단 근처 7% | 중립 |

---

## 📈 종합 평가

- **최고 평가** 🔥🔥: 한화오션
- **긍정적** 👍: 한화오션
- **중립** 👌: 삼성전자

## 💡 시황 요약

- 총 2개 종목 분석
- 강한 매수 신호 🔥: 1개
- 중립/관망 👌: 1개

---

⚠️ *이는 기술적 분석 참고 자료이며, 투자 판단은 본인 책임하에 진행하세요.*
```

### generate() 로직

```python
def generate(self, market: str, date: str, results: List[Dict]) -> str:
    market_name = "한국" if market == "kr" else "미국"
    
    lines = [
        f"# 📊 {market_name} 주식 분석 리포트",
        f"**날짜**: {date}",
        "",
        "---",
        "",
        # 테이블 헤더
        "| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |",
        "|--------|-----------|-----------|------|------|"
    ]
    
    # 종목별 행
    for result in results:
        name = result['name']
        evals = result['evaluations']
        
        bb_emoji = evals.get('bollinger', {}).get('emoji', '⚠️')
        ich_emoji = evals.get('ichimoku', {}).get('emoji', '⚠️')
        overall = result.get('overall_emoji', '❓')
        
        price = result.get('current_price', 0)
        price_str = f"{price:,.0f}원" if market == "kr" else f"${price:,.2f}"
        
        bb_comment = evals.get('bollinger', {}).get('comment', '')[:20]
        ich_comment = evals.get('ichimoku', {}).get('comment', '')[:20]
        
        other = f"💰 {price_str} | {bb_comment} | {ich_comment}"
        
        lines.append(f"| {name} | {bb_emoji} | {ich_emoji} | {overall} | {other} |")
    
    # 종합 평가 섹션
    lines.extend([
        "",
        "---",
        "",
        "## 📈 종합 평가",
        ""
    ])
    
    # 최고 평가
    best = max(results, key=lambda x: x.get('overall_score', 0), default=None)
    if best:
        lines.append(f"- **최고 평가** {best['overall_emoji']}: {best['name']}")
    
    # 긍정적 종목 (score >= 2.75)
    positive = [r for r in results if r.get('overall_score', 0) >= 2.75]
    if positive:
        names = ", ".join([r['name'] for r in positive])
        lines.append(f"- **긍정적** 👍: {names}")
    
    # ... (중립, 주의)
    
    # 시황 요약
    lines.extend([
        "",
        "## 💡 시황 요약",
        "",
        f"- 총 {len(results)}개 종목 분석"
    ])
    
    # 통계
    strong_buy = len([r for r in results if r.get('overall_score', 0) >= 3.5])
    if strong_buy > 0:
        lines.append(f"- 강한 매수 신호 🔥: {strong_buy}개")
    
    # 푸터
    lines.extend([
        "",
        "---",
        "",
        "⚠️ *이는 기술적 분석 참고 자료이며, 투자 판단은 본인 책임하에 진행하세요.*"
    ])
    
    return "\n".join(lines)
```

### save() 로직

```python
def save(self, market: str, date: str, content: str) -> str:
    filename = f"{market}_{date}.md"
    filepath = self.output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 리포트 저장: {filepath}")
    return str(filepath)
```

### 예시
```python
from reporters import MarkdownReporter

reporter = MarkdownReporter({'output_dir': 'reports'})

results = [
    {
        'code': '005930',
        'name': '삼성전자',
        'current_price': 165800,
        'evaluations': {
            'bollinger': {'score': 1.0, 'emoji': '🔴', 'comment': '과매수'},
            'ichimoku': {'score': 4.0, 'emoji': '🟢', 'comment': '골든크로스'}
        },
        'overall_score': 2.5,
        'overall_emoji': '👌'
    }
]

report = reporter.generate("kr", "2026-02-10", results)
filepath = reporter.save("kr", "2026-02-10", report)
```

## HTMLReporter

### 파일
`src/reporters/html.py`

### 목적
분석 결과를 HTML 형식의 리포트로 생성 (브라우저에서 보기 좋음)

### 초기화
```python
reporter = HTMLReporter({
    'output_dir': 'reports'
})
```

### HTML 템플릿

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>한국 주식 분석 리포트 - 2026-02-10</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        th {
            background-color: #4CAF50;
            color: white;
            padding: 12px;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .emoji {
            font-size: 1.5em;
        }
    </style>
</head>
<body>
    <h1>📊 한국 주식 분석 리포트</h1>
    <div class="meta">
        <strong>날짜:</strong> 2026-02-10
    </div>
    
    <table>
        <thead>
            <tr>
                <th>종목명</th>
                <th>볼린저밴드</th>
                <th>일목균형표</th>
                <th>평가</th>
                <th>기타</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>삼성전자</strong></td>
                <td class="emoji">🔴</td>
                <td class="emoji">🟢</td>
                <td class="emoji">👌</td>
                <td>💰 165,800원<br>과매수 80%<br>골든크로스</td>
            </tr>
            ...
        </tbody>
    </table>
    
    <div class="summary">
        <h2>📈 종합 평가</h2>
        <ul>
            <li><strong>최고 평가</strong> 🔥🔥: 한화오션</li>
            <li><strong>긍정적</strong> 👍: 한화오션</li>
        </ul>
    </div>
    
    <div class="footer">
        ⚠️ 이는 기술적 분석 참고 자료이며, 투자 판단은 본인 책임하에 진행하세요.
    </div>
</body>
</html>
```

### generate() 로직

```python
def generate(self, market: str, date: str, results: List[Dict]) -> str:
    market_name = "한국" if market == "kr" else "미국"
    
    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{market_name} 주식 분석 리포트 - {date}</title>
    <style>
        /* CSS 스타일 */
    </style>
</head>
<body>
    <h1>📊 {market_name} 주식 분석 리포트</h1>
    <div class="meta">
        <strong>날짜:</strong> {date}
    </div>
    
    <table>
        <thead>
            <tr>
                <th>종목명</th>
                <th>볼린저밴드</th>
                <th>일목균형표</th>
                <th>평가</th>
                <th>기타</th>
            </tr>
        </thead>
        <tbody>
"""
    
    # 종목별 행
    for result in results:
        name = result['name']
        evals = result['evaluations']
        
        bb_emoji = evals.get('bollinger', {}).get('emoji', '⚠️')
        ich_emoji = evals.get('ichimoku', {}).get('emoji', '⚠️')
        overall = result.get('overall_emoji', '❓')
        
        price = result.get('current_price', 0)
        price_str = f"{price:,.0f}원" if market == "kr" else f"${price:,.2f}"
        
        bb_comment = evals.get('bollinger', {}).get('comment', '')
        ich_comment = evals.get('ichimoku', {}).get('comment', '')
        
        other = f"💰 {price_str}<br>{bb_comment}<br>{ich_comment}"
        
        html += f"""
            <tr>
                <td><strong>{name}</strong></td>
                <td class="emoji">{bb_emoji}</td>
                <td class="emoji">{ich_emoji}</td>
                <td class="emoji">{overall}</td>
                <td>{other}</td>
            </tr>
"""
    
    html += """
        </tbody>
    </table>
    
    <div class="summary">
        <h2>📈 종합 평가</h2>
        <ul>
"""
    
    # 종합 평가
    best = max(results, key=lambda x: x.get('overall_score', 0), default=None)
    if best:
        html += f"            <li><strong>최고 평가</strong> {best['overall_emoji']}: {best['name']}</li>\n"
    
    html += """
        </ul>
    </div>
    
    <div class="footer">
        ⚠️ 이는 기술적 분석 참고 자료이며, 투자 판단은 본인 책임하에 진행하세요.
    </div>
</body>
</html>
"""
    
    return html
```

## 메인 프로그램 연동

### Reporter 선택 로직
```python
# main.py

report_format = self.report_config.get('format', 'markdown')

if report_format == 'html':
    self.reporter = HTMLReporter(self.report_config)
else:
    self.reporter = MarkdownReporter(self.report_config)
```

### 리포트 생성 및 저장
```python
def generate_report(self, market: str, date: str, results: List[Dict]) -> str:
    # 리포트 생성
    content = self.reporter.generate(market, date, results)
    
    # 파일 저장
    filepath = self.reporter.save(market, date, content)
    
    # DB 저장
    report_format = self.report_config.get('format', 'markdown')
    self.db.save_report(market, date, content, report_format)
    
    return filepath
```

## 새 Reporter 추가 방법

### 1. 새 파일 생성
```python
# src/reporters/pdf.py

from typing import List, Dict
from pathlib import Path

class PDFReporter:
    """PDF 형식 리포터"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.output_dir = Path(self.config.get('output_dir', 'reports'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, market: str, date: str, results: List[Dict]) -> bytes:
        """
        PDF 리포트 생성
        
        Returns:
            PDF 바이너리 데이터
        """
        # PDF 생성 로직 (예: reportlab 사용)
        # ...
        return pdf_bytes
    
    def save(self, market: str, date: str, content: bytes) -> str:
        """PDF 파일 저장"""
        filename = f"{market}_{date}.pdf"
        filepath = self.output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(content)
        
        print(f"✅ 리포트 저장: {filepath}")
        return str(filepath)
```

### 2. __init__.py에 등록
```python
# src/reporters/__init__.py

from .markdown import MarkdownReporter
from .html import HTMLReporter
from .pdf import PDFReporter

__all__ = ['MarkdownReporter', 'HTMLReporter', 'PDFReporter']
```

### 3. 설정 파일에 추가
```yaml
# config/report.yml

format: pdf  # markdown, html, pdf
```

### 4. main.py에서 선택
```python
# src/main.py

report_format = self.report_config.get('format', 'markdown')

if report_format == 'pdf':
    self.reporter = PDFReporter(self.report_config)
elif report_format == 'html':
    self.reporter = HTMLReporter(self.report_config)
else:
    self.reporter = MarkdownReporter(self.report_config)
```

## 리포트 커스터마이징

### 설정 옵션
```yaml
# config/report.yml

format: markdown
output_dir: "reports"
filename_format: "{market}_{date}.{ext}"

include:
  summary: true       # 종합 평가 포함
  table: true         # 종목별 표 포함
  details: true       # 상세 분석 포함
  chart_data: false   # 차트 데이터 (추후)

table_columns:
  - "종목명"
  - "볼린저밴드"
  - "일목균형표"
  - "평가"
  - "기타"

language: "ko"
timezone: "Asia/Seoul"
```

### 템플릿 엔진 사용 (선택)
```python
from jinja2 import Template

template = Template("""
# {{ title }}
**날짜**: {{ date }}

{% for result in results %}
| {{ result.name }} | {{ result.evaluations.bollinger.emoji }} | ...
{% endfor %}
""")

content = template.render(title="주식 분석", date="2026-02-10", results=results)
```

## 테스트

### 단위 테스트
```python
def test_markdown_generate():
    reporter = MarkdownReporter()
    
    results = [
        {'code': '005930', 'name': '삼성전자', 'current_price': 165800,
         'evaluations': {'bollinger': {'emoji': '🔴'}},
         'overall_emoji': '👌'}
    ]
    
    report = reporter.generate("kr", "2026-02-10", results)
    
    assert "삼성전자" in report
    assert "165,800원" in report
    assert "👌" in report
```

### 통합 테스트
```python
def test_full_workflow():
    # 분석 결과 생성
    results = run_analysis("kr", "2026-02-10")
    
    # Markdown 리포트
    md_reporter = MarkdownReporter()
    md_report = md_reporter.generate("kr", "2026-02-10", results)
    md_reporter.save("kr", "2026-02-10", md_report)
    
    # HTML 리포트
    html_reporter = HTMLReporter()
    html_report = html_reporter.generate("kr", "2026-02-10", results)
    html_reporter.save("kr", "2026-02-10", html_report)
    
    # 파일 존재 확인
    assert os.path.exists("reports/kr_2026-02-10.md")
    assert os.path.exists("reports/kr_2026-02-10.html")
```

---

**문서 버전**: 1.0  
**최종 수정**: 2026-02-10
