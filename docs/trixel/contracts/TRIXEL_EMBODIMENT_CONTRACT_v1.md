# TRIXEL EMBODIMENT CONTRACT v1

Status: Draft contract, production migration target
Scope: EngAIn semantic scene state to deterministic Godot trixel terrain embodiment
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

---

## 1. Purpose

The Trixel Embodiment Contract defines the deterministic ABI where EngAIn semantic/runtime scene state becomes renderable trixel terrain for Godot.

This contract exists to collapse the current trixel ecosystem into one coherent lane:

```text
Narrative / ZONJ scene
→ normalized runtime scene document
→ trixel embodiment contract
→ deterministic terrain grid
→ role and atlas resolution
→ Godot terrain embodiment
```

The contract is not a new planner, renderer, governance system, or art generator. It formalizes the strongest existing lane already present in the repository so future work can converge instead of creating Trixel v7.

Every trixel embodiment path must either:

1. produce this contract,
2. consume this contract,
3. validate this contract,
4. or be explicitly marked legacy/fallback.

That rule is the main architectural boundary.

---

## 2. Non-goals

This contract does not:

- define canonical narrative state;
- mutate runtime authority or AP governance state;
- let Godot own authoritative world state;
- replace ZONJ, ZON, AP, or the simulation snapshot model;
- invent a new terrain planner;
- define final visual style or final trixel aesthetics;
- require immediate deletion of old terrain/planning/render experiments;
- require immediate shader, parallax, glow, biome, or GPU work;
- hand-edit generated terrain artifacts;
- make generated `.engain_cache/terrain_plans/*.json` canonical source.

Art quality, biome richness, glow layers, parallax, shaders, animation, and asset-generation improvements happen after this ABI is stable.

First make incarnation deterministic, inspectable, and singular. Then improve art.

---

## 3. Current operational lane

The current strongest lane is:

```text
Scene server payload
→ godotnew/semantic/scripts/Boot.gd
→ Boot._adapt_scene_server_payload_to_runtime_doc()
→ godotnew/semantic/trixel/TrixelEnvironmentPlanner.gd
→ TrixelEnvironmentPlanner.plan(runtime_scene_doc)
→ terrain/trixel_world_adapter.py --demo --context ...
→ terrain_grid JSON
→ Boot attaches terrain_grid to runtime scene doc
→ Boot._apply_environment_from_scene_doc()
→ godotnew/semantic/scripts/SemanticRenderer.gd
→ SemanticRenderer.set_environment_layout(layout)
→ SemanticRenderer._spawn_terrain_grid()
→ godotnew/semantic/trixel/TrixelRoleResolver.gd
→ SemanticRenderer._load_atlas_for(terrain)
→ godotnew/semantic/trixel/trixelassets/<terrain>/atlas_meta.json
→ godotnew/semantic/trixel/trixelassets/<terrain>/atlas.png
→ StaticBody3D / MeshInstance3D Godot terrain cells
```

The lane is already operational. A read-only audit verified that repeated calls to `terrain/trixel_world_adapter.py --demo` with identical semantic input produced identical output hashes.

This contract promotes that lane into the formal embodiment ABI.

---

## 4. Authority ownership

### 4.1 Runtime authority

The Python runtime and EngAInOS authority layers remain responsible for authoritative world state, AP rules, mutation permissions, and canonical state transitions.

Trixel embodiment is a visual/materialization boundary. It must not become canonical world authority.

### 4.2 Planner authority

`godotnew/semantic/trixel/TrixelEnvironmentPlanner.gd` is the primary trixel embodiment planner boundary.

Responsibilities:

- accept normalized runtime scene documents;
- extract typed semantic terrain inputs;
- call deterministic terrain backends when needed;
- normalize terrain aliases through the vocabulary binding layer;
- construct a complete trixel embodiment contract;
- identify fallback or treaty/proof sources explicitly;
- return a deterministic contract for identical input.

### 4.3 Backend terrain-field authority

`terrain/trixel_world_adapter.py` is a deterministic terrain field backend.

Responsibilities:

- convert structured terrain context into terrain grids;
- convert terrain field values through `terrain/terrain_thresholds.py`;
- emit JSON that can be wrapped into this contract;
- support generated proof artifacts.

It does not own scene authority. It receives typed context from the planner and returns terrain materialization data.

### 4.4 Adapter authority

`godotnew/semantic/scripts/Boot.gd` is a scene-payload adapter and contract courier.

Responsibilities:

- receive scene server payloads;
- normalize them into runtime scene docs;
- call `TrixelEnvironmentPlanner.plan()`;
- pass the returned contract to `SemanticRenderer.gd`;
- log useful proof/debug information.

