"""
평가 도구 베이스 클래스
모든 평가 도구는 이 클래스를 상속받아 구현
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple


class BaseEvaluator(ABC):
    """평가 도구 추상 베이스 클래스"""
    
    def __init__(self, config: Dict = None):
        """
        Args:
            config: 평가 도구 설정 딕셔너리
        """
        self.config = config or {}
        self.name = self.__class__.__name__.replace('Evaluator', '').lower()
    
    @abstractmethod
    def evaluate(self, data: List[Dict]) -> Tuple[float, str, str]:
        """
        주가 데이터를 평가하여 점수와 시그널 반환
        
        Args:
            data: 주가 데이터 리스트 (최신순)
                  [{'date': '2026-02-10', 'open': 100, 'high': 110, 'low': 95, 'close': 105, 'volume': 1000}, ...]
        
        Returns:
            (score, emoji, comment)
            - score: 1.0~4.0 점수
            - emoji: 시그널 emoji (🟢, 🟡, 🟠, 🔴)
            - comment: 분석 코멘트
        """
        pass
    
    @abstractmethod
    def get_details(self, data: List[Dict]) -> Dict:
        """
        상세 분석 정보 반환
        
        Args:
            data: 주가 데이터 리스트
        
        Returns:
            상세 정보 딕셔너리 (DB 저장용)
        """
        pass
    
    def get_weight(self) -> float:
        """
        종합 평가 시 가중치 반환
        
        Returns:
            가중치 (기본값 1.0)
        """
        return self.config.get('weight', 1.0)
    
    def get_name(self) -> str:
        """평가 도구 이름 반환"""
        return self.name
    
    @staticmethod
    def get_overall_emoji(avg_score: float) -> str:
        """
        평균 점수에 따른 종합 평가 emoji 반환
        
        Args:
            avg_score: 평균 점수
        
        Returns:
            종합 평가 emoji
        """
        if avg_score >= 3.5:
            return '🔥🔥'
        elif avg_score >= 3.25:
            return '🔥'
        elif avg_score >= 2.75:
            return '👍'
        elif avg_score >= 2.5:
            return '👌'
        elif avg_score >= 2.0:
            return '🧐'
        elif avg_score >= 1.5:
            return '👎'
        else:
            return '💣'
