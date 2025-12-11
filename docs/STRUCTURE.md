# EngAIn Directory Structure

```
EngAIn/
│
├── 📄 README.md                    # Project overview
├── 📄 PROJECT_MANIFEST.md          # Current state & roadmap
├── 📄 requirements.txt             # Python dependencies
├── 📄 .gitignore                   # Git ignore rules
│
├── 📦 core/                        # Core Python modules
│   ├── __init__.py
│   │
│   ├── zon/                       # ZON: 4D Memory System
│   │   ├── __init__.py
│   │   └── zon_binary_pack.py    # Binary packing (READY FOR YOUR CODE)
│   │
│   ├── zw/                        # ZW: Ziegel Wagga Protocol
│   │   └── __init__.py           # (stub)
│   │
│   └── ap/                        # AP: Anti-Python Rules
│       └── __init__.py           # (stub)
│
├── 🔧 tools/                       # Development Tools
│   ├── cli/                       # Command-line utilities
│   │   ├── pack_zon.py          # ✅ .zonj → .zonb
│   │   └── unpack_zon.py        # ✅ .zonb → .zonj
│   │
│   ├── converters/               # Format converters
│   │   └── zil2zon.py          # ✅ ZIL → ZON converter
│   │
│   └── obsidian/                 # Obsidian integration (empty)
│
├── 🎮 godot/                       # Godot Integration
│   ├── addons/
│   │   └── engain/               # EngAIn Plugin
│   │       ├── plugin.cfg       # Plugin config
│   │       ├── engain_plugin.gd # Plugin entry point
│   │       └── ZONBinary.gd     # ✅ .zonb loader (partial)
│   │
│   ├── scenes/                    # Example scenes (empty)
│   └── scripts/                   # Runtime scripts (empty)
│
├── 🎲 zork/                        # Zork Integration & Research
│   ├── source/                   # Original .zil files (copy from ~/zw/zork3-master)
│   ├── parsed/                   # Converted .zonj.json files
│   ├── compiled/                 # Binary .zonb files
│   └── README.md                 # ✅ Zork integration guide
│
├── 🧪 tests/                       # Test Suite
│   ├── unit/
│   │   └── test_zon_pack.py     # ✅ ZON packing tests
│   │
│   ├── integration/               # (empty)
│   └── fixtures/                  # (empty)
│
├── 📚 docs/                        # Documentation
│   └── README.md                  # Doc index
│
└── 💡 examples/                    # Sample Files
    └── door_rule.zonj.json        # ✅ Example constraint
```

## File Status Legend

- ✅ **Ready** - File exists and is functional/ready for use
- 🟡 **Partial** - File exists but needs completion
- 📋 **Stub** - Placeholder waiting for implementation
- (empty) - Directory created, awaiting content

## Key Files Ready For Your Code

### 1. `core/zon/zon_binary_pack.py`
**Current state**: Skeleton with type definitions  
**Action needed**: Replace `NotImplementedError` with your working `pack_zonj()` and `unpack_zonb()` functions

### 2. `godot/addons/engain/ZONBinary.gd`
**Current state**: Partial implementation with decode stubs  
**Action needed**: Complete the unpacking logic to mirror Python implementation

### 3. `tools/cli/*.py`
**Current state**: Fully functional wrappers  
**Action needed**: Will work once core module is implemented

## Next File To Create

After implementing the core, you'll want:
- `core/zon/zon_validator.py` - Validate ZON structure
- `godot/scripts/ZWRuntime.gd` - ZW execution engine
- `godot/scripts/APSimKernel.gd` - AP constraint solver
- `docs/ZON_FORMAT.md` - Binary format specification

---

**The foundation is ready. Time to build.**
