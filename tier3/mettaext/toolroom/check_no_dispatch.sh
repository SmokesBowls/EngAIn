#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

failed=0

echo "=== METTAEXT NO-DISPATCH CHECK ==="

matches="$(
  grep -RIn \
    "urllib.request\|requests\.post\|http://127.0.0.1\|localhost:8080\|scene/load\|world/load_mirror" \
    pipeline_runner.py run1time.py engain_ingest.py chapterroom passroom \
    --exclude-dir=__pycache__ \
    --exclude='*.pyc' \
    2>/dev/null || true
)"

if [[ -n "$matches" ]]; then
  echo "$matches"
  failed=1
else
  echo "METTAEXT_RUNTIME_DISPATCH_REFERENCES=NONE"
fi

if [[ "$failed" -eq 0 ]]; then
  echo "METTAEXT_NO_DISPATCH=TRUE"
else
  echo "METTAEXT_NO_DISPATCH=FALSE"
fi

exit "$failed"
