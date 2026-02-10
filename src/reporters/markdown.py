"""
마크다운 리포트 생성기
"""

from datetime import datetime
from typing import List, Dict
from pathlib import Path
from .llm_generator import ClaudeCommentGenerator


class MarkdownReporter:
    """마크다운 형식 리포트 생성기"""
    
    def __init__(self, config: Dict = None):
        """
        Args:
            config: 리포트 설정
        """
        self.config = config or {}
        self.output_dir = Path(self.config.get('output_dir', '../reports'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # LLM 생성기 초기화
        use_llm = self.config.get('use_llm', False)
        if use_llm:
            llm_model = self.config.get('llm_model', 'claude-3-5-haiku-20241022')
            self.llm_generator = ClaudeCommentGenerator(model=llm_model)
        else:
            self.llm_generator = None
            print("ℹ️  LLM 기능이 비활성화되었습니다.")
    
    def generate(self, market: str, date: str, results: List[Dict]) -> str:
        """
        리포트 생성
        
        Args:
            market: 시장 (kr, us)
            date: 날짜 (YYYY-MM-DD)
            results: 분석 결과 리스트
                [
                    {
                        'code': '005930',
                        'name': '삼성전자',
                        'current_price': 165800,
                        'evaluations': {
                            'bollinger': {'score': 1.0, 'emoji': '🔴', 'comment': '...'},
                            'ichimoku': {'score': 4.0, 'emoji': '🟢', 'comment': '...'}
                        },
                        'overall_score': 2.5,
                        'overall_emoji': '👌'
                    },
                    ...
                ]
        
        Returns:
            리포트 마크다운 문자열
        """
        market_name = "한국" if market == "kr" else "미국"
        
        # 헤더
        lines = [
            f"# 📊 {market_name} 주식 분석 리포트",
            f"**날짜**: {date}",
            "",
            "---",
            ""
        ]
        
        # 테이블 헤더
        lines.extend([
            "| 종목명 | 볼린저밴드 | 일목균형표 | 평가 | 기타 |",
            "|--------|-----------|-----------|------|------|"
        ])
        
        # 종목별 행
        for result in results:
            name = result['name']
            evals = result['evaluations']
            
            # 볼린저 밴드
            bb = evals.get('bollinger', {})
            bb_emoji = bb.get('emoji', '⚠️')
            
            # 일목균형표
            ich = evals.get('ichimoku', {})
            ich_emoji = ich.get('emoji', '⚠️')
            
            # 종합 평가
            overall = result.get('overall_emoji', '❓')
            
            # 기타 정보
            price = result.get('current_price', 0)
            price_str = f"{price:,.0f}원" if market == "kr" else f"${price:,.2f}"
            
            bb_comment = bb.get('comment', '')[:20]
            ich_comment = ich.get('comment', '')[:20]
            
            other = f"💰 {price_str} | {bb_comment} | {ich_comment}"
            
            lines.append(f"| {name} | {bb_emoji} | {ich_emoji} | {overall} | {other} |")
        
        # 종합 평가
        lines.extend([
            "",
            "---",
            "",
            "## 📈 종합 평가",
            ""
        ])
        
        # 최고 평가 종목
        best = max(results, key=lambda x: x.get('overall_score', 0), default=None)
        if best:
            lines.append(f"- **최고 평가** {best['overall_emoji']}: {best['name']}")
        
        # 긍정적 종목 (score >= 2.75)
        positive = [r for r in results if r.get('overall_score', 0) >= 2.75]
        if positive:
            names = ", ".join([r['name'] for r in positive])
            lines.append(f"- **긍정적** 👍: {names}")
        
        # 중립 종목
        neutral = [r for r in results if 2.0 <= r.get('overall_score', 0) < 2.75]
        if neutral:
            names = ", ".join([r['name'] for r in neutral])
            lines.append(f"- **중립** 👌: {names}")
        
        # 부정적 종목
        negative = [r for r in results if r.get('overall_score', 0) < 2.0]
        if negative:
            names = ", ".join([r['name'] for r in negative])
            lines.append(f"- **주의** 👎: {names}")
        
        # 시황 요약
        lines.extend([
            "",
            "## 💡 시황 요약",
            ""
        ])
        
        # 통계
        total = len(results)
        strong_buy = len([r for r in results if r.get('overall_score', 0) >= 3.5])
        buy = len([r for r in results if 2.75 <= r.get('overall_score', 0) < 3.5])
        hold = len([r for r in results if 2.0 <= r.get('overall_score', 0) < 2.75])
        sell = len([r for r in results if r.get('overall_score', 0) < 2.0])
        
        lines.append(f"- 총 {total}개 종목 분석")
        if strong_buy > 0:
            lines.append(f"- 강한 매수 신호 🔥: {strong_buy}개")
        if buy > 0:
            lines.append(f"- 매수 신호 👍: {buy}개")
        if hold > 0:
            lines.append(f"- 중립/관망 👌: {hold}개")
        if sell > 0:
            lines.append(f"- 주의/매도 고려 👎: {sell}개")
        
        # LLM 기반 시황 분석 (활성화된 경우)
        if self.llm_generator and self.llm_generator.enabled:
            lines.extend(["", "### 💬 시장 분석"])
            market_summary = self.llm_generator.generate_market_summary(results, market)
            lines.append(f"{market_summary}")
        
        # 종목별 상세 분석 (LLM 활성화 시)
        if self.llm_generator and self.llm_generator.enabled:
            lines.extend(["", "---", "", "## 📝 종목별 상세 분석", ""])
            
            for result in results:
                stock_comment = self.llm_generator.generate_stock_analysis(result)
                price = result.get('current_price', 0)
                change_rate = result.get('price_change_rate', 0)
                price_str = f"{price:,.0f}원" if market == "kr" else f"${price:,.2f}"
                
                lines.extend([
                    f"### {result['overall_emoji']} {result['name']}",
                    f"**현재가**: {price_str} ({change_rate:+.2f}%)",
                    "",
                    stock_comment,
                    ""
                ])
        
        # 푸터
        lines.extend([
            "",
            "---",
            "",
            "⚠️ *이는 기술적 분석 참고 자료이며, 투자 판단은 본인 책임하에 진행하세요.*"
        ])
        
        return "\n".join(lines)
    
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
        filename = f"{market}_{date}.md"
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
    
    reporter = MarkdownReporter()
    report = reporter.generate("kr", "2026-02-10", sample_results)
    print(report)
