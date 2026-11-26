# EngAIn — Current State

Last updated: 2026-11-25. Branch `main`. This file records facts; update it when they change.

## Repositories in play

| Repo | Path | Remote | HEAD at last update |
|---|---|---|---|
| EngAIn | `~/Desktop/burdens_of_a_forgotten_past/EngAIn` | `git@github.com:SmokesBowls/EngAIn.git` | see `git log -1`; all work pushed 2026-11-25 (through `5be0614a` + this record update) |
| godotnew (chapter selector) | `/mnt/data-drive/devvm-projects/engain-chapter-selector` | `SmokesBowls/godotnew` (origin is HTTPS without stored creds; push via `git@github.com:SmokesBowls/godotnew.git`) | `28d8c2a`, pushed |
| trixel3.2d | `~/Desktop/burdens_of_a_forgotten_past/trixel3.2d` | `git@github.com:SmokesBowls/trixel3.2d.git` | `7749c95` (continuity docs only; code unchanged since `dffe13a`), pushed |
| Frozen Godot donor | `~/Downloads/godotnew/semantic` (no git) | — | read-only; verified unchanged against `/mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/T01_round4_godot_bridge_2026-11-24/MANIFEST.sha256` |

## Services (managed by `start_stack.fish` / `stop_stack.fish`, logs in `.run/`)

| Port | Process | Entry |
|---|---|---|
| 8080 | GodotSim runtime | `python3 -u -m tier2.godotsim.sim_runtime` |
| 8765 | Stageroom / Tier 1 scene server + live Trixel route | `python3 -u tier1/engainos/launch_engine.py` |
| 8090 | EngAInOS facade | `python3 -m uvicorn tier1.engainos.engainos_server:app --host 127.0.0.1 --port 8090` |

`start_stack.fish` starts no Godot and delivers no client credentials.

## Pipeline as it exists (commit that made it so)

| Stage | Code | Commit |
|---|---|---|
| Catalog + extraction of one chapter (Mettaext Dec-2025 Pass 1–5, unchanged) | `tier1/engainos/tools/run_chapter_extraction.py`; 8765 `GET /chapters/catalog`, `GET /chapters/extraction`, `POST/GET /chapters/extract` | earlier; `f1822566` (extract endpoint) |
| Pass 1 spatial signals (restored, side output only) | `tier3/mettaext/passroom/pass1_spatial.py`, run by `narrative_to_game.py` | `eb3d77ce` |
| Topologist: signals → artifact → validator → acceptance gate; cited occupancy | `tier2/topologist/artifactroom/{passroom_signal_converter,occupancy_evidence}.py` | `f48e8d59` |
| Cartographer: entity layout (PGT→m basis), terrain metric grant | `tier2/cartographer/layoutroom/{topology_metric_layout_solver,terrain_metric_solver}.py` | `b42860c7`, `ca9c425c` |
| WorldField: declared elevation → nucleus → grid facts | `tier2/worldfield/trixel_world_adapter.py::field_from_elevation_grid`, `grid_facts_emitter.py` | `955f5b58` |
| Catalog candidate → runtime doc | 8765 `GET /load_scene?catalog_id=` (`StageroomSceneResolver.load_catalog_scene`) | `5cbbfc69` |
| Runtime activation (stamp-protected) | 8080 `POST /scene/load` (legacy, unsigned) and `POST /scene/activate` (signed, flag `ENGAIN_SCENE_ACTIVATION_AUTH=1`) | `ba243bac`, `1f340fbd` |
| Request assembly (bound to provider hashes) | `tier1/engainos/bridgeroom/trixel32d_request_assembler.py::assemble_bound_surface_request` | `b0a201cc` |
| Live Trixel route (build/consume, one-time grants) | `tier1/engainos/bridgeroom/trixel32d_live_route.py`, flag `TRIXEL32D_LIVE_ROUTE=1`; declarations `tier1/engainos/authority/scene_truth/<scene_id>.json` | `e06cb110` |
| Trixel construction | `../trixel3.2d/tools/consume_trixel32d_request_drop.py` (subprocess, file drops) | unchanged |
| Godot presentation | godotnew (see its `docs/continuity/`) | `0f9eafc`…`a2c4bd4` |

Receipts for each operation: `docs/integration_receipts/` (OP_A…OP_I, H02, H03).

## Production policy files (all deny-all)

- `tier1/engainos/authority/TRIXEL32D_LIVE_CLIENT_POLICY_V1.json` — `clients: {}`
- `tier1/engainos/authority/SCENE_ACTIVATION_CLIENT_POLICY_V1.json` — `clients: {}`
- `tier1/engainos/authority/scene_truth/` — README only, no scene declarations

