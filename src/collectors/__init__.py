"""데이터 수집 모듈"""

try:
    from .fdr_collector import FDRCollector
    __all__ = ['FDRCollector']
except ImportError:
    __all__ = []
