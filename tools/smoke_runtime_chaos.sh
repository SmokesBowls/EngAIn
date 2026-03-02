#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/burdens/burdens_of_a_forgotten_past/EngAIn"
cd "$REPO_ROOT"

echo "=== Runtime Chaos Smoke ==="
echo

echo "== AP engine import + function existence =="
python3 - <<'PY'
from engainos.core import ap_engine

need = ["resonance", "vrel_harmony"]
missing = [n for n in need if not hasattr(ap_engine, n)]
if missing:
    raise SystemExit(f"FAIL: ap_engine missing: {missing}")
print("OK: ap_engine has:", need)
PY

echo
echo "== Godot bridge semantic contract grep =="
# We want to see that the bridge consumes semantic hints and ambiguity.
rg -n "ambiguity|time_dilation|aurora|shimmer|emission|pulse|fear|triumph" engainos/godot/EngAInBridge.gd || {
  echo "WARN: Could not find expected tokens in EngAInBridge.gd"
}

echo
echo "== Lax mode boot probe =="
# This assumes launch_engine.py is the entrypoint you changed.
# We run it twice: strict and lax, expecting lax to be MORE tolerant.
STRICT_LOG="tmp/boot_strict.log"
LAX_LOG="tmp/boot_lax.log"
mkdir -p tmp

set +e
python3 engainos/launch_engine.py --probe-only >"$STRICT_LOG" 2>&1
STRICT_RC=$?
ENGAIN_LAX=1 python3 engainos/launch_engine.py --probe-only >"$LAX_LOG" 2>&1
LAX_RC=$?
set -e

echo "Strict rc: $STRICT_RC"
echo "Lax    rc: $LAX_RC"
echo
echo "--- strict (tail) ---"
tail -n 40 "$STRICT_LOG" || true
echo
echo "--- lax (tail) ---"
tail -n 40 "$LAX_LOG" || true

# Heuristic: lax should not fail if strict does, unless it's a truly critical error.
if [[ $STRICT_RC -ne 0 && $LAX_RC -ne 0 ]]; then
  echo
  echo "WARN: Both strict and lax failed. Inspect logs above."
fi

echo
echo "DONE: smoke_runtime_chaos.sh"
