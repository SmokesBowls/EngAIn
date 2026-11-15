# Trixel3.2D ↔ EngAIn ↔ Godot interface contracts (2026-11-05)

Status: **implemented and verified in isolation; production unconfigured.**
`TRIXEL32D_LIVE_ROUTE` is still off. The production client policy is deny-all,
and production has no observation source, so a started engine composes no
authority and takes no ledger lock. See "Round 3 implementation" at the end;
it supersedes the PROPOSED labels in C1, C3 and C4 below.
Companion: `docs/TRIXEL32D_LIVE_ROUTE_BLOCKERS_2026-11-05.md` (blocker history).
Labels: **IMPLEMENTED** (in the working tree, tested), **EXISTING** (already in
the code, reused unchanged), **PROPOSED** (needs approval before code).

Path that is governed:

```
Trixel3.2D built drop ─► 8765 intake + validation ─► LiveApplicationIssuer ─► ledger
                                                                              │
Godot apply executor ◄── pre-apply consumption (8765) ◄── authorization artifact
        │
        └─► SCENE_BOUND presentation node (no collision, no gameplay, no canon)
```

---

## C1. Caller identity and transport authentication (B4)

### What exists (inspected)

| Mechanism | Path | Usable as authentication? |
|---|---|---|
| 8080 request context | `tier2/godotsim/runtime_gateway.py` `_extract_request_context` | No. The tier, mode and `actor_id` come from the request body. |
| `UntrustedPrincipal` + `register_trusted_principal` | `tier1/engainos/authority/trixel32d_live_authority_state.py:66,257` | Partly. It is an in-process trust token that only the holder of the composition-root capability can mint. It does not authenticate the transport. **Reused**: it is how a resolved identity reaches the issuer. |
| Session-claim tokens | `tier1/engainos/core/session_claim_registry.py` | No. It is a dispatch mutex, and `agent_id` is self-declared. |
| Presence authority (8767) | `claim_token` | No. It only proves who holds a release claim. |
| `SimClient.gd` `ENGAIN_OPERATOR_ID` | `~/Downloads/godotnew/semantic/autoload/SimClient.gd:19-24` | No. It is a launch-process label sent in the body. |

**Result:** EngAIn has no authenticated transport, so the route stays at 503 "B4".

### Proposed minimal local authenticated transport (PROPOSED)

The transport credential and the actor identity are separate on purpose. A credential
proves **which client binding** sent the bytes. Server policy decides
**which actor**, if any, that binding acts as.

| Element | Type | Owner | Rule |
|---|---|---|---|
| `client_id` | str, `^[a-z0-9-]{3,64}$` | composition root (`launch_engine.run`) | Names one binding, such as `godot-semantic-presentation`. It is not an actor. |
| client secret | 32 random bytes | composition root, created at start | Delivered over a launch-process channel only: a 0600 file under `runtime/` named by an env var. Never stored in project files, never in a request body, never logged. A restart rotates it. |
| `X-EngAIn-Client` | header, str | client | Must name a client in the live credential table. |
| `X-EngAIn-Timestamp` | header, int (unix s) | client | Rejected when more than 30 s from server time. |
| `X-EngAIn-Nonce` | header, 32 hex | client | Rejected if already seen within the window (in-memory replay cache). |
| `X-EngAIn-Signature` | header, 64 hex | client | `HMAC-SHA256(secret, method \n path \n timestamp \n nonce \n sha256(body))`, compared with `hmac.compare_digest`. Godot side: `HMACContext`. |
| client policy | file, owned by EngAInOS | **architect** (§6J.8 Q1/Q3/Q7) | `client_id → {actor_id, actor_authority_tier, permitted_routes}`. If the file is empty or missing, every request fails closed. No entries are proposed here, because that would be a privileged assignment. |
| `reality_mode` | str | **8080 runtime state**, not the caller | Read from the runtime's `RealityManager` context through `/snapshot/peek`. See gap G1. |

Trust boundaries:

