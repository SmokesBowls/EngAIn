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

## 6A. Simulation (MR) kernels and the combat path

Pure snapshot-in/snapshot-out kernels; adapters queue deltas and call them once per tick.

### 6A.1 Inventory — STATIC unless marked

| Kernel (`tier2/godotsim/kernels/`) | Responsibility | Called by the live tick? | Other importers |
|---|---|---|---|
| `spatial3d_mr` | positions / velocities | **yes** (`runtime_core.py:390`) | — |
| `perception_mr` | visibility / hearing | **yes** (`runtime_core.py:410`) | — |
| `behavior3d_mr` | NPC behaviour | **yes**, via `BehaviorStateView` (`runtime_core.py:424-428`) | — |
| `combat3d_mr` | damage, health, died / low-health alerts (`step_combat`) | **no** | `bridgeroom/zon_bridge.py`, `core/replay.py`, tier1 shim — none live |
| `inventory3d_mr` | take / drop / wear / load | **no** (adapter built, `tick()` never called) | — |
| `dialogue3d_mr` | dialogue / reputation | **no** (same) | — |
| `navigation_mr` | pathing | **no**; no runtime ever imported it (git `-S`) | `adapters/navigation_adapter.py` (unimported) |
| `quest3d_mr` | quest state | **no**; never runtime-wired | `bridgeroom/quest3d_integration.py` (unimported), tier1 shim |
| `piece3d_mr` | Godot scene-piece validation (not a tick kernel) | n/a | `builders/godot_scene_piece_builder.py`, gates only |

Other copies and removed kernels:

- `tier2/godotsim/combat3d_mr.py` (96 lines): older GodotSim combat kernel (tuple alerts); unimported.
- `tier1/engainos/core/combat3d_mr.py`, `quest3d_mr.py`: re-export shims ("historical misplaced … MR kernel path").
- Removed: `empire_mr.py` (EngAInOS orchestrator, "AI First with Human Overreach"; only ever built in tests), `trixel_world_mr.py` (2D Trixel eviction), `archive/zonengine4d/.../behavior_mr.py`.
- No `*_mr.py` in `out of root/`.

### 6A.2 Who delegated to the kernels (HISTORICAL)

- **GodotSim, live — confirmed.** Before `5f213ca5` (2026-03-02, "refractored run_time"), `godotsim/sim_runtime.py` registered combat/inventory/dialogue entities at boot (lines 608-652; hard-coded `player`/`guard`/`enemy`, "remove in production") and called `combat.tick`, `inventory.tick`, `dialogue.tick` every frame in `_update_subsystems` (lines 900-916).
- **EngAInOS, tests only — confirmed.** The gateway → Empire → kernel chain was constructed only in `test_agent_gateway.py`, `test_full_pipeline_integration.py`, `test_full_stack.py`; archived `f4066e2a` (06-13). No live server used it.

### 6A.3 Misplaced-kernel relocation (HISTORICAL, `203e130e`, 2026-06-21)

`combat3d_mr.py` and `quest3d_mr.py` sat in `godotengain/engainos/core/` instead of with the GodotSim kernels. Six gates (`godotsim/gates/gate_mr_kernel_{placement_classification,relocation_readiness,shim_plan,old_path_shims,new_lane_imports,active_import_clean}.py`) classified them as pure simulation kernels (`GODOTSIM_RUNTIME_KERNEL_CANDIDATE`), copied them to `godotsim/kernels/`, left shims at the old path, and repointed importers. Those gates and `combat3d_mr.py.pre_shim_backup` were deleted with old `godotengain/` in `c0b6bc6a` (06-24); git history only.

Side effect: the EngAInOS copy (dict alerts) became canonical and the combat adapter was repointed to it, but the adapter still unpacks alerts as `(entity_id, alert_type)` tuples. It never failed because the combat tick was already off.

### 6A.4 Combat execution path

```
Before 2026-03-02 (HISTORICAL):
POST /combat/damage → handler → combat.handle_delta (queue)
frame loop → _update_subsystems → combat.tick → step_combat → HP updated → snapshot["combat"]

Now (STATIC):
POST /combat/damage → RuntimeGateway (AP rules) → CommandDispatcher → combat.handle_delta (queue)
frame loop → _process_tick → spatial / perception / behavior only
→ damage stays in combat.pending_damage; entity_hp stays empty; no combat output
```

Stacked breaks:

