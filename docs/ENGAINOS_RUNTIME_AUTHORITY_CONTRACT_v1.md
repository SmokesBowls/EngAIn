EngAInOS contract is the **runtime authority contract**.

Plain version:

EngAInOS decides whether a runtime action is allowed, converts safe scene/ZON/ZONJ data into runtime-facing forms, exposes Godot-facing runtime state, and blocks anything that tries to mutate the world without AP/reality authority.

It is **not** lore authority, not final prose authority, not 3D simulation truth, not trixel art generation, and not Godot rendering. It is the law/checkpoint layer between extracted scene data, agents, runtime, and Godot. The EngAInOS profile says its strongest identity is “decide what is allowed, normalize runtime contracts, expose safe state to Godot, and prevent loose ZON/scene/game data from mutating the world without AP authority.” 

The practical contract is this:

```text
incoming payload
→ protocol/envelope validation
→ contract/schema validation
→ reality-mode validation
→ authority-tier validation
→ AP rule evaluation
→ ZON/ZONJ/runtime conversion if allowed
→ runtime or Godot-facing output
→ reject safely if anything fails
```

The core rule:

```text
No mutation reaches runtime unless EngAInOS says allowed.
```

The main owned files/layers:

```text
launch_engine.py
  Blessed local bootstrap / startup authority.

runtime_client.py
  Client to runtime endpoints like /snapshot, /command, combat, inventory, dialogue.

engainos_server.py
  FastAPI/facade surface if used by Godot or tools.

core/authority_validator.py
  Tier + reality validation.

core/reality_mode.py
  DRAFT / IMBUED / FINALIZED / REPLAY / DREAM semantics.

core/ap_runtime.py
core/ap_engine.py
core/ap_complex_rules.py
core/ap_world_rules.py
core/ap_quest_rules.py
  AP rule loading, checking, and runtime-law logic.

core/protocol_envelope.py
  Runtime message/snapshot envelope shape.

core/scene_loader.py
core/scene_server.py
  Scene serving/loading bridge.

core/zon_bridge.py
core/zon_to_game.py
core/zon_to_entities.py
  ZON/ZONJ → runtime/game/Godot conversion.

core/spatial_skin_system.py
core/godot_adapter.py
  Entity3D/render-plan/Godot-facing conversion.

core/mesh_manifest.py
core/mesh_intake.py
  Mesh/skin manifest validation; possibly should later move partly to trixel systems.
```

The minimum inbound contract should look like this:

```json
{
  "trace_id": "string",
  "source": "mettaext|godotsim|godot|agent|human|test",
  "actor_id": "string",
  "actor_authority_tier": 0,
  "reality_mode": "DRAFT|IMBUED|FINALIZED|REPLAY|DREAM",
  "action": "string",
  "scene_id": "scene.example",
  "payload": {},
  "contract_version": "engainos.runtime_action.v1"
}
```

Required fields:

```text
trace_id
source
actor_id
actor_authority_tier
reality_mode
action
payload
```

Fail-closed behavior:

```json
{
  "allowed": false,
  "trace_id": "same trace_id if supplied",
  "stage": "protocol|contract|authority|reality|ap|conversion|runtime",
  "reason": "human-readable reason",
  "errors": [],
  "output": null
}
```

Allowed output should look like:

```json
{
  "allowed": true,
  "trace_id": "same trace_id",
  "stage": "allowed",
  "reason": "approved",
  "ap_decision": {
    "allowed": true,
    "rule_id": "string",
    "tier": 1,
    "reality_mode": "IMBUED"
  },
  "runtime_action": {
    "type": "spawn_entity|update_entity|command|load_scene|query",
    "payload": {}
  }
}
```

For Godot, the outbound contract is roughly:

```json
{
  "type": "spawn_entity",
  "id": "entity_id",
  "entity_type": "string",
  "position": [0, 0, 0],
  "render_mode": "placeholder|skin_2d|skin_3d",
  "scene_ref": "res://...",
  "collision_profile": "static|dynamic|trigger",
  "interaction_radius": 2.0
}
```

For AP decision, the contract should be:

```json
{
  "allowed": true,
  "reason": "string",
  "rule_id": "string",
  "blocked_by": null,
  "read_set": [],
  "write_set": [],
  "tier": 1,
  "reality_mode": "IMBUED",
  "trace_id": "string"
}
```

Boundary rules:

```text
Ask MrLore when canon truth, contradiction, identity, or finalized story meaning is involved.

Ask mettaext when ZON/ZONJ extraction shape is malformed or scene IDs/entities are ambiguous.

Ask godotsim when spatial state, physics, collision, proximity, or simulation truth is needed.

Ask trixel systems when mesh, skin, visual asset, render material, or trixel output is needed.

Ask EngAInOS before anything mutates runtime state or bypasses AP.
```

So the shortest contract name would be:

```text
ENGAINOS_RUNTIME_AUTHORITY_CONTRACT_v1
```

And its one-line law is:

```text
EngAInOS is the gate that turns proposed scene/runtime actions into allowed runtime actions, or rejects them with a traceable reason.
```

