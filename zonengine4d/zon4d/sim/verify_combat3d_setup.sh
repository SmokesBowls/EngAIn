#!/bin/bash
# verify_combat3d_setup.sh - FINAL VERSION
# Verifies Combat3D setup is ready to run

echo "========================================"
echo "Combat3D Setup Verification"
echo "========================================"
echo ""

# Check Python files
echo "[1/5] Checking Python runtime files..."

if [ -f "sim_runtime_file_test.py" ]; then
    echo "  ✓ sim_runtime_file_test.py found"
    
    # Check for atomic writes
    if grep -q "os.replace" sim_runtime_file_test.py; then
        echo "  ✓ Atomic writes implemented"
    else
        echo "  ⚠ WARNING: Atomic writes missing (may cause parse errors)"
    fi
    
    # Check for static entity spawning
    if grep -q '"static": True' sim_runtime_file_test.py; then
        echo "  ✓ Static entity spawning enabled"
    else
        echo "  ⚠ WARNING: Static spawning missing (entities may fall)"
    fi
else
    echo "  ✗ sim_runtime_file_test.py NOT FOUND"
    echo "    Run this script from: ~/Downloads/EngAIn/zonengine4d/zon4d/sim"
    exit 1
fi

echo ""

# Check adapter files
echo "[2/5] Checking adapter dependencies..."
ALL_ADAPTERS_FOUND=true

for file in spatial3d_adapter.py perception_adapter.py navigation_adapter.py combat3d_adapter.py; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
        ALL_ADAPTERS_FOUND=false
    fi
done

if [ "$ALL_ADAPTERS_FOUND" = false ]; then
    echo "  ⚠ Some adapters missing - Python runtime may fail"
fi

echo ""

# Check Godot project
echo "[3/5] Checking Godot project..."

# Try multiple possible paths
GODOT_ROOT=""
if [ -f "$HOME/Downloads/EngAIn/godot/project.godot" ]; then
    GODOT_ROOT="$HOME/Downloads/EngAIn/godot"
elif [ -f "../../../godot/project.godot" ]; then
    GODOT_ROOT="../../../godot"
elif [ -f "../../../../godot/project.godot" ]; then
    GODOT_ROOT="../../../../godot"
fi

if [ -n "$GODOT_ROOT" ]; then
    echo "  ✓ Godot project found: $GODOT_ROOT"
    
    # Check for GDScript client
    if [ -f "$GODOT_ROOT/scripts/sim_client_file_test.gd" ]; then
        echo "  ✓ sim_client_file_test.gd found"
    else
        echo "  ⚠ sim_client_file_test.gd MISSING"
        echo "    Copy to: $GODOT_ROOT/scripts/"
    fi
    
    # Check for test scene
    if [ -f "$GODOT_ROOT/combat_test.tscn" ]; then
        echo "  ✓ combat_test.tscn found"
    else
        echo "  ⚠ combat_test.tscn not created yet"
        echo "    Follow COMPLETE_SETUP_GUIDE.md"
    fi
else
    echo "  ⚠ Godot project not found"
    echo "    Expected: ~/Downloads/EngAIn/godot/"
    echo "    This is OK if you haven't set up Godot yet"
fi

echo ""

# Check runtime communication
echo "[4/5] Checking runtime communication..."

SNAPSHOT="/tmp/engain_snapshot.json"
COMMAND="/tmp/engain_command.json"

if [ -f "$SNAPSHOT" ]; then
    # Check file size
    if [ -s "$SNAPSHOT" ]; then
        echo "  ✓ Snapshot file exists and has content"
        
        # Validate JSON
        if python3 -c "import json; json.load(open('$SNAPSHOT'))" 2>/dev/null; then
            echo "  ✓ Snapshot JSON is valid"
            
            # Count entities
            ENTITY_COUNT=$(python3 -c "import json; print(len(json.load(open('$SNAPSHOT')).get('entities', {})))" 2>/dev/null)
            echo "  ✓ Contains $ENTITY_COUNT entities"
        else
            echo "  ✗ Snapshot JSON is INVALID"
            echo "    This will cause parse errors in Godot"
        fi
    else
        echo "  ⚠ Snapshot file exists but is empty"
        echo "    Python runtime may have just started"
    fi
else
    echo "  ⚠ Snapshot file not found"
    echo "    Start Python runtime: python3 sim_runtime_file_test.py"
fi

echo ""

# Entity health check
echo "[5/5] Checking entity states..."

if [ -f "$SNAPSHOT" ]; then
    python3 << 'EOF' 2>/dev/null
import json
try:
    data = json.load(open('/tmp/engain_snapshot.json'))
    entities = data.get('entities', {})
    
    if not entities:
        print("  ⚠ No entities in snapshot")
    else:
        for eid, edata in entities.items():
            pos = edata.get('pos', [0,0,0])
            health = edata.get('health', 0)
            max_health = edata.get('max_health', 100)
            state = edata.get('state', 'unknown')
            alive = edata.get('alive', False)
            
            # Check if entity is falling
            if abs(pos[1]) > 1.0:
                status = "✗ FALLING"
            elif not alive:
                status = "✓ dead"
            else:
                status = "✓ alive"
            
            print(f"  {status} {eid}: pos={pos}, health={health}/{max_health}, state={state}")
except Exception as e:
    print(f"  ✗ Error reading snapshot: {e}")
EOF
else
    echo "  ⚠ Cannot check entities (snapshot file missing)"
fi

echo ""
echo "========================================"
echo "Verification Summary"
echo "========================================"
echo ""

# Final verdict
READY=true

if [ ! -f "sim_runtime_file_test.py" ]; then
    echo "✗ Python runtime missing"
    READY=false
fi

if [ "$ALL_ADAPTERS_FOUND" = false ]; then
    echo "⚠ Some adapters missing"
fi

if [ -f "$SNAPSHOT" ]; then
    echo "✓ Python runtime appears to be running"
else
    echo "⚠ Python runtime not started yet"
fi

if [ -n "$GODOT_ROOT" ]; then
    echo "✓ Godot project found"
else
    echo "⚠ Godot project not found (setup needed)"
fi

echo ""

if [ "$READY" = true ]; then
    echo "Status: READY ✓"
    echo ""
    echo "To run:"
    echo "  1. Terminal: python3 sim_runtime_file_test.py"
    echo "  2. Godot: Open combat_test.tscn and press F5"
    echo "  3. Test: Press SPACE to attack"
else
    echo "Status: NOT READY ✗"
    echo ""
    echo "Fix the issues above, then re-run this script."
fi

echo ""
