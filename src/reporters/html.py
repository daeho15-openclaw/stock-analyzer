"""
HTML 리포트 생성기
"""

from datetime import datetime
from typing import List, Dict
from pathlib import Path


"""
HTML 리포트 생성기
"""

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
        
        # HTML 헤더 및 스타일
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{market_name} 주식 분석 리포트 - {date}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', 'Pretendard', sans-serif; background-color: #f8fafc; }}
    </style>
</head>
<body class="p-4 md:p-10">

    <div class="max-w-6xl mx-auto">
        <div class="mb-8 flex justify-between items-end">
            <div>
                <h1 class="text-3xl font-bold text-gray-900">주식 분석 리포트</h1>
                <p class="text-gray-500 mt-2">볼린저 밴드 및 일목균형표 기술적 지표 요약 ({market_name} 시장)</p>
            </div>
            <div class="text-sm text-gray-400">기준일: {date}</div>
        </div>

        <!-- 모바일 뷰 (카드 형태) -->
        <div class="md:hidden space-y-4 mb-8">
"""
        # 모바일 카드 생성
        for result in results:
            name = result['name']
            code = result['code']
            
            # 시장별 표시 순서 (미국은 코드가 메인)
            if market == 'us':
                main_text = code
                sub_text = name
            else:
                main_text = name
                sub_text = code

            # 평가 결과 추출
            evals = result.get('evaluations', {})
            bb = evals.get('bollinger', {})
            bb_emoji = bb.get('emoji', '❓')
            ich = evals.get('ichimoku', {})
            ich_emoji = ich.get('emoji', '❓')
            overall_emoji = result.get('overall_emoji', '❓')
            
            # 가격 정보
            current_price = result.get('current_price', 0)
            price_change_rate = result.get('price_change_rate', 0.0)
            
            currency = "원" if market == "kr" else "$"
            price_str = f"{current_price:,.0f}{currency}" if market == "kr" else f"${current_price:,.2f}"
            
            change_sign = "+" if price_change_rate > 0 else ""
            change_str = f"{change_sign}{price_change_rate:.2f}%"
            
            if price_change_rate > 0:
                price_color = "text-red-600"
            elif price_change_rate < 0:
                price_color = "text-blue-600"
            else:
                price_color = "text-gray-900"
                
            main_comment = bb.get('comment', '분석 중...')
            
            html += f"""
            <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
                <div class="flex justify-between items-start mb-3">
                    <div>
                        <div class="font-bold text-gray-900 text-lg">{main_text}</div>
                        <div class="text-xs text-gray-400 font-mono">{sub_text}</div>
                    </div>
                    <div class="text-right">
                        <div class="{price_color} font-bold">{price_str}</div>
                        <div class="{price_color} text-xs">{change_str}</div>
                    </div>
                </div>
                <div class="flex items-center gap-4 mb-3 bg-gray-50 p-3 rounded-lg">
                    <div class="flex flex-col items-center">
                        <span class="text-xs text-gray-500 mb-1">볼린저</span>
                        <span class="text-xl">{bb_emoji}</span>
                    </div>
                    <div class="flex flex-col items-center border-l border-gray-200 pl-4">
                        <span class="text-xs text-gray-500 mb-1">일목</span>
                        <span class="text-xl">{ich_emoji}</span>
                    </div>
                    <div class="flex flex-col items-center border-l border-gray-200 pl-4">
                        <span class="text-xs text-gray-500 mb-1">종합</span>
                        <span class="text-xl">{overall_emoji}</span>
                    </div>
                </div>
                <div class="text-sm text-gray-600">
                    {main_comment}
                </div>
            </div>
"""

        html += """
        </div>

        <!-- 데스크탑 뷰 (테이블 형태) -->
        <div class="hidden md:block bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
            <div class="overflow-x-auto">
                <table class="w-full border-collapse text-left">
                    <thead>
                        <tr class="bg-slate-50 border-b border-gray-100">
                            <th class="px-6 py-4 font-semibold text-gray-700">종목명</th>
                            <th class="px-6 py-4 font-semibold text-gray-700 text-center">볼린저밴드</th>
                            <th class="px-6 py-4 font-semibold text-gray-700 text-center">일목균형표</th>
                            <th class="px-6 py-4 font-semibold text-gray-700">평가 및 의견</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50">
