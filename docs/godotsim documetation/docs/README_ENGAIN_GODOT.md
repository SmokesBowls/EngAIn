# EngAIn Godot Integration - Active Code Artifacts

This collection contains working GDScript and Python code for integrating the EngAIn AI Game Engine with Godot 4.x.

## Architecture Overview

EngAIn follows a **three-layer modular architecture**:

1. **MR Kernels** (Python): Pure functional logic, snapshot-in/snapshot-out
2. **Deep Contracts** (Python): ZON4D integration layer with temporal anchoring
3. **Adapters** (Python + GDScript): Delta processing and engine bridges

**Key Principle**: Python maintains authority over all game logic. Godot serves as a thin rendering client.

## Files Included

### Core Runtime

- **`sim_runtime.py`**: Python HTTP server that wraps all EngAIn subsystems
  - Runs simulation loop at ~60 FPS
  - Processes commands from Godot clients
  - Manages world snapshot and delta queue
  - Integrates Spatial3D, Perception, Behavior, Navigation subsystems

- **`ZWRuntime.gd`**: Godot adapter that connects to Python runtime
  - HTTP communication with sim_runtime.py
  - Snapshot/delta synchronization
  - Command queuing and execution
  - Add to scene as singleton or autoload

### Scene Controllers

- **`TestZWScene.gd`**: Test harness for ZW subsystems
  - Automated test suite
  - Manual test triggers (press 1, 2, 3, R, D)
  - Console logging for debugging
  - Use for validation and development

- **`player.gd`**: 3D FPS player controller
  - WASD movement, mouse look
  - Combat integration with ZW
  - State synchronization with ZWRuntime
  - Health/inventory management

- **`EngAInBridge.gd`**: Advanced 2D isometric controller
  - Natural language command processing
  - Dynamic NPC spawning
  - World state management
  - Event system for dialogue/combat/quests

- **`AkashicHub.gd`**: Save/load UI system
  - Spiritual/narrative flavor for persistence
  - ZON4D snapshot saving
  - 10 save slots
  - Metadata display (name, timestamp, level)

## Setup Instructions

### 1. Python Runtime Setup

```bash
# Install dependencies (if needed)
pip install --break-system-packages <dependencies>

# Start the runtime server
python3 sim_runtime.py
```

The server will run on `http://localhost:8080` by default.

### 2. Godot Project Setup

**Option A: Autoload (Recommended)**
1. Go to Project → Project Settings → Autoload
2. Add `ZWRuntime.gd` as autoload singleton named "ZWRuntime"
3. Now accessible everywhere via `ZWRuntime`

**Option B: Scene Instance**
1. Add `ZWRuntime.gd` to your main scene
2. Add to group "zw_runtime" so other scripts can find it
3. Access via `get_tree().get_first_node_in_group("zw_runtime")`

### 3. Scene-Specific Setup

**For 3D FPS (Screenshot 1):**
```
Scene Tree:
├── player (CharacterBody3D) [player.gd]
│   ├── CollisionShape3D
│   ├── Camera3D
│   │   └── gun_model (MeshInstance3D)
└── ZWRuntime [ZWRuntime.gd]
```

**For Test Scene (Screenshot 3):**
```
Scene Tree:
├── TestZWScene (Node2D) [TestZWScene.gd]
│   ├── ZWRuntime [ZWRuntime.gd]
│   └── Label
```

**For Isometric World (Screenshot 4):**
```
Scene Tree:
├── EngAInBridge (Node2D) [EngAInBridge.gd]
│   ├── Sprite2D (world background)
│   ├── CharacterBody2D (player)
│   ├── LineEdit (command input)
│   ├── SnapshotManager
│   └── DynamicContextManager
```

**For Akashic Hub (Screenshot 2):**
```
Scene Tree:
├── AkashicHub (Control) [AkashicHub.gd]
│   ├── Backdrop
│   ├── Tabs
│   └── content
│       ├── BookPanel
│       │   ├── SaveBtn
│       │   ├── LoadBtn
│       │   └── Slots
│       ├── OptionsPanel
│       ├── LorePanel
│       └── BestiaryPanel
```

## Usage Examples

### Sending Commands from GDScript

