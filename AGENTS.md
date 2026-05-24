# AGENTS.md

## Purpose

This repository is a living EngAIn workspace: game-engine code, narrative-to-game tooling, Godot/UPBGE clients, generated scene artifacts, architecture notes, recovered fragments, and historical prototypes live side by side.

Future agents must work here conservatively. Do not treat this as a clean package repo. Treat it as a survival archive with active systems embedded inside it.

Repository root observed for this checkout:

`/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

Remote observed:

`git@github.com:SmokesBowls/EngAIn.git`

Current branch observed:

`main`

## Non-negotiable safety rules

0. Do not produce code that is not Production grade.
1. Do not rename, move, delete, quarantine, or “clean up” files unless the user explicitly asks for that exact mutation.
2. Do not assume old `/home/burdens/...` paths in docs/scripts are valid. This checkout is under `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`.
3. Do not assume generated files are disposable unless you identify their generator and the user approves regeneration.
4. Do not assume archive, quarantine, recovered, or duplicate-looking directories are obsolete. They may contain memory anchors or historical implementation fragments.
5. Do not bypass authority gates in runtime code. If an invariant fails, fix the invariant cause; do not work around it silently.
6. Do not let clients own authoritative state. Python runtime/EngAInOS authority owns state; Godot/UPBGE render or request changes.
7. Do not mutate canonical/finalized narrative or world state as an AI agent unless the authority model permits it.
8. Do not trust one architecture document as complete truth. Cross-check docs, code, manifests, runtime endpoints, and user intent.
9. Do not run cleanup scripts casually. Files named cleanup/purge/reconcile may have broad side effects.
10. Do not write to this repo when the user asks for a draft, audit, map, or explanation only.

## Active systems

### 1. EngAIn simulation runtime

Primary path:

`godotsim/`

Important files:

- `godotsim/sim_runtime.py`
- `godotsim/runtime_core.py`
- `godotsim/command_dispatcher.py`
- `godotsim/protocol_envelope.py`
- `godotsim/scene_manager.py`
- `godotsim/scene_extractor.py`
- `godotsim/semantic_bridge.py`
- `godotsim/vault_manager.py`
- `godotsim/vault_linker.py`

Runtime role:

- Main Python simulation/runtime server.
- Holds the active world snapshot.
- Exposes HTTP API on port `8080`.
- Runs MR-style systems: spatial, perception, behavior, combat, inventory, dialogue, navigation.
- Provides text/debug commands such as `status`, `look`, `segments`, and `examine`.

Known contract:

- `EngAInRuntime.snapshot` is the single source of truth for runtime state.
- `snapshot["scene"]` is the normalized scene view used by look/examine/status pipelines.
- `snapshot["scene_raw"]` preserves original ZONJ scene input.
- URL paths are transport metadata, not gameplay commands.
- Gameplay dispatch should derive from request payload fields such as `text`, `action`, or command-specific fields.
- `/scene/load` has been hardened to accept wrapped and unwrapped ZONJ payloads.
- Empty bodies should return deterministic `400`, not crash.
- Unexpected exceptions should print full tracebacks.

Common endpoints:

- `GET /health`
- `GET /snapshot`
- `POST /scene/load`
- `POST /command`
- `POST /world/sync`
- `POST /world/load_mirror`
- `POST /vault/link`
- `GET /vault/search?q=...`
- `POST /combat/damage`
- `POST /inventory/take`
- `POST /inventory/drop`
- `POST /inventory/wear`
- `POST /dialogue/say`
- `POST /dialogue/ask`

### 2. EngAInOS / AP / authority runtime

Primary path:

`godotengain/engainos/`

Important files:

- `godotengain/engainos/launch_engine.py`
- `godotengain/engainos/engainos_server.py`
- `godotengain/engainos/runtime_client.py`
- `godotengain/engainos/runtime_api.py`
- `godotengain/engainos/core/ap_engine.py`
- `godotengain/engainos/core/ap_runtime.py`
- `godotengain/engainos/core/authority_validator.py`
- `godotengain/engainos/core/agent_gateway.py`
- `godotengain/engainos/core/empire_agent_gateway.py`
- `godotengain/engainos/core/reality_mode.py`
- `godotengain/engainos/core/intent_shadow.py`
- `godotengain/engainos/core/history_xeon.py`
- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`

Runtime role:

