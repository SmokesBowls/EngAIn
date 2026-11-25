# OP_H — Integrate the new Godot project (godotnew)

OPERATION_ID: OP_H
SYSTEM: godotnew (/mnt/data-drive/devvm-projects/engain-chapter-selector, SmokesBowls/godotnew)
SCRIPT_PATH: scripts/EngAInRuntimeLink.gd (new); main.gd, scene_view.gd (wired); trixel_proof/** (donor executor + consumer, byte-identical)
FUNCTION: activate_candidate(catalog_id) / activate_scene(scene, expected) -> present(load) -> report_observation() ; apply_authorization(authorization) -> LiveExecutor.apply_live
INPUT_ARTIFACT: live catalog + candidate (8765), runtime stamp (8080 peek), authorization handed over by the build caller
OUTPUT_ARTIFACT: applied SCENE_BOUND MeshInstance3D under Surfaces; godot.trixel32d_live_apply_report.v1 presentation receipt

PORTED BYTE-IDENTICAL (sha256 prefixes, equal to ~/Downloads/godotnew/semantic and godotollama copies; uids from the T01 archive):
  trixel32d_live_apply_executor.gd 8f08c704e270, trixel32d_apply_executor.gd afbac1946176, trixel32d_surface_consumer.gd 34db74ef1fcf
NOT COPIED: donor SimClient.load_scene_doc (no stamp, body-declared tier/mode — conflicts with T03-R3/OP_F).

GATES (tests/h01_runtime_link_check.py, real EngAIn handlers in-process, real Trixel, real Godot 4.6.1 headless; isolated test policy):
  live_chapter_catalog_displayed: TRUE (vault obsidianburdenNov25, 141 chapters; existing S03a selftest 5/5 covers the UI tree)
  actual_manuscript_chapter_selected: TRUE (book_01_book_of_genesis/003_first_contact.md)
  candidate_resolved_from_mettaext: TRUE
  candidate_inspection_does_not_mutate_runtime: TRUE
  authorized_activation_succeeds: TRUE (signed /scene/activate; unsigned refused 401)
  active_scene_identity_confirmed: TRUE (peek stamp == response stamp == Godot presented load == runtime)
  trixel_surface_build_completes: TRUE
  godot_consumes_delivered_surface: TRUE (one-time grant, apply_live APPLIED)
  geometry_counts_match_packet: TRUE
  declared_transform_applied: TRUE (90° about +Y, origin (1.5,0,-2))
  collision_denial_honored: TRUE (collision_applied DENIED_NONE; no physics nodes)
  stale_surface_consumption_refused: TRUE (authorization for load N presented after reload N+1: refused, nothing attached; old surface released)
  presentation_receipt_produced: TRUE
  frozen_donor_unchanged: TRUE (T01 MANIFEST.sha256 re-verified against live donors)
  existing_godotnew_checks: TRUE (T02 24 checks, S03a 5/5)

UI: "Activate in runtime (DRAFT)" button, enabled only while a candidate is displayed and an activator credential is configured; selection never activates. Applied surfaces live in a separate Surfaces node, never mixed with candidate capsules. Label stays CANDIDATE — not accepted.
FINDING FIXED IN THE CONSUMER: Godot's JSON yields float load_seq; EngAIn correctly refuses non-integer stamps. EngAInRuntimeLink.normalize_load restores {str,int,str}.

FILES_CREATED (godotnew): scripts/EngAInRuntimeLink.gd(+uid), tests/h01_runtime_link_check.{py,gd}, trixel_proof/** (3 scripts + uids)
FILES_MODIFIED (godotnew): main.gd, scene_view.gd
TESTS_EXECUTED / PASSED / FAILED: H01 22/22/0; T02 24/24/0; S03a 5/5/0
PRE_EXISTING_FAILURES: none in godotnew
DEPENDENCY_BLOCKERS:
  - Production credentials: no launch script provisions or delivers ENGAIN_ACTIVATOR_*/OBSERVER_*/EXECUTOR_* or the grant key to godotnew (start_stack.fish starts no Godot); production policies are deny-all.
  - No production channel hands a new authorization to Godot (no real build caller).
  - SURFACE_PARENT ("RUNTIME_CONTAINER","chapter-selector-surfaces") must be named by EngAIn scene declarations for a real scene.
AUTHORITY_BOUNDARY: Godot requests, presents and testifies; it never declares actor/tier/mode, never builds terrain, never grants collision.
GIT_COMMIT: godotnew 0f9eafc (local, not pushed)
