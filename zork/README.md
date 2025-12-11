# Zork Integration

## Overview

Zork (1979) is the **original declarative game logic system**. Written in ZIL (Zork Implementation Language), it represents the first practical implementation of what EngAIn is rebuilding with modern tools.

## Why Zork?

**ZIL is ZON+AP from 1979:**
- Declarative room/object definitions (like ZON)
- Conditional logic and state rules (like AP)
- Persistent world state
- All in S-expressions (semantic blocks)

By converting Zork's logic into EngAIn's format, we prove the system can:
1. Ingest legacy declarative systems
2. Preserve complex game logic across formats
3. Reason about interactive narrative at scale

## Structure

```
zork/
├── source/           # Original .zil files from zork3-master
├── parsed/           # Converted .zonj.json files
├── compiled/         # Binary .zonb files
└── README.md         # This file
```

## Conversion Pipeline

```
.zil (ZIL source) → .zonj.json (ZON canonical) → .zonb (binary) → Godot
```

### Step 1: Parse ZIL to ZON

**Tool**: `tools/converters/zil2zon.py` (to be created)

Example ZIL:
```lisp
<ROOM LIVING-ROOM
  (DESC "You are in a living room.")
  (FLAGS LIGHT)
  (EXITS (NORTH KITCHEN) (EAST TROPHY-ROOM))>
```

Becomes ZON:
```json
{
  "type": "room",
  "id": "LIVING-ROOM",
  "description": "You are in a living room.",
  "flags": ["LIGHT"],
  "exits": {
    "north": "KITCHEN",
    "east": "TROPHY-ROOM"
  }
}
```

### Step 2: Pack to Binary

Use existing tools:
```bash
python3 tools/cli/pack_zon.py parsed/living_room.zonj.json compiled/living_room.zonb
```

### Step 3: Load in Godot

```gdscript
var loader = ZONBinary.new()
var room = loader.load_zonb("res://zork/compiled/living_room.zonb")
```

## Mapping ZIL Concepts to ZON

| ZIL Concept | ZON Type | Notes |
|------------|----------|-------|
| `<ROOM>` | `room` | Locations |
| `<OBJECT>` | `object` | Items, props |
| `<ROUTINE>` | `action` | Verbs, logic |
| `FLAGS` | `flags` | State booleans |
| `EXITS` | `connections` | Graph edges |
| Conditions | `requires` | AP constraints |

## Implementation Status

- [ ] Copy Zork source files
- [ ] Create ZIL parser (`tools/converters/zil2zon.py`)
- [ ] Define ZIL→ZON mapping schema
- [ ] Convert sample rooms
- [ ] Test binary packing
- [ ] Load in Godot
- [ ] Verify logic preservation

## Research Value

Zork represents **600+ rooms, 400+ objects, 100+ verbs** of tested game logic. By converting it, we gain:

1. **Proof of concept** - Can EngAIn handle real complexity?
2. **Test corpus** - Hundreds of examples for validation
3. **AI training data** - Teach agents what game logic looks like
4. **Rosetta Stone** - Compare ZIL vs ZON expressiveness

## Next Steps

1. Copy `.zil` files from `~/zw/zork3-master/` to `zork/source/`
2. Build `zil2zon.py` parser
3. Start with simple rooms (LIVING-ROOM, KITCHEN)
4. Gradually convert full game
5. Document discoveries

---

**Zork is not legacy. Zork is the prototype.**

We're not replacing it - we're **translating its wisdom** into a form AI can extend.