Long-term rule: `Boot.gd` must not be a competing terrain planner. Existing terrain fallback code in `Boot.gd` is transitional fallback authority only.

### 4.5 Renderer authority

`godotnew/semantic/scripts/SemanticRenderer.gd` is the contract consumer and Godot embodiment layer.

Responsibilities:

- validate minimum contract fields before rendering;
- read `terrain_grid` and optional render metadata;
- resolve roles through `TrixelRoleResolver.gd`;
- resolve terrain atlases and atlas metadata;
- instantiate terrain nodes;
- log missing atlas/role fallback behavior;
- never infer narrative terrain semantics from prose.

### 4.6 Role authority

`godotnew/semantic/trixel/TrixelRoleResolver.gd` is the role derivation authority for terrain cells.

Responsibilities:

- map terrain-neighbor topology to tile roles;
- remain deterministic for identical grids;
- avoid owning atlas policy or scene semantics.

### 4.7 Alias authority

`godotnew/semantic/primitive_vocabulary_bindings.json` is the terrain alias ABI.

Responsibilities:

- map semantic/generated terrain names into renderable atlas terrain names;
- preserve renderer compatibility;
- prevent scattered alias dictionaries across planner and renderer code.

Current observed alias examples:

```json
{
  "coarse_sediment_dark": "sand",
  "ash_plain": "rock",
  "fog_waste": "grass",
  "ash_plain_dark": "rock",
  "cracked_soil": "sand",
  "basalt": "rock",
  "scree": "rock",
  "wet_sand": "sand",
  "forest": "forest_edge"
}
```

---

## 5. Required contract fields

A v1 contract is a JSON-compatible dictionary. Godot may represent it as a `Dictionary`; Python may represent it as a `dict`.

Required top-level fields:

| Field | Type | Required | Owner | Meaning |
|---|---|---:|---|---|
| `contract_version` | string | yes | planner | Must be `trixel_embodiment.v1`. |
| `scene_id` | string | yes | adapter/planner | Scene identity from runtime scene doc. |
| `source` | string | yes | planner/backend | Source of terrain plan, e.g. `world_field`, `static_fallback`, `treaty_plan`, `generated_artifact`. |
| `resolved_via` | string | yes | planner/backend | Resolution path, e.g. `runtime_context`, `cached_file`, `boot_fallback`, `treaty_override`. |
| `semantic_input` | dictionary | yes | planner | Typed semantic terrain inputs used to generate the plan. |
| `map_size` | dictionary | yes | planner/backend | `x` and `y` dimensions of `terrain_grid`. |
| `terrain_grid` | array[array[string]] | yes | planner/backend | Renderable terrain cells before role resolution. |
| `terrain_aliases_applied` | dictionary | yes | planner/renderer | Alias substitutions known or applied for renderable terrain. Empty dictionary allowed. |
| `atlas_requirements` | dictionary | yes | planner/renderer | Terrain families expected by renderer, with atlas/meta paths where known. Empty dictionary allowed during transition. |
| `role_policy` | dictionary | yes | planner/renderer | Role resolver and fallback policy. |
| `prop_placements` | array | yes | planner | Optional props. Empty array allowed. |
| `landmark_nodes` | array | yes | planner | Optional landmarks/spawn/navigation anchors. Empty array allowed. |
| `render_manifest` | dictionary | yes | planner/backend | Optional material swaps, visual emitters, and render hints. Empty dictionary allowed. |
| `debug_trace` | dictionary | yes | planner | Determinism/provenance/debug details. |

Unknown extra fields are allowed in v1, but consumers must ignore unknown fields unless explicitly upgraded to use them.

---

## 6. Contract field definitions

### 6.1 `contract_version`

Must equal:

```text
trixel_embodiment.v1
```

Consumers may reject contracts with a different major version. During migration, consumers may warn and continue if `terrain_grid` exists.

### 6.2 `scene_id`

The scene id must come from the normalized scene doc, usually one of:

- `scene_id`
- `id`
- `@id`

If no scene id exists, the planner may use `unknown`, but must record this in `debug_trace.warnings`.

### 6.3 `source`

Allowed v1 values:

- `world_field` — generated through `terrain/trixel_world_adapter.py` or equivalent deterministic field backend;
- `static_fallback` — generated by deterministic fallback logic;
- `treaty_plan` — loaded from a structurally validated treaty terrain plan;
- `generated_artifact` — loaded from generated cache output;
- `manual_fixture` — intentionally hand-authored test fixture;
- `legacy_fallback` — older lane preserved temporarily.

### 6.4 `resolved_via`

Suggested v1 values:

- `runtime_context`
- `cached_file`
- `treaty_override`
- `boot_fallback`
- `static_default`
- `manual_test`

This field is for traceability. It must identify how the terrain plan was selected, not just what generated it.

