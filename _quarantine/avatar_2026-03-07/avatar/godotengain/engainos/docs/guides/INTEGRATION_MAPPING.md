# Trixel Integration - File Mapping Guide

## Current State (trixelcomposer-main/)

```
trixelcomposer-main/
├── files (4).zip                              → ARCHIVE
├── mesh_intake.py                             → CHECK/ARCHIVE (duplicate)
├── test_mesh_intake.py                        → ARCHIVE
├── trixel/
│   ├── learning_validator_agent.py            → MOVE to tools/trixel/
│   ├── MEMORY_GOVERNANCE_VALIDATION_RESULTS.md → ARCHIVE
│   ├── test1_commit.json                      → ARCHIVE
│   └── test2_rejection.json                   → ARCHIVE
├── TRIXEL_PIPELINE.md                         → MOVE to tools/trixel/
└── Untitled Folder/
    ├── brush_tutorial_zw.txt                  → ARCHIVE
    ├── empire_bridge.py                       → SKIP (optional, move later)
    ├── enhanced_trixel_core.py                → MOVE (rename to trixel_composer.py)
    ├── README.md                              → MOVE to tools/trixel/
    ├── terminal_trixel.py                     → MOVE to tools/trixel/
    ├── trixel composer research.txt           → ARCHIVE
    └── trixel_creative_cycle.txt              → ARCHIVE
```

## Target State (EngAIn structure)

```
EngAIn/
├── godotengain/
│   └── engainos/
│       ├── core/
│       │   └── mesh_intake.py                 ← Already exists (LAW)
│       │
│       ├── tools/
│       │   └── trixel/                        ← NEW HOME FOR TRIXEL
│       │       ├── __init__.py                ← AUTO-CREATED
│       │       ├── trixel_composer.py         ← FROM enhanced_trixel_core.py
│       │       ├── terminal_trixel.py         ← FROM Untitled Folder/
│       │       ├── learning_validator_agent.py ← FROM trixel/
│       │       ├── README.md                  ← FROM Untitled Folder/
│       │       └── TRIXEL_PIPELINE.md         ← FROM root
│       │
│       └── assets/
│           └── trixels/                       ← .trixel outputs only
│
└── archive/
    └── trixel_notes/                          ← ARCHIVED RESEARCH
        ├── trixel composer research.txt
        ├── trixel_creative_cycle.txt
        ├── brush_tutorial_zw.txt
        ├── test1_commit.json
        ├── test2_rejection.json
        ├── files (4).zip
        ├── MEMORY_GOVERNANCE_VALIDATION_RESULTS.md
        ├── test_mesh_intake.py
        └── mesh_intake_duplicate.py (if duplicate found)
```

## Decision Logic

### ✅ MOVE to tools/trixel/
**Why:** Active code that will be imported and used

- `terminal_trixel.py` - CLI interface for Trixel
- `enhanced_trixel_core.py` → `trixel_composer.py` - Core Trixel logic
- `learning_validator_agent.py` - Validation system
- `README.md` - Documentation for tools
- `TRIXEL_PIPELINE.md` - Pipeline specification

### 🗄️ ARCHIVE to archive/trixel_notes/
**Why:** Historical/research artifacts, not active code

- `trixel composer research.txt` - Conceptual notes
- `trixel_creative_cycle.txt` - Design thinking
- `brush_tutorial_zw.txt` - Tutorial content
- `test1_commit.json` - Example data
- `test2_rejection.json` - Example data
- `files (4).zip` - Unknown payload
- `MEMORY_GOVERNANCE_VALIDATION_RESULTS.md` - Test results
- `test_mesh_intake.py` - Duplicate test (core has real one)

### ⚠️ CHECK/ARCHIVE
**Why:** Potential duplicates of core law

