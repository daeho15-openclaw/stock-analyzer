"""
LLM 기반 리포트 해설 생성기 (Claude API)
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional


def load_openclaw_token() -> Optional[str]:
    """OpenClaw의 Anthropic OAuth token 로드"""
    try:
        # OpenClaw auth-profiles.json 경로
        home = Path.home()
        auth_file = home / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json"
        
        if not auth_file.exists():
            return None
        
        with open(auth_file, 'r') as f:
            data = json.load(f)
        
        # anthropic:default 프로필의 token 가져오기
        token = data.get('profiles', {}).get('anthropic:default', {}).get('token')
        
        if token:
            print("✅ OpenClaw Anthropic OAuth token 로드 성공")
            return token
        
        return None
    except Exception as e:
        print(f"⚠️  OpenClaw token 로드 실패: {e}")
        return None


class ClaudeCommentGenerator:
    """Claude API를 사용한 자연어 해설 생성기"""
    
    def __init__(self, model: str = "claude-haiku-4-5", 
                 api_key: Optional[str] = None, 
                 auth_token: Optional[str] = None,
                 use_openclaw_token: bool = False):
        """
        Args:
            model: Claude 모델 (haiku 또는 sonnet)
            api_key: Anthropic API 키 (없으면 환경변수에서 로드)
            auth_token: Anthropic OAuth token (API 키보다 우선)
            use_openclaw_token: OpenClaw의 OAuth token 자동 로드
        """
        self.model = model
        
        # 1순위: OpenClaw token (use_openclaw_token=True인 경우)
        if use_openclaw_token:
            self.auth_token = load_openclaw_token()
        else:
            self.auth_token = None
        
        # 2순위: 직접 전달된 OAuth token
        if not self.auth_token:
            self.auth_token = auth_token or os.environ.get('ANTHROPIC_AUTH_TOKEN')
        
        # 3순위: API key
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        
        if not self.auth_token and not self.api_key:
            print("⚠️  ANTHROPIC_AUTH_TOKEN 또는 ANTHROPIC_API_KEY가 설정되지 않았습니다. LLM 기능이 비활성화됩니다.")
            self.enabled = False
        else:
            self.enabled = True
            
            # Anthropic 클라이언트 로드
            try:
                from anthropic import Anthropic
                
                # OAuth token이 있으면 우선 사용
                if self.auth_token:
                    self.client = Anthropic(auth_token=self.auth_token)
                    print(f"✅ Claude API 연결 성공 (OAuth token, 모델: {self.model})")
                else:
                    self.client = Anthropic(api_key=self.api_key)
                    print(f"✅ Claude API 연결 성공 (API key, 모델: {self.model})")
                    
            except ImportError:
                print("⚠️  anthropic 패키지가 설치되지 않았습니다. pip install anthropic")
                self.enabled = False
            except Exception as e:
                print(f"❌ Claude API 초기화 실패: {e}")
                self.enabled = False
    
    def generate_stock_analysis(self, stock_data: Dict) -> str:
        """
        개별 종목에 대한 자연어 해설 생성
        
        Args:
            stock_data: 종목 분석 데이터
        
        Returns:
            2-3문장의 해설
        """
        if not self.enabled:
            return self._fallback_stock_comment(stock_data)
        
        try:
            # 평가 데이터 추출
            evals = stock_data.get('evaluations', {})
            bb = evals.get('bollinger', {})
            ich = evals.get('ichimoku', {})
            
            prompt = f"""당신은 주식 애널리스트입니다. 다음 기술적 분석 결과를 바탕으로 투자자가 이해하기 쉽게 해설해주세요.

종목: {stock_data['name']} ({stock_data['code']})
현재가: {stock_data['current_price']:,.0f}원
등락률: {stock_data.get('price_change_rate', 0):.2f}%

볼린저 밴드 분석:
- 점수: {bb.get('score', 0)}/4.0
- 코멘트: {bb.get('comment', 'N/A')}

일목균형표 분석:
- 점수: {ich.get('score', 0)}/4.0
- 코멘트: {ich.get('comment', 'N/A')}

종합 평가: {stock_data['overall_emoji']} ({stock_data['overall_score']:.2f}/4.0)

2-3문장으로 간결하게 설명하되, 투자 시사점을 포함해주세요. 이모지는 사용하지 마세요. 마크다운 문법을 쓰지 말고 문장만 만들어."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
        
        except Exception as e:
            print(f"⚠️  Claude API 호출 실패 ({stock_data['name']}): {e}")
            return self._fallback_stock_comment(stock_data)
    
    

if __name__ == "__main__":
    # 테스트
    generator = ClaudeCommentGenerator()
    
    if generator.enabled:
        sample_stock = {
            'code': '005930',
            'name': '삼성전자',
            'current_price': 165800,
            'price_change_rate': -0.36,
            'evaluations': {
                'bollinger': {'score': 1.0, 'comment': '과매수 80%, 매도 고려'},
                'ichimoku': {'score': 4.0, 'comment': '골든크로스, 강세'}
            },
            'overall_score': 2.5,
            'overall_emoji': '👌'
        }
        
        comment = generator.generate_stock_analysis(sample_stock)
        print(f"종목 해설: {comment}")
    else:
        print("LLM 비활성화 상태")