### 6.5 `semantic_input`

Required shape:

```json
{
  "terrain_family": "coastal",
  "environment": "coastal",
  "region": "",
  "spatial_scale_hint": "medium",
  "atmospheric_profile": "default"
}
```

Rules:

- Use typed fields, not free-text scans, whenever typed fields exist.
- Free-text/prose scans are legacy fallback only and must be reported as fallback in `resolved_via` and `debug_trace`.
- Missing values must become deterministic defaults, not random behavior.

### 6.6 `map_size`

Required shape:

```json
{
  "x": 48,
  "y": 48
}
```

Rules:

- `x` must equal the width of every row in `terrain_grid`.
- `y` must equal the number of rows in `terrain_grid`.
- Ragged grids are invalid.

### 6.7 `terrain_grid`

Required shape:

```json
[
  ["deep_water", "deep_water", "shallow_water"],
  ["sand", "sand", "grass"]
]
```

Rules:

- The grid is row-major: `terrain_grid[y][x]`.
- Values should be renderable terrain keys after alias normalization when possible.
- If non-renderable semantic terrain appears, it must have a corresponding entry in `terrain_aliases_applied` or vocabulary bindings.
- The renderer must not read prose or scene semantics to reinterpret this grid.

### 6.8 `terrain_aliases_applied`

Required shape:

```json
{
  "coarse_sediment_dark": "sand",
  "ash_plain": "rock"
}
```

Rules:

- Empty dictionary is valid.
- The planner should include aliases it applied or expects the renderer vocabulary cache to apply.
- Renderer-side alias resolution is allowed during migration, but alias authority must remain centralized in `primitive_vocabulary_bindings.json`.

### 6.9 `atlas_requirements`

Required shape:

```json
{
  "sand": {
    "atlas": "res://trixel/trixelassets/sand/atlas.png",
    "meta": "res://trixel/trixelassets/sand/atlas_meta.json"
  }
}
```

Rules:

- Empty dictionary is valid during migration.
- If present, keys must be renderable terrain keys after alias resolution.
- The renderer may still discover atlases from its configured atlas root, but missing requirements should be logged.

Current observed atlas terrain keys:

- `cliff`
- `deep_water`
- `forest_edge`
- `grass`
- `pier`
- `rock`
- `sand`
- `shallow_water`
- `shoreline`

### 6.10 `role_policy`

Required shape:

```json
{
  "resolver": "TrixelRoleResolver.gd",
  "missing_role_fallback": "center",
  "missing_atlas_fallback": "skip_tile"
}
```

Rules:

- Role resolution must be deterministic for identical terrain grids.
- The v1 role resolver is `godotnew/semantic/trixel/TrixelRoleResolver.gd`.
- If a terrain atlas does not contain a resolved role, renderer must use `center` when available.
- If `center` is missing, renderer may use the first atlas tile or skip the tile, but must log a warning.
- Path roles are currently best supported by `pier` and `shoreline` atlases.

### 6.11 `prop_placements`

Required field; empty array is valid.

Suggested item shape:

```json
{
  "id": "landmark_0",
  "type": "landmark",
  "name": "Old Gate",
  "position": {"x": 8, "y": 0, "z": 8}
}
```

V1 terrain embodiment does not require prop rendering. Consumers may ignore this field.

### 6.12 `landmark_nodes`

Required field; empty array is valid.

Suggested item shape:

```json
{
  "id": "entry_point",
  "kind": "spawn",
  "direction": "south"
}
```

V1 terrain embodiment does not require navigation integration. Consumers may ignore this field.

### 6.13 `render_manifest`

Required shape:

```json
{
  "material_grid_swaps": {},
  "queued_visual_emitters": []
}
```

Rules:

- Empty dictionary is valid during migration.
- `material_grid_swaps` may map grid coordinates to terrain/material keys.
- `queued_visual_emitters` may describe fog/glow/particle hints, but renderers may ignore them in v1.
- Render manifest hints are not world authority.

### 6.14 `debug_trace`

Required shape:

```json
{
  "planner": "TrixelEnvironmentPlanner.plan",
  "terrain_backend": "terrain/trixel_world_adapter.py",
  "deterministic": true,
  "warnings": []
}
```

Rules:

- Must identify planner/backend path.
- Must record fallback behavior.
- Must record missing scene id, missing typed terrain, missing atlas, or alias fallback where known.
- Should include stable dimensions and profile selections when available.

---

## 7. Example contract

