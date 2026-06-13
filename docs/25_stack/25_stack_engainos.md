## EngAInOS project awareness profile

Project: **engainos**
Role: **runtime law / AP authority / Godot-facing runtime authority**

This stack tastes like the law layer, not the art layer and not the lore layer. Its strongest identity is: **decide what is allowed, normalize runtime contracts, expose safe state to Godot, and prevent loose ZON/scene/game data from mutating the world without AP authority.**

---

## 1. PROJECT ROLE

EngAInOS owns the **runtime authority boundary**. Its own bootstrap says `launch_engine.py` is the “ONLY blessed runtime entrypoint,” and that if it fails, the engine should be fixed rather than bypassed. 

It owns:

Runtime startup authority: `launch_engine.py`

AP rule loading/evaluation bridge: `ap_runtime.py`, `ap_engine.py`, `ap_world_rules.py`, `ap_quest_rules.py`

Protocol shape and envelope authority: `protocol_envelope.py`

Runtime client/facade authority: `runtime_client.py`, `engainos_server.py`

Scene serving/loading authority: `scene_server.py`, `scene_loader.py`

Godot-facing conversion authority: `godot_adapter.py`, `spatial_skin_system.py`

ZON-to-runtime/game conversion authority: `zon_bridge.py`, `zon_to_game.py`, `zon_to_entities.py`

Mesh/skin contract validation currently present but probably should be externalized: `mesh_manifest.py`, `mesh_intake.py`

It does **not** own final prose canon. `_mrlore` owns canon/lore truth. EngAInOS can require a canon authority token or truth anchor, but it should not decide whether a chapter event is canonically true.

It does **not** own raw narrative extraction. `mettaext` owns ZON/ZONJ production.

It does **not** own 3D simulation truth. `godotsim` owns spatial/sim packets and scene simulation behavior.

It does **not** own final visual rendering or trixel art production. Trixel systems own render/visual packets, mesh generation, skins, and visual asset pipelines.

Neighboring projects that depend on EngAInOS: Godot shells need allowed commands and runtime state; mettaext needs a strict receiver for ZON/ZONJ; `_mrlore` needs EngAInOS to respect canon gates; godotsim needs runtime-accepted spatial packets; trixel systems need EngAInOS to consume render references without becoming the art generator.

---

## 2. CURRENT WORKING STATUS

Confirmed working from the stack:

`launch_engine.py` has a real bootstrap path, invariant checks, core file requirements, import boundary checks, AP runtime init, scene server startup, and Godot adapter readiness. It checks for `mesh_intake.py`, `mesh_manifest.py`, `scene_server.py`, and `godot_adapter.py`, then starts a scene HTTP server on port `8765`. 

`runtime_client.py` is a current NGAT-RT client for `/snapshot`, `/command`, `/combat/damage`, `/inventory/take`, `/inventory/drop`, `/inventory/wear`, `/dialogue/say`, and `/dialogue/ask`. 

`zon_bridge.py` is strict and useful for typed combat conversion. It requires `entities` as a dict and requires combat entities to have `health` and `max_health`. It also supports damage events with either `attacker/target` or `source_id/target_id`. 

`spatial_skin_system.py` is conceptually clean. It says the placeholder mesh is always the real game object, and skins are optional visual overlays for 3D, 2D, or fallback color. 

Partially working:

AP exists in several forms, but not fully unified. There is `ap_engine.py`, `ap_runtime.py`, `ap_world_rules.py`, `ap_quest_rules.py`, and `ap_complex_rules.py`. The complex AP rule file explicitly describes pre-execution vetting that requires querying kernel state before authorizing commands.  That is good doctrine, but it is not clearly wired as the single mandatory gate for every mutation path.

Scene loading exists twice: `scene_loader.py` prepares scene data for Godot, while `scene_server.py` also serves scenes and AP queries. That can work, but the boundary is blurred.

ZON conversion exists in multiple shapes. `zon_to_game.py` expects `entities` as a dict, while `zon_to_entities.py` expects `entities` as a list. That is a live schema mismatch.  

Untested or uncertain:

Whether all runtime commands must pass through AP before mutation.

Whether `contract_validator.py` is actually called in front of runtime commands.

Whether `authority_validator.py` is called by the runtime facade, or only exists as a pure helper.

Whether Godot-facing commands are consistently envelope-wrapped.

Whether `scene_server.py` and `engainos_server.py` are meant to coexist or one should be the only server authority.

Abandoned, legacy, or proof-only:

`runtime_api.py` looks stale beside `runtime_client.py`. It imports `NGATRuntimeClient`, while current `runtime_client.py` defines `NGATRTClient`, which suggests old client/API naming drift.  

