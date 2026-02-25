#!/bin/bash
# EngAIn Tree Cleanup Script
# Organizes loose files, removes duplicates, maintains clean structure

set -e

echo "======================================================================"
echo "ENGAIN TREE CLEANUP"
echo "======================================================================"

# Verify we're in the right place
if [ ! -d "core" ] || [ ! -d "tools" ]; then
    echo "Error: Run from engainos/ directory"
    exit 1
fi

echo ""
echo "[1/6] Creating proper documentation structure..."

# Create docs directory if needed
mkdir -p docs/architecture
mkdir -p docs/completed_sessions
mkdir -p docs/guides

echo "  ✓ Created docs/ structure"

echo ""
echo "[2/6] Moving documentation files to docs/..."

# Move architectural docs
DOC_FILES=(
    "ARCHITECTURE_COMPLETE.md"
    "AUTHORITY_TIER_SPEC_v1.md"
    "DEFENSE_LAYERS_COMPLETE.md"
    "FOUNDATION_COMPLETE.md"
    "MEMORY_LAYERS_COMPLETE.md"
    "EMPIREKERNEL_REALITY_DRIVEN_DEVELOPMENT.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/architecture/
        echo "  ✓ $file → docs/architecture/"
    fi
done

# Move session docs
if [ -f "SESSION_2025-12-28_COMPLETE.md" ]; then
    mv "SESSION_2025-12-28_COMPLETE.md" docs/completed_sessions/
    echo "  ✓ SESSION_2025-12-28_COMPLETE.md → docs/completed_sessions/"
fi

# Move guides
GUIDE_FILES=(
    "FIXES_README.md"
    "GODOT_BRIDGE_README.md"
    "INTEGRATION_MAPPING.md"
    "TRIXEL_INSTALLATION_GUIDE.md"
)

for file in "${GUIDE_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" docs/guides/
        echo "  ✓ $file → docs/guides/"
    fi
done

# Trixel identity goes with Trixel
if [ -f "TRIXEL_IDENTITY.md" ]; then
    mv "TRIXEL_IDENTITY.md" tools/trixel/
    echo "  ✓ TRIXEL_IDENTITY.md → tools/trixel/"
fi

echo ""
echo "[3/6] Cleaning up duplicate/broken files..."

# Remove duplicate Godot files with ".." in name
DUPLICATE_GD_FILES=(
    "ClickablePlaceholder..gd"
    "ClickablePlaceholder..gd.uid"
)

for file in "${DUPLICATE_GD_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✗ Removed duplicate: $file"
    fi
done

# Remove backup files from root
if [ -f "__init__.py.backup" ]; then
    rm "__init__.py.backup"
    echo "  ✗ Removed stray backup: __init__.py.backup"
fi

# Check for .broken files
if [ -f "core/agent_gateway.py.broken" ]; then
    echo "  ⚠ Found core/agent_gateway.py.broken"
    echo "    Recommend: rm core/agent_gateway.py.broken (if agent_gateway.py works)"
fi

if [ -f "core/ap_complex_rules.py.old" ]; then
    echo "  ⚠ Found core/ap_complex_rules.py.old"
    echo "    Recommend: rm core/ap_complex_rules.py.old (if ap_complex_rules.py works)"
fi

echo ""
echo "[4/6] Organizing Godot files..."

# Create proper godot structure
mkdir -p godot/scripts
mkdir -p godot/scenes

# Move .gd files to godot/scripts if they're in root
ROOT_GD_FILES=(
    "ClickablePlaceholder.gd"
    "test_bridge.gd"
)

for file in "${ROOT_GD_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" godot/scripts/
        if [ -f "$file.uid" ]; then
            mv "$file.uid" godot/scripts/
        fi
        echo "  ✓ $file → godot/scripts/"
    fi
done

# Move .tscn files to godot/scenes if in root
if [ -f "node_3d.tscn" ]; then
    mv "node_3d.tscn" godot/scenes/
    echo "  ✓ node_3d.tscn → godot/scenes/"
fi

echo ""
echo "[5/6] Cleaning up script files..."

# Move utility scripts to scripts/ directory
mkdir -p scripts

SCRIPT_FILES=(
    "fix_trixel_init.sh"
    "verify_trixel_integration.sh"
)

for file in "${SCRIPT_FILES[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" scripts/
        echo "  ✓ $file → scripts/"
    fi
done

echo ""
echo "[6/6] Checking for orphaned files..."

# List any remaining unexpected files in root
EXPECTED_ROOT=(
    "core"
    "tools"
    "tests"
    "godot"
    "docs"
    "assets"
    "configs"
    "game_scenes"
    "scripts"
    "project.godot"
    "icon.svg"
    "icon.svg.import"
)

echo "  Scanning for unexpected root files..."
for item in *; do
    if [ "$item" = "core" ] || [ "$item" = "tools" ] || [ "$item" = "tests" ] || \
       [ "$item" = "godot" ] || [ "$item" = "docs" ] || [ "$item" = "assets" ] || \
       [ "$item" = "configs" ] || [ "$item" = "game_scenes" ] || [ "$item" = "scripts" ] || \
       [ "$item" = "project.godot" ] || [ "$item" = "icon.svg" ] || [ "$item" = "icon.svg.import" ]; then
        continue
    fi
    
    if [ -f "$item" ]; then
        echo "  ⚠ Unexpected file in root: $item"
    fi
done

echo ""
echo "======================================================================"
echo "CLEANUP COMPLETE"
echo "======================================================================"

echo ""
echo "New structure:"
echo ""
echo "docs/"
echo "├── architecture/        # Architecture docs"
echo "├── completed_sessions/  # Historical session notes"
echo "└── guides/             # Integration & installation guides"
echo ""
echo "godot/"
echo "├── scripts/            # .gd script files"
echo "└── scenes/             # .tscn scene files"
echo ""
echo "scripts/                # Utility shell scripts"
echo ""

echo "======================================================================"
echo "RECOMMENDED MANUAL CLEANUP"
echo "======================================================================"

echo ""
echo "Remove these if the non-.broken/.old versions work:"
if [ -f "core/agent_gateway.py.broken" ]; then
    echo "  rm core/agent_gateway.py.broken"
fi
if [ -f "core/ap_complex_rules.py.old" ]; then
    echo "  rm core/ap_complex_rules.py.old"
fi

echo ""
echo "Check this mystery file:"
if [ -f "core/todays lunch" ]; then
    echo "  cat 'core/todays lunch'  # What is this?"
    echo "  rm 'core/todays lunch'   # If junk"
fi

echo ""
echo "Remove backup files if main files work:"
if [ -f "godot/SceneSpawner.gd.backup" ]; then
    echo "  rm godot/SceneSpawner.gd.backup"
fi
if [ -f "tools/trixel/__init__.py.backup" ]; then
    echo "  rm tools/trixel/__init__.py.backup"
fi

echo ""
echo "======================================================================"
