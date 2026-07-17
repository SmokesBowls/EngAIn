# TIER2 PRODUCTION MAP — what each system produces for EngAInOS

Date: 2026-07-17. Method: file-level deep dive of `tier2/` (topologist 9 py files,
cartographer 9, engionality 25, godotsim 57), reading each system's artifact
classes, packet emissions, and machinery. Each system is documented separately
below with exactly what it produces. Synthesis at the end maps tier2's combined
output onto EngAInOS's needs (runtime-truth governance + the five
`trixel32d_surface_request` crew blocks of
`docs/contracts/TRIXEL32D_REQUEST_ASSEMBLY_AND_CONSUMER_v1.md`).

---

## Topologist — produces qualitative spatial truth

Role: interprets prose-derived signals into topology law. Doctrine (in code):
"Producer describes. Consumer interprets." Passroom never imports topologist.

**Produces exactly:**

1. **`ProseTopologyArtifact`** (`artifactroom/topology_artifact.py`) — the internal
   artifact class carrying entities and qualitative links, with lifecycle state
   and frame-of-reference.
2. **Passroom conversion** (`artifactroom/passroom_signal_converter.py`) — consumes
   mettaext `out_pass1_spatial_*.json` signal records and decides: which signals
   are valid topological actors, which link type applies (QSLINK / OLINK /
   MOVELINK), the entity set, and the artifact's lifecycle entry state. Unknown or
   ambiguous relations are skipped, never guessed.
3. **`accepted_spatial_truth` packets** (`reckoningroom/topology_validator.py`) —
   the validated output: `packet_type = accepted_spatial_truth`,
   `source_artifact_id`, `entities`, `qslinks`, `olinks`, `movelinks`. This is
   the packet cartographer and MrLore concurrence consume.
4. **Its own acceptance gate** (`gates/gate_accept_proposed_topology_artifact.py`)
   plus a classroom probe runner — the topologist polices its own proposals
   before they leave the system.

**Part of EngAInOS it produces:** the qualitative spatial-truth INPUT to canon
verification, and the head of the provenance chain (source_artifact_id begins
here).

---

## Cartographer — produces authorized metric truth

Role: concretizes accepted qualitative topology into one deterministic metric
proposal. Explicitly does NOT parse prose, validate topology, render art, create
Godot nodes, or mutate runtime (its own docstring).

**Produces exactly:**

1. **`MetricLayoutArtifact`** (`artifactroom/metric_layout_artifact.py`) — the
   engine-agnostic metric proposal contract: `MetricPosition {x, y, z}` (floats),
   `MetricLayoutEntity {entity_id, position, placement_source}`, lifecycle
   `DRAFT → PROPOSED → REJECTED` (frozen dataclasses — proposals are immutable).
2. **`engain.cartographer_metric_layout.v1` proposals**
   (`layoutroom/topology_metric_layout_solver.py`) — deterministic solving of
   `accepted_spatial_truth` into coordinates: anchor entity selection, axis
   distances, OLINK offsets (left/right/above/below), half-extents with declared
   defaults. Output fields per its contract doc: `artifact_id`,
   `source_artifact_id`, `source_packet_hash`, `lifecycle`,
   `coordinate_space = world_cell_y_up`, `unit = meter`, `axis_contract`,
   `anchor_entity_id`, `entities`, `applied_constraints`,
   `unresolved_constraints`.
3. **Provenance hashing** (`_canonical_hash`: sha256 over canonical JSON) — the
   source_packet_hash discipline that lets downstream authorities prove which
   exact input a proposal derived from.
4. **Proposal gate + validator** (`gates/gate_propose_metric_layout.py`,
   `reckoningroom/metric_layout_validator.py`).

**Part of EngAInOS it produces:** the metric-truth input to governance, and —
for the trixel seam — the **Authorized metrics** crew block directly (cell
metrics, unit, vertical rule authority), plus co-supply of **Identity/
provenance** (hashing) and the **Coordinate declaration** pattern
(`world_cell_y_up`, axis contract).

---

## GodotSim — produces the governed state, its evidence, and (today) hosts a piece of EngAInOS

Role: spatial/simulation execution authority. Four distinct product lines:

**Produces exactly:**

1. **The runtime state being governed** — nine deterministic kernels
   (`kernels/`): `spatial3d_mr` (SpatialWorld with bounds, snapshot-in/
   snapshot-out, bounds enforcement alerts), `combat3d_mr`, `inventory3d_mr`,
   `dialogue3d_mr`, `quest3d_mr`, `behavior3d_mr`, `perception_mr`,
   `navigation_mr`, `piece3d_mr` — plus `adapters/` exposing them and
   `runtime_core.py` holding the snapshot. This IS the "declared runtime truth"
   EngAInOS's admission decisions are about.