`deep_seek_set_1_2_3.md` and `dream_event_store.txt` are not EngAInOS runtime-law files. They contain Godot implementation guides and dream/reality mechanics, but they are closer to design/prototype material than runtime authority.  

---

## 3. ERROR PROFILE

Import/path errors:

`launch_engine.py` hard-stops if run outside `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`. That protects authority, but it can break if the actual active root is now a different path. 

`scene_loader.py` imports `mettaext.scene_identity`, which means EngAInOS depends on a neighboring project for canonical scene IDs. If `mettaext` is not installed or not on `PYTHONPATH`, scene loading fails.

`runtime_api.py` imports a client class name that does not match current `runtime_client.py`. That is a likely stale import.

Missing files:

`contract_validator.py` expects frozen docs schemas under a `docs/schema` path and returns `SCHEMA_MISSING` if they are not present. 

`mesh_manifest.py` can reject manifests if mesh paths are unresolved or missing. 

Duplicate files:

Two runtime client surfaces exist: `runtime_api.py` and `runtime_client.py`.

Two scene surfaces exist: `scene_loader.py` and `scene_server.py`.

Multiple ZON conversion surfaces exist: `zon_bridge.py`, `zon_to_game.py`, `zon_to_entities.py`, and possibly semantic bridge logic.

Two reality/canon authorities appear conceptually: `reality_mode.py` and canon lifecycle logic. The reality file says FINALIZED and REPLAY are special authority states, while canon lifecycle also manages DRAFT → IMBUED → FINALIZED.  

Stale backups:

The stack strongly suggests `runtime_api.py` is the stale API surface. Keep `runtime_client.py` and `engainos_server.py`; retire or rewrite `runtime_api.py`.

Schema mismatch:

`zon_bridge.py` requires `entities` as a dict for combat snapshots. 
`zon_to_game.py` also reads `entities` as a dict. 
`zon_to_entities.py` reads `entities` as a list. 
Godot-facing exported scenes use `entities` as a list. 

That means the project needs an explicit rule:

`ZONJ.entities` may be dict internally, but `GodotScene.entities` is list; conversion must be named and validated.

Runtime bridge mismatch:

`engainos_server.py` fronts NGAT-RT, while `launch_engine.py` starts its own scene server on `8765`, and `runtime_client.py` targets NGAT-RT on `8080`. This is not wrong, but it creates three runtime faces: NGAT-RT, EngAInOS facade, and scene server.

Godot scene/autoload mismatch:

`godot_adapter.py` outputs render data, while `scene_loader.py` outputs spawn commands with hardcoded `scene_ref` like `res://assets/EngAInDragon.tscn`. If the Godot project’s actual dragon path is different, the adapter assumptions fail.

Generated-output drift:

`zon_to_game.py` exports a Godot-compatible JSON scene, but `scene_loader.py` then reformats scene data again. That can cause drift between exported scene JSON and runtime spawn commands.

Old architecture still present:

The word “Empire” remains in `zon_bridge.py` and `zon_to_game.py`. The newer project language seems to be EngAInOS/AP/runtime authority, so “Empire commands” should be renamed or quarantined as legacy.  

---

## 4. CONTRADICTION PROFILE

The largest contradiction is that EngAInOS says `launch_engine.py` is the only blessed runtime entrypoint, but the stack also contains `engainos_server.py`, `runtime_client.py`, `scene_server.py`, and stale `runtime_api.py`. The fix is not to delete all but one; the fix is to name their lanes:

`launch_engine.py` = local engine bootstrap
`runtime_client.py` = outbound NGAT-RT client
`engainos_server.py` = FastAPI facade
`scene_server.py` = scene/AP query server, or legacy if replaced
`runtime_api.py` = stale/hold unless rewritten

The second contradiction is AP shape. `ap_engine.py` uses string predicates and effects. `ap_world_rules.py` and `ap_quest_rules.py` use dict predicates/effects. That is not fatal, but it means there is no single AP rule schema yet.

The third contradiction is reality authority. `reality_mode.py` says FINALIZED is not editable and REPLAY is read-only, but `authority_validator.py` allows tier 3 mutation in FINALIZED while `reality_mode.py` treats FINALIZED as not editable.   Human needs to decide whether Tier 3 can mutate FINALIZED, or only create a new authorized revision.

The fourth contradiction is trixel ownership. `mesh_manifest.py` says it is the contract enforcer between Trixel law and mesh tools.  That makes it valuable, but it probably belongs to trixel systems, with EngAInOS consuming the manifest contract rather than owning art intake.