```json
{
  "contract_version": "trixel_embodiment.v1",
  "scene_id": "scene.proof.001",
  "source": "world_field",
  "resolved_via": "runtime_context",
  "semantic_input": {
    "terrain_family": "coastal",
    "environment": "coastal",
    "region": "",
    "spatial_scale_hint": "medium",
    "atmospheric_profile": "default"
  },
  "map_size": {"x": 48, "y": 48},
  "terrain_grid": [
    ["deep_water", "deep_water", "shallow_water"],
    ["sand", "sand", "grass"]
  ],
  "terrain_aliases_applied": {},
  "atlas_requirements": {
    "deep_water": {
      "atlas": "res://trixel/trixelassets/deep_water/atlas.png",
      "meta": "res://trixel/trixelassets/deep_water/atlas_meta.json"
    },
    "sand": {
      "atlas": "res://trixel/trixelassets/sand/atlas.png",
      "meta": "res://trixel/trixelassets/sand/atlas_meta.json"
    },
    "grass": {
      "atlas": "res://trixel/trixelassets/grass/atlas.png",
      "meta": "res://trixel/trixelassets/grass/atlas_meta.json"
    }
  },
  "role_policy": {
    "resolver": "TrixelRoleResolver.gd",
    "missing_role_fallback": "center",
    "missing_atlas_fallback": "skip_tile"
  },
  "prop_placements": [],
  "landmark_nodes": [],
  "render_manifest": {
    "material_grid_swaps": {},
    "queued_visual_emitters": []
  },
  "debug_trace": {
    "planner": "TrixelEnvironmentPlanner.plan",
    "terrain_backend": "terrain/trixel_world_adapter.py",
    "deterministic": true,
    "warnings": []
  }
}
```

---

## 8. Fallback policy

Fallbacks are allowed during migration, but they must be explicit.

### 8.1 General fallback rules

- A fallback may produce a contract.
- A fallback may consume a contract.
- A fallback may validate a contract.
- A fallback must not silently become primary authority.
- A fallback must set `source` and `resolved_via` accordingly.
- A fallback must add an entry to `debug_trace.warnings`.

### 8.2 Boot fallback

`Boot.gd` currently contains fallback terrain generation through:

- `REGION_CONFIG`
- `_resolve_region_config()`
- `_build_region_grid()`
- `_build_beach_grid()`
- `_build_environment_layout()`

This code is transitional fallback authority. It must not be expanded as the primary terrain planner.

During migration, if `Boot.gd` fallback generation is used, the output must be wrapped into this contract shape with:

```json
{
  "source": "legacy_fallback",
  "resolved_via": "boot_fallback"
}
```

### 8.3 Treaty/proof fallback

Scene-specific proof plans, such as `scene.proof.001`, must not be hard-coded as renderer behavior long-term.

During migration, a treaty/proof plan may be loaded if:

- the file exists;
- required structural keys are present;
- the result is wrapped in this contract;
- `source` is `treaty_plan` or `generated_artifact`;
- `resolved_via` is `treaty_override` or `cached_file`;
- debug trace records the path.

### 8.4 Static fallback

Static fallback grids are allowed only for deterministic proof and safe degraded rendering.

A static fallback must:

- avoid randomness;
- use valid renderable terrain keys;
- include dimensions;
- include fallback warning trace;
- be clearly marked `static_fallback`.

---

## 9. Determinism rules

For identical semantic input, contract producers must produce identical output unless the contract explicitly includes a deterministic seed and that seed changes.

Rules:

1. No hidden randomness.
2. No prose scanning when typed fields are available.
3. No clock/time dependence.
4. No environment-dependent atlas selection except configured path existence checks.
5. No mutation of canonical scene/runtime state.
6. No renderer-side terrain inference from narrative text.
7. Same `semantic_input` + same vocabulary bindings + same terrain backend version must produce the same `terrain_grid`.
8. Generated plans must be reproducible or identified as generated artifacts with provenance.

Suggested verification command for the current backend lane:

```bash
python3 terrain/trixel_world_adapter.py --demo --width 48 --height 48 \
  --context '{"terrain_profile":"coastal","environment_type":"coastal","region_type":"","atmospheric_profile":"default","world_state_id":"audit"}' \
  --scene-id audit | sha256sum
```

Run it twice. Hashes must match.

---

## 10. Renderer responsibilities

`SemanticRenderer.gd` should consume the contract and render terrain. It must not become scene/terrain semantic authority.

Required v1 behavior:

- accept a dictionary layout;
- require `terrain_grid` at minimum during migration;
- eventually require `contract_version == "trixel_embodiment.v1"`;
- render row-major grid cells;
- call `TrixelRoleResolver.resolve_role(grid, x, y, terrain)`;
- resolve terrain aliases through the centralized vocabulary binding layer;
- load atlas metadata from `res://trixel/trixelassets/<terrain>/atlas_meta.json`;
- load atlas texture from `res://trixel/trixelassets/<terrain>/atlas.png`;
- use `center` for missing roles when available;
- skip missing atlas terrains with a warning;
- set useful node metadata (`tile_id`, `gx`, `gy`, `terrain`, `role`);
- keep runtime tile updates deterministic.

