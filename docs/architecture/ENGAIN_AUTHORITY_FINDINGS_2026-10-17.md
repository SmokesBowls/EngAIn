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
| `quest3d_mr` | quest state | **no**; no runtime caller in current tree or git | `bridgeroom/quest3d_integration.py` (unimported), tier1 shim |
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

**Headline: no inspected version (git history, the Dec 2025 pop-drive runtimes in §6C/§6D) has a complete combat health path:** health stayed adapter-owned in all of them. Death reached `snapshot["entities"]` only in the Dec 21 runtime, and only through its alert handler (§6C, corrected 2026-10-18). What the March refactor lost was kernel execution, not a working health pipeline.

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
| Scene load | Nothing in `tier2/godotsim` reads `initial_state`. `snapshot["entities"]` gets the scene's **dict** entities as given (non-dict entities are skipped) plus text-extracted entities (`scene_manager.py:160-208`). Whether health arrives depends on the scene source (corrected 2026-10-18, §6F): Stageroom Pass 5 packets carry per-entity `health`/`max_health` and keep it; `.engain_cache` zonj files list entities as strings and lose it. |
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
- **Combat's output:** `(type, payload)` pairs `behavior3d/set_flag`, `navigation3d/disable`. No consumer found in the current tree or in git history. One existed on disk in Dec 2025: `route_delta()` in `zon4d/sim/simruntime.py` and `test_full_stack_with_combat.py` (Dec 11) handled both (§6D.5).
- **Historical routers:** `74abb5b9` (02-26) `_apply_delta(delta.type)` handled only `navigation3d/request_path`, `behavior3d/attack` (→ events), `behavior3d/high_intent` (log). `5f213ca5^` `_apply_deltas` only logged, and calls `.get()` on each delta, which the combat pairs do not support (not executed). `_apply_combat_alert` marked `entity_died` in `snapshot["entities"]`, but combat's tick returned deltas, not alerts, so it never fired.

### 6B.5 Lost vs not found

"Not found" = absent from every version inspected (current tree, git history, pre-move copy, the pop-drive sources named in §6C/§6D); it is not a claim that no implementation ever existed.

| Item | Status |
|---|---|
| Combat/inventory/dialogue kernel execution each tick | **Lost** — March runtime refactor `5f213ca5` (before the June tier migration) |
| Registration of (hard-coded test) entities with the adapters | **Lost** — same commit |
| Adapter/kernel alert format agreement | **Broken** by the 06-21 kernel relocation `203e130e`; fixed in working tree (D14) |
| Scene/initial health into the runtime | **Source-dependent** — kept from Stageroom Pass 5 packets; lost from `.engain_cache` zonj files, the source `godotnew/semantic` posts (§6F) |
| Combat health in `EngAInRuntime.snapshot` (the SSOT) | **Not found** |
| A consumer for combat follow-up actions | **Dec 11 only, then lost** — `route_delta()` in the zon4d runtime (§6D.5); not in git |
| Death reaching `snapshot["entities"]` via combat | **Dec 21 only, via the alert handler, then lost** — `_apply_combat_alert` set `alive=False`; that runtime discarded combat's deltas. The Dec 26 pair would most likely crash before its alert routing ran (§6C.3). Not reached in any git version. |
| HUD reading the exported combat shape | **Never matched** (D17) |

D15 and D16 remain unresolved; D16 is re-scoped in §6F (which scene source is authoritative). Before choosing health ownership: establish how combat state can be exposed consistently to the runtime and AP without creating another authoritative health store, and reuse the existing adapter-output path (6B.4) before proposing any new translation layer.

---

## 6C. December 2025 evidence from the pop drive (HISTORICAL)

Sources (read-only; nothing restored): `/run/media/mytruelove/storage1/pop/` — workspace `godotsim/` (files Dec 15–25), extracted workspace `godotsim (1)/godotsim/`, and archives `godotsim combat complete.tar.gz`, `godotsim starting dialogue.tar.gz`, `godotsim 5of 5 test.tar.gz`, `godotsim_5of5_integrated_20251226_025746.zip`, `godotsim_pre_crash_debug_20251226_221048.zip`, `godotsim_BOTH_5of5_20251226_233746.zip`. Git history for GodotSim starts at `c7a636d3` (2026-02-16), when `godotsim/` was converted from a gitlink to tracked files; everything before that exists only on disk.

### 6C.1 Combat timeline

