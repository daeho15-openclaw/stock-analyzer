"""
기존 JSON 파일에서 데이터를 읽어오는 수집기
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class JSONCollector:
    """JSON 파일 기반 데이터 수집기"""
    
    def __init__(self, data_dir: str = "../../stock-data"):
        """
        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.data_dir = Path(data_dir)
    
    def collect(self, code: str, market: str = "KRX") -> List[Dict]:
        """
        JSON 파일에서 주가 데이터 로드
        
        Args:
            code: 종목 코드 (예: "005930")
            market: 시장 (KRX 등)
        
        Returns:
            주가 데이터 리스트 [{'date': 'YYYY-MM-DD', 'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ...}, ...]
        """
        try:
            # 파일 경로
            if market == "KRX":
                filepath = self.data_dir / "kr" / f"{code}.json"
            else:
                filepath = self.data_dir / "us" / f"{code}.json"
            
            if not filepath.exists():
                print(f"⚠️  [{code}] 파일 없음: {filepath}")
                return []
            
            # JSON 로드
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            data = json_data.get('data', [])
            
            if not data:
                print(f"⚠️  [{code}] 데이터 없음")
                return []
            
            print(f"✅ [{code}] {len(data)}건 로드 (최신: {data[0]['date']})")
            
            return data
        
        except Exception as e:
            print(f"❌ [{code}] 로드 실패: {e}")
            return []
    
    def collect_multiple(self, stocks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        여러 종목 데이터 일괄 로드
        
        Args:
            stocks: 종목 리스트 [{'code': '005930', 'market': 'KRX', ...}, ...]
        
        Returns:
            종목별 데이터 딕셔너리 {code: [data, ...], ...}
        """
        results = {}
        
        for stock in stocks:
            code = stock['code']
            market = stock.get('market', 'KRX')
            
            data = self.collect(code, market)
            if data:
                results[code] = data
        
        return results


if __name__ == "__main__":
    # 테스트
    collector = JSONCollector("../../../stock-data")
    
    # 삼성전자 데이터 로드
    data = collector.collect("005930", "KRX")
    if data:
        print(f"\n최신 데이터: {data[0]}")
        print(f"총 {len(data)}건")
