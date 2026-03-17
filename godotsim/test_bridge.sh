#!/bin/bash
# test_bridge.sh — Verify semantic bridge wiring with vault preloading
# Run with: bash test_bridge.sh
# Assumes sim_runtime is running on localhost:8080

# --- Configuration (EDIT THESE TO MATCH YOUR SYSTEM) ---
VAULT_ROOT="/home/burdens/obsidian/obsidianburdenNov25"
MANIFEST_PATH="/home/burdens/obsidian/obsidianburdenNov25/vault.manifest.json"
SCENE_ID="scene.04_the_convergence"   # A scene that exists in your vault
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
MANIFEST_CONTENT=$(python3 -c "
import json, sys
with open('$MANIFEST_PATH') as f:
    data = json.load(f)
print(json.dumps(data))
")

VAULT_PAYLOAD=$(jq -n \
    --arg root "$VAULT_ROOT" \
    --argjson manifest "$MANIFEST_CONTENT" \
    '{vault_root: $root, manifest: $manifest}')

VAULT_RESPONSE=$(curl -sS -X POST http://127.0.0.1:8080/vault/link \
    -H "Content-Type: application/json" \
    -d "$VAULT_PAYLOAD" 2>&1)

# Check for actual error
if echo "$VAULT_RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
    echo "❌ Vault linking failed:"
    echo "   $VAULT_RESPONSE"
    exit 1
elif echo "$VAULT_RESPONSE" | jq -e '.status == "ok"' >/dev/null 2>&1; then
    echo "$VAULT_RESPONSE" | jq '.'
else
    echo "⚠️  Unexpected response:"
    echo "   $VAULT_RESPONSE"
    exit 1
fi
echo ""

# 4. Load a test scene by ID (from vault) — using ZONJ @id format
echo "4. Loading scene '$SCENE_ID' from vault..."
SCENE_LOAD_RESPONSE=$(curl -sS -X POST http://localhost:8080/scene/load \
    -H 'Content-Type: application/json' \
    -d "{\"@id\":\"$SCENE_ID\"}" 2>&1)

# Try to pretty-print if JSON, otherwise show raw
if echo "$SCENE_LOAD_RESPONSE" | jq -e . >/dev/null 2>&1; then
    echo "$SCENE_LOAD_RESPONSE" | jq '.'
else
    echo "   (raw response) $SCENE_LOAD_RESPONSE"
fi
echo ""

# 5. Check snapshot for bridge_entities
echo ""
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
PY <<<"$snap"

echo "6. Quick look command..."
LOOK_RESPONSE=$(curl -sS -X POST http://localhost:8080/command \
    -H 'Content-Type: application/json' \
    -d '{"command": "look"}' 2>&1)

if echo "$LOOK_RESPONSE" | jq -e . >/dev/null 2>&1; then
    echo "$LOOK_RESPONSE" | jq '.'
else
    echo "   (raw response) $LOOK_RESPONSE"
fi
echo ""

echo "=== Test Complete ==="