```gdscript
# Get ZWRuntime reference
var zw = get_tree().get_first_node_in_group("zw_runtime")

# Spawn an entity
zw.send_command({
    "action": "spawn_entity",
    "entity_id": "guard_01",
    "entity_type": "guard",
    "position": {"x": 10.0, "y": 0.0, "z": 5.0}
})

# Combat action
zw.send_command({
    "action": "combat",
    "type": "shoot",
    "player_id": "player",
    "weapon": "simple_gun",
    "direction": [0, 0, -1]
})

# Natural language command
zw.send_command({
    "action": "natural_command",
    "command": "spawn a merchant near me",
    "context": {"player_pos": player.position}
})
```

### Receiving State Updates

```gdscript
func _ready():
    var zw = get_tree().get_first_node_in_group("zw_runtime")
    zw.state_updated.connect(_on_state_updated)

func _on_state_updated(snapshot: Dictionary):
    # Update game state from Python authority
    if snapshot.has("entities"):
        for entity_id in snapshot["entities"].keys():
            update_entity_visual(entity_id, snapshot["entities"][entity_id])
```

### Test Scene Keyboard Shortcuts

When running `TestZWScene.gd`:

- **1**: Test greeter with low reputation
- **2**: Test greeter with high reputation  
- **3**: Test merchant interaction
- **R**: Reload ZW/ZON blocks
- **D**: Dump current state to console

## Communication Protocol

### Request: Command (POST /command)
```json
{
    "action": "spawn_entity",
    "entity_id": "npc_123",
    "entity_type": "merchant",
    "position": {"x": 5.0, "y": 0.0, "z": 3.0}
}
```

### Response: Acknowledgment
```json
{
    "type": "ack",
    "status": "ok"
}
```

### Request: Snapshot (GET /snapshot)

### Response: Full Snapshot
```json
{
    "type": "snapshot",
    "snapshot": {
        "entities": {
            "player": {"health": 100, "position": {...}},
            "npc_123": {"type": "merchant", ...}
        },
        "world": {
            "time": 123.45,
            "weather": "clear"
        },
        "events": []
    }
}
```

### Response: Delta Update
```json
{
    "type": "delta",
    "delta": {
        "entities": {
            "player": {"health": 95}  // Only changed fields
        }
    }
}
```

## Integration with EngAIn Subsystems

The Python runtime can integrate with your existing EngAIn subsystems:

```python
# In sim_runtime.py
from spatial3d_adapter import Spatial3DAdapter
from perception_adapter import PerceptionAdapter
from behavior_adapter import BehaviorAdapter
from navigation_mr import NavigationMR
```

Each subsystem follows the three-layer pattern:
- **MR Kernel**: Pure functional logic
- **Deep Contract**: ZON4D integration  
- **Adapter**: Delta processing + JSON bridge

## Development Workflow

1. **Start Python runtime**: `python3 sim_runtime.py`
2. **Open Godot project**: Load appropriate scene
3. **Test functionality**: Use keyboard shortcuts or UI
4. **Check console**: Both Python and Godot output debug info
5. **Iterate**: Modify code, reload (Ctrl+R in Godot, or 'R' in test scene)

## Debugging Tips

**Python Side:**
- Check console for "EngAIn Runtime: Initialized"
- Watch for command processing logs
- Use "dump_state" to inspect snapshot

**Godot Side:**
- Verify ZWRuntime connection: "ZWRuntime: Initialized"
- Check HTTP request status codes
- Watch for JSON parse errors
- Use Remote debugger (Debug → Deploy with Remote Debug)

**Network Issues:**
- Ensure `sim_runtime.py` is running first
- Check firewall settings for localhost:8080
- Verify Godot network permissions in project settings

## Next Steps

1. **Expand subsystems**: Add more MR kernels (Combat3D, Resource3D, etc.)
2. **Enhance commands**: Add more natural language parsing
3. **Optimize networking**: Implement delta compression, binary protocol
4. **Add visuals**: Create proper sprites/models for NPCs
5. **Integrate narrative**: Connect to Pass 1-4 pipeline for ZON4D content

## Philosophy

This code embodies the EngAIn principle: **"AI Logic Built for AI, Not Humans"**

- **World Model as Truth**: Python maintains canonical state
- **Semantic Compression**: ZW format for efficient AI reasoning
- **Temporal Integrity**: ZON4D for 4D memory fabric
- **Engine Agnostic**: Same logic works with any renderer

The goal is to make it as natural as possible for AI agents to generate, understand, and modify game logic directly.

---

**Questions or Issues?**
Check console output on both Python and Godot sides. Most issues are connection-related or JSON parsing errors.
