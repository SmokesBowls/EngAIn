## godotsim project awareness profile

Project name resolved as: **godotsim — spatial/3D simulation and Blender bridge authority**

This stack is not the whole EngAIn machine. Its strongest authority is the 3D runtime lane: scene activation into spatial state, semantic entities into 3D render packets, simulation snapshots, bridge packets for Godot/UPBGE/Blender, and candidate terrain generation through Blender MCP.

It is **not fully clean authority yet**. The stack is powerful, but it carries several “two versions of the same idea” conflicts: `spatial3d.py` vs `spatial3d_mr.py` vs `spatial3d_adapter.py`, `sim_runtime.py` vs `runtime_core.py` vs `runtime_gateway.py`, two EnvironmentManager patterns, two protocol envelope styles, and unresolved adapter imports for behavior/combat/dialogue/inventory.

---

## 1. PROJECT ROLE

godotsim owns the **spatial/3D simulation lane**.

It owns:

`spatial3d_mr.py` as the deterministic, renderer-agnostic spatial physics kernel. It takes snapshot-in, deltas, and `dt`, then returns snapshot-out, accepted deltas, and alerts. Its internal entity schema is `id`, `pos`, `vel`, `radius`, `solid`, and `tags`. 

`spatial3d_adapter.py` as the protocol boundary between external API names and kernel names. It explicitly says internal state uses `pos` / `vel`, while external API uses `position` / `velocity`. 

`runtime_core.py` as the central runtime state machine, subsystem initializer, simulation loop, snapshot holder, and kernel orchestrator. It initializes scene manager, vault linker, protocol envelope, spatial/perception/behavior adapters, combat, inventory, dialogue, command dispatcher, and the simulation thread. 

`sim_runtime.py` as the slim HTTP server entrypoint. It instantiates `EngAInRuntime`, injects it into `RuntimeHTTPHandler`, attaches `EnvironmentManager`, performs vault auto-relink, installs live-edit shims, and starts `ThreadingHTTPServer` on `127.0.0.1:8080`. 

`scene_manager.py` as scene registry, activation, entity extraction, entity reset, semantic bridge injection, and active snapshot population. 

`bridge_integration.py`, `semantic_bridge.py`, `spatial_skin_system.py`, and `concept_profiles.json` as the semantic-to-3D bridge. They resolve ZON/ZW concepts into `Entity3D` packets with transform, placeholder mesh, color, collision role, AP profile, tags, and source data.   

`environment_manager.py`, `blender_mcp_bridge.py`, and `embodiment_contract_builder.py` as the candidate Blender terrain / embodiment path: ZONJ scene → terrain profile → Blender MCP → GLB → Godot mount / embodiment contract.   

It explicitly does **not** own:

The core narrative truth. That belongs upstream to vault / canon / mettaext.

The complete AP law. This stack imports governance from `godotengain/engainos/core`, especially `reality_mode`, `canon`, `intent_shadow`, and optional `ap_complex_rules`. That means godotsim enforces some mutation gates but does not originate the law. 

The Godot visual client. godotsim produces packets and snapshots; Godot renders them.

The Blender server itself. godotsim can call Blender MCP, but the actual MCP service is external: `blender-open-mcp` or `engain_blender_mcp`.

The terrain/trixelmap source authority. godotsim can consume terrain profiles and materialization contracts, but terrain field semantics should come from terrain/trixelmap or trixel composer.

Neighboring projects depending on godotsim:

`godot3d` / Godot thin client depends on godotsim for `/snapshot`, `bridge_entities`, transforms, pending embodiment contracts, terrain mount packets, and world updates.

`engainos` depends on godotsim to materialize state into spatial simulation and to enforce runtime mutation gateways against active snapshots.

`mettaext` depends on godotsim to turn scene meaning into visible/explorable 3D entities.

`trixelmap` / terrain depends on godotsim to provide coordinate bounds, placement authority, and mount targets.

