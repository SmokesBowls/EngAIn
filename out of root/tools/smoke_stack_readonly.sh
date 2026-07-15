#!/usr/bin/env bash
set -u

# Read-only local stack smoke test for the current EngAIn checkout.
# No POST requests. No scene loading. No vault linking. No ingest/build writes.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT" || exit 2

TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-2}"
FAILURES=0

json_field_equals() {
  local field="$1"
  local expected="$2"
  local body
  body="$(cat)"
  BODY="$body" python3 - "$field" "$expected" <<'PY'
import json
import os
import sys

field = sys.argv[1]
expected = sys.argv[2]
try:
    data = json.loads(os.environ.get("BODY", ""))
except Exception:
    sys.exit(1)
cur = data
for part in field.split('.'):
    if not isinstance(cur, dict) or part not in cur:
        sys.exit(1)
    cur = cur[part]
if isinstance(cur, bool):
    actual = "true" if cur else "false"
elif cur is None:
    actual = "null"
else:
    actual = str(cur)
sys.exit(0 if actual == expected else 1)
PY
}

check_json_endpoint() {
  local label="$1"
  local url="$2"
  local field="${3:-}"
  local expected="${4:-}"
  local body

  if ! body="$(curl -fsS --max-time "$TIMEOUT_SECONDS" "$url" 2>&1)"; then
    echo "FAIL required $label - $url - $body"
    FAILURES=$((FAILURES + 1))
    return 1
  fi

  if ! printf '%s' "$body" | python3 -m json.tool >/dev/null 2>&1; then
    echo "FAIL required $label - $url - response was not JSON"
    FAILURES=$((FAILURES + 1))
    return 1
  fi

  if [ -n "$field" ]; then
    if ! printf '%s' "$body" | json_field_equals "$field" "$expected"; then
      echo "FAIL required $label - $url - expected JSON field $field=$expected"
      FAILURES=$((FAILURES + 1))
      return 1
    fi
  fi

  echo "PASS required $label - $url"
  return 0
}

check_optional_endpoint() {
  local label="$1"
  local url="$2"
  local body

  if ! body="$(curl -fsS --max-time "$TIMEOUT_SECONDS" "$url" 2>&1)"; then
    echo "SKIP optional $label - $url - not required for current EngAInOS API path ($body)"
    return 0
  fi

  if printf '%s' "$body" | python3 -m json.tool >/dev/null 2>&1; then
    echo "PASS optional $label - $url"
  else
    echo "SKIP optional $label - $url - responded but not JSON"
  fi
}

echo "EngAIn read-only stack smoke"
echo "ROOT: $ROOT"
echo

check_json_endpoint "GodotSim health" "http://127.0.0.1:8080/health" "ok" "true"
check_json_endpoint "GodotSim snapshot" "http://127.0.0.1:8080/snapshot"
check_json_endpoint "EngAInOS FastAPI facade health" "http://127.0.0.1:8090/api/health" "ok" "true"
check_json_endpoint "Trixel tile server health" "http://127.0.0.1:8766/health" "status" "ok"

# 8765 is launch_engine's scene/AP query server. engainos_server.py does not depend on it;
# current /api authority/facade path depends on 8080 via NGAT_RT_BASE_URL instead.
check_optional_endpoint "EngAInOS scene server list_scenes" "http://127.0.0.1:8765/list_scenes"

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "SMOKE PASS: required local EngAIn Python stack services are alive."
  exit 0
fi

echo "SMOKE FAIL: $FAILURES required check(s) failed."
exit 1
