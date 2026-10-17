# EngAIn Authority Findings — 2026-10-17

**Checkpoint, not a contract.** Records what the authority audit established so
work can resume from here. It grants no authority and binds no subsystem.
Nothing described here has been repaired.

Written at EngAIn `ac87402b` (plus staged, uncommitted archive moves — §9).
Follows `ENGAIN_ARCHITECTURE_BASELINE_2026-10-16.md`, which stays unedited as
history. Where the two disagree on authority, the doctrine in §1 is newer.

Evidence labels:

| Label | Meaning |
|---|---|
| **TESTED** | Exercised in-process from a scratch copy on 2026-10-17 (§6) |
| **STATIC** | Established by reading code or git history; not executed |
| **HISTORICAL** | From git history or the 06-14 pre-move copy |
| **ARCHITECT** | Stated by the architect in this session |
| **OPEN** | Not established |

---

## 1. Doctrine (ARCHITECT, 2026-10-17)

- **The story (manuscript) is canon and the only authority.** It must be preserved.
- **Neither the human nor Dragon holds authority** inside EngAIn; either could damage the world.
- The human's only lever: **rewrite the book and re-run it.**
- If EngAIn produces a wrong result, that is **a system bug to fix in code**, never something corrected by editing a scene or generated output.
- Trae and clutterbot are retired as authority candidates; MrLore's role shrinks as EngAIn grows.

Consequence for this document: anything that grants a "human root" or lets an
actor override canon is recorded as superseded design, not as missing
functionality.

---

## 2. Historical design (HISTORICAL)

These existed and were removed from the tree. None were restored.

| Item | Last tree location | Removed | Survives in |
|---|---|---|---|
| `AUTHORITY_TIER_SPEC_v1.md` ("FROZEN") | `godotengain/engainos/docs/architecture/` | `c0b6bc6a` 06-24 | git; pre-move copy; Feb extracted copy |
| `ACTION_CLASSIFICATION_CONTRACT_v1.md` | `godotengain/engainos/docs/` | `c0b6bc6a` | git; pre-move copy |
| `AP_RULE_REGISTRY_CONTRACT_v1.md` | `godotengain/engainos/docs/` | `c0b6bc6a` | git; pre-move copy |
| `CLIENT_AUTHORITY_BOUNDARY.md` | `godotengain/engainos/` | `c0b6bc6a` | git only |
| `rules/runtime_mutation/reality_mode_gate.zon`, `replay_blocks_all.zon` | `godotengain/engainos/rules/` | `c0b6bc6a` | git; pre-move copy |
| `tests/test_authority_spec_v1.py` | `godotengain/engainos/tests/` | `c0b6bc6a` | git; pre-move copy |
| `empire_agent_gateway.py` | `core/` → `archive/legacy_core/` (`f4066e2a` 06-13) | `c0b6bc6a` | git; Feb extracted copy |
| `ENGAINOS_RUNTIME_AUTHORITY_CONTRACT_v1.md` | `docs/` | `8e3af2a1` 06-17 | git; pre-move copy |

Pre-move copy: `/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn` @ `f7a911f` (06-14).
Read from git with e.g. `git show c0b6bc6a^:godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`.

What the historical design required:

- Tiers 0 System, 1 AI agent, 2 Human operator, 3 Human root; tier × reality-mode matrix (REPLAY blocks all; FINALIZED needs Tier 3).
- **"Tier is injected externally"; no actor may self-promote.**
- Rejected → Intent Shadow; accepted → history (canonical in FINALIZED).
- EngAInOS, not the caller, classifies actions; unknown actions fail closed; legacy `command` is deliberately unknown.
- `reality_mode_gate.zon` was the only place `actor_authority_tier >= action.required_tier` was checked.
- Authority proof must run without Godot.

**Conflict with §1:** the spec's Tier 2/3 human authority and Tier-3 mutation of FINALIZED contradict the doctrine. Its closing line, "Canon outranks convenience," agrees with it.

---

## 3. Migration findings