1. Loopback is not authentication; any local process can connect.
2. The secret proves possession only. Whoever can read the 0600 file is that client.
3. The policy file is the only source of tier. The tier is never taken from the wire.
4. Identity fields in the body stay ignored, as they are today; tested in `test_body_identity_and_observation_have_no_effect`.

Rejections: a missing or unknown client, bad signature, timestamp skew, or reused
nonce → 401, with no side effect. An authenticated client with no policy entry,
or a route outside `permitted_routes` → 403. Any of these comes before the
existing B4 503 check.

**Gap G1:** the runtime's reality mode lives in the per-process
`tier1/engainos/aproom/reality_mode.py` `RealityManager`, which
`runtime_core.py:505` reads inside 8080. It is not published in the snapshot.
8765 runs in a different process, so it cannot read it today. Its
enum (`DRAFT, IMBUED, FINALIZED, DREAM, REPLAY, TEST`) is also wider than
`LiveAuthorityState._REALITY_MODES` (`DRAFT, FINALIZED, REPLAY`). The smallest
change needed: 8080 adds `reality_mode` to the `/snapshot/peek` payload, and
the architect decides how IMBUED, DREAM and TEST map to the issuer's modes,
or whether they are refused.

---

## C2. Godot presentation observation (B3)

### Implemented part: the testimony must name its load (IMPLEMENTED)

`ObservationSource` (`tier1/engainos/bridgeroom/trixel32d_live_route.py`) is now a
**zero-argument** callable, so it cannot echo back the server's expected load.
It returns Godot's latest testimony:

| Field | Type | Meaning | Validation on 8765 |
|---|---|---|---|
| `observed_load.runtime_instance_id` | non-empty str | The 8080 `runtime_instance_id` that Godot rendered. | Same parser as the runtime stamp (`_parse_load_identity`). |
| `observed_load.load_seq` | int ≥ 1, not bool | The 8080 `scene_load_seq` that Godot rendered. | as above |
| `observed_load.scene_id` | non-empty str | The scene id that Godot rendered. | as above |
| `main_instance_id` | int > 0, not bool | `Main.get_instance_id()` | `observe_semantic_activation` (EXISTING) |
| `local_generation` | int ≥ 0, not bool | `Main._presentation_local_generation` | Within one activation it must increase strictly (EXISTING) |

