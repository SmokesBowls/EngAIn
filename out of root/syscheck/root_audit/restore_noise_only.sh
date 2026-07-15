#!/usr/bin/env bash
set -euo pipefail

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn

echo "[RESTORE] runtime pid files"
git restore -- .run || true

echo "[RESTORE] generated EngAIn cache"
git restore -- .engain_cache || true

echo "[RESTORE] vault cache"
git restore -- .vault_cache || true

echo "[RESTORE] mettaext generated compiled pipeline output"
git restore -- tier3/mettaext/compiled/pipeline_work || true

echo "[RESTORE] godotsim tracked node_modules deletions"
git restore -- godotsim/node_modules || true

echo "[DONE] restored generated/dependency noise only"
echo
git status --short --untracked-files=all | head -200