Forbidden renderer behavior:

- scanning prose to choose terrain;
- mutating canonical scene state;
- silently inventing terrain aliases outside the vocabulary binding layer;
- becoming the source of `terrain_family` or `terrain_grid` except for editor preview fixtures.

---

## 11. Planner responsibilities

`TrixelEnvironmentPlanner.gd` should produce the contract.

Required v1 behavior:

- accept normalized runtime scene doc;
- resolve scene id deterministically;
- extract typed terrain fields;
- construct `semantic_input`;
- call `terrain/trixel_world_adapter.py` through structured context when using world-field backend;
- accept treaty/generated terrain plans only through structural validation;
- build prop and landmark arrays even if empty;
- attach map size;
- attach role policy;
- attach alias policy details;
- attach debug trace;
- return a complete contract.

Forbidden planner behavior:

- silently returning partial layouts without provenance;
- hiding scene-specific overrides outside debug trace;
- relying on absolute generated-artifact paths without warning;
- mutating narrative or runtime authority state.

---

## 12. Atlas and role policy

### 12.1 Atlas files

Renderable terrain keys resolve under:

```text
res://trixel/trixelassets/<terrain>/atlas.png
res://trixel/trixelassets/<terrain>/atlas_meta.json
```

Observed terrain atlas keys:

```text
cliff
deep_water
forest_edge
grass
pier
rock
sand
shallow_water
shoreline
```

### 12.2 Atlas metadata

`atlas_meta.json` must define:

- `tile_width`
- `tile_height`
- `columns`
- `rows`
- `tile_order`

`tile_order` maps role names to atlas rects by index.

### 12.3 Role fallback

If `TrixelRoleResolver.gd` emits a role not present in the atlas:

1. use `center` if present;
2. otherwise use `single` if present;
3. otherwise use first tile rect if safe;
4. otherwise skip the tile and log warning.

Current implementation uses `center` fallback. This is valid v1 behavior.

### 12.4 Role duplication

`TrixelAtlas.gd` currently contains sample/preview role-resolution logic that overlaps with `TrixelRoleResolver.gd`.

Long-term role authority belongs in `TrixelRoleResolver.gd`. Preview tools may duplicate behavior temporarily, but must be marked as preview/test logic if retained.

---

## 13. Generated artifact policy

Generated/cache/runtime directories are not canonical source by default.

Known generated terrain plans:

```text
.engain_cache/terrain_plans/scene.002_molten_descent_worldfield_plan.json
.engain_cache/terrain_plans/scene.proof.001_worldfield_plan.json
```

Policy:

- Do not hand-edit generated terrain plans unless the user explicitly asks for artifact surgery.
- Do not delete generated terrain plans casually.
- Treat generated terrain plans as proof artifacts or cache outputs.
- If a generated plan is loaded, record its path in `debug_trace`.
- If a generated plan influences rendering, wrap it into this contract shape.
- If generated output conflicts with source narrative or typed scene semantics, investigate the generator path before editing artifacts.

---

## 14. Migration steps

### Step 1: Establish documentation boundary

Create and maintain this document as the trixel embodiment ABI reference.

No code movement is required for this step.

### Step 2: Add contract fields to planner output

Update `TrixelEnvironmentPlanner.plan()` so every successful return includes:

- `contract_version`
- `source`
- `resolved_via`
- `semantic_input`
- `terrain_aliases_applied`
- `atlas_requirements`
- `role_policy`
- `render_manifest`
- `debug_trace`

Existing consumers may continue reading `terrain_grid`.

### Step 3: Pass the whole contract through Boot

Update `Boot.gd` so `_apply_environment_from_scene_doc()` can pass the complete planner result to `SemanticRenderer.set_environment_layout()`, not only `terrain_grid`.

During transition, keep `terrain_grid` copy for compatibility.

### Step 4: Make renderer validate contract shape

Update `SemanticRenderer.set_environment_layout()` to:

- accept legacy `{"terrain_grid": ...}` layouts;
- warn when `contract_version` is missing;
- validate map size against terrain grid;
- log `source`, `resolved_via`, and atlas requirements.

### Step 5: Move proof/treaty override into planner authority

Move `scene.proof.001` treaty plan selection out of direct Boot override behavior and into `TrixelEnvironmentPlanner.plan()` or a clearly named planner helper.

The returned contract must mark:

```json
{
  "source": "treaty_plan",
  "resolved_via": "treaty_override"
}
```

### Step 6: Demote Boot terrain fallback

Keep `Boot.gd` fallback generation only as legacy fallback, or move it behind planner authority.