1. Combat/inventory/dialogue tick calls dropped in `5f213ca5` (intent not recorded in the commit). STATIC/HISTORICAL
2. Entity registration with the adapters dropped in the same commit; `Combat3DAdapter` starts with zero entities. STATIC
3. Adapter/kernel alert-format mismatch from `203e130e`. **TESTED** in-process: register two entities, queue damage, `tick()` → `ValueError: too many values to unpack (expected 2, got 4)`.
4. Scene health is never read: loadable scenes (`.engain_cache/parsed/scenes/*.zonj.json`) list entities as names and keep health in `initial_state.combat.entities`; nothing maps it into `snapshot["entities"]` (where AP rules read health) or into the combat adapter. No runtime version ever did. `tier1/engainos/game_scenes/*.json` carry health on entities but lack `segments`, so `/scene/load` refuses them. STATIC

Engionality has its own tick loop (`tier2/engionality/controlroom/runtime_loop.py`, `bootstrap.py`); no runtime file in git history ever referenced Engionality. The architect recalls turning a tick off; git does not show where (OPEN).

---

## 6B. Combat health state trace (read-only, 2026-10-17)

**Headline: the complete combat health path was never implemented, including before the March refactor.** What the March refactor lost was the execution of the kernels, not a working health pipeline.

### 6B.1 Existing written snapshot contract — STATIC

- `AGENTS.md:85`: `EngAInRuntime.snapshot` is the single source of truth for runtime state.
- `AGENTS.md:372-374`: MR kernels operate on snapshot/slices and return deltas/outputs; kernels do not mutate global state in place; runtime/adapters apply accepted deltas back into the snapshot.
- `docs/contracts/GODOTSIM_TIER2_AUTHORITY/GODOTSIM_TIER2_SPATIAL_SIM_CONTRACT_v1.md` §2: GodotSim owns spatial truth only; EngAInOS accepts or rejects state mutations. No contract found assigns ownership of combat or health state.
- The architecture map AGENTS.md cites (`godotsim/architectual_map_sim_runtime.md`) is not in the tree (OPEN).

Measured against that contract, today's combat health lives outside the SSOT (below).

### 6B.2 Where health is, per step — STATIC

| Step | What happens |
|---|---|
| Starting value | The pipeline assigns a default `100.0` per character (`tier3/mettaext/passroom/pass5_game_bridge.py:848`), carried as `initial_state.combat.entities` by `bridgeroom/zon_to_game.py:164-186` and `bridgeroom/scene_loader.py:217`. This is a governed default, not manuscript fact (an unspecified gameplay property may be inferred or assigned by governed defaults without becoming canon). |
| Scene load | Nothing in `tier2/godotsim` reads `initial_state`. `snapshot["entities"]` gets the scene's entities as given plus text-extracted entities (`scene_manager.py:160-208`); neither carries health. |
| Kernel update | `step_combat` returns a new `CombatSnapshot`; the adapter keeps it privately plus an `entity_hp` mirror (`combat3d_adapter.py:110-118`). Nothing writes it into `EngAInRuntime.snapshot`. |
| Export | `get_snapshot()` attaches `combat.get_all_state()` (`active_combats`, `entity_hp`, `entity_armor`, `pending_damage`) to the exported envelope under `"combat"` (`runtime_core.py:774-776`), not to `self.snapshot`. `build_snapshot_pack()` also includes it, but its consumer `_run_kernel` has no callers. |

### 6B.3 Four readers, four answers — STATIC

| Reader | Reads | When absent |
|---|---|---|
| AP complex rules (`aproom/ap_complex_rules.py`) | `snapshot["entities"][id]["health"]` | 0 → attack rejected |
| Slice builder (`slice_builders.py:99`) | same field | 100 |
| Combat adapter / kernel | its registered `CombatSnapshot` | unregistered → damage ignored |
| 8090 HUD (`engainos_server.py:98-108,395-405`) | exported `combat.entities[id]` | key never exported → always `health 0, alive False` |

### 6B.4 Follow-up action mechanism — STATIC / HISTORICAL

