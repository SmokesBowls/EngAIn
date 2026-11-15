# Trixel 3.2d Live Route — Blockers (2026-11-05)

Status: **route implemented, feature flag OFF, NOT approved for enablement.**
Nothing here is committed. No server was started, no live `runtime/` slot,
ledger, or Godot project was touched while producing this document.

Interface contracts and the remaining activation checks (V1–V3) are in
`docs/TRIXEL32D_INTERFACE_CONTRACTS_2026-11-05.md`.

Route: `POST /trixel32d/build` on the 8765 scene server
(`tier1/engainos/bridgeroom/scene_server.py` → `bridgeroom/trixel32d_live_route.py`),
404 unless `TRIXEL32D_LIVE_ROUTE=1`.

Test baseline at time of writing (flag unset):

| Suite | Command | Result |
|---|---|---|
| Live route | `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tier1/engainos/tests/test_trixel32d_live_route.py` | 10 passed |
| EngAIn trixel32d | same, `tier1/engainos/tests -k trixel32d` | 233 passed |
| trixel3.2d | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests` (in `../trixel3.2d`) | 85 passed, 100 subtests |

Fixed during review (regression-tested): `built_drop_dir` was computed relative to
`REPO_ROOT` *after* the ledger commit, so a runtime directory outside the repo
crashed between the ledger record and the receipt. Now computed before any
authorization (`test_built_drop_ref_is_runtime_relative_when_runtime_is_outside_repo`,
`test_rejected_issuance_writes_neither_ledger_record_nor_receipt`).

Remaining ordering note: after a successful ledger commit, `write_intake_receipt`
is the only remaining step. If it fails (disk error, or a receipt racing into the
slot), the ledger holds an authorization with no receipt. The ledger is the
authority record; the receipt is evidence. Acceptable only if that hierarchy is
confirmed.

---

## Resolution pass (2026-11-05, later) — status per blocker

Flag still OFF. No server started or restarted; no live `runtime/` slot, ledger,
or Godot file touched. Nothing committed.

| Blocker | Status | Change |
|---|---|---|
| B1 destructive read | **RESOLVED** | `runtime_core.get_snapshot()` is now a pure read; `/snapshot` and `/transforms` drain events themselves (behaviour unchanged); new `GET 8080 /snapshot/peek` reads through the same live-edit shim without draining. The route reads `/snapshot/peek`. |
| B2 fresh state per request | **RESOLVED (pending one confirmation)** | `LiveRouteAuthority` (in `trixel32d_live_route.py`) is built once by `launch_engine.EngAInRuntime.run()` only when the flag is set, injected via `start_scene_server(trixel32d_authority=…)`; the route never constructs state. Activation follows the runtime load stamp (below), not each request. Needs confirmation: SCENE_BOUND = "dies with the runtime scene load / process". |
| B3a self-issued activation | **PARTIAL** | `scene_manager.select_active_scene` stamps `snapshot["scene_activation"] = {runtime_instance_id, load_seq, scene_id}` after a completed activation. EngAInOS activates only when the stamp changes, so the activation is tied to a real runtime load (a reload of the same scene is a new activation). |
| B3b Semantic observation | **OPEN — authentication blocked on B4** | body `semantic` no longer accepted; composed `observation_source` only (none in production → 503). Testimony must name its `observed_load`; any other load → 409 (contracts C2). See guidance §2 below |
| B4 caller identity | **OPEN — no authentication contract exists** | registry removed; composed principal only (none in production → 503). See guidance §1 below |

New finding (affects B2/B3 design): `select_active_scene` stores the same entity
dicts in `snapshot["scene"]["entities"]` and `snapshot["entities"]`
(`entities_dict[eid] = ent`), so ticks mutate `snapshot["scene"]` (pos, presence).
A content hash of the scene is therefore **not** a stable scene identity and was
not used as the change signal. `scene_revision` is the hash of the scene as first
observed for a load. The aliasing itself was not changed (it may be relied on).

Corrected B3b finding: `~/Downloads/godotnew/semantic/Main.gd` (2026-11-04) *does*
build a presentation observation (`read_presentation_observation()`:
`main_instance_id = get_instance_id()`, `local_generation`, `locally_active`,
`geometry_application_permitted: false`) and emits `presentation_observation_changed`.
No listener exists outside `Main.gd`, and nothing transmits it to 8765/8080.
It lives in an individual engine project, not the reusable integration layer.
Until a transport exists, the route still takes `semantic` from the request body
and still echoes its own `activation_id` as `observed_activation_id`, so the
issuer's stale checks remain tautological. "Independently verified" also needs
the reporter's identity, which is B4.

### Architectural guidance applied (2026-11-05, evening)

Guidance received for the six open decisions. Per decision: existing
implementation, contract support, change made, tests, what stays open.

**1. B4 — 8765 caller identity.** Existing: none to reuse. 8080
`tier2/godotsim/runtime_gateway.py:_extract_request_context` reads tier, mode
and `actor_id` from the body (self-declared). Server-side mode authority exists
only as the process-global `tier1/engainos/aproom/reality_mode.RealityManager`.
No caller authentication, no tier classifier for HTTP callers, no
trusted-envelope issuer (findings §6J.6 table; re-checked: nothing new since
`176d1b87`). Contract support: none — **unresolved blocker**. Change: removed
`TRIXEL32D_LIVE_PRINCIPALS` (it was an invented identity table). The principal
is a composition-root input to `LiveRouteAuthority(principal=…)`;
`launch_engine` supplies none, so the route returns 503 "B4" before any side
effect. Body `principal`/`actor_id`/tier/mode are ignored. Tests:
`test_no_trusted_principal_fails_closed_before_any_side_effect`,
`test_body_identity_and_observation_have_no_effect`. Open: §6J.8 Q1/Q3/Q7 —
which authenticated identity and tier 8765 callers carry, who sets
`reality_mode`, who issues the envelope.

**2. B3 — Godot observation.** Existing reporting from the real Godot runtime
(`~/Downloads/godotnew/semantic`): `autoload/SimClient.gd` → 8080
(`/scene/load` with self-declared `actor_authority_tier: 2`, `/command`,
`/snapshot`, `/embodiment/pending`); `autoload/SceneClient.gd` → 8765 GETs only
(`/list_scenes`, `/load_scene`); `ArtworkClient.gd` → 8090. The observation
itself is `Main.gd:read_presentation_observation()`, emitted on a local signal
only. None of these channels is authenticated. Recommendation: the report
belongs on Godot's existing runtime channel, 8080 — the runtime is the
snapshot SSOT, Godot already reports load state there, and 8765 then reads it
through the non-consuming `/snapshot/peek` like the scene itself; 8765 must
not receive it directly (it would be certifying its own input). It should be
sent from the reusable integration layer (SimClient), not from `Main.gd`.
Contract support: channel yes; authentication **no — blocker (depends on B4)**.
Change: the route no longer accepts `semantic` from the body; the observation is
a composition-root `observation_source`, none supplied → 503 "B3". Tests:
`test_no_observation_source_fails_closed_before_any_side_effect`,
`test_body_identity_and_observation_have_no_effect`. Open: how Godot's report
is authenticated; then the observation must carry the activation id Godot saw
(today the issuer still compares the server's id with itself).

**3. Scene-bound slots.** Existing: `LiveAuthorityState.activate_scene` resets
occupancy and observation; `consume_authorization` refuses another activation
or runtime session; ledger replay keys occupancy by session. Contract support:
yes. Gap found and fixed: request-drop slots were keyed by request bytes only,
so pending work outlived a reload/restart and an identical request could never
be re-sent after a reload. Slots are now keyed by
(runtime_session_id, activation_id, request). Also added: a reload observed
mid-build is refused (409) rather than issued against a stale activation.
Tests: `test_scene_load_invalidates_the_old_slot_and_its_authorization`,
`test_runtime_restart_is_a_new_load_identity`,
`test_process_restart_invalidates_authorizations_and_pending_work`,
`test_load_change_during_a_build_is_refused` (mutation-checked: the first three
fail with the old key). Open: activation syncs lazily on the next route call;
a future consumer of authorizations must sync to the runtime load stamp first.

**4. Ledger and receipt.** Existing: `LiveAuthorityState` ledger (append-only,
fsync'd) is the record; `write_intake_receipt` is create-only. Change: the
receipt gains `authority_ledger_entry` {decision_id, apply_id, artifact_sha256,
runtime_session_id} (optional argument; other callers unchanged); a receipt
write failure now returns 500 naming the committed decision. A retry cannot get
a second authorization: the drop slot and the application slot both stay
occupied. Tests: `test_receipt_references_its_ledger_entry`,
`test_receipt_failure_is_explicit_and_never_yields_a_second_authorization`.
Open: no receipt re-issue path for a recorded decision (needs approval: it would
write evidence outside the request flow).

**5. Geometry delivery.** Existing routes: (a) trixel32d: built drop under
`runtime/trixel32d_built_drops/` + apply authorization → Godot apply executor
`/mnt/data-drive/godotollama/trixel_proof/trixel32d_apply_executor/` (isolated
proof, reads files; no transport); established by HANDSHAKES §7a/§7a.1 and
`docs/contracts/TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md`. (b)
`POST 8080 /embodiment/apply` + `GET /embodiment/pending` (`trixel_embodiment.v1`
Blender recipe texture) — HANDSHAKES §11.3 "not a valid integration path", yet
**live**: `Boot.gd` polls `/embodiment/pending` every 2 s. (c) `.trixel` skin
manifests (§7d; `assets/trixels/` empty). (d) 8765 `/art_recipe` (recipe, not
geometry). Retain: (a). Nothing in the live route feeds (b). Conflict found:
the executor accepts only `engainos.trixel32d_apply_authorization.v1` (from
`executors/trixel32d_apply_authorization_export_v1.py`, with
`collision_authorized` and `payload_binding`); the live issuer emits
`engainos.trixel32d_live_application_authorization.v1` without them. The inner
`trixel32d_surface_apply.v1` packet is the same. **Needs approval:** which
wrapper is canonical, and whether to retire (b) — removal is a deletion and
would change Godot behaviour. No code changed.

**6. `/transforms`.** Dependency analysis: no client calls `/transforms` (all
Godot projects in the repo, `~/Downloads/godotnew/semantic`, UPBGE, 8090,
tools); its docstring's SemanticRenderer caller no longer exists. No Godot code
reads runtime `payload.events`; the one reader is the 8090 HUD
(`engainos_server.py` `events_count`), which drains them through `/snapshot`.
Recommendation: state polling (`/transforms`, `/snapshot/peek`) non-consuming,
event consumption on one explicit consumer only. Change: none (behaviour pinned
by `test_transforms_poll_keeps_its_existing_draining_behaviour`). Needs
approval: which client is the event consumer, given none reads events today.

---

## B1 — Destructive scene read (`GET 8080 /snapshot`)

**Finding (STATIC):** `runtime_core.get_snapshot()` clears `self.snapshot["events"]`
after copying (`tier2/godotsim/runtime_core.py:832-833`). Every route call would
consume events a Godot client has not yet polled.

**Existing read-only sources inspected:**

| Source | Side effects | Gives | Usable? |
|---|---|---|---|
| `GET 8080 /snapshot` | clears events | full scene | **No** (destructive) |
| `POST 8080 /command {"text":"status"}` | none found; classified read-only, skips identity | `scene_id` only | identity only — no content, so no `scene_revision` |
| `GET 8080 /health` `/status` | none | subsystem status | no scene |
| `GET 8080 /transforms`, `/vault/status` | not fully traced | not the scene | no |
| `GET 8080 /embodiment/pending` | **pops** a queued contract | — | no (destructive) |
| 8765 `SceneLoader.load_scene(id)` | file read only | candidate scene file | not proof of the *loaded* scene (cf. D16: two scene sources disagree) |

**Conclusion:** no existing side-effect-free source of the active scene's full
content exists. The safest existing read is `status` (scene identity only).

**Minimum change (owner: GodotSim / tier2 runtime):** one of — (a) make
`get_snapshot` non-consuming and move event draining to an explicit consumer, or
(b) add a read-only scene view. Either touches `sim_runtime`/`runtime_core`,
currently out of scope.

**Proof test:** two consecutive reads return identical `events`; a Godot-style
poll after a route call still sees events emitted before it.

## B2 — Duplicate slot authorization (fresh state per request)

**Finding (TESTED via code read):** `LiveAuthorityState.activate_scene` always
mints a new activation and resets `_slot_occupancy = {}`. Ledger replay keys
occupancy by `(runtime_session_id, activation_id, parent_kind, parent_id, slot)`.
A fresh state per request therefore starts with every slot empty. Only the
request-drop slot (keyed by request bytes) blocks an identical retry; a
different request to the same slot is authorized again.

**Reuse through the 8765 composition root (no semantic change) — feasible, with conditions:**

- One `LiveAuthorityState` per process, built in `EngAInRuntime.__init__`
  (`launch_engine.py`), capabilities held there; passed into `start_scene_server`
  the same way `msg_handler` is (it becomes a `SceneRequestHandler` class
  attribute — process-wide, same pattern already used). Route receives the
  issuer only.
- The ledger flock is exclusive for process lifetime: no second process may use
  the same ledger path while 8765 runs.
- `AUTHORITY_REVISION` must stay constant across restarts or ledger load fails closed.
- New process ⇒ new `runtime_session_id` ⇒ slots free again. Correct only if
  SCENE_BOUND lifetime means "dies with the runtime session" (needs confirmation).
- **`activate_scene` must be called only on a real scene change**, never per
  request — otherwise occupancy resets and B2 returns. 8765 has no scene-change
  signal today; this depends on B1/B3.

**Minimum change (owner: EngAInOS / launch_engine composition root):** construct
state once; route stops constructing it; activation driven by a scene-change signal.

**Proof test:** two different requests to the same declared slot in one process
→ first AUTHORIZED, second 409 `CREATE_ONLY application slot is occupied`;
a second process cannot open the ledger while the first holds it.

## B3 — Self-issued activation / Semantic observation

**Finding (STATIC):** the route mints the activation and immediately echoes its
id as `observed_activation_id`; `semantic_main_instance_id` / `local_generation`
are client-supplied. The issuer's stale-activation and stale-generation checks
are therefore tautological. Inspected: no runtime activation identity exists
(`protocol_envelope.epoch_id` is the constant `"runtime_alpha"`); no Godot code
in `~/Downloads/godotnew/semantic` reports a Semantic instance id or generation.

**Minimum change:** (a) activation recorded when the scene is actually loaded
(owner: GodotSim scene load → EngAInOS state); (b) a Godot → EngAInOS Semantic
observation report (owner: reusable Godot integration layer, not one project).
Both out of current scope.

**Proof test:** a request carrying an activation id from a previous scene load
→ rejected `activation observation is stale`; a generation lower than the last
observed → rejected `Semantic local generation is stale`.

## B4 — Unauthenticated caller identity (D18)

**Finding:** 8765 has no authentication. The route's principal registry
(`TRIXEL32D_LIVE_PRINCIPALS`) maps a body-asserted `actor_id` to tier/mode — this
is effectively a new identity table, conflicting with D18's "no new identity
system" and the 2026-10-17 doctrine that humans hold no runtime authority.

**Existing trust contract:** `docs/architecture/ENGAIN_AUTHORITY_FINDINGS_2026-10-17.md`
§6J. The proposed repair (§6J.7, NOT DECIDED) is a fixed server-side principal
per HTTP entry point, body identity kept as a logged hint only. It does not
verify `actor_id`; no issuer exists or is specified. Open architect questions
that gate this route: §6J.8 Q1 (which fixed tier), Q3 (who sets `reality_mode`),
Q7 (is the Trixel "trusted EngAInOS authority envelope" the same envelope the
runtime gateway should consume, and who issues it). **No tier is chosen here.**

**Minimum change (owner: architect decision, then EngAInOS):** replace the
registry file with the §6J.7 fixed entry-point principal once Q1/Q3/Q7 are
answered; remove `TRIXEL32D_LIVE_PRINCIPALS`.

**Proof test:** body-supplied `actor_id`/tier/mode have no effect on the
authorization's `authority_evidence`; the evidence always names the fixed
entry-point principal.

---

## Geometry delivery: relation to `POST 8080 /embodiment/apply`

- `/embodiment/apply` accepts `trixel_embodiment.v1`: a **recipe texture** for an
  existing Blender GLB mount (`SemanticRenderer.apply_embodiment_contract` →
  `BlenderTerrainMount.apply_recipe_texture`). No geometry, no authorization.
- It is **ungated** (D5), in-memory, and `GET /embodiment/pending` pops destructively.
  `HANDSHAKES.md` §11 lists it under "Ungoverned mutation routes — not valid
  integration paths"; §7d calls it the in-EngAIn socket the 3.2d producer will
  "feed — or replace when the 7a contract settles."
- Producer: `tier2/godotsim/embodiment_contract_builder.py`; no live caller found.
- The live route produces a different thing: a checksum-locked
  `trixel32d_surface_built` mesh plus a `trixel32d_live_application_authorization`.
  It currently delivers nothing to Godot (returns the artifact and the drop path).

**Decision required (architect):** one geometry-delivery path. Either retire
`trixel_embodiment.v1` in favor of the authorized trixel32d path, or extend
the embodiment channel to carry the trixel32d authorization — but only after it
gains a gate, since an ungated queue cannot carry authority. Do not add a third
channel.
