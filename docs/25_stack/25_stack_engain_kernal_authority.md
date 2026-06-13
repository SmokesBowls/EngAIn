## 1. PROJECT ROLE

**Project:** `engain` shared core facade package.

`engain` owns the **public shared facade layer** for kernel, world, render, runtime, and semantic contracts. Its role is to give neighboring projects one canonical import surface instead of making every project import directly from `godotsim`, `terrain`, `trixelcomposer`, `mettaext`, or Godot scripts. The package root exposes only the namespaces `kernels`, `semantic`, `render`, `world`, and `runtime`, which makes it a facade boundary rather than a full runtime engine. 

It owns these shared surfaces:

`engain.kernels.perception`, `engain.kernels.spatial`, and `engain.kernels.navigation` as facade exports over legacy `godotsim` implementations.   

`engain.world.coordinates`, `engain.world.chunks`, `engain.world.field`, `engain.world.world_field_adapter`, and `engain.world.topology_stub` as world/grid/chunk/topology normalization surfaces.     

`engain.render.transforms`, `engain.render.packet_io`, and `engain.render.trixel` as engine-agnostic render/placement packet boundaries.   

It explicitly **does not own the legacy implementations yet**. Many files say “Public facade. Do not place implementation here yet,” and point back to `godotsim`, `terrain`, `trixelcomposer`, `mettaext`, or `godotnew/semantic/scripts/SemanticRenderer.gd`.   

Neighboring projects depending on it should be:

`terrain`, because `engain.world.field`, `engain.world.coordinates`, and `engain.world.chunks` duplicate or wrap world-field coordinate behavior.  

`godotsim`, because spatial, perception, navigation, runtime, and extraction facades still point there.     

`trixelcomposer`, because trixel address and atlas composition are still re-exported from it. 

`godotnew/semantic`, because `RenderTransformABI` says it is the engine-agnostic replacement boundary for behavior formerly living in `SemanticRenderer.gd`. 

`mettaext`, because semantic extraction currently re-exports helper behavior from `mettaext.semantic_environment_extractor`. 

---

## 2. CURRENT WORKING STATUS

**Confirmed working, from the files:**

The package has a clean root facade namespace: `kernels`, `semantic`, `render`, `world`, and `runtime`. 

The coordinate ABI is implemented as pure Python and side-effect free. It converts 2D grid plus elevation into a 3D world cell using `x <- grid_x`, `y <- elevation`, `z <- grid_y`. 

Chunk conversion is implemented. `local_to_world_xz()` and `world_to_chunk_local_xz()` define a concrete chunk/local/world coordinate conversion with validation that `chunk_size > 0`. 

World-field payload normalization is implemented for two shapes: direct `terrain_grid` payloads and single-chunk `chunks` payloads. It validates rectangular grids and elevation shape. 

Placement packet emission is implemented from terrain grid plus elevations into deterministic packet lists. It validates rectangular grid shape, builds coordinate ABI, builds chunk coordinate, builds render transform, and sorts packets deterministically. 

Render packet IO is implemented. It writes deterministic JSON with UTF-8, indentation, sorted keys, and trailing newline; it reads packet lists and validates required packet keys. 

The runtime facade correctly refuses to import `godotsim.sim_runtime` because that legacy entrypoint can start runtime/server side effects. This is a good safety boundary. 

**Partially working:**

Kernel facades are partial. `perception`, `spatial`, and `navigation` try to import legacy `godotsim` modules, but if imports fail they only define error functions, not full replacement implementations.   

The trixel facade is partial. It imports `trixelcomposer.tile_address`, while heavier atlas functions are optional and silently skipped if imports fail. 

Semantic extraction is partial. It re-exports from `godotsim.scene_extractor` and `mettaext.semantic_environment_extractor` only if those imports succeed. 

World field facade is partial. It imports from `terrain.world_field_nucleus`, `terrain.terrain_thresholds`, and optionally `terrain.trixel_world_adapter`, but the actual authority remains in `terrain`. 

