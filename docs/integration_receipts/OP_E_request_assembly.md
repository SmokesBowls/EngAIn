# OP_E — EngAInOS request assembly (+ OP_C C3 coordinate check)

OPERATION_ID: OP_E
SYSTEM: Tier 1 EngAInOS (bridgeroom)
SCRIPT_PATH: tier1/engainos/bridgeroom/trixel32d_request_assembler.py
FUNCTION: verify_contribution_chain(grid_facts, metric_grant, provenance) -> reasons; assemble_bound_surface_request(...) -> (status, request, reasons) (new); assemble_surface_request (unchanged)
INPUT_ARTIFACT: worldfield_grid_facts.v1 (OP_D), engain.cartographer_terrain_metric_grant.v1 (OP_C), provenance, construction_policy
OUTPUT_ARTIFACT: trixel32d_surface_request.v1

GATES:
  existing_assembler_tests_pass: TRUE (6/6, proof fixtures kept as isolated tests)
  real_worldfield_contribution_accepted: TRUE
  real_cartographer_contribution_accepted: TRUE
  scene_provenance_consistent: TRUE (grant.measurement_basis.scene_id == provenance.source_scene_id)
  mismatched_artifacts_rejected: TRUE (other scene, altered grid facts, altered grant, foreign metric id, missing contract)
  missing_metrics_rejected: TRUE
  missing_appearance_policy_rejected: TRUE
  unmapped_recipe_rejected: TRUE (existing)
  deterministic_request: TRUE
  existing_handshake_gate_passes: TRUE (134 tests in the 5 handshake-gate test modules)
  no_proof_constants_in_production_entry: TRUE (the bound entry rejects the proof METRIC_GRANT: no grant contract, no grid binding)
  C3_asymmetric_landmarks: TRUE — real Trixel build of an asymmetric 3x2 field: every top-face centroid == ((x-cx)*cw, round(e*layers), -(y-cy)*cd); east landmark at +X, row 1 forward at -Z. No mirror, no rotation, no axis reversed.

CHAIN CHECKS (hashes the providers already emit, no new identity scheme):
  grant.contract; grant.source_artifact_id == "terrain_metric." + sha256(grant minus id)[:16];
  grant.grid.grid_facts_sha256 == sha256(grid_facts); basis_status == evidence;
  basis.scene_id == provenance.source_scene_id; provenance.metric_layout_artifact_id == grant.source_artifact_id.

FILES_CREATED: tier1/engainos/tests/test_trixel32d_bound_assembly.py
FILES_MODIFIED: tier1/engainos/bridgeroom/trixel32d_request_assembler.py (append-only)
TESTS_EXECUTED: test_trixel32d_bound_assembly.py (9), test_trixel32d_request_assembler.py (6), handshake-gate modules (134 total incl. the 9)
TESTS_PASSED: all
TESTS_FAILED: 0
PRE_EXISTING_FAILURES: none in scope
DEPENDENCY_BLOCKERS:
  - The content-address on the grant proves it was not altered after Cartographer, not who produced it; production trust in the build caller comes from the signed transport + client policy (OP_F/OP_G), which is empty (deny-all).
  - topology_artifact_id is not hash-bound: the terrain surface does not consume topology, and the accepted_spatial_truth packet carries no scene id or hash to bind against.
  - The production terrain grant itself is BLOCKED (OP_C: no physical measurement basis) and real elevation is BLOCKED (OP_D).
AUTHORITY_BOUNDARY: EngAInOS joins and verifies; it computes no metrics, elevations or colors.
GIT_COMMIT: (this commit)