- Authority, AP rules, core law checks, scene server, Godot adapter.
- `launch_engine.py` is described in-code as authoritative/canonical.
- Starts a scene HTTP server on port `8765`.
- `engainos_server.py` is a FastAPI facade/supervisor over the runtime, normally on port `8090`.

Important invariant from `launch_engine.py`:

- It expects to run inside `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`.
- It checks core law files.
- It enforces import boundaries:
  - `core` must not import `godot`
  - `core` must not import `tools`
  - `tools` must not import `godot`
- It requires Python `3.10+`.
- It may create `assets/` and `assets/trixels/` if missing, so running it is not perfectly read-only.

Core law files checked by `launch_engine.py`:

- `godotengain/engainos/core/mesh_intake.py`
- `godotengain/engainos/core/mesh_manifest.py`
- `godotengain/engainos/core/scene_server.py`
- `godotengain/engainos/core/godot_adapter.py`

### 3. FastAPI supervisor facade

Primary file:

`godotengain/engainos/engainos_server.py`

Role:

- FastAPI facade titled `EngAInOS Kernel+Supervisor Facade`.
- Talks to the runtime via `NGAT_RT_BASE_URL`, defaulting to `http://127.0.0.1:8080`.
- Typically launched with uvicorn on `127.0.0.1:8090`.

Known routes:

- `GET /api/health`
- `GET /api/snapshot`
- `POST /api/command`
- `POST /api/combat/damage`
- `POST /api/inventory/take`
- `POST /api/inventory/drop`
- `POST /api/inventory/wear`
- `POST /api/dialogue/say`
- `POST /api/dialogue/ask`
- `GET /api/hud/engine`
- `GET /api/hud/combat`
- `GET /api/hud/inventory`
- `GET /api/hud/engine_summary`

### 4. Narrative / semantic / ZONJ pipeline

Primary paths:

- `mettaext/`
- `ghhhg/`
- `ingested/`
- `loaded/`
- `.engain_cache/`
- `.vault_cache/`

Important files:

- `mettaext/narrative_to_game.py`
- `mettaext/master_pipeline.py`
- `mettaext/pipeline_runner.py`
- `mettaext/pass1_explicit.py`
- `mettaext/pass2_entity_filter.py`
- `mettaext/pass2_event_builder.py`
- `mettaext/pass2_enhanced.py`
- `mettaext/pass3_merge.py`
- `mettaext/pass4_zon_bridge.py`
- `mettaext/pass5_game_bridge.py`
- `mettaext/engain_ingest.py`
- `mettaext/docs/UNIFIED_PIPELINE_GUIDE.md`
- `mettaext/docs/NARRATIVE_TO_GAME_PROOF.md`

Pipeline concept:

Narrative text -> typed segments -> inferred entities/events -> merged ZONJ -> ZON memory bridge -> game scene JSON.

Known stages:

1. Pass 1: segmentation
2. Pass 2: inference/entity/event building
3. Pass 3: merge
4. Pass 4: ZON bridge
5. Pass 5: game bridge

Authority principle from proof docs:

- Narrative is machine-readable authority.
- ZON is memory fabric.
- AI must not directly mutate world state outside governance.

### 5. Godot clients / renderers

Primary paths:

- `godotroot/`
- `godotnew/`
- `godot3d/`
- `godot_engain_test/`
- `godotengain/`

Role:

- Godot is a renderer/client, not state authority.
- Godot should request commands or render snapshots.
- Godot must not become the canonical state owner.

Important docs:

- `docs/README_ENGAIN_GODOT.txt`
- `godot3d/files/BRIDGE_PROTOCOL.md`
- `godotengain/engainos/docs/guides/GODOT_BRIDGE_README.md`

### 6. UPBGE client

~Discontinued usage until further notice.

Primary path:

`upbge/`

Important files:

- `upbge/ENGAIN_RUNTIME_META.md`
- `upbge/engain_http_client.py`
- `upbge/engain_upbge_bridge.py`
- `upbge/run_upbge_game.sh`
- `upbge/one_path.blend`

Role:

- UPBGE is a client/renderer/creative environment.
- Python runtime still owns state.
- UPBGE can spawn/update visual objects based on `/snapshot`.

Important line from `upbge/ENGAIN_RUNTIME_META.md`:

`Authority: Python. Always. Clients render. Clients never own state.`

### 7. Trixel / pixel / LibreSprite ecosystem

Primary paths:

- `trixelcomposer/`
- `trixelpixel/`
- `trixelmap/`
- `trixelworld/`
- `mechanimation/`
- `godotengain/engainos/tools/trixel/`

