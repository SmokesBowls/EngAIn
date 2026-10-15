# EngAIn Handshake Switchboard
## Architecture Specification v0.2 — Hypothesis and Discovery Plan
**Date:** 2026-10-15  
**Supersedes:** v0.1 (2026-10-14)  
**Status:** Hypothesis. Not implemented. Not authorized for repository modification beyond read-only discovery and the single pilot in Section 9 once approved.

> **ANTI-DRIFT RULE (binding on every reader, human or AI):** Nothing in this document, and nothing proposed from it, is true until verified against the actual repository. Every claim carries evidence before a proposal is accepted as what it says it is. See Section 12.

> **Terminology note:** Names used here (Switchboard, absolute handshake, alpha authority, tiers, rooms, subsystem names) are working terms chosen by the architect. They are not settled vocabulary. Where the repository already uses a different name for the same thing, the repository's name wins and this spec is updated.

---

## 1. Problem
EngAIn's subsystems connect through direct handshakes scattered across files: imports, paths, payload assumptions, adapters. Three different concerns are tangled together inside those handshakes:

| Concern | Question it answers |
|---|---|
| **Identity** | What is this subsystem and what does it do? |
| **Authority** | Who is responsible for deciding this operation? |
| **Routing** | How does a request physically reach that subsystem? |

Because authority is embedded in routing, it is **invisible**. No single place shows who owns what. AI agents repair or replace one connection, unknowingly change who decides something, and break an established chain. This is the drift problem.

## 2. Core hypothesis
Each statement below is labeled `HYPOTHESIS` until the pilot (Section 9) produces evidence.

- **H-SW1.** A central Switchboard can hold the authority and routing map for EngAIn's handshakes without owning any domain logic. `HYPOTHESIS`
- **H-SW2.** Existing direct handshakes ("absolute handshakes") can be kept intact and demoted from *default* route to *fallback* route. `HYPOTHESIS`
- **H-SW3.** Tracing and registering handshakes one at a time will reconstruct EngAIn's real architecture (the blueprint) from working machinery, instead of imposing a new design onto it. `HYPOTHESIS`
- **H-SW4.** Once handshakes are registered, authority corrections can be made at the Switchboard instead of across every participating file. `HYPOTHESIS`

The Switchboard is the **deliberate breaking point**. If it fails, the system does not stop. It falls back to the handshakes that exist today.

## 3. Operating model

### 3.1 Normal operation
```text
Subsystem ──► Switchboard ──► resolved handshake ──► authorized handler
```

### 3.2 Switchboard unavailable
```text
Subsystem ──► original absolute handshake ──► handler
```

The absolute handshake is the direct connection the subsystem already has, or should have, today. It is preserved, not rewritten. Its role changes from default to fallback.

### 3.3 Failure modes
Different failures get different responses. "Still works" is not the same as "still authorized."

| Condition | Response |
|---|---|
| Switchboard unavailable (outage) | Use the absolute handshake **only if** it is marked `fallback_authorized` at its last verification |
| Known authority conflict (two producers claim the same decision) | **Fail closed.** Do not route. Flag for human review |
| Switchboard corrected an authority, and the absolute handshake still points to the old authority | That fallback is **not authorized**. Fail closed on that handshake until the fallback is updated and re-verified |
| Handshake not yet registered | Unchanged: original direct path runs exactly as it does today |
| Absolute handshake broken (e.g., subsystem moved) | Flag as `fallback_stale`. Switchboard route continues; fallback must be repaired and re-tested before it counts |

### 3.4 Fallback staleness
Absolute handshakes contain hard paths. When a subsystem moves, the Switchboard binding is updated, but the fallback can silently go stale. Therefore:
- Every migration updates the Switchboard binding **and** re-tests the fallback.
- A handshake whose fallback has not been re-verified since the last move is labeled `fallback_stale`, never `complete`.
- How a caller knows its fallback is authorized when the Switchboard is down is an open decision (Section 13).

## 4. Authority model
**Authority is a hierarchy. Handshakes are a graph.**

- Authority to *establish* a relationship follows the hierarchy: some authority must permit the connection.
- Messages do *not* have to pass physically through every tier. Two systems at the same level may exchange data directly once that relationship is authorized.
- Two systems may share a parent authority without either being subordinate to the other.
- The Switchboard **resolves** registered authority relationships. It never **decides** who deserves authority and never acquires a domain's logic. If AP owns a combat rule, the Switchboard routes to AP. It cannot redefine the rule.