**Untested or not proven by the files:**

No uploaded file proves that Godot consumes the emitted `PlacementPacket` JSON correctly.

No uploaded file proves that `trixelmap`, `engainos`, or Godot currently use this facade instead of their old local coordinate/render logic.

No uploaded file proves multi-chunk world-field normalization. In fact, the isolated adapter explicitly rejects multiple chunks. 

No uploaded file proves that `topology_stub` feeds a real terrain generator. It is explicitly called a stub. 

**Abandoned, legacy, or proof-only:**

The implementation authority is still mostly legacy. The package repeatedly points to old sources: `godotsim/*.py`, `terrain/*.py`, `trixelcomposer/*.py`, `mettaext/*.py`, and `godotnew/semantic/scripts/SemanticRenderer.gd`.    

`topology_stub` is proof-only. It produces deterministic coastal/highland/cosmic terrain grids, elevations, and chunk metadata, but it is not a real topology/world generator yet. 

---

## 3. ERROR PROFILE

**Import/path errors**

High risk. The facade imports from legacy packages that may not be on `PYTHONPATH`: `godotsim.perception_mr`, `godotsim.spatial3d_mr`, `godotsim.navigation_mr`, `terrain.world_field_nucleus`, `trixelcomposer.tile_address`, and `mettaext.semantic_environment_extractor`.      

Most likely failure:

```text
ModuleNotFoundError: No module named 'godotsim'
ModuleNotFoundError: No module named 'terrain'
ModuleNotFoundError: No module named 'trixelcomposer'
```

**Missing files**

Risk is high because the facade assumes legacy modules exist. If `godotsim/perception_mr.py`, `godotsim/spatial3d_mr.py`, or `godotsim/navigation_mr.py` are missing, facade import fallback only creates error helpers, not a working implementation.   

**Duplicate files**

Likely. The package intentionally duplicates public contract names already implied by `terrain`, `godotsim`, `trixelcomposer`, and `godotnew/semantic`. This is not bad yet, but it means there may be two truths until imports are reversed.

Duplicate coordinate/field/packet logic found:

`CoordinateABI` in `engain.world.coordinates` overlaps with `terrain/world_field_nucleus.py` and `trixelcomposer/tile_address.py`, because the facade says legacy source remains there. 

`ChunkCoordinate` overlaps with `terrain/world_field_nucleus.py`. 

`RenderTransformABI` overlaps with `godotnew/semantic/scripts/SemanticRenderer.gd`. 

`PlacementPacket` and packet JSON IO overlap with renderer adapters.  

**Stale backups**

Not directly proven by these files. The bigger risk is not `.bak` files; it is stale legacy modules still acting as truth while `engain` claims the public facade.

**Schema mismatch**

Very high risk around coordinates. `CoordinateABI` stores `grid_xy`, `elevation`, `view_address_hint`, and `world_cell_3d`, but `validate_coordinate_record()` expects a different envelope with `schema_version`, `authority_level`, `authoritative`, `artifact_kind`, `position`, and `chunk`. 

That means there are at least two coordinate shapes:

```text
Internal facade object:
CoordinateABI(grid_xy, elevation, view_address_hint, world_cell_3d)

External coordinate record:
schema_version, authority_level, authoritative, artifact_kind, position, chunk
```

This must be reconciled before deeper authority.

**Runtime bridge mismatch**

Medium to high. `engain.runtime.sim` intentionally does not import `godotsim.sim_runtime`, which is correct for safety, but it also means the facade does not yet provide a callable runtime client or bridge. 

Likely mismatch:

```text
Neighbor project expects engain.runtime.sim to start or expose runtime API.
Actual behavior: it only exposes LEGACY_ENTRYPOINT, RUNTIME_API_PORT, and not_imported_reason().
```

**Godot scene/autoload mismatch**

Not directly owned by this package. However, `RenderTransformABI` says the legacy source remains in `godotnew/semantic/scripts/SemanticRenderer.gd`, so Godot may still expect a different transform structure than the Python packet emits. 

