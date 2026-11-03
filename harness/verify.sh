#!/usr/bin/env bash
# 전체 검증 파이프라인: 원고 검사 → 빌드 → PDF/PNG + 레이아웃 검사 → 보고서
#   bash harness/verify.sh            # 전체
#   bash harness/verify.sh --png      # 페이지 PNG까지 (교차 검토용)
set -uo pipefail
cd "$(dirname "$0")/.."
STAMP=$(date +%Y%m%d-%H%M)
OUT=reports/verify/$STAMP
mkdir -p "$OUT"

echo "== 1/3 원고 검사"
python3 harness/check.py --report "$OUT/content.json"; C=$?

echo "== 2/3 빌드"
python3 harness/build.py --out dist/book.html || exit 2

echo "== 3/3 렌더링 + 레이아웃 검사"
PNG_ARGS=()
[[ "${1:-}" == "--png" ]] && PNG_ARGS=(--png dist/png --scale 1.4)
node harness/render.mjs --html dist/book.html --pdf dist/ai-literacy-workbook.pdf --report "$OUT/layout.json" "${PNG_ARGS[@]}"; L=$?

python3 harness/report.py "$OUT" > "$OUT/SUMMARY.md"
cp "$OUT/SUMMARY.md" reports/verify/LATEST.md
echo "report: $OUT/SUMMARY.md"
[[ $C -eq 0 && $L -eq 0 ]] && echo "RESULT: PASS" || { echo "RESULT: FAIL"; exit 1; }
