# EngAIn — Current State

Last updated: 2026-11-25. Branch `main`. This file records facts; update it when they change.

## Repositories in play

| Repo | Path | Remote | HEAD at last update |
|---|---|---|---|
| EngAIn | `~/Desktop/burdens_of_a_forgotten_past/EngAIn` | `git@github.com:SmokesBowls/EngAIn.git` | `ca9c425c` (pushed through `f1822566`; `ca9c425c` local only) |
| godotnew (chapter selector) | `/mnt/data-drive/devvm-projects/engain-chapter-selector` | `SmokesBowls/godotnew` (origin is HTTPS without stored creds; push via `git@github.com:SmokesBowls/godotnew.git`) | `a2c4bd4` (pushed through `509dfd4`) |
| trixel3.2d | `~/Desktop/burdens_of_a_forgotten_past/trixel3.2d` | — | `dffe13a` (unchanged by the integration) |
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

H04b (godotnew world environment viewport, `a2c4bd4`). See NEXT_OPERATION.md.
