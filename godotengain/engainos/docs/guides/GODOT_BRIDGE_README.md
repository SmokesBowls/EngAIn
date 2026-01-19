# EngAIn Godot Bridge - Installation Guide

Complete bridge between Python EngAIn and Godot rendering.

## What This Does

**Flow:**
```
Story (ZW) → ZON → Entity3D → RenderPlan (JSON) → Godot Scene Nodes
```

**Result:** Colored placeholder meshes (cubes, capsules, cylinders) spawn in Godot from narrative text.

## Files

### Python Side
- `godot_bridge_test.py` - Python script that Godot calls
- `zon_to_entities.py` - ZON → Entity3D converter
- `spatial_skin_system.py` - Entity3D data structures
- `mesh_manifest.py` - Trixel manifest system

### Godot Side
- `EngAInBridge.gd` - Main bridge script (attach to Node3D)
- `TestScene.tscn` - Example scene

## Installation

### Step 1: Install Python Files

```bash
cd ~/Downloads/EngAIn/godotengain/engainos

# Core modules (already installed from previous tests)
# - core/zon_to_entities.py ✓
# - core/spatial_skin_system.py ✓
# - core/mesh_manifest.py ✓

# Add bridge script
cp ~/Downloads/godot_bridge_test.py tests/
chmod +x tests/godot_bridge_test.py

# Test it works
cd tests
python3 godot_bridge_test.py --scene chapter1_opening
```

Expected output:
```json
{
  "scene_id": "chapter1_opening",
  "entity_count": 6,
  "entities": [
    {
      "placeholder_mesh": "capsule",
      "transform": {...},
      "color": {"r": 0.8, "g": 0.2, "b": 0.2},
      "zw_concept": "guard",
      ...
    },
    ...
  ]
}
```

### Step 2: Install Godot Files

```bash
# In your Godot project directory
cd ~/Downloads/EngAIn/godotengain

# Copy Godot bridge script
cp ~/Downloads/EngAInBridge.gd .

# Copy test scene (optional)
cp ~/Downloads/TestScene.tscn .
```

### Step 3: Configure Bridge

Open `EngAInBridge.gd` and verify paths:

```gdscript
@export var python_executable: String = "python3"
@export var engain_core_path: String = ""  # Auto-detects from project
@export var auto_load_on_ready: bool = false
@export var test_scene_id: String = "chapter1_opening"
```

## Usage

### Option 1: Use Test Scene

1. Open Godot Editor
2. Open `TestScene.tscn`
3. Press F5 (Run Scene)

**Result:** 6 entities spawn as colored placeholders:
- 2 guards (red capsules)
- 1 merchant (green capsule)
- 1 door (brown cube)
- 1 barrel (brown cylinder)
- 1 chest (golden cube)

### Option 2: Add to Existing Scene

1. Add Node3D to your scene
2. Attach `EngAInBridge.gd` script
3. Call from code:

```gdscript
# In your game script
var bridge = $EngAInBridge

# Load scene
bridge.load_scene("chapter1_opening")

# Query entities
var guards = bridge.get_entities_by_concept("guard")
print("Found ", guards.size(), " guards")

# Get statistics
var stats = bridge.get_scene_statistics()
print("Scene has ", stats.total_entities, " entities")
```

### Option 3: Manual Spawning

```gdscript
var bridge = $EngAInBridge

# Spawn single entity
var entity_data = {
    "placeholder_mesh": "capsule",
    "transform": {
        "position": {"x": 10, "y": 0, "z": 5},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "scale": {"x": 1, "y": 1, "z": 1}
    },
    "color": {"r": 0.8, "g": 0.2, "b": 0.2},
    "zw_concept": "guard",
    "entity_id": "guard_001"
}

var node = bridge.spawn_entity(entity_data)
```

## Placeholder Mesh Types

| Type | Godot Mesh | Used For |
|------|------------|----------|
| `cube` | BoxMesh | Doors, chests, walls |
| `capsule` | CapsuleMesh | Characters (guards, merchants, player) |
| `cylinder` | CylinderMesh | Barrels, towers, columns |
| `sphere` | SphereMesh | Bosses, orbs, projectiles |
| `plane` | PlaneMesh | Floor markers, portals |

## Default Colors

| Concept | Color | Hex |
|---------|-------|-----|
| Guard | Red | #CC3333 |
| Merchant | Green | #33CC33 |
| Player | Blue | #3333CC |
| Door | Brown | #996633 |
| Chest | Golden | #B38033 |
| Barrel | Dark Brown | #804D19 |
| Unknown | Magenta | #FF00FF (error) |

## Adding Custom Concepts

