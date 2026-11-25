# OP_G — Live Trixel construction bridge

OPERATION_ID: OP_G
SYSTEM: Tier 1 EngAInOS (8765 /trixel32d/build|consume) -> external Trixel3.2D (subprocess drop)
SCRIPT_PATH: tier1/engainos/bridgeroom/trixel32d_live_route.py; tier1/engainos/authority/trixel32d_live_authority_state.py (scene_revision_of)
FUNCTION: _scene_truth_for(scene_id); _current_runtime(); _build() -> assemble_bound_surface_request
INPUT_ARTIFACT: signed build body (placement, collision, surface contributions); runtime /snapshot/peek
OUTPUT_ARTIFACT: Trixel built drop + intake receipt + one-time application authorization

CHANGES:
  - Fixed proof scene truth (TRIXEL32D_SCENE_TRUTH_V1.json, scene "scene-first-proof") removed from the production path. Declarations are now read per scene from tier1/engainos/authority/scene_truth/<scene_id>.json, must carry contract + scene_revision, and the revision must equal the active scene's revision (scene_revision_of, the same hash LiveAuthorityState stamps). Checked before any target is registered. Scene ids that could address other files are refused.
  - Build uses assemble_bound_surface_request (OP_E chain) and refuses provenance that does not name the active scene.
  - Proof declarations/grants remain only in tests.

GATES:
  real_scene_identity_accepted: TRUE (any scene id with a matching declaration; no fixed id)
  fixed_proof_scene_dependency_absent: TRUE (SCENE_TRUTH_PATH gone from the route; scene-first-proof finds no declaration)
  correct_target_declaration_resolved: TRUE (existing 75 route tests on the new contract)
  wrong_scene_rejected: TRUE (provenance for another scene 409; declaration for another scene/revision 409)
  stale_activation_rejected: TRUE (existing: reload/restart invalidates authorizations)
  occupied_slot_rejected: TRUE (existing slot_occupancy check)
  construction_request_signed_and_validated: TRUE (signed transport + bound assembly + handshake gate)
  trixel_receives_request: TRUE (real consumer subprocess in route tests)
  built_response_validated_against_request: TRUE (existing intake re-hash + validation)
  returned_bytes_and_hashes_verified: TRUE (existing)
  unauthorized_collision_refused: TRUE (collision.mode must be 'denied')
  no_stale_build_on_replacement_scene: TRUE (existing different-scene / restart tests)

FILES_CREATED: tier1/engainos/authority/scene_truth/README.md
FILES_MODIFIED: trixel32d_live_route.py, trixel32d_live_authority_state.py (helper extracted, behaviour identical), tests: test_trixel32d_live_route.py (+9 cases), test_trixel32d_live_godot_integration.py, test_trixel32d_semantic_integration.py (fixtures moved to the new declaration + bound-contribution contract; no assertion removed or weakened)
TESTS_EXECUTED: tier1/engainos/tests + tier2 (full)
TESTS_PASSED: 813 (+38 subtests); live-route 84/84; live Godot integration 2/2 (real Godot)
TESTS_FAILED: 4, all pre-existing (3 test_snapshot_ownership; test_trixel32d_semantic_integration — frozen donor sends no activation stamp, HANDSHAKES §1e, unchanged failure point)
PRE_EXISTING_FAILURES: as above
DEPENDENCY_BLOCKERS:
  - No scene declarations exist for real scenes (authority decision: which parent/slot a scene's terrain occupies).
  - Live client policy TRIXEL32D_LIVE_CLIENT_POLICY_V1.json still deny-all: no production build caller or presenter (architect: actor/tier for `build`).
  - Real grid facts and metric grants are BLOCKED upstream (OP_C, OP_D).
AUTHORITY_BOUNDARY: EngAInOS authorizes; Trixel only builds; nothing applies without the one-time grant.
GIT_COMMIT: (this commit)
