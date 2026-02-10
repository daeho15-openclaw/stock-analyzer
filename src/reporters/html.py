"""
HTML 리포트 생성기
"""

from datetime import datetime
from typing import List, Dict
from pathlib import Path


class HTMLReporter:
    """HTML 형식 리포트 생성기"""
    
    def __init__(self, config: Dict = None):
        """
        Args:
            config: 리포트 설정
        """
        self.config = config or {}
        self.output_dir = Path(self.config.get('output_dir', '../reports'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, market: str, date: str, results: List[Dict]) -> str:
        """
        HTML 리포트 생성
        
        Args:
            market: 시장 (kr, us)
            date: 날짜
            results: 분석 결과 리스트
        
        Returns:
            HTML 문자열
        """
        market_name = "한국" if market == "kr" else "미국"
        
        # HTML 템플릿
        html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{market_name} 주식 분석 리포트 - {date}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .meta {{
            color: #666;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .summary h2 {{
            color: #4CAF50;
            margin-top: 0;
        }}
        .summary ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        .summary li {{
            padding: 5px 0;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        .emoji {{
            font-size: 1.5em;
        }}
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
            
            bb = evals.get('bollinger', {})
            bb_emoji = bb.get('emoji', '⚠️')
            
            ich = evals.get('ichimoku', {})
            ich_emoji = ich.get('emoji', '⚠️')
            
            overall = result.get('overall_emoji', '❓')
            
            price = result.get('current_price', 0)
            price_str = f"{price:,.0f}원" if market == "kr" else f"${price:,.2f}"
            
            bb_comment = bb.get('comment', '')
            ich_comment = ich.get('comment', '')
            
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
        
        positive = [r for r in results if r.get('overall_score', 0) >= 2.75]
        if positive:
            names = ", ".join([r['name'] for r in positive])
            html += f"            <li><strong>긍정적</strong> 👍: {names}</li>\n"
        
        neutral = [r for r in results if 2.0 <= r.get('overall_score', 0) < 2.75]
        if neutral:
            names = ", ".join([r['name'] for r in neutral])
            html += f"            <li><strong>중립</strong> 👌: {names}</li>\n"
        
        negative = [r for r in results if r.get('overall_score', 0) < 2.0]
        if negative:
            names = ", ".join([r['name'] for r in negative])
            html += f"            <li><strong>주의</strong> 👎: {names}</li>\n"
        
        html += """
        </ul>
    </div>
    
    <div class="summary">
        <h2>💡 시황 요약</h2>
        <ul>
"""
        
        # 통계
        total = len(results)
        strong_buy = len([r for r in results if r.get('overall_score', 0) >= 3.5])
        buy = len([r for r in results if 2.75 <= r.get('overall_score', 0) < 3.5])
        hold = len([r for r in results if 2.0 <= r.get('overall_score', 0) < 2.75])
        sell = len([r for r in results if r.get('overall_score', 0) < 2.0])
        
        html += f"            <li>총 {total}개 종목 분석</li>\n"
        if strong_buy > 0:
            html += f"            <li>강한 매수 신호 🔥: {strong_buy}개</li>\n"
        if buy > 0:
            html += f"            <li>매수 신호 👍: {buy}개</li>\n"
        if hold > 0:
            html += f"            <li>중립/관망 👌: {hold}개</li>\n"
        if sell > 0:
            html += f"            <li>주의/매도 고려 👎: {sell}개</li>\n"
        
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
    
    def save(self, market: str, date: str, content: str) -> str:
        """
        리포트 파일로 저장
        
        Args:
            market: 시장
            date: 날짜
            content: 리포트 내용
        
        Returns:
            저장된 파일 경로
        """
        filename = f"{market}_{date}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 리포트 저장: {filepath}")
        return str(filepath)


if __name__ == "__main__":
    # 테스트
    sample_results = [
        {
            'code': '005930',
            'name': '삼성전자',
            'current_price': 165800,
            'evaluations': {
                'bollinger': {'score': 1.0, 'emoji': '🔴', 'comment': '과매수 80%, 매도 고려'},
                'ichimoku': {'score': 4.0, 'emoji': '🟢', 'comment': '골든크로스, 강세'}
            },
            'overall_score': 2.5,
            'overall_emoji': '👌'
        }
    ]
    
    reporter = HTMLReporter()
    report = reporter.generate("kr", "2026-02-10", sample_results)
    reporter.save("kr", "2026-02-10", report)