2. **Admission control (transplanted EngAInOS)** — `runtime_gateway.py`:
   governance logic checking (in order) global REPLAY mode, caller-claimed
   REPLAY, FINALIZED-vs-authority(<3), complex AP rules, then dispatch; records
   IntentShadow on every rejection. It imports
   `tier1.engainos.aproom.{reality_mode, canon.can_edit,
   authority_gate.ACTION_CLASSIFICATION, ap_complex_rules}` and
   `tier1.engainos.core.intent_shadow` — i.e., this is EngAInOS admission logic
   RESIDENT IN TIER2, currently the live governor on 8080 `/command`. The
   governance wiring gap is therefore a re-homing/delegation problem, not a
   build-from-scratch problem.
3. **Construction/presentation instructions** —
   `embodiment_contract_builder.py` emits `trixel_embodiment.v1`:
   `coordinate_authority` (source spatial3d_mr, bounds), `geometry_authority`
   (mode blender_mesh, mount_node, mesh_path), `materialization` (authority
   SemanticRenderer, `source: trixel_recipe`, `terrain_profile`,
   `recipe_texture_path`, assignment_rule). `builders/
   godot_scene_piece_builder.py` validates piece demands and writes Godot 4
   `.tscn` files with strict `BUILT / REJECTED / SUSPENDED` statuses — a working
   model of what the trixel `surface_built` consumer should be.
4. **Evidence** — thirteen proof gates (`gates/`): visible-floor, static-room,
   player-body, player-movement (+ visible-observer variant), trigger-zone
   light-off and multi-trigger routing, piece recipe packs 001/002, headless
   parse, piece3d baseline, ollama patcher tests. This is the witness layer
   acceptance leans on.

**Part of EngAInOS it produces:** the state to govern, the live admission gate
(to be reunited with `authority_gate.evaluate()`), the **Construction
instruction** crew block (prototyped in `trixel_embodiment.v1`), and the proof/
evidence system.

---

## Engionality — produces the enforcement substrate and expressive truth

Role: performance, timing, synchronization, expressive execution — and the
machinery that makes governance verdicts enforceable.

**Produces exactly:**

1. **Invertible mutation machinery** — `controlroom/zon4d_kernel.py`
   (SimpleZON4DKernel): the three-method contract required by
   `EnginalityRuntime._step6_apply_deltas()` and `_rollback()`, including
   `compute_inverse_delta(state, delta)`. `controlroom/runtime_loop.py` tracks
   `deltas_in → deltas_ordered → deltas_accepted / deltas_rejected →
   inverse_deltas` per tick and declares
   `preflight_delta(snapshot, delta, ms_budget) -> APVerdict`. This is the
   apply-or-revert mechanism that turns an EngAInOS accept/reject into applied
   state or a clean rollback — without it, governance verdicts are opinions.
2. **`engionality.affect_packet.v1`** (expressive/emotional truth) — gate rails
   complete (`gates/`: required fields, affect_state_valid, intensity_bounds,
   relationship_deltas_valid_if_present, scene_mood_valid_if_present,
   hard_rejects, no_lane_theft, no_legacy_imports) and consumed by
   `tier1/engainos/engainos_control_center.py` (source "engionality"). Live
   producer not yet wired — the rails exist, the train doesn't run yet.
3. **Task/plan structures** — `controlroom/task_system_merged.py`: TaskTree
   (planning) vs Task (execution) with semantic facades (Quest, Behavior,
   Sequence, Conversation, Maintenance, Routine) + `task_types.py`.
4. **Performance/presentation timing** — `showroom/`: `scene_track.py` (Tracks
   of ordered Clips with layering metadata), `animation_engine.py` (animation +
   facial tracks), `audio_engine.py`, `dialogue_engine.py` (Dialogue → Clip
   mapping), `performer_engine.py`, `domain_views.py` — the "expressive
   execution" instructions Godot presentation would consume.
5. **Bootstrap/harness** — `controlroom/bootstrap.py`,
   `performance_harness.py` (ms-budget discipline visible in preflight).

**Part of EngAInOS it produces:** the ENFORCEMENT ARM (invertible deltas +
AP-verdict preflight), plus expressive truth (affect packets) and presentation
timing.

---

## WorldField — produces per-cell world-surface truth (rehoused 2026-07-17)

