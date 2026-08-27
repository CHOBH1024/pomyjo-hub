#!/usr/bin/env bash
# POMYJO 배포 스크립트
#
# 사용법:
#   ./deploy.sh
#
# Cloudflare Pages 프로젝트 "pomyjo" 로 현재 폴더를 배포한다.
# 인증이 필요하다. 둘 중 하나:
#   1) 브라우저 로그인 (한 번만):  npx wrangler login
#   2) API 토큰:                   export CLOUDFLARE_API_TOKEN=...
#
# 배포 전에 build.py 를 돌려 CSS 인라인과 링크 정규화를 반영한다.

set -euo pipefail
cd "$(dirname "$0")"

echo "[1/3] build.py 실행 (CSS 인라인 · 내부 링크 정규화)"
python build.py

echo
echo "[2/3] 배포할 파일 확인"
ls -1 *.html guides/*.html | wc -l | xargs echo "  HTML 페이지:"

echo
echo "[3/3] Cloudflare Pages 배포"
npx wrangler pages deploy . \
  --project-name=pomyjo \
  --branch=main \
  --commit-dirty=true

echo
echo "완료. 확인:"
echo "  https://pomyjo.com/about"
echo "  https://pomyjo.com/contact"
echo "  https://pomyjo.com/guides/"