"""
        
        # 데스크탑 행 생성
        for result in results:
            name = result['name']
            code = result['code']
            
            # 시장별 표시 순서
            if market == 'us':
                main_text = code
                sub_text = name
            else:
                main_text = name
                sub_text = code
            
            # 평가 결과 추출
            evals = result.get('evaluations', {})
            
            # 볼린저 밴드
            bb = evals.get('bollinger', {})
            bb_emoji = bb.get('emoji', '❓')
            
            # 일목균형표
            ich = evals.get('ichimoku', {})
            ich_emoji = ich.get('emoji', '❓')
            
            # 종합 평가
            overall_emoji = result.get('overall_emoji', '❓')
            
            # 가격 정보
            current_price = result.get('current_price', 0)
            price_change = result.get('price_change', 0)
            price_change_rate = result.get('price_change_rate', 0.0)
            
            # 가격 포맷팅
            currency = "원" if market == "kr" else "$"
            price_str = f"{current_price:,.0f}{currency}" if market == "kr" else f"${current_price:,.2f}"
            
            change_sign = "+" if price_change_rate > 0 else ""
            change_str = f"{change_sign}{price_change_rate:.2f}%"
            
            # 등락 색상 (한국 기준: 상승=빨강, 하락=파랑)
            if price_change_rate > 0:
                price_color = "text-red-600"
                change_color = "text-red-600"
            elif price_change_rate < 0:
                price_color = "text-blue-600"
                change_color = "text-blue-600"
            else:
                price_color = "text-gray-900"
                change_color = "text-gray-500"
                
            # 코멘트 선정 (가장 중요한 코멘트 하나)
            # 1. 볼린저 코멘트 사용
            main_comment = bb.get('comment', '분석 중...')
            
            html += f"""
                        <tr class="hover:bg-blue-50/30 transition-colors">
                            <td class="px-6 py-5">
                                <div class="font-bold text-gray-900 text-lg">{main_text}</div>
                                <div class="text-xs text-gray-400 font-mono">{sub_text}</div>
                            </td>
                            <td class="px-6 py-5 text-center text-xl">{bb_emoji}</td>
                            <td class="px-6 py-5 text-center text-xl">{ich_emoji}</td>
                            <td class="px-6 py-5">
                                <span class="{price_color} font-bold block">{price_str} ({change_str})</span>
                                <p class="text-sm text-gray-500 mt-1">{main_comment} {overall_emoji}</p>
                            </td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="mt-6 text-center text-xs text-gray-400 leading-relaxed">
            본 데이터는 기술적 분석 결과일 뿐, 투자의 책임은 본인에게 있습니다.<br>
            볼린저 밴드는 20일 이동평균선과 ±2표준편차&#40;&sigma;&#41;를 기준으로 계산되었습니다.
        </div>
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
    # 테스트용 데이터
    sample_results = [
        {
            'code': '005930', 
            'name': '삼성전자', 
            'current_price': 75000, 
            'price_change': 1500,
            'price_change_rate': 2.04,
            'evaluations': {
                'bollinger': {'emoji': '👌', 'details': {'position': 45}, 'comment': '중립'},
                'ichimoku': {'emoji': '☁️'}
            },
            'overall_emoji': '👌'
        },
        {
            'code': '000660', 
            'name': 'SK하이닉스', 
            'current_price': 140000, 
            'price_change': -2000,
            'price_change_rate': -1.41,
            'evaluations': {
                'bollinger': {'emoji': '🔥', 'details': {'position': 90}, 'comment': '과매수 주의'},
                'ichimoku': {'emoji': '📈'}
            },
            'overall_emoji': '🔥'
        }
    ]
    
    reporter = HTMLReporter()
    print(reporter.generate('kr', '2026-02-10', sample_results))

