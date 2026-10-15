# EngAIn Handshake Switchboard
## Architecture Specification v0.3 — Hypothesis, Evidence, and Pilot Plan
**Date:** 2026-10-14  
**Supersedes:** v0.2 (same day). v0.1 dated 2026-10-14.  
**Evidence baseline:** repository `main @ 567392ba` (read-only audit, 2026-10-14)  
**Status:** Hypothesis. Not implemented. Not authorized for repository modification beyond read-only discovery and the single pilot in Section 9 once approved.

> **ANTI-DRIFT RULE (binding on every reader, human or AI):** Nothing in this document, and nothing proposed from it, is true until verified against the actual repository. Every claim carries evidence before a proposal is accepted as what it says it is. See Section 12.

> **Terminology note:** Names used here are working terms chosen by the architect. Where the repository uses a different name for the same thing, the repository's name wins. Verified example: the subsystem is **Engionality** (`tier2/engionality/`), not "Engineality."

### What changed from v0.2
- "AP" split into its distinct meanings; the authority question is now asked per AP (§5)
- Written-contract evidence added to the authority hypotheses (§5.2)
- Existing relay law addressed; Switchboard adopts it rather than competing with it (§4.1)
- Staleness extended from fallback to binding; content hashes added (§3.4, §8)
- Evidence must be re-runnable; checks must not write into the repo (§12)
- Conflicts come only from registered records, never inference (§3.5)
- Deletion manifest required for moves and cleanups (§17)
- New label `ARCHITECT-STATED` for design intent that cannot live in code (§12.3)
- Verification table updated with audit results (§11)
- Narration redesigned as self-introduction: roll call at wake-up, with every spoken fact built from records and checked live (§16)

---

## 1. Problem
EngAIn's subsystems connect through direct handshakes scattered across files: imports, paths, payload assumptions, adapters. Three concerns are tangled inside those handshakes:

| Concern | Question it answers |
|---|---|
| **Identity** | What is this subsystem and what does it do? |
| **Authority** | Who is responsible for deciding this operation? |
| **Routing** | How does a request physically reach that subsystem? |

Because authority is embedded in routing, it is **invisible**. Agents repair or move one connection, unknowingly change who decides something, and break an established chain.

Documented instances at `567392ba`:
- One filename (`ap_engine.py`) held two unrelated implementations at different times; gates validated the wrong one. Fix: identity independent of path (§8 `handshake_id`).
- Gates passed and wrote acceptance reports; later gates trusted those reports instead of re-checking. Fix: re-runnable evidence (§12.2).
- `tier1/engainos/relays/ap_runtime_relay.py:47` still points at a `godotengain/…` path removed during rehousing. Fix: staleness tracking (§3.4).

## 2. Core hypothesis and history
- **H-SW1.** A central Switchboard can hold the authority and routing map without owning domain logic. `HYPOTHESIS`
- **H-SW2.** Existing direct ("absolute") handshakes can be kept intact and demoted from default to fallback. `HYPOTHESIS`
- **H-SW3.** Tracing and registering handshakes one at a time reconstructs the real blueprint from working machinery. `HYPOTHESIS`
- **H-SW4.** Authority corrections can then be made at the Switchboard instead of across every participating file. `HYPOTHESIS`

**Why the fallback is non-negotiable** (`ARCHITECT-STATED`): an earlier generation of the system (MythTech era) ran on beacons, a broker, and a port sheriff, a central router with no fallback. One beacon's memory leak produced a ~600 GB file, and the central layer took everything down with it. The Switchboard is therefore designed as the **deliberate breaking point**: if it fails, the system falls back to the direct handshakes, it does not stop.

## 3. Operating model

### 3.1 Normal operation
```text
Subsystem ──► Switchboard ──► resolved handshake ──► authorized handler
```

### 3.2 Switchboard unavailable
```text
Subsystem ──► original absolute handshake ──► handler
```

### 3.3 Failure modes
| Condition | Response |
|---|---|
| Switchboard unavailable | Use absolute handshake **only if** `fallback_authorized` at last verification |
| Registered authority conflict (§3.5) | **Fail closed.** Do not route. Flag for human review |
| Switchboard corrected an authority; absolute handshake still points at old authority | Fallback **not authorized**. Fail closed until fallback updated and re-verified |
| Handshake not yet registered | Unchanged: original path runs exactly as today |
| Fallback path missing or content hash mismatch | `fallback_stale`. Switchboard route continues; fallback repaired and re-tested before it counts |
| Switchboard binding path missing or content hash mismatch | `binding_stale`. Do not route via Switchboard; use fallback if authorized; flag |

