
shut out

lsof -nP -iTCP:8080 -sTCP:LISTEN
lsof -nP -iTCP:8090 -sTCP:LISTEN
ss -ltnp '( sport = :8080 or sport = :8090 )'


kill

kill -9





{fire up all}

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/tools 
./engain_stack_tmux.sh




{godot}-renderer

godot --path /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender --editor

This is your visual client. It runs the zonjrender Godot project in the editor so you can play the scene, see the spawned “bridge entities”, swap placeholder meshes for real skins, and interact with the runtime through UI tools. It’s the window where your story state becomes pixels, meshes, labels, and camera.
----

{upbge}-editor

cd /home/burdens/Applications/upbge-0.50-linux-x64
./blender --path /home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge/one_path.blend

This is your Blender/UPBGE world editor and alternate renderer. You use it to inspect and author 3D scene composition, test placeholder spawning in a Blender-native game loop, and eventually swap placeholders for Blender-authored assets. It’s where “engine state” can become a Blender scene with live objects.
----

{server 8080}-subsystems

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim
python3 sim_runtime.py

This is the main EngAIn simulation runtime. It hosts the live world state and core adapters (Spatial3D/Perception/Behavior/Combat/Inventory/Dialogue), ingests the vault scenes, loads a selected scene, runs the tick loop, and exposes HTTP endpoints like /health, /vault/link, /scene/load, /command, /snapshot, and /transforms. Everything else reads from or writes to this.
----

{local host 8765}-apengine

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 launch_engine.py

This is the AP/Authority sidecar. It’s the “rules brain” and orchestration layer that sits beside the sim runtime, meant to route AP queries, run rule checks, and coordinate engine-facing interfaces (the “engine ready” router you saw). It’s not the scene API and not the runtime; it’s the policy/authority engine lane.
----

{server 8090}-http 

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090

This is the optional HTTP facade (FastAPI) that Godot-side UI/HUD clients talk to. It serves endpoints like /api/hud/engine_summary and related “projection” views of the engine state. It’s not required for the sim to run, but it makes the UI layer cleaner and gives Godot a stable API surface for dashboards and tools.
----

{obsidian}-vault

cd /home/burdens/obsidian/obsidianburdenNov25

This is the source-of-truth content vault. It contains your narrative files and the vault.manifest.json. The runtime links to it, extracts/loads scenes, and uses it as the library of canonical content. Think of it as the “world book” the engine reads from and turns into playable scenes.

/////////////////////////////////////


***

## **📋 EngAIn System Architecture - ACCURATE (v2.0)**

***

### **CONTENT LAYER (Source of Truth)**

```bash
{obsidian}-vault

cd /home/burdens/obsidian/obsidianburdenNov25

Source-of-truth content vault containing narrative files and vault.manifest.json. 
The runtime links to it, extracts/loads scenes, and uses it as the library of 
canonical content. Think of it as the "world book" the engine reads from and 
turns into playable scenes.

STATUS: ✅ Linked (101 scenes available)
```

***

### **SIMULATION LAYER (World State)**

```bash
{server-8080}-subsystems

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim
python3 sim_runtime.py

Main EngAIn simulation runtime. Hosts live world state and core adapters 
(Spatial3D/Perception/Behavior/Combat/Inventory/Dialogue), ingests vault scenes, 
loads selected scene, runs tick loop @ 60Hz.

ENDPOINTS:
  /health          - Service health check
  /vault/link      - Link to content vault
  /scene/load      - Load scene by ID
  /command         - Execute commands (current: {"command":"look", "text":""})
  /snapshot        - CANONICAL render feed (payload.bridge_entities)
  /transforms      - Fast transform updates (polling only, not write)

STATUS: ✅ Running, 26 entities resolved from scene.01_the_ethereal_vigil
NOTE: /snapshot is the source of entity transforms for all renderers
“Entities resolved from loaded scene (count varies by scene).”
```

***

### **RULES LAYER (Authority Engine - Optional)**

```bash
{localhost-8765}-apengine

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 launch_engine.py

AP/Authority sidecar. Rules brain and orchestration layer that routes AP queries, 
runs rule checks, and coordinates engine-facing interfaces. Not the scene API, 
not the runtime—this is the policy/authority engine lane.

STATUS: ✅ Running, 3 rules loaded (pickup_key, unlock_door, open_door)
```

