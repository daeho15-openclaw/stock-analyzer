"""
HTML 리포트 생성기
"""

from typing import List, Dict
from pathlib import Path
from .llm_generator import ClaudeCommentGenerator


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
        
        # LLM 생성기 초기화
        use_llm = self.config.get('use_llm', False)
        if use_llm:
            llm_model = self.config.get('llm_model', 'claude-3-5-haiku-20241022')
            use_openclaw_token = self.config.get('use_openclaw_token', False)
            self.llm_generator = ClaudeCommentGenerator(
                model=llm_model,
                use_openclaw_token=use_openclaw_token
            )
        else:
            self.llm_generator = None
            print("ℹ️  LLM 기능이 비활성화되었습니다.")
    
    def _get_score(self, emoji: str) -> float:
        """이모지를 점수로 변환"""
        scores = {
            '🚀': 4.0, '☀️': 3.5, '🌤️': 3.0, '☁️': 2.5,
            '🌧️': 2.0, '⛈️': 1.5, '🚨': 1.0, '❓': 0.0
        }
        return scores.get(emoji, 0.0)

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
        formatted_date = date.replace('-', '.') + '.'
        
        # LLM 개별 종목 분석
        if self.llm_generator and self.llm_generator.enabled:
            print("🤖 Claude AI가 종목 분석을 시작합니다...")
            for result in results:
                if 'llm_analysis' not in result:
                    try:
                        result['llm_analysis'] = self.llm_generator.generate_stock_analysis(result)
                    except Exception as e:
                        print(f"⚠️ 종목 분석 실패 ({result['name']}): {e}")
                        result['llm_analysis'] = ""
        
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
        body {{ 
            font-family: 'Inter', 'Pretendard', sans-serif; 
            background-color: #f8fafc; 
        }}

        /* 데스크탑 AI 박스 스타일 */
        .ai-box-desktop {{
            height: 6.5rem;
            overflow: hidden;
            position: relative;
            transition: height 0.3s ease;
        }}

        .ai-box-desktop.expanded {{
            height: auto;
            overflow: visible;
        }}

        .ai-box-desktop .ai-content {{
            display: -webkit-box;
            -webkit-line-clamp: 3;
            line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .ai-box-desktop.expanded .ai-content {{
            -webkit-line-clamp: unset;
            line-clamp: unset;
            overflow: visible;
        }}

        /* 짧은 텍스트 수직 중앙 */
        .ai-box-desktop:not(.has-overflow) {{
            display: flex;
            align-items: center;
        }}

        .ai-box-desktop:not(.has-overflow) .ai-content {{
            display: block;
            -webkit-line-clamp: unset;
            line-clamp: unset;
        }}

        .ai-toggle-desktop {{
            display: none;
        }}

        /* 오버플로우 발생 시 하단에 그라데이션과 함께 버튼 표시 */
        .ai-box-desktop.has-overflow .ai-toggle-desktop {{
            display: flex;
            justify-content: center;
            align-items: flex-end;
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2.5rem;
            background: linear-gradient(to bottom, transparent, #eef2ff 60%);
            padding-bottom: 0.25rem;
            color: #6366f1;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
        }}

        .ai-box-desktop.has-overflow .ai-toggle-desktop:hover {{
            color: #4f46e5;
        }}

        /* 펼쳐진 상태에서는 하단에 일반 텍스트 버튼으로 표시 */
        .ai-box-desktop.expanded .ai-toggle-desktop {{
            position: static;
            height: auto;
            background: none;
            justify-content: flex-end;
            padding-bottom: 0;
            margin-top: 0.5rem;
            width: 100%;
        }}

        /* 모바일 AI 텍스트 스타일 */
        .ai-text-mobile {{
            font-size: 0.875rem;
            color: #312e81; /* text-indigo-900 */
            line-height: 1.6;
        }}
        .inline-btn {{
            color: #4f46e5;
            font-weight: 600;
            font-size: 0.875rem;
            margin-left: 0.25rem;
            cursor: pointer;
        }}
    </style>
</head>
<body class="p-4 md:p-10">

    <div class="max-w-6xl mx-auto">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900">주식 분석 리포트 <span class="text-2xl font-semibold text-gray-500">({formatted_date})</span></h1>
            <p class="text-gray-500 mt-2">볼린저 밴드 및 일목균형표 기술적 지표 요약 ({market_name} 시장)</p>
        </div>

        <!-- 모바일 뷰 (카드 형태) -->
        <div class="md:hidden">
            <!-- 정렬 버튼 -->
            <div class="flex justify-end mb-3">
                <button id="mobileSortToggle" onclick="toggleSort('mobile')" class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-all shadow-sm">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/></svg>
                    <span id="mobileSortLabel">종합점수</span>
                </button>
            </div>

            <div class="space-y-4 mb-8" id="mobileBody">
"""
        # 모바일 카드 생성
        for idx, result in enumerate(results):
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
            bb = evals.get('bollinger', {})
            bb_emoji = bb.get('emoji', '❓')
            ich = evals.get('ichimoku', {})
            ich_emoji = ich.get('emoji', '❓')
            overall_emoji = result.get('overall_emoji', '❓')
            
            # 점수 계산
            overall_score = result.get('overall_score', self._get_score(overall_emoji))
            
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
            bb_pos = bb.get('details', {}).get('position')
            if bb_pos is not None:
                main_comment += f" ({bb_pos:.0f}%)"
            
            ai_analysis_text = result.get('llm_analysis', '')
            
            # AI 분석이 있으면 data 속성으로 전달
            ai_attr = f'data-full="{ai_analysis_text}"' if ai_analysis_text else ''
            
            html += f"""
                <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100" data-score="{overall_score:.2f}" data-order="{idx}">
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
                    
                    <div class="bg-gray-50 p-4 rounded-lg mb-3 flex items-center lg:gap-4 gap-3">
                        <div class="flex flex-col items-center min-w-[3rem]">
                            <span class="text-xs text-gray-500 mb-1 font-medium">BOLL</span>
                            <span class="text-2xl">{bb_emoji}</span>
                        </div>
                        <div class="h-8 w-px bg-gray-200"></div>
                        <div class="flex flex-col items-center min-w-[3rem]">
                            <span class="text-xs text-gray-500 mb-1 font-medium">IC</span>
                            <span class="text-2xl">{ich_emoji}</span>
                        </div>
                        <div class="h-8 w-px bg-gray-200"></div>
                        <div class="flex-1 min-w-0">
                            <span class="block text-xs text-gray-500 mb-1 font-medium">평가</span>
                            <div class="flex items-center gap-2">
                                <span class="text-2xl flex-shrink-0">{overall_emoji}</span>
                                <div class="text-sm text-gray-700 font-medium truncate leading-snug">
                                    {main_comment} <span class="text-gray-400 font-normal">({overall_score:.1f}점)</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """
            
            if ai_analysis_text:
                html += f"""
                    <div class="mt-3 pt-3">
                        <div class="bg-indigo-50 p-3 rounded-lg ai-text-mobile" {ai_attr}>
                            <!-- JS가 내용을 채움 -->
                        </div>
                    </div>
                """
                
            html += """
                </div>
"""

        html += """
            </div>
        </div>

        <!-- 데스크탑 뷰 (테이블 형태) -->
        <div class="hidden md:block">
            <!-- 정렬 버튼 -->
            <div class="flex justify-end mb-3">
                <button id="desktopSortToggle" onclick="toggleSort('desktop')" class="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/></svg>
                    <span id="desktopSortLabel">종합점수</span>
                </button>
            </div>

            <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
                <div class="overflow-x-auto">
                    <table class="w-full border-collapse text-left" id="stockTable">
                        <thead>
                            <tr class="bg-slate-50 border-b border-gray-100">
                                <th class="px-6 py-4 font-semibold text-gray-700 text-center min-w-[140px]">종목명</th>
                                <th class="px-5 py-4 font-semibold text-gray-700 text-center min-w-[130px]">현재가</th>
                                <th class="px-4 py-4 font-semibold text-gray-700 text-center w-20">BOLL</th>
                                <th class="px-4 py-4 font-semibold text-gray-700 text-center w-20">IC</th>
                                <th class="px-6 py-4 font-semibold text-gray-700 text-center">평가 및 의견</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-50" id="stockBody">
"""
        
        # 데스크탑 행 생성
        for idx, result in enumerate(results):
            name = result['name']
            code = result['code']
            
            if market == 'us':
                main_text = code
                sub_text = name
            else:
                main_text = name
                sub_text = code
            
            evals = result.get('evaluations', {})
            bb = evals.get('bollinger', {})
            bb_emoji = bb.get('emoji', '❓')
            ich = evals.get('ichimoku', {})
            ich_emoji = ich.get('emoji', '❓')
            overall_emoji = result.get('overall_emoji', '❓')
            
            overall_score = result.get('overall_score', self._get_score(overall_emoji))
            
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
            
            # AI 분석 텍스트
            ai_analysis = result.get('llm_analysis', '')
            ai_html = ""
            if ai_analysis:
                ai_html = f"""
                                    <div class="text-sm text-indigo-800 bg-indigo-50 p-2.5 rounded-lg leading-relaxed ai-box-desktop">
                                        <div class="ai-content">🤖 {ai_analysis}</div>
                                        <div onclick="toggleDesktop(this)" class="ai-toggle-desktop">더보기</div>
                                    </div>
                """
            
            html += f"""
                            <tr class="hover:bg-blue-50/30 transition-colors" data-score="{overall_score:.2f}" data-order="{idx}">
                                <td class="px-6 py-5 min-w-[140px]">
                                    <div class="font-bold text-gray-900 text-lg whitespace-nowrap">{main_text}</div>
                                    <div class="text-xs text-gray-400 font-mono">{sub_text}</div>
                                </td>
                                <td class="px-5 py-5 min-w-[130px]">
                                    <div class="{price_color} font-bold text-base">{price_str}</div>
                                    <div class="{price_color} text-xs">{change_str}</div>
                                </td>
                                <td class="px-4 py-5 text-center text-xl w-20">{bb_emoji}</td>
                                <td class="px-4 py-5 text-center text-xl w-20">{ich_emoji}</td>
                                <td class="px-6 py-5">
                                    <div class="flex items-center gap-2 mb-2">
                                        <span class="text-lg">{overall_emoji}</span>
                                        <span class="text-sm font-semibold text-gray-700">{overall_score:.2f} / 4.0</span>
                                        <span class="text-gray-300">·</span>
                                        <span class="text-sm text-gray-500">{main_comment}</span>
                                    </div>
                                    {ai_html}
                                </td>
                            </tr>
"""

        html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="mt-6 text-center text-xs text-gray-400 leading-relaxed">
            본 데이터는 기술적 분석 결과일 뿐, 투자의 책임은 본인에게 있습니다.<br>
            볼린저 밴드는 20일 이동평균선과 ±2표준편차&#40;&sigma;&#41;를 기준으로 계산되었습니다.
        </div>
    </div>

    <script>
    let desktopSorted = false;
    let mobileSorted = false;

    function resetExpandedState(container) {
        // 정렬 시 모든 확장된 항목을 접음
        // 데스크탑
        container.querySelectorAll('.ai-box-desktop.expanded').forEach(box => {
            box.classList.remove('expanded');
            const btn = box.querySelector('.ai-toggle-desktop');
            if (btn) btn.textContent = '더보기';
        });
        // 모바일은 별도 처리 없음
    }

    function toggleSort(view) {
        if (view === 'desktop') {
            const body = document.getElementById('stockBody');
            const rows = Array.from(body.querySelectorAll('tr'));
            const label = document.getElementById('desktopSortLabel');
            
            resetExpandedState(body);

            if (!desktopSorted) {
                rows.sort((a, b) => parseFloat(b.dataset.score) - parseFloat(a.dataset.score));
                label.textContent = '기본';
            } else {
                rows.sort((a, b) => parseInt(a.dataset.order) - parseInt(b.dataset.order));
                label.textContent = '종합점수';
            }
            rows.forEach(row => body.appendChild(row));
            desktopSorted = !desktopSorted;
        } else {
            const body = document.getElementById('mobileBody');
            const cards = Array.from(body.children);
            const label = document.getElementById('mobileSortLabel');

            if (!mobileSorted) {
                cards.sort((a, b) => parseFloat(b.dataset.score) - parseFloat(a.dataset.score));
                label.textContent = '기본';
            } else {
                cards.sort((a, b) => parseInt(a.dataset.order) - parseInt(b.dataset.order));
                label.textContent = '종합점수';
            }
            cards.forEach(card => body.appendChild(card));
            mobileSorted = !mobileSorted;
        }
    }

    function toggleDesktop(btn) {
        const box = btn.closest('.ai-box-desktop');
        const isExpanded = box.classList.toggle('expanded');
        btn.textContent = isExpanded ? '접기' : '더보기';
    }

    // 모바일 텍스트 처리
    function expandMobile(btn) {
        const container = btn.parentElement;
        const fullText = container.dataset.full;
        container.innerHTML = `🤖 ${fullText} <span class="inline-btn" onclick="collapseMobile(this)">접기</span>`;
    }

    function collapseMobile(btn) {
        const container = btn.parentElement;
        const originalText = container.dataset.full;
        const maxLength = 150;
        const shortText = originalText.substring(0, maxLength);
        container.innerHTML = `🤖 ${shortText}... <span class="inline-btn" onclick="expandMobile(this)">더보기</span>`;
    }

    // 초기화 로직
    window.addEventListener('DOMContentLoaded', () => {
        // 데스크탑 오버플로 감지
        document.querySelectorAll('.ai-box-desktop').forEach(box => {
            const content = box.querySelector('.ai-content');
            content.style.webkitLineClamp = 'unset';
            content.style.lineClamp = 'unset';
            content.style.overflow = 'visible';
            content.style.display = 'block';
            const fullHeight = content.scrollHeight;
            content.style.webkitLineClamp = '';
            content.style.lineClamp = '';
            content.style.overflow = '';
            content.style.display = '';

            if (fullHeight > box.clientHeight) {
                box.classList.add('has-overflow');
                box.querySelector('.ai-toggle-desktop').classList.add('visible');
            }
        });

        // 모바일 텍스트 Truncate
        document.querySelectorAll('.ai-text-mobile').forEach(el => {
            const originalText = el.dataset.full;
            if (!originalText) return;
            
            const maxLength = 150;
            if (originalText.length > maxLength) {
                const shortText = originalText.substring(0, maxLength);
                el.innerHTML = `🤖 ${shortText}... <span class="inline-btn" onclick="expandMobile(this)">더보기</span>`;
            } else {
                el.innerHTML = `🤖 ${originalText}`;
            }
        });
    });
    </script>

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