Most likely mismatch:

```text
Python packet render.position = [x, y, z]
Godot renderer expects transform.origin, position Vector3, tile_address, node_path, or another legacy field.
```

**Generated-output drift**

High risk. `write_packets_json()` enforces deterministic JSON shape with required keys: `tile_id`, `grid`, `chunk`, `world`, and `render`. 

But `PlacementPacket.to_dict()` nests `render.position`, `render.rotation`, `render.scale`, and `render.visible_face`.  If any renderer expects flat fields like `world_x`, `world_y`, `world_z`, or `tile_type`, generated packets will drift.

**Old architecture still present**

Confirmed. Almost every facade file says implementation remains elsewhere. This package is a shared facade, not yet the source-of-truth engine.    

---

## 4. CONTRADICTION PROFILE

**Contradiction with own stated role**

The package claims public facade authority, but many modules still import implementation from legacy projects. That means `engain` is the intended import authority, not yet the implementation authority. 

**Contradiction with terrain**

`engain.world.coordinates` and `engain.world.chunks` define coordinate/chunk helpers, while comments say legacy source remains in `terrain/world_field_nucleus.py`.  

Human decision needed:

```text
Does terrain keep owning world math?
Or does engain.world become the canonical coordinate authority and terrain imports from engain?
```

**Contradiction with godotsim**

Kernel facades point to `godotsim`, but the package name suggests shared core authority.   

Human decision needed:

```text
Do godotsim kernels move into engain.kernels?
Or does engain.kernels remain a compatibility import layer forever?
```

**Contradiction with trixelcomposer / trixelmap**

`engain.render.trixel` points to `trixelcomposer/tile_address.py` and `trixelcomposer/atlas_composer.py`. 

If `trixelmap` also has tile address or render packet logic, then there are probably three competing layers:

```text
trixelcomposer = tile/atlas implementation
trixelmap = map/render consumer or generator
engain.render.trixel = intended shared facade
```

The uploaded files prove the `trixelcomposer` overlap, but they do not directly prove the `trixelmap` implementation shape.

**Contradiction with engainos**

Not directly proven from these files. The likely contradiction is architectural: `engainos` may expose runtime/API outputs while `engain` exposes shared pure-Python contracts. The uploaded files do not show whether `engainos` imports these facades.

**File naming contradiction**

There are multiple `__init__.py` files with only facade language and no implementation. That is good for namespace safety, but weak for authority.     

**Schema name contradiction**

`validate_coordinate_record()` expects `schema_version: trixel_coordinate_abi.v1`, but the internal class is named `CoordinateABI`, not `TrixelCoordinateABI`. 

This is a naming conflict:

```text
CoordinateABI = internal terrain/world coordinate object
trixel_coordinate_abi.v1 = external schema envelope
```

**Old vs new pipeline behavior**

Old behavior: Godot/terrain/trixel/godotsim own their local logic.

New intended behavior: `engain` becomes the shared facade and stable contract point.

Current reality: mixed. Some contracts are implemented in `engain`, but many imports still depend on old modules.   

---

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

**Name:** EngAIn Shared Core Contract Facade.

**What it wants to become:**
A single package where terrain, semantic extraction, placement, render packet IO, spatial kernels, perception kernels, navigation kernels, and runtime bridge outputs all agree on one stable set of contracts.

**Files implying it:**

`engain/__init__.py` defines the facade namespace. 

`engain.world.coordinates` defines canonical coordinate conversion and coordinate validation. 

`engain.world.chunks` defines chunk/local/world conversion. 

`engain.world.world_field_adapter` normalizes terrain/chunk payloads into placement-emitter input. 

`engain.world.placement_emitter` turns terrain grid truth into placement packets. 

`engain.render.transforms` defines `RenderTransformABI` and `PlacementPacket`. 

`engain.render.packet_io` defines deterministic JSON packet IO. 

`engain.world.topology_stub` implies future topology/world-field generation but is still a stub. 

**What is missing before it becomes real:**