- **Process (ARCHITECT):** assign tiers → move files and run until nothing was reported missing → split systems into rooms (`aproom`, …) → bring in outside tools (e.g. Paradox Machine) → leftovers into `out of root/`. Nothing was intentionally deleted.
- **Repo is no longer the whole project (ARCHITECT):** the Godot project lives in `~/Downloads` on purpose.
- **`out of root/` is not a complete inventory (STATIC):** committed 07-15 (`7e78e1a0`). None of the §2 items are in it (content-hash search of the whole tree). They stayed in old `godotengain/`, which git dropped in `c0b6bc6a`.
- **Why the run-until-it-works method missed them (STATIC):** the rules folder is read only when a mutating action reaches 8090; specs and tests never load at startup. Nothing failed, so nothing pointed at them.
- **Verification drifted from the engine (STATIC):** of 38 gates in `tier1/engainos/gates/`, 26 reference pre-tier paths. Every missing *implementation* path has a current counterpart (moved, not lost); the rest are gate outputs, scratch dirs, or candidate names. 22 of the 26 are labelled ACTIVE. All last modified 06-25. Survey: scratchpad `gate_survey.txt` (§10).

---

## 4. Current implementation (as of `ac87402b`)

### 4.1 Actor identity — STATIC

No authentication anywhere. `actor_id` and `actor_authority_tier` are read from the request body (`tier2/godotsim/runtime_gateway.py:138-149`; `tier1/engainos/aproom/authority_gate.py:531`). Self-assigned Tier 3 is sent by Godot Semantic `SimClient.gd:21` and the Trixel executor (`executors/trixel32d_apply_authorization_export_v1.py:62,215,242`).

### 4.2 Surfaces

| Surface | Checks performed | Label |
|---|---|---|
| 8090 `/api/command` → `authority_gate.evaluate` | required fields; action classification; AP registry for mutating/unknown actions | TESTED |
| 8090 combat/inventory/dialogue routes | none (`engainos_server.py:310-375`) | STATIC |
| 8080 `/command` + legacy combat/inventory/dialogue → `RuntimeGateway` | identity fields present; REPLAY; FINALIZED needs tier ≥ 3; gameplay complex rules | TESTED |
| 8080 `/scene/load` | identity; REPLAY; scene-level FINALIZED only (`http_handlers.py:401-438`) | STATIC |
| 8080 `/embodiment/apply`, `/vault/link`, `/world/sync`, `/world/load_mirror` | none | STATIC |
| 8765 AP runtime (`launch_engine.py:179-215` → `aproom/ap_runtime.py`) | execute needs `allow_execute`; timeline write needs runtime config + message; history read needs `allow_history_read` | TESTED in-process; HTTP route STATIC (`scene_server.py:285-286`) |
| Trixel apply gate (`gates/gate_trixel32d_surface_apply.py`) | packet vs "trusted authority evidence"; evidence produced by the same executor with hard-coded Tier 3 | STATIC |
| Presence / session claims (`core/presence_registry.py`, `session_claim_registry.py`) | conversation-session identity only; no world-mutation policy | STATIC |

### 4.3 Decision propagation — STATIC

- 8080 rejections → `IntentShadow`, in memory only (`core/intent_shadow.py:45`); lost on restart.
- 8090 rejections → not recorded.
- Accepted actions → not recorded anywhere. `history_xeon.commit_event` has no live caller (the old Empire gateway called it).
- FINALIZED never occurs: `canon.finalize_scene` and `reality_mode.set_mode` have no live callers; both stores are in memory.

---

## 5. Disconnected or unconnected components — STATIC

Present in the tree, not on any live path. Whether each was meant to be connected is OPEN.

| Component | State |
|---|---|
| `aproom/authority_validator.py` (spec matrix) | no callers; gate TODO at `authority_gate.py:548-550` |
| `relays/ap_runtime_relay.py` | no live caller; its target `godotengain/engainos/core/ap_runtime.py` (`:46-47`) does not exist |
| `server/safe_runtime_server_entrypoint.py` | imported only by `server/__init__.py`; `start_stack.fish:130` runs `tier2.godotsim.sim_runtime` instead |
| `core/history_xeon.py` `commit_event` | no live caller |
| `core/no_godot_scene_proof.py` | present; the test that ran it is gone |

---

## 6. Test evidence (TESTED, 2026-10-17)