Any fallback output must be wrapped in this contract.

### Step 7: Add regression checks

Add deterministic verification for:

- same structured context → same terrain hash;
- generated contract has required fields;
- grid dimensions match `map_size`;
- all terrain keys resolve directly or through alias bindings;
- all atlas requirements exist;
- missing roles fall back deterministically.

---

## 15. Verification checklist

Before claiming a trixel lane change is complete, verify:

### Contract shape

- [ ] `contract_version` is present and equals `trixel_embodiment.v1`.
- [ ] `scene_id` is present.
- [ ] `source` is present.
- [ ] `resolved_via` is present.
- [ ] `semantic_input` is present.
- [ ] `map_size.x` and `map_size.y` match `terrain_grid` dimensions.
- [ ] `terrain_grid` is rectangular.
- [ ] `terrain_aliases_applied` is present.
- [ ] `atlas_requirements` is present.
- [ ] `role_policy` is present.
- [ ] `prop_placements` is present, even if empty.
- [ ] `landmark_nodes` is present, even if empty.
- [ ] `render_manifest` is present.
- [ ] `debug_trace` is present.

### Determinism

- [ ] Same semantic input produces same terrain output hash.
- [ ] No hidden randomness is used.
- [ ] No current time/date is used in terrain generation.
- [ ] No renderer prose scan chooses terrain.
- [ ] Fallback usage is logged in `debug_trace`.

### Atlas and role resolution

- [ ] Every terrain key is either directly renderable or has an alias mapping.
- [ ] Required atlas metadata files exist for renderable terrain keys.
- [ ] Required atlas texture files exist for renderable terrain keys.
- [ ] Missing roles fall back to `center`, `single`, first tile, or logged skip.
- [ ] Path roles are only assumed for atlases that support them.

### Authority separation

- [ ] Runtime state remains authoritative outside rendering.
- [ ] Godot renderer consumes embodiment data; it does not own canonical state.
- [ ] `Boot.gd` adapts and passes contracts; it does not silently become terrain planner.
- [ ] Generated terrain plans are treated as artifacts unless explicitly promoted.
- [ ] Fallback lanes are marked fallback/legacy.

### Minimal live proof

- [ ] A known scene can load into a normalized runtime scene doc.
- [ ] Planner returns a trixel embodiment contract.
- [ ] Renderer receives the contract.
- [ ] Renderer spawns terrain nodes.
- [ ] Node count equals `map_size.x * map_size.y` minus explicitly skipped missing-atlas tiles.
- [ ] Debug logs identify source, resolution path, grid size, missing aliases, missing atlases, and fallback behavior.

---

## 16. Canonical rule

The next frontier is not more intelligence. It is incarnation.

EngAIn already has memory, semantic ingestion, runtime authority, governance, scene structure, persistence, ontology, and orchestration.

Trixel v1 embodiment must provide the missing formal boundary between semantic memory and playable visible world.

Therefore:

```text
No new trixel system should bypass this contract.
No old trixel system must be deleted immediately.
Every trixel system must be classified by its relationship to this contract.
```

That is the consolidation path.

---

## Appendix A. Editor/AI Tool Classification

This appendix classifies trixel editor, AI bridge, replay, and creative-memory tooling relative to the v1 embodiment contract.

These tools are valuable. They are not runtime embodiment authority.

The purpose of this appendix is to prevent editor workflows, AI collaboration, PixiEditor integration, or creative-memory systems from silently redefining the terrain embodiment ABI.

### A.1 One-line law

```text
No Trixel editor, AI bridge, or PixiEditor integration may mutate or redefine runtime embodiment directly. They may only produce editor artifacts, suggestions, overlays, or contract-compatible inputs that are validated before application.
```

This law applies to terminal editors, GUI editors, PixiEditor adapters, autonomous composer tools, bridge/orchestration tools, replay tools, and future creative AI integrations.

### A.2 Classification table

