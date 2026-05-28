# COORDINATE ABI v1

Status: Draft contract, constitutional stabilization target
Scope: Objective spatial truth, coordinate authority, chunk/occupancy/elevation ownership, and observer-relative view derivation boundaries
Parent embodiment contract: `docs/trixel/contracts/TRIXEL_EMBODIMENT_CONTRACT_v1.md`
Related composer contract: `docs/trixel/contracts/TRIXEL_COMPOSER_ABI_v1.md`
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`
Target path: `docs/trixel/contracts/COORDINATE_ABI_v1.md`

---

## 1. Purpose

The Coordinate ABI freezes the boundary between objective spatial truth and observer-relative perception inside the Trixel/EngAIn runtime stack.

This contract exists because coordinate behavior already exists across runtime, terrain, renderer, adapter, and perception systems, but those systems do not yet share a constitutional authority boundary.

The core distinction is:

```text
CoordinateABI = what exists
ViewAddressABI = what is seen
```

The Coordinate ABI defines the stable, replayable, non-observer-relative spatial state of an entity, tile, terrain cell, region, actor, prop, or spatial unit.

The ViewAddress ABI defines a derived perceptual address from the perspective of a specific observer, camera, renderer, AI eye, or viewport.

This contract prevents spatial authority drift where:

```text
renderer interpretation ≠ world truth
camera perception ≠ coordinate mutation
AI perception ≠ spatial authority
editor preview ≠ canonical location
```

The goal is not to invent a new coordinate system. The goal is to freeze ownership of coordinate truth so that physics, navigation, AI planning, replay, multiplayer, rendering, and dragon embodiment can consume spatial data without redefining it.

---

## 2. Non-goals

This contract does not:

- define final rendering style;
- define atlas tile selection;
- define material appearance;
- define terrain generation algorithms;
- replace the Trixel Embodiment Contract;
- replace AP governance;
- replace runtime mutation governance;
- make Godot authoritative over world state;
- make renderer-visible position canonical;
- make `tile_address.py` a spatial truth authority;
- make editor canvas coordinates canonical world coordinates;
- define multiplayer networking protocol details;
- require immediate code changes;
- require renaming, deleting, or moving existing files;
- require refactoring current runtime behavior before review.

This is a documentation-first constitutional boundary. Existing implementations may remain transitional until validators and adapters are created in later phases.

---

## 3. Spatial authority ownership

### 3.1 Coordinate authority

Coordinate authority belongs to the runtime/world authority layer that owns canonical spatial state.

Coordinate authority may be produced or updated only by systems explicitly authorized to mutate objective world state, such as:

- runtime scene authority;
- simulation state authority;
- terrain/world-field authority;
- AP-approved mutation systems;
- deterministic replay reconstruction;
- validated import/promotion pipelines.

Coordinate authority must not be claimed by:

- renderers;
- cameras;
- view adapters;
- editor previews;
- AI suggestions;
- composer sessions;
- atlas resolvers;
- role resolvers;
- screenshot/screen-space tools;
- observer-relative perception systems.

### 3.2 Current baseline systems

Current baseline coordinate-related systems include:

| System | Baseline role | Authority status |
|---|---|---|
| `world_field_nucleus.py` | Float substrate/world-field behavior | Spatial substrate authority candidate |
| `trixel_world_adapter.py` | Float-to-semantic terrain boundary | Adapter, not canonical owner |
| `terrain_thresholds.py` | Deterministic float-to-terrain semantic mapping | Semantic mapping layer |
| `TrixelEnvironmentPlanner.gd` | Embodiment planner boundary | Contract producer, not world truth owner |
| `SemanticRenderer.gd` | Godot materialization/render consumer | Consumer only |
| `tile_address.py` | View-relative/perceptual tile addressing | ViewAddress generator/consumer, not Coordinate authority |
| `TRIXEL_EMBODIMENT_CONTRACT_v1.md` | Materialization boundary | Downstream from CoordinateABI |

### 3.3 Authority statement

```text
Only CoordinateABI defines objective spatial truth.
ViewAddressABI may describe perception of that truth.
ViewAddressABI must NEVER redefine CoordinateABI.
```

---

## 4. Coordinate truth vs perception truth

### 4.1 Coordinate truth

Coordinate truth is observer-independent.

It answers:

```text
Where does this thing exist?
What spatial unit does it occupy?
What chunk owns its storage?
What elevation or layer does it inhabit?
What semantic occupancy does it impose?
Who or what owns this spatial unit?
```

Coordinate truth must remain stable across:

- camera angle changes;
- renderer changes;
- viewport changes;
- atlas substitutions;
- screen scaling;
- observer position;
- fog/occlusion/shader effects;
- AI perception modes;
- preview/editor display modes.

### 4.2 Perception truth

Perception truth is observer-relative.

It answers:

```text
Which face is visible from this observer?
Which side should be rendered?
Is the object occluded from this view?
Which normals are visible?
What compact view address should be used for lookup?
```

Perception truth may change every frame without implying any mutation to objective world state.

### 4.3 Canonical dependency direction

Allowed direction:

```text
CoordinateABI + ObserverContext
→ ViewAddressGenerator
→ ViewAddressABI
→ renderer / perception consumer
```

Forbidden direction:

```text
ViewAddressABI
→ CoordinateABI mutation
```

Forbidden shortcut:

```text
renderer-visible result
→ spatial truth
```

---

## 5. Required coordinate fields

A CoordinateABI v1 object is a JSON-compatible dictionary. Godot may represent it as a `Dictionary`; Python may represent it as a `dict`.

### 5.1 Required top-level envelope

```json
{
  "schema_version": "trixel_coordinate_abi.v1",
  "authority_level": "coordinate_truth",
  "authoritative": true,
  "artifact_kind": "coordinate_record",
  "source": "runtime|world_field|terrain_authority|ap_mutation|replay|validated_import|manual_fixture|unknown",
  "scene_id": "scene-id-or-null",
  "entity_id": "entity-or-cell-id",
  "coordinate_space": "world",
  "unit": "cell|tile|meter|trixel|voxel|unknown",
  "position": {},
  "chunk": {},
  "elevation": {},
  "semantic_occupancy": {},
  "spatial_ownership": {},
  "determinism": {},
  "debug_trace": {}
}
```

### 5.2 Required coordinate payload

```json
{
  "position": {
    "world_x": 0,
    "world_y": 0,
    "world_z": 0
  },
  "chunk": {
    "chunk_x": 0,
    "chunk_y": 0,
    "chunk_z": 0,
    "chunk_size": 32,
    "local_x": 0,
    "local_y": 0,
    "local_z": 0
  },
  "elevation": {
    "value": 0.0,
    "datum": "world_zero",
    "layer": "surface"
  },
  "semantic_occupancy": {
    "kind": "terrain|actor|prop|water|air|blocked|unknown",
    "terrain": "grass|null",
    "blocking": false,
    "walkable": true,
    "flyable": true,
    "swimmable": false
  },
  "spatial_ownership": {
    "owner_type": "runtime|terrain|actor|system|none",
    "owner_id": "string|null",
    "mutation_authority": "runtime|ap|terrain_authority|replay|none"
  }
}
```

### 5.3 Field meanings

| Field | Meaning |
|---|---|
| `world_x`, `world_y`, `world_z` | Objective world-space coordinate. This is not a screen coordinate. |
| `chunk_x`, `chunk_y`, `chunk_z` | Chunk address used for storage, culling, paging, and deterministic lookup. |
| `chunk_size` | Size of the chunk grid used to derive local coordinates. |
| `local_x`, `local_y`, `local_z` | Position inside the chunk. Derived from world coordinate and chunk size. |
| `elevation.value` | Height or vertical layer value relative to the declared datum. |
| `elevation.datum` | Reference baseline such as `world_zero`, `sea_level`, or another named datum. |
| `elevation.layer` | Semantic vertical layer such as `subsurface`, `surface`, `air`, `sky`, `void`. |
| `semantic_occupancy.kind` | What type of content occupies this coordinate. |
| `semantic_occupancy.blocking` | Whether this space blocks traversal or placement. |
| `semantic_occupancy.walkable` | Whether ground traversal may use this coordinate. |
| `semantic_occupancy.flyable` | Whether aerial traversal may pass through this coordinate. |
| `semantic_occupancy.swimmable` | Whether water traversal may use this coordinate. |
| `spatial_ownership.owner_type` | Class of system/entity that owns the spatial unit. |
| `spatial_ownership.owner_id` | Specific owning entity/system identifier when applicable. |
| `spatial_ownership.mutation_authority` | System allowed to mutate this coordinate record. |

### 5.4 Required invariants

- `world_x/world_y/world_z` must not be derived from screen pixels.
- `chunk_x/chunk_y/chunk_z` must be derived deterministically from world coordinates and chunk size.
- `local_x/local_y/local_z` must be derived deterministically from world coordinates and chunk address.
- `semantic_occupancy` must not be inferred by renderer prose scanning.
- `spatial_ownership` must not be assigned by renderer visibility.
- A coordinate record must be valid without a camera.
- A coordinate record must be valid without a renderer.
- A coordinate record must be valid without a dragon observer.

---

## 6. Chunk authority

Chunk authority governs how world-space coordinates map to storage and update regions.

### 6.1 Chunk ownership

Chunks may own storage and dirty-state tracking, but chunks do not own semantic interpretation beyond the fields explicitly assigned to them by coordinate authority.

A chunk may answer:

```text
Which spatial cells are stored here?
Which cells are dirty?
Which local coordinates changed?
```

A chunk must not answer:

```text
Which face should render?
Which camera sees this cell?
Which atlas tile should appear?
Which narrative state is canon?
```

### 6.2 Chunk derivation rule

For a grid coordinate system, chunk addressing must be deterministic.

Suggested v1 derivation:

```text
chunk_x = floor(world_x / chunk_size)
chunk_y = floor(world_y / chunk_size)
chunk_z = floor(world_z / chunk_size)