Rejections, all with no ledger write:
- testimony that isn't a mapping, or lacks a valid `observed_load` → 409 "Godot observation …";
- `observed_load` ≠ the load identity that the current activation was created from (an older load, a load that hasn't happened, another runtime process, or another scene) → 409 "names a different runtime scene load; stale or mismatched";
- a replayed or older `local_generation`, or a changed `main_instance_id` within one activation → 403 (the EXISTING state check).

The issuer's `observed_activation_id` is now set only after Godot's `observed_load`
matched the load behind the current activation. Godot never sees 8765's
`engain-activation-…` id. The 8080 load stamp is the activation identity Godot
can actually observe, and it maps one-to-one to the 8765 activation
(`LiveRouteAuthority.sync_activation`).

**Testimony vs verified state:** this is authenticated client *testimony*: Godot
says what it rendered. Nothing on the server verifies the scene tree. The
artifact's `semantic_activation` block records that testimony, not proof.

### Report transport (PROPOSED, depends on C1)

`SimClient.gd`, the shared runtime client, sends `POST /presentation/observation` to
8080, signed under C1 as `godot-semantic-presentation`. Its body is the table
above, filled from `Main.read_presentation_observation()` together with the
`scene_activation` stamp of the snapshot Godot last accepted. Main.gd must pass its
data in; it must not post on its own. 8080 stores only the latest report per
`(client_id, runtime_instance_id)` and rejects:
- a `runtime_instance_id` other than its own,
- a `load_seq` that isn't its current one,
- a generation that doesn't increase,
- an unsigned report.

8765's composed `ObservationSource` reads that report back through `/snapshot/peek`
(as `presentation_observation`, with the attesting `client_id`). It never accepts the
report from the caller who is requesting the build. The composition root must
also require that the attesting client is a different binding from the build caller.

Godot project change required (not made): add the report call to
`SimClient.gd`, and add the load stamp to the data Main.gd keeps from accepted snapshots.

---

## C3. Scene-bound lifecycle

| Boundary | Effect | Evidence |
|---|---|---|
| Load of a different scene | New activation; occupancy cleared; old authorization unconsumable | EXISTING `test_scene_replacement_invalidates_unconsumed_authorization` |
| Reload of the same scene (new `load_seq`) | New activation and a new drop slot; the old authorization fails "different scene activation" | IMPLEMENTED `test_scene_load_invalidates_the_old_slot_and_its_authorization`; EXISTING `test_same_scene_reactivation_invalidates_old_authorization` |
| 8080 restart (new `runtime_instance_id`) | New activation | IMPLEMENTED `test_runtime_restart_is_a_new_load_identity` |
| 8765 restart | New `runtime_session_id`; old authorizations fail "different runtime session"; fresh drop dir | IMPLEMENTED `test_process_restart_invalidates_authorizations_and_pending_work`; EXISTING `test_runtime_restart_invalidates_unconsumed_authorization` |
| Load during a build | 409, no ledger write | IMPLEMENTED `test_load_change_during_a_build_is_refused` |
| Newer Godot generation | Unconsumed authorization invalidated | EXISTING `test_newer_semantic_generation_invalidates_unconsumed_authorization` |

**Pre-apply check (PROPOSED).** The live state's activation changes only when 8765
handles a build request, because `sync_activation` runs inside `_build`. So the consume path must
first read `/snapshot/peek`, call `sync_activation`, and then call the EXISTING
`LiveAuthorityState.consume_authorization`. That call checks the exact artifact hash,
the runtime session, the activation, the Godot observation and the slot occupant, and allows a single use. The
Godot executor applies only on success. It then re-checks that its own last
accepted load stamp still equals the `observed_load` it consumed under, in the same
frame, before `add_child`. Removing the node when the scene is unloaded is
Godot's half of SCENE_BOUND. This needs to be verified on the real path (V1).

---

## C4. Authorization artifact: field-by-field mapping

Sources: `executors/trixel32d_apply_authorization_export_v1.py` (v1 producer),
`/mnt/data-drive/godotollama/trixel_proof/trixel32d_apply_executor/godot/trixel32d_apply_executor.gd`
(v1 consumer), `tier1/engainos/authority/trixel32d_live_application_issuer.py` (live).

| v1 executor check | v1 field | Live artifact source | Faithful? |
|---|---|---|---|
| raw file bytes SHA-256 = caller lock | (`expected_authorization_sha256` parameter) | ledger `artifact_sha256` = SHA-256 of `json.dumps(sort_keys, separators=(",",":"))` | Yes, if the file is written in exactly those canonical bytes. |
| `contract == engainos.trixel32d_apply_authorization.v1` | `contract` | `engainos.trixel32d_live_application_authorization.v1` | **Do not rename.** |
| gate name/passed | `gate_result.{gate_name,passed,message}` | `gate_result.{gate_name,passed}` | Yes. The executor doesn't read `message`. |
| 64-char intent digest | `authorized_intent_sha256` | same | Yes |
| `collision_authorized == false` | `collision_authorized` | absent; `apply_packet.collision.decision == "DENIED"` | Derivable; the executor already checks the packet. |
| embedded `trixel32d_surface_apply.v1` packet and all its sub-checks | `apply_packet` | `apply_packet`, same schema, same builder shape | Yes |
| `payload_binding` equals `surface_binding` | `payload_binding` | absent; it would be a copy of `apply_packet.surface_binding` | Redundant |
| declared target tuple | `scene_truth.declared_targets` | absent; declarations are authority state | **Not representable in the artifact.** Replaced by the consume check. |
| CREATE_ONLY slot unoccupied | `scene_truth.slot_occupancy` | absent; occupancy is authority state (and after commit the slot *is* occupied by this apply) | **Not representable.** The consume check requires occupant == `apply_id`. |
| not checked | `authority{…7 fields}` | `authority_evidence{…same 7}` | Yes |
| **no check** | — | `scene_activation{activation_id,scene_id,scene_revision}` | **v1 has no field and no check** |
| **no check** | — | `semantic_activation{activation_id,semantic_main_instance_id,semantic_local_generation}` | **v1 has no field and no check** |
| **no check** | — | `execution_performed:false`, `renderer_contacted:false` | v1 ignores them |
| **no check** | — | ledger reference (`decision_id`, `apply_id`, `artifact_sha256`, `runtime_session_id`) | v1 has nothing like it |
| scope | `godot_runtime_scope: ISOLATED_APPLY_EXECUTOR_PROOF_ONLY` | absent | v1 is marked proof-only |

**Finding: v1 is insufficient as the live target.** The v1 executor's
`apply(authorization_path, expected_sha256, payload_path, parent_nodes)` takes
no runtime session, no activation and no load identity. Its committed fixture from
`session-2026-07-18-proof` still applies today: Godot test
`01_…` passed on 2026-11-05. An adapter from live to v1 would therefore produce artifacts that
apply in any later scene load, which is the failure C3 forbids, and it would drop
`scene_activation`, `semantic_activation` and the ledger reference without any notice. The ledger also pins the live
artifact's exact key set (`_validate_ledger_artifact_bindings`), so v1 fields
cannot be added to it. **No adapter was built.**

**Proposed versioned successor (PROPOSED).** Do not add a new artifact schema. The live artifact is
already the authority record, so the change goes in the executor:
`trixel32d_apply_executor` gains `apply_live(...)`. That function accepts only
`engainos.trixel32d_live_application_authorization.v1` with the exact key set the
ledger enforces. It also requires a **consumption grant** from the C3 pre-apply check:
`{decision_id, apply_id, artifact_sha256, runtime_session_id, observed_load}`, returned by 8765 after
`consume_authorization` succeeds and delivered on the C1 transport. It refuses the grant when
`observed_load` ≠ its current accepted load, and re-runs every v1 packet check. v1 `apply()` stays frozen
for the July proof fixtures, and the old proof-only scope is retired when the architect decides.

Rejection proof status:

| Attack | Refused by | Evidence |
|---|---|---|
| Forged artifact (hash mismatch) | `consume_authorization` exact hash | EXISTING `test_consumption_requires_trusted_capability_and_exact_artifact_hash`; Godot v1 `SHA-256 does not match` |
| Forged issuance without capability | capability objects | EXISTING `test_direct_commit_without_issuer_capability_rejects` |
| Replay (second use) | `_consumed` set (durable) | EXISTING `test_authorization_consumption_is_durable_and_single_use` |
| Expired: new load, scene or session | activation and session check | C3 table |
| Mismatched payload | issuer SHA-256; Godot payload binding | EXISTING `test_mismatched_payload_hash_rejects`; Godot dual-slab `02/03` |
| Cross-activation | activation check | `…scene_load_invalidates…` and `…same_scene_reactivation…` |
| Stale Godot testimony | route `observed_load` | IMPLEMENTED `test_godot_testimony_for_another_load_is_refused` |
| **Cross-activation at the Godot executor** | **nothing in v1** | **Open until `apply_live` + grant (V1)** |

---

## C5. Geometry delivery

The governed path is the diagram at the top. Trixel produces bytes only. It holds no gameplay,
collision or canon authority: the issuer permits only `PRESENTATION_ONLY`,
`DENIED` and `SCENE_BOUND`, and the executor requires a MeshInstance3D with no collider.

The legacy `/embodiment` route has these consumers (inspected:
`tier2/godotsim`, `~/Downloads/godotnew/semantic`; not inspected: other Godot projects, `out of root/`):

| Role | Path |
|---|---|
| producer | `POST /embodiment/apply` (`tier2/godotsim/http_handlers.py:199,248`), **ungated** (D5). It accepts `trixel_embodiment.v1`. |
| builder with no caller found in that scope | `tier2/godotsim/embodiment_contract_builder.py` `build_embodiment_contract` |
| queue | `runtime_core.py:226` `pending_embodiment_contracts`; `GET /embodiment/pending` **pops** (destructive) |
| poller | `Boot.gd:191-195`, every 2 s → `SimClient.fetch_pending_embodiment_contract` |
| consumer | `Boot.gd:304-314` → `SemanticRenderer.apply_embodiment_contract` (`SemanticRenderer.gd:404`) → `BlenderTerrainMount.gd` |

Deprecation plan (PROPOSED, not started):
1. Characterization tests first: Python tests that `/embodiment/apply` + `/pending`
   keep their current shape and FIFO pop, and a GDScript test that
   `apply_embodiment_contract` refuses wrong versions, authorities and modes as it does today.
2. Add a startup warning when `/embodiment/apply` receives a contract. Behaviour is unchanged.
3. Once `apply_live` lands and is verified, gate `/embodiment/apply` behind an explicit
   legacy flag that defaults on. Then flip the default to off after the Boot.gd poll is shown to be a no-op.
4. Remove the Boot.gd poll and the routes only with explicit approval to delete them.

---

## C6. Runtime events

Current behaviour (EXISTING, preserved; tested in `tier2/godotsim/test_snapshot_peek.py`):
`GET /snapshot` returns the events and then clears them. `/transforms` clears them too.
`/snapshot/peek` never clears. The one live reader found is the 8090 HUD's
`events_count`, read through `/snapshot`. No Godot code reads the events.

Proposed cursor contract (PROPOSED):

| Element | Contract |
|---|---|
| sequence | Every event the runtime appends gets `event_seq`, an int that increases monotonically within one `runtime_instance_id`, in the order the tick appends events. |
| retention | A bounded ring (count and bytes) owned by the runtime. Reading never removes anything. |
| read | `GET /events?after=<seq>&limit=<n>` → `{runtime_instance_id, first_retained_seq, last_seq, events:[{event_seq,…}], gap:bool}` |
| gap / replay | `after < first_retained_seq - 1` → `gap:true`, and the client resyncs from `/snapshot/peek`. A different `runtime_instance_id` means the cursor is invalid and the client resyncs. Rereading a retained range is allowed and returns the same bytes. |
| authority | None. A cursor is the client's own position; no consumer is privileged, so the HUD is not nominated. |

Migration: (1) add `/events` alongside the current routes; (2) move the HUD to it;
(3) only then remove the drains from `/snapshot` and `/transforms`, with tests that
pin the new non-destructive behaviour. That last step changes behaviour and needs approval.

---

## C7. Ledger and receipts

The ledger (`LiveAuthorityState`, flock'd, append-only) is the authority. A receipt
(`trixel32d_built_drop_intake.write_intake_receipt`) is derived evidence and carries
`authority_ledger_entry {decision_id, apply_id, artifact_sha256, runtime_session_id}`
(IMPLEMENTED). Duplicates are prevented by the occupied slot and the create-only receipt (EXISTING and IMPLEMENTED,
`test_receipt_failure_is_explicit_and_never_yields_a_second_authorization`).

Idempotent receipt recovery (PROPOSED). The ledger `authorization_issued` event already
holds `built_response_b64`, `trusted_request`, `artifact` and `artifact_sha256`:
1. This runs inside the ledger owner (8765) only, because the flock forbids a second reader process.
2. Find exactly one `authorization_issued` event for the `decision_id`. If there is none → refuse.
3. Re-run the EXISTING `intake_built_drop` on the drop dir, using the ledger's
   `trusted_request` and `surface_binding.built_response_sha256`. The drop payload bytes
   must equal the base64-decoded `built_response_b64` from the ledger.
4. Receipt absent → write it create-only with `authority_ledger_entry` taken from the ledger.
   Receipt present and identical → no-op. Present and different → refuse and report.
5. Never calls the issuer, never appends to the ledger, never touches occupancy.

---

## Verification still required before activation

- **V1:** the real Godot apply path: `apply_live` + consumption grant, run in
  `godotnew/semantic` against a running 8080/8765, with a cross-activation attempt
  refused at the executor and the node freed on scene unload. Nothing in this change exercises it.
- **V2:** C1 is implemented and the client policy is filled in by the architect.
- **V3:** G1, publishing the runtime reality mode and mapping its six modes.

---

## Round 3 implementation (2026-11-05, approved scope)

### C1: signed-request transport (IMPLEMENTED)
`tier1/engainos/authority/local_signed_transport.py`. HMAC-SHA256 over
`METHOD\nPATH\nTIMESTAMP\nNONCE\nsha256(body)`, ±30 s freshness, a per-client
nonce replay cache that refuses when full, constant-time comparison, and 32-byte
secrets minted at every start (0600 files in a 0700 dir). Verification runs
before the body is parsed. The policy (`engainos.local_client_policy.v1`) is the
only source of `actor_id` and tier. It allows tiers 1–3 only (tier 0 is the
spec's internal system tier), has no reality-mode field, and refuses unknown
keys, duplicate keys and unknown routes. The committed
`tier1/engainos/authority/TRIXEL32D_LIVE_CLIENT_POLICY_V1.json` is
`{"clients": {}}`, i.e. deny-all. **Human decision required:** which client
bindings exist, and which actor_id and tier each gets. These can't be derived
from current contracts: the actor roster is stale and the 2026-10-17 doctrine
leaves human runtime authority undefined (§6J.8 Q1/Q3/Q7).

### Reality modes (IMPLEMENTED as fail-closed)
Inspected: the frozen `AUTHORITY_TIER_SPEC_v1.md` §3 (removed in `c0b6bc6a`,
read from git), `aproom/reality_mode.py`, and `TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md` §7.
- **Same dimension.** The spec defines one five-value dimension: DRAFT, IMBUED, FINALIZED, DREAM, REPLAY.
  `aproom.RealityMode` implements it and adds **TEST**, which the spec doesn't define.
- **Partial coverage, no mapping.** The Trixel contract defines handling for DRAFT, FINALIZED and REPLAY only.
  IMBUED and DREAM are spec values with no Trixel rule, and TEST is outside the spec. All three are refused with 409, naming the mode.
  This is identity within one dimension plus refusal. Nothing is mapped.
- **What 8080 publishes, and where.** 8080 now publishes `reality_context {mode, scene_id}` at the
  `/snapshot/peek` *envelope* level, outside the checksummed payload, read-only from
  `get_context()`. Missing → refused. Scoped to another scene → refused.
- **Finding:** nothing in production calls `set_mode`, so the runtime is always
  the default DRAFT. That is the runtime's real state, not a decision anyone made.

### C3/C4: atomic consumption, grant, `apply_live` (IMPLEMENTED)
- `POST /trixel32d/consume` runs under the authority lock, in this order:
  1. re-sync the activation from 8080's current load;
  2. require Godot's reported observation (read from the runtime) to name that load;
  3. require the consumer's own testimony to equal that report;
  4. refuse if the reality mode changed since issuance;
  5. sign the grant;
  6. call the existing `consume_authorization`, which checks the exact hash, session, activation,
     observation and slot occupant, and allows a single durable use.

  A refused consumption discards the grant unseen.
- The grant (`engainos.trixel32d_application_grant.v1`, `tier1/engainos/authority/trixel32d_application_grant.py`)
  is RSA-3072 PKCS#1 v1.5 / SHA-256, with a key pair generated per process.
  Godot gets only the public key, so it cannot mint a grant. It uses the
  installed `cryptography` package, which is not yet a declared EngAIn
  dependency, and fails closed if that package is absent.
- The authorization file is written create-only in the ledger's exact canonical
  bytes (`TRIXEL32D_LIVE_APPLICATION_AUTHORIZATION.json` next to the receipt).
  The live artifact is unchanged, and there is no v1 adapter.
- `godotollama/trixel_proof/trixel32d_apply_executor/godot/trixel32d_live_apply_executor.gd`
  holds `apply_live`, a new file; v1 is byte-identical. `apply_live`:
  - verifies the grant signature, its exact keys and that it is unused (it is burned on first presentation);
  - requires the host's current load and observation to equal the grant's;
  - checks the artifact's bytes against the grant hash and its exact live keys;
  - cross-binds decision, session, activation and observation;
  - re-runs all of v1's packet checks, then the payload hash, declared parent and CREATE_ONLY;
  - materializes through the passive consumer and attaches.

  All of this is synchronous, with no await between the check and the attach.
  `release_for_load()` frees nodes from earlier loads; nodes also die with their scene.

### Verification (V1) — isolated, not the production Godot project
`tier1/engainos/tests/test_trixel32d_live_godot_integration.py` drives headless
Godot 4.6.1 against a real 8765 (real routes, ledger, issuer, Trixel consumer)
and a stand-in 8080, using disposable data and a disposable two-client policy. All 23
GDScript checks pass, and mutations of the load check, the grant burn, the signature check and the
server-side consumption each make it fail.

Still unverified: the same path inside `~/Downloads/godotnew/semantic` with the real
`sim_runtime` on 8080. That needs:
- the SimClient → 8080 observation report (B3 transport),
- `SimClient` signing,
- the host calling `release_for_load` on each accepted snapshot,
- the human policy decision above.

---

## Round 4 — B3 runtime bridge and pre-activation security review (2026-11-05/06)

### B3 implemented
- **8080 intake** (`tier2/godotsim/presentation_observation.py`, wired in `http_handlers.py` and `sim_runtime.py`):
  - `POST /presentation/observation`, signed under the same transport contract, accepted only from clients holding the `observe` role.
  - 8080 has its own credentials under `runtime/engain_transport/8080/`.
  - Flag off → 404; uncomposed → 503.
  - The body has exactly these keys: `observed_load{runtime_instance_id, load_seq, scene_id}`, `main_instance_id`, `local_generation`, `presentation_active`, `report_seq`.
- **What is refused:**
  - a report naming anything other than the runtime's current load stamp (older, newer, another runtime, another scene, or no load);
  - for the same client and `main_instance_id`: a `report_seq` that doesn't increase (a delayed report), or a lower `local_generation` for the same load.

  A new `main_instance_id` (a restarted Godot) starts a new sequence.
- **What is retained:** the latest accepted report per client, labelled `AUTHENTICATED_CLIENT_TESTIMONY`, with the transport nonce and timestamp. It is kept in memory, so an 8080 restart forgets it.
- **How it is published:** at envelope level on `/snapshot/peek` as `presentation_observations`. Reading it never consumes it. `/snapshot` does not include it.
- **8765:** the observation source comes from the policy's single `observe` client and is read back from that peek. Testimony must have `presentation_active: true`. Composition refuses unless exactly one observer is assigned.
- **Godot (`~/Downloads/godotnew/semantic`)**:
  - `scripts/EngAInSignedRequest.gd` is the shared client signer.
  - `SimClient` reports signed observations on its own HTTPRequest. Reports are coalesced to the latest, and `report_seq` increases.
  - `SceneClient.consume_trixel32d_authorization` sends the signed consume request.
  - `Main`:
    - adopts the `scene_activation` stamp of every accepted snapshot;
    - calls `release_for_load` whenever it changes;
    - reports `active=false` for the previous load first;
    - clears the stamp on a new selection, a cancel or disk hydration;
    - reports on every observation change;
    - applies only through `apply_live`, using the load and observation current after the consume await.

    Its two hardcoded `http://127.0.0.1:8080/snapshot` URLs now use `SimClient.sim_base`; the default is the same.
- **Executor:** byte-identical copies of the godotollama executor files are vendored at the same `res://trixel_proof/...` paths. A test pins their hashes to the godotollama originals.

### One-time grant semantics
| Property | Behaviour |
|---|---|
| Issuance | Only inside `/trixel32d/consume`, after authentication, the current-load and observation checks, and the reality-mode check. The grant is signed *before* `consume_authorization`; a refused consumption discards it unseen. |
| One-time | Ledger: `authorization_consumed` is durable and allows a single use. Executor: `grant_id` is burned on first presentation. |
| Bound to | the consuming `client_id` (the executor refuses a grant naming another executor), runtime session, activation, scene/revision, runtime load, Godot main instance and generation, and the artifact SHA-256. |
| Expiry | `expires_at = issued_at + 30 s`. The executor refuses outside `[issued_at - 5 s, expires_at]`. |
| Failure | Never reissued. The authorization stays consumed and its slot stays occupied until the next scene load frees it. A failure costs presentation, never authority. |
| 8765 restart | The key pair is per process. After `reload_trixel32d_credentials()`, older grants stop verifying. A grant consumed *before* the restart and not yet reloaded-against stays executable until it expires, for the load it names only. Its consumption already happened in the ledger. |

Forged, self-signed, tampered, stolen (another executor) and expired grants are refused by the executor (godotollama checks 06a–06e). A grant presented early or late, under any load other than its own, is refused (semantic 03b, godotollama 01f/02d). Possessing a grant never creates an application without a prior ledger consumption: the semantic harness asserts every applied decision appears among the consumed decisions, and that no decision is consumed twice.

### Authentication before parsing
8765's `/trixel32d/*` and 8080's `/presentation/observation` are routed by **path only**. Both refuse a missing Content-Length (411) or one above 16 MiB (413) before reading. The remaining body bytes **are buffered**, then verified. JSON parsing and every state change happen only after verification. The only state the verifier itself changes is recording the nonce, and that happens only after the signature verifies. The HTTP server has already parsed the request line and headers by then.

### Scene-change races reviewed
1. *8080 reloads between consume and apply.* Godot applies only under the load it has *accepted*. A node can therefore show for the old load until Godot accepts the next snapshot, and is then released. Authority is unaffected: the authorization was valid when it was consumed.
2. *Godot changes load during the consume await.* `Main` re-reads its state after the await, and `apply_live` refuses on a mismatch. This is proven at the executor (semantic 03b); the await window itself is not timing-tested.
3. *Observation lag.* Consume requires the caller's testimony to equal the latest retained report. `Main` waits for `SimClient` to settle first. If a report is refused, the next consume fails closed (409).
4. *Two Godot processes on one credential.* The last report wins. A grant is bound to one `main_instance_id`, so the other process's executor refuses it.

### Same-user credential limits
Secrets are 0600 files in 0700 directories, rotated on every server start. Any process running as the same OS user can read them and act as that client; HMAC proves possession, not process identity. Loopback is not a boundary. Stronger options, not implemented: a dedicated OS user for EngAIn services, or Unix-domain sockets with `SO_PEERCRED`.

### Dependency
`tier1/engainos/requirements-authority.txt` pins `cryptography==50.0.2` (the installed system package). `GrantSigner` refuses with `AuthorityStateError` if the package is missing or not major version 50. Composition then returns no authority.

### Transport roles (policy entries still empty)
| Role | Server | Carries actor/tier | Real client today |
|---|---|---|---|
| `build` | 8765 | **yes**, recorded as authority evidence | **none exists**; nothing in EngAIn or Godot requests builds yet |
| `consume` | 8765 | no | the Godot presentation process (`SceneClient`) |
| `observe` | 8080 | no | the same Godot process (`SimClient`); one binding may hold both roles |

None of these is Dragon (canon only; it holds no runtime authority under the 2026-10-17 doctrine), Hermes (an LLM provider-session identity, `core/provider_session_binding.py`), or Foundry (found only in manuscript text within the inspected code). They are transport bindings, not actors.

### Evidence
- Real-project run (`tier1/engainos/tests/test_trixel32d_semantic_integration.py`): 24/24 GDScript checks.
  - Coverage: reload, stale grant, other scene, second use and request replay, delayed and superseded reports, stale observation, 8765 restart, 8080 restart, scene unload.
  - The ledger, receipts and authorization files cross-checked with what Godot applied: 4 applied, each consumed exactly once.
  - Mutations caught: skipping `release_for_load` (4 failures), dropping 8080 report ordering (1).
- 8080 intake: 14 tests.

Still not exercised:
- a separately launched `sim_runtime` process;
- Godot's full chooser UI flow (the test injects one registry entry and calls `Main._on_scene_selected`);
- a real build caller.