| Path | Classification | Allowed role | Forbidden role |
|---|---|---|---|
| `trixelcomposer/terminal_trixel.py` | Legacy/fallback creative editor | Produce editor canvas artifacts, editor replay traces, local creative sessions, and contract-referenced overlays. | Own runtime terrain, runtime snapshots, scene memory, atlas policy, role policy, or canonical embodiment. |
| `trixelcomposer/enhanced_trixel_core.py` | Legacy/fallback autonomous editor prototype | Explore creative cognition, canvas editing, local UI behavior, and non-authoritative visual drafts. | Own terrain generation, canonical replay, runtime memory, or direct embodiment mutation. |
| `trixelcomposer/empire_bridge.py` | AI suggestion bridge only | Request, receive, normalize, and persist AI suggestions as proposals. | Directly mutate runtime embodiment or treat AI output as accepted without validation. |
| `godotengain/engainos/tools/trixel/terminal_trixel.py` | Embedded/older terminal editor copy | Historical or tool-local terminal editing if explicitly invoked. | Become a second maintained embodiment path without classification and ABI compliance. |
| `mechanimation/trixel_composer/trixelcomposer-main/terminal_trixel.py` | Historical/duplicate terminal editor copy | Reference or archive comparison. | Silently supersede `trixelcomposer/terminal_trixel.py` or runtime embodiment lanes. |
| `mechanimation/trixel_composer/trixelcomposer-main/enhanced_trixel_core.py` | Historical/duplicate autonomous editor copy | Reference or archive comparison. | Become primary editor/runtime authority without explicit promotion. |
| `mechanimation/trixel_composer/trixelcomposer-main/empire_bridge.py` | Historical/duplicate AI bridge copy | Reference or archive comparison. | Become active AI mutation path without validation. |

If any classified tool becomes active production code, it must either produce, consume, validate, or explicitly wrap `trixel_embodiment.v1` contracts.

### A.3 Editor canvas authority

Editor canvas state is not runtime world state.

Editor canvas state may represent:

- a draft visual artifact;
- a human-authored or AI-assisted overlay;
- a tile/atlas sketch;
- a PixiEditor document;
- a preview surface;
- a replayable creative session.

Editor canvas state must not represent:

- `EngAInRuntime.snapshot`;
- canonical ZON memory;
- canonical scene state;
- AP-approved mutation history;
- authoritative terrain grid;
- authoritative role or atlas policy.

When an editor canvas is associated with runtime embodiment, it must reference the base contract instead of replacing it.

Suggested metadata:

```json
{
  "schema_version": "trixel_editor_artifact.v1",
  "base_contract_version": "trixel_embodiment.v1",
  "base_scene_id": "scene.proof.001",
  "base_contract_digest": "sha256:...",
  "artifact_role": "overlay|draft_asset|atlas_source|preview",
  "authoring_tool": "terminal_trixel|enhanced_trixel_core|pixieditor|empire_bridge"
}
```

### A.4 Memory ownership

Creative/editor memory is not EngAIn runtime memory.

The following are editor memory only:

- `.zw/memory.json`
- in-memory `AutonomousCreativeMemory` instances
- `EmpireBridge.creative_memory`
- creative phase histories
- tool preference histories
- style evolution notes
- AI collaboration notes

These may guide future editor suggestions, but they must not mutate or override:

- runtime snapshots;
- ZON memory;
- scene canonical state;
- AP authority state;
- trixel embodiment contracts;
- terrain aliases;
- atlas requirements.

If creative memory influences a proposed edit, the influence must be captured as proposal metadata, not hidden state.

Suggested proposal field:

```json
{
  "memory_influence": {
    "source": "editor_memory",
    "summary": "preferred brush based on prior editor session",
    "authoritative": false
  }
}
```

### A.5 Snapshot naming and ownership

The word `snapshot` is overloaded and dangerous.

`EngAInRuntime.snapshot` is runtime state authority.

`terminal_trixel.py` `SnapshotManager` snapshots are editor canvas snapshots only.

All editor-facing schemas should prefer these names:

- `editor_canvas_snapshot`
- `canvas_snapshot`
- `preview_snapshot`
- `artifact_snapshot`

They should avoid the unqualified name `snapshot` unless the surrounding schema explicitly distinguishes runtime snapshots from editor snapshots.

A valid editor snapshot reference should identify its base runtime or embodiment context when known:

```json
{
  "schema_version": "trixel_editor_snapshot.v1",
  "snapshot_kind": "editor_canvas_snapshot",
  "base_contract_version": "trixel_embodiment.v1",
  "base_scene_id": "scene.proof.001",
  "base_contract_digest": "sha256:...",
  "authoritative": false
}
```

### A.6 Replay ownership

Editor replay is not runtime replay.

The following are editor replay/session artifacts unless explicitly promoted through runtime/AP authority:

- `.zw/experience_log.jsonl`
- `.zw/experience.lmdb`
- `.zw/experience_counter.txt`
- `.zw/sessions/*.json`
- collaborative session JSON
- autonomous session JSON
- PixiEditor edit histories

A replay event may be useful for deterministic reproduction of an editor canvas, but it must not be treated as canonical world mutation.

Suggested replay envelope:

```json
{
  "schema_version": "trixel_editor_replay.v1",
  "base_contract_version": "trixel_embodiment.v1",
  "base_scene_id": "scene.proof.001",
  "base_contract_digest": "sha256:...",
  "deterministic_seed": 12345,
  "events": []
}
```

Replay events must be deterministic if they are used for verification. If they depend on external AI output, the exact AI response payload must be captured in the replay event.

