# EngAIn Quick Start

## Current State: Foundation Ready

The project structure is in place. Here's how to get started:

---

## Step 1: Add Your Working Code

### 🎯 Priority: Implement ZON Binary Packing

You mentioned you have working `pack_zonj()` and `unpack_zonb()` functions.

**📍 Location**: `core/zon/zon_binary_pack.py`

Replace the `NotImplementedError` placeholders with your working implementation:

```python
def pack_zonj(data: Dict[str, Any]) -> bytes:
    # YOUR WORKING CODE HERE
    pass

def unpack_zonb(data: bytes) -> Dict[str, Any]:
    # YOUR WORKING CODE HERE
    pass
```

---

## Step 2: Test It

### Run the CLI tools:

```bash
# From EngAIn root directory:

# Pack a file
python3 tools/cli/pack_zon.py examples/door_rule.zonj.json test.zonb

# Unpack it back
python3 tools/cli/unpack_zon.py test.zonb test_roundtrip.zonj.json

# Compare (should be identical)
diff examples/door_rule.zonj.json test_roundtrip.zonj.json
```

### Run the tests:

```bash
cd tests/unit
python3 test_zon_pack.py
```

---

## Step 3: Complete Godot Loader

**📍 Location**: `godot/addons/engain/ZONBinary.gd`

The skeleton is there - you need to complete the `unpack_zonb()` and `decode_value()` functions to mirror your Python implementation.

Key functions to implement:
- `unpack_zonb()` - Main unpacking logic
- `decode_value()` - Type-aware value decoder
- Block/dictionary decoding

---

## Step 4: Test End-to-End

1. Create a test Godot project in `godot/`
2. Enable the EngAIn plugin
3. Load a `.zonb` file:

```gdscript
var loader = ZONBinary.new()
var data = loader.load_zonb("res://data/door_rule.zonb")
print(data)
```

---

## What You Have Now

### ✅ Working Structure
- Clean separation: Python core, Godot runtime, CLI tools
- Proper module organization
- Ready for version control

### ✅ CLI Tools
- `pack_zon.py` - Convert JSON to binary
- `unpack_zon.py` - Convert binary to JSON

### ✅ Godot Integration Points
- Plugin framework
- Binary loader (partial)

### ✅ Example Data
- `door_rule.zonj.json` - Sample constraint

---

## What's Next

### Immediate (This Week)
1. ✅ **Structure created** ← YOU ARE HERE
2. ⏳ Implement core ZON packing
3. ⏳ Complete Godot loader
4. ⏳ Test full pipeline

### Short Term (Next 2 Weeks)
- Add ZW parser
- Add AP constraint solver  
- Create more example files
- Write format documentation

### Medium Term (Next Month)
- Obsidian bridge
- AI agent integration
- Example game project
- Complete documentation

---

## Migration Path

Your existing `engain_avatar-main` project:
- Keep as reference implementation
- Extract working components when ready:
  - EventBus.gd
  - SnapshotManager.gd
  - Dragon avatar scene
  
Don't port yet - wait until core systems are solid.

---

## Getting Help

If you get stuck:
1. Check `STRUCTURE.md` for file locations
2. Read `PROJECT_MANIFEST.md` for system overview
3. Look at example files in `examples/`

---

## The Goal

```
Author in .zon → Pack to .zonb → Load in Godot → Execute in game
```

**You're building the bridge between human thought and AI execution.**

**Let's make games remember.**