local_x = world_x - (chunk_x * chunk_size)
local_y = world_y - (chunk_y * chunk_size)
local_z = world_z - (chunk_z * chunk_size)
```

If a subsystem uses a different derivation, it must declare that derivation in `debug_trace.coordinate_derivation` and must not silently interoperate as if it were the same grid.

### 6.3 Dirty chunks

Dirty chunks are update signals, not authority grants.

A dirty chunk may trigger:

- terrain adapter updates;
- renderer refresh;
- delta emission;
- replay event creation;
- validation checks.

A dirty chunk must not grant renderer, editor, or perception systems permission to mutate CoordinateABI.

---

## 7. Occupancy authority

Occupancy authority defines what spatial unit is occupied and how that occupation affects traversal, placement, physics, and AI reasoning.

### 7.1 Occupancy categories

Suggested v1 categories:

```text
terrain
actor
prop
water
air
blocked
portal
trigger
landmark
unknown
```

### 7.2 Occupancy rules

- Occupancy must be objective and observer-independent.
- A cell does not become occupied because it is visible.
- A cell does not become unoccupied because it is occluded.
- A renderer may hide an occupied cell, but it may not erase its occupancy.
- AI perception may fail to see occupancy, but AI failure to perceive does not remove occupancy.
- Editor preview may propose occupancy, but proposal is not occupancy authority.

### 7.3 Terrain occupancy

Terrain occupancy may include terrain identity, movement properties, and blocking information.

Example:

```json
{
  "kind": "terrain",
  "terrain": "rock",
  "blocking": true,
  "walkable": false,
  "flyable": true,
  "swimmable": false
}
```

Terrain occupancy may be consumed by pathfinding, physics, AP validation, dragon planning, and renderer materialization.

Terrain occupancy must not be reclassified by atlas lookup failure.

---

## 8. Elevation authority

Elevation authority defines vertical truth.

### 8.1 Elevation is coordinate truth

Elevation belongs to CoordinateABI when it affects:

- traversal;
- physics;
- terrain topology;
- line of sight;
- water/fog/air classification;
- actor placement;
- pathfinding cost;
- replay determinism.

### 8.2 Elevation is not render style

Visual height illusion, parallax, screen offset, shader displacement, bobbing, glow, and camera projection are not CoordinateABI elevation unless explicitly promoted by runtime authority.

Forbidden:

```text
screen_y offset → elevation mutation
sprite shadow → elevation mutation
parallax depth → world_z mutation
visible cliff face → changed coordinate height
```

Allowed:

```text
CoordinateABI.elevation → ViewAddressABI.visible_face
CoordinateABI.elevation → renderer side selection
CoordinateABI.elevation → navigation cost
CoordinateABI.elevation → line-of-sight calculation
```

### 8.3 Datum declaration

Every elevation value must declare a datum.

Suggested v1 values:

```text
world_zero
sea_level
terrain_base
chunk_origin
scene_local
unknown
```

If `datum` is `unknown`, consumers may render but must not use that value for authoritative pathfinding, replay, or physics without validation.

---

## 9. Observer prohibition rules

Observer systems may perceive CoordinateABI, but they may not redefine it.

### 9.1 Observer systems include

- cameras;
- Godot viewport;
- renderers;
- screen-space effects;
- AI perception pipelines;
- dragon visual perception;
- screenshot analyzers;
- editor preview panes;
- minimaps;
- debug overlays.

### 9.2 Prohibited observer mutations

Observer systems must not:

- change `world_x/world_y/world_z` because of camera angle;
- change `chunk_x/chunk_y/chunk_z` because of viewport culling;
- change `elevation` because of visible side selection;
- change `semantic_occupancy` because something is occluded;
- change `spatial_ownership` because something is selected on screen;
- treat screen coordinates as world coordinates without explicit conversion;
- treat projected coordinates as canonical coordinates;
- promote ViewAddressABI into CoordinateABI.

### 9.3 Selection and inspection

A renderer or editor may select, highlight, or inspect a coordinate record.

Selection creates a view/editor state, not a coordinate mutation.

Allowed:

```text
screen click → raycast/pick → CoordinateABI lookup → selected_coordinate_id
```

Forbidden:

```text
screen click → invented world coordinate → authoritative CoordinateABI write
```

---

## 10. ViewAddress generation rules

ViewAddressABI is a derived observer-relative envelope.

### 10.1 Required ViewAddress envelope

```json
{
  "schema_version": "trixel_view_address_abi.v1",
  "authority_level": "observer_relative",
  "authoritative": false,
  "artifact_kind": "view_address_record",
  "source": "view_address_generator|renderer|ai_eye|debug_view|unknown",
  "base_coordinate_digest": "sha256:...|null",
  "observer_id": "camera|dragon|viewport|ai_eye|unknown",
  "observer_context": {},
  "observer_direction": {"x": 0.0, "y": 0.0, "z": -1.0},
  "visible_face": "top|bottom|north|south|east|west|slope|wall|edge|underside|none|unknown",
  "normals": [],
  "occlusion": {
    "state": "visible|partial|occluded|unknown",
    "amount": 0.0
  },
  "render_side": "top_variant|east_wall_variant|underside_variant|none|unknown",
  "perspective_relative_address": "string|null",
  "debug_trace": {}
}
```

### 10.2 ViewAddress derivation

ViewAddressABI must be generated from:

```text
CoordinateABI + ObserverContext + view generation policy
```

It must not be generated from prose alone.

It must not be treated as valid if no base coordinate identity or derivation context exists, except for explicit debug/manual fixtures.

### 10.3 ViewAddress consumers

ViewAddressABI may be consumed by:

- renderer;
- asset resolver;
- atlas side selector;
- visibility systems;
- screen-space effects;
- observer-relative AI perception;
- dragon visual reasoning;
- debug overlays;
- screenshots/snapshots that declare themselves perceptual.

### 10.4 ViewAddress non-authority

ViewAddressABI must never be consumed as:

- physics truth;
- pathfinding truth;
- AP mutation authority;
- replay source of world position;
- multiplayer authoritative position;
- terrain occupancy source;
- elevation authority.

### 10.5 `tile_address.py` placement

`tile_address.py`, or any equivalent tile address generator, belongs on the ViewAddress side of the boundary unless it is explicitly refactored and governed as a CoordinateABI producer.

Default rule:

```text
tile_address.py consumes CoordinateABI.
tile_address.py emits ViewAddressABI or lookup keys.
tile_address.py does not define CoordinateABI.
```

---

## 11. Runtime mutation rules

CoordinateABI mutation is a world-authority action.

### 11.1 Allowed mutation sources

CoordinateABI may be mutated by:

- runtime authority;
- AP-approved mutation pipeline;
- deterministic terrain authority;
- validated scene import;
- deterministic replay reconstruction;
- explicitly marked manual fixtures in test mode.

### 11.2 Forbidden mutation sources

CoordinateABI must not be mutated directly by:

- renderer;
- Godot preview layer;
- atlas resolver;
- role resolver;
- AI suggestion;
- composer/editor canvas;
- ViewAddress generator;
- camera controller;
- dragon perception layer;
- screenshot analysis;
- cached visual artifact.

### 11.3 Mutation envelope

Any future CoordinateABI mutation event should preserve this shape or wrap into it:

```json
{
  "schema_version": "trixel_coordinate_mutation.v1",
  "authority_level": "coordinate_truth",
  "authoritative": true,
  "artifact_kind": "coordinate_mutation",
  "source": "runtime|ap|terrain_authority|replay|validated_import|manual_fixture",
  "status": "proposed|validated|accepted|applied|rejected|recorded",
  "mutation_id": "string",
  "scene_id": "scene-id",
  "target_coordinate_id": "string",
  "before_digest": "sha256:...|null",
  "after_digest": "sha256:...|null",
  "operation": "create|move|occupy|vacate|elevate|lower|transfer_ownership|delete",
  "reason": "string|null",
  "debug_trace": {}
}
```

### 11.4 Proposal does not equal mutation

AI, editor, composer, renderer, or dragon systems may propose coordinate changes.

Proposal is not mutation.

Required lifecycle:

```text
proposal
→ validation
→ authority acceptance
→ CoordinateABI mutation
→ replay event
→ downstream perception/render refresh
```

Forbidden shortcut:

```text
AI suggestion → CoordinateABI write
```

---

## 12. Replay determinism requirements

Replay systems depend on CoordinateABI, not ViewAddressABI.

### 12.1 Replay truth

Replay must reconstruct objective spatial state from:

- initial CoordinateABI records;
- deterministic mutation events;
- deterministic seeds;
- AP-approved state transitions;
- terrain authority events;
- actor movement events.

Replay must not reconstruct world truth from:

- screenshots;
- rendered frames;
- camera-visible faces;
- ViewAddressABI alone;
- editor previews;
- atlas output;
- debug overlays.

### 12.2 Determinism fields

CoordinateABI records should include a determinism block when persisted or emitted outside process memory:

```json
{
  "determinism": {
    "deterministic": true,
    "seed": 12345,
    "coordinate_digest": "sha256:...|null",
    "source_digest": "sha256:...|null",
    "generation_policy": "string|null"
  }
}
```

### 12.3 Replay invariant

For the same initial CoordinateABI state and the same accepted mutation event sequence, replay must produce the same CoordinateABI state.

Observer changes must not affect replay truth.

```text
same CoordinateABI + same mutations = same world truth
same CoordinateABI + different camera = different ViewAddressABI only
```

---

## 13. Dragon perception constraints

The dragon may perceive the world, reason about the world, and propose actions in the world. The dragon must not become coordinate authority merely by seeing.

### 13.1 Dragon coordinate reasoning

Dragon planning may consume CoordinateABI for:

- pathfinding;
- navigation;
- actor placement reasoning;
- spatial conflict detection;
- tactical planning;
- route selection;
- object proximity;
- world-state explanation.

### 13.2 Dragon visual perception

Dragon vision may consume ViewAddressABI for:

- visible face reasoning;
- occlusion awareness;
- line-of-sight explanation;
- screen/world alignment;
- “what am I looking at?” responses;
- render-aware debugging;
- visual scene narration.

### 13.3 Dragon prohibition

The dragon must not:

- treat visible position as canonical position;
- infer hidden world truth from rendered pixels without validation;
- mutate CoordinateABI directly from perception;
- treat screenshot state as runtime state;
- treat ViewAddressABI as replay truth;
- override AP mutation authority;
- bypass runtime authority with a movement or placement proposal.

### 13.4 Dragon eyes snapshot

A future dragon “eyes” snapshot should expose both layers separately:

```json
{
  "coordinate_records": [],
  "view_address_records": [],
  "observer_context": {},
  "snapshot_kind": "dragon_eyes_structural_snapshot",
  "authoritative_coordinate_state": true,
  "authoritative_view_state": false
}
```

Rules:

- Coordinate records describe what exists.
- View address records describe what the dragon sees.
- The snapshot must not merge the two into one ambiguous visual truth.

---

## 14. Fallback policy

Fallbacks are allowed during migration, but they must be explicit.

### 14.1 Coordinate fallback

A fallback coordinate record may exist only if it declares:

```json
{
  "source": "manual_fixture|legacy_fallback|validated_import|unknown",
  "debug_trace": {
    "fallback": true,
    "warnings": []
  }
}
```

Fallback coordinate records must not silently become primary authority.

### 14.2 View fallback

A fallback view address may be generated for rendering/debugging when coordinate detail is incomplete.

It must declare:

```json
{
  "authority_level": "observer_relative",
  "authoritative": false,
  "debug_trace": {
    "fallback": true,
    "reason": "missing coordinate detail|legacy renderer|manual fixture|unknown"
  }
}
```

### 14.3 Legacy renderer behavior

Legacy renderers may continue to infer side/face/render hints temporarily.

They must not write those inferences back into CoordinateABI.

### 14.4 Legacy coordinate ambiguity

If existing systems provide `x`, `y`, `z` without declaring whether they are world, local, screen, chunk, or view-relative, consumers must treat those coordinates as ambiguous until wrapped or validated.

Ambiguous coordinates may be used for preview/debug only.

They must not be used for authoritative replay, AP mutation, multiplayer sync, or dragon navigation.

---

## 15. Example coordinate envelope

### 15.1 CoordinateABI example

```json
{
  "schema_version": "trixel_coordinate_abi.v1",
  "authority_level": "coordinate_truth",
  "authoritative": true,
  "artifact_kind": "coordinate_record",
  "source": "world_field",
  "scene_id": "scene.proof.001",
  "entity_id": "terrain_cell_10_16_56",
  "coordinate_space": "world",
  "unit": "cell",
  "position": {
    "world_x": 10,
    "world_y": 16,
    "world_z": 56
  },
  "chunk": {
    "chunk_x": 0,
    "chunk_y": 0,
    "chunk_z": 1,
    "chunk_size": 32,
    "local_x": 10,
    "local_y": 16,
    "local_z": 24
  },
  "elevation": {
    "value": 0.82,
    "datum": "world_zero",
    "layer": "surface"
  },
  "semantic_occupancy": {
    "kind": "terrain",
    "terrain": "cliff",
    "blocking": true,
    "walkable": false,
    "flyable": true,
    "swimmable": false
  },
  "spatial_ownership": {
    "owner_type": "terrain",
    "owner_id": "world_field",
    "mutation_authority": "terrain_authority"
  },
  "determinism": {
    "deterministic": true,
    "seed": 12345,
    "coordinate_digest": "sha256:example-coordinate-digest",
    "source_digest": "sha256:example-source-digest",
    "generation_policy": "trixel_coordinate_abi.v1"
  },
  "debug_trace": {
    "coordinate_derivation": "world_to_chunk_floor_division",
    "created_by": "world_field_nucleus|adapter|manual_fixture",
    "warnings": []
  }
}
```

### 15.2 ViewAddressABI example derived from the same coordinate

```json
{
  "schema_version": "trixel_view_address_abi.v1",
  "authority_level": "observer_relative",
  "authoritative": false,
  "artifact_kind": "view_address_record",
  "source": "view_address_generator",
  "base_coordinate_digest": "sha256:example-coordinate-digest",
  "observer_id": "dragon_eye.primary",
  "observer_context": {
    "observer_world_x": 14,
    "observer_world_y": 16,
    "observer_world_z": 56,
    "projection": "world_to_view"
  },
  "observer_direction": {
    "x": -1.0,
    "y": 0.0,
    "z": 0.0
  },
  "visible_face": "east",
  "normals": [
    {"x": 1.0, "y": 0.0, "z": 0.0}
  ],
  "occlusion": {
    "state": "visible",
    "amount": 0.0
  },
  "render_side": "east_wall_variant",
  "perspective_relative_address": "w10.y16.z56.face.east.obs.dragon_eye.primary",
  "debug_trace": {
    "derived_from_coordinate": true,
    "warnings": []
  }
}
```

### 15.3 Required interpretation

The two envelopes describe the same spatial subject from different authority layers.

CoordinateABI says:

```text
The cliff cell exists at world position 10,16,56.
```

ViewAddressABI says:

```text
From this observer, the east face of that cliff cell is visible.
```

ViewAddressABI may change if the observer moves.

CoordinateABI must not change unless an authorized world mutation occurs.

---

## 16. Contract summary

The Coordinate ABI freezes the following constitutional rules:

```text
CoordinateABI owns objective spatial truth.
ViewAddressABI owns observer-relative perception.
Renderers consume perception; they do not define world truth.
AI perception may observe; it does not mutate coordinates.
Dragon vision must keep seen-state separate from exists-state.
Replay reconstructs CoordinateABI, not screenshots or ViewAddressABI.
ViewAddressABI must NEVER redefine CoordinateABI.
```

This contract is ready for Architecture Boundary Committee review.