### A.7 Action schema policy

Current observed action schemas diverge:

- `terminal_trixel.py` and `enhanced_trixel_core.py` use `CreativeAction.tool`.
- `empire_bridge.py` returns `ai_plan["action"]` for the tool name.

This divergence must not spread into PixiEditor or runtime embodiment.

Canonical editor action envelope:

```json
{
  "schema_version": "trixel_editor_action.v1",
  "tool": "brush",
  "x": 8,
  "y": 8,
  "color": [255, 255, 255],
  "pressure": 1.0,
  "reasoning": "AI suggestion",
  "source": "human|local_autonomy|empire_bridge|ollama|replay|pixieditor",
  "status": "proposed|accepted|rejected|applied",
  "base_contract_version": "trixel_embodiment.v1",
  "base_scene_id": "scene.proof.001",
  "base_contract_digest": "sha256:..."
}
```

Rules:

- Use `tool`, not `action`, for brush/tool identity.
- Use `status` to distinguish AI suggestion from applied edit.
- Include base contract reference when the edit is tied to runtime embodiment.
- Do not apply editor actions to runtime terrain without validation.

### A.8 AI suggestion lifecycle

AI output is suggestion, not mutation.

Required lifecycle:

1. AI proposes an edit or guidance message.
2. Bridge records the raw suggestion payload.
3. Bridge normalizes the suggestion into `trixel_editor_action.v1` or another explicit proposal schema.
4. Validator checks schema, bounds, color shape, base contract reference, and authority.
5. Human, local editor policy, or AP-authorized runtime path accepts or rejects it.
6. Only accepted actions may be applied to an editor canvas or promoted toward runtime input.
7. Applied actions are written to deterministic editor replay.

Forbidden lifecycle:

```text
AI response → direct runtime embodiment mutation
```

Also forbidden long-term:

```text
AI response → composer.act(...) without proposal validation
```

During migration, direct composer application may exist only as legacy editor behavior and must not be connected to runtime embodiment.

### A.9 PixiEditor integration boundary

PixiEditor integration must be classified before implementation.

Allowed PixiEditor roles:

- editor canvas surface;
- atlas/tile authoring tool;
- overlay authoring tool;
- preview renderer;
- human review surface;
- source of editor actions or asset drafts.

Forbidden PixiEditor roles unless explicitly promoted through a future contract:

- runtime snapshot owner;
- terrain planner;
- role resolver;
- atlas policy authority;
- AP bypass;
- hidden scene memory store;
- canonical replay authority;
- direct runtime mutation channel.

PixiEditor may produce files consumed by the embodiment lane, but those files must be classified as assets, overlays, editor artifacts, or contract-compatible inputs.

### A.10 Determinism rules for editor and AI tools

If editor or AI tools participate in verification, replay, or reproducible builds, they must record deterministic context.

Required when determinism matters:

- explicit seed;
- tool name;
- tool version or file digest when available;
- base contract digest;
- sorted/stable JSON serialization;
- full action event list;
- full external AI suggestion payloads;
- accepted/rejected/applied status;
- no hidden clock/time dependence in replayed outputs.

Wall-clock timestamps may be recorded as metadata, but replay must not require them to reproduce output.

Unseeded randomness is allowed only for non-authoritative live creative exploration and must be marked non-deterministic.

### A.11 Promotion rule

A classified editor/AI tool may be promoted only by an explicit migration step.

Promotion requires:

- documented target role;
- contract relationship: producer, consumer, validator, or legacy/fallback;
- deterministic serialization plan;
- memory ownership declaration;
- replay ownership declaration;
- validation boundary;
- proof that runtime authority remains outside the editor/AI tool.

No duplicate copy becomes primary because it is newer, more convenient, or imported first.

### A.12 Appendix verification checklist

Before integrating PixiEditor, EmpireBridge, terminal editor, or autonomous composer output with trixel embodiment, verify:

- [ ] The tool is classified in this appendix or a successor contract.
- [ ] It does not mutate runtime embodiment directly.
- [ ] It does not redefine `terrain_grid` without producing `trixel_embodiment.v1`.
- [ ] It does not own runtime snapshots.
- [ ] Its memory is marked editor/creative/non-authoritative.
- [ ] Its replay/session artifacts are marked editor replay/session artifacts.
- [ ] AI output remains proposal until validation and acceptance.
- [ ] Action schema uses `tool`, not bridge-local `action`, for tool identity.
- [ ] Deterministic replay records seed and full event payloads.
- [ ] Any contract-related output references `base_contract_version`, `base_scene_id`, and `base_contract_digest` when available.

This appendix is part of the v1 constitutional border. It may be superseded by a v2 editor contract, but it must not be bypassed silently.