### 3.4 Staleness (binding and fallback)
Both sides can go stale. A single rehousing commit broke 15 gates at once.
- Every registered path (binding and fallback) must exist at `last_verified_commit`, and its content hash must match the recorded hash.
- Every migration updates the binding **and** the fallback, then re-tests both.
- A handshake with either side unverified since the last move is `binding_stale` or `fallback_stale`, never `complete`.
- "Same filename, different code" must show up as a hash mismatch, not a silent pass.

### 3.5 Conflict detection
The Switchboard never *infers* a conflict and never *infers* an authority. A conflict exists only when two or more registered records claim the same `authority_owner` scope for the same operation. Detection is a mechanical comparison of records; resolution is a human decision.

## 4. Authority model
**Authority is a hierarchy. Handshakes are a graph.**
- Authority to *establish* a relationship follows the hierarchy.
- Messages need not pass through every tier.
- Peers may share a parent without either being subordinate. Supporting contract: `docs/contracts/README_TIER_VS_LANE.md:23`, "TIER1 systems cannot overrule each other." `VERIFIED @ 567392ba`
- The Switchboard **resolves** registered authority; it never **decides** authority and never acquires domain logic.

### 4.1 Relationship to the existing relay law
A relay law already exists in the project's history: "Relay carries approved calls only," plus a list of prohibited relay behaviors (`scratch/CONTINUE_FROM_HERE.md @ 63fd347d`, L134–141). It is not in the current tree. The live relay (`ap_runtime_relay.py`) is stale and bypassed.

**Decision proposed:** the Switchboard **adopts** the relay law as its own constraint rather than becoming a second, competing routing layer.
- The relay law text is restored into `docs/contracts/` (location to be approved) with its source commit cited.
- The existing `ap_runtime_relay.py` is registered as a handshake in discovery with `binding_stale`, not deleted.
- Any place the Switchboard's behavior differs from the relay law is listed explicitly in the contract.

## 5. The supreme-authority question

### 5.1 First: "AP" is not one thing
Asking "AP or EngAInOS?" has no answer until it is clear which AP. At `567392ba` the repository contains at least:

