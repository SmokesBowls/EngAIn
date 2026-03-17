# EngAIn → UPBGE Architecture Bridge
## Dual-Client Strategy: Godot (thin) + UPBGE (thick creative)

---

## Philosophy

EngAIn was built engine-agnostic by design. Python is authoritative.
The rendering client is a consumer, never a source of truth.

**What stays identical:**
- `sim_runtime.py` (HTTP server, world state authority)
- All 7 subsystems (Spatial3D, Perception3D, Navigation3D, Behavior3D, Combat3D, Inventory3D, Dialogue3D)
- ZW/ZON4D/AP stack
- MR kernels (pure functional, snapshot-in/snapshot-out)
- Protocol envelope format
- Every Python file in `EngAIn/godotsim/`

**What changes:** One new consumer script that speaks BGE instead of GDScript.

---

## The Contract

EngAIn exposes these HTTP endpoints. Both Godot and UPBGE consume them identically:

```
GET  /health              → {"ok": true, "ts": ...}
GET  /snapshot            → full world state envelope
POST /scene/load          → {"scene_id": "scene.04_the_convergence"}
POST /command             → {"command": "look"} or {"command": "damage", "target": "guard", ...}
POST /world/sync          → {"world": {...}, "entities": {...}}
GET  /vault/search?q=...  → search loaded scenes
POST /vault/link          → {"path": "/path/to/vault"}
```

UPBGE doesn't need any new endpoints. It consumes the same API.

---

## Godot vs UPBGE: What Each Client Does

| Responsibility | Godot Client | UPBGE Client |
|---|---|---|
| Poll /snapshot | ZWRuntime.gd (every N frames) | engain_bge_bridge.py (Logic Brick timer) |
| Spawn entities | instance_scene() on PackedScene | scene.addObject() on template |
| Update positions | node.position = Vector3(...) | obj.worldPosition = Vector(...) |
| Sync back to Python | HTTP POST /world/sync | HTTP POST /world/sync (identical) |
| Object persistence | Dies on stop | Survives in .blend |
| Edit spawned objects | Requires EditorPlugin hack | Native Blender tools |
| Material editing | Inspector only | Full Blender shader editor |
| Animation | AnimationPlayer | Blender Actions + NLA |

---

## UPBGE Integration Architecture

```
┌─────────────────────────────────────────────┐
│           sim_runtime.py (Python)            │
│  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │
│  │Spatial3D│ │ Combat3D │ │ Dialogue3D   │  │
│  │ MR kern │ │ MR kern  │ │ MR kern      │  │
│  └────┬────┘ └────┬─────┘ └──────┬───────┘  │
│       └───────────┼──────────────┘           │
│              ┌────▼────┐                     │
│              │ HTTP API│ :8080               │
│              └────┬────┘                     │
└───────────────────┼─────────────────────────┘
                    │ JSON over HTTP
        ┌───────────┼───────────┐
        ▼                       ▼
┌───────────────┐     ┌─────────────────┐
│  Godot 4.x    │     │    UPBGE 0.50   │
│  ZWRuntime.gd │     │  engain_bge_    │
│  (thin client)│     │  bridge.py      │
│               │     │  (thick client) │
│  Objects die  │     │  Objects live   │
│  on stop      │     │  in .blend      │
└───────────────┘     └─────────────────┘
```

---

## File Map

### What you need in your UPBGE project:

```
your_project.blend          ← Blender file with Logic Bricks
  └── EngAInController      ← Empty object, runs the bridge
  └── EntityTemplate        ← Cube in main collection (hidden, spawnable)

scripts/
  engain_controller.py      ← Logic Brick entry point (Script mode)
  engain_bge_bridge.py      ← HTTP client + scene graph manager
```

### What stays untouched in EngAIn:

```
EngAIn/godotsim/
  sim_runtime.py            ← No changes
  runtime_core.py           ← No changes  
  command_dispatcher.py     ← No changes
  http_handlers.py          ← No changes
  spatial3d_mr.py           ← No changes
  combat3d_adapter.py       ← No changes
  ... (all subsystems)      ← No changes
```

---

## UPBGE-Specific Considerations

### Things UPBGE does better:
- Edit-while-playing loop (the whole point)
- Python is native (no HTTP needed for local calls, but we keep HTTP for architecture purity)
- Full Blender toolchain available during gameplay
- Objects spawned at runtime are real Blender objects

### Things UPBGE does worse:
- Fewer shader features than Godot 4
- Smaller community, less documentation
- Physics engine is older (Bullet vs Godot's custom)
- No built-in UI system (need BGE overlay or Blender panels)
- May be buggier on edge cases

### Things to watch for:
- `scene.addObject()` requires template in ACTIVE collection (not hidden/excluded)
- BGE runs at fixed logic tick rate (default 60), not frame-dependent
- Python runs in BGE's thread — long HTTP calls will freeze the game
- Use `threading` or `urllib.request` with timeout for non-blocking HTTP

---

## Migration Checklist

### Phase 1: Basic spawn loop (where you are now)
- [x] Logic Bricks fire Python script
- [x] Script mode works (logic.initialized pattern)
- [ ] EntityTemplate in correct collection (spawnable)
- [ ] scene.addObject() spawns cubes
- [ ] HTTP GET /snapshot from BGE script
- [ ] Parse snapshot → spawn/update objects

### Phase 2: Full state sync
- [ ] Poll sim_runtime every N ticks
- [ ] Diff snapshot vs scene objects
- [ ] Spawn new entities, remove dead ones
- [ ] Update positions/properties on existing
- [ ] POST /world/sync back to Python

### Phase 3: Creative loop
- [ ] Player edits spawned object in Blender (move, scale, material)
- [ ] BGE detects changes, syncs back to Python
- [ ] Python validates via AP rules
- [ ] Changes persist in .blend on save

### Phase 4: Command interface  
- [ ] BGE overlay or panel for text commands
- [ ] POST /command from BGE
- [ ] Display command results in BGE UI
- [ ] Scene load/switch from within BGE

---

## Key Difference from Godot Integration

In Godot, we had `ZWRuntime.gd` doing:
```gdscript
func _process(delta):
    poll_timer -= delta
    if poll_timer <= 0:
        var snapshot = http_get("/snapshot")
        apply_snapshot(snapshot)
        poll_timer = POLL_INTERVAL
```

In UPBGE, we have `engain_controller.py` doing:
```python
# Runs every logic tick via Logic Brick
if not hasattr(logic, 'bridge'):
    logic.bridge = EngAInBridge("http://localhost:8080")

logic.bridge.tick()  # polls, diffs, spawns/updates
```

Same pattern. Same data. Different scene graph API.
