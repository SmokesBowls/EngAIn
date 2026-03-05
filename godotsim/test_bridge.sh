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
echo "5. Checking snapshot for bridge_entities..."
SNAPSHOT=$(curl -sS http://localhost:8080/snapshot 2>/dev/null)

if echo "$SNAPSHOT" | jq -e . >/dev/null 2>&1; then
    echo "$SNAPSHOT" | jq -r '
      .snapshot // . |
      "  Scene: " + (.scene_id // "none") +
      "\n  Bridge entities: " + (if .bridge_entities then (.bridge_entities | length | tostring) else "0" end) +
      "\n"
    ' 2>/dev/null

    echo "$SNAPSHOT" | jq -r '
      .snapshot // . |
      if .bridge_entities then
        .bridge_entities[] | "  [" + (.name // "?") + "] concept=" + (.zw_concept // "?") + 
        " mesh=" + (.placeholder_mesh // "?") + 
        " color=" + (.color_hex // "?") + 
        " pos=(" + (if .transform.position then "\(.transform.position.x // 0),\(.transform.position.y // 0),\(.transform.position.z // 0)" else "0,0,0" end) + ")" +
        " placeholder=\(.is_placeholder // true)"
      else
        "  ✗ No bridge_entities in snapshot\n    Check: is bridge_integration.py in godotsim/?\n    Check: is concept_profiles.json in godotsim/?\n    Check: is spatial_skin_system.py in godotsim/?\n    Also verify vault linking succeeded (step 3)."
      end
    ' 2>/dev/null
else
    echo "   Snapshot not valid JSON: $SNAPSHOT"
fi
echo ""

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