Method: `tier1/` and `tier2/godotsim/runtime_gateway.py` copied to the scratchpad; probe run in-process with `python3 -I`; no servers, no ports; no files created in the copy; repo unchanged. Script: scratchpad `livefence/probe.py` (§10). The 8080 gateway ran with a stand-in runtime and dispatcher.

| Case | Result |
|---|---|
| 8765 execute, no `allow_execute` | rejected `execution_intent_required` |
| 8765 execute + timeline write requested | rejected `timeline_write_not_allowed` |
| 8765 execute with `allow_execute: true` | accepted (flag is caller-supplied) |
| 8765 history read without / with flag | rejected / accepted |
| 8765 rules loaded from `tier1/engainos/game_scenes/` | **0** |
| Gameplay rules on live `/combat/damage` shape (`source/target/damage`), attacker 5 HP | no rule fires |
| Same, self-attack | no rule fires |
| Gameplay rules on `attacker/target/amount` shape | `rule_attacker_min_health` / `rule_cannot_attack_self` fire |
| 8080 live combat shape, weak attacker | accepted, dispatched |
| 8080 `reality_mode: "LIVE"` | accepted as DRAFT |
| 8080 `actor_authority_tier: 99` | accepted |
| 8080 missing identity / REPLAY / FINALIZED at tier 1 | rejected |
| 8080 FINALIZED with self-claimed tier 3 | accepted |
| 8090 `look` (also under REPLAY) | allowed |
| 8090 `load_scene`, `command` | **crash**: `APRuleLoadError: AP registry not found …/tier1/engainos/rules/runtime_mutation` |

### 6.1 The empty AP rule set

The 8765 AP runtime loaded 0 rules. It reads `scene["rules"]` and converts `scene["events"]` (`ap_runtime.py:249-258`). `git log -G` over the game-scene paths finds no history of AP rules in those files. **There is no evidence these rules ever existed**, so this is not recorded as missing functionality. AP policy may have been deferred until the other systems were integrated (OPEN).

---

## 7. Reproducible defects (prioritized; none fixed)

| # | Defect | Repro | Label |
|---|---|---|---|
| D1 | 8090 crashes on any mutating or unknown action instead of refusing | `evaluate({...,"action":"load_scene"})` → `APRuleLoadError`; cause: registry dir dropped in `c0b6bc6a` | TESTED |
| D2 | Caller-assigned tier accepted without bounds or identity; self-claimed tier 3 passes FINALIZED | 8080 body with `actor_authority_tier: 99`, or `3` + `reality_mode: FINALIZED` → accepted | TESTED |
| D3 | Gameplay AP rules never match the live combat request | `/combat/damage` sends `source/target/damage` (`runtime_client.py:103-104`); rules expect `attacker/amount` (`ap_complex_rules.py:143-153`); gateway checks before the dispatcher renames fields (`command_dispatcher.py:83`) | TESTED |
| D4 | Unknown `reality_mode` silently becomes DRAFT | `reality_mode: "LIVE"` (what Godot sends) → DRAFT (`runtime_gateway.py:138-139`) | TESTED |
| D5 | Mutating routes with no gate | 8080 `/embodiment/apply`, `/vault/link`, `/world/sync`, `/world/load_mirror`; 8090 combat/inventory/dialogue | STATIC |
| D6 | AP rule exceptions swallowed in the 8080 gateway (fails open) | `runtime_gateway.py:268-279` prints and continues | STATIC |
| D7 | `/scene/load` skips the global and per-request FINALIZED checks `/command` performs | `http_handlers.py:401-438` vs `runtime_gateway.py:246-259` | STATIC |
| D8 | 8765 execute/history intent is caller-declared | `allow_execute: true` → accepted (harmless today: 0 rules, timeline write off) | TESTED |
| D9 | Decisions not durable: 8090 rejections unrecorded; IntentShadow in memory; accepts never logged | §4.3 | STATIC |
| D10 | 22 ACTIVE gates check pre-tier paths | §3 survey | STATIC |
| D11 | `canon.can_edit` returns True for scenes it has never seen | `aproom/canon.py:107-113` | STATIC |
| D12 | Reality-mode helpers disagree: `RealityContext.is_editable()` blocks FINALIZED even at tier 3; `allows_mutation()` and the matrix do not; `TEST` mode exists in code but not in the matrix | `aproom/reality_mode.py:24-35,52-54,68-70`; `authority_validator.py:45-46` | STATIC |

