claude~

Here's my manifest entry:

---

**Date:** 2026-02-25

**Session:** sim_runtime.py State Persistence Fix + Syscheck Operations Suite

**What was broken:**
- `look`, `status`, `segments`, and `examine` all returned "No scene is loaded" even after a successful scene load — because `self.snapshot["scene"]` was never written
- `status` hardcoded `"scene_id": None` in 4 return paths, ignoring the computed value
- `GET /snapshot` crashed on `Combat3DAdapter.get_all_state()` (method didn't exist)
- `do_POST` had a misaligned `else` block causing silent crashes and empty responses
- `/command` path name collided with command text parsing ("command" shadowed the actual `{"text":"look"}` payload)

**What was fixed:**
1. **Bug 1 — Scene persistence:** Added `self.runtime.snapshot["scene"] = zonj` at line 982 in the text command handler, making the loaded ZONJ document visible to `look`/`status`/`segments`/`examine`
2. **Bug 2 — Status scene_id:** Replaced 4 hardcoded `"scene_id": None` returns with the computed `scene_id` variable
3. **Bug 3 — Snapshot crash:** Wrapped `combat.get_all_state()`, `inventory.get_all_state()`, and `dialogue.get_all_state()` in `try/except AttributeError`
4. **do_POST structural fix** (Antigravity): Resolved misaligned `else` block, semantic collision on `/command` path, and added robust ZONJ extraction + hard logging
5. **Removed dead code** from prior patch attempts (orphaned `getattr` block)

**Artifacts delivered:**
- `syscheck/doctor.sh` (v2) — one-screen stack health check matched to actual architecture (:8080 sim_runtime, :8090 scene_api)
- `syscheck/start_backend.sh`, `start_gateway.sh`, `start_engainos.sh`, `start_all.sh`, `stop_all.sh` — full operations suite
- Multiple diagnostic and fix scripts (`diagnose_all_bugs_v2.sh`, `fix_sim_runtime_final.sh`, `test_fixes.sh`)

**Verified result:**
```
scene_id: scene.12_nephilim_summoning
segments: 157
entities: korrhan, pazuzu, saresh, torhh, unknown
text: "chapter 12 The Nephilim Summoning..."
```

Full pipeline: Godot → SceneClient → scene_api:8090 → sim_runtime:8080 → look returns real narrative content.

GPT~
---

### 2026-02-25 — Runtime Routing + ZONJ Load Hardening (godotsim :8080)
Submitted-by: [NAME]

**Scope:** Runtime HTTP server on `127.0.0.1:8080` handling `/scene/load` and `/command`.

**Files (primary)**
- `~/burdens_of_a_forgotten_past/EngAIn/godotsim/sim_runtime.py`
- (If routing helpers exist) `~/burdens_of_a_forgotten_past/EngAIn/godotsim/protocol_envelope.py`
- (If server wrapper exists) `~/burdens_of_a_forgotten_past/EngAIn/godotsim/protocol_envelope_server.py`

**Problem**
- `/command` transport label was being treated as a gameplay command token (“command”), shadowing payload instruction (e.g., `text:"look"`), causing misrouting.
- `/scene/load` behavior diverged between wrapped (`{"zonj": {...}}`) and unwrapped (direct ZONJ doc) JSON payloads.
- Empty request bodies could crash or fail unclearly.
- Insufficient logging obscured request/dispatch routing.
- Unexpected errors did not reliably emit full tracebacks.

**Fixes Implemented**
1. Dispatcher uses payload instruction fields only (e.g., `text`) and ignores route labels.
2. `/scene/load` accepts wrapped and unwrapped ZONJ payloads; validates minimal schema (`@id`) before load.
3. Empty request bodies return `400 Bad Request` with clear error.
4. Hard logging for every POST + dispatch; unexpected errors print full tracebacks to STDOUT.

**Invariants Locked**
1. URL paths are transport metadata, never gameplay commands.
2. Gameplay dispatch derives from payload fields only.
3. Scene load accepts wrapped and unwrapped ZONJ forms.
4. `@id` required before mutating runtime state.
5. Empty body must deterministically return `400`.
6. Unexpected exceptions must print full traceback.

**Verification (Canonical Commands)**
- Scene load:
  - POST `http://127.0.0.1:8080/scene/load`
  - Body: `@$HOME/burdens_of_a_forgotten_past/EngAIn/mettaext/ingested/scenes/12_nephilim_summoning.zonj.json`
- Look:
  - POST `http://127.0.0.1:8080/command`
  - Body: `{"text":"look"}`

**Proof Observed (key fields)**
- Scene load returned: `status:"loaded"`, `scene_id:"scene.12_nephilim_summoning"`.
- Look returned:
  - `scene_id:"scene.12_nephilim_summoning"`
  - `entities_present:[korrhan, pazuzu, saresh, torhh, unknown]`
  - `total_segments:157`


gpt

This is clean now. Your accounting is internally consistent, and you proved the earlier 269/270 weirdness was just “selection work contaminating ingestion metrics.”

What you have, exactly

Health: OK and machine-readable (`/health` returns JSON).

Sync: deterministic short-circuiting.
Both dry_run=true and dry_run=false return `status: "skipped"` / `reason: "vault_unchanged"` with the same fingerprint. That’s fine; dry-run vs real won’t differ when the fingerprint gate blocks the entire operation.

Mirror load: fully consistent loader math.

* `scanned_files: 287`
* `attempted: 287`
* `accepted_new: 269`
* `rejected: 18`
* `failed: 0`
* `registry_size_before: 0`
* `registry_size_after: 269`
  So `accepted_new + rejected + failed = attempted` → `269 + 18 + 0 = 287` ✅
  And `registry_size_after = accepted_new` (because before=0, no overwrites applied into registry) ✅

Collision policy: clarified.
You’ve split “duplicate scene id overwritten pre-load: 11” vs “duplicate ignored: 6”. That explains why `overwritten: 0` at the registry stage: you’re resolving collisions before insertion, so there’s no runtime overwrite event to count.

Default selection: separated from ingestion.
Profiler now shows:

* `load_scene_calls: 269`
* `select_active_calls: 1`
  So the earlier mismatch is resolved the right way: selection does not inflate ingestion.

Status smoke test: correct.
`status` reports `scene_id: "015_the_choice"` after load_mirror, meaning the active scene pointer is set.

Only two improvements I’d still make (small, but worth it)

1. Rename “overwritten: 0” to be unambiguous.
   Right now you have:

* `overwritten: 0`
* `duplicate_scene_id_overwritten_pre_load: 11`

That’s confusing because “overwritten” sounds like it should be 11. Either:
A) Rename fields:

* `overwritten_in_registry: 0`
* `resolved_by_preload_newest: 11`
  or
  B) Set:
* `overwritten: 11` and add `overwritten_stage: "pre_load"`.

Pick one. The current form will cause future you to misread it.

2. Add `active_scene_set_method`.
   You already return `default_scene_reason`. Add one more field like:

* `active_scene_set_method: "default_first_loaded" | "preserved" | "explicit_request"`.

That will make it obvious when a later API call changes active scene (and you won’t need to infer from logs).

Net: you’ve got a reproducible cold-start sequence:
health → sync → load_mirror → command/status.
And the telemetry now reflects reality instead of profiler noise.

