"""
FinanceDataReader를 사용한 데이터 수집기
"""

import FinanceDataReader as fdr
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time


class FDRCollector:
    """FinanceDataReader 기반 데이터 수집기"""
    
    def __init__(self, days: int = 60, delay: float = 0.5):
        """
        Args:
            days: 수집할 과거 데이터 일수
            delay: API 호출 간 대기 시간 (초)
        """
        self.days = days
        self.delay = delay
    
    def collect(self, code: str, market: str = "KRX", 
                start_date: Optional[str] = None,
                end_date: Optional[str] = None) -> List[Dict]:
        """
        주가 데이터 수집
        
        Args:
            code: 종목 코드 (예: "005930", "NVDA")
            market: 시장 (KRX, NASDAQ, NYSE 등)
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
        
        Returns:
            주가 데이터 리스트 [{'date': 'YYYY-MM-DD', 'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ...}, ...]
        """
        try:
            # 날짜 설정
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            if not start_date:
                start_dt = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=self.days)
                start_date = start_dt.strftime('%Y-%m-%d')
            
            # 데이터 수집
            print(f"📥 [{code}] 데이터 수집 중... ({start_date} ~ {end_date})")
            
            df = fdr.DataReader(code, start_date, end_date)
            
            if df is None or df.empty:
                print(f"⚠️  [{code}] 데이터 없음")
                return []
            
            # DataFrame -> List[Dict] 변환
            data = []
            for date, row in df.iterrows():
                try:
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row.get('Open', 0)),
                        'high': float(row.get('High', 0)),
                        'low': float(row.get('Low', 0)),
                        'close': float(row.get('Close', 0)),
                        'volume': int(row.get('Volume', 0))
                    })
                except Exception as e:
                    print(f"⚠️  [{code}] 행 변환 오류: {e}")
                    continue
            
            # 최신 데이터가 앞에 오도록 정렬
            data.reverse()
            
            print(f"✅ [{code}] {len(data)}건 수집 완료")
            
            # API rate limit 방지
            time.sleep(self.delay)
            
            return data
        
        except Exception as e:
            print(f"❌ [{code}] 수집 실패: {e}")
            return []
    
    def collect_multiple(self, stocks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        여러 종목 데이터 일괄 수집
        
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
    collector = FDRCollector(days=10)
    
    # 삼성전자 데이터 수집
    data = collector.collect("005930", "KRX")
    if data:
        print(f"\n최신 데이터: {data[0]}")
        print(f"총 {len(data)}건")