- `mesh_intake.py` - Check if core/ already has this
  - If YES: Archive as `mesh_intake_duplicate.py`
  - If NO: Move to core/ (shouldn't happen)

### ⏭️ SKIP (Move Later)
**Why:** Optional integration, not core to Trixel

- `empire_bridge.py` - Empire integration (separate concern)

## File Role Reference

### Active Code (tools/trixel/)

| File | Role | Imports From |
|------|------|--------------|
| `trixel_composer.py` | Semantic authority, visual validation | core.mesh_intake |
| `terminal_trixel.py` | CLI interface for Trixel | trixel_composer |
| `learning_validator_agent.py` | Learning/validation system | trixel_composer |

**Key rule:** These import FROM core, never vice versa

### Law (core/)

| File | Role | Authority |
|------|------|-----------|
| `mesh_intake.py` | HARD GATE for mesh acceptance | Authoritative |

**Key rule:** Core never imports from tools/

### Archive (archive/trixel_notes/)

All files here are **read-only history**. Not imported anywhere.

## Integration Commands

### Option 1: Automated (Recommended)
```bash
cd ~/Downloads/EngAIn/trixelcomposer-main/
bash integrate_trixel.sh
```

### Option 2: Manual Step-by-Step

```bash
# Create directories
mkdir -p ../godotengain/engainos/tools/trixel
mkdir -p ../archive/trixel_notes
mkdir -p ../godotengain/engainos/assets/trixels

# Move active code
cp "Untitled Folder/terminal_trixel.py" ../godotengain/engainos/tools/trixel/
cp "Untitled Folder/enhanced_trixel_core.py" ../godotengain/engainos/tools/trixel/trixel_composer.py
cp "trixel/learning_validator_agent.py" ../godotengain/engainos/tools/trixel/
cp "Untitled Folder/README.md" ../godotengain/engainos/tools/trixel/
cp "TRIXEL_PIPELINE.md" ../godotengain/engainos/tools/trixel/

# Archive research
cp "Untitled Folder/"*.txt ../archive/trixel_notes/
cp "trixel/"*.json ../archive/trixel_notes/
cp "trixel/MEMORY_GOVERNANCE_VALIDATION_RESULTS.md" ../archive/trixel_notes/
cp "files (4).zip" ../archive/trixel_notes/
cp "test_mesh_intake.py" ../archive/trixel_notes/

# Check for duplicates
if [ -f "../godotengain/engainos/core/mesh_intake.py" ]; then
    echo "mesh_intake.py already in core - archiving duplicate"
    cp "mesh_intake.py" ../archive/trixel_notes/mesh_intake_duplicate.py
fi

# Create __init__.py
cat > ../godotengain/engainos/tools/trixel/__init__.py << 'EOF'
"""Trixel Composer - EngAIn Mesh Authoring Tools"""
from .trixel_composer import TrixelComposer
from .terminal_trixel import TerminalTrixel
from .learning_validator_agent import LearningValidator
__all__ = ['TrixelComposer', 'TerminalTrixel', 'LearningValidator']
EOF
```

## Verification Steps

### 1. Check No Godot Imports in Tools
```bash
cd ../godotengain/engainos
grep -R "import godot" tools/
# Should return NOTHING
```

### 2. Verify Import Structure
```bash
cd tools/trixel
python3 -c "from trixel_composer import TrixelComposer; print('✓ Import works')"
```

### 3. Verify No Circular Dependencies
```bash
# Tools can import core
grep -r "from core" tools/trixel/  # OK

# Core should NOT import tools
grep -r "from tools" core/  # Should be empty
```

## Final Mental Model

```
Law Authority:
  core/mesh_intake.py ← Decides acceptance

Advisory/Judgment:
  tools/trixel/trixel_composer.py ← Judges quality

Execution:
  godot/ ← Renders approved meshes only

History:
  archive/trixel_notes/ ← Read-only research
```

**The key:** Trixel advises, mesh_intake decides, core binds, Godot displays.

## Post-Integration Cleanup

After running integration script and verifying everything works:

```bash
# Delete original trixelcomposer-main/ (safe because everything copied)
cd ~/Downloads/EngAIn/
rm -rf trixelcomposer-main/

# Or keep as backup for a few days
mv trixelcomposer-main/ trixelcomposer-main.backup/
```

## What Changes in Your Workflow

### Before (Messy)
```bash
cd ~/Downloads/EngAIn/trixelcomposer-main/
python terminal_trixel.py  # Where is this in the tree?
```

### After (Clean)
```bash
cd ~/Downloads/EngAIn/godotengain/engainos/
python -m tools.trixel.terminal_trixel  # Clear location, proper module
```

## Import Patterns (Critical)

### ✅ Correct
```python
# In tools/trixel/trixel_composer.py
from core.mesh_intake import intake_mesh  # Tools import FROM core

# In core/mesh_intake.py
# No imports from tools at all
```

### ❌ Wrong
```python
# In core/mesh_intake.py
from tools.trixel import TrixelComposer  # ← NEVER DO THIS

# In tools/trixel/anything.py
import godot  # ← NEVER DO THIS
```

## Summary

**Active Code:** `tools/trixel/` (5 files)  
**Archives:** `archive/trixel_notes/` (8+ files)  
**Skipped:** `empire_bridge.py` (move later if needed)

**Authority preserved:** mesh_intake stays in core/, Trixel stays advisory