***

### **RENDERING LAYER (Visual Clients)**

```bash
{godot}-renderer

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender
godot --path . --editor

Visual client running zonjrender Godot project. Two modes:
  • EDITOR MODE: Tweak scenes, scripts, test in viewport
  • RUN MODE: F5 to play, see live spawned entities from :8080/snapshot

FEATURES:
  ✅ Semantic entity rendering (blue capsules + labels)
  ✅ Auto-polling: lifecycle (2.0s), transforms (0.1s)
  ✅ Unshaded materials (glows without lighting)
  ✅ @tool mode (spawn entities in editor without playing)
  ⚠️  UI click-select exists (scenes/control.gd) but not raycast-based
  ❌ Drag-to-move (planned, needs /command support)

SYNC LATENCY: Near real-time, bounded by 0.1s transform polling + network RTT
STATUS: ✅ Rendering 26 entities correctly
```

```bash
{upbge}-editor

cd /home/burdens/Applications/upbge-0.50-linux-x64
./blender /home/burdens/burdens_of_a_forgotten_past/EngAIn/upbge/one_path.blend

Blender/UPBGE world editor and alternate renderer. Inspect/author 3D scene 
composition, test placeholder spawning in Blender-native game loop.

FEATURES:
  ✅ Gray cube placeholders from EntityTemplate
  ✅ Polling @ 0.5s (spawn_poll_interval_s)
  ✅ Coordinate conversion: Godot Y-up → UPBGE Z-up
  ❌ Visual editing (not implemented yet)

USAGE: Open file, press P to start game (not --path flag)
STATUS: ✅ Spawning 26 entities, positions sync with Godot
```

***

### **UI LAYER (Optional Projection Service)**

```bash
{server-8090}-http

cd /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090

FastAPI facade serving projection views of engine state. Godot-side UI/HUD 
clients read from here for dashboard data. Not required for sim to run.

ENDPOINTS:
  /api/hud/engine_summary - Engine stats for UI display

NOTE: This is a projection/HUD service, NOT the source of entity transforms
      (that's :8080/snapshot)
      
STATUS: ⚠️  Optional, not always running
```

***

### **EDITING LAYER (Planned)**

```bash
{editing}-workflow

CURRENT CAPABILITIES:
  ✅ Manual API editing (curl to :8080/command)
  ✅ Entity selection in Godot (UI-based in scenes/control.gd)
  ❌ 3D raycast selection (needs CollisionShape3D on spawned entities)
  ❌ Drag-to-move (needs runtime command support)
  ❌ Inspector panel (not built yet)

PLANNED WORKFLOW:
  1. User clicks entity in Godot → UI selection or raycast
  2. Inspector panel shows properties (name, position, type, color)
  3. User modifies value → sends command to :8080
  4. Runtime updates world state (REQUIRES NEW COMMAND TYPE)
  5. All clients poll /snapshot → changes appear

PROPOSED API CONTRACT (not yet implemented in runtime):
  POST http://localhost:8080/command
  {
    "command": "update_entity",
    "entity_id": "korath",
    "transform": {"position": {"x": 20, "y": 0, "z": -8}},
    "color": {"r": 1.0, "g": 0.5, "b": 0.0}
  }

CURRENT TESTING METHOD:
  # Move entity via existing /command (if supported)
  curl -X POST http://localhost:8080/command \
    -H "Content-Type: application/json" \
    -d '{"command": "move_entity", "entity": "korath", "position": {...}}'

NEXT STEPS:
  1. Verify /command handler supports entity updates
  2. Add CollisionShape3D to spawned entities (for raycasting)
  3. Implement EntitySelector.gd with PhysicsRayQuery
  4. Build Inspector panel UI
  5. Wire up drag-to-move with command submission

STATUS: ⚠️  Selection works (UI-based), movement requires manual commands
```

***

## **🎯 System Startup Order (Corrected)**