`engain_blender_mcp` or `blender-open-mcp` depends on godotsim to generate Blender execution requests and consume generated GLB output.

---

## 2. CURRENT WORKING STATUS

Confirmed working by file structure:

The runtime is modularized. `sim_runtime.py` says it is only the entrypoint and delegates engine logic to `runtime_core.py`, HTTP routing to `http_handlers.py`, scene logic to `scene_manager.py`, command routing to `command_dispatcher.py`, and vault utilities to `vault_manager.py`. 

HTTP routing is real. `http_handlers.py` exposes `/health`, `/status`, `/snapshot`, `/transforms`, `/embodiment/pending`, `/environment/terrain/<scene_id>`, `/vault/status`, `/vault/search`, `/command`, `/scene/load`, `/vault/link`, `/world/sync`, `/world/load_mirror`, and `/embodiment/apply`. 

Scene activation is real. `scene_manager.py` normalizes scene docs, preserves `spatial_hints`, `zon_blocks`, `compiler_report`, and `validation`, clears stale entity/spatial/perception/behavior/events state on activation, extracts narrative entities, and runs semantic bridge into `snapshot["bridge_entities"]`. 

Semantic entity output is real. `spatial_skin_system.py` defines `Entity3D.to_dict()` with `entity_id`, `zw_concept`, `ap_profile`, `placeholder_mesh`, `skin_3d_id`, `color`, `color_hex`, `transform`, `collision_role`, `semantic_tags`, `kernel_bindings`, `is_placeholder`, and `source_data`. 

Spatial MR kernel is real. It parses `snapshot_in["spatial3d"]`, accepts deltas like `spatial/spawn`, `spatial/despawn`, `spatial/teleport`, `spatial/set_velocity`, `spatial/apply_impulse`, integrates gravity/damping, resolves collisions, enforces bounds, and returns alerts. 

Partially working:

Blender bridge is candidate, not settled. `blender_mcp_bridge.py` calls `POST {mcp_url}/tool` with `"name": "blender_execute_code"`, but `environment_manager.py` uses JSON-RPC MCP at `POST /mcp` with `initialize` and `tools/call`. Those are two different MCP calling styles.  

Embodiment contracts are defined, but not proven end-to-end. `embodiment_contract_builder.py` creates `trixel_embodiment.v1` contracts for Godot materialization, and `http_handlers.py` can queue and return pending embodiment contracts, but the actual Godot consumer is outside this stack.  

Runtime governance is partially integrated. `runtime_gateway.py` enforces explicit `reality_mode` and `actor_authority_tier`, blocks REPLAY, blocks FINALIZED below Tier 3, and optionally checks complex AP rules. But it imports authority modules from EngAInOS, so godotsim is an enforcement lane, not the law source. 

Untested or not proven from this 25-stack:

Behavior MR, perception MR, combat adapter, inventory integration, and dialogue integration are imported by `runtime_core.py`, but the actual files are not in this provided stack. The runtime degrades if they are missing. 

Navigation has no dedicated runtime adapter in this stack. It appears only as a topic extracted by `scene_extractor.py`, not as a real 3D navigation kernel. 

Godot autoload compatibility is not proven here. The files produce snapshots and packets, but no Godot `.gd` consumer is included in this 25-stack.

Abandoned, legacy, or proof-only:

`spatial3d.py` is a minimal stub, not the real kernel. It defines only `Spatial3DStateView` and `Alert`. It exists so the adapter can stand alone, but it lacks `handle_delta`, even though `spatial3d_adapter.py` calls `super().handle_delta(...)`. That is a serious mismatch.  

`protocol_envelope_server.py` looks like a proof/demo version. It defines `version`, `tick`, `epoch`, `content_hash`, and `payload`, while the active `protocol_envelope.py` defines `protocol`, `version`, `epoch`, `tick`, `hash`, `timestamp`, and `payload`. These are not the same wire schema.  