| Date | Runtime imports | Combat kernel | State |
|---|---|---|---|
| Dec 21 | `combat3d_integration.Combat3DAdapter` | **wound-state kernel** `df717de8` (5,904 B; `WOUND_STATE_*`; `step_combat(snapshot_in, deltas, dt)`) | Ran live: `godotsim/runtime.log` shows combat/inventory/dialogue entities registering; session summary records 100 → 75 → 50 → 25 → 0 → death |
| Dec 25 | still `combat3d_integration` | swapped to the tuple-alert `CombatSnapshot` kernel `27182543` (= today's unused `tier2/godotsim/combat3d_mr.py`) | Likely broken: integration still imports `WOUND_STATE_DEAD` (not run) |
| Dec 26 | `combat3d_adapter.Combat3DAdapter` | dict-alert `CombatSnapshot` kernel `597a868d` (= today's `tier2/godotsim/kernels/combat3d_mr.py`) | Adapter and kernel agree (dict alerts; adapter returns `(deltas, alerts)`), but the runtime would most likely crash on the first follow-up action (§6C.3, corrected 2026-10-18) |

The wound-state kernel survives in three places, none in git: both Dec 21 archives and `pop/godotsim (1)/godotsim/combat3d_mr.py`. Inventory and dialogue kernels are byte-identical from December to today.

### 6C.2 Kernel comparison (wound-state `df717de8` vs current `597a868d`) — STATIC

| Aspect | Wound-state kernel (Dec 21) | Current kernel |
|---|---|---|
| Interface | dict `{"combat3d": {...}}` + queued `{type, payload}` deltas + `dt`; returns `(snapshot, accepted_ids, alerts)` | frozen `CombatSnapshot` + `List[DamageEvent]`; returns `CombatOutput` |
| Damage | `combat3d/apply_damage` subtracts, clamps at 0 | same, via `CombatEntity.apply_damage` |
| Dead entities | damage still subtracted (then clamped); no second `entity_died` | dead entities ignore damage |
| Wound states | stored on entity: healthy → wounded (< max) → badly_wounded (≤ 25%) → dead; `wound_state_change` on transitions | none |
| Low-health alert | only on the transition into badly_wounded | on every hit while ≤ 25% |
| Hit log | `attack_hit` per hit | `damage_applied` per hit |
| Attack resolution | `combat3d/attack`: 85% hit, damage = strength − defense (min 1) | none |
| Determinism | `combat3d/attack` uses unseeded `random.random()` — conflicts with the "kernels are pure" invariant | deterministic |
| Extra fields | `strength`, `defense`, `state` | `stagger_timer`, `invuln_timer` (unused) |

Observations, not decisions: wound state is a pure function of `health`, `max_health` and `alive`, so it could be derived instead of stored; attack resolution would need a seeded RNG to stay pure.

### 6C.3 Why today's adapter drops alerts

- The Dec 26 adapter (dict alerts, `return deltas, alerts`) exists only inside the three Dec 26 zips.
- All 13 extracted copies of `combat3d_adapter.py` on the pop drive — including `EngAIn_BACKUP_20260224_193632`, `workspace22/EngAIn-main`, `godotsim-(4.5)`, the earlier `zonengine4d/sim` copies — are the tuple-alert, deltas-only lineage (`e9e456fc` and descendants). Git's first adapter (`c7a636d3`) is the same lineage, and git never contains `return deltas, alerts`.
- So the alert pass-through was not removed by a later edit: the Dec 26 rewrite never entered the lineage later work continued from. A zip named `pre_crash_debug` (Dec 26 22:10) suggests a crash that day; the reason the work did not carry forward is OPEN.
- The October D14 fix reproduces the Dec 26 alert mapping exactly; it does not restore the `(deltas, alerts)` return or the runtime routing.
- **Dec 26 runtime would most likely crash (STATIC, not executed; corrected 2026-10-18).** Its `_update_subsystems` appends combat's `(type, payload)` tuples to `all_deltas`, then `_apply_deltas` calls `delta.get(...)` on each; a tuple raises `AttributeError` (confirmed in isolation). The call sits outside any `try`, and `_simulation_loop` has none, so the first low-health or death hit would most likely end the simulation thread *before* `_push_alerts` (the alert routing) runs. Even without the crash, `_apply_deltas` only printed each delta. This may explain the `pre_crash_debug` zip; that link is a hypothesis.
- **Dec 21** is the only runtime found where death reached `snapshot["entities"]`: its tick discards combat's deltas and routes alerts (inside `try`) to `_apply_combat_alert`, which sets `alive=False`, `state="dead"` if the entity is in `snapshot["entities"]`. State changed via a notification, not via a state delta.

---

## 6D. Kernel–adapter–runtime trace and migration compatibility (2026-10-18)

Standard for this section: every absence claim names what was inspected. "Not called" means no caller in the named versions.

### 6D.1 The three-layer design (HISTORICAL)

`pop/Documents/documentationai-Docs/zonengine4d/zon4d/sim/doc/BUILD_STATUS.md` (Dec 7, 2025) defines the layers:

1. **Deep Contract**: a StateView class (`Spatial3DStateView`) with delta pre-validation (`_validate_spawn`, `_validate_move`) and AP constraint functions (`spatial3d_no_overlap_constraint`, `spatial3d_velocity_limit_constraint`). No callers of the two constraint functions were found in that workspace.
2. **Adapter**: converts deep deltas to MR deltas, validates AP before and after the kernel, rolls back on violation, and converts MR alerts to runtime alerts.
3. **MR kernel**: pure, snapshot in → snapshot out.

The term "Pillar3" was not found; the third layer is named "Deep Contract".

### 6D.2 Pairs in the current tree (isolated execution, 2026-10-18)

Each adapter's own step method was called directly against today's kernels. The runtime was not started and no tick ran.

| Kernel | Adapter | Runtime creates it | Runtime calls adapter step | Adapter step in isolation |
|---|---|---|---|---|
| `spatial3d_mr` | `Spatial3DStateViewAdapter` | yes | no; `_process_tick` calls `step_spatial3d` directly | **FAIL** (§6D.3) |
| `perception_mr` | `PerceptionStateView` | yes | no; calls `step_perception` directly | PASS (runs its validate/rollback path) on fallback stubs (§6D.4) |
| `behavior3d_mr` | `BehaviorStateView` | yes | **yes**, `behavior_step` | PASS |
| `navigation_mr` | `NavigationStateView` | no | no | PASS (`request_path` → 1 delta) |
| `combat3d_mr` | `combat3d_adapter.Combat3DAdapter` | yes | no (not ticked, D13) | PASS (`test_combat3d_adapter.py`) |
| `combat3d_mr` | `combat3d_integration.Combat3DAdapter` | no | no | FAIL: `step_combat() takes 2 positional arguments but 3 were given` — written for the Dec 21 wound-state kernel |
| `inventory3d_mr` | `Inventory3DAdapter` | yes | no (dispatcher `handle_delta` only) | PASS |
| `dialogue3d_mr` | `Dialogue3DAdapter` | yes | no (dispatcher `handle_delta` only) | PASS |

`combat3d_integration.py` (lines 124–234), `inventory3d_integration.py` (119–291) and `dialogue3d_integration.py` (62–136) each end in a large string literal holding runtime glue (registration, `tick()` calls, alert handlers). It does not execute; its content has not been reviewed.

### 6D.3 Spatial: adapter bound to a stub parent

Today's `tier2/godotsim/spatial3d.py` is 987 B and says "Minimal stubs for Spatial3D adapter to work standalone without full ENGINALITY framework". The same 987 B file is dated 2025-12-16 in `pop/godotsim/` and is identical in every git version (`c7a636d3` onward). The Dec 7 Deep Contract (5,014 B, `zon4d/sim/spatial3d.py`) is not in git. Against the stub, the adapter fails three ways:

- `handle_delta` → `super().handle_delta()` → `AttributeError` (the stub has no such method).
- `physics_step` → the stub `Alert(level, message, context)` → `TypeError: unexpected keyword argument 'step'` (the adapter expects the Deep Contract's `Alert(level, step, message, tick, ts, payload)`).
- `spawn_entity` → `from fix_1_snapshot_purity import ...` → not found. Absent from the repo at every inspected git version; present on pop (`pop/godotsim/`, `pop/godotsim-(4.5)/`, `pop/godotsim_quarantine_20251225_180820/`).

### 6D.4 Import resolution — what Python actually loads

Method: static AST resolution of every import in `tier2/godotsim`, then importing `tier2.godotsim.runtime_core` and reading `sys.modules`.

- Every kernel and adapter import resolves to `kernels/` / `adapters/` as intended; `SUBSYSTEM_STATUS` is all `True`. The stray root `tier2/godotsim/combat3d_mr.py` (tuple kernel) is not loaded by any current import.
- **Unresolved:** `ENGINALITY.state.domain_views`, `ENGINALITY.alerts`, `ENGINALITY.delta_types`, `ENGINALITY.tasks` (perception adapter, which falls back to its own stubs: `ENGINALITY_AVAILABLE=False`), and `fix_1_snapshot_purity` (spatial). In git `c7a636d3`, `92b3df2f` and `f4066e2a`, `ENGINALITY/` contains only `domain_views.py` (no `state/`, `alerts`, `delta_types`, `tasks`), so these imports did not resolve before the migration either.
- **Hazard, not a defect:** `perception_adapter.py` puts `tier2/godotsim` (and `tier2`) on `sys.path` at import. After that, a bare `import combat3d_mr` resolves to the stray tuple kernel. `runtime_core.py:485,757` bare-imports `bridge_integration`, which resolves only because of that side effect.

### 6D.5 Which layer each runtime called

| Runtime | Spatial | Perception | Combat follow-up actions |
|---|---|---|---|
| Dec 11, `zon4d/sim/simruntime.py` + `sim_runtime_file_test.py` | `physics_step()` (adapter) | `perception_step()` (adapter) | `combat.tick()` → `route_delta()` consumed `behavior3d/set_flag`, `navigation3d/disable` |
| git `c7a636d3` (Feb 16), `92b3df2f` (Mar 1) | direct `step_spatial3d` | `perception_step()` (adapter) | ticked; tuples to `_apply_deltas` (§6B.4) |
| git `6a9c3056` (Mar 5), `f4066e2a` (Jun 13), current | direct | direct `step_perception` | not ticked |

`f4066e2a` (pre-relocation, pre-tier) creates and calls the same adapter methods as today, line for line, with bare imports instead of package imports.

### 6D.6 Adapter output vs the runtime's state-change format

`_apply_delta` expects `{domain, op, path, value}`. No adapter emits it:

| Adapter | Returns |
|---|---|
| behavior | `Delta(id, type, payload, tags)` — translated by `runtime_core.py:431-437` into the dict form (only live adapter → snapshot path) |
| navigation | `Delta` dataclass, `navigation3d/path_requested` |
| inventory, dialogue | the accepted input deltas echoed as `{type, payload}`; outcomes are in the alerts (e.g. `item_taken`) and in adapter state |
| combat | `(type, payload)` tuples |
| perception (direct kernel call) | the kernel's dicts; 0 in the probe |

A `{type, payload}` dict passed to `_apply_delta` is a silent no-op (empty path). A tuple or `Delta` object raises `AttributeError` on `.get` (outside the per-kernel `try`; caught by `_simulation_loop`).

### 6D.7 Migration vs earlier disconnection

| Defect | When | Source |
|---|---|---|
| Spatial Deep Contract replaced by stub; `fix_1_snapshot_purity` missing | Dec 2025 (stub dated Dec 16), before git | pop + all git versions |
| Spatial adapter bypassed | between Dec 11 and Feb 16 | §6D.5 |
| `ENGINALITY.*` imports unresolved (perception on fallback stubs) | at or before Feb 16 | git |
| Perception adapter bypassed; combat/inventory/dialogue ticks dropped | March refactor (`5f213ca5` / `6a9c3056`) | git |
| `combat3d_integration` unimportable against its bare `combat3d_mr` (`WOUND_STATE_DEAD` missing) | at or before Feb 16 | git |
| Combat adapter/kernel alert-format mismatch (D14, fixed) | June 21 kernel relocation `203e130e` | git |
| Runtime adapter registration and calls | **unchanged** by the June migration | `f4066e2a` vs current |

Of the kernel-system breaks inspected, only the D14 mismatch came from the migration. The rest predate it.

Not inspected: the Dec 21/26 runtimes' spatial and perception calls (narrows the spatial-bypass date); the `zon4d/` tarballs (`sim 4 point passtest`, `simall systems check`, `sim spat percep`); the Dec navigation/behavior adapters' AP logic; the integration-file glue strings; MrLore; Engionality kernel conventions. No December test was run.

**Engionality commit loop (related, STATIC):** `tier2/engionality/controlroom/runtime_loop.py` (RUNTIME_LOOP_v0.1) defines per-delta AP preflight, snapshot finalize, inverse-delta application and rollback. Its AP steps 4/5/8 are marked "Phase 2", and `bootstrap.SimpleAPEngine` accepts everything. Its only users found are its own three files (`runtime_loop`, `bootstrap`, `zon4d_kernel`).

`_run_kernel` (`runtime_core.py:577`): no callers in any git version; its call signature (`snapshot=, intent=, rng=, now_tick=`) matches no current kernel. It may be an unused design alternative; the working commit path historically ran through the adapter layer.

---

## 6E. Spatial Deep Contract compatibility, embedded runtime glue, `out of root` facades (2026-10-18)

- **Deep Contract vs stub (isolated, scratch copies only).** Today's `spatial3d_adapter.py` + today's `kernels/spatial3d_mr.py` + the Dec 7 `zon4d/sim/spatial3d.py` + `pop/godotsim/fix_1_snapshot_purity.py` (Dec 20): all 10 probe steps PASS (spawn, move, contract rejections of a missing id and a 2-element target, `physics_step` with collision resolution, `spawn_entity`, both constraints on the result). Today's adapter is byte-identical (imports normalised) to `pop/godotsim/spatial3d_adapter.py` (Dec 24), which already sat beside the Dec 16 stub — the mismatch dates from December. Only the adapter imports `spatial3d.py`; the stub's extra API has no users; nothing calls the runtime's `self.spatial`.
- **What the Deep Contract checks.** Input shape only (entity id present; move target has 3 values). No tier, reality mode or canon; the two constraint functions have no callers; `physics_step`'s docstring says "applies AP" but does not. Adapter-local validation is not an authority decision. The Dec contract is itself a standalone version (its own `Alert`/`BaseStateView` are labelled "Minimal … for standalone use").
- **Snapshot field names disagree.** `fix_1` requires protocol names (`position`/`velocity`) in snapshots and purges `pos`/`vel`; today's runtime writes `pos`/`vel` into `snapshot["entities"]` (`runtime_core.py:399-400, 474, 720, 745`). `fix_1.write_kernel_output_to_snapshot` (a snapshot commit helper) has no users.
- **Embedded runtime glue.** `INTEGRATION_PATCH` strings in `combat3d_integration.py`, `inventory3d_integration.py`, `dialogue3d_integration.py` are the Dec 21 runtime wiring. Present in today's runtime: imports, `_init_*`, HTTP endpoints, `get_snapshot` export. Absent: test-entity registration, per-frame `tick(dt)`, `_apply_*_alert` handlers. Inventory and dialogue handlers only print; combat's `entity_died` is the only snapshot write. State stayed adapter-owned by design, copied into the export. The combat patch targets `combat3d_integration` (wound-state API), not `combat3d_adapter`.
- **`out of root/tools`.** `patch_sim_runtime_autorelink_v1–v3b` re-link the vault at boot (they rewrite `godotsim/sim_runtime.py` in place; pre-tier target). `probe_domain_views.py` tests `tier2.engionality.showroom.domain_views.generate_domain_views_from_state`, not the `ENGINALITY.state.domain_views.BaseStateView` the perception adapter imports. `check_ap_engine_singleton.py` checks for more than one loaded `ap_engine.py` (pre-tier module path). No file references kernels, adapters, StateView or ENGINALITY.
- **`out of root/engain/` facades.** `engain/kernels/{spatial,perception,navigation}.py` import `tier2.godotsim.{spatial3d_mr,perception_mr,navigation_mr}`, which do not exist (kernels moved to `kernels/` on 06-21) — a path break, likely from the tier-prefix rewrite (not verified against the rehousing map). Nothing imports them. `facade/` gates report "Legacy modules are wrapped, not replaced: TRUE" from a hard-coded packet in `facade_control_center.py` (listing only `godotengain.engainos.core.ap_core`), not from importing the facades.

---

## 6F. Combat input-to-result trace and scene health sources (2026-10-18)

Read-only; no servers started. Layers kept distinct: EngAIn runtime / reusable engine integration / individual engine project (`AGENTS.md`, engine-agnostic integration boundary).

### 6F.1 Combat, input to visible result

| # | Boundary | Today | Status |
|---|---|---|---|
| 1 | Initiator | `godotnew/semantic` sends no combat request (its calls: `/snapshot`, `/scene/load`, `/command` text, vault). Behavior kernel/adapter emit no attack intents. Dec client `combat3d_godot_integration.gd` (pop only) posted `/combat/damage`. | Nothing initiates combat |
| 2a | 8090 | `/api/combat/damage` → `runtime_client.combat_damage()` posts `{source,target,damage,trace_id}` with no identity fields → 8080 gateway **400** (checked against the real `_missing_identity_fields`) → 8090 returns 502. The route bypasses 8090's own gate. | Broken |
| 2b | 8080 direct | `http_handlers` sets `command="combat/damage"` → `RuntimeGateway.submit`. Passes with identity fields. | Works |
| 3 | AP | `rule_attacker_min_health` reads `snapshot["entities"][attacker]["health"]` — source-dependent (§6F.2). | Broken on the `.engain_cache` source |
| 4 | Dispatch | queues `combat3d/apply_damage`, replies `damage_applied` before anything is applied | Works; misleading ack |
| 5 | Adapter tick | unregistered targets ignored (D15); `tick()` never called (D13) | Broken |
| 6 | State commit | outcome stays in the adapter; copy exported as `snapshot["combat"]["entity_hp"]` | Broken |
| 7 | Observer | `godotnew/semantic` reads no combat fields; 8090 HUD reads `combat.entities` (D17) | Broken |

### 6F.2 Health along the two scene sources

| Step | 8765 scene server (EngAIn protocol) | `godotnew/semantic` active path |
|---|---|---|
| Source | `bridgeroom/scene_server.py` `/load_scene` → `StageroomSceneResolver` → `tier3/mettaext/stageroom/output/passroom/<id>/game_scenes/<id>.json` (Pass 5) | `Main._on_scene_selected` → `tier3/mettaext/loaded/scene_index.json` (via `tier1/engainos/assets/engain_manifest.json`, library `latest_ingested`) → `.engain_cache/parsed/scenes/*.zonj.json` |
| Health in payload | 212 scenes, 409 entity dicts, all with `health`/`max_health` | 109 scenes, 184 entities, all strings; health only in `initial_state.combat.entities` (94 scenes) |
| Integration | not on the active load path | `normalize_scene_payload` + `SimClient.load_scene_doc` preserve everything (add identity fields) |
| `snapshot["entities"]` | dict entities kept as-is → `health` present | string entities skipped (`scene_manager.py:168-170`); only narrative-extracted entities, no health |
| AP | allowed (tested) | rejected: "Attacker must have health >= 10" (tested) |

- `Boot.gd`'s entity adapter keeps `health` only in its layout document (`accept_main_owned_scene_for_layout`); `/scene/load` is posted only by `Main.gd:509`.
- One sample (`001_the_ethereal_vigil_with_semantics.zonj.json`): `initial_state.combat.entities` key `mordain` vs entities `["Aeon Keepers","Korath"]` — ids may not line up; not checked across files.
- `godotnew/semantic` is a consumer project (absolute repo paths in 5 `.gd` files, project-specific chooser/layout). No reusable Godot integration layer found in the repo (only `godot/{boot,input}/*BridgeConsumeCommand.gd`, which set `combat_state_write_allowed: false`), `godotnew`, or the Dec pop copy (whose `combat3d_godot_integration.gd` was itself a patch for one project's `ZWRuntime.gd`).

Not inspected: when Boot's 8765 path runs and the wrapped `{status, data}` response on that path; what generates `.engain_cache/parsed/scenes` and whether it should match Pass 5; text `/command` handling of combat words.

---

## 6G. Scene products: chapter workflow vs scene workflow (2026-10-18)

Read-only. "Intended" below means supported by authority notes and code defaults; it is **not** verified live integration.

### 6G.1 Two workflows over the same Passes 1–5

| | Chapter workflow (`.engain_cache/parsed/scenes`) | Scene workflow (Stageroom, served by 8765) |
|---|---|---|
| Driver | `start_button.py` STEP 2/2.7 (`44a4bfbd`, 05-03) | Chapterroom A/B/C → Passroom 1–5 → `stageroom/output/passroom/<scene_id>/` |
| Unit | whole chapter as one scene (109 files) | one scene packet per Chapterroom boundary (212) |
| Product | Pass 4 ZON fabric → `zw_compiler` → `<chapter>_with_semantics.zonj.json` → Pass 5 `events/locations/initial_state/metadata` merged in ("entities are UNTOUCHED") | Pass 1–5 artifacts per scene on disk; 8765 serves only the Pass 5 `game_scenes/<id>.json` |
| Dates | all files 2026-06-13 | 06-23 → 10-06 |
| Rebuildable now | not per code (not run): `start_button` runs `master_pipeline` from `ENGAIN_ROOT/"mettaext"` (gone); `build_scene_index.py` `CACHE_DIR` resolves to `tier3/.engain_cache` (absent) | active |

Pass 1 → `out_pass1_*.txt` (explicit structure); Pass 2 → `out_pass2_*.metta` (inferences); Pass 3 → merged ZONJ (`segments`); Pass 4 → ZON4D fabric (`@when/@where/@scope/=segments/=inferred`); Pass 5 → game scene (entity dicts with default `health` 100.0, `initial_state`, `locations`, `level_design`). Git cannot confirm the author's pass ordering (Passes 2/4/5 enter git together in `c7d509c3`, 01-22).

### 6G.2 Provisional confirmation (architect, 2026-10-18)

Chapterroom → Passroom 1–5 → Stageroom → 8765 is the **intended** current scene-product delivery path, subject to EngAInOS authority and validation. Evidence: `CHAPTERROOM_AUTHORITY_NOTE.md` ("Pass 1–5 compiles scene packets"; "Do not force Pass 1–5 to pretend a whole chapter is one scene"); `STAGEROOM_AUTHORITY_NOTE.md` (`compiled/pipeline_work`, the chapter workflow's Pass 5 source, is a "compatibility bridge only"); `bridgeroom/scene_loader.py` (default = Chapterroom/Passroom discovery; explicit `scenes_dir` = "historical flat mode"). Stageroom output is still "not accepted runtime truth unless validated/promoted". Not verified: any live load of a Stageroom packet through 8765 into 8080.

### 6G.3 What exists only in the chapter workflow

Field comparison over all files (cache 110; Pass 5 212; Pass 4 213; Pass 3 212):

- **Only in the chapter workflow:** `zon_blocks`, `spatial_hints`, `compiler_report` (incl. `validation`), all from `zw_compiler.py`; `game_metadata` (merge naming only). `zw_compiler` is referenced only by `start_button.py`; nothing in Chapterroom/Passroom runs it.
- **What `zw_compiler` does:** hard-coded canon phrase matchers → `STATE_DELTA`/`CONTEXT`/`RULE`/`EVENT` `zon_blocks`; `SPATIAL_MAPPING` regexes → canon location paths; `NAME_FIXES` name normalisation; **replaces `entities`/`@entities` with names from `CANON_ENTITIES` found in the text** (why cache entities are strings).
- **In the scene workflow but not served:** the Pass 4 fabric (`=segments`, `@when`, `@where`, `@scope`, `=inferred`, `@chapter_id`, entities observed/manifested) is written per scene but 8765 returns only Pass 5.
- **Runtime contract:** `scene_manager.py:91-103` normalises `@where/@when/@entities/=segments` (Pass 4 names) and passes through `spatial_hints/zon_blocks/compiler_report/validation` (`zw_compiler` names). That contract matches the chapter workflow's composite. The served Pass 5 packet lacks narrative `segments`, `@when/@where`, and all four compiler fields; its `events` are a small extract (one sample, `scene.003_first_contact.scene002`: 4 events, the first a dialogue line, vs 97 Pass 4 segments; not checked across scenes).

### 6G.4 Chapter continuity across the scene split

- Scene packets (`stageroom/output/chapterroom/scene_packets/<chapter>/scene.*.txt`, `engain.scene_text_packet.v1`) are text slices with a header: `@scene_id`, `@chapter_id`, `@scene_index`, boundary lines, method, authority state. No state from earlier scenes is carried.
- Passroom compiles each packet independently. No cross-scene carry mechanism found in Chapterroom or Passroom (searched `previous/prior scene`, `carry over/forward`, `continuity`, `chapter_context`, `preceding`, `inherit`); the only links are `@chapter_id` and `@scene_index`.
- `passB_scene_boundary_provider.py:208-216`: text before the first scene marker is "excluded as chapter-level material".
- Authored `continuity:` scene-meta lines are kept in segment text (`pass2_enhanced.py:648-656`), not structured.
- The chapter workflow compiled the whole chapter together, so its entities, `zon_blocks` and spatial hints spanned the chapter. That chapter-wide view has no counterpart in the scene workflow found so far.

Not inspected: MrLore's claims pipeline as a possible continuity owner; `master_pipeline.py` internals; whether Pass 5 `initial_state` differs between chapter and scene runs; `zw_world_rules_compiler.py`.

---

## 6H. Scene delivery contract: Pass 4 → Pass 5 → runtime (2026-10-18)

Bounded repair authorized and implemented 2026-10-18 (§6H.5); verified in isolation only.

### 6H.1 What happens to each Pass 4 field in Pass 5 (all 211 unambiguous pairs) — TESTED

| Pass 4 field | In Pass 5 | Count |
|---|---|---|
| `@when`, `@where`, `@scope` | `metadata.when/where/scope`, equal value | 211 |
| `@chapter_id` | `metadata.chapter_id`, equal | 208 (3 have none) |
| `@environment`, `@region`, `@terrain_family`, `@spatial_scale_hint` | top-level bare name, equal | 211 |
| `=entities_observed` | top-level `entities_observed`, equal | 202 |
| `@entities` (name strings) | transformed into `entities` dicts with `health`/`max_health` (`pass5_game_bridge.py:695-700`); equal only where both empty | 187 differ / 24 equal |
| `@id` | replaced by `scene_id` (Pass 4 `@id == scene_id` in all 212) | — |
| `=segments` | **absent** (consumed for description/events/region/level design, not carried) | 211 |
| `=inferred`, `=scene_content_observed`, `@entities_manifested`, `environment_inference` | absent | 211 / 109 / 192 / 211 |

Pairing: every scene has exactly `<scene_dir>/<scene_id>.zonj.json` (212/212, all with `=segments` as dicts carrying `text`). One directory, `scene.999_abc_smoke.scene001`, also holds an older unprefixed `999_abc_smoke.scene001.zonj.json`, so a glob would be ambiguous; an exact name is not.

### 6H.2 Runtime scene fields and their active readers — STATIC

| Normalised field (`scene_manager.py:91-103`) | Read from | Active reader | Served Pass 5 supplies |
|---|---|---|---|
| `segments` | `=segments` / `segments` | `handle_text_command` look/status (`scene_manager.py:396-420`, `seg["text"]`); `scene_extractor.extract` (not loaded at boot: "SceneExtractor not found"); `environment_manager.py:96` | **no** |
| `where`, `when` | `@where`/`where`, `@when`/`when` | look/status; vault search (`http_handlers.py:539`) | only as `metadata.where/when` → read as missing |
| `entities` | `@entities` **before** `entities` | snapshot entity sync (`scene_manager.py:168-178`), bridge | yes (dicts with health) — but a Pass 4 `@entities` would shadow them |
| `environment` | `environment` | lite behaviours read `environment.regions` (`runtime_core.py:657-668`) | a value is present; shape vs `.regions` not checked |
| `spatial_hints`, `zon_blocks`, `compiler_report`, `validation` | same names | copied into the snapshot; no other reader found in tier2 | no (chapter workflow only, §6G) |

### 6H.3 Delivery shape (as proposed; implemented per §6H.5)

At the Stageroom delivery boundary (`bridgeroom/stageroom_scene_resolver.py`, served by 8765), for `scene_id`:

```
payload = <Pass 5 game_scenes/<scene_id>.json, unchanged>
        + "=segments": Pass 4 <scene_dir>/<scene_id>.zonj.json ["=segments"]   # only field taken from Pass 4
        + "where": payload["metadata"]["where"]                               # translated from Pass 5, not copied from Pass 4
        + "when":  payload["metadata"]["when"]
```

- Never taken from Pass 4: `@entities` (would shadow Pass 5 entities), `@when/@where/@scope/@chapter_id` (already in Pass 5 metadata), `=inferred` and the rest (no runtime reader).
- Identity guard: Pass 4 `@id` must equal `scene_id`; exact file name, no glob; a missing or mismatched Pass 4 artifact raises, matching the resolver's existing fail-closed `ValueError` behaviour.
- Alternative for `where`/`when`: the runtime normaliser reads `metadata.where/when` instead; a runtime change, not chosen here.
- Out of scope: cross-scene continuity carry (§6G.4); `zw_compiler` fields (manuscript-specific matchers, §6G.3); D13/D15 combat execution.

### 6H.4 Test plan for the repair (when authorized)

1. Unit, resolver only (no servers): for `scene.003_first_contact.scene002`, the served payload has 97 `=segments`; `entities` is identical to the Pass 5 file's (dicts with `health`); no `@entities` key; `where`/`when` equal `metadata.where/when`; every other Pass 5 key unchanged.
2. Unit, fail-closed: a scene whose Pass 4 file is missing or whose `@id` differs raises; `scene.999_abc_smoke.scene001` resolves to the prefixed file only.
3. Unit, regression: all 212 indexed scenes resolve without error.
4. Integration (in-process, no ports): feed one resolved payload to `SceneManager.load_scene`; `snapshot["scene"]["segments"]` non-empty; `snapshot["entities"][id]["health"]` present; `status` reports non-zero segments; `look` returns narrative text; `check_complex_rules` allows an attack between two loaded entities.
5. Existing suites unchanged: `tier2/godotsim` tests and bridgeroom scene-server tests.

### 6H.5 Implemented (2026-10-18) — TESTED IN ISOLATION

- `bridgeroom/stageroom_scene_resolver.py`: `_delivery_packet`, applied in `load_scene` only (listing unchanged; a bad Pass 4 affects only its own scene). Adds `=segments` from exactly `<scene_dir>/<scene_id>.zonj.json`; `where`/`when` from the packet's own `metadata` when no `where`/`@where`/`when`/`@when` exists; nothing else from Pass 4. Raises `ValueError` on `@id` mismatch, non-list/non-dict segments, a symlinked Pass 4, or both current and legacy (`<scene_id minus "scene.">.zonj.json`) names present. A packet already holding segments is served without reading Pass 4; with no exactly named Pass 4, Pass 5 is served unchanged. Flat `SceneLoader` mode untouched.
- Tests: `tier1/engainos/tests/test_scene_loader_stageroom.py` 40 pass (31 existing unchanged + 9 delivery). New `tier2/godotsim/test_stageroom_scene_delivery.py` 3 pass (real resolver, `SceneManager`, AP rules, combat adapter; stub runtime): `look` returns narrative; `snapshot["entities"]` carries health; a valid attack passes AP and is **only queued** — target unregistered, snapshot health unchanged. Full `tier2/godotsim` suite: 33 pass.
- Real Stageroom data (read-only): `scene.003_first_contact.scene002` → 97 segments, entities identical to the Pass 5 file, no `@entities`, only `=segments/where/when` added. 211/212 scenes load with segments.

Review outcomes:
- **Smoke scene rejected (by design).** `scene.999_abc_smoke.scene001` holds two Pass 4 files claiming the same `@id`; they differ (`@entities`, `@region`, `@when`, `@where`, `metadata`, `region`). Evidence identifies the true pair: the Pass 5 packet matches the prefixed file (same mtime; `where`/`when`/`region` match), the unprefixed file is an earlier run (~8.4 h older). The current writers emit the prefixed name (`pipeline_runner.py:123`, `pass4_zon_bridge.py:864`). Resolution is an operator action on generated output (remove or archive the stale unprefixed file), not a resolver change. No code, gate, tool or Godot script references the smoke scene (one comment in `vaultroom/vault_source_index.py`).
- **Missing Pass 4 is permissive (safeguard 5).** No real scene is affected (212/212 have the exact file), but such a scene would load without narrative and `look` would show placeholder text, silently. Making it fail closed would change the expectations of existing fixture tests that write Pass 5 only; left as an open decision.

Unverified: live 8765 → 8080 load; Godot's Boot path, which receives the wrapped `{status, data}` 8765 response.

---

## 6I. Combat registration, execution and snapshot commit (2026-10-18)

Authority (architect): `EngAInRuntime.snapshot` owns health and `alive`; `Combat3DAdapter` is per-step working state only.

### 6I.1 Implemented

| Step | Where | Behaviour |
|---|---|---|
| Registration | `scene_manager.select_active_scene`, after `snapshot["entities"]` is set | `combat.reset()` (drops previous scene's working state and pending hits), then `register_entity(id, health, max_health, alive=…)` for entities with numeric `health`/`max_health`; ids containing `/` skipped (not addressable by `_apply_delta` paths) |
| Queue | `command_dispatcher` | after `RuntimeGateway.submit` (identity, mode, canon, AP) accepts, `runtime.add_command({…, "command": "combat/damage"})`; ack `{"type":"ack","status":"queued","command":"combat/damage"}` (was `damage_applied`) |
| Execute | `runtime_core._execute_command` | `combat/damage` branch → `combat.handle_delta("combat3d/apply_damage", combat_damage_payload(cmd))`, after the existing execution-time REPLAY/FINALIZED re-check; sim thread |
| Commit | `runtime_core._step_combat`, called from `_process_tick` only when hits are queued | re-seed adapter from `snapshot["entities"]` (same thread as commit, so newer snapshot values win; entities that left are unregistered), `combat.tick()`, then `_apply_delta({"domain":"combat3d","op":"set","path":"entities/<id>/health"|".../alive","value":…})` only for entities present at re-seed and only where the value changed. Follow-up action tuples are not consumed |

Unchanged: AP rules, spatial/perception/behaviour kernels, inventory/dialogue ticks (still off), HUD, Godot, continuity. Sim cadence unchanged (combat runs inside the existing `_process_tick`; the kernel ignores `dt`).

### 6I.2 Tests (isolated) — TESTED

`tier2/godotsim/test_combat_commit.py`, 12/12 (real `EngAInRuntime` with `_simulation_loop` patched out; real gateway, dispatcher, adapter, kernel):
- **Queued:** scene load seeds working state from the snapshot; an accepted hit is only queued (1 in `command_queue`, adapter empty, health 100); an AP-rejected hit queues nothing.
- **Executed:** drain moves the hit into the adapter once (health still 100); REPLAY during drain blocks it; inventory/dialogue `tick` never called.
- **Committed:** one hit → 90 and stays 90 over further drains/ticks (`alive` not written); lethal → 0, `alive: False`; newer snapshot value respected (50 → 40); an entity removed before the tick is not recreated; scene switch drops pending hits; committed health feeds the next AP check (attacker at 5 rejected).

`test_gateway_combat_rules.py` now asserts the queued payload instead of the adapter call; it previously passed only because its live sim thread drained the queue in time, and a `Mock` combat would have raised in `_step_combat` every tick. Full `tier2/godotsim` suite 45/45 (three consecutive runs); `test_scene_loader_stageroom` 40/40.

### 6I.3 Live smoke (2026-10-18) — LIVE, runtime HTTP only

Neither service was running; this session started `python3 -m tier1.engainos.bridgeroom.scene_server` (8765) and `python3 -m tier2.godotsim.sim_runtime` (8080) from the working tree, then stopped both. No tracebacks in the runtime log; no repo paths created or changed. Identity on every mutation: `reality_mode: DRAFT`, `actor_authority_tier: 1`.

| # | Request | Response / observation |
|---|---|---|
| 1 | `GET 8765/load_scene?scene_id=scene.001_the_garden_genesis.scene002` | 200 `status: success`; 182 `=segments`; `where: Realm/Physical/Unknown`; no `@entities`; mordain, pelagor, syreth, theron, vaelith at 100/100 |
| 2 | `POST 8080/scene/load` (the delivered scene + identity) | 200 `status: loaded`, `scene_id: scene.001_the_garden_genesis_scene002` (runtime canonical form) |
| 3 | `GET 8080/snapshot`; `POST /command {"text":"look"}` | `entities.mordain/pelagor.health` 100.0, `max_health` 100.0; `look` → `total_segments: 182`, `where`/`when` populated, 5 entities present |
| 4 | `POST 8080/combat/damage {source: mordain, target: pelagor, damage: 10}` | 200 `{"type":"ack","status":"queued","command":"combat/damage"}` |
| 5 | `GET 8080/snapshot` (polled) | within 0.1 s: pelagor `health` 90.0; mordain 100.0 |
| 6 | `POST 8080/combat/damage {source: mordain, target: mordain}` | 403 `governance_rejected`, "Cannot attack yourself"; after 0.5 s: mordain 100.0, pelagor 90.0 |

Verified: the runtime HTTP path (8765 delivery → 8080 load → AP → queue → execute → commit into `EngAInRuntime.snapshot`). **Not verified:** any Godot client or the 8090 HUD observing the result (the current Godot project sends no combat request and reads no combat fields; the HUD reads a shape the runtime does not export, D17).

### 6I.4 Remaining (separate defects)

- `look`'s first lines are the scene text packet's `@scene_id/@chapter_id/...` header, which Pass 1 carries as segments (Passroom content; not addressed).
- Scene load runs on the HTTP thread and can race the sim thread's `_step_combat` (same existing race as the snapshot flush).
- Two hits queued in one tick are AP-checked against pre-tick health.
- Combat follow-up actions (`dead`/`low_health` flags, `navigation3d/disable`) have no consumer.
- The 8090 route forwards no identity fields (400 at 8080, §6F); HUD shape (D17); inventory/dialogue ticks and registration (D13/D15 remainder).
- The runtime rewrites `scene.<chapter>.sceneNNN` to `scene.<chapter>_sceneNNN` on load (existing canonicalisation; not examined).

### 6I.5 Architect's live run (2026-10-18) — LIVE, runtime HTTP only

The architect started both services from the working tree at `772bc7f4` (`python3 -m tier1.engainos.bridgeroom.scene_server`, `python3 -m tier2.godotsim.sim_runtime`) and repeated steps 1–5 of §6I.3 with curl: same scene, same identity fields (`reality_mode: DRAFT`, `actor_authority_tier: 1`). The results match §6I.3: 8765 delivered the scene; 8080 loaded it as `scene.001_the_garden_genesis_scene002` with 182 segments and 5 entities; `combat/damage` mordain → pelagor, 10 → `{"type":"ack","status":"queued","command":"combat/damage"}`; after 1 s, pelagor 90.0 / 100, mordain 100.0 / 100. Step 6 (AP rejection) was not repeated and is covered only by §6I.3. Godot and the 8090 HUD were not involved.

What the run verifies, and what it does not:

- **Verified:** the AP rules evaluated the request correctly on the inputs they were given (attacker health ≥ 10, not a self-attack), and the accepted hit was executed and committed into `EngAInRuntime.snapshot`.
- **Not verified:** who sent the request. `reality_mode`, `actor_authority_tier` and `actor_id` came from the request body, chosen by the caller (D18). A correct AP verdict computed on a self-declared tier is not authorization: a refusal invariant such as "cannot attack yourself" is only as strong as the identity and authority inputs fed to the rules.

Observations from the run logs. None is a combat failure:

- **Misleading trace (STATIC).** `[TRACE_SCENE030][HTTP_SCENE_LOAD_ENTRY] ... body_segments=32`. The counter at `tier2/godotsim/http_handlers.py:354` falls back to `body["events"]` when the body has no `segments` key. Stageroom delivery sends `=segments`, so 32 is the Pass 5 event count, not a segment count. The following trace line, `doc_segments=182`, is the real segment count. Logging defect only; no data lost.
- **MCP warning (OPEN).** `[ENV_MANAGER] Failed to initialize MCP session: All connection attempts failed`, printed after the scene load from `tier2/godotsim/environment_manager.py:47`. `sim_runtime.py:92` points `EnvironmentManager` at `http://127.0.0.1:8000`. Whether a service is meant to listen there, and what depends on that session, was not investigated.
- **SemanticBridge import (OPEN).** The run also logged `[BRIDGE] semantic_bridge not available: attempted relative import with no known parent package`. This is likely the cause of the boot warning `SemanticBridge not found`; not verified. `SceneExtractor not found` at boot remains untraced.
- **Scene-ID rewrite (remains, §6I.4).** Requested `scene.001_the_garden_genesis.scene002`; the runtime id is `scene.001_the_garden_genesis_scene002`.
- **Empty snapshot (UNRESOLVED).** An empty snapshot was reported before a successful reload; that query is not in the captured output. A fresh 8080 runtime holds no scene until `/scene/load`, so a query made before loading would be empty, but whether that is what happened is not established. Recorded as an observation, not a diagnosed defect.

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

| D13 | Combat, inventory and dialogue kernels never run: their ticks were dropped in `5f213ca5` | accepted damage stays in `combat.pending_damage`; HP never changes (§6A.4). **Combat fixed 2026-10-18 (§6I)**; inventory and dialogue ticks remain off | combat: TESTED + LIVE (runtime HTTP); inventory/dialogue: unresolved |
| D14 | Combat adapter crashes against the canonical kernel's dict alerts | `Combat3DAdapter` + queued damage + `tick()` → `ValueError` (§6A.4) | TESTED. **Fixed in working tree, uncommitted** (§9); `tier2/godotsim/test_combat3d_adapter.py` |
| D15 | No entities registered with the combat/inventory/dialogue adapters | `Combat3DAdapter` starts empty; no live `register_entity` caller (§6B). **Combat fixed 2026-10-18**: `select_active_scene` registers entities with numeric `health`/`max_health` (§6I); inventory/dialogue unregistered | combat: TESTED + LIVE; inventory/dialogue: unresolved |
| D16 | Scene health does not reach the runtime **from the `.engain_cache` scene source** (re-scoped 2026-10-18) | Stageroom Pass 5 packets (served by 8765) carry per-entity `health` and it survives to AP (allowed). `godotnew/semantic` posts `.engain_cache/parsed/scenes/*.zonj.json`, whose entities are strings; health exists only in `initial_state.combat.entities`, which nothing reads, so AP sees 0 and rejects (§6F). Open question: which scene source is authoritative | TESTED (AP rule, both shapes); unresolved |
| D17 | 8090 HUD reads a combat shape the runtime never exports | `/api/hud/combat` reads `combat.entities[id]`; export has `entity_hp`, not `entities` → always health 0, dead (§6B.3) | STATIC |
| D18 | **CRITICAL — authority boundary: caller identity is unverified.** `actor_id`, `actor_authority_tier` and `reality_mode` are read from the request body (`tier2/godotsim/runtime_gateway.py:114-117,138-147`; 8090 `aproom/authority_gate.py:531`, §4.1) with no authentication or provenance. The AP rules then evaluate correctly, but against whatever the caller declared. Tracked separately from D2 (the tier value has no bounds) and D4 (unknown mode becomes DRAFT): D18 is that no actor-identifying field is trusted input at all, so any caller can present any actor, tier or mode | D2's repro (self-claimed tier 3 + `FINALIZED` accepted); §6I.3/§6I.5 combat accepted at a caller-declared tier 1 | STATIC (source) + TESTED (via D2) + LIVE (combat route, declared tier 1); impersonation on the combat route not exercised |

D1–D4 are the most direct contradictions of "nothing changes runtime state unless EngAInOS allows it." D18 underlies D2 and D4: bounding the tier or the mode does not help while the caller supplies both. No defect here permits writing canon history: the timeline fence held (§6).

**Architect priority (2026-10-18):** resolve D18 before exposing combat through any additional client. A system can correctly reject self-attacks and still have a serious authorization gap if a caller can impersonate a higher authority.

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