```bash
# 1. Start simulation runtime (REQUIRED)
cd ~/burdens_of_a_forgotten_past/EngAIn/godotsim
python3 sim_runtime.py
# Wait for: "Server running on http://localhost:8080"

# 2. Link vault (one-time, or after vault changes)
curl -X POST http://localhost:8080/vault/link \
  -H "Content-Type: application/json" \
  -d '{"vault_path": "/home/burdens/obsidian/obsidianburdenNov25"}'

# 3. Load a scene
curl -X POST http://localhost:8080/scene/load \
  -H "Content-Type: application/json" \
  -d '{"scene_id": "scene.01_the_ethereal_vigil"}'

# 4. (Optional) Start AP engine
cd ~/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 launch_engine.py
# Wait for: "ENGINE READY"

# 5. Start Godot renderer/editor
cd ~/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender
godot --path . --editor
# Press F5 to run scene

# 6. (Optional) Start UPBGE editor
cd ~/Applications/upbge-0.50-linux-x64
./blender ~/burdens_of_a_forgotten_past/EngAIn/upbge/one_path.blend
# Press P to start game engine

# 7. (Optional) Start UI server
cd ~/godotengain/engainos
python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090
```

***

## **📊 Current State vs Target**

### **✅ WORKING NOW:**
- Vault → Runtime → Dual Rendering (Godot + UPBGE)
- 101 scenes available, scene loading works
- 26 entities visible with semantic rendering
- Real-time updates (near real-time, bounded by polling)
- Coordinate system conversion (Godot Y-up ↔ UPBGE Z-up)
- UI-based entity selection in Godot

### **⚠️  PARTIALLY WORKING:**
- Entity editing via manual curl commands (limited by /command handler)
- Latency varies (Godot 0.1-2.0s, UPBGE 0.5s, plus network RTT)

### **❌ NOT IMPLEMENTED YET:**
- 3D raycast-based entity selection (needs CollisionShape3D)
- Drag-to-move in either engine
- Visual property inspector panel
- Runtime support for update_entity command
- Save edited state back to vault
- Rotation/scale editing

***

## **🔧 Data Flow Diagram**

```
┌─────────────────────┐
│  Obsidian Vault     │ vault.manifest.json, 101 scenes
└──────────┬──────────┘
           │ reads
           ▼
┌─────────────────────┐
│  sim_runtime :8080  │ World state, tick @ 60Hz
│  /snapshot          │ ← CANONICAL entity data
│  /command           │ ← Write commands (limited)
│  /transforms        │ ← Fast polling (read-only)
└──────────┬──────────┘
           │
      ┌────┼────┬──────────┐
      │         │          │
      ▼         ▼          ▼
  ┌─────┐  ┌─────┐   ┌────────┐
  │Godot│  │UPBGE│   │AP:8765 │
  │ 0.1s│  │ 0.5s│   │ Rules  │
  └─────┘  └─────┘   └────────┘
      │         │
      └────┬────┘
           │ (planned)
           ▼
    ┌──────────────┐
    │ Edit commands│ ← NOT WORKING YET
    │ update_entity│    (needs runtime support)
    └──────────────┘
```

***

## **🎯 Selection Model Decision**

**Option A: UI Click-Select (Current - Simplest)**
- Already in `scenes/control.gd`
- Picks nearest entity by screen distance
- ✅ Works now
- ❌ Less precise (screen-space)

**Option B: 3D Raycast (Better - Needs Work)**
- Requires `CollisionShape3D` on each spawned entity
- PhysicsRayQuery from camera through mouse
- ❌ Not implemented
- ✅ More precise (world-space)

**RECOMMENDATION: Start with Option A, migrate to Option B later**

***

## **📝 Key System Invariants**

1. **:8080/snapshot is THE source of entity transforms** - All renderers must poll this
2. **:8090 is projection only** - UI dashboards, not entity data
3. **Coordinate systems differ** - Godot Y-up, UPBGE Z-up (bridge handles conversion)
4. **Polling-based sync** - Not websocket, not push, pull model with configurable intervals
5. **No save-to-vault yet** - Edits live in runtime memory only

***

**This is now ACCURATE documentation of what's built and honest about what's planned. No marketing fluff, just engineering truth.** ✅

Want me to tackle the first missing piece - adding `update_entity` support to the runtime's `/command` handler?
