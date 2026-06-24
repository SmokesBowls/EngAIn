#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

failed=0

echo "=== STAGEROOM RULE CHECK ==="

echo
echo "[1] Root generated-output strays"
root_strays="$(find . -maxdepth 1 -type f \
  \( -name 'out_pass*' -o -name 'zonj_*' -o -name '*.zon' -o -name '*.zonj.json' \) \
  | sort || true)"
if [[ -n "$root_strays" ]]; then
  echo "$root_strays"
  failed=1
else
  echo "ROOT_OUTPUT_STRAYS=NONE"
fi

echo
echo "[2] Chapterroom generated-output strays"
chapterroom_strays="$(find chapterroom -type f \
  \( -name 'out_pass*' -o -name 'zonj_*' -o -name '*.zon' -o -name '*.zonj.json' -o -name 'scene.*.txt' -o -name 'scene.*.json' \) \
  | sort || true)"
if [[ -n "$chapterroom_strays" ]]; then
  echo "$chapterroom_strays"
  failed=1
else
  echo "CHAPTERROOM_OUTPUT_STRAYS=NONE"
fi

echo
echo "[3] Passroom generated-output strays"
passroom_strays="$(find passroom -type f \
  \( -name 'out_pass*' -o -name 'zonj_*' -o -name '*.zon' -o -name '*.zonj.json' -o -name 'scene.*.json' \) \
  | sort || true)"
if [[ -n "$passroom_strays" ]]; then
  echo "$passroom_strays"
  failed=1
else
  echo "PASSROOM_OUTPUT_STRAYS=NONE"
fi

echo
echo "[4] Toolroom proofroom check"
if [[ -d toolroom/proofroom ]]; then
  echo "TOOLROOM_PROOFROOM_EXISTS=TRUE"
  failed=1
else
  echo "TOOLROOM_PROOFROOM_EXISTS=FALSE"
fi

echo
echo "[5] Legacy pipeline compatibility bridge"
if [[ -L compiled/pipeline_work ]]; then
  echo "COMPILED_PIPELINE_WORK_IS_SYMLINK=TRUE"
  echo "COMPILED_PIPELINE_WORK_REALPATH=$(readlink -f compiled/pipeline_work)"
else
  echo "COMPILED_PIPELINE_WORK_IS_SYMLINK=FALSE"
  failed=1
fi

if [[ -d stageroom/output/legacy_pipeline_work ]]; then
  echo "LEGACY_PIPELINE_REAL_PATH_EXISTS=TRUE"
else
  echo "LEGACY_PIPELINE_REAL_PATH_EXISTS=FALSE"
  failed=1
fi

echo
if [[ "$failed" -eq 0 ]]; then
  echo "STAGEROOM_RULE=TRUE"
else
  echo "STAGEROOM_RULE=FALSE"
fi

exit "$failed"
