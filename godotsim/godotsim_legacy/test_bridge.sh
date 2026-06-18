#!/usr/bin/env bash
set -e

json_get() {
    python3 - "$1" "$2" <<'PYJSON'
import json
import sys

raw = sys.argv[1]
key = sys.argv[2]

try:
    data = json.loads(raw)
except Exception:
    sys.exit(1)

cur = data
for part in key.split("."):
    if isinstance(cur, dict) and part in cur:
        cur = cur[part]
    else:
        sys.exit(1)

if isinstance(cur, bool):
    print("true" if cur else "false")
elif cur is None:
    print("null")
else:
    print(cur)
PYJSON
}

json_pretty() {
    python3 - "$1" <<'PYJSON'
import json
import sys

raw = sys.argv[1]
try:
    print(json.dumps(json.loads(raw), indent=2))
except Exception:
    print(raw)
PYJSON
}

json_valid() {
    python3 - "$1" <<'PYJSON'
import json
import sys

try:
    json.loads(sys.argv[1])
    sys.exit(0)
except Exception:
    sys.exit(1)
PYJSON
}

#!/bin/bash
# test_bridge.sh — Verify semantic bridge wiring with vault preloading
# Run with: bash test_bridge.sh
# Assumes sim_runtime is running on localhost:8080

# --- Configuration (EDIT THESE TO MATCH YOUR SYSTEM) ---
VAULT_ROOT="${ENGAIN_VAULT_ROOT:-/home/mytruelove/Downloads/obsidianburdenNov25}"
MANIFEST_PATH="${ENGAIN_VAULT_ROOT:-/home/mytruelove/Downloads/obsidianburdenNov25}/vault.manifest.json"
SCENE_ID="scene.004_the_convergence"   # A scene that exists in your vault
# -------------------------------------------------------

echo "=== Semantic Bridge Integration Test (with Vault) ==="
echo ""

# 1. Check server health
echo "1. Health check..."
if ! curl -sS http://localhost:8080/health > /dev/null; then
    echo "❌ Server not reachable. Is sim_runtime running on port 8080?"
    exit 1
fi
curl -sS http://localhost:8080/health | python3 -m json.tool 2>/dev/null || echo "   (non-JSON response)"
echo ""

# 2. Verify vault paths exist
echo "2. Checking vault paths..."
if [ ! -d "$VAULT_ROOT" ]; then
    echo "❌ Vault root not found: $VAULT_ROOT"
    exit 1
fi
if [ ! -f "$MANIFEST_PATH" ]; then
    echo "❌ Manifest not found: $MANIFEST_PATH"
    exit 1
fi
echo "   Vault paths OK."
echo ""

# 3. Read manifest content and link vault
echo "3. Linking vault (sending manifest content)..."
VAULT_PAYLOAD=$(python3 - "$VAULT_ROOT" "$MANIFEST_PATH" <<'PYJSON'
import json
import sys
from pathlib import Path

vault_root = sys.argv[1]
manifest_path = Path(sys.argv[2])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

print(json.dumps({
    "vault_root": vault_root,
    "manifest": manifest,
}))
PYJSON
)

VAULT_RESPONSE=$(curl -sS -X POST http://127.0.0.1:8080/vault/link \
    -H "Content-Type: application/json" \
    -d "$VAULT_PAYLOAD" 2>&1)

# Check for actual error
if json_get "$VAULT_RESPONSE" "error" >/dev/null 2>&1; then
    echo "❌ Vault linking failed:"
    echo "   $VAULT_RESPONSE"
    exit 1
elif [ "$(json_get "$VAULT_RESPONSE" "status" 2>/dev/null || true)" = "ok" ]; then
    json_pretty "$VAULT_RESPONSE"
else
    echo "⚠️  Unexpected response:"
    echo "   $VAULT_RESPONSE"
    exit 1
fi
echo ""

# 4. Load a test scene by ID (from vault) — using ZONJ @id format
echo "4. Scene load contract check..."
echo "   Vault link registered scene IDs, including: $SCENE_ID"
echo "   NOTE: /scene/load expects full ZONJ payload with scene_id/id + segments."
echo "   NOTE: test_bridge.sh will not call /scene/load by ID because that contract is invalid."
echo
echo "5. Checking snapshot for bridge_entities..."

# Pull snapshot and parse payload.bridge_entities (retry briefly in case of timing jitter)
snap=""
for i in $(seq 1 10); do
  snap="$(curl -sS http://127.0.0.1:8080/snapshot || true)"
  count="$(python3 -c 'import sys,json; 
d=json.loads(sys.stdin.read() or "{}"); 
p=d.get("payload",{}); 
be=p.get("bridge_entities") or []; 
print(len(be))' <<<"$snap" 2>/dev/null || echo 0)"
  if [ "$count" -gt 0 ]; then
    break
  fi
  sleep 0.2
done

python3 - <<'PY'
import json, sys

try:
    d = json.loads(sys.stdin.read() or "{}")
except Exception:
    d = {}

p = d.get("payload", {}) if isinstance(d, dict) else {}
scene_id = p.get("scene_id") or "none"
scene_ok = isinstance(p.get("scene"), dict)
be = p.get("bridge_entities") or []
entities_map = p.get("entities") or {}
spatial_map = (p.get("spatial") or {}).get("entities") or {}

print(f"  Scene: {scene_id}")
print(f"  Has payload.scene: {scene_ok}")
print(f"  Bridge entities: {len(be)}")
print(f"  payload.entities map: {len(entities_map) if isinstance(entities_map, dict) else 0}")
print(f"  payload.spatial.entities map: {len(spatial_map) if isinstance(spatial_map, dict) else 0}")

if not be:
    print("")
    print("  ✗ No bridge_entities in snapshot")
    print("    (This script reads payload.bridge_entities. If it stays empty, check sim_runtime snapshot hydration.)")
else:
    e = be[0] if isinstance(be[0], dict) else {}
    print(f"  Sample: {e.get('entity_id')} {e.get('placeholder_mesh')} {e.get('position')}")
PY

echo "6. Quick look command..."
LOOK_RESPONSE=$(curl -sS -X POST http://localhost:8080/command \
    -H 'Content-Type: application/json' \
    -d '{"command": "look", "reality_mode": "DRAFT", "actor_authority_tier": 3, "actor_id": "test_bridge", "source_system": "godotsim/test_bridge"}' 2>&1)

if json_valid "$LOOK_RESPONSE"; then
    json_pretty "$LOOK_RESPONSE"
else
    echo "   (raw response) $LOOK_RESPONSE"
fi
echo ""

echo "=== Test Complete ==="