| ID | What it is | Location / interface |
|---|---|---|
| **AP-ZW** | ZWAPEngine rule engine (APZWV.1) | port 8765 |
| **AP-CORE** | ap_core axiom checker | `ap_core.py` |
| **AP-GOV** | ap/0.1 governance registry behind `authority_gate` (EngAInOS's gate) | EngAInOS |
| **AP-CMD** | ap_complex_rules command vetting | port 8080 |
| **AP-ARB** | Engionality's SimpleAPEngine arbitration | `tier2/engionality/` |
| **AP-POLICY** | AP as an authority/arbitration policy concept in the architect's notes | Markor `ap policy.txt` |

All Python AP code sits under `tier1/engainos/aproom/`, physically inside EngAInOS. Physical location is evidence of *housing*, not of *authority*. Both are recorded separately.

Recoverable history relevant to AP (in git history and archive copies, removed by the 2026-06-24 cleanup commit): the May AP kernel prototype (`ap/ap_runtime.py`), the ap/0.1 rule-registry and action-classification contracts, two `.zon` rule files, and the default-rules `ap_engine.py`. These are discovery inputs, not current behavior.

Known AP defects, out of scope for the Switchboard but recorded so they are not confused with routing failures:
- **D1:** canonical door rule stopped firing after the 2026-03-01 rewrite.
- **D5:** deterministic tie-break existed in a second copy and was lost the same day.

### 5.2 Hypotheses with current evidence
| ID | Hypothesis | Evidence @ 567392ba | Leaning |
|---|---|---|---|
| **A1** | EngAInOS supreme; AP under its governance | `ENGAINOS_TIER1_AUTHORITY/ENGAINOS_AUTHORITY_MAP.md:22–30`: EngAInOS authoritative over "AP / contract gates … runtime acceptance" | Supported **for gate-style AP (AP-GOV)** only |
| **A2** | AP supreme over EngAInOS | `HUMAN_OVERRIDE_AUTHORITY_CONTRACT_v1.md` §5: an Overrule Event does not bypass AP validation | AP **validation** binds even human override; does not show AP governs EngAInOS |
| **A3** | Split jurisdiction under shared contract | `README_TIER_VS_LANE.md:23`: Tier 1 systems cannot overrule each other | Consistent; boundary contract not yet found |
| **A4** | Human operator is alpha; EngAInOS highest automated authority | `HUMAN_OVERRIDE_AUTHORITY_CONTRACT_v1.md` §3: Human outside tier structure as "originator" | Supported, **with caveat** below |

**Caveat on the human-override contract:** it opens with chat-style text, which suggests it may be a pasted AI conversation rather than a ratified contract. It must be confirmed by the architect (`ARCHITECT-STATED`) before it counts as binding.

**Working picture, not a decision:** the evidence so far is consistent with a layered model: the Human as originator (A4), EngAInOS governing the gate apparatus (A1, for AP-GOV), and AP validation acting as a constraint that even human override does not bypass (part of A2). This must be confirmed per AP variant and by the architect before anything is built on it.

### 5.3 Remaining investigation (read-only)
For **each** AP variant in §5.1:
1. Where does EngAInOS delegate to it?
2. Where does it decide without EngAInOS?
3. Can either override, veto, or bypass the other?
4. Is it live, stale, or historical at `567392ba`?

Plus, `ARCHITECT-STATED`:
5. Was AP's authority meant to cover EngAInOS, or only gameplay and simulation?
6. Is `HUMAN_OVERRIDE_AUTHORITY_CONTRACT_v1.md` ratified?
7. Which tier list is canonical (see §11, tier membership)?

## 6. Handshake lifecycle
| Stage | What happens | Exit evidence |
|---|---|---|
| **1. Trace** | Locate producer, consumer, call site, payload, return, transport | Paths + functions + content hashes at a commit |
| **2. Verify original** | Run the original as-is | Re-runnable test or run output |
| **3. Register** | Write the record (§8); routing unchanged | Record committed, all fields labeled |
| **4. Shadow** | Switchboard resolves in parallel; original still executes; results compared | Resolutions match on recorded runs |
| **5. Route** | Switchboard becomes default; original becomes fallback | Behavior unchanged on same tests |
| **6. Fallback test** | Switchboard disabled; fallback runs | Same result; fallback authorized |
| **7. Record** | Evidence preserved | Record marked `complete` |

Routing never changes before stages 1–2 complete.

## 7. Definition of done
A handshake is `complete` only when all five checks pass with re-runnable evidence:
1. **Behavior** — what happens is verified.
2. **Contract** — what crosses the boundary each way is verified. A passing test proves behavior, not interface; both are required.
3. **Authority resolution** — resolves to the correct owner; delegation source recorded.
4. **Safe fallback** — Switchboard disabled, fallback works **and** is authorized; binding and fallback both non-stale.
5. **Narrated** — participants introduce themselves and speak their actions per §16, with every spoken fact built from records; captured narration stored as evidence.

A started server, a resolved import, a placeholder that returns something, or a prior acceptance report is not `complete`.

## 8. Handshake record
| Field | Purpose |
|---|---|
| `handshake_id` | Stable logical name, independent of path |
| `family` / `version` | Functional grouping; contract version |
| `purpose` | Why the exchange exists |
| `producer` / `consumer` | Concrete participants, with roles |
| `contract_in` / `contract_out` | What crosses the boundary each way |
| `authority_owner` | Who decides; for AP, which variant (§5.1) |
| `authority_scope` | The operation(s) owned; used for conflict detection (§3.5) |
| `delegated_by` | Which higher authority granted ownership, with contract citation |
| `transport` | Import, file artifact, event, socket, stdout pipe, etc. |
| `switchboard_binding` | Resolved endpoint |
| `binding_hash` | Content hash (git blob or sha256) of the binding's code |
| `binding_status` | ok / stale / broken / untested |
| `absolute_handshake` | Original direct connection: file, function, path |
| `absolute_hash` | Content hash of the absolute handshake's code |
| `fallback_authorized` | true / false at last verification |
| `fallback_status` | ok / stale / broken / untested |
| `checks` | five checks, each with re-run command and result |
| `stage` | Lifecycle stage (§6) |
| `last_verified_commit` | Commit at which evidence was gathered |
| `history` | Binding, authority, and fallback changes |

Example records are marked `NON-AUTHORITATIVE`.

## 9. Pilot: one handshake
**Selection criteria:**
- Has a passing test or reproducible run
- One producer, one consumer
- Authority not contested; **no AP variant on either side** (given §5.1)
- Low blast radius; fully reversible
- Not dependent on a hot simulation tick path (keeps narration rules simple for the first proof)

**Pilot passes if:** all seven stages complete; all five checks pass; participating logic unchanged (diff shows routing and narration only, in separate commits); disabling the Switchboard falls back cleanly; re-enabling restores the preferred route; the roll call and session narration, with and without the Switchboard, meet §16.5.

**Pilot stops if:** a stage cannot produce evidence, behavior changes, or participating logic must change to make routing work. A stop is a finding; record it.

Only after the pilot passes is a second handshake attempted.

## 10. Authority boundaries
- **AP (all variants):** rule jurisdiction per variant (§5.1). The Switchboard does not invent or override AP decisions.
- **EngAInOS:** governance and acceptance; authoritative over gate-style AP per `ENGAINOS_AUTHORITY_MAP.md:22–30`.
- **GodotSim:** simulation; HP/damage paths need trace verification.
- **Engionality:** temporal/scheduling ownership unverified; hosts AP-ARB.
- **Mechanimation:** motion execution lane (`docs/contracts/SUPPORT_LANE_DISTRIBUTION/mechanimation_2ndlane_motion_execution/`); boundaries to be traced.
- **MrLore:** narrative/canonical authority not reassigned.
- **Trixel:** handshake boundary unverified; "Class 1 entry point" not found in repo text (§11).
- **Cartographer / Topologist:** inspected before declaring duplication.

A route is never permission to mutate authoritative state.

## 11. Verification table @ 567392ba
| Claim | Label | Evidence |
|---|---|---|
| Relays carry approved calls only | `VERIFIED` as historical doctrine; `CONTRADICTED` as live behavior | `scratch/CONTINUE_FROM_HERE.md @ 63fd347d` L134–141; relay bypassed; `ap_runtime_relay.py:47` stale path |
| Contracts live under `docs/contracts/` | `VERIFIED` | 50+ contract files grouped by tier folder |
| "All system calls must be Python imports" | `UNKNOWN` | Not found in repo; source not located. **Removed as a constraint** until a source is found |
| Engineality vs Engionality | `VERIFIED`: **Engionality** | `tier2/engionality/` |
| Mechanimation exists | `VERIFIED` | `mechanimation/*.pose.json`; contract folder under `SUPPORT_LANE_DISTRIBUTION/` |
| Tier 1/2/3 membership | `CONTRADICTED` (sources disagree) | Directories: tier1 = engainos, mrlore, paradox_machine; tier2 = cartographer, engionality, godotsim, topologist, worldfield. Human-override contract lists a different set, including Trixel, Mechanimation, and Trae (Trae retired 2026-07-04). Canonical list is an open decision |
| AP has absolute authority over game logic | `UNVERIFIED` | Depends on AP variant (§5.1) |
| Trixel Class 1 is the entry point | `UNKNOWN` | No "Class 1" text under Trixel paths |
| MythTech → EngAInHQ: working behavior replaced with connected-looking stubs | `ARCHITECT-STATED` | Architect's account, 2026-10-14; not repo evidence |
| AP code unchanged by the rehousing move | `VERIFIED` | Git content tracking: `ap_core.py`, `ap_zw_engine.py`, `ap_engine.py` changed only import lines and one label; `ap_runtime.py` changed two import lines |
| AP defects D1, D5 predate gates and the move | `VERIFIED` | Introduced 2026-03-01 rewrite |
| 2026-06-24 cleanup removed AP kernel prototype, ap/0.1 contracts, `.zon` rules, default `ap_engine.py` | `VERIFIED` | Commit "mrlore next"; recoverable from git history and archive copies |
| Repo history intact | `VERIFIED` | No resets/rebases in reflog; no commits missing vs other clones; archived AP files match historical versions |

## 12. Verification before proposal (anti-drift rule)

### 12.1 Rule
A proposal is not a proposal until all of it is verified. Applies to this specification.

### 12.2 What counts as evidence
- File path plus function/class/line range, read at a stated commit, with content hash where code identity matters
- Commit hash (history, moves, deletions)
- A test or check **re-run at the stated commit**, with its command and actual result
- Captured run output or log from an actual execution

**A prior report file is not evidence on its own.** Acceptance JSON, `ACCEPTED_*` flags, earlier gate outputs, memory, specs, filenames, and other agents' summaries are inputs to re-check. Earlier relay gates passed partly by reading `ACCEPTED_*` from previous gates' JSON; that pattern is prohibited.

### 12.3 Labels
| Label | Meaning |
|---|---|
| `VERIFIED` | Re-runnable evidence cited at a stated commit |
| `UNVERIFIED` | Not yet checked; may not be acted on |
| `CONTRADICTED` | Evidence shows the claim false or sources disagree |
| `UNKNOWN` | Could not be determined |
| `HYPOTHESIS` | A design proposition awaiting pilot evidence |
| `ARCHITECT-STATED` | Design intent or history from the architect that cannot be verified in code; binding as intent, but must not be presented as code behavior |

A proposal with any `UNVERIFIED` or `CONTRADICTED` claim in a load-bearing position is returned as a draft.

### 12.4 Checks must not alter what they check
Running a verification must not change the repository. Every existing AP gate writes into `scratch/` when it runs, so running them changes the tree being verified. Pilot checks and all future gates must:
- write only outside the repository, **or** to a single declared evidence directory excluded from the hashed paths, and
- leave `git status` unchanged for all tracked files after running.

### 12.5 Re-verification
Evidence is tied to a commit. If the repository changes before action, affected claims and hashes are re-checked. Names must match the repository exactly.

### 12.6 Agent handoff
Every AI-produced proposal ends with a verification table: claim, label, evidence, commit. Without it, the proposal is returned unreviewed.

## 13. Open decisions
1. Alpha authority, per AP variant (§5)
2. Ratification status of the human-override contract
3. Canonical tier membership (directory layout vs. human-override contract)
4. Where the restored relay law and Switchboard contracts live under `docs/contracts/`
5. How a caller knows its fallback is authorized when the Switchboard is down: (a) original runs as-is, trusted by last recorded verification, or (b) cached last-verified snapshot of bindings, hashes, and flags per subsystem
6. Shadow-mode comparison for file-based and asynchronous handshakes
7. Which handshake is the pilot
8. Approval authority for binding-only vs. authority or contract changes
9. Static manifest, runtime resolver, or both
10. Declared evidence directory location (§12.4)

## 14. Non-goals
- Rebuilding AP, EngAInOS, GodotSim, Engionality, Mechanimation, or Trixel
- Fixing AP defects D1/D5 (tracked separately)
- Restoring deleted gates; their checks were path-presence checks tied to old locations
- Assigning supreme authority by design rather than evidence
- Routing all traffic through a single relay
- Replacing ZW/ZON
- Treating a registry entry, started server, resolved import, or prior report as proof
- Wholesale reconstruction of EngAIn

## 15. Decision gate
**Authorized now:** read-only discovery (§5.3; tracing pilot candidates).  
**Requires approval:** selecting and running the single pilot (§9).  
**Not authorized:** routing any second handshake, assigning the alpha authority, or modifying any subsystem's logic until the pilot passes with evidence and results are reviewed.

## 16. Narration standard ("smart code, not loud code")
The system introduces itself. When it wakes, the Switchboard greets the operator and calls the roll. Each subsystem answers in its own voice: who it is, what it governs or does, who it works with, and where it leaves its work. During operation, each one says what it is doing and who it is doing it with.

Narration is **smart, not loud**. It speaks at decisions, handoffs, submissions, validations, refusals, and fallbacks. It does not narrate loop internals or every function call.

### 16.1 The words come from the code
No subsystem's introduction is a hand-written string. Every sentence is **constructed from the handshake records and the live code**:

| Spoken phrase | Built from |
|---|---|
| "I am Trixel" | `participant` identity in the registry |
| "I paint the world" | `purpose` field of its registered handshakes |
| "I'll need WorldField and the Topologist" | handshakes where it is `consumer` |
| "we will both submit to EngAInOS" | handshakes where it is `producer` and EngAInOS is `authority_owner` |
| "I validate what Trixel and Cartographer submit" | `authority_owner` + `authority_scope` + `delegated_by` |
| "I leave them in outputs/…" | artifact `transport` + binding path, checked to exist |

Only the **voice** (tone, sentence templates per subsystem) is authored. The **facts** in every sentence are filled from records at wake-up. Edit the records and the introductions change; there is no second copy to drift.

SEE ALSO APPEND_v0.3.md

### 16.2 Introductions check themselves
At roll call, every fact a subsystem is about to say is checked against the code before it is spoken (path exists, content hash matches, endpoint reachable). The verification label decides how it speaks:

| Label | How it sounds |
|---|---|
| `VERIFIED` | Stated plainly: "I submit spatial requests to EngAInOS." |
| `UNVERIFIED` | Hedged: "I believe I submit to EngAInOS, but nobody has checked." |
| `CONTRADICTED` | Flagged: "My records say I submit to EngAInOS, but that path is gone." |
| `UNKNOWN` | Honest: "I don't know who I report to yet." |
| stale binding/fallback | "My Switchboard line is stale; I'm on my direct line." |

The roll call is therefore a **spoken health check and a spoken blueprint**. If what a subsystem says about itself doesn't match what the architect expects, that mismatch *is* the drift, found at startup instead of weeks later.

### 16.3 Shape of a session (illustrative; roles, names, and paths are placeholders, not claims)
```text
[SWITCHBOARD] Hello. I'm the Switchboard. Hold on while I wake up the team...
[ENGAINOS]    Reporting for duty. I govern <scope>. <A> and <B> submit to me; I validate.
[<A>]         As requested. I <purpose>, but not alone: I need <C> and <D> first,
              then <B> and I submit to EngAInOS.
[<E>]         Don't bother me unless you need <scope>. I can see <source>.
[<F>]         I turn <input> into <formats>. I leave them in <path> (exists, 14 files).
[<G>]         I believe I report to EngAInOS, but nobody has verified that yet.
[SWITCHBOARD] Roll call done: 5 answered, 4 verified, 1 unverified, 0 stale. Shall we begin?

[<A>]         Asking <C> for world nuclei for region north_ridge...
[<C>]         Here: 3 nuclei, seed 4471.
[<A>]         Submitting tile request with <B> to EngAInOS.
[ENGAINOS]    Received from <A> and <B>. Validating... rejected: <B>'s bounds overlap reserved zone 7.
```

### 16.4 Rules
1. **Facts from records, voice from templates.** No subsystem may say anything about its role, partners, or outputs that is not filled from a registered record or a live check.
2. **Report what happened, not verdicts.** "Rejected: bounds overlap zone 7," never just "failed." "14 files in outputs/," never just "done."
3. **Say who.** Every action names the partner it was done with or for.
4. **Smart, not loud.** Speak at decisions, handoffs, submissions, validations, refusals, fallbacks, and stale detections. Hot per-tick paths speak at most once per tick, or as a periodic summary. Logs rotate or cap in size.
5. **One shared `narrate()` helper per language** (Python, GDScript): consistent speaker tags, adjustable volume, capturable to a log.
6. **Python narration goes to stderr**, so it never mixes into stdout used as a handshake transport.
7. **Summarize big payloads.** Shape and key values only; never credentials.
8. **Narration is evidence.** Captured roll calls and sessions from pilot, shadow, and fallback runs are stored with the handshake records in the declared evidence location (§12.4).
9. **Narration changes no logic.** Added in its own commits, separate from routing changes.

### 16.5 Pilot use
The pilot (§9) includes a roll call limited to the two participants in the piloted handshake. It passes when both introductions are generated entirely from records, each spoken fact is checked before it is spoken, and the session reads as a plain-language account the architect recognizes as correct.

## 17. Deletion manifest rule
The 2026-06-24 cleanup commit removed real work (AP kernel prototype, ap/0.1 contracts, `.zon` rules, default `ap_engine.py`) along with clutter. Nothing was lost permanently, but the deletion was a side effect, not a decision.

Any commit that moves, renames, rehouses, or deletes files must be preceded by a **deletion manifest**:
- every file the commit removes or relocates, with its content hash;
- a one-line description of what each removed file contained;
- for each, a disposition: `deleted-intentionally`, `moved-to <path>`, or `archived-at <path>`;
- registered handshakes whose binding or fallback the commit affects.

The manifest is reviewed before the commit. A removal without a manifest entry is treated as an error, not a cleanup.