The fifth contradiction is Godot authority. EngAInOS should emit commands and render plans, not assume actual Godot scene paths unless those paths are part of an inbound Godot capability registry.

---

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

Proposed system: **EngAInOS Authority Gate v1**

Implied by: `authority_validator.py`, `contract_validator.py`, `ap_engine.py`, `ap_runtime.py`, `protocol_envelope.py`, `reality_mode.py`

Missing before real: one mandatory request path:

`incoming payload → protocol envelope validation → contract validation → authority/reality validation → AP rule evaluation → runtime mutation or rejection`

Right now, the pieces exist, but the single enforced path is not obvious.

Proposed system: **Canonical ZON/ZONJ Runtime Bridge v1**

Implied by: `zon_bridge.py`, `zon_to_game.py`, `zon_to_entities.py`, `godot_adapter.py`, `scene_loader.py`

Missing before real: one canonical schema map:

`Mettaext ZONJScene → EngAIn GameScene → Entity3D/RenderPlan → GodotSpawnCommand`

Also missing: formal conversion between dict-entity and list-entity shapes.

Proposed system: **Godot Runtime Facade v1**

Implied by: `engainos_server.py`, `runtime_client.py`, `engine_summary.py`, `godot_adapter.py`, `scene_loader.py`

Missing before real: one blessed Godot-facing contract for:

`/api/health`, `/api/snapshot`, `/api/command`, `/api/hud/engine_summary`, `/api/scene/load`, `/api/ap/decision`

Proposed system: **Trixel Manifest Consumption Boundary**

Implied by: `mesh_manifest.py`, `mesh_intake.py`, `spatial_skin_system.py`, `zon_to_entities.py`

Missing before real: move mesh creation/intake out to trixel systems, keep only `skin_3d_id`, `placeholder_mesh`, `collision_role`, `ap_profile`, and validated manifest reference inside EngAInOS.

---

## 6. INBOUND SCHEMA

Inbound from `mettaext`: `ZONJScene` / `.zonj.json`

Required fields:

`scene_id` or canonical scene id
`description` optional but strongly preferred
`entities`
`events`
`locations` optional
`initial_state` optional
`metadata.where` optional but useful for scene placement

Failure behavior:

Missing `scene_id`: use `unknown_scene`, but mark as unsafe for authority.
Missing `entities`: allowed for non-visual scenes, but cannot spawn gameplay entities.
Wrong entity shape: hard reject unless conversion lane is explicit.

Inbound from `_mrlore`: `CanonAuthorityPacket`

Required fields:

`truth_anchor`
`canon_state`: DRAFT / IMBUED / FINALIZED / REPLAY
`source_chapter` or `source_file`
`allowed_mutation_tier`
`review_status`

Failure behavior:

Missing truth anchor: reject canonical query/mutation. `contract_validator.py` already treats missing `authority.truth_anchor` as `MISSING_TRUTH_ANCHOR` for query contracts. 

Inbound from `godotsim`: `SpatialSimPacket`

Required fields:

`scene_id`
`entities`
`position`
`rotation` optional
`velocity` optional
`collision_role`
`sim_tick` or `time`

Failure behavior:

Missing position: default to `[0,0,0]` only in draft/test; reject in FINALIZED/REPLAY.

Inbound from trixel systems: `RenderVisualPacket` / `TrixelManifest`

Required fields:

`zw_concept`
`ap_profile`
`collision_role`
`lod_class`
`placeholder_mesh`
`geometry` with `source_tool`, `source_file`, `export_format`, `vertex_count`, `face_count`

Failure behavior:

Reject if unsupported placeholder mesh, invalid collision role, invalid LOD class, missing mesh, or vertex/face constraints fail. `mesh_manifest.py` already validates those fields. 

---

## 7. OUTBOUND SCHEMA

Outbound to Godot: `GodotSpawnCommand`

Required fields:

`type: "spawn_entity"`
`id`
`entity_type`
`position`
`render_mode`
`scene_ref` or placeholder mesh/render plan
`collision_profile`
`interaction_radius`

Stability: **candidate**

Outbound to Godot HUD: `EngineSummary`

Required fields:

`game_time`
`scene_id`
`active_quests`
`completed_quests`
`combat_state`
`reality_mode`
`player_health`
`player_health_max`
`player_location`
`entities_count`
`tick_rate`
`pillar_status`

Stability: **candidate/stable-ish** because `engine_summary.py` is clearly a read-only Godot HUD projection. 

Outbound to runtime: `AllowedRuntimeAction`

Required fields:

`trace_id`
`action`
`actor/entity`
`target` optional
`payload`
`authority_context`
`ap_decision`
`reality_mode`

