#!/bin/bash
# verify_combat3d_setup.sh
# Quick verification that Combat3D is ready to run

echo "========================================"
echo "Combat3D Setup Verification"
echo "========================================"
echo ""

# Check Python files
echo "[1/5] Checking Python files..."
if [ -f "sim_runtime_file_test.py" ]; then
    echo "  ✓ sim_runtime_file_test.py found"
    
    # Check for atomic writes
    if grep -q "os.replace" sim_runtime_file_test.py; then
        echo "  ✓ Atomic writes implemented"
    else
        echo "  ✗ WARNING: Atomic writes missing"
    fi
    
    # Check for static entity spawning
    if grep -q '"static": True' sim_runtime_file_test.py; then
        echo "  ✓ Static entity spawning enabled"
    else
        echo "  ✗ WARNING: Entities may fall"
    fi
else
    echo "  ✗ sim_runtime_file_test.py NOT FOUND"
    echo "    Run from: ~/Downloads/EngAIn/zonengine4d/zon4d/sim"
    exit 1
fi

echo ""

# Check adapters
echo "[2/5] Checking adapter files..."
for file in spatial3d_adapter.py perception_adapter.py navigation_adapter.py combat3d_adapter.py; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
    fi
done

echo ""

# Check Godot project
echo "[3/5] Checking Godot files..."
GODOT_DIR="../../../godot"
if [ -d "$GODOT_DIR" ]; then
    echo "  ✓ Godot directory found"
    
    if [ -f "$GODOT_DIR/scripts/sim_client_file_test.gd" ]; then
        echo "  ✓ sim_client_file_test.gd found"
    else
        echo "  ✗ sim_client_file_test.gd MISSING"
        echo "    Copy from outputs to: $GODOT_DIR/scripts/"
    fi
else
    echo "  ✗ Godot directory not found at: $GODOT_DIR"
fi

echo ""

# Check file paths
echo "[4/5] Checking communication files..."
SNAPSHOT="/tmp/engain_snapshot.json"
COMMAND="/tmp/engain_command.json"

if [ -f "$SNAPSHOT" ]; then
    SIZE=$(stat -f%z "$SNAPSHOT" 2>/dev/null || stat -c%s "$SNAPSHOT" 2>/dev/null)
    if [ "$SIZE" -gt 100 ]; then
        echo "  ✓ Snapshot file exists and has content ($SIZE bytes)"
        echo "  ℹ Python runtime appears to be running"
    else
        echo "  ⚠ Snapshot file exists but is small ($SIZE bytes)"
        echo "    Python runtime may have just started"
    fi
else
    echo "  ⚠ Snapshot file not found (Python not running yet)"
    echo "    Start: python3 sim_runtime_file_test.py"
fi

if [ -f "$COMMAND" ]; then
    echo "  ℹ Command file exists (Godot sent command)"
else
    echo "  ⚠ Command file not found (Godot not running or no input yet)"
fi

echo ""

# Test JSON validity
echo "[5/5] Testing snapshot JSON..."
if [ -f "$SNAPSHOT" ]; then
    if python3 -c "import json; json.load(open('$SNAPSHOT'))" 2>/dev/null; then
        echo "  ✓ Snapshot JSON is valid"
        
        # Check entities
        ENTITIES=$(python3 -c "import json; print(len(json.load(open('$SNAPSHOT')).get('entities', {})))" 2>/dev/null)
        echo "  ✓ Contains $ENTITIES entities"
        
        # Check entity positions
        python3 -c "
import json
data = json.load(open('$SNAPSHOT'))
for eid, edata in data.get('entities', {}).items():
    pos = edata.get('pos', [0,0,0])
    health = edata.get('health', 0)
    state = edata.get('state', 'unknown')
    print(f'  ℹ {eid}: pos={pos}, health={health}, state={state}')
" 2>/dev/null
        
    else
        echo "  ✗ Snapshot JSON is INVALID"
        echo "    This could cause parse errors in Godot"
    fi
else
    echo "  ⚠ No snapshot to test (Python not running)"
fi

echo ""
echo "========================================"
echo "Verification Complete"
echo "========================================"
echo ""

# Summary and next steps
if [ -f "sim_runtime_file_test.py" ] && [ -f "combat3d_adapter.py" ]; then
    echo "✓ Python side ready"
    echo ""
    echo "To start:"
    echo "  1. python3 sim_runtime_file_test.py"
    echo "  2. Open Godot and run combat_test.tscn"
    echo "  3. Press SPACE to test combat"
else
    echo "✗ Setup incomplete"
    echo ""
    echo "Missing files. Are you in the correct directory?"
    echo "Should be: ~/Downloads/EngAIn/zonengine4d/zon4d/sim"
fi

echo ""
