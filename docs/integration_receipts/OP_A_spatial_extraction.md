# OP_A — Restore the isolated spatial extraction pass

OPERATION_ID: OP_A
SYSTEM: Tier 3 Mettaext (Passroom)
SCRIPT_PATH: tier3/mettaext/passroom/pass1_spatial.py
FUNCTION: process_file(pass1_path: Path, output_path: Path) -> dict
INPUT_ARTIFACT: pipeline_work/out_pass1_<stem>.txt (real pass1_explicit output)
OUTPUT_ARTIFACT: pipeline_work/out_pass1_spatial_<stem>.json

GATES:
  historical_source_provenance: TRUE   (git blob c761741f… == 49be3a11:tier3/mettaext/passroom/pass1_spatial.py; sha256 6598cbc6…66bc)
  restored_explicit_pass_unchanged: TRUE (pass1_explicit.py and Pass 2-5 untouched)
  spatial_extractor_executes: TRUE
  spatial_json_contract_preserved: TRUE (keys source_pass1/signal_count/signals)
  recovery_fixture_reproduces_signals: TRUE (3 signals incl. the known bad object hint "before"; Topologist excludes it, OP_B)
  anchored_scene_regression: TRUE (5/5 Dec-2025 game_scenes byte-exact: 4 via full pipeline, 03_Fist_contact via Pass 5 on preserved Pass 4)
  no_runtime_mutation: TRUE (pure file-in/file-out)

FILES_CREATED: tier3/mettaext/passroom/pass1_spatial.py (byte-exact restore), tier3/mettaext/tests/test_pass1_spatial.py
FILES_MODIFIED: tier3/mettaext/narrative_to_game.py (one subprocess step after Pass 1; output feeds no later pass)
TESTS_EXECUTED: test_pass1_spatial.py (1); anchored regression (5 scenes)
TESTS_PASSED: 1 + 5
TESTS_FAILED: 0
PRE_EXISTING_FAILURES: tier3/mettaext/tests — 10 modules fail to collect at HEAD (import pipeline_runner / pass2_entity_filter removed by a0af1728; "not yet reconnected").
DEPENDENCY_BLOCKERS: none
AUTHORITY_BOUNDARY: extraction evidence only; no Topologist/Trixel/Godot/runtime calls.
RECOVERY_RECEIPTS: /tmp/engain-spatial-recovery copied to /mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/R00_spatial_recovery_workspace_2026-11-25/ (MANIFEST.sha256)
GIT_COMMIT: (this commit)
