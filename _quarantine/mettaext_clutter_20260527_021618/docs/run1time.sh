#!/usr/bin/env bash
set -euo pipefail

IN="03_Fist_contact.txt"
BASE="$(basename "$IN" .txt)"

python3 pass1_explicit.py "$IN"

P1="$(find . -maxdepth 4 -type f -name "out_pass1_${BASE}.txt" | head -n 1)"
if [ -z "$P1" ]; then
  echo "FAIL: Pass1 did not produce out_pass1_${BASE}.txt anywhere under $(pwd)"
  exit 1
fi
echo "Using Pass1 output: $P1"

python3 pass2_core.py "$P1"

P2="$(dirname "$P1")/out_pass2_${BASE}.metta"
[ -f "$P2" ] || P2="out_pass2_${BASE}.metta"
echo "Using Pass2 output: $P2"

python3 pass3_merge.py "$P1" "$P2"

ZONJ="$(dirname "$P1")/zonj_${BASE}.json"
[ -f "$ZONJ" ] || ZONJ="zonj_${BASE}.json"
echo "Using Pass3 output (zonj): $ZONJ"

python3 pass4_zon_bridge.py "$ZONJ" --era FirstAge --location Beach --output-dir out

echo "OK: wrote ./out/${BASE}.zon and ./out/${BASE}.zonj.json"
