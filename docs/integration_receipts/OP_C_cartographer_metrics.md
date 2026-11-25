# OP_C — Cartographer metric contributions

OPERATION_ID: OP_C
SYSTEM: Tier 2 Cartographer
SCRIPT_PATH: tier2/cartographer/layoutroom/topology_metric_layout_solver.py (C1); layoutroom/terrain_metric_solver.py + reckoningroom/terrain_metric_validator.py (C2, new)
FUNCTION: build_metric_layout(accepted_spatial_truth, measurement_basis=None); solve_terrain_metrics(grid_facts, measurement_basis); validate_terrain_metric_grant(grant, grid_facts)
INPUT_ARTIFACT: accepted_spatial_truth (OP_B); worldfield_grid_facts (OP_D) + declared physical measurement basis
OUTPUT_ARTIFACT: metric layout (now carries measurement_basis, metric_status, per-entity extent_source); engain.cartographer_terrain_metric_grant.v1 or a BLOCKED receipt

GATES:
  recovery_fixture_valid_proposal: TRUE (guard (0,0,0), king (1,0,0), stone gate (0,0,-2); gate PROPOSED)
  existing_24_checks_pass: TRUE
  declared_pgt_conversion_applied: TRUE (meters_per_pgt from a basis with basis_id + source)
  pgt_never_silently_meters: TRUE (no basis -> PGT numbers ignored, fallback 0.5 m half-extent, metric_status=provisional)
  missing_basis_refused_for_authorized_metrics: TRUE (terrain grant BLOCKED; provisional basis BLOCKED)
  physical_extent_and_grid_resolution_separate: TRUE (cell = physical_extent / cells; same 8 m field at 4 vs 40 columns -> 2.0 vs 0.2 m)
  non_square_grids: TRUE (4x2 over 8x6 m -> 2.0 x 3.0 m cells)
  missing_vertical_scale_refused: TRUE (and fractional vertical extent refused: Trixel int()s max_height_layers)
  metric_provenance_retained: TRUE (basis echoed; grant bound to sha256 of the exact grid facts; source_artifact_id is a content hash)
  coordinate_conversion_asymmetric_test: DEFERRED TO OP_E (needs a real assembled request + Trixel build)
  no_mirrored_or_rotated_placement: see OP_E
  no_unauthorized_construction_metrics: TRUE (grant only from basis_status=evidence)

C3 FINDING (coordinate spaces): Trixel's world-cell index space (trixel32d_worldfield_to_worldcell_projection) uses world_cell_z = +field_y; its built surface geometry uses field_y -> FORWARD = (0,0,-1). These are different spaces. The research mapping (pos.z <- world_y, TOPOLOGY_SOLVER_BRIEF) matches the index space. Cartographer's entity layout is anchored at the origin and has no declared binding to the field grid, so entity-on-terrain placement has no transform to apply yet; no axis was reversed.

FILES_CREATED: tier2/cartographer/layoutroom/terrain_metric_solver.py, tier2/cartographer/reckoningroom/terrain_metric_validator.py, tier2/cartographer/tests/{__init__.py,test_metric_contributions.py}
FILES_MODIFIED: tier2/cartographer/layoutroom/topology_metric_layout_solver.py, tier2/cartographer/artifactroom/metric_layout_artifact.py
TESTS_EXECUTED: tier2/cartographer/tests (8) + tier2/topologist/tests (5); tools/gameproof/run_gameproof_007.py before/after
TESTS_PASSED: 13 (+9 subtests); gameproof 007 PASSED before and after (positions identical; only new fields added; tracked proof outputs restored, not committed)
TESTS_FAILED: 0
PRE_EXISTING_FAILURES: none in scope
DEPENDENCY_BLOCKERS:
  - PRODUCTION BLOCKED: no scene, WorldField region or Mettaext output declares physical extents (physical_width_m, physical_depth_m, vertical_extent_m) or a PGT->meter basis. Real terrain grants return BLOCKED until a measurement basis with provenance is declared (architect decision).
  - Entity-to-terrain placement binding is undeclared (C3 finding).
  - The proposal gate's authority_note still names MrLore (retired); text left unchanged, no behaviour depends on it.
AUTHORITY_BOUNDARY: Cartographer computes metrics only from declared bases; never infers extents, never emits recipes/colors/meshes.
GIT_COMMIT: (this commit)
