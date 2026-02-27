#!/usr/bin/env bash
set -euo pipefail

RUNTIME="http://127.0.0.1:8080"
VAULT_ID="${1:-book01_garden_genesis}"
VAULT_ROOT="${2:-/home/burdens/chapters_md}"

echo "[1/3] Link vault"
curl -sS -X POST "${RUNTIME}/vault/link" \
  -H 'Content-Type: application/json' \
  -d "{\"vault_id\":\"${VAULT_ID}\",\"vault_root\":\"${VAULT_ROOT}\"}" | python3 -m json.tool

echo
echo "[2/3] Dry-run world sync (no changes)"
curl -sS -X POST "${RUNTIME}/world/sync" \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}' | python3 -m json.tool

echo
echo "[3/3] Real world sync"
curl -sS -X POST "${RUNTIME}/world/sync" \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": false}' | python3 -m json.tool