Role: the terrain-lane heir (old doctrine name: `terrain_2ndlane_worldsurface_
management`). Rehoused from the pre-move repo's `terrain/` into `tier2/worldfield/`
after being orphaned by the tier move (zero references anywhere in tier1/2/3 before
rehousing; output artifacts survived in `.engain_cache/terrain_plans/`).

**Produces exactly:**

1. **The WorldField float authority** (`world_field_nucleus.py`) — sparse chunked
   2D float field (32×32 chunks, values 0.0–1.0 = normalized elevation), sculpted
   by four operators (add/subtract/smooth/clamp, radial falloff), with dirty-chunk
   tracking. `GodotWorldFieldBridge` emits dirty-chunk packets
   `{chunk_key, data: float[size²], size}`.
2. **Semantic classification** (`terrain_thresholds.py`) — deterministic
   float→terrain-string mapping via biome threshold profiles (coastal_beach,
   default_wasteland, volcanic, cosmic) plus `classify_biome(elevation, moisture,
   heat)`. EngAIn decides WHAT a cell is; trixel3.2d decides what it looks like.
3. **Terrain plan packets** (`trixel_world_adapter.py`) —
   `{terrain_grid: [[str]], terrain_palette, source: "world_field", profile,
   scene_id?, render_manifest?}`; consumes semantic scene contracts
   (`load_region_contract`: regions with bounds/topology/elevation_bias →
   field operators), resolves profiles deterministically from typed fields
   (`resolve_profile_dispatch` — no keyword heuristics), and fires
   `TerrainDelta(world_x, world_y, old_terrain, new_terrain)` events through
   registered AP threshold rules.

4. **`worldfield_grid_facts.v1` packets** (`grid_facts_emitter.py`, added
   2026-07-17) — the Grid-facts block itself: DENSE row-major per-cell records
   `{field_x, field_y, elevation, terrain, recipe}` joining WorldField elevation
   floats with adapter semantics. Recipe identities come from the declared
   `TERRAIN_TO_RECIPE` v1 table (all 9 referenced identities verified present in
   trixel3.2d's `recipes/terrain/`); unmapped terrain names emit `recipe: null`
   and are surfaced in `unmapped_terrains` — fail-visible, never guessed.

**Part of EngAInOS it produces:** the **Grid facts** crew block, now emitting in
final shape. WorldField is Trixel's input doorway without being part of Trixel:
`worldfield → worldfield_grid_facts → EngAInOS request assembly →
trixel32d_surface_request → Trixel 3.2d`. Remaining: trixel3.2d concurrence on the
recipe table's entries. The elevation→worldcell projection and all visual
semantics downstream are ALREADY owned by trixel3.2d
(`worldfield_to_worldcell_projection.v1`, gate-proven, + `recipes/terrain/`).

---

## Synthesis

**Against the five trixel32d request blocks** (who in tier2 supplies what):

| Block | Tier2 supplier | Status |
|---|---|---|
| Identity / provenance | topologist artifact ids + cartographer sha256 hashing | pattern exists |
| Grid facts (per-cell heightfield + visual intent) | **worldfield** (rehoused 2026-07-17): dense grid + per-cell visual intent today; needs the elevation-joining emitter + recipe-vocabulary reconciliation | rehoused, 2 upgrades |
| Coordinate declaration | cartographer (`world_cell_y_up`, axis contract) as the in-house pattern; doctrine constants stamped by EngAInOS | pattern exists |
| Authorized metrics | cartographer, directly | ready |
| Construction instruction | godotsim `embodiment_contract_builder` (`trixel_embodiment.v1` materialization block already references trixel recipes) | prototyped |

**Against EngAInOS as a whole**, tier2 produces:
- its **inputs** (topologist + cartographer proposals with provenance and
  lifecycle),
- its **enforcement arm** (engionality's invertible deltas + APVerdict
  preflight),
- its **evidence** (godotsim's 13 proof gates),
- and a resident piece of **EngAInOS itself** (godotsim `runtime_gateway`,
  already importing tier1 aproom modules) — the wire→inject→protect priority is
  a reunification, not a construction.

The structural gap identified in the first edition of this map (no producer of
the WorldField per-cell grid) was closed 2026-07-17 by rehousing the terrain
lane into `tier2/worldfield/`. The crew is now complete on paper; the remaining
work is the grid-facts emitter (join elevation floats with terrain strings),
recipe-vocabulary reconciliation with trixel3.2d, and the requester that
assembles all five blocks into a `trixel32d_surface_request`.
