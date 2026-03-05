# EngAIn Runtime Meta Reference
## The one doc for wiring any client into sim_runtime

**Runtime:** `sim_runtime.py` on `http://localhost:8080`
**Authority:** Python. Always. Clients render. Clients never own state.
**Clients proven:** Godot 4.x (thin), UPBGE 0.50 (thick creative)

---

## 1. HTTP Contract (what both clients share)

Every client talks to the same endpoints. No client-specific routes.

```
GET  /health                → {"ok":true, "service":"engain", "pid":811207, "ts":...}
GET  /snapshot              → full world state (THE BIG ONE — see §2)
POST /scene/load            → {"scene_id": "scene.04_the_convergence"}
POST /command               → {"command": "look"} or {"command":"damage","target":"guard","amount":5}
POST /vault/link            → {"vault_root": "/path/to/vault", "manifest": {<manifest content>}}
GET  /vault/search?q=giant  → {"hits":[...], "count":3, "total_scenes":101}
POST /world/sync            → {"world":{...}, "entities":{...}}  (client pushes changes back)
```

### Health check pattern
```
Your bridge already does this:  client.get_json("/health")
Response: {"ok": true, "service": "engain", "pid": 811207}
```

### Scene loading
```
POST /scene/load
Body: {"scene_id": "scene.04_the_convergence"}
Response: {"type":"result", "action":"scene/load", "scene_id":"scene.04_the_convergence", "status":"loaded"}
```

Scene IDs match vault manifest keys. Format: `scene.XX_name_here`
After loading, /snapshot returns populated bridge_entities.

---

## 2. Snapshot Shape (THE critical structure)

`GET /snapshot` returns the protocol envelope:

```json
{
  "protocol": "EngAIn v1.0.1",
  "payload": {
    "scene_id": "scene.04_the_convergence",
    "entities": {},
    "bridge_entities": [ ... ],
    "scene": {
      "entities": ["Senareth", "Giant", ...],
      "scene_id": "scene.04_the_convergence"
    }
  }
}
```

### Where the data actually lives

| Field                       | Type   | Use it?  | Notes                                    |
|-----------------------------|--------|----------|------------------------------------------|
| `payload.bridge_entities`   | Array  | **YES**  | Rich semantic data. This is what you spawn from. |
| `payload.entities`          | Dict   | No       | Empty in current build                   |
| `payload.scene.entities`    | Array  | No       | Just name strings, no transforms         |
| `payload.scene_id`          | String | Yes      | Current scene name                       |

### Unwrapping the envelope (both clients do this the same way)

**Python (UPBGE):**
```python
raw = client.get_json("/snapshot")
payload = raw.data.get("payload", raw.data)
bridge_entities = payload.get("bridge_entities", [])
scene_id = payload.get("scene_id", "")
```

**GDScript (Godot):**
```gdscript
var payload: Dictionary = data.get("payload", data)
var bridge_entities: Array = payload.get("bridge_entities", [])
var scene_id: String = payload.get("scene_id", "")
```

---

## 3. Entity Data Model (what each entity looks like)

Every item in `bridge_entities` is a dict with this shape:

```json
{
  "entity_id": "Senareth",
  "name": "Senareth",
  "inferred_type": "character",
  "zw_concept": "character",
  "ap_profile": "character_npc",
  "semantic_tags": ["character", "interactive"],
  "collision_role": "dynamic",
  "placeholder_mesh": "capsule",
  "transform": {
    "position": {"x": 17.5, "y": 0.0, "z": 0.0},
    "scale": {"x": 0.5, "y": 1.8, "z": 0.5}
  },
  "color": {"r": 0.2, "g": 0.6, "b": 1.0}
}
```

### Field reference

| Field              | Type     | Example                     | Purpose                                         |
|--------------------|----------|-----------------------------|-------------------------------------------------|
| `entity_id`        | string   | `"Senareth"`                | Unique key. Use for tracking spawned objects.    |
| `name`             | string   | `"Senareth"`                | Display name (label text)                        |
| `inferred_type`    | string   | `"character"`, `"creature"`, `"location"`, `"concept"` | Semantic type from bridge  |
| `zw_concept`       | string   | `"character"`               | ZW classification                                |
| `ap_profile`       | string   | `"character_npc"`           | Anti-Python constraint profile                   |
| `semantic_tags`    | [string] | `["character","interactive"]` | Freeform tags from semantic bridge             |
| `collision_role`   | string   | `"dynamic"`, `"static"`     | Physics hint                                     |
| `placeholder_mesh` | string   | `"capsule"`, `"box"`        | Suggested mesh shape                             |
| `transform.position` | {x,y,z} | `{"x":17.5,"y":0,"z":0}`  | World position                                   |
| `transform.scale`  | {x,y,z} | `{"x":0.5,"y":1.8,"z":0.5}` | Entity scale (giants=3.5 height, humans=1.8)   |
| `color`            | {r,g,b} | `{"r":0.2,"g":0.6,"b":1.0}` | Pre-computed by semantic bridge. 0.0-1.0 range. |

### Color meanings (set by semantic bridge, not by clients)
- Blue tones → characters
- Brown tones → creatures (giants)
- Green tones → locations/environment
- Grey → concepts/abstract

### Scale meanings
- `scale.y = 1.8` → human-height character
- `scale.y = 3.5` → giant
- `scale.y = 0.5` → small item/concept

---

## 4. Vault Linking (loading the 101-scene corpus)

Before /snapshot has entities, you need to link the vault and load a scene.