`blender_managment.py` is a sketch-style older EnvironmentManager pattern, and even its header says “In sim_runtime.py or a new environment_manager.py.” The actual newer `environment_manager.py` exists separately.  

---

## 3. ERROR PROFILE

Import/path errors:

`spatial3d_adapter.py` imports `Spatial3DStateView` and `Alert` from `spatial3d.py`, then calls `super().handle_delta(...)`. The stub `Spatial3DStateView` shown in `spatial3d.py` has `get_entity`, `get_all_entities`, and `set_entity`, but no `handle_delta`. That means `Spatial3DStateViewAdapter.handle_delta()` can fail at runtime unless another real `spatial3d.py` shadows this stub.  

`semantic_bridge.py` imports `yaml`. If PyYAML is not installed, config loading can fail before the bridge runs. 

`runtime_core.py` imports several optional modules not present in this 25-stack: `slice_builders`, `perception_mr`, `behavior3d_mr`, `perception_adapter`, `behavior_adapter`, `combat3d_adapter`, `inventory3d_integration`, and `dialogue3d_integration`. The code has fallbacks for many of them, but full 3D behavior/combat/dialogue/inventory cannot be trusted from this stack alone. 

Missing files:

No real Godot renderer script is included here.

No actual `combat3d_adapter.py`, `inventory3d_integration.py`, `dialogue3d_integration.py`, `behavior3d_mr.py`, `perception_mr.py`, or navigation adapter appears in the uploaded 25-stack.

No definitive MCP client compatibility contract is included. The stack has two calling styles, but no proof of which Blender MCP server is authoritative.

Duplicate files / duplicate concepts:

`environment_manager.py` and `blender_managment.py` both define EnvironmentManager-like behavior. `blender_managment.py` calls `BlenderMCPBridge.generate_terrain_from_zonj()`, while `environment_manager.py` does its own MCP JSON-RPC calls.  

`protocol_envelope.py` and `protocol_envelope_server.py` both define protocol envelopes but disagree on field names and version.  

`spatial3d.py`, `spatial3d_mr.py`, and `spatial3d_adapter.py` are three layers, but only two are coherent. `spatial3d_mr.py` is the real kernel, `spatial3d_adapter.py` is the intended translation layer, and `spatial3d.py` is too thin to satisfy the adapter’s inheritance assumptions.   

Stale backups / old vault path recovery leftovers:

`runtime_core.py` contains a hardcoded dead placeholder path check: `if os.path.exists("/path/to/vault/vault.manifest.json")`. That is not valid production behavior and should be removed or gated as example-only. 

`sim_runtime.py` defaults `_resolve_expected_root()` to `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn` if no manifest is passed. That may be historically useful, but it is a machine-specific root and can block launch on another machine. 

`vault_linker.py` and `vault_manager.py` both participate in vault loading. This is not automatically wrong, but it creates two vault pathways: one linker that converts markdown to ZONJ, and one manager that validates/syncs/mirrors manifests.  

Schema mismatch:

Kernel spatial uses `pos` and `vel`; protocol/adapter external API uses `position` and `velocity`; semantic bridge/Godot transform uses `transform.position`; runtime snapshot entities often use `pos`; bridge also emits `position_godot`, UPBGE `position`, and `transform_upbge`. This is deliberate in parts, but dangerous unless every consumer respects the boundary.  

Scene docs use both `@id` / `scene_id`, `@entities` / `entities`, and `=segments` / `segments`. `scene_manager.py` normalizes this, but external callers must still be careful. 

Protocol envelope mismatch is severe: active `protocol_envelope.py` uses `hash`; server proof file uses `content_hash`. Active uses `protocol`; proof file does not. Active version is `1.0.1`; proof version is `1.0.0`.  

Runtime bridge mismatch:

