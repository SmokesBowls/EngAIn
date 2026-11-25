# OP_F — Scene activation and presentation authority boundaries

OPERATION_ID: OP_F
SYSTEM: Tier 2 GodotSim (8080) using Tier 1 signed transport
SCRIPT_PATH: tier2/godotsim/scene_activation_intake.py (new); http_handlers.py (_handle_scene_activate, shared _activate_scene_doc); sim_runtime.py (composition, F5 lock)
FUNCTION: POST /scene/activate  -> SceneActivationIntake.authenticate -> runtime_mode_permits_activation -> canon.can_edit -> _activate_scene_doc (SceneManager stamp)
INPUT_ARTIFACT: signed {scene, expected_scene_activation}
OUTPUT_ARTIFACT: scene_activation stamp {runtime_instance_id, load_seq, scene_id}

DESIGN:
  - Existing protocol, own route vocabulary {"activate"}, own policy file (tier1/engainos/authority/SCENE_ACTIVATION_CLIENT_POLICY_V1.json, deny-all), own credential dir runtime/engain_transport/8080_activation — the editor-route precedent. Flag ENGAIN_SCENE_ACTIVATION_AUTH=1; ENGAIN_SCENE_ACTIVATION_POLICY may point launch config at an isolated policy.
  - "activate" is route-only: load_client_policy refuses actor_id/tier on it. No operator registry; no actor tier assigned.
  - Body is exactly {scene, expected_scene_activation}; actor_id / actor_authority_tier / reality_mode in the body -> 400.
  - Runtime mode from aproom.reality_mode.get_context(): DRAFT permits; REPLAY refuses (preserved); FINALIZED/IMBUED/DREAM/TEST refuse — no contract defines activation there (fail closed).
  - A FINALIZED scene (canon.can_edit false) is refused with no tier override on this path.
  - Activation core is shared with /scene/load (one code path into SceneManager under activation_lock).
  - F5: sim_runtime._snap_wrapper holds SceneManager.activation_lock across copy + hydration + overlay. Lock order activation_lock -> _live_overrides_lock; no reverse holder exists (tick, /scene/load, SceneManager take only activation_lock; only the shim takes _live_overrides_lock).

GATES:
  unauthenticated_activation_refused: TRUE (unsigned 401, tampered body 401, unknown client refused, flag off 404, uncomposed 503)
  forged_actor_tier_grants_nothing: TRUE (400; activate role cannot carry a tier)
  client_mode_cannot_override_runtime_mode: TRUE (body mode refused; REPLAY/FINALIZED/IMBUED/DREAM runtime refuses)
  deny_by_default: TRUE (shipped policy is empty; composes nothing, writes no credentials)
  stale_activation_rejected: TRUE
  same_scene_reload_protected: TRUE (needs the current stamp; stamped reload = new load_seq)
  snapshot_consistent: TRUE
  concurrent_snapshot_test: TRUE (mutation-checked: fails 2/2 with the lock removed, passes 3/3 with it)
  no_combat_route_exposed: TRUE (no /command path added; activation only)
  no_ap_rules_invented: TRUE
  no_credentials_committed: TRUE (keys minted at startup, 0600, under runtime/)
  existing_transport_tests_pass: TRUE

FILES_CREATED: tier2/godotsim/scene_activation_intake.py, tier2/godotsim/test_scene_activation_auth.py, tier1/engainos/authority/SCENE_ACTIVATION_CLIENT_POLICY_V1.json
FILES_MODIFIED: tier2/godotsim/http_handlers.py, tier2/godotsim/sim_runtime.py
TESTS_EXECUTED: test_scene_activation_auth.py (12); tier2/godotsim (all); tier1/engainos/tests (all); test_local_signed_transport; test_editor_edit_authority
TESTS_PASSED: 194 (tier2/godotsim + transport + editor) ; 681 (tier1/engainos/tests)
TESTS_FAILED: 4, all pre-existing
PRE_EXISTING_FAILURES:
  - tier2/godotsim/test_snapshot_ownership.py x3 (fail at HEAD before T03)
  - tier1/engainos/tests/test_trixel32d_semantic_integration.py (frozen donor sends no activation stamp; HANDSHAKES §1e)
DEPENDENCY_BLOCKERS / DECISIONS:
  - Who holds the "activate" role in production (policy population) — architect.
  - Legacy unsigned POST /scene/load remains open and still reads body-declared tier/mode (D18). Not retired here (retirement not authorized). The new integration path does not use it.
  - Whether activation should ever be permitted in IMBUED/DREAM/TEST/FINALIZED runtime modes (currently refused).
AUTHORITY_BOUNDARY: transport identity != actor; activation is DRAFT runtime activation, not canonical acceptance.
GIT_COMMIT: (this commit)
