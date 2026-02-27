# EngAIn System Manifest

## Core Architecture Truths
*Established: 2026-02-25*

### 1. The Unified Dispatcher
- **Single Entry Point**: All commands (HTTP POST, Text, Internal) MUST pass through `CommandDispatcher.dispatch()`.
- **Normalization**: The dispatcher resolves collisions between JSON keys (`command` vs `action` vs `text`) and prioritizes specific intent over generic labels.
- **Legacy Compatibility**: URL paths (e.g., `/scene/load`) are automatically mapped to dispatcher actions to support older client versions while using the new centralized logic.

### 2. State Management (SSOT)
- **Definitive State**: `EngAInRuntime.snapshot` is the **Single Source of Truth**.
- **Scene Storage**: 
    - `snapshot["scene"]`: Normalized view optimized for the `look/examine` pipeline.
    - `snapshot["scene_raw"]`: Immutable copy of the original ZONJ document.
- **Entity Dict**: `snapshot["entities"]` is a dictionary keyed by ID, ensuring O(1) lookups during simulation ticks.

### 3. Communication Protocol
- **Port**: `8080` (Default).
- **Synchronous Queries**: Text commands (`look`, `status`, `segments`) are processed **synchronously**. The HTTP response contains the result immediately—no polling required.
- **Asynchronous Actions**: Simulation mutations (`spawn_entity`, `update_entity`, `interact`) are **queued** for the next simulation tick and return an `ack`.
- **Safe Serialization**: All responses use `SafeJSONEncoder`. It gracefully handles `sets`, `tuples`, and custom objects by converting to lists or strings, preventing "Empty Reply" (Curl 52) errors.

### 4. Component Integration
- **MR Kernels**: Logic is partitioned into `spatial3d_mr`, `perception_mr`, and `behavior3d_mr`.
- **Adapters**: State-to-Kernel mapping is handled by specific adapters (Combat, Inventory, Dialogue).

## System Victories
- [x] **Unification**: Unified `/scene/load`, `/command`, `/inventory/*`, and `/combat/*` into a single dispatch pipeline.
- [x] **Responsiveness**: Eliminated the 250ms wait-loop for text commands; queries now return instant results.
- [x] **Stability**: Implemented `SafeJSONEncoder` to stop silent server crashes.
- [x] **Transparency**: Added verbose server-side logging for every incoming request and internal dispatch decision.


Files (confirmed by your debug output)

1. Runtime server

* `/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py`
  This is the Python `BaseHTTP/0.6` server that is actually answering on `127.0.0.1:8080` and implementing the endpoints you’re hitting (health/sync/load_mirror/command).

2. Mirror scene source (where `world/load_mirror` is scanning)

* `/home/burdens/chapters_md/.engain/build/book01_garden_genesis/scenes/*.json`
  Examples from collisions:

  * `zonj_05_the_garden_blooms.json` vs `zonj_05_the garden_blooms.json`
  * `zonj_chapter_26_the_claiming.json` vs `zonj_Chapter 26 the claiming.json`
  * `zonj_06_the_first_coming.json` vs `zonj_06_the first coming.json`
    (and several more)

Commands / endpoints we have working (the “known-good” set)

A) Health check

```bash
curl -sS http://127.0.0.1:8080/health | python3 -m json.tool
```

Expected: JSON like `{ "ok": true, "service": "engain", ... }`

B) World sync (fingerprint-gated; may return “skipped / vault_unchanged”)

```bash
curl -sS -X POST http://127.0.0.1:8080/world/sync \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": true}' | python3 -m json.tool

curl -sS -X POST http://127.0.0.1:8080/world/sync \
  -H 'Content-Type: application/json' \
  -d '{"dry_run": false}' | python3 -m json.tool
```

C) Load mirror scenes (this is the one that actually populates the registry and selects a default scene if none is active)

```bash
curl -sS -X POST http://127.0.0.1:8080/world/load_mirror \
  -H 'Content-Type: application/json' \
  -d '{}' | python3 -m json.tool
```

Expected: something like `scanned_files ~287`, `loaded ~269`, collisions report, `active_scene_after` set (e.g. `015_the_choice`).

D) Command dispatcher (your “text interface”)

```bash
curl -sS -X POST http://127.0.0.1:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"text":"status"}' | python3 -m json.tool

curl -sS -X POST http://127.0.0.1:8080/command \
  -H 'Content-Type: application/json' \
  -d '{"text":"look"}' | python3 -m json.tool
```

Expected: `status` includes `scene_id`, and `look` returns scene text + segment counts.

Important “negative” finding (so you don’t chase ghosts)

* `GET /` can return 404 and that’s not a problem.
* Earlier `GET /health` returned 404, but now it’s fixed and returns JSON. So health is implemented now; don’t rely on old outputs.

If you want, I can give you a single bash script that runs the whole smoke-test sequence and fails fast if any step returns non-JSON or `ok:false`.