`http_handlers.py` imports `RuntimeGateway` inside `_handle_command`, so command mutation is governance-gated. But `/scene/load` manually repeats governance logic. That is workable, but it means two mutation paths must stay synchronized.  

`runtime_core.py` itself also checks governance in `_execute_command`, creating defense-in-depth but also possible double rejection / inconsistent rejection messages. 

Godot scene/autoload mismatch:

This stack assumes Godot reads `/snapshot`, `bridge_entities`, `/embodiment/pending`, and terrain info, but no Godot autoload file is present here to prove the exact consumer schema.

Generated-output drift:

Bridge output can include both Godot and UPBGE coordinate forms. `bridge_integration.py` keeps rotation unchanged during Godot→UPBGE conversion, explicitly warning that proper handedness/basis conversion depends on the consumer. That is a drift risk for Blender/UPBGE generated placement. 

Old architecture still present:

The stack still carries proof names: `blender_managment.py`, `protocol_envelope_server.py`, hardcoded vault examples, and two Blender MCP call styles.

---

## 4. CONTRADICTION PROFILE

Contradiction: “godotsim owns spatial3D,” but `spatial3d.py` is only a stub.

The real spatial authority is `spatial3d_mr.py`. `spatial3d.py` should be treated as compatibility scaffolding unless upgraded.  

Contradiction: “adapter routes all paths through AP → MR → State,” but the base class does not supply AP checks.

`spatial3d_adapter.py` says it routes through AP pre-checks via `super().handle_delta(...)`, but the provided `Spatial3DStateView` has no such method. That means the adapter’s stated role is ahead of its base implementation.  

Contradiction: “runtime is slim,” but `sim_runtime.py` contains vault auto-relink, live-edit snapshot shims, bridge entity injection helpers, root validation, and environment manager injection.

The top docstring says `sim_runtime.py` does exactly three things, but the actual file does more than entrypoint duty. It is slimmer than a monolith, but not truly only a launcher. 

Contradiction: `runtime_core.py` owns simulation, but it also contains legacy vault auto-link placeholder.

That belongs in `sim_runtime.py`, `vault_manager.py`, or `vault_linker.py`, not the core runtime constructor. 

Contradiction: Blender MCP bridge style.

`blender_mcp_bridge.py` calls `/tool` with `{"name":"blender_execute_code"}`, while `environment_manager.py` initializes JSON-RPC at `/mcp` and calls `tools/call`. These target different server contracts.  

Contradiction: output path authority.

`blender_mcp_bridge.py` defaults GLB output to `user://blender/...`, which is a Godot-style virtual path. `environment_manager.py` writes `/tmp/engain/<scene>_<profile>.glb`, a host filesystem path. `embodiment_contract_builder.py` defaults to `res://assets/blender/engain_biome_terrain.glb`. Those three paths cannot all be the same authority.   

Contradiction: Protocol envelope authority.

`protocol_envelope.py` appears active in `runtime_core.py`, while `protocol_envelope_server.py` describes itself as “SERVER-SIDE PROTOCOL ENVELOPE GENERATOR” with a different schema.   

Contradiction: 3D combat/dialogue/inventory named as loaded subsystems, but files not present in the stack.

`runtime_core.py` is ready to load them, and `command_dispatcher.py` routes commands to them, but this 25-stack does not prove their contracts.  

---

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

Proposed system: **Unified Spatial Runtime Contract**

Implied by: `spatial3d_mr.py`, `spatial3d_adapter.py`, `spatial_skin_system.py`, `bridge_integration.py`, `runtime_core.py`.

Missing before it becomes real:

A single canonical schema document saying when to use `pos`, `position`, `transform.position`, `position_godot`, and UPBGE `position`.

A fixed base `Spatial3DStateView.handle_delta()` or removal of the bad `super().handle_delta()` call.

A smoke test proving spawn → MR step → snapshot → bridge_entities → Godot packet.

Proposed system: **Godot/Blender Dual Coordinate Bridge**