D1–D4 are the most direct contradictions of "nothing changes runtime state unless EngAInOS allows it." No defect here permits writing canon history: the timeline fence held (§6).

---

## 8. Proposed repairs — NOT DECIDED

Placeholder only. No repair is approved, and none should restore human-root override (§1). Each needs an architect decision first:

- What `actor_authority_tier` means under §1: removed, reduced to system-vs-requester, or assigned by EngAInOS rather than the caller.
- Whether REPLAY and tier-vs-action checks live in AP rule files or in code.
- Which gate is canonical for runtime mutation: 8090 `authority_gate` or 8080 `RuntimeGateway`.
- Whether the AP relay and the safe 8080 entrypoint were intended replacements or deliberate experiments (§5).
- Whether FINALIZED should be read-only to every actor, with change only via re-running the manuscript.
- Whether runtime/gameplay state (inventory, combat) is governed separately from canon.

---

## 9. Changes made in this session (outside the audit itself)

Staged, not committed:

- `tier1/engainos/core/agent_gateway.py` → `tier1/engainos/archive/retired_agents/`
- `tier1/engainos/core/trae_observer.py` → `tier1/engainos/archive/retired_agents/` (already unimportable from `core/`: `from .reality_mode`)
- `tier1/mrlore/schema/TRAE_MRLORE.md` → `docs/contracts/SUPPORT_LANE_DISTRIBUTION/retired_agents/`
- `docs/contracts/human_external_originating_authority/` → `docs/contracts/archive/`
- New notes: `tier1/engainos/archive/retired_agents/README.md`, `docs/contracts/archive/README.md`

References left pointing at old locations: `AGENTS.md`, `HANDSHAKES.md` (not edited by rule); `PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md` and `SHARED_SESSION_CONTINUITY_CONTRACT_v1.md` (name `agent_gateway.py` as "Gate 1"); the Switchboard spec v0.3 §5 (cites the human-override contract).

Not staged:

- `out of root/premigration_home_2026-02/`: 382 reflink copies from the extracted Feb workspace, made by mistake during an off-track recovery step. **Deleted 2026-10-17**, and its `.git/info/exclude` entry removed. Before deletion, all 382 files (and every non-`.git` file of the extracted folder) were verified byte-identical inside the source archive `/run/media/mytruelove/storage1/pop/burdens_of_a_forgotten_past.tar.gz` (Feb 24, 16.5 GB, read cleanly to end). The overflow-drive `burdens_of_a_forgotten_past.tar.gz` (Oct 6) is a post-migration backup and does not contain them.
- `~/burdens_of_a_forgotten_past/`: the architect's extraction of that archive, a reference copy of the pre-migration layout; removal left to the architect. Its accidental commit `cb7dffd` and failed push/pull never touched this repository or the remote.
- This document and the 10-16 baseline: untracked.

---

## 10. Remaining uncertainties

- The 8765 HTTP route was not exercised over HTTP; 8080 was exercised with a stand-in dispatcher.
- Whether the 22 ACTIVE gates actually fail when run (expected; not run).
- Whether the import-boundary rules inside the migration gates still hold.
- Whether the Godot project in `~/Downloads` still points at pre-tier EngAIn paths.
- The 12 gates that passed the path survey were not reviewed.
- Engionality's AP arbitration engine, MrLore's own gates and `ap_complex_rules` beyond the two built-in rules were not audited.
- Whether AP policy for scenes was ever written, or deliberately deferred (§6.1).

Evidence scripts (disposable) in the Claude scratchpad for session `187e26dc-…`:
`gate_survey.txt`, `livefence/probe.py`, `stray_diff/` —
`/mnt/data-drive/EngAIn_Recovery/07_TMP/claude-1000/-home-mytruelove-Desktop-burdens-of-a-forgotten-past-EngAIn/187e26dc-63a6-445c-aff9-b5dc25bd03c3/scratchpad/`.
Everything needed to resume is in this file.
