#!/usr/bin/env bash
set -euo pipefail

RUNTIME="${RUNTIME:-http://127.0.0.1:8080}"
SCENE_FILE="${1:-}"

if [[ -z "${SCENE_FILE}" ]]; then
  echo "usage: $0 path/to/scene.json"
  exit 2
fi

echo "[0] sanity: runtime reachable?"
if ! curl -fsS "${RUNTIME}/snapshot" >/dev/null 2>&1; then
  echo "FAIL: cannot reach ${RUNTIME}/snapshot (runtime down or wrong port)"
  exit 1
fi

echo "[1/3] load scene -> ${SCENE_FILE}"
LOAD_OUT="$(mktemp)"
LOAD_HDR="$(mktemp)"
HTTP_CODE="$(curl -sS -o "${LOAD_OUT}" -D "${LOAD_HDR}" -w "%{http_code}" \
  -X POST "${RUNTIME}/scene/load" \
  -H 'Content-Type: application/json' \
  --data-binary @"${SCENE_FILE}")"

echo "HTTP ${HTTP_CODE}"
echo "--- response headers ---"
sed -n '1,25p' "${LOAD_HDR}"
echo "--- response body (first 400 bytes) ---"
head -c 400 "${LOAD_OUT}"; echo

# Validate JSON
if ! python3 -c 'import json,sys; json.load(open(sys.argv[1],"r"))' "${LOAD_OUT}" 2>/dev/null; then
  echo
  echo "FAIL: /scene/load did not return JSON."
  echo "Common causes:"
  echo "  - handler is not calling _send_json_response for /scene/load"
  echo "  - wrong endpoint/port (HTML 404/500)"
  echo "  - runtime returned plain text"
  echo
  echo "Full body saved at: ${LOAD_OUT}"
  exit 1
fi

python3 -m json.tool "${LOAD_OUT}"

echo
echo "[2/3] status (must show scene_segments > 0)"
STATUS="$(curl -sS -X POST "${RUNTIME}/command" \
  -H 'Content-Type: application/json' \
  -d '{"text":"status"}')"
echo "${STATUS}" | python3 -m json.tool

python3 - <<'PY'
import json, os, sys
status = json.loads(os.environ["STATUS_JSON"])
seg = status.get("scene_segments")
if seg is None:
  print("FAIL: status missing scene_segments (add it to status output).")
  sys.exit(1)
if seg <= 0:
  print(f"FAIL: scene_segments={seg} (scene not visible to text pipeline).")
  sys.exit(1)
print(f"OK: scene_segments={seg}")
PY
STATUS_JSON="${STATUS}" >/dev/null

echo
echo "[3/3] look (must not be placeholder)"
LOOK="$(curl -sS -X POST "${RUNTIME}/command" \
  -H 'Content-Type: application/json' \
  -d '{"text":"look"}')"
echo "${LOOK}" | python3 -m json.tool

python3 - <<'PY'
import json, os, sys
look = json.loads(os.environ["LOOK_JSON"])
text = (look.get("text") or "").strip()
if text == "The scene stretches before you.":
  print("FAIL: look returned placeholder text.")
  sys.exit(1)
if not text:
  print("FAIL: look returned empty text.")
  sys.exit(1)
print("OK: look produced narrative text.")
PY
LOOK_JSON="${LOOK}" >/dev/null

echo
echo "SMOKE PASS"