Implied by: `bridge_integration.py`, `environment_manager.py`, `blender_mcp_bridge.py`, `embodiment_contract_builder.py`.

Missing:

A declared coordinate authority. The bridge currently maps Godot to UPBGE but leaves rotation unchanged. 

A single output path contract: `user://`, `/tmp/engain`, or `res://assets/blender`.

A Blender MCP compatibility adapter that supports one chosen server API.

Proposed system: **Trixel Embodiment Contract Pipeline**

Implied by: `embodiment_contract_builder.py`, `/embodiment/apply`, `/embodiment/pending`, `trixel_composer.py`.

Missing:

A proven Godot `SemanticRenderer` / `BlenderTerrainMount` consumer.

A terrain texture/recipe handoff contract from trixelmap/trixelcomposer.

A rule for whether terrain geometry is Blender-owned, trixel-owned, or hybrid.

Proposed system: **Vault-to-Scene-to-3D Auto Materializer**

Implied by: `vault_linker.py`, `vault_manager.py`, `scene_manager.py`, `semantic_bridge.py`, `bridge_integration.py`, `environment_manager.py`.

Missing:

A strict manifest path policy with no machine-specific fallbacks.

A stable event actor file path contract from mettaext.

A proof that `/scene/load` triggers terrain generation, bridge entity generation, and snapshot update without stale scene leakage.

---

## 6. INBOUND SCHEMA

Inbound item: scene/game state from engainos
Source project: `engainos`
Expected schema name: `runtime command envelope` or mutation request
Required fields: `command` or `action`, `reality_mode`, `actor_authority_tier`
Optional fields: `actor_id`, `source_system`, `scene_id`, `target_artifact`, command-specific payload
Failure behavior: reject with `governance_rejected` if `reality_mode` or `actor_authority_tier` is missing; reject REPLAY mutations; reject FINALIZED below Tier 3. 

Inbound item: ZONJ scene document
Source project: `mettaext` / vault linker / ingest pipeline
Expected filename or schema name: ZONJ scene
Required fields: `scene_id` or `@id`, plus `segments` or `=segments`
Optional fields: `where`, `@where`, `when`, `@when`, `environment`, `exits`, `entities`, `@entities`, `spatial_hints`, `zon_blocks`, `compiler_report`, `validation`
Failure behavior: `/scene/load` returns `invalid_zonj` if scene identity and segments are missing.  

Inbound item: scene meaning from mettaext
Source project: `mettaext`
Expected filename or schema name: `out_events_<scene>.json`
Required fields: `events`, with each event optionally carrying `actor`
Optional fields: any event metadata not consumed by godotsim
Failure behavior: bridge logs empty actors and continues with normal entity list; it never raises for missing event actor files. 

Inbound item: concept profile registry
Source project: godotsim local config, possibly mettaext/trixel later
Expected filename: `concept_profiles.json`
Required fields: `concepts`, each concept requiring `placeholder_mesh`, `ap_profile`, `collision_role`, `default_color`
Optional fields: `default_scale`, `tags`, `partial_matches`
Failure behavior: semantic bridge falls back to magenta cube / generic static if a concept cannot resolve.  

Inbound item: terrain fields from terrain/trixelmap
Source project: `terrain` / `trixelmap`
Expected schema name: terrain profile or scene environment
Required fields: at minimum `terrain_profile` or enough scene `where` text to infer one
Optional fields: `biome`, `preset`, `regions`, `polygon`, `tags`, material recipe path
Failure behavior: `environment_manager.py` falls back to `"generic"` terrain profile if no match is found.  

Inbound item: Blender execution channel
Source project: `engain_blender_mcp` or `blender-open-mcp`
Expected schema name: MCP tool execution
Required fields: MCP URL, tool name, code payload
Optional fields: session ID, export path, transport mode
Failure behavior: environment generation returns `None` or failed status if MCP initialize/call/export fails. 