## Local, uncommitted state (operator data, not code)

- Catalog extractions produced from the Godot Extract button under `tier3/mettaext/stageroom/output/narrative_to_game/catalog/` (001_the_ethereal_vigil, 002_molten_descent, book_19…).
- `.run/*.pid` change whenever the stack starts/stops.
- `docs/architecture/ZON4D_*`, `ZW_ZON_ZON4D_*` drafts and a stray file named `how --name-status a0af1728 -- \` (pre-existing, not from this work).

## Where development stopped

H04b (godotnew world environment viewport, `a2c4bd4`), then continuity records. Development paused 2026-11-25 for the manuscript rewrite; everything committed and pushed. See NEXT_OPERATION.md.

## Verified findings about Mettaext output (2026-11-25, chapter `book_01_book_of_genesis/001_the_ethereal_vigil.md`)

These are facts about the current pipeline, re-checked against the code and a real extraction. Do not lose them.

1. **Pass 4 preserves the narration.** `pipeline_work/out_pass1_<stem>.zonj.json` holds every segment as `=segments` (types `scene_header`, `narration`, `dialogue`): 197 segments, ~20,255 characters for this chapter. This is the richest manuscript-derived artifact. The runtime is fed from it (8765 `/load_scene?catalog_id=` takes `=segments` from Pass 4).
2. **Pass 5 truncates.** `tier3/mettaext/passroom/pass5_game_bridge.py:62-67` `_get_description` returns the first narration segment cut to `[:200]` characters. Pass 5 carries 32 events against Pass 4's 197 segments. Pass 5 game scenes (what the selector preview shows) are therefore a lossy summary, not the manuscript record.
3. **The environment extractor is disconnected.** `tier3/mettaext/semantic_environment_extractor.py` (keyword → profile scoring: coastal, forest, wasteland, …) is called by nothing in EngAIn's pipeline. Its only callers are the frozen donor's `Boot.gd` (`SEM_ENV_EXTRACTOR_SCRIPT`, via `OS.execute`) and an import-only facade in `out of root/engain/semantic/extraction.py`. It is keyword inference, not evidence; any reconnection is a D2 decision.
4. **Five candidate entities ≠ seventeen runtime entities. Keep them distinct.**
   - **5 candidate entities**: Pass 4 `@entities` (`he, mordain, syreth, unknown, vaelith`), copied by Pass 5 into the game scene. Shown in the selector's object preview (Layer 1).
   - **17 runtime entities**: GodotSim's `bridge_entities` after activation = those 5 plus 12 that GodotSim's own `SceneExtractor` finds in the Pass 4 segments (`SceneManager._extract_entities_for_scene`, `tier2/godotsim/scene_manager.py:336-343`; it extracts 16 capitalized names, e.g. `ethereal, realm, three, veil, aeon, keepers, lyaris, theron, tiamat, korath, pelagor, nephoretti`). Shown in the world environment (Layer 2).
   - The extra 12 are a runtime extraction, not Mettaext output and not manuscript-confirmed; several are not entities at all ("realm", "three", "veil", "ethereal").

## Spatial-language probe (2026-11-25): what pass1_spatial catches today

The manuscript work in progress inserts explicit spatial language (e.g. "Tran stood at the left edge of the rock while watching the northern sky. Meanwhile, behind him, Keen came around the corner of the southern cottage."). Run through real Pass 1 → `pass1_spatial.process_file` → `convert_spatial_signals_to_artifact`:

- Signals: `stand` (subj tran, obj "next"), `stand` (subj tran, obj "left edge"), `behind` (subj "meanwhile", obj "came around").
- Topologist entities: `meanwhile`, `came around`. Tran, Keen, the rock and the cottage are not recovered.
- Cause: `pass1_spatial.py` `_TRIGGERS` is a fixed list of ~25 triggers (before, behind, beside, near, above, below, within, between, through, in front of; stood, approached, moved, entered, crossed, retreated, withdrew, waited, raised; blocked, closed, barred, sealed). Subject = nearest content word to the left, object = next content words to the right. There is no handling of names, pronouns ("him"), landmarks, "next to", "edge of", "around the corner", compass terms (northern/southern), facing ("watching the northern sky") or simultaneity ("meanwhile").
- The inserted language is preserved verbatim in Pass 4 `=segments`; it is available to a better spatial pass (Tier 3 Mettaext deficiency, not a manuscript problem).