Stability: **candidate**

Outbound to AP/history: `APDecision`

Required fields:

`allowed: bool`
`reason`
`rule_id` or `blocked_by`
`read_set`
`write_set`
`tier`
`reality_mode`

Stability: **candidate**

Outbound to mettaext/_mrlore: `RuntimeStateObservation`

Required fields:

`scene_id`
`tick`
`entities` summary
`events_applied`
`events_rejected`
`canon_conflicts`

Stability: **unknown**

Outbound to trixel systems: `VisualNeedRequest`

Required fields:

`zw_concept`
`placeholder_mesh`
`skin_2d_id` optional
`skin_3d_id` optional
`ap_profile`
`collision_role`
`semantic_tags`

Stability: **candidate**

---

## 8. AUTHORITY BOUNDARIES

EngAInOS must stop and ask `_mrlore` when:

A scene is FINALIZED or canon-affecting.

A contradiction must be resolved in story/lore.

A truth anchor is missing.

A requested mutation changes named canon history.

EngAInOS must stop and ask `mettaext` when:

ZON/ZONJ structure is malformed.

Entity extraction is ambiguous.

Scene IDs cannot be canonicalized.

Dialogue/event extraction is missing required actors or targets.

EngAInOS must stop and ask `godotsim` when:

Spatial state conflicts with simulation.

Collision, position, velocity, or world physics are unclear.

A runtime command depends on simulated proximity or physical reachability.

EngAInOS must stop and ask trixel systems when:

A skin, mesh, render asset, or visual packet is missing.

Mesh manifest validation fails.

The visual system requests an art-generation decision rather than a runtime placeholder.

Other projects must stop and ask EngAInOS when:

They want to mutate runtime state.

They want to mark an action as allowed.

They want to send Godot commands that affect game state.

They want to bypass AP.

They want to turn ZON/ZONJ into active game entities.

They want to commit a scene state into runtime.

---

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Is `launch_engine.py` truly the only blessed local entrypoint, or is `engainos_server.py` now the real entrypoint for Godot-facing runtime?

2. Should `runtime_api.py` be deleted, quarantined, or rewritten to match `runtime_client.py`?

3. Is `scene_server.py` still active, or should all scene serving move under `engainos_server.py`?

4. Which AP rule shape is canonical: string predicates/effects from `ap_engine.py`, or dict predicates/effects from `ap_world_rules.py` and `ap_quest_rules.py`?

5. Can Tier 3 mutate FINALIZED scenes, or must Tier 3 create a new revision rather than editing canon?

6. Should ZON/ZONJ `entities` be a dict, a list, or explicitly two forms: `ZONJ.entities_by_id` and `GodotScene.entities[]`?

7. Does EngAInOS own `mesh_manifest.py` and `mesh_intake.py`, or should those move to trixel systems?

8. What is the canonical Godot scene path for dragon/entity visual instancing?

9. Is “Empire” now a dead name that should be removed from code comments and command schemas?

10. What is the mandatory mutation path: protocol envelope → contract validator → authority validator → AP engine → runtime, or something else?

---

## 10. STACK VERDICT

**AUTHORITY_WITH_FIX_FLAGS**

EngAInOS is not proof-only. It has real runtime authority pieces: a blessed bootstrap, AP engine pieces, runtime client/facade, protocol envelope, scene loader/server, Godot adapter, ZON bridge, entity conversion, and HUD summary. The stack clearly knows its job.

But it cannot be called fully `AUTHORITY_READY` yet because the authority path is not single-file obvious, AP rule schemas conflict, runtime API/client naming has drifted, scene loader/server responsibilities overlap, and ZON entity shape is inconsistent across converters.

My clean verdict:

`engainos` should remain the **runtime law/AP/Godot authority project**, but it needs a short consolidation pass:

Keep:

`launch_engine.py`
`engainos_server.py`
`runtime_client.py`
`protocol_envelope.py`
`ap_engine.py`
`ap_runtime.py`
`ap_world_rules.py`
`ap_quest_rules.py`
`authority_validator.py`
`contract_validator.py`
`reality_mode.py`
`scene_loader.py` or `scene_server.py`, not both as equal authorities
`godot_adapter.py`
`zon_bridge.py`
`zon_to_game.py`
`zon_to_entities.py`
`spatial_skin_system.py`
`engine_summary.py`

Fix or quarantine:

`runtime_api.py`
old “Empire” naming
duplicate scene server/loader authority
dict/list entity mismatch
trixel mesh intake ownership
DeepSeek/Godot dream prototype files inside this stack

The heart is good. The law exists. The danger is not missing authority; the danger is **too many old doors into authority**.
