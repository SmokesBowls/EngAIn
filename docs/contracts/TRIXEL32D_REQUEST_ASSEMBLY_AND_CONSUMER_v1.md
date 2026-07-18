# TRIXEL32D REQUEST ASSEMBLY & CONSUMER REQUIREMENTS v1

Date: 2026-07-17. Sources:
- `~/Desktop/burdens_of_a_forgotten_past/trixel3.2d/TRIXEL_ENGAINOS_FINAL_HANDSHAKE.md`
  (trixel-side statement of what EngAInOS "needs his crew to tell him")
- `~/godotollama-task-performer-main/trixel_proof/worldfield_surface_builder.gd`
  (233-line Godot proof, mined as evidence — NOT adopted as the consumer)
- `docs/contracts/TRIXEL32D_SURFACE_REQUEST_CONTRACT_v1.md` (both packet shapes)

Direction (fixed 2026-07-16): EngAIn AUTHORS `trixel32d_surface_request` → trixel3.2d
BUILDS and returns `trixel32d_surface_built` → EngAIn/Godot materializes. The in-repo
gate (`tier1/engainos/gates/gate_trixel32d_handshake.py`) is pre-flight validation of
outgoing requests.

---

## 1. Request assembly — which crew member supplies each block

Per the final handshake, the request has five blocks. Proposed supplier mapping
(from the systems that actually own each truth today):

| Block | Fields | Supplier ("the crew") |
|---|---|---|
| Identity | contract/version, packet_type, request_id, source scene/surface identity, source provenance | EngAInOS mints request_id; scene identity + provenance from the vault/spatial-truth chain (scene ids, source_artifact_id / packet hashes — same pattern as cartographer's `source_packet_hash`) |
| Grid facts | width, height, one COMPLETE entry per cell (field_x, field_y, elevation, terrain/material/recipe or base visual intent) | WorldField owner (terrain lane heir / cartographer metric layout for elevations); per-cell visual intent references the trixel3.2d `recipes/` registry |
| Coordinate declaration | source coordinate space, Y-up target policy, field_x/field_y directions, explicit orientation vectors | Fixed doctrine — constants owned by the contract itself; EngAInOS stamps them, no subsystem improvises |
| Authorized metrics | cell width, cell depth, vertical measurement rule, height scale or max height layers | Cartographer (the metric authority: `unit = meter`, `world_cell_y_up`), post-concurrence — "authorized" means accepted metrics, not free parameters |
| Construction instruction | topology policy, gap-fill policy, deterministic ordering, appearance policy or recipe reference | EngAInOS policy + trixel recipe references |

Key upgrade over the v1 request contract: per-cell `base_color` generalizes to
**recipe/visual-intent reference**, and `height scale / vertical measurement rule`
becomes an explicit AUTHORIZED metric (the Godot proof had to invent `height_scale`
locally — that gap is now closed at the contract level).

## 2. Consumer requirements — derived from the worldfield proof

The proof did everything in Godot; sorting its operations tells us what the real
`surface_built` consumer may and may not do.

**Legitimate consumer verbs (parse → validate → materialize → apply → witness):**
- Load + parse the delivered packet; FAIL CLOSED on missing fields (no silent
  defaults — the proof's `data.get("width", 16)` pattern is forbidden)
- Build ArrayMesh from DELIVERED vertices/indices using the contract's
  `cell_geometry_ranges` (SurfaceTool commit = pure materialization)
- Apply DECLARED appearance (texture/recipe, declared filter policy)
- Apply the DECLARED local-to-scene transform
- Attach collision ONLY when explicitly authorized by EngAInOS
- Write a consume-report (counts vs. expected, `top_faces_point_up`-style checks —
  same shape as the Godot boot bridge report packet)

**Authority the proof smuggled into the renderer — must live upstream:**
- Geometry construction from elevations (that IS trixel3.2d's job)
- Axis-binding decision (request `orientation` owns it)
- height_scale application (cartographer-authorized metric)
- Elevation→color gradient + normalization (visual truth = trixel)
- Unilateral collision creation (EngAInOS must explicitly authorize collision;
  GodotSim may execute or refuse but cannot grant AP)
- Any silent default

Target size: the real consumer is ~40 lines of materialization + a report, not 233.

## 3. Application boundary resolved; execution still open

1. **World placement — contract resolved:**
   `TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md` requires an exact basis-column
   Trixel-local-to-declared-scene transform issued by EngAInOS.
2. **Collision declaration — contract resolved:** the same application packet
   requires explicit EngAInOS `DENIED` or `GRANTED`; GodotSim may later execute
   or refuse the exact declaration but may not grant AP or rewrite it.
3. **Transport — open:** HTTP / file-drop / library call remains undecided. The
   boot kernel ↔ Godot file-drop protocol is the only proven request→act→report
   loop in the ecosystem and is the natural template.
4. **Live application — open:** identity-complete built-response hardening, the
   application validator, runtime executor, live passive consumer, and execution
   receipt do not exist. No runtime wiring is authorized by these docs.
