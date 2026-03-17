#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/burdens/burdens_of_a_forgotten_past/EngAIn"

cd "$REPO_ROOT"

echo "=== Verify Chaos Patch Presence ==="
echo "Repo: $REPO_ROOT"
echo

# 1) Basic file existence
declare -a MUST_HAVE=(
  "mettaext/pass2_core.py"
  "mettaext/pass3_merge.py"
  "engainos/core/ap_engine.py"
  "engainos/godot/EngAInBridge.gd"
  "engainos/launch_engine.py"
)

missing=0
for f in "${MUST_HAVE[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "[MISSING] $f"
    missing=$((missing+1))
  else
    echo "[OK]      $f"
  fi
done

if [[ $missing -gt 0 ]]; then
  echo
  echo "ERROR: Missing required files. Fix paths first."
  exit 2
fi

echo
echo "=== Git status (summary) ==="
if command -v git >/dev/null 2>&1 && [[ -d .git ]]; then
  git status -sb || true
  echo
  echo "=== Git diff (stat) ==="
  git diff --stat || true
else
  echo "No git repo detected at $REPO_ROOT (or git not installed). Skipping git checks."
fi

echo
echo "=== Contract probes (grep) ==="
# Probe for new fields and functions
PATTERNS=(
  "ambiguity_score"
  "hypotheses"
  "multi-hypothesis"
  "resonance("
  "vrel_harmony"
  "time_dilation"
  "ENGAIN_LAX"
  "aurora"
  "shimmer"
  "glow"
  "pulse"
)

for p in "${PATTERNS[@]}"; do
  echo
  echo "--- $p ---"
  rg -n --hidden --no-ignore-vcs "$p" \
    mettaext/pass2_core.py \
    mettaext/pass3_merge.py \
    engainos/core/ap_engine.py \
    engainos/godot/EngAInBridge.gd \
    engainos/launch_engine.py \
    2>/dev/null || echo "(no matches)"
done

echo
echo "DONE: verify_chaos_patch.sh"
