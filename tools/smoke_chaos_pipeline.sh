#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/burdens/burdens_of_a_forgotten_past/EngAIn"
cd "$REPO_ROOT"

OUTDIR="tmp/chaos_smoke"
mkdir -p "$OUTDIR"

INPUT_TXT="$OUTDIR/input_narrative.txt"
PASS2_OUT="$OUTDIR/pass2.json"
PASS3_OUT="$OUTDIR/pass3.json"
ASSERT_PY="$OUTDIR/assert_contract.py"

cat > "$INPUT_TXT" <<'EOF'
Tran kneels before the Nephradi. The aurora shimmers; a pulse of fear turns the air sickly green.
Time stretches. Viên feels terror — seconds become minutes.
EOF

echo "=== Chaos Pipeline Smoke ==="
echo "Input: $INPUT_TXT"
echo

# Adjust invocation if your passes take different flags/args.
# Goal: produce JSON-like artifacts for pass2 and pass3.
echo "== Run pass2_core.py =="
python3 mettaext/pass2_core.py \
  --in "$INPUT_TXT" \
  --out "$PASS2_OUT"

echo "== Run pass3_merge.py =="
python3 mettaext/pass3_merge.py \
  --in "$PASS2_OUT" \
  --out "$PASS3_OUT"

echo
echo "== Show outputs (head) =="
echo "--- pass2 ---"
python3 -c 'import json;print(json.dumps(json.load(open("'"$PASS2_OUT"'")), indent=2)[:1800])' || true
echo
echo "--- pass3 ---"
python3 -c 'import json;print(json.dumps(json.load(open("'"$PASS3_OUT"'")), indent=2)[:1800])' || true

cat > "$ASSERT_PY" <<'PY'
import json, sys

p2_path, p3_path = sys.argv[1], sys.argv[2]
p2 = json.load(open(p2_path, "r", encoding="utf-8"))
p3 = json.load(open(p3_path, "r", encoding="utf-8"))

def has_key_anywhere(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return True
        return any(has_key_anywhere(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(has_key_anywhere(v, key) for v in obj)
    return False

def find_any_string_token(obj, tokens):
    if isinstance(obj, dict):
        return any(find_any_string_token(v, tokens) for v in obj.values())
    if isinstance(obj, list):
        return any(find_any_string_token(v, tokens) for v in obj)
    if isinstance(obj, str):
        s = obj.lower()
        return any(t in s for t in tokens)
    return False

# Contract expectations (tune if you used different key names)
EXPECT_KEYS = [
    "ambiguity", "ambiguity_score", "hypotheses", "actions", "time_dilation"
]

VIS_TOKENS = ["aurora", "shimmer", "glow", "pulse", "fear", "triumph", "emission"]

missing = []
for k in EXPECT_KEYS:
    if not (has_key_anywhere(p2, k) or has_key_anywhere(p3, k)):
        missing.append(k)

vis_ok = find_any_string_token(p2, VIS_TOKENS) or find_any_string_token(p3, VIS_TOKENS)

print("=== Assertions ===")
if missing:
    print("FAIL: Missing expected keys:", missing)
    sys.exit(2)

if not vis_ok:
    print("FAIL: Did not find expected visual semantic tokens anywhere.")
    sys.exit(3)

print("OK: keys present and visual semantics detected.")
PY

echo
echo "== Assert contracts =="
python3 "$ASSERT_PY" "$PASS2_OUT" "$PASS3_OUT"

echo
echo "DONE: smoke_chaos_pipeline.sh"
echo "Artifacts: $OUTDIR"