Notes:

- This area includes active tooling, experiments, vendored code, generated build products, and historical/recovered material.
- `trixelcomposer/LibreSprite-master/` is a large vendored/third-party source tree.
- `trixelcomposer/LibreSprite-master/build/` is generated build output.
- Do not edit vendored LibreSprite internals unless the user explicitly asks.

### 8. ZW / ZON / AP protocol material

Primary paths:

- `zw_repo-master/`
- `ap/`
- `docs/`
- `godotengain/engainos/core/zw/`
- `godotengain/engainos/core/zon_bridge.py`
- `godotengain/engainos/core/zon_to_entities.py`
- `godotengain/engainos/core/zon_to_game.py`

Conceptual model:

- ZW / Ziegel Wagga: semantic protocol / LLM-friendly narrative packet language.
- ZON: 4D declarative memory / persistent state.
- AP: declarative enforcement/rule layer.

Project motto from docs:

`Ziegel Wagga remembers. ZON persists. AP enforces.`

### 9. OKArchitect / multi-agent architecture notes

Primary path:

`okarchitect/`

Role:

- Technical/multi-agent architecture notes and OKArchitect council design.
- Treat as documentation/source doctrine unless the user says otherwise.

### 10. GUI / legacy ZW editor

Primary paths:

- `gui/`
- `tests/`

Important files:

- `gui/zw_gui.py`
- `gui/official_zw_validator.py`
- `gui/official_zw_spec_rules.py`
- `run_tests.sh`

Known test command:

`xvfb-run python3 -m unittest discover -s gui/tests/`

## Runtime ports

Known active/default ports:

| Port | System | Where observed | Notes |
|---:|---|---|---|
| `8080` | `godotsim/sim_runtime.py` | `system.manifest.md`, `server_instructions-subsystems.md`, `upbge/ENGAIN_RUNTIME_META.md` | Main EngAIn runtime HTTP API. |
| `8765` | `godotengain/engainos/launch_engine.py` scene server | `server_instructions-godot.md`, `launch_engine.py` | AP/scene HTTP server started by launch engine. |
| `8090` | FastAPI facade via uvicorn | `tools/engain_stack_tmux.sh`, `.logs/engainos_uvicorn.log` | `engainos_server:app`, proxy/supervisor over runtime. |

Common stack command from existing tooling:

```bash
tools/engain_stack_tmux.sh
```

Be careful: this launches multiple interactive/runtime systems including sim runtime, AP scene server, FastAPI facade, Godot editor, UPBGE, and vault window. Do not run it unless the user wants the full stack started.

## Current authority model

Authority is layered and contextual.

### Runtime authority

- `godotsim/sim_runtime.py` / `EngAInRuntime.snapshot` is the runtime state authority for the simulation server.
- MR kernels should operate on snapshot/slices and return deltas/outputs.
- Kernels should not directly mutate global world state in place.
- Runtime/adapters apply accepted deltas back into the snapshot.

### Client authority

- Godot and UPBGE are clients/renderers.
- Clients may render snapshots.
- Clients may submit commands.
- Clients must not own canonical state.
- Client-specific routes should not replace shared runtime contracts.

### AP / governance authority

Normative spec:

`godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`

Authority tiers:

| Tier | Actor type | Description |
|---:|---|---|
| `0` | System | Internal runtime, replay, validation |
| `1` | AI Agent | Autonomous but constrained |
| `2` | Human Operator Limited | Assisted control, non-final |
| `3` | Human Authority Root | Canonical override |

Reality modes:

| Mode | Mutability | Canonical? |
|---|---:|---:|
| `DRAFT` | Yes | No |
| `IMBUED` | Yes | No |
| `FINALIZED` | Restricted | Yes |
| `DREAM` | Sandbox | No |
| `REPLAY` | No | N/A |

Hard rules:

- A tier is necessary but not sufficient for mutation.
- `REPLAY` blocks all mutation.
- `FINALIZED` requires Tier 3.
- AI agents cannot mutate `FINALIZED`.
- Tier escalation is impossible from inside the actor.
- Rejected commands go to Intent Shadow and must not mutate world state.
- Governance must be deterministic: same inputs + same tier + same reality mode -> same result.
- If a test conflicts with the frozen authority spec, the test is wrong.

## Source vs generated / runtime / archive directories

This repo mixes source, generated artifacts, runtime state, third-party code, and archives.

