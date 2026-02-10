#!/bin/bash
# 주식 분석 실행 스크립트

cd "$(dirname "$0")/src"

# 기본값
MARKET="kr"
FORCE=""

# 인자 파싱
while [[ $# -gt 0 ]]; do
  case $1 in
    -m|--market)
      MARKET="$2"
      shift 2
      ;;
    -f|--force)
      FORCE="-f"
      shift
      ;;
    -h|--help)
      echo "사용법: $0 [-m kr|us|all] [-f]"
      echo ""
      echo "옵션:"
      echo "  -m, --market  분석할 시장 (kr, us, all) [기본값: kr]"
      echo "  -f, --force   캐시 무시하고 강제 업데이트"
      echo "  -h, --help    도움말 출력"
      exit 0
      ;;
    *)
      echo "알 수 없는 옵션: $1"
      echo "도움말: $0 -h"
      exit 1
      ;;
  esac
done

echo "🚀 주식 분석 시작..."
echo "📊 시장: $MARKET"
echo ""

python main.py -m "$MARKET" $FORCE

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ 분석 완료!"
  echo "📄 리포트: ../reports/"
  ls -lh ../reports/*.md ../reports/*.html 2>/dev/null | tail -5
else
  echo ""
  echo "❌ 분석 실패!"
  exit 1
fi
