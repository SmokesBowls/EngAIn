#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "== Repo =="
pwd
echo

echo "== Status (before) =="
git status -sb
echo

echo "== Ensure .gitignore exists =="
touch .gitignore

echo "== Append local/generated ignores (one-time block) =="
if ! grep -q "BEGIN: local generated ignores" .gitignore; then
  cat >> .gitignore <<'EOF'

# BEGIN: local generated ignores
.agent/
**/.agent/

reports/
**/reports/
cleanup_reports/
cleanup_reports_hh/
avatar/reports/
all_traces.json_concat

__pycache__/
**/__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.godot/
.import/
# END: local generated ignores
EOF
fi

echo "== Stage all changes =="
git add -A

echo
echo "== Staged summary (first 200 lines) =="
git diff --cached --name-status | sed -n '1,200p'
echo

echo "== Commit =="
git commit -m "workspace: reconcile docs restructure + ignore local outputs"

echo
echo "== Status (after) =="
git status -sb
