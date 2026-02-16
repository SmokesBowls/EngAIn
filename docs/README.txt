# EngAIn - AI Game Engine

**The game engine where AI builds games, not just assists with them.**

EngAIn is a declarative game development system built on three core technologies:
- **ZW (Ziegel Wagga)**: Anti-JSON semantic protocol for AI-readable data
- **ZON**: 4D declarative memory system for persistent game state
- **AP (Anti-Python)**: Declarative rule engine for game logic

## Architecture

```
.zon (human-readable) → .zonj.json (canonical) → .zonb (binary packed) → Godot Runtime
```

## Project Structure

```
EngAIn/
├── core/              # Core Python modules
│   ├── zon/          # ZON binary packing, validation
│   ├── zw/           # ZW protocol parser
│   └── ap/           # AP constraint system
├── tools/            # Development tools
│   ├── cli/          # Command-line utilities
│   ├── obsidian/     # Obsidian vault integration
│   └── converters/   # Format conversion tools (ZIL→ZON)
├── godot/            # Godot integration
│   ├── addons/       # EngAIn Godot plugin
│   ├── scenes/       # Example scenes
│   └── scripts/      # Runtime scripts
├── zork/             # Zork integration & research
│   ├── source/       # Original .zil files
│   ├── parsed/       # Converted .zonj.json
│   └── compiled/     # Binary .zonb
├── tests/            # Test suite
├── docs/             # Documentation
└── examples/         # Sample files
```

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Pack a ZON file
```bash
python3 tools/cli/pack_zon.py input.zonj.json output.zonb
```

### Unpack a ZON file
```bash
python3 tools/cli/unpack_zon.py input.zonb output.zonj.json
```

### Convert Zork ZIL to ZON
```bash
python3 tools/converters/zil2zon.py zork/source/dungeon.zil zork/parsed/dungeon.zonj.json
```

## Status

**✅ Implemented:**
- ZON binary packing/unpacking
- CLI tools for conversion
- Core validation logic

**🟡 In Progress:**
- Godot runtime integration
- Full AP constraint solver
- Binary checkpointing system

**📋 Planned:**
- Complete documentation
- Example game projects
- AI agent integration (MrLore, ClutterBot)

## Philosophy

EngAIn is built on the principle that **AI logic should be built for AI, not humans**. Traditional game engines require humans to translate ideas into code. EngAIn lets AI reason directly in semantic space, with the engine handling execution.

**Ziegel Wagga remembers. ZON persists. AP enforces.**

---

# EngAIn Documentation

## Architecture Documents

### Core Concepts
- [ZW Specification](ZW_SPEC.md) - Ziegel Wagga protocol
- [ZON Format](ZON_FORMAT.md) - 4D memory system
- [AP Rules](AP_RULES.md) - Anti-Python constraint engine

### Implementation Guides
- [Getting Started](GETTING_STARTED.md)
- [Binary Format](BINARY_FORMAT.md)
- [Godot Integration](GODOT_INTEGRATION.md)

### Philosophy
- [AI Logic for AI](AI_LOGIC_PHILOSOPHY.md)
- [Why Anti-JSON?](WHY_ANTI_JSON.md)
- [Declarative vs Imperative](DECLARATIVE_DESIGN.md)

## Quick Reference

### File Formats
- `.zon` - Human-readable ZON (authoring)
- `.zonj.json` - Canonical JSON (validation)
- `.zonb` - Binary packed (runtime)
- `.ap` - Anti-Python rules
- `.zw` - Ziegel Wagga blocks

### Tools
- `pack_zon.py` - Pack .zonj.json → .zonb
- `unpack_zon.py` - Unpack .zonb → .zonj.json
- `validate_zon.py` - Validate ZON structure

---