### Python Side (zon_to_entities.py)

```python
from zon_to_entities import register_concept_mapping, ConceptMapping
from spatial_skin_system import ColorRGB

register_concept_mapping(ConceptMapping(
    zw_concept="dragon_boss",
    ap_profile="boss_legendary",
    placeholder_mesh="sphere",
    collision_role="solid",
    default_color=ColorRGB(1.0, 0.0, 0.0),  # Red
    kernel_bindings={"combat": True, "ai": "boss"}
))
```

### Godot Side (Automatic)

Once registered in Python, Godot automatically handles it:

```python
# In your ZON data
{"type": "dragon_boss", "position": [20, 5, 20]}

# Spawns as red sphere automatically
```

## Test Scenes Available

### chapter1_opening (6 entities)
- 2 guards
- 1 merchant
- 1 door
- 1 barrel
- 1 chest

### test_minimal (2 entities)
- 1 player
- 1 guard

## Troubleshooting

### "Python bridge failed"

Check paths:
```bash
cd ~/Downloads/EngAIn/godotengain/engainos/tests
ls godot_bridge_test.py  # Should exist
python3 godot_bridge_test.py --scene test_minimal  # Should output JSON
```

### "Failed to parse JSON"

Check Python output manually:
```bash
cd ~/Downloads/EngAIn/godotengain/engainos/tests
python3 godot_bridge_test.py --scene chapter1_opening 2>&1 | head
```

Look for Python errors before JSON output.

### "No entities spawned"

1. Check Godot console for errors
2. Verify scene_id exists in TEST_SCENES (godot_bridge_test.py)
3. Add debug: `print(entities)` in load_scene()

### "Module not found"

Check PYTHONPATH:
```bash
cd ~/Downloads/EngAIn/godotengain/engainos/tests
PYTHONPATH=../core python3 -c "from zon_to_entities import *; print('OK')"
```

## Next Steps

### 1. Add Real Chapter Integration

Replace TEST_SCENES with actual ZON extraction:

```python
# In godot_bridge_test.py
from zon_extraction import extract_scene_from_chapter

def get_scene_data(scene_id: str) -> dict:
    # Load real story chapter
    zon_scene = extract_scene_from_chapter(f"chapters/{scene_id}.txt")
    # Convert as before...
```

### 2. Add Art Skins

When .trixel manifests exist:

```python
entities = zon_scene_to_entities(
    zon_scene,
    trixel_search_paths=[Path("assets/trixels")],
    auto_bind_skins=True
)
```

Then in Godot:

```gdscript
# In spawn_entity(), after creating placeholder:
if entity_data.has("skin_3d_id") and entity_data.skin_3d_id:
    var skin_path = "res://assets/" + entity_data.skin_3d_id
    if ResourceLoader.exists(skin_path):
        var skin = load(skin_path)
        mesh_node.add_child(skin.instantiate())
```

### 3. Add Live Reload

```gdscript
func _process(delta):
    if Input.is_action_just_pressed("reload_scene"):
        load_scene(test_scene_id)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│ Story Chapter (ZW text)                     │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ ZON Extraction                              │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ zon_to_entities.py                          │
│ - Maps concepts → Entity3D                  │
│ - Applies placeholder meshes                │
│ - Optional: binds .trixel skins             │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ spatial_skin_system.py                      │
│ - build_render_plan()                       │
│ - Outputs JSON-ready data                   │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ godot_bridge_test.py                        │
│ - CLI entry point for Godot                 │
│ - Converts RenderPlan → JSON                │
└──────────────┬──────────────────────────────┘
               ↓ JSON via OS.execute()
┌─────────────────────────────────────────────┐
│ EngAInBridge.gd                             │
│ - Parses JSON                               │
│ - spawn_entity() for each                   │
│ - Creates MeshInstance3D nodes              │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ Godot Scene (Visible!)                      │
│ - Colored placeholders                      │
│ - Collision enabled                         │
│ - Metadata attached                         │
└─────────────────────────────────────────────┘
```

## Success Criteria

✅ Python test works: `python3 godot_bridge_test.py --scene chapter1_opening`

✅ Godot spawns entities: Run TestScene.tscn, see colored meshes

✅ Correct positioning: Guards at (10,0,5) and (15,0,5)

✅ Correct colors: Guards red, merchant green, door brown

✅ Collision works: Placeholders are solid

✅ Metadata attached: `get_meta("zw_concept")` returns correct value

## Complete!

You now have:
- Story → Playable scene (complete pipeline)
- Visible entities in Godot
- No art dependencies (ships with placeholders)
- Ready to add .trixel skins when available
