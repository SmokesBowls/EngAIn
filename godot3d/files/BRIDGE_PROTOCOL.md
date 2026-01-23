# THIN CLIENT BRIDGE PROTOCOL

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    THIN CLIENT ARCHITECTURE                  │
└─────────────────────────────────────────────────────────────┘

Python Simulation (Authority)              Godot (Renderer)
┌──────────────────────────┐              ┌─────────────────┐
│  sim_runtime.py          │              │  sim_client.gd  │
│                          │              │                 │
│  ┌────────────────────┐  │              │  ┌───────────┐  │
│  │ Spatial3D          │  │              │  │ Entities  │  │
│  │ Perception3D       │  │              │  │ (cubes)   │  │
│  │ Navigation3D       │  │  snapshots   │  │           │  │
│  │ Behavior3D         │  ├─────────────>│  │ Camera    │  │
│  │ Combat3D           │  │   JSON       │  │           │  │
│  └────────────────────┘  │              │  └───────────┘  │
│           ^              │              │        │        │
│           │              │   commands   │        │        │
│           └──────────────┼──────────────┼────────┘        │
│                          │   JSON       │                 │
└──────────────────────────┘              └─────────────────┘

         AUTHORITY                              DISPLAY
    (single source of truth)              (visualization only)
```

## Communication Protocol

### Transport: stdin/stdout with JSON

**Python reads from stdin:**
- One JSON command per line
- Blocking read (waits for Godot)

**Python writes to stdout:**
- One JSON snapshot per line after each tick
- Godot reads and renders

**Python logs to stderr:**
- Debug messages, errors
- Doesn't interfere with JSON protocol

---

## Message Formats

### 1. Commands (Godot → Python)

#### Tick Command
```json
{"type": "tick"}
```
Advances simulation by one frame.

#### Move Command
```json
{
  "type": "move",
  "entity_id": "player",
  "data": {
    "target_pos": [5.0, 0.0, 3.0],
    "speed": 5.0
  }
}
```
Moves entity toward target position.

#### Attack Command
```json
{
  "type": "attack",
  "entity_id": "player",
  "data": {
    "target_id": "enemy",
    "damage": 25.0
  }
}
```
Applies damage to target entity.

#### Spawn Command
```json
{
  "type": "spawn",
  "entity_id": "monster_01",
  "data": {
    "pos": [10.0, 0.0, 5.0],
    "health": 80.0
  }
}
```
Spawns new entity in the world.

#### Quit Command
```json
{"type": "quit"}
```
Gracefully shuts down Python runtime.

---

### 2. Snapshots (Python → Godot)

#### World Snapshot
```json
{
  "tick": 42,
  "entities": {
    "guard": {
      "pos": [-3.0, 0.0, 0.5],
      "vel": [0.0, 0.0, 0.1],
      "radius": 0.5,
      "tags": ["guard", "perceiver"],
      "health": 75.0,
      "max_health": 100.0,
      "alive": true,
      "state": "fleeing",
      "flags": ["low_health"]
    },
    "enemy": {
      "pos": [3.0, 0.0, 0.0],
      "vel": [0.0, 0.0, 0.0],
      "radius": 0.5,
      "tags": [],
      "health": 50.0,
      "max_health": 50.0,
      "alive": true,
      "state": "idle",
      "flags": []
    },
    "wall": {
      "pos": [0.0, 0.0, 0.0],
      "vel": [0.0, 0.0, 0.0],
      "radius": 2.0,
      "tags": ["obstacle"],
      "health": 100.0,
      "max_health": 100.0,
      "alive": true,
      "state": "idle",
      "flags": []
    }
  }
}
```

**Snapshot Fields:**

- `tick` - Current simulation tick number
- `entities` - Dictionary of all entities keyed by ID

**Entity Fields:**

Spatial:
- `pos` - [x, y, z] position
- `vel` - [x, y, z] velocity
- `radius` - Collision radius
- `tags` - Entity tags list

Combat:
- `health` - Current health
- `max_health` - Maximum health
- `alive` - Boolean alive status

Behavior:
- `state` - Current behavior state ("idle", "fleeing", "dead", etc.)
- `flags` - Active flags list (["low_health", "dead"], etc.)

---

## Setup Instructions

### 1. Python Side

**Location:** `~/Downloads/EngAIn/zonengine4d/zon4d/sim/`

**Files:**
- `sim_runtime.py` - Main server script
- All existing adapter files (spatial3d_adapter.py, etc.)

**Run:**
```bash
cd ~/Downloads/EngAIn/zonengine4d/zon4d/sim
python3 sim_runtime.py
```

**Expected output (stderr):**
```
[RUNTIME] EngAIn simulation initialized
[SPATIAL] Initialized
[PERCEPTION] Initialized
[NAVIGATION] Initialized
[COMBAT] Initialized
[SPAWN] guard at [-3, 0, 0] with 100.0/100.0 HP
[SPAWN] enemy at [3, 0, 0] with 50.0/50.0 HP
[SPAWN] wall at [0, 0, 0] with 100.0/100.0 HP
[RUNTIME] Starting main loop
[RUNTIME] Waiting for commands on stdin...
```

**Test manually:**
```bash
python3 sim_runtime.py
# Type: {"type": "tick"}
# Press Enter
# You should see JSON snapshot output
```

### 2. Godot Side

**Location:** `~/Downloads/EngAIn/godot/`

**Files:**
- `scripts/sim_client.gd` - Main client script
- `sim_runtime.py` - Copy of Python runtime (for convenience)

**Scene Structure:**
```
Node3D (root)
├─ script: sim_client.gd
├─ Camera3D
│   └─ Position: (0, 10, 15)
│       Rotation: (-30, 0, 0)
└─ DirectionalLight3D
    └─ Rotation: (-45, -45, 0)