### Treat as source / hand-authored unless proven otherwise

- `godotsim/` except obvious caches, `node_modules`, generated outputs, or patch artifacts
- `godotengain/engainos/core/`
- `godotengain/engainos/launch_engine.py`
- `godotengain/engainos/engainos_server.py`
- `godotengain/engainos/runtime_client.py`
- `godotengain/engainos/runtime_api.py`
- `mettaext/*.py`
- `upbge/*.py`
- `gui/*.py`
- `tools/*.sh` and tool scripts, but inspect before running
- `docs/`
- `manifests/`
- `system.manifest.md`
- `project.manifest.md`
- `server_instructions-*.md`
- architecture map docs such as `godotsim/architectual_map_sim_runtime.md`
- protocol/spec folders such as `zw_repo-master/`, `ap/`, and ZW/ZON/AP docs
- Godot scripts/scenes/project files unless clearly generated
- UPBGE bridge code and `.blend` assets unless the user says to regenerate them

### Treat as generated/cache/runtime state by default

Do not hand-edit unless the user explicitly wants artifact surgery.

- `.engain_cache/`
- `.engain_logs/`
- `.logs/`
- `.run/`
- `.vault_cache/`
- `__pycache__/`
- any nested `__pycache__/`
- `*.pyc`
- `tmp/`
- `loaded/`
- `ingested/`
- `mettaext/loaded/`
- `mettaext/ingested/`
- `mettaext/ingested/scenes/`
- generated `*.zonj.json` scene outputs unless source of truth is established
- generated scene indexes such as `mettaext/loaded/scene_index.json`
- runtime logs such as `.logs/launch_engine.log`, `.logs/sim_runtime.log`, `.logs/engainos_uvicorn.log`

### Treat as dependency/vendor/build output

Do not edit unless explicitly working on that vendored project or build system.

- `godotsim/node_modules/`
- `trixelcomposer/LibreSprite-master/third_party/`
- `trixelcomposer/LibreSprite-master/build/`
- compiled artifacts such as `.o`, `.a`, binaries, ninja logs/deps
- `trixelcomposer/LibreSprite-master.zip_incomplete/`

### Treat as archive/quarantine/historical preservation

Do not delete or “clean” without explicit user approval.

- `_quarantine/`
- `archive/`
- `stray/`
- copied/recovered folders
- duplicate-looking old GUI files such as `old_*` / `older_*`
- architecture conversation transcripts
- large historical docs under `trixelworld/Documentation/`

These may be evidence, memory anchors, or recovery material.

## Forbidden assumptions

Do not assume:

1. “Old” means unused.
2. “Duplicate” means safe to delete.
3. “Generated” means safe to regenerate.
4. “Quarantine” means trash.
5. “Archive” means irrelevant.
6. “Docs are stale” without checking code and current user intent.
7. “Code is canonical” when a frozen authority/spec doc says otherwise.
8. “Tests are right” when they contradict authority model docs.
9. `/home/burdens/...` paths still work.
10. The current working directory is always repo root.
11. Godot or UPBGE owns game state.
12. AI agents may mutate finalized canon.
13. `GET /` returning `404` means the runtime is down.
14. `GET /health` history in older docs reflects current behavior.
15. Runtime commands are asynchronous unless the endpoint says so; text commands are synchronous in current docs.
16. URL path names are gameplay commands.
17. Node, Python, Godot, Blender, UPBGE, tmux, or uvicorn are installed without checking.

## Mutation rules

### Before any edit

1. Confirm the requested scope.
2. Run `git status --short`.
3. Identify whether the target is source, generated, vendor, archive, quarantine, or runtime state.
4. Read the relevant authority/spec docs first if touching runtime, AP, canon, governance, or pipeline code.
5. Prefer minimal patches over rewrites.
6. Preserve file paths unless the user explicitly requests a move/rename.
7. Do not update generated outputs unless the user requested regeneration.
8. Do not run formatters across the whole repo.
9. Do not run cleanup scripts unless the user explicitly asks and understands scope.
10. If starting servers, note ports and stop them afterward unless the user asks to keep them running.

### Runtime/code mutation boundaries

When touching `godotsim/`:

- Preserve `EngAInRuntime.snapshot` as SSOT.
- Preserve synchronous text command behavior for `look`, `status`, `segments`, `examine`.
- Preserve safe JSON serialization.
- Preserve route-vs-payload distinction.
- Preserve wrapped and unwrapped ZONJ scene loading if editing `/scene/load`.
- Preserve full traceback logging for unexpected runtime errors.