- **Existing translation pattern (current):** `runtime_core.py:424-433` converts behavior-adapter `Delta` objects into `{domain, op, path, value}` dicts, which `_apply_delta` (`runtime_core.py:616-651`) writes into `self.snapshot`. This is the only live path from an adapter's output into the SSOT.
- **Combat's output:** `(type, payload)` pairs `behavior3d/set_flag`, `navigation3d/disable`. No consumer for either exists anywhere, current or in git history.
- **Historical routers:** `74abb5b9` (02-26) `_apply_delta(delta.type)` handled only `navigation3d/request_path`, `behavior3d/attack` (→ events), `behavior3d/high_intent` (log). `5f213ca5^` `_apply_deltas` only logged, and calls `.get()` on each delta, which the combat pairs do not support (not executed). `_apply_combat_alert` marked `entity_died` in `snapshot["entities"]`, but combat's tick returned deltas, not alerts, so it never fired.

### 6B.5 Lost vs never implemented

| Item | Status |
|---|---|
| Combat/inventory/dialogue kernel execution each tick | **Lost** — March runtime refactor `5f213ca5` (before the June tier migration) |
| Registration of (hard-coded test) entities with the adapters | **Lost** — same commit |
| Adapter/kernel alert format agreement | **Broken** by the 06-21 kernel relocation `203e130e`; fixed in working tree (D14) |
| Scene/initial health into the runtime | **Never implemented** |
| Combat health in `EngAInRuntime.snapshot` (the SSOT) | **Never implemented** |
| A consumer for combat follow-up actions | **Never implemented** |
| Death reaching `snapshot["entities"]` via combat | **Never implemented** (handler existed; never reached) |
| HUD reading the exported combat shape | **Never matched** (D17) |

D15 and D16 remain unresolved. Before choosing health ownership: establish how combat state can be exposed consistently to the runtime and AP without creating another authoritative health store, and reuse the existing adapter-output path (6B.4) before proposing any new translation layer.

---

## 7. Reproducible defects (prioritized)

| # | Defect | Repro | Label |
|---|---|---|---|
| D1 | 8090 crashes on any mutating or unknown action instead of refusing | `evaluate({...,"action":"load_scene"})` → `APRuleLoadError`; cause: registry dir dropped in `c0b6bc6a` | TESTED |
| D2 | Caller-assigned tier accepted without bounds or identity; self-claimed tier 3 passes FINALIZED | 8080 body with `actor_authority_tier: 99`, or `3` + `reality_mode: FINALIZED` → accepted | TESTED |
| D3 | Gameplay AP rules never match the live combat request | `/combat/damage` sends `source/target/damage` (`runtime_client.py:103-104`); rules expect `attacker/amount` (`ap_complex_rules.py:143-153`); gateway checks before the dispatcher renames fields | TESTED. **Fixed in working tree, uncommitted** (§9); proven over real HTTP by `tier2/godotsim/test_gateway_combat_rules.py` |
| D4 | Unknown `reality_mode` silently becomes DRAFT | `reality_mode: "LIVE"` (what Godot sends) → DRAFT (`runtime_gateway.py:138-139`) | TESTED |
| D5 | Mutating routes with no gate | 8080 `/embodiment/apply`, `/vault/link`, `/world/sync`, `/world/load_mirror`; 8090 combat/inventory/dialogue | STATIC |
| D6 | AP rule exceptions swallowed in the 8080 gateway (fails open) | `runtime_gateway.py:268-279` prints and continues | STATIC |
| D7 | `/scene/load` skips the global and per-request FINALIZED checks `/command` performs | `http_handlers.py:401-438` vs `runtime_gateway.py:246-259` | STATIC |
| D8 | 8765 execute/history intent is caller-declared | `allow_execute: true` → accepted (harmless today: 0 rules, timeline write off) | TESTED |
| D9 | Decisions not durable: 8090 rejections unrecorded; IntentShadow in memory; accepts never logged | §4.3 | STATIC |
| D10 | 22 ACTIVE gates check pre-tier paths | §3 survey | STATIC |
| D11 | `canon.can_edit` returns True for scenes it has never seen | `aproom/canon.py:107-113` | STATIC |
| D12 | Reality-mode helpers disagree: `RealityContext.is_editable()` blocks FINALIZED even at tier 3; `allows_mutation()` and the matrix do not; `TEST` mode exists in code but not in the matrix | `aproom/reality_mode.py:24-35,52-54,68-70`; `authority_validator.py:45-46` | STATIC |