Illustrative only, not verified against the repository:
```text
Alpha authority          top-level governing contract (identity: UNKNOWN, see §5)
  Tier 1                 governance, authorized delegation
  Tier 2                 domain responsibilities
  Tier 3                 execution, bounded handoffs
Switchboard              resolves relationships across these; owns none of them
```

## 5. The supreme-authority question (OPEN)
It is not known whether AP or EngAInOS holds supreme authority. This spec does **not** assign it. Four hypotheses are on the table:

| ID | Hypothesis | What would support it |
|---|---|---|
| **A1** | EngAInOS is supreme; AP operates under its governance | EngAInOS authorizes or can veto AP; AP cannot instruct EngAInOS |
| **A2** | AP is supreme; EngAInOS is subject to AP rules | EngAInOS consults AP before governance actions; AP rules constrain engine lifecycle |
| **A3** | Split jurisdiction under a shared architectural contract: EngAInOS governs the engine (lifecycle, registration, tier relationships), AP governs game logic (rules, state transitions) | Neither overrides the other; each defers within the other's domain; a written contract defines the boundary |
| **A4** | The human operator is the alpha; EngAInOS is the highest *automated* authority | Acceptance or override paths require human approval; "operator is part of the architecture" appears in contracts |

AP being newest does not make it subordinate, and AP being designed as "absolute" does not make it supreme over the engine. Absolute authority *within a jurisdiction* and supreme authority *over the system* are different things.

### 5.1 Investigation (read-only)
1. Find every place EngAInOS delegates to AP.
2. Find every place AP issues instructions or decisions without EngAInOS involvement.
3. Find any place either one can override, veto, or bypass the other.
4. Find any written contract defining their boundary.
5. Record the architect's original design intent: was AP's authority meant to cover EngAInOS, or only gameplay and simulation?

Result is labeled per Section 12. Until then, the alpha is `UNKNOWN` and nothing is built that depends on it.

## 6. Handshake lifecycle
Each handshake moves through these stages individually. No stage is skipped. Routing never changes before the original is traced and verified, because changing it first would obscure the behavior being discovered.

| Stage | What happens | Exit evidence |
|---|---|---|
| **1. Trace** | Locate producer, consumer, call site, payload, return, transport | File paths + functions cited at a commit |
| **2. Verify original** | Run the original handshake as-is | Test or run output proving current behavior |
| **3. Register** | Write the record (Section 8); route unchanged | Record committed; all fields labeled |
| **4. Shadow** | Switchboard resolves the route in parallel; **original still executes**; results compared | Switchboard resolution matches original target on recorded runs |
| **5. Route** | Switchboard becomes default; original becomes fallback | Behavior unchanged on the same tests |
| **6. Fallback test** | Switchboard deliberately disabled; fallback runs | Fallback produces same result and is authorized |
| **7. Record** | Evidence preserved as permanent verified record | Section 8 record marked `complete` |

The shadow stage is how routing through the Switchboard reveals the blueprint without risk: the Switchboard watches before it drives.

## 7. Definition of done
A handshake is `complete` only when all five checks pass and their evidence is recorded:

1. **Behavior** — what happens is verified (e.g., an attack reduces HP by the expected amount).
2. **Contract** — how another system invokes it is verified: what crosses the boundary in, what comes back. A passing test proves behavior, not the interface; both are required.
3. **Authority resolution** — the Switchboard resolves to the correct authority owner, and the owner's delegation source is recorded.
4. **Safe fallback** — with the Switchboard disabled, the absolute handshake works **and** is authorized.
5. **Narrated** — every step of the handshake speaks in the CLI per Section 16, and the captured narration is saved as run evidence.

A server that starts, an import that resolves, or a placeholder that returns something is not `complete`. Later changes are tested against this record; an agent cannot replace working behavior with a stub and claim success.

