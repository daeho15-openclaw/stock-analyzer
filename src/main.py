#!/usr/bin/env python3
"""
주식 분석 메인 프로그램
"""

import sys
import json
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# 현재 디렉토리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from database import StockDatabase
try:
    from collectors import FDRCollector
    HAS_FDR = True
except ImportError:
    HAS_FDR = False
from collectors.json_collector import JSONCollector
from evaluators import BollingerEvaluator, IchimokuEvaluator, BaseEvaluator
from reporters import MarkdownReporter, HTMLReporter


class StockAnalyzer:
    """주식 분석 메인 클래스"""
    
    def __init__(self, config_dir: str = "../config"):
        """
        Args:
            config_dir: 설정 파일 디렉토리
        """
        self.config_dir = Path(config_dir)
        self.load_configs()
        
        # 데이터베이스
        self.db = StockDatabase("../data/stock_data.db")
        
        # 데이터 수집기
        data_config = self.stocks_config.get('data_config', {})
        if HAS_FDR:
            self.collector = FDRCollector(
                days=data_config.get('days', 60),
                delay=0.5
            )
            print("📥 FinanceDataReader 사용")
        else:
            self.collector = JSONCollector()
            print("📦 JSON 파일에서 데이터 로드")
        
        # 평가 도구
        self.evaluators = self.init_evaluators()
        
        # 리포터
        report_format = self.report_config.get('format', 'markdown')
        if report_format == 'html':
            self.reporter = HTMLReporter(self.report_config)
        else:
            self.reporter = MarkdownReporter(self.report_config)
    
    def load_configs(self):
        """설정 파일 로드"""
        if HAS_YAML:
            # stocks.yml
            with open(self.config_dir / "stocks.yml", 'r', encoding='utf-8') as f:
                self.stocks_config = yaml.safe_load(f)
            
            # evaluators.yml
            with open(self.config_dir / "evaluators.yml", 'r', encoding='utf-8') as f:
                self.evaluators_config = yaml.safe_load(f)
            
            # report.yml
            with open(self.config_dir / "report.yml", 'r', encoding='utf-8') as f:
                self.report_config = yaml.safe_load(f)
        else:
            # 기본 설정
            self.stocks_config = {
                'kr_stocks': [
                    {'code': '005930', 'name': '삼성전자', 'market': 'KRX'},
                    {'code': '042660', 'name': '한화오션', 'market': 'KRX'}
                ],
                'data_config': {'days': 60}
            }
            self.evaluators_config = {
                'enabled_evaluators': ['bollinger', 'ichimoku'],
                'bollinger': {'period': 20, 'std_multiplier': 2.0, 'weight': 1.0},
                'ichimoku': {'conversion_period': 9, 'base_period': 26, 'span_b_period': 52, 'weight': 1.0}
            }
            self.report_config = {
                'format': 'markdown',
                'output_dir': '../reports'
            }
    
    def init_evaluators(self) -> List[BaseEvaluator]:
        """평가 도구 초기화"""
        evaluators = []
        
        enabled = self.evaluators_config.get('enabled_evaluators', [])
        
        if 'bollinger' in enabled:
            config = self.evaluators_config.get('bollinger', {})
            evaluators.append(BollingerEvaluator(config))
        
        if 'ichimoku' in enabled:
            config = self.evaluators_config.get('ichimoku', {})
            evaluators.append(IchimokuEvaluator(config))
        
        return evaluators
    
    def collect_and_cache_data(self, stock: Dict, force_update: bool = False) -> List[Dict]:
        """
        데이터 수집 및 캐싱
        
        Args:
            stock: 종목 정보
            force_update: 강제 업데이트 여부
        
        Returns:
            주가 데이터 리스트
        """
        code = stock['code']
        market = stock.get('market', 'KRX')
        
        # 캐시 확인
        if not force_update:
            latest_date = self.db.get_latest_date(code)
            if latest_date:
                # 최신 데이터가 오늘이면 DB에서 로드
                today = datetime.now().strftime('%Y-%m-%d')
                if latest_date >= today:
                    print(f"📦 [{code}] 캐시에서 로드")
                    return self.db.get_price_data(code, limit=60)
        
        # 데이터 수집
        data = self.collector.collect(code, market)
        
        if data:
            # DB 저장
            self.db.save_price_data(code, market, data)
        
        return data
    
    def evaluate_stock(self, stock: Dict, data: List[Dict], date: str) -> Dict:
        """
        종목 평가
        
        Args:
            stock: 종목 정보
            data: 주가 데이터
            date: 평가 날짜
        
        Returns:
            평가 결과 딕셔너리
        """
        code = stock['code']
        name = stock['name']
        
        # 각 평가 도구로 평가
        evaluations = {}
        scores = []
        
        for evaluator in self.evaluators:
            eval_name = evaluator.get_name()
            score, emoji, comment = evaluator.evaluate(data)
            details = evaluator.get_details(data)
            
            evaluations[eval_name] = {
                'score': score,
                'emoji': emoji,
                'comment': comment,
                'details': details
            }
            
            scores.append(score * evaluator.get_weight())
            
            # DB 저장
            self.db.save_evaluation(code, date, eval_name, score, details)
        
        # 종합 평가
        if scores:
            overall_score = sum(scores) / len(scores)
        else:
            overall_score = 2.0
        
        overall_emoji = BaseEvaluator.get_overall_emoji(overall_score)
        
        # 현재가 및 등락률
        current_price = data[0]['close'] if data else 0
        
        # 전일 대비 등락 계산
        price_change = 0
        price_change_rate = 0.0
        
        if len(data) >= 2:
            prev_price = data[1]['close']
            price_change = current_price - prev_price
            if prev_price > 0:
                price_change_rate = (price_change / prev_price) * 100
        
        return {
            'code': code,
            'name': name,
            'current_price': current_price,
            'price_change': price_change,
            'price_change_rate': price_change_rate,
            'evaluations': evaluations,
            'overall_score': overall_score,
            'overall_emoji': overall_emoji
        }
    
    def analyze_market(self, market: str, date: str = None, force_update: bool = False) -> List[Dict]:
        """
        시장 전체 분석
        
        Args:
            market: 시장 (kr, us)
            date: 분석 날짜 (기본값: 오늘)
            force_update: 강제 업데이트 여부
        
        Returns:
            분석 결과 리스트
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 종목 목록
        stocks_key = f"{market}_stocks"
        stocks = self.stocks_config.get(stocks_key, [])
        
        if not stocks:
            print(f"❌ {market} 시장 종목이 없습니다.")
            return []
        
        print(f"\n{'='*60}")
        print(f"📊 {market.upper()} 시장 분석 시작 ({date})")
        print(f"{'='*60}\n")
        
        results = []
        
        for stock in stocks:
            print(f"\n🔍 [{stock['code']}] {stock['name']} 분석 중...")
            
            # 데이터 수집
            data = self.collect_and_cache_data(stock, force_update)
            
            if not data:
                print(f"⚠️  [{stock['code']}] 데이터 없음, 건너뜀")
                continue
            
            # 평가
            result = self.evaluate_stock(stock, data, date)
            results.append(result)
            
            print(f"✅ [{stock['code']}] 평가 완료: {result['overall_emoji']}")
        
        return results
    
    def generate_report(self, market: str, date: str, results: List[Dict]) -> str:
        """
        리포트 생성
        
        Args:
            market: 시장
            date: 날짜
            results: 분석 결과
        
        Returns:
            리포트 파일 경로
        """
        # 리포트 생성
        content = self.reporter.generate(market, date, results)
        
        # 파일 저장
        filepath = self.reporter.save(market, date, content)
        
        # DB 저장
        report_format = self.report_config.get('format', 'markdown')
        self.db.save_report(market, date, content, report_format)
        
        return filepath
    
    def run(self, market: str = 'kr', date: str = None, force_update: bool = False):
        """
        분석 실행
        
        Args:
            market: 시장 (kr, us, all)
            date: 날짜
            force_update: 강제 업데이트
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        markets = ['kr', 'us'] if market == 'all' else [market]
        
        for mkt in markets:
            # 분석
            results = self.analyze_market(mkt, date, force_update)
            
            if results:
                # 리포트 생성
                filepath = self.generate_report(mkt, date, results)
                
                print(f"\n{'='*60}")
                print(f"✅ {mkt.upper()} 시장 분석 완료!")
                print(f"📄 리포트: {filepath}")
                print(f"{'='*60}\n")
    
    def close(self):
        """종료"""
        self.db.close()


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='주식 분석 프로그램')
    parser.add_argument('-m', '--market', choices=['kr', 'us', 'all'], default='kr',
                        help='분석할 시장 (kr: 한국, us: 미국, all: 전체)')
    parser.add_argument('-d', '--date', type=str,
                        help='분석 날짜 (YYYY-MM-DD, 기본값: 오늘)')
    parser.add_argument('-f', '--force', action='store_true',
                        help='캐시 무시하고 데이터 강제 업데이트')
    parser.add_argument('-c', '--config', type=str, default='../config',
                        help='설정 파일 디렉토리')
    
    args = parser.parse_args()
    
    try:
        analyzer = StockAnalyzer(config_dir=args.config)
        analyzer.run(market=args.market, date=args.date, force_update=args.force)
        analyzer.close()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