First, legacy import direction must reverse. Instead of `engain` importing `terrain`, `godotsim`, and `trixelcomposer`, those projects should import stable contracts from `engain`.

Second, `topology_stub` needs to become a real topology service or be renamed as test/demo only. It currently emits simple deterministic profile maps, not authored world truth. 

Third, the coordinate schema must be unified. `CoordinateABI` and `trixel_coordinate_abi.v1` are not the same shape yet. 

Fourth, placement emitter must accept richer placement requests. Right now it emits one packet per grid cell, but it does not include biome authority, entity placement, asset IDs, collision rules, material hints, LOD, layer, rotation policy, or renderer target. 

Fifth, render consumers must be tested against the packet IO contract: `tile_id`, `grid`, `chunk`, `world`, and `render`. 

---

## 6. INBOUND SCHEMA

### Inbound: semantic extraction input

**Source project:** `mettaext`, `godotsim`, possibly book/vault ingestion.

**Expected filename/schema name:** not fully declared in these files. Current facade points to `godotsim.scene_extractor` and `mettaext.semantic_environment_extractor`. 

**Required fields:** unknown from this stack. The facade does not define the semantic extraction input schema.

**Optional fields:** unknown.

**Failure behavior if missing:** current behavior is silent partial import failure. If imports fail, the facade simply does not expose those helpers. 

**Fix flag:** define `SEMANTIC_EXTRACTION_INPUT_v1` with at least:

```json
{
  "source_id": "string",
  "source_kind": "chapter|scene|manual|test",
  "text": "string",
  "metadata": {},
  "expected_output": "environment|scene|field|entities"
}
```

---

### Inbound: world field data

**Source project:** `terrain`, topology generator, or future world-field service.

**Expected filename/schema name:** candidate `WORLD_FIELD_PAYLOAD_v1`.

**Required fields, direct shape:**

```json
{
  "terrain_grid": [["grass"]],
  "elevations": [[0.0]]
}
```

`terrain_grid` must be a non-empty rectangular list of rows. `elevations` must exist and match the terrain grid shape. 

**Optional fields, direct shape:**

```json
{
  "chunk_x": 0,
  "chunk_y": 0,
  "chunk_size": 48
}
```

Defaults are `chunk_x=0`, `chunk_y=0`, and `chunk_size=48`. 

**Required fields, single-chunk shape:**

```json
{
  "chunks": [
    {
      "terrain_grid": [["grass"]],
      "elevations": [[0.0]]
    }
  ]
}
```

Only one chunk is supported by the isolated adapter. Multiple chunks fail. 

**Optional fields, single-chunk shape:**

```json
{
  "chunks": [
    {
      "chunk_key": [0, 0],
      "chunk_size": 48
    }
  ],
  "chunk_x": 0,
  "chunk_y": 0,
  "chunk_size": 48
}
```

**Failure behavior if missing:** raises `ValueError` for missing `terrain_grid`, missing `elevations`, non-rectangular grids, elevation shape mismatch, invalid chunk key, or multiple chunks. 

---

### Inbound: placement requests

**Source project:** terrain, topology service, semantic placement planner, or human placement UI.

**Expected filename/schema name:** candidate `PLACEMENT_REQUEST_v1`.

**Current required fields:** not formally defined. The current emitter accepts function arguments:

```python
terrain_grid
elevations
chunk_x
chunk_y
chunk_size
tile_scale
```

It validates grid shape and elevation shape, then emits packets. 

**Required fields in practice:**

```json
{
  "terrain_grid": [["grass"]]
}
```

**Optional fields in practice:**

```json
{
  "elevations": [[0.0]],
  "chunk_x": 0,
  "chunk_y": 0,
  "chunk_size": 48,
  "tile_scale": 1.0
}
```

**Failure behavior if missing:** missing or invalid `terrain_grid` raises `ValueError`; bad `elevations` shape raises `ValueError`. 

**Contract gap:** no explicit request ID, actor ID, destination renderer, asset mapping, biome metadata, layer, rotation policy, collision policy, or authority source.

