"""
일목균형표 평가 도구
"""

from typing import List, Dict, Tuple
from .base import BaseEvaluator


class IchimokuEvaluator(BaseEvaluator):
    """일목균형표 평가 도구"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.conversion_period = self.config.get('conversion_period', 9)
        self.base_period = self.config.get('base_period', 26)
        self.span_b_period = self.config.get('span_b_period', 52)
    
    def calculate_ichimoku(self, highs: List[float], lows: List[float], closes: List[float]) -> Dict:
        """
        일목균형표 계산
        
        Args:
            highs: 고가 리스트 (최신순)
            lows: 저가 리스트 (최신순)
            closes: 종가 리스트 (최신순)
        
        Returns:
            {'conversion': 전환선, 'baseline': 기준선, 'span_a': 선행스팬A, 'span_b': 선행스팬B, 'current': 현재가}
        """
        if len(highs) < self.base_period or len(lows) < self.base_period:
            return None
        
        # 전환선 (9일)
        conv_high = max(highs[:self.conversion_period])
        conv_low = min(lows[:self.conversion_period])
        conversion = (conv_high + conv_low) / 2
        
        # 기준선 (26일)
        base_high = max(highs[:self.base_period])
        base_low = min(lows[:self.base_period])
        baseline = (base_high + base_low) / 2
        
        # 선행스팬 A (전환선 + 기준선) / 2
        span_a = (conversion + baseline) / 2
        
        # 선행스팬 B (52일)
        if len(highs) >= self.span_b_period:
            span_b_high = max(highs[:self.span_b_period])
            span_b_low = min(lows[:self.span_b_period])
            span_b = (span_b_high + span_b_low) / 2
        else:
            span_b = span_a  # 데이터 부족 시 span_a로 대체
        
        # 구름대 (선행스팬 A와 B 사이)
        cloud_top = max(span_a, span_b)
        cloud_bottom = min(span_a, span_b)
        
        current = closes[0]
        
        return {
            'conversion': conversion,
            'baseline': baseline,
            'span_a': span_a,
            'span_b': span_b,
            'cloud_top': cloud_top,
            'cloud_bottom': cloud_bottom,
            'current': current
        }
    
    def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
        """
        일목균형표 평가
        
        평가 기준:
        - 🟢 4점: 전환선 > 기준선 AND 현재가 > 구름대 (강한 매수)
        - 🟡 3점: 전환선 > 기준선 OR 현재가 > 구름대 (약한 매수)
        - 🟠 2점: 전환선 < 기준선 OR 현재가 < 구름대 (약한 매도)
        - 🔴 1점: 전환선 < 기준선 AND 현재가 < 구름대 (강한 매도)
        """
        if not data or len(data) < self.base_period:
            return 2.0, '🟡', '데이터 부족'
        
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        closes = [d['close'] for d in data]
        
        ich = self.calculate_ichimoku(highs, lows, closes)
        
        if not ich:
            return 2.0, '🟡', '계산 실패'
        
        conv = ich['conversion']
        base = ich['baseline']
        curr = ich['current']
        cloud_top = ich['cloud_top']
        cloud_bottom = ich['cloud_bottom']
        
        # 전환선 > 기준선 (골든크로스)
        conv_above = conv > base
        # 현재가 > 구름대 상단
        price_above = curr > cloud_top
        # 현재가 < 구름대 하단
        price_below = curr < cloud_bottom
        
        if conv_above and price_above:
            score = 4.0
            emoji = '🟢'
            comment = "골든크로스, 강세"
        elif conv_above or price_above:
            score = 3.0
            emoji = '🟡'
            comment = "중립, 추세 전환 중"
        elif not conv_above and price_below:
            score = 1.0
            emoji = '🔴'
            comment = "데드크로스, 약세"
        else:
            score = 2.0
            emoji = '🟠'
            comment = "하락 조짐"
        
        return score, emoji, comment
    
    def get_details(self, data: List[Dict]) -> Dict:
        """상세 분석 정보"""
        if not data or len(data) < self.base_period:
            return {'error': '데이터 부족'}
        
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        closes = [d['close'] for d in data]
        
        ich = self.calculate_ichimoku(highs, lows, closes)
        
        if not ich:
            return {'error': '계산 실패'}
        
        score, emoji, comment = self.evaluate(data)
        
        return {
            'conversion': ich['conversion'],
            'baseline': ich['baseline'],
            'span_a': ich['span_a'],
            'span_b': ich['span_b'],
            'cloud_top': ich['cloud_top'],
            'cloud_bottom': ich['cloud_bottom'],
            'current': ich['current'],
            'score': score,
            'emoji': emoji,
            'comment': comment
        }


if __name__ == "__main__":
    # 테스트
    sample_data = [
        {'date': '2026-02-10', 'high': 168100, 'low': 165500, 'close': 165800},
        {'date': '2026-02-07', 'high': 169000, 'low': 166000, 'close': 167400},
    ] + [
        {'date': f'2026-02-{i:02d}', 'high': 170000 + i * 100, 'low': 168000 + i * 100, 'close': 169000 + i * 100}
        for i in range(1, 30)
    ]
    
    evaluator = IchimokuEvaluator({
        'conversion_period': 9,
        'base_period': 26,
        'span_b_period': 52
    })
    
    score, emoji, comment = evaluator.evaluate(sample_data)
    
    print(f"점수: {score}, Emoji: {emoji}, 코멘트: {comment}")
    print(f"상세: {evaluator.get_details(sample_data)}")