```

**Client Properties:**
- `python_runtime_path`: Path to sim_runtime.py
- `python_executable`: "python3"
- `player_entity_id`: "player"
- `move_speed`: 5.0

---

## Testing the Bridge

### Test 1: Manual Python Test
```bash
cd ~/Downloads/EngAIn/zonengine4d/zon4d/sim
python3 sim_runtime.py

# Type commands:
{"type": "tick"}
{"type": "attack", "entity_id": "enemy", "data": {"target_id": "guard", "damage": 25.0}}
{"type": "tick"}
{"type": "quit"}
```

### Test 2: Godot Integration Test

**Simplified test (file-based):**

Instead of stdin/stdout, start with file-based communication:

**Python: Write snapshots to file**
```python
# In sim_runtime.py, add:
def write_snapshot_to_file(self, path="/tmp/engain_snapshot.json"):
    snapshot = self.get_world_snapshot()
    with open(path, 'w') as f:
        json.dump(snapshot, f)
```

**Godot: Read from file**
```gdscript
# In sim_client.gd:
func read_snapshot_from_file(path: String = "/tmp/engain_snapshot.json"):
    var file = FileAccess.open(path, FileAccess.READ)
    if file:
        var json_str = file.get_as_text()
        var json = JSON.new()
        json.parse(json_str)
        return json.get_data()
    return {}
```

This lets you test rendering **without** complex subprocess management.

---

## Rendering Rules

**Godot visualizes Python's authority:**

1. **Entity Creation**
   - Python snapshot contains entity → Create cube in Godot
   - Entity ID becomes node name

2. **Position Updates**
   - Every frame, update `node.position` from `snapshot["entities"][id]["pos"]`
   - No interpolation yet (add later for smoothness)

3. **Color Coding**
   - `alive == false` → Black
   - `health < 25%` → Red
   - `health < 50%` → Yellow
   - `state == "fleeing"` → Orange
   - Default: Green (guard), Dark Red (enemy), Blue (player)

4. **Label Text**
   - Show: entity_id, health/max_health, state
   - Example: "guard\n75/100 HP\nfleeing"

5. **Entity Removal**
   - Entity not in snapshot → Remove from scene

---

## Next Steps

### Phase 1: File-Based Test ✓
- Python writes snapshots to `/tmp/engain_snapshot.json`
- Godot reads file each frame
- Validates rendering logic

### Phase 2: Subprocess Integration
- Godot spawns Python process
- Pipes stdin/stdout
- Real-time communication

### Phase 3: Optimization
- Add interpolation for smooth movement
- Batch commands
- Delta compression (only changed entities)

### Phase 4: Rich Rendering
- Replace cubes with 3D models
- Add animations
- Particle effects
- Sound effects

---

## Advantages of Thin Client

✅ **Single Source of Truth** - Python sim is authority  
✅ **Engine Agnostic** - Swap Godot for Unreal/Unity later  
✅ **Easy Testing** - Test Python sim independently  
✅ **No Logic Duplication** - Combat3D exists once (in Python)  
✅ **AI Development** - Debug complex AI in Python  
✅ **Matches Inform 7 Philosophy** - World model → renderer  

---

## Troubleshooting

**Python not outputting JSON:**
- Check stderr for errors
- Verify stdin is receiving commands
- Test with `{"type": "tick"}` manually

**Godot not rendering entities:**
- Check snapshot format (print to console)
- Verify entity IDs match
- Check Camera3D can see origin (0,0,0)

**Commands not working:**
- Check Python stderr for parsing errors
- Verify JSON format (use online validator)
- Test commands manually in terminal first

---

**Status:** Architecture complete, ready for integration testing!
