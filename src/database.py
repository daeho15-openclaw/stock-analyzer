"""
데이터베이스 관리 모듈 (SQLite)
주가 데이터 및 평가 결과 저장
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class StockDatabase:
    """주식 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "data/stock_data.db"):
        """
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화 (테이블 생성)"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # 주가 데이터 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                market TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, date)
            )
        """)
        
        # 평가 결과 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                evaluator TEXT NOT NULL,
                score REAL NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, date, evaluator)
            )
        """)
        
        # 종합 리포트 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market TEXT NOT NULL,
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                format TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(market, date, format)
            )
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_code_date ON stock_prices(code, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_eval_code_date ON evaluations(code, date)")
        
        self.conn.commit()
    
    def save_price_data(self, code: str, market: str, data: List[Dict]):
        """
        주가 데이터 저장
        
        Args:
            code: 종목 코드
            market: 시장 (KRX, NASDAQ, NYSE 등)
            data: 주가 데이터 리스트 [{'date': '2026-02-10', 'open': 100, ...}, ...]
        """
        cursor = self.conn.cursor()
        
        for row in data:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO stock_prices 
                    (code, market, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    code,
                    market,
                    row['date'],
                    row.get('open'),
                    row.get('high'),
                    row.get('low'),
                    row.get('close'),
                    row.get('volume')
                ))
            except Exception as e:
                print(f"⚠️  데이터 저장 오류 ({code}, {row.get('date')}): {e}")
        
        self.conn.commit()
    
    def get_price_data(self, code: str, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None, limit: int = 60) -> List[Dict]:
        """
        주가 데이터 조회
        
        Args:
            code: 종목 코드
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            limit: 조회 건수 제한
        
        Returns:
            주가 데이터 리스트 (최신 순)
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM stock_prices WHERE code = ?"
        params = [code]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_latest_date(self, code: str) -> Optional[str]:
        """
        종목의 최신 데이터 날짜 조회
        
        Args:
            code: 종목 코드
        
        Returns:
            최신 날짜 (YYYY-MM-DD) 또는 None
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT MAX(date) as latest FROM stock_prices WHERE code = ?",
            (code,)
        )
        row = cursor.fetchone()
        return row['latest'] if row else None
    
    def save_evaluation(self, code: str, date: str, evaluator: str, 
                       score: float, details: Dict):
        """
        평가 결과 저장
        
        Args:
            code: 종목 코드
            date: 날짜
            evaluator: 평가 도구 이름
            score: 점수
            details: 상세 정보 (dict)
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO evaluations 
            (code, date, evaluator, score, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            code,
            date,
            evaluator,
            score,
            json.dumps(details, ensure_ascii=False)
        ))
        
        self.conn.commit()
    
    def get_evaluations(self, code: str, date: str) -> List[Dict]:
        """
        평가 결과 조회
        
        Args:
            code: 종목 코드
            date: 날짜
        
        Returns:
            평가 결과 리스트
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM evaluations 
            WHERE code = ? AND date = ?
        """, (code, date))
        
        rows = cursor.fetchall()
        results = []
        
        for row in rows:
            data = dict(row)
            data['details'] = json.loads(data['details'])
            results.append(data)
        
        return results
    
    def save_report(self, market: str, date: str, content: str, format: str):
        """
        리포트 저장
        
        Args:
            market: 시장 (kr, us 등)
            date: 날짜
            content: 리포트 내용
            format: 형식 (markdown, html)
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO reports 
            (market, date, content, format)
            VALUES (?, ?, ?, ?)
        """, (market, date, content, format))
        
        self.conn.commit()
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # 테스트
    db = StockDatabase("../data/stock_data.db")
    
    # 샘플 데이터 저장
    sample_data = [
        {'date': '2026-02-10', 'open': 100, 'high': 110, 'low': 95, 'close': 105, 'volume': 1000000}
    ]
    db.save_price_data("005930", "KRX", sample_data)
    
    # 데이터 조회
    data = db.get_price_data("005930", limit=10)
    print(f"조회된 데이터: {len(data)}건")
    
    db.close()