## 8. Handshake record
| Field | Purpose |
|---|---|
| `handshake_id` | Stable logical name, independent of path |
| `family` / `version` | Functional grouping; contract version |
| `purpose` | Why the exchange exists |
| `producer` / `consumer` | Concrete participants, with roles |
| `contract_in` / `contract_out` | What crosses the boundary each way |
| `authority_owner` | Who decides this operation |
| `delegated_by` | Which higher authority granted that ownership |
| `transport` | Import, file artifact, event, socket, etc. |
| `switchboard_binding` | Current resolved endpoint |
| `absolute_handshake` | Original direct connection: file, function, path (preserved evidence) |
| `fallback_authorized` | true / false, as of last verification |
| `fallback_status` | ok / stale / broken / untested |
| `checks` | behavior / contract / authority / fallback, each with evidence |
| `stage` | Lifecycle stage from Section 6 |
| `last_verified_commit` | Commit at which evidence was gathered |
| `history` | Binding, authority, and fallback changes |

Example records must be marked `NON-AUTHORITATIVE` and must not be mistaken for real handshakes.

## 9. Pilot: one handshake
Do not route everything through the Switchboard. Prove the idea on one handshake first.

**Selection criteria:**
- Already has a passing test or a reproducible run
- One producer, one consumer
- Authority **not** contested (not an AP-vs-EngAInOS boundary)
- Low blast radius if it breaks
- Fully reversible

**Pilot passes if:**
- All seven lifecycle stages complete with evidence
- All five checks in Section 7 pass
- The CLI narration of a full run, with and without the Switchboard, reads as a step-by-step account a non-programmer can follow
- Participating subsystems' logic is unchanged (diff shows only routing changes)
- Disabling the Switchboard falls back cleanly
- Re-enabling the Switchboard restores the preferred route

**Pilot stops if:** any stage cannot produce evidence, behavior changes, or the participating logic has to be modified to make routing work. A stop is a finding, not a failure; record what was learned.

Only after the pilot passes is a second handshake attempted.

## 10. Authority boundaries (carried from v0.1)
- **AP:** declarative rule jurisdiction. The Switchboard does not invent or override AP decisions.
- **EngAInOS:** governance and acceptance responsibilities. Final interface recovered from code.
- **GodotSim:** simulation; HP/damage paths need historical and current trace verification.
- **Engineality / Engionality:** temporal/scheduling ownership unverified; name itself unverified (see §11).
- **MrLore:** narrative/canonical authority not reassigned.
- **Trixel:** Class 1 entry/handoff boundary respected; internal class delegation not bypassed.
- **Cartographer / Topologist:** spatial roles inspected before declaring duplication.

A route is never permission to mutate authoritative state.

## 11. Claims requiring verification before use
These appear in prior notes, chats, or AI reviews. All are `UNVERIFIED` until checked against the repository.

| Claim | Why it matters |
|---|---|
| EngAInOS already owns request routing / "Relays carry approved calls" | Switchboard may duplicate an existing relay mechanism |
| Contracts canonically live under `docs/contracts/` | Likely home for Switchboard contracts |
| "All system calls must be Python imports" | Conflicts with file/event/socket transports unless scoped |
| Subsystem spelled *Engineality* vs *Engionality* | Name mismatch; one subsystem or two |
| "Mechanimation" exists as a subsystem | Named in AI review; not in v0.1 |
| Tier 1 / 2 / 3 structure and membership | Basis of the authority hierarchy |
| AP has absolute authority over game logic | Basis of hypotheses A2 / A3 |
| Trixel Class 1 is the entry point | Determines Trixel's handshake boundary |
| MythTech → EngAInHQ failure was caused by replacing working behavior with connected-looking stubs | Cited as the cautionary precedent; confirm the lesson |

## 12. Verification before proposal (anti-drift rule)

### 12.1 Rule
A proposal is not a proposal until all of it is verified. Every claim in any proposal, plan, inventory, handshake record, or migration step is checked against the current repository before acceptance. This applies to this specification.

### 12.2 What counts as evidence
- File path plus function, class, or line range, read at the current revision
- Commit hash (history, moves, deletions)
- Test name and actual result
- Captured run output or log

Memory, "it was designed to," prior specs, filenames, and other agents' summaries are **inputs to check**, not evidence. When they disagree with the code, the code wins and the discrepancy is recorded.

### 12.3 Labels
`VERIFIED` · `UNVERIFIED` · `CONTRADICTED` · `UNKNOWN` · `HYPOTHESIS`

A proposal with any `UNVERIFIED` or `CONTRADICTED` claim in a load-bearing position is returned as a draft.

### 12.4 Re-verification
Evidence is tied to a commit. If the repository changes before action, affected claims are re-checked. Names must match the repository exactly.

### 12.5 Agent handoff
Every AI-produced proposal ends with a verification table: claim, label, evidence, commit. Without it, the proposal is returned unreviewed.

