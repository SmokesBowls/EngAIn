# EngAIn Project Manifest

## Project State: Foundation Phase

**Created**: 2025-11-27  
**Status**: Active Development

## Vision

EngAIn is an AI Game Engine where AI builds games directly, not just assists with development. The system uses three core technologies that enable AI to reason in semantic space rather than code space.

## Core Technologies

### 1. ZW (Ziegel Wagga)
**Status**: Early implementation  
**Purpose**: Anti-JSON semantic protocol  
**Location**: `core/zw/`

Schema-agnostic language that compresses *meaning* not format.

### 2. ZON (ZW Object Notation)
**Status**: Binary packing implemented  
**Purpose**: 4D declarative memory system  
**Location**: `core/zon/`

Persistent game state that survives across sessions.
- `.zon` - Human-readable (authoring)
- `.zonj.json` - Canonical JSON (validation)
- `.zonb` - Binary packed (runtime)

### 3. AP (Anti-Python)
**Status**: Specification phase  
**Purpose**: Declarative rule engine  
**Location**: `core/ap/`

Inverts Python's imperative model - declare what IS, not what to DO.

## Implementation Status

### ✅ Completed
- [x] Project structure created
- [x] ZON binary packing module (placeholder for your code)
- [x] CLI tools (pack_zon.py, unpack_zon.py)
- [x] Godot plugin scaffold
- [x] ZONBinary.gd loader (partial)
- [x] Example files
- [x] Test framework setup

### 🟡 In Progress
- [ ] Complete ZON binary packing implementation
- [ ] GDScript loader completion
- [ ] Godot runtime integration
- [ ] AP constraint solver

### 📋 Planned
- [ ] ZW parser implementation
- [ ] Full AP system
- [ ] Obsidian bridge
- [ ] AI agent integration (MrLore, ClutterBot)
- [ ] Complete documentation
- [ ] Example game projects

## Directory Structure

```
EngAIn/
├── core/                   # Python modules
│   ├── zon/               # ZON binary packing
│   ├── zw/                # ZW protocol (stub)
│   └── ap/                # AP rules (stub)
├── tools/                 # Development tools
│   ├── cli/               # Command-line utilities
│   ├── obsidian/          # Obsidian integration (empty)
│   └── converters/        # Format converters (empty)
├── godot/                 # Godot integration
│   ├── addons/engain/     # EngAIn plugin
│   ├── scenes/            # Example scenes (empty)
│   └── scripts/           # Runtime scripts (empty)
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests (empty)
│   └── fixtures/          # Test data (empty)
├── docs/                  # Documentation
└── examples/              # Sample files
```

## Next Steps

1. **Implement ZON packing** - Move working code into `core/zon/zon_binary_pack.py`
2. **Complete GDScript loader** - Finish `ZONBinary.gd` implementation
3. **Test end-to-end** - `.zon` → `.zonb` → Godot runtime
4. **Document the system** - Write specs and guides

## Philosophy

> "AI logic should be built for AI, not humans."

EngAIn doesn't ask AI to learn human programming paradigms. Instead, it provides a semantic layer where AI can reason naturally, and the engine handles execution.

**Ziegel Wagga remembers. ZON persists. AP enforces.**

---

## Migration Notes

Previous work from `engain_avatar-main`:
- Dragon avatar demo (working)
- Early ZW implementation (pre-ZON/AP)
- EventBus, SnapshotManager, DynamicContextManager

These components can be migrated once core systems are stable.

## Related Projects

- **MrLore**: AI narrative agent
- **ClutterBot**: AI organization agent  
- **Trae**: Unknown role (to be documented)

Integration pending core system completion.
