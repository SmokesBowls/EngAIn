#!/usr/bin/env bash
set -euo pipefail

# Run from repo root. No Downloads assumptions.
REPO_ROOT="${REPO_ROOT:-$(pwd)}"
RUNTIME_BASE="${RUNTIME_BASE:-http://127.0.0.1:8080}"

# 1) Find loader script within repo
LOADER_SCRIPT="${LOADER_SCRIPT:-}"
if [[ -z "${LOADER_SCRIPT}" ]]; then
  # Prefer mettaext/engain_ingest.py, but fall back to any engain_ingest.py
  if [[ -f "${REPO_ROOT}/mettaext/engain_ingest.py" ]]; then
    LOADER_SCRIPT="${REPO_ROOT}/mettaext/engain_ingest.py"
  else
    LOADER_SCRIPT="$(find "${REPO_ROOT}" -maxdepth 6 -type f -name "engain_ingest.py" -print -quit || true)"
  fi
fi

if [[ -z "${LOADER_SCRIPT}" || ! -f "${LOADER_SCRIPT}" ]]; then
  echo "ERROR: Could not locate engain_ingest.py inside repo root: ${REPO_ROOT}"
  echo "Fix: export LOADER_SCRIPT=/absolute/path/to/engain_ingest.py"
  exit 1
fi

# 2) Find ZONJ scenes directory within repo
ZONJ_DIR="${ZONJ_DIR:-}"
if [[ -z "${ZONJ_DIR}" ]]; then
  # Common candidates (add more if your repo differs)
  for cand in \
    "${REPO_ROOT}/mettaext/game_scenes" \
    "${REPO_ROOT}/game_scenes" \
    "${REPO_ROOT}/scenes" \
    "${REPO_ROOT}/assets/game_scenes" \
    "${REPO_ROOT}/data/game_scenes"
  do
    if [[ -d "${cand}" ]]; then
      ZONJ_DIR="${cand}"
      break
    fi
  done

  # If still empty, search for a directory that contains .zonj files
  if [[ -z "${ZONJ_DIR}" ]]; then
    ZONJ_DIR="$(find "${REPO_ROOT}" -maxdepth 7 -type f \( -iname "*.zonj" -o -iname "*.json" \) \
      -path "*game_scenes*" -print -quit | xargs -r dirname || true)"
  fi
fi

if [[ -z "${ZONJ_DIR}" || ! -d "${ZONJ_DIR}" ]]; then
  echo "ERROR: Could not locate a scenes directory inside repo root: ${REPO_ROOT}"
  echo "Fix: export ZONJ_DIR=/absolute/path/to/your/game_scenes"
  exit 1
fi

echo "=== EngAIn Repo Smoke Test ==="
echo "REPO_ROOT:    ${REPO_ROOT}"
echo "RUNTIME_BASE: ${RUNTIME_BASE}"
echo "LOADER_SCRIPT:${LOADER_SCRIPT}"
echo "ZONJ_DIR:     ${ZONJ_DIR}"
echo

echo "== A) Verify command channel works =="
curl -sS -X POST "${RUNTIME_BASE}/command" \
  -H 'Content-Type: application/json' \
  -d '{"text":"status"}' | python3 -m json.tool
echo
curl -sS -X POST "${RUNTIME_BASE}/command" \
  -H 'Content-Type: application/json' \
  -d '{"text":"look"}' | python3 -m json.tool
echo

echo "== B) Verify /snapshot exists (your test_fixes.sh says it should) =="
http_code="$(curl -sS -o /tmp/engain_snapshot.json -w "%{http_code}" "${RUNTIME_BASE}/snapshot" || true)"
echo "GET /snapshot -> HTTP ${http_code}"
if [[ "${http_code}" == "200" ]]; then
  cat /tmp/engain_snapshot.json | python3 -m json.tool | head -n 60 || true
else
  echo "(Not fatal, but your runtime claims this should be 200.)"
fi
echo

echo "== C) Load scenes via loader (repo-local) =="
# Important: runtime must match your fixed runtime. Do not default to other ports.
python3 "${LOADER_SCRIPT}" --load-zonj "${ZONJ_DIR}" --out "${REPO_ROOT}/loaded" --runtime "${RUNTIME_BASE}"

echo
echo "== D) Validate after loader =="
curl -sS -X POST "${RUNTIME_BASE}/command" \
  -H 'Content-Type: application/json' \
  -d '{"text":"status"}' | python3 -m json.tool
echo
curl -sS -X POST "${RUNTIME_BASE}/command" \
  -H 'Content-Type: application/json' \
  -d '{"text":"look"}' | python3 -m json.tool
echo

echo "=== Done ==="
echo "If you still see placeholder look text or total_segments=0:"
echo "- loader is not actually populating scene content, or"
echo "- runtime accepts scene_id but not narrative segments/entities."