## 13. Open decisions
1. Who is the alpha authority? (Section 5)
2. Does an existing EngAInOS relay or routing mechanism already serve part of this role?
3. Where does the Switchboard live? (`docs/contracts/` is the default to beat.)
4. How does a caller know its fallback is authorized when the Switchboard is down?
   - (a) The original absolute handshake runs as-is, trusted by its last recorded verification
   - (b) Each subsystem holds a cached last-verified snapshot of its bindings and authorization flags
5. How is shadow-mode comparison performed for file-based or asynchronous handshakes?
6. Which handshake is the pilot?
7. Who approves binding-only changes versus authority or contract changes?
8. Static manifest, runtime resolver, or both?

## 14. Non-goals
- Rebuilding AP, EngAInOS, GodotSim, Engineality, or Trixel
- Assigning supreme authority by design rather than by evidence
- Routing all traffic through a single relay
- Replacing ZW/ZON or reinterpreting the semantic protocol
- Treating a registry entry, a started server, or a resolved import as proof of a working handshake
- Wholesale reconstruction of EngAIn

## 15. Decision gate
**Authorized now:** read-only discovery (Section 5.1 investigation; tracing for pilot candidates).  
**Requires approval:** selecting and running the single pilot (Section 9).  
**Not authorized:** routing any second handshake, assigning the alpha authority, or modifying any subsystem's logic, until the pilot passes with evidence and the results are reviewed.

## 16. Narration standard ("smart coding")
Every file the Switchboard touches talks. Running it in the CLI should read like a conversation with the system: what it received, what it is deciding, why, what it did, and what came back. Silence is treated as a defect.

### 16.1 What gets narrated
Every handshake narrates every step, including:
- **Received** — who called, which `handshake_id`, a short summary of the payload
- **Resolving** — what the Switchboard is looking up
- **Resolved** — which handler was chosen, and *why* (authority owner, who delegated it)
- **Calling** — the exact endpoint or absolute path being used
- **Returned** — what actually came back (values, counts, file written)
- **Fallback** — loudly: that the Switchboard was unavailable, which absolute handshake is being used, and whether it is authorized
- **Refused** — authority conflict, unauthorized fallback, schema mismatch, with the reason
- **Shadow** — in shadow stage, both the Switchboard's answer and the original's answer, and whether they match

### 16.2 Example (illustrative only)
```text
[SWITCHBOARD] Request in: simulation.damage_result from GodotSim (attacker=wolf_02, target=player, raw=14)
[SWITCHBOARD] Looking up who decides damage... registry says AP owns it, delegated by EngAInOS (verified @ a1b2c3d)
[SWITCHBOARD] Routing to AP at ap/combat/damage.py::resolve_damage
[AP]          I got the attack. Applying armor rule: 14 - 2 = 12
[AP]          Returning: target=player, hp_delta=-12
[SWITCHBOARD] Got hp_delta=-12 back. Handing it to GodotSim.
[SWITCHBOARD] *** I'M DOWN. Caller should use its absolute handshake. ***
[GODOTSIM]    Switchboard unreachable. Falling back to absolute path ap/combat/damage.py (fallback_authorized=true, last verified a1b2c3d)
```

### 16.3 Rules
1. **Report facts, not verdicts.** Print the value, path, or count that was observed. Never print "success," "connected," or "done" without the evidence beside it. A file announcing it worked is not proof it worked, and a stub must not be able to narrate its way to `complete`.
2. **Say why.** Every routing decision states the authority reason, not just the destination.
3. **One shared helper per language.** Use a single `narrate()` helper in Python and one in GDScript, not scattered bare `print()` calls. That gives consistent tags, lets volume be turned down for production runs, and lets narration be captured to a log file.
4. **Narration goes to stderr (Python).** Any handshake that passes data through stdout (subprocess pipes, CLI tools whose output another tool reads) must not have narration mixed into its payload. Which handshakes use stdout as transport is a verification target.
5. **Summarize big payloads.** Print shape and key values, not entire scene packages or vault documents. Never print credentials or secrets.
6. **Narration is evidence.** Captured narration from pilot runs, shadow comparisons, and fallback tests is stored with the handshake record and counts as run output under Section 12.2.
7. **Adding narration changes no logic.** Narration is added in its own commits, separate from routing changes, so a diff review can confirm behavior was untouched.
