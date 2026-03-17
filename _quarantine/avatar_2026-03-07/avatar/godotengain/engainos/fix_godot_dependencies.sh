#!/bin/bash
# Fix missing Godot script dependencies
# The scene expects files in res:// root, but they were moved

cd ~/Downloads/EngAIn/godotengain/engainos

echo "======================================================================"
echo "FIXING MISSING GODOT SCRIPT DEPENDENCIES"
echo "======================================================================"
echo ""

# Files that Godot expects in res:// (project root)
MISSING_FILES=(
    "ClickablePlaceholder.gd"
    "test_bridge.gd"
)

echo "Godot scene expects these files in res:// (engainos/ root):"
for file in "${MISSING_FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "Checking locations..."
echo ""

# Check if files exist in godot/ subdirectory
for file in "${MISSING_FILES[@]}"; do
    echo "[$file]"
    
    if [ -f "$file" ]; then
        echo "  ✓ Already in res:// root"
    elif [ -f "godot/$file" ]; then
        echo "  ⚠ Found in godot/ subdirectory"
        echo "    Copying to res:// root..."
        cp "godot/$file" "$file"
        echo "  ✓ Copied to res://$file"
    elif [ -f "godot/scripts/$file" ]; then
        echo "  ⚠ Found in godot/scripts/"
        echo "    Copying to res:// root..."
        cp "godot/scripts/$file" "$file"
        echo "  ✓ Copied to res://$file"
    else
        echo "  ✗ Not found anywhere"
        echo "    Need to create stub"
        
        # Create minimal stub
        if [ "$file" = "ClickablePlaceholder.gd" ]; then
            cat > "$file" << 'EOF'
extends MeshInstance3D
# Minimal ClickablePlaceholder stub
# TODO: Implement full functionality

func _ready():
    print("ClickablePlaceholder ready")
EOF
            echo "  ✓ Created stub: $file"
            
        elif [ "$file" = "test_bridge.gd" ]; then
            cat > "$file" << 'EOF'
extends Node
# Minimal test_bridge stub
# TODO: Implement full functionality

func _ready():
    print("TestBridge ready")
EOF
            echo "  ✓ Created stub: $file"
        fi
    fi
    
    echo ""
done

echo "======================================================================"
echo "VERIFICATION"
echo "======================================================================"
echo ""

for file in "${MISSING_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists in res://"
    else
        echo "✗ $file still missing"
    fi
done

echo ""
echo "======================================================================"
echo "NEXT STEPS"
echo "======================================================================"
echo ""
echo "1. Restart Godot scene (or reload project)"
echo "2. Click 'Fix Dependencies' in the error dialog"
echo "3. Scene should load without errors"
echo ""
echo "If files were created as stubs, you may need to implement"
echo "full functionality based on your godot/ directory files."
echo "======================================================================"