When touching `godotengain/engainos/`:

- Respect `launch_engine.py` as canonical entrypoint.
- Respect import boundaries: `core ← tools ← godot`.
- Do not make `core/` depend on `godot/`, `tools/`, or tests.
- Do not bypass `AUTHORITY_TIER_SPEC_v1.md`.
- Keep tests aligned to the authority spec, not the other way around.

When touching clients:

- Godot/UPBGE should render snapshots and submit commands.
- Do not move authority into GDScript, Blender logic nodes, or UPBGE scripts.
- Shared runtime endpoints are preferred over client-specific special cases.

When touching narrative/canon:

- Do not rewrite canon or generated scene meaning casually.
- Establish source of truth first: novel/vault/chapter text, generated ZONJ, runtime scene JSON, or docs.
- Keep provenance clear.

## Verification commands

Use commands selectively. Do not run long or mutating commands without reason.

### Basic repository state

```bash
git status --short
git branch --show-current
git remote -v
```

### Check runtime ports

```bash
ss -ltnp | grep -E ':(8080|8765|8090)\b' || true
```

### Main runtime health, if `godotsim/sim_runtime.py` is already running

```bash
curl -sS http://127.0.0.1:8080/health | python3 -m json.tool
curl -sS http://127.0.0.1:8080/snapshot | python3 -m json.tool | head -n 80
```

### Main runtime command checks

```bash
curl -sS -X POST http://127.0.0.1:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"text":"status"}' | python3 -m json.tool

curl -sS -X POST http://127.0.0.1:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"text":"look"}' | python3 -m json.tool
```

Expected:

- `status` should include a scene id or clear no-scene state.
- `look` should return narrative content after a scene is loaded.
- Placeholder-only text after scene load means the scene is not visible to the text pipeline.

### World sync/load mirror smoke sequence, if runtime is running

```bash
curl -sS -X POST http://127.0.0.1:8080/world/sync \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}' | python3 -m json.tool

curl -sS -X POST http://127.0.0.1:8080/world/load_mirror \
  -H 'Content-Type: application/json' \
  -d '{}' | python3 -m json.tool

curl -sS -X POST http://127.0.0.1:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"text":"status"}' | python3 -m json.tool
```

### Start main runtime manually

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim
python3 sim_runtime.py
```

Expected:

- Server on `http://localhost:8080`.
- Boot messages for SceneExtractor, SemanticBridge, protocol, epoch, MR/adapters.
- Stop with `Ctrl+C`.

### Start EngAInOS / AP launch engine manually

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
python3 launch_engine.py
```

Expected:

- Phase 2 invariant checks pass.
- Scene server starts on `http://localhost:8765/`.
- Godot adapter reports ready.
- Stop with `Ctrl+C`.

Warning:

- `launch_engine.py` may create `assets/` and `assets/trixels/` if missing.

### Start FastAPI supervisor manually

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
NGAT_RT_BASE_URL=http://127.0.0.1:8080 \
python3 -m uvicorn engainos_server:app --host 127.0.0.1 --port 8090
```

Then verify:

```bash
curl -sS http://127.0.0.1:8090/api/health | python3 -m json.tool
curl -sS http://127.0.0.1:8090/api/snapshot | python3 -m json.tool | head -n 80
```

### GUI tests

```bash
export PYTHONPATH="$PYTHONPATH:."
xvfb-run python3 -m unittest discover -s gui/tests/
```

Existing helper:

```bash
./run_tests.sh
```

### EngAInOS unit tests

Run narrowly first:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_authority_spec_v1.py'
```

Broader test discovery, only when needed:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

### Import boundary checks

Preferred if using launch engine:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import launch_engine
launch_engine.run_invariants_check()
PY
```

Caution:

- Importing `launch_engine.py` may execute module-level imports and path checks.
- Full `python3 launch_engine.py` starts server components.

### Full stack helper

```bash
tools/engain_stack_tmux.sh
```

Only run this when the user wants the whole stack. It attempts to start:

- `godotsim/sim_runtime.py` on `8080`
- `godotengain/engainos/launch_engine.py` on `8765`
- `engainos_server:app` on `8090`
- Godot editor
- UPBGE/Blender
- vault window

This script contains older `/home/burdens/...` paths in this checkout. Check and adapt paths before relying on it.

## Known path hazards

Many docs/scripts still reference old paths such as:

- `/home/burdens/burdens_of_a_forgotten_past/EngAIn`
- `/home/burdens/chapters_md`
- `/home/burdens/obsidian/obsidianburdenNov25`
- `/home/burdens/Applications/upbge-0.50-linux-x64`
- `~/Downloads/EngAIn`

Current observed root is:

`/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

