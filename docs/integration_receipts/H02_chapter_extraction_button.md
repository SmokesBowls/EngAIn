# H02 — Chapter Extraction Button

OPERATION_ID: H02
SYSTEM: Tier 1 EngAInOS (8765 scene_server) + godotnew main.gd
SCRIPT_PATH: tier1/engainos/bridgeroom/chapter_extraction_route.py (new); scene_server.py (_handle_chapter_extract, GET branch); godotnew main.gd
FUNCTION: POST /chapters/extract {"catalog_id"} -> ChapterExtractionJobs.start -> run_chapter_extraction.find_entry (resolver) + run_extraction (existing, worker thread); GET /chapters/extract?catalog_id= -> ChapterExtractionJobs.status
  godotnew: _on_extract_pressed, _start_allowed, _update_extract_button, _http_json
INPUT_ARTIFACT: catalog_id selected in the live catalog
OUTPUT_ARTIFACT: engain.chapter_extraction_receipt.v1 (Stageroom candidate, "not accepted")

ACCESS CONTROL: loopback clients only; Content-Type application/json only (no browser form posts); body exactly {"catalog_id"} (<=4 KiB); id resolved by the existing find_entry (active vault + live catalog) — paths refused 404 before anything runs. No runtime credential needed or accepted. One extraction per 8765 process at a time (409 busy); Godot also disables the button and blocks re-entry while running.
SIDE EFFECTS: writes only the extraction directory under Stageroom (existing run_extraction). No 8080, Trixel, activation or vault writes.

GATES:
  valid_chapter_selection: TRUE (book_01_book_of_genesis/001_the_ethereal_vigil.md, state not_extracted)
  extraction_request_delivered: TRUE
  existing_catalog_resolver_used: TRUE (receipt catalog_id / source_sha256 / vault_id = resolver entry)
  existing_mettaext_operation_executed: TRUE (driver tier3/mettaext/narrative_to_game.py, returncode 0)
  extraction_receipt_returned: TRUE (state finished, status candidate, contract engain.chapter_extraction_receipt.v1)
  candidate_preview_refreshed: TRUE (automatic GET /chapters/extraction -> state candidate, 1 scene rendered, label CANDIDATE — not accepted)
  duplicate_extraction_prevented: TRUE (Godot: button disabled + re-entry blocked; server: 409 busy, runner called once)
  manuscript_unchanged: TRUE (chapter mtime + sha256 and vault listing identical)
  runtime_state_unchanged: TRUE (isolated 8080: no activation before/after; peek identical)
  existing_regression_tests_passed: TRUE (818 passed; 4 failures all pre-existing)

TESTS: tier1/engainos/tests/test_chapter_extraction_route.py 5/5; godotnew tests/h02_extract_button_check.py 10/10 (real main.tscn, production-like single-threaded 8765, real vault read-only, temp Stageroom); godotnew H01 22/22, T02 24/24, S03a 5/5; EngAIn tier1+tier2 818 passed, 4 pre-existing failures (3 test_snapshot_ownership, semantic donor integration — HANDSHAKES §1e).
NOTE: jobs live in memory; an 8765 restart forgets job state (an interrupted run leaves an unfinished dir that run_extraction refuses to overwrite and reports).
GIT_COMMIT: EngAIn (this commit); godotnew see below
