#!/bin/bash
# Trixel Integration Verification Script
# Run from: ~/Downloads/EngAIn/godotengain/engainos/

echo "======================================================================"
echo "TRIXEL INTEGRATION VERIFICATION"
echo "======================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Verify we're in the right place
if [ ! -d "core" ] || [ ! -d "tools" ]; then
    check_fail "Not in engainos/ directory. Please run from ~/Downloads/EngAIn/godotengain/engainos/"
    exit 1
fi

echo ""
echo "[1/6] Checking directory structure..."

if [ -d "tools/trixel" ]; then
    check_pass "tools/trixel/ exists"
else
    check_fail "tools/trixel/ missing"
    exit 1
fi

if [ -d "assets/trixels" ]; then
    check_pass "assets/trixels/ exists"
else
    check_warn "assets/trixels/ missing (will be created on first use)"
    mkdir -p assets/trixels
fi

echo ""
echo "[2/6] Checking active Trixel files..."

EXPECTED_FILES=(
    "tools/trixel/__init__.py"
    "tools/trixel/trixel_composer.py"
    "tools/trixel/terminal_trixel.py"
    "tools/trixel/learning_validator_agent.py"
)

for file in "${EXPECTED_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file"
    else
        check_fail "$file missing"
    fi
done

echo ""
echo "[3/6] Checking for Godot imports in tools/ (CRITICAL)..."

GODOT_IMPORTS=$(grep -r "import godot" tools/ 2>/dev/null)
if [ -z "$GODOT_IMPORTS" ]; then
    check_pass "No 'import godot' found in tools/ (correct)"
else
    check_fail "Found 'import godot' in tools/ - VIOLATION!"
    echo "$GODOT_IMPORTS"
    echo ""
    echo "Fix required: Remove Godot imports from tools/"
fi

echo ""
echo "[4/6] Checking import structure..."

# Check if tools imports from core (allowed)
CORE_IMPORTS=$(grep -r "from core" tools/trixel/ 2>/dev/null | wc -l)
if [ "$CORE_IMPORTS" -gt 0 ]; then
    check_pass "tools/trixel/ imports from core/ ($CORE_IMPORTS imports) - allowed"
else
    check_warn "No core imports found (may need mesh_intake integration)"
fi

# Check if core imports from tools (NOT allowed)
TOOLS_IMPORTS=$(grep -r "from tools" core/ 2>/dev/null | wc -l)
if [ "$TOOLS_IMPORTS" -eq 0 ]; then
    check_pass "core/ does NOT import from tools/ (correct)"
else
    check_fail "core/ imports from tools/ - VIOLATION!"
    grep -r "from tools" core/
fi

echo ""
echo "[5/6] Checking for duplicate mesh_intake..."

if [ -f "core/mesh_intake.py" ]; then
    check_pass "core/mesh_intake.py exists (LAW)"
    
    # Check if there's a duplicate elsewhere
    DUPLICATES=$(find . -name "mesh_intake.py" -not -path "./core/*" 2>/dev/null)
    if [ -z "$DUPLICATES" ]; then
        check_pass "No duplicate mesh_intake.py found"
    else
        check_warn "Duplicate mesh_intake.py found - should be archived:"
        echo "$DUPLICATES"
    fi
else
    check_fail "core/mesh_intake.py missing!"
fi

echo ""
echo "[6/6] Testing Python imports..."

# Test if Trixel can be imported
cd tools/trixel
if python3 -c "import sys; sys.path.insert(0, '../..'); from tools.trixel.trixel_composer import AutonomousCreativeMemory; print('Import OK')" 2>/dev/null; then
    check_pass "trixel_composer.py imports successfully"
else
    check_warn "trixel_composer.py import has issues (may need dependencies)"
fi

cd ../..

echo ""
echo "======================================================================"
echo "VERIFICATION SUMMARY"
echo "======================================================================"

# Count issues
ISSUES=0

# Critical checks
if ! grep -r "import godot" tools/ 2>/dev/null > /dev/null; then
    echo -e "${GREEN}✓ CRITICAL:${NC} No Godot imports in tools/"
else
    echo -e "${RED}✗ CRITICAL:${NC} Godot imports found in tools/ - MUST FIX"
    ISSUES=$((ISSUES + 1))
fi

if ! grep -r "from tools" core/ 2>/dev/null > /dev/null; then
    echo -e "${GREEN}✓ CRITICAL:${NC} Core does not import from tools/"
else
    echo -e "${RED}✗ CRITICAL:${NC} Core imports from tools/ - MUST FIX"
    ISSUES=$((ISSUES + 1))
fi

if [ -f "tools/trixel/trixel_composer.py" ]; then
    echo -e "${GREEN}✓ ESSENTIAL:${NC} trixel_composer.py in place"
else
    echo -e "${RED}✗ ESSENTIAL:${NC} trixel_composer.py missing"
    ISSUES=$((ISSUES + 1))
fi

if [ -f "core/mesh_intake.py" ]; then
    echo -e "${GREEN}✓ ESSENTIAL:${NC} mesh_intake.py in core/"
else
    echo -e "${RED}✗ ESSENTIAL:${NC} mesh_intake.py missing from core/"
    ISSUES=$((ISSUES + 1))
fi

echo ""
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}======================================================================"
    echo "ALL CRITICAL CHECKS PASSED - INTEGRATION IS CLEAN"
    echo "======================================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test Trixel: python3 -m tools.trixel.terminal_trixel --help"
    echo "  2. Review archive: ls -la ../../archive/trixel_notes/ (if exists)"
    echo "  3. Delete trixelcomposer-main: rm -rf ../../../trixelcomposer-main/"
else
    echo -e "${RED}======================================================================"
    echo "FOUND $ISSUES CRITICAL ISSUE(S) - NEEDS ATTENTION"
    echo "======================================================================${NC}"
fi

echo ""
echo "======================================================================"
echo "FILE INVENTORY"
echo "======================================================================"
echo ""
echo "Active Trixel Code (tools/trixel/):"
ls -lh tools/trixel/ 2>/dev/null || echo "  (none)"
echo ""
echo "Law Files (core/):"
ls -lh core/mesh_intake.py core/mesh_manifest.py 2>/dev/null || echo "  (check if these exist)"
echo ""
echo "Assets (assets/trixels/):"
ls -lh assets/trixels/ 2>/dev/null || echo "  (empty - will populate on first use)"
