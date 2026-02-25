#!/bin/bash
# Find boundary violations in core/
# Run from: ~/Downloads/EngAIn/godotengain/engainos/

echo "======================================================================"
echo "FINDING BOUNDARY VIOLATIONS"
echo "======================================================================"

cd core/

echo ""
echo "Searching for 'import godot' in core/..."
echo ""

# Find all violations
VIOLATIONS=$(grep -rn "import godot\|from godot" . --include="*.py" 2>/dev/null)

if [ -z "$VIOLATIONS" ]; then
    echo "✓ No violations found (strange - bootstrap detected one)"
    echo ""
    echo "Checking for subtle variations..."
    grep -rn "godot" . --include="*.py" | grep -i "import"
else
    echo "Found violations:"
    echo ""
    echo "$VIOLATIONS"
    echo ""
    echo "======================================================================"
    echo "VIOLATION DETAILS"
    echo "======================================================================"
    echo ""
    
    # Show each file with context
    while IFS= read -r line; do
        file=$(echo "$line" | cut -d: -f1)
        lineno=$(echo "$line" | cut -d: -f2)
        
        echo "File: $file"
        echo "Line: $lineno"
        echo "Context:"
        sed -n "$((lineno-2)),$((lineno+2))p" "$file" | nl -v $((lineno-2))
        echo ""
        echo "---"
        echo ""
    done <<< "$VIOLATIONS"
fi

echo ""
echo "======================================================================"
echo "RECOMMENDED FIXES"
echo "======================================================================"
echo ""
echo "Option 1: Remove the import if unused"
echo "  - Edit the file and delete the import line"
echo ""
echo "Option 2: Move file to godot/ if it's actually Godot code"
echo "  - mv core/filename.py godot/"
echo ""
echo "Option 3: Refactor to remove Godot dependency"
echo "  - Core should never know about Godot"
echo "  - Godot imports from core, not vice versa"
echo ""
echo "======================================================================"