---

### Inbound: render/trixel packet data

**Source project:** `placement_emitter`, renderer adapter, trixel pipeline.

**Expected filename/schema name:** candidate `PLACEMENT_PACKET_LIST_v1`.

**Required fields per packet:**

```json
{
  "tile_id": "grass",
  "grid": {"x": 0, "y": 0},
  "chunk": {"x": 0, "y": 0},
  "world": {"x": 0.0, "y": 0.0, "z": 0.0},
  "render": {
    "position": [0.0, 0.0, 0.0],
    "rotation": [0.0, 0.0, 0.0],
    "scale": [1.0, 1.0, 1.0],
    "visible_face": "top"
  }
}
```

Required top-level keys are enforced by packet IO: `tile_id`, `grid`, `chunk`, `world`, and `render`. 

**Optional fields:** none currently accepted by validation, but extra keys are not rejected by `read_packets_json()` as long as required keys exist. 

**Failure behavior if missing:** `ValueError` for non-list root, non-object item, or missing required keys. 

---

## 7. OUTBOUND SCHEMA

### Outbound: shared coordinate types

**Destination project:** `terrain`, `trixelmap`, `trixelcomposer`, `godotsim`, `engainos`, Godot render bridge.

**Expected filename/schema name:** `CoordinateABI`, candidate `trixel_coordinate_abi.v1`.

**Required fields, object form:**

```python
CoordinateABI(
    grid_xy=(grid_x, grid_y),
    elevation=elevation,
    view_address_hint="...",
    world_cell_3d=(grid_x, elevation, grid_y)
)
```

**Optional fields:** `tile_address` is deprecated; `view_address_hint` replaces it. 

**Stability level:** candidate. The implementation exists, but the validator expects a different external envelope. 

---

### Outbound: chunk coordinate types

**Destination project:** terrain/world renderer/placement emitter.

**Expected filename/schema name:** `ChunkCoordinate`.

**Required fields:**

```python
ChunkCoordinate(
    chunk_key=(chunk_x, chunk_y),
    chunk_size=48,
    local_xz=(local_x, local_z),
    world_xz=(world_x, world_z)
)
```

**Optional fields:** none.

**Stability level:** stable candidate. The math is explicit and side-effect free. 

---

### Outbound: world field adapter behavior

**Destination project:** placement emitter and render packet generation.

**Expected filename/schema name:** candidate `WORLD_FIELD_PAYLOAD_NORMALIZED_v1`.

**Required fields after normalization:**

```json
{
  "terrain_grid": [["grass"]],
  "elevations": [[0.0]],
  "chunk_x": 0,
  "chunk_y": 0,
  "chunk_size": 48
}
```

**Optional fields:** none after normalization; defaults are filled during normalization. 

**Stability level:** candidate. It is useful but only supports direct payloads and single chunks.

---

### Outbound: placement packets

**Destination project:** Godot renderer, trixel renderer, atlas composer, visualizer, packet recorder.

**Expected filename/schema name:** `PlacementPacket`.

**Required fields:**

```python
PlacementPacket(
    tile_id="grass",
    grid={"x": 0, "y": 0},
    chunk={"x": 0, "y": 0},
    world={"x": 0.0, "y": 0.0, "z": 0.0},
    render=RenderTransformABI(...)
)
```

**Optional fields:** currently none formal.

**Stability level:** candidate. Packet shape is clear, but renderer adoption is not proven. 

---

### Outbound: render packet IO

**Destination project:** renderer adapters, test harnesses, generated-output diffs.

**Expected filename/schema name:** candidate `PLACEMENT_PACKET_LIST_v1.json`.

**Required root:** JSON list.

**Required item keys:** `tile_id`, `grid`, `chunk`, `world`, `render`. 

**Optional fields:** extra keys tolerated but not specified.

**Stability level:** stable candidate. IO behavior is deterministic and validation exists. 

---

### Outbound: kernel outputs for spatial/navigation/perception