Before running any script that embeds absolute paths:

1. Read it.
2. Check for `/home/burdens`.
3. Prefer environment variables if the script supports them.
4. Ask before editing path constants.

## Handling generated scene data

Generated scene data exists in multiple places:

- `.engain_cache/parsed/scenes/`
- `mettaext/ingested/`
- `mettaext/ingested/scenes/`
- `mettaext/loaded/`
- `loaded/`
- `ingested/`

Rules:

1. Do not hand-edit generated scenes unless the user explicitly asks.
2. If runtime behavior is wrong, first identify whether the issue is:
   - source narrative
   - pipeline transform
   - generated ZONJ
   - loader
   - runtime snapshot visibility
   - client rendering
3. If regenerating, preserve or diff old outputs.
4. Do not delete collision/duplicate outputs until the collision policy is understood.
5. Scene ID collisions may be resolved before registry insertion, so runtime `overwritten: 0` does not necessarily mean no pre-load duplicates existed.

## Debugging principles

1. Reproduce with the smallest live surface.
2. Check which server is actually answering.
3. Check port before assuming code path.
4. Check JSON validity before analyzing payload semantics.
5. For runtime scene issues, verify:
   - `/scene/load` returns loaded status.
   - `snapshot["scene"]` or payload scene fields are populated.
   - `status` shows nonzero segments.
   - `look` returns real narrative text, not placeholder.
6. For authority/gateway issues, check:
   - actor tier
   - reality mode
   - AP rule result
   - Intent Shadow recording
   - canonical history mutation/no mutation
7. For client rendering issues, verify `/snapshot` first. If the snapshot is wrong, fix runtime/pipeline. If the snapshot is right, fix client adapter/rendering.

## Recommended workflow for future agents

1. Start with `git status --short`.
2. Read the relevant manifest/docs:
   - `system.manifest.md`
   - `project.manifest.md`
   - `server_instructions-subsystems.md`
   - `server_instructions-godot.md`
   - relevant architecture map
   - relevant frozen authority spec
3. Classify touched paths as source/generated/vendor/archive/runtime.
4. Use narrow reads/searches before editing.
5. If editing, patch minimally.
6. Run the smallest verification command that proves the change.
7. Report:
   - files touched
   - commands run
   - ports used
   - verification result
   - any skipped tests and why
8. If no files were changed, say so clearly.

## Quick classification cheat sheet

Living core:

- `godotsim/`
- `godotengain/engainos/core/`
- `godotengain/engainos/launch_engine.py`
- `godotengain/engainos/engainos_server.py`
- `mettaext/*.py`
- `upbge/*.py`
- `gui/*.py`
- `tools/`

Canonical/foundational docs:

- `system.manifest.md`
- `project.manifest.md`
- `server_instructions-*.md`
- `docs/`
- `godotsim/architectual_map_sim_runtime.md`
- `godotroot/architectual_map_zonjrender.md`
- `godotengain/architectural_map_launch_engine (copy).md`
- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`
- `mettaext/docs/NARRATIVE_TO_GAME_PROOF.md`
- `mettaext/docs/UNIFIED_PIPELINE_GUIDE.md`

Generated/runtime:

- `.engain_cache/`
- `.engain_logs/`
- `.logs/`
- `.run/`
- `.vault_cache/`
- `loaded/`
- `ingested/`
- `mettaext/loaded/`
- `mettaext/ingested/`
- `__pycache__/`
- `tmp/`

Vendor/build:

- `godotsim/node_modules/`
- `trixelcomposer/LibreSprite-master/third_party/`
- `trixelcomposer/LibreSprite-master/build/`

Preserve/historical/recovery:

- `_quarantine/`
- `archive/`
- `stray/`
- old/copied/recovered docs and prototypes

## Final reminder

This repository is not just code. It is code plus lore, canon, protocol doctrine, generated state, engine experiments, client integrations, and recovery history.

Work like a careful archivist-engineer:

- preserve first,
- classify before changing,
- respect authority,
- verify on the right port,
- never let convenience outrank canon.