| D13 | Combat, inventory and dialogue kernels never run: their ticks were dropped in `5f213ca5` | accepted damage stays in `combat.pending_damage`; HP never changes (§6A.4) | STATIC |
| D14 | Combat adapter crashes against the canonical kernel's dict alerts | `Combat3DAdapter` + queued damage + `tick()` → `ValueError` (§6A.4) | TESTED. **Fixed in working tree, uncommitted** (§9); `tier2/godotsim/test_combat3d_adapter.py` |
| D15 | No entities registered with the combat/inventory/dialogue adapters | `Combat3DAdapter` starts empty; no live `register_entity` caller (§6B) | STATIC; unresolved |
| D16 | Scene health never reaches the runtime | health lives in `initial_state.combat.entities`; AP rules read `snapshot["entities"][id]["health"]` and see 0, so every attack between real entities is rejected (§6B) | STATIC; unresolved |
| D17 | 8090 HUD reads a combat shape the runtime never exports | `/api/hud/combat` reads `combat.entities[id]`; export has `entity_hp`, not `entities` → always health 0, dead (§6B.3) | STATIC |

D1–D4 are the most direct contradictions of "nothing changes runtime state unless EngAInOS allows it." No defect here permits writing canon history: the timeline fence held (§6).

---

## 8. Proposed repairs — NOT DECIDED

Placeholder only. No repair is approved, and none should restore human-root override (§1).

**Repair boundary (agreed in session):** reconnect kernel execution without changing snapshot ownership, validation, fallback behaviour, or canonical persistence. If a repair needs any of those, stop and review the design first. Proposed ownership split, **not yet verified against the existing snapshot protocol**: a kernel calculates changes (e.g. `step_combat` computes health deltas); the runtime incorporates them into authoritative state; snapshots report that state without owning it. Do not add a second health store or fall back to older snapshots to make combat tests pass.

Each of the following needs an architect decision first:

- What `actor_authority_tier` means under §1: removed, reduced to system-vs-requester, or assigned by EngAInOS rather than the caller.
- Whether REPLAY and tier-vs-action checks live in AP rule files or in code.
- Which gate is canonical for runtime mutation: 8090 `authority_gate` or 8080 `RuntimeGateway`.
- Whether the AP relay and the safe 8080 entrypoint were intended replacements or deliberate experiments (§5).
- Whether FINALIZED should be read-only to every actor, with change only via re-running the manuscript.
- Whether runtime/gameplay state (inventory, combat) is governed separately from canon.

---

## 9. Changes made in this session (outside the audit itself)

Committed in `24af637b` ("before ap is rebuilt", pushed), together with this document and the 10-16 baseline:

- `tier1/engainos/core/agent_gateway.py` → `tier1/engainos/archive/retired_agents/`
- `tier1/engainos/core/trae_observer.py` → `tier1/engainos/archive/retired_agents/` (already unimportable from `core/`: `from .reality_mode`)
- `tier1/mrlore/schema/TRAE_MRLORE.md` → `docs/contracts/SUPPORT_LANE_DISTRIBUTION/retired_agents/`
- `docs/contracts/human_external_originating_authority/` → `docs/contracts/archive/`
- New notes: `tier1/engainos/archive/retired_agents/README.md`, `docs/contracts/archive/README.md`

References left pointing at old locations: `AGENTS.md`, `HANDSHAKES.md` (not edited by rule); `PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md` and `SHARED_SESSION_CONTINUITY_CONTRACT_v1.md` (name `agent_gateway.py` as "Gate 1"); the Switchboard spec v0.3 §5 (cites the human-override contract).

Not staged (working tree):

- D3 fix: `tier2/godotsim/command_dispatcher.py` (shared `combat_damage_payload()`), `tier2/godotsim/runtime_gateway.py` (`_ap_rule_view()` feeds AP rules attacker/target/amount from that payload). New test `tier2/godotsim/test_gateway_combat_rules.py` (real 8080 handler and gateway, combat adapter mocked): 22/22 pass with the existing godotsim tests. Behaviour change: a damage request without `source` is now rejected when the scene has entities (rule fail-safe on attacker "unknown").
- D14 fix: `tier2/godotsim/adapters/combat3d_adapter.py` alert loop reads the kernel's dict alerts (`entity_died` → dead flag + navigation disable; `low_health_warning` → low_health flag; `damage_applied` → no delta), producing the same deltas as before the 06-21 switch. New test `tier2/godotsim/test_combat3d_adapter.py` (real adapter + real kernel, no mocks): 26/26 godotsim tests pass. The runtime still does not call `combat.tick()` (D13 untouched); snapshot ownership unchanged.
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
