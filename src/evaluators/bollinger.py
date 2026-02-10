"""
볼린저 밴드 평가 도구
"""

import statistics
from typing import List, Dict, Tuple
from .base import BaseEvaluator


class BollingerEvaluator(BaseEvaluator):
    """볼린저 밴드 평가 도구"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.period = self.config.get('period', 20)
        self.std_multiplier = self.config.get('std_multiplier', 2.0)
    
    def calculate_bollinger(self, closes: List[float]) -> Dict:
        """
        볼린저 밴드 계산
        
        Args:
            closes: 종가 리스트 (최신순)
        
        Returns:
            {'sma': 중심선, 'upper': 상단밴드, 'lower': 하단밴드, 'current': 현재가, 'position': 밴드내위치%}
        """
        if len(closes) < self.period:
            return None
        
        recent = closes[:self.period]
        sma = sum(recent) / self.period
        std = statistics.stdev(recent)
        
        upper = sma + (std * self.std_multiplier)
        lower = sma - (std * self.std_multiplier)
        current = closes[0]
        
        # 밴드 내 위치 계산 (0~100%)
        if upper != lower:
            position = ((current - lower) / (upper - lower)) * 100
        else:
            position = 50
        
        return {
            'sma': sma,
            'upper': upper,
            'lower': lower,
            'current': current,
            'position': position
        }
    
    def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
        """
        볼린저 밴드 평가
        
        평가 기준:
        - 🟢 4점: 밴드 내 위치 0~25% (하단 근처, 강한 매수)
        - 🟡 3점: 밴드 내 위치 25~50% (중립, 약한 매수)
        - 🟠 2점: 밴드 내 위치 50~80% (과열, 약한 매도)
        - 🔴 1점: 밴드 내 위치 80~100% (과매수, 강한 매도)
        """
        if not data or len(data) < self.period:
            return 2.0, '🟡', '데이터 부족'
        
        closes = [d['close'] for d in data]
        bb = self.calculate_bollinger(closes)
        
        if not bb:
            return 2.0, '🟡', '계산 실패'
        
        pos = bb['position']
        
        if pos <= 25:
            score = 4.0
            emoji = '🟢'
            comment = f"하단 근처 {pos:.0f}%, 반등 기대"
        elif pos <= 50:
            score = 3.0
            emoji = '🟡'
            comment = f"중립 {pos:.0f}%, 관망"
        elif pos <= 80:
            score = 2.0
            emoji = '🟠'
            comment = f"과열 {pos:.0f}%, 조정 주의"
        else:
            score = 1.0
            emoji = '🔴'
            comment = f"과매수 {pos:.0f}%, 매도 고려"
        
        return score, emoji, comment
    
    def get_details(self, data: List[Dict]) -> Dict:
        """상세 분석 정보"""
        if not data or len(data) < self.period:
            return {'error': '데이터 부족'}
        
        closes = [d['close'] for d in data]
        bb = self.calculate_bollinger(closes)
        
        if not bb:
            return {'error': '계산 실패'}
        
        score, emoji, comment = self.evaluate(data)
        
        return {
            'sma': bb['sma'],
            'upper': bb['upper'],
            'lower': bb['lower'],
            'current': bb['current'],
            'position': bb['position'],
            'score': score,
            'emoji': emoji,
            'comment': comment
        }


if __name__ == "__main__":
    # 테스트
    sample_data = [
        {'date': '2026-02-10', 'close': 165800},
        {'date': '2026-02-07', 'close': 167400},
        {'date': '2026-02-06', 'close': 168100},
    ] + [{'date': f'2026-02-{i:02d}', 'close': 170000 + i * 100} for i in range(1, 20)]
    
    evaluator = BollingerEvaluator({'period': 20, 'std_multiplier': 2.0})
    score, emoji, comment = evaluator.evaluate(sample_data)
    
    print(f"점수: {score}, Emoji: {emoji}, 코멘트: {comment}")
    print(f"상세: {evaluator.get_details(sample_data)}")