### Step 1: Link vault

```bash
curl -X POST http://localhost:8080/vault/link \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json
with open('/home/burdens/obsidian/obsidianburdenNov25/vault.manifest.json') as f:
    manifest = json.load(f)
print(json.dumps({
    'vault_root': '/home/burdens/obsidian/obsidianburdenNov25',
    'manifest': manifest
}))
")"
```

**CRITICAL:** `manifest` must be the parsed JSON content, NOT a filepath string.

Response: `{"scenes_loaded": 101}`

### Step 2: Load a scene

```bash
curl -X POST http://localhost:8080/scene/load \
  -H "Content-Type: application/json" \
  -d '{"scene_id": "scene.04_the_convergence"}'
```

Response: `{"type":"result","action":"scene/load","scene_id":"scene.04_the_convergence","status":"loaded"}`

### Step 3: Verify

```bash
curl -s http://localhost:8080/snapshot | python3 -c "
import sys,json
d=json.load(sys.stdin)
p=d.get('payload',d)
ents=p.get('bridge_entities',[])
print(f'{len(ents)} entities in {p.get(\"scene_id\",\"?\")}')"
```

Expected: `29 entities in scene.04_the_convergence`

### Convenience script (test_bridge.sh)

Location: `/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/test_bridge.sh`
Does vault link + scene load + snapshot check in one shot.

---

## 5. Key Paths on Disk

| What                    | Path                                                                              |
|-------------------------|-----------------------------------------------------------------------------------|
| sim_runtime.py          | `~/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py`                    |
| Obsidian vault          | `~/obsidian/obsidianburdenNov25/` (102 .md files, 17 books)                       |
| vault.manifest.json     | `~/obsidian/obsidianburdenNov25/vault.manifest.json`                               |
| ZONJ scene files        | `~/burdens_of_a_forgotten_past/EngAIn/mettaext/ingested/runtime_scenes/`           |
| UPBGE project           | `~/burdens_of_a_forgotten_past/EngAIn/upbge/one_path.blend`                        |
| UPBGE bridge            | `~/burdens_of_a_forgotten_past/EngAIn/upbge/engain_upbge_bridge.py`                |
| UPBGE HTTP client       | `~/burdens_of_a_forgotten_past/EngAIn/upbge/engain_http_client.py`                 |
| test_bridge.sh          | `~/burdens_of_a_forgotten_past/EngAIn/godotsim/test_bridge.sh`                     |
| Semantic bridge         | `~/burdens_of_a_forgotten_past/EngAIn/godotsim/spatial_skin_system.py`             |
| Concept profiles        | `~/burdens_of_a_forgotten_past/EngAIn/godotsim/concept_profiles.json`              |

---

## 6. Spawning Pattern (client-agnostic pseudocode)

Both UPBGE and Godot follow the same loop:

```
every N seconds:
    snapshot = HTTP GET /snapshot
    payload = snapshot["payload"]
    bridge_entities = payload["bridge_entities"]

    seen = {}
    for entity in bridge_entities:
        eid = entity["entity_id"]
        seen[eid] = true

        if eid in managed_objects:
            update position, scale, color
        else:
            spawn new object from template
            set position from entity.transform.position (x, y, z)
            set scale from entity.transform.scale (x, y, z)
            set color from entity.color (r, g, b)
            store entity_id, name, type as metadata
            managed_objects[eid] = new_object

    for eid in managed_objects:
        if eid not in seen:
            destroy object
            remove from managed_objects
```

### UPBGE-specific spawn

```python
obj = scene.addObject("EntityTemplate", owner, 0)
obj.worldPosition = [pos["x"], pos["y"], pos["z"]]
obj.localScale = [scl["x"], scl["y"], scl["z"]]
obj.color = [col["r"], col["g"], col["b"], 1.0]
obj["entity_id"] = eid          # game property
obj["entity_type"] = entity["inferred_type"]
```

### Godot-specific spawn

```gdscript
var node = MeshInstance3D.new()
node.mesh = BoxMesh.new()  # or CapsuleMesh for characters
node.position = Vector3(pos.x, pos.y, pos.z)
node.scale = Vector3(scl.x, scl.y, scl.z)
node.material_override = unshaded_material(Color(col.r, col.g, col.b))
node.set_meta("entity_id", eid)
add_child(node)
```

---

## 7. What's Proven vs What's Not

### Proven (don't rebuild these)
- sim_runtime boots, all 7 subsystems load
- Vault linking: 101 scenes from manifest
- Scene loading: 29 bridge_entities from Chapter 4
- Semantic bridge: entities have position, scale, color, type, tags
- Protocol envelope: consistent shape, unwrap via payload key
- UPBGE bridge: KX_PythonComponent connects, health polling works at 0-3ms
- HTTP client: stdlib-only, runs in BGE Python, proper error handling

### Not yet working
- UPBGE entity spawning (bridge polls health but doesn't fetch /snapshot yet)
- Godot client (SemanticRenderer exists but untested with current snapshot shape)
- Bidirectional sync (/world/sync from client back to runtime)
- Scene switching from within either client
- Trae Agent behavior scripting (not integrated in current architecture)
- Blender asset generation (started but incomplete)

### Architecture decisions (don't revisit these)
- Python is authoritative, rendering clients are consumers
- Narrative is single source of truth (story-first extraction)
- Godot is thin client, UPBGE is thick creative client
- Both share same HTTP API, same snapshot format
- Don't port empire code — start fresh in current architecture