Inbound item: Trixel recipe texture
Source project: `trixel_composer` / trixelmap
Expected schema name: recipe texture path
Required fields: `recipe_texture_path`, `terrain_profile`, `scene_id`, spatial bounds
Optional fields: assignment rule, mount node, mesh path
Failure behavior: embodiment contract can still be built only if caller provides path; no validator proves the file exists. 

---

## 7. OUTBOUND SCHEMA

Outbound item: 3D placement packets
Destination project: Godot 3D renderer, UPBGE/Blender bridge
Expected schema name: `bridge_entities` / `Entity3D`
Required fields: `entity_id`, `zw_concept`, `ap_profile`, `placeholder_mesh`, `transform`, `collision_role`, `semantic_tags`, `is_placeholder`
Optional fields: `skin_3d_id`, `color`, `color_hex`, `kernel_bindings`, `source_data`, `position_godot`, UPBGE `position`, `transform_upbge`, `presence`, `importance`, `behavior`, `dialogue`
Stability level: **candidate**. The `Entity3D` core is stable-ish, but extra Godot/UPBGE dual fields are still bridge-specific.  

Outbound item: simulation state
Destination project: Godot client, EngAInOS observer, debugging tools
Expected schema name: `/snapshot` protocol envelope
Required fields: active protocol envelope currently provides `protocol`, `version`, `epoch`, `tick`, `hash`, `timestamp`, `payload`
Optional fields in payload: `scene_id`, `entities`, `spatial`, `perception`, `behavior`, `world`, `events`, `scene`, `bridge_entities`, `spatial_hints`, `zon_blocks`, `compiler_report`, `validation`
Stability level: **candidate with fix flag**, because `protocol_envelope_server.py` defines a different envelope shape.  

Outbound item: embodied contracts
Destination project: Godot `SemanticRenderer` / `BlenderTerrainMount`
Expected schema name: `trixel_embodiment.v1`
Required fields: `contract_version`, `scene_id`, `coordinate_authority`, `geometry_authority`, `materialization`, `debug_trace`
Optional fields: mount node, mesh path, recipe texture path, assignment rule, warnings
Stability level: **candidate**. Contract exists, queue endpoints exist, consumer not proven in this stack.  

Outbound item: Blender generation requests
Destination project: `engain_blender_mcp` or `blender-open-mcp`
Expected schema name: MCP `tools/call` or legacy `/tool` call
Required fields: tool name, Python code, scene ID, terrain profile
Optional fields: output path, session ID, selected objects
Stability level: **unknown / conflict**, because two different MCP request styles exist.  

Outbound item: Godot/world update packets
Destination project: Godot world client
Expected schema name: `/transforms`, `/snapshot`, `/embodiment/pending`, `/environment/terrain/<scene_id>`
Required fields: depends on endpoint; terrain response needs `status`, `mesh_path`, `terrain_profile`, `scene_id` when complete
Optional fields: debug chain, generated terrain metadata
Stability level: **candidate**. HTTP endpoints exist, but Godot consumer is not inside this stack. 

Outbound item: vault status / loaded scenes
Destination project: EngAIn tools, human debugging, scene browser
Expected schema name: `/vault/status`, `/vault/search`, `VaultLinkResult`
Required fields: `status`, `vault_id`, `vault_root`, scene counts, registered scenes
Optional fields: errors, linked timestamp, manifest path
Stability level: **candidate**, because vault logic is split between `vault_linker.py`, `vault_manager.py`, runtime auto-relink, and HTTP handlers.  

---

## 8. AUTHORITY BOUNDARIES

godotsim must stop and ask engainos when:

A command wants to mutate a FINALIZED scene without Tier 3 authority.

A request lacks `reality_mode` or `actor_authority_tier`.

A rule belongs to AP/canon rather than spatial simulation.

A runtime mode decision is needed: DRAFT, IMBUED, FINALIZED, DREAM, REPLAY, TEST.