**Destination project:** `godotsim`, `engainos`, Godot runtime bridge, agent runtime.

**Expected filename/schema name:** unknown.

**Required fields:** not defined in this stack.

**Optional fields:** unknown.

**Stability level:** legacy/unknown. The facades re-export legacy `godotsim` modules but do not define stable output schemas.   

---

## 8. AUTHORITY BOUNDARIES

`engain` must stop and ask `terrain` when the question is about authoritative terrain generation, terrain thresholds, biome rules, or real world-field nucleus behavior. The facade currently imports those from `terrain`; it does not own them yet. 

`engain` must stop and ask `godotsim` when the question is about actual runtime behavior, scene extraction internals, perception implementation, spatial implementation, or navigation implementation. Those remain legacy sources.     

`engain` must stop and ask `trixelcomposer` when the question is about atlas composition, tile address internals, or terrain type listing. 

`engain` must stop and ask Godot/Godot semantic renderer when the question is about actual rendered node placement, scene autoloads, mesh instantiation, or engine transform application. `engain.render.transforms` is engine-agnostic and explicitly does not call Godot. 

Other projects must stop and ask `engain` before changing these shared contracts:

```text
CoordinateABI
ChunkCoordinate
RenderTransformABI
PlacementPacket
PLACEMENT_PACKET_LIST JSON shape
world-field normalized payload shape
grid_y -> world_z mapping
elevation -> world_y mapping
```

Those are the parts this facade is clearly trying to stabilize.     

---

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Should `engain.world.coordinates` become the true coordinate authority, or should `terrain/world_field_nucleus.py` remain authority?

2. Should `CoordinateABI` and `trixel_coordinate_abi.v1` be merged into one schema, or should one be internal and one be external?

3. Is `grid_y -> world_z` now permanent law for all terrain/render projects? 

4. Should `chunk_y` be renamed to `chunk_z` for 3D consistency, or kept as 2D chunk grid naming?

5. Should placement packets include both `chunk: {"x","y"}` and external coordinate record fields like `chunk_x`, `chunk_y`, `chunk_z`, `local_x`, `local_y`, `local_z`?  

6. Should `topology_stub` be promoted into a real topology generator, or quarantined as test/demo only? 

7. What renderer is the first authority consumer of `PlacementPacket`: Godot, trixelmap, trixelcomposer, or engainos?

8. Should `engain.runtime.sim` grow a safe runtime client API, or remain a non-importing warning facade forever? 

9. Should semantic extraction output world-field data directly, or should it output scene/environment facts that another project converts into world field?

10. Should old projects import from `engain`, or should `engain` remain a compatibility wrapper around old projects?

---

## 10. STACK VERDICT

**Verdict: COMPACT_AUTHORITY**

`engain` is not abandoned, and it is not wrong-merge evidence. It has real, useful, pure-Python contract code for coordinates, chunks, world-field normalization, placement emission, render transforms, and packet IO.      

But it is not full `AUTHORITY_READY`, because the implementation authority is still split across `godotsim`, `terrain`, `trixelcomposer`, `mettaext`, and Godot semantic renderer scripts.     

The cleanest status card is:

```text
engain
Status: COMPACT_AUTHORITY
Role: shared core facade package for kernel/world/render/semantic/runtime contracts
Confirmed: coordinate ABI, chunk conversion, render transform ABI, placement packet shape, deterministic packet JSON IO, world-field payload normalization
Not confirmed: renderer consumption, Godot autoload integration, engainos adoption, trixelmap adoption, real topology generation, stable kernel output schemas
Main risk: old implementation authority still lives in neighboring projects
Human decision: reverse imports so terrain/godotsim/trixelcomposer consume engain contracts, or keep engain as compatibility facade only
```

The biggest fix flag is this:

```text
Do not let engain become a second implementation of terrain/godotsim/trixel logic.
Either make it the canonical shared contract package,
or clearly mark it as a facade-only compatibility layer.
```

Right now, it tastes like the **right shared core shell**. It just needs authority consolidation before deeper systems trust it.
