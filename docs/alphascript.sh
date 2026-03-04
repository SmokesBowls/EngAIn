#!/usr/bin/env bash
# engain_alpha.sh (fixed + clears port)
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
BASE_URL="http://${HOST}:${PORT}"

PYTHON="${PYTHON:-python3}"
RUNTIME_PY="${RUNTIME_PY:-/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py}"
START_ARGS="${START_ARGS:-}"

LOG_DIR="${LOG_DIR:-./.engain_logs}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
SERVER_LOG="${LOG_DIR}/server_${STAMP}.log"
SERVER_PID_FILE="${LOG_DIR}/server_${PORT}.pid"

say() { printf "\n[%s] %s\n" "$(date +%H:%M:%S)" "$*"; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1" >&2; exit 1; }; }

need_cmd curl
need_cmd "$PYTHON"

port_owner() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true
  elif command -v ss >/dev/null 2>&1; then
    ss -lptn "sport = :$PORT" 2>/dev/null || true
  else
    echo "(no lsof/ss available)"
  fi
}

free_port() {
  say "Port ownership BEFORE clear:"
  port_owner

  say "Clearing port ${PORT}..."

  # kill recorded PID
  if [[ -f "$SERVER_PID_FILE" ]]; then
    oldpid="$(cat "$SERVER_PID_FILE" 2>/dev/null || true)"
    if [[ -n "${oldpid:-}" ]] && kill -0 "$oldpid" >/dev/null 2>&1; then
      say "Killing recorded PID ${oldpid}"
      kill "$oldpid" >/dev/null 2>&1 || true
      sleep 0.4
      kill -9 "$oldpid" >/dev/null 2>&1 || true
    fi
    rm -f "$SERVER_PID_FILE" || true
  fi

  # kill current listener(s)
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${pids:-}" ]]; then
      say "Killing listener(s) on ${PORT}: ${pids}"
      kill ${pids} >/dev/null 2>&1 || true
      sleep 0.4
      kill -9 ${pids} >/dev/null 2>&1 || true
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
  fi

  sleep 0.2
  say "Port ownership AFTER clear:"
  port_owner
}

start_server() {
  [[ -f "$RUNTIME_PY" ]] || { echo "ERROR: missing RUNTIME_PY: $RUNTIME_PY" >&2; exit 1; }

  say "Starting runtime:"
  say "  ${PYTHON} ${RUNTIME_PY} ${START_ARGS}"
  say "Log: ${SERVER_LOG}"

  nohup "$PYTHON" "$RUNTIME_PY" ${START_ARGS} >"$SERVER_LOG" 2>&1 &
  pid=$!
  echo "$pid" >"$SERVER_PID_FILE"
  say "Server PID: $pid"
}

get_to_file() {
  # prints HTTP code; writes body to file
  local url="$1"
  local out="$2"
  curl -sS -m 2 -o "$out" -w "%{http_code}" "$url" || echo "000"
}

post_to_file() {
  # prints HTTP code; writes body to file
  local path="$1"
  local payload="$2"
  local out="$3"
  curl -sS -m 5 -o "$out" -w "%{http_code}" -X POST "${BASE_URL}${path}" \
    -H 'Content-Type: application/json' \
    -d "$payload" || echo "000"
}

require_json_200() {
  local code="$1"
  local file="$2"
  local label="$3"

  if [[ "$code" != "200" ]]; then
    say "ERROR: ${label} -> HTTP ${code}"
    say "Body (first 400 chars):"
    head -c 400 "$file" || true
    echo
    return 1
  fi

  if ! "$PYTHON" -m json.tool <"$file" >/dev/null 2>&1; then
    say "ERROR: ${label} -> HTTP 200 but body is not valid JSON"
    say "Body (first 400 chars):"
    head -c 400 "$file" || true
    echo
    return 1
  fi

  "$PYTHON" -m json.tool <"$file"
}

wait_health() {
  say "Waiting for ${BASE_URL}/health (HTTP 200 + JSON)..."
  local tries=80
  local tmp
  tmp="$(mktemp)"

  for i in $(seq 1 "$tries"); do
    local code
    code="$(get_to_file "${BASE_URL}/health" "$tmp")"

    if [[ "$code" == "200" ]] && "$PYTHON" -m json.tool <"$tmp" >/dev/null 2>&1; then
      say "Health OK:"
      "$PYTHON" -m json.tool <"$tmp"
      rm -f "$tmp"
      return 0
    fi

    if (( i % 10 == 0 )); then
      say "health not ready (try ${i}/${tries}): HTTP ${code}, sample: $(head -c 120 "$tmp" 2>/dev/null || true)"
    fi
    sleep 0.25
  done

  say "FAIL: /health never became JSON/200."
  say "---- server log tail ----"
  tail -n 200 "$SERVER_LOG" || true
  rm -f "$tmp"
  return 1
}

smoke_test() {
  local tmp
  tmp="$(mktemp)"

  say "POST /world/sync dry_run=true"
  code="$(post_to_file "/world/sync" '{"dry_run": true}' "$tmp")"
  require_json_200 "$code" "$tmp" "world/sync dry_run=true"

  say "POST /world/sync dry_run=false"
  code="$(post_to_file "/world/sync" '{"dry_run": false}' "$tmp")"
  require_json_200 "$code" "$tmp" "world/sync dry_run=false"

  say "POST /world/load_mirror"
  code="$(post_to_file "/world/load_mirror" '{}' "$tmp")"
  require_json_200 "$code" "$tmp" "world/load_mirror"

  say "POST /command status"
  code="$(post_to_file "/command" '{"text":"status"}' "$tmp")"
  require_json_200 "$code" "$tmp" "command status"

  say "POST /command look"
  code="$(post_to_file "/command" '{"text":"look"}' "$tmp")"
  require_json_200 "$code" "$tmp" "command look"

  rm -f "$tmp"
}

on_fail() {
  say "SCRIPT FAILED."
  say "Port ownership NOW:"
  port_owner
  say "---- server log tail ----"
  tail -n 250 "$SERVER_LOG" || true
}
trap on_fail ERR

main() {
  free_port
  start_server
  wait_health
  smoke_test
  say "OK. PID file: $SERVER_PID_FILE"
}

main "$@"