godotsim must stop and ask mettaext when:

Scene meaning is ambiguous.

Scene IDs conflict.

`out_events_<scene>.json` actor extraction disagrees with ZONJ `entities`.

A narrative entity should be present, absent, hidden, hostile, or interactable based on story truth.

godotsim must stop and ask terrain/trixelmap when:

A terrain profile cannot be inferred from scene text.

Terrain regions, walkable polygons, cover zones, heightmaps, or biome material rules are needed.

A trixel recipe or material assignment is missing.

godotsim must stop and ask Blender MCP authority when:

The MCP endpoint style is uncertain: `/tool` vs `/mcp` JSON-RPC.

A GLB export path must be chosen.

Blender code execution fails.

Godot needs a mountable asset path, not just a host `/tmp` path.

Other projects must stop and ask godotsim when:

They need canonical 3D placement.

They need Godot/UPBGE coordinate conversion.

They need current simulation state.

They need bridge entity packets.

They want to spawn/move/despawn entities in the spatial runtime.

They need an embodiment contract grounded in spatial bounds.

They need to know which scene is active in the 3D runtime.

---

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Which file is the real spatial authority: `spatial3d_mr.py` only, or `spatial3d_adapter.py` plus MR?

2. Should `spatial3d.py` remain a stub, or should it receive the missing `handle_delta()` AP base method?

3. Which protocol envelope is canonical: `protocol_envelope.py` with `hash`, or `protocol_envelope_server.py` with `content_hash`?

4. Which Blender MCP contract is real: `/tool` with `blender_execute_code`, or JSON-RPC `/mcp` with `initialize` and `tools/call`?

5. What is the canonical generated mesh path: `user://blender`, `/tmp/engain`, or `res://assets/blender`?

6. Is Godot coordinate space the master, or is `spatial3d_mr` coordinate space the master?

7. Should UPBGE/Blender rotation conversion be implemented now, or should Blender consumers accept unconverted rotation?

8. Are combat, inventory, dialogue, perception, and behavior adapters part of godotsim authority, or should they be moved to a neighboring project and only consumed here?

9. Should vault loading remain inside godotsim runtime, or should godotsim only receive already-compiled ZONJ from mettaext/engainos?

10. Which scene source is canonical when `@entities`, extracted entities, event actors, and bridge-generated fallback entities disagree?

---

## 10. STACK VERDICT

**AUTHORITY_WITH_FIX_FLAGS**

godotsim is not proof-only. It has a real runtime, real HTTP endpoints, real scene activation, real semantic bridge packets, real spatial MR kernel, real governance gateway integration, and a plausible Blender/Godot embodiment path.

But it cannot be marked `AUTHORITY_READY` yet because the stack contains unresolved authority splits:

`spatial3d.py` is too weak for `spatial3d_adapter.py`.

`protocol_envelope.py` and `protocol_envelope_server.py` disagree.

`environment_manager.py` and `blender_mcp_bridge.py` disagree on MCP transport.

`runtime_core.py`, `sim_runtime.py`, and `runtime_gateway.py` overlap more than their file comments admit.

3D combat/dialogue/inventory/behavior/perception are referenced but not proven inside this 25-stack.

The clean verdict is:

```text
godotsim = AUTHORITY_WITH_FIX_FLAGS

Owns:
- spatial3D runtime
- scene activation into 3D snapshot
- semantic entity-to-Entity3D bridge
- Godot/UPBGE placement packet generation
- candidate Blender terrain/embodiment handoff

Does not fully own yet:
- AP/canon law
- narrative truth
- Blender server transport
- Godot renderer implementation
- final terrain/trixel field authority
- proven combat/inventory/dialogue/navigation schemas
```

The next fix should be small and surgical: declare one canonical spatial schema, one protocol envelope, and one Blender MCP transport. After those three are frozen, this stack becomes much closer to true 3D authority.
