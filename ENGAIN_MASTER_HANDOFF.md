# EngAIn Master Handoff

**Updated:** 2026-10-27 · **EngAIn HEAD:** `e0b4b0db` (2026-10-18) · **Trixel 3.2D HEAD:** `fd39ff1` (2026-09-24)

This is the single entry point. Read it before changing anything, then the subsystem doc it points to.
It is an index: it doesn't replace the subsystem handoffs, contracts or findings, and it doesn't restate them.

**The rule:** read this file first. When you finish, update your subsystem's handoff. Update this file only when overall status changes.
**Handoff vs handshake:** a handoff says where work stopped and what comes next. A handshake says how systems connect and which connections work. For handshakes, see [`HANDSHAKES.md`](HANDSHAKES.md).
`AGENTS.md` still governs every safety, authority and mutation rule. Nothing here overrides it.

---

## 1. What EngAIn demonstrably does today

| Capability | Evidence | Source |
|---|---|---|
| Stack boots: 8080 sim runtime, 8765 EngAInOS/AP scene server, 8090 authority gate (8766 Trixel tile server not started) | LIVE 2026-10-16 | Baseline §2 |
| Stageroom scene → 8765 → Godot Boot → 8080 `/scene/load` | LIVE, scene 045, 2026-10-15 | Baseline §2 |
| Main scene chooser → 8080 load and snapshot sync | LIVE, scene 006, verified by the user 2026-10-16 | Baseline §2 |
| Pass 4 narrative segments delivered through Stageroom | TESTED in isolation (`34c215ea`) | Findings §6H.5 |
| Combat: `/combat/damage` → AP rules → kernel → committed into the runtime snapshot | LIVE over runtime HTTP, architect's run 2026-10-18 at `772bc7f4`: pelagor 100 → 90 | Findings §6I.5 |
| Kernel ↔ Godot boot handshake (file drop) | WIRED and proven | HANDSHAKES §4 |
| Mettaext Gen2 first lever: entities, locations, presence, aliases | RUNNING (`567392ba`, 2026-10-06; commit message reports 59 tests passing) | Gen2 design |
| Trixel 3.2D: first editable art bound onto the proven courtyard geometry | Frozen, tag `TRIXEL32D-FIRST-ART-ON-WORLD` (`84682b8`) | trixel3.2d freeze receipt |
| Trixel Lane A terrain-state proof | TESTED 2026-10-27: 20 passed, 100 subtests (uncommitted) | Recovery handoff §1 |

**Not demonstrated:**
- No trusted caller identity (D18).
- Inventory and dialogue kernels don't tick (D13/D15).
- Trixel surface transport is unwired.
- Cartographer, Paradox Machine, Engionality and MrLore have no runtime caller.
- `/world/sync` is broken.

## 2. Subsystems: status and where to read

| Subsystem | Status | Read |
|---|---|---|
| **EngAInOS / authority / runtime** | Last active (to 2026-10-18). Combat path fixed (D3, D13–D15). **D18 is CRITICAL and open.** | [`docs/architecture/ENGAIN_AUTHORITY_FINDINGS_2026-10-17.md`](docs/architecture/ENGAIN_AUTHORITY_FINDINGS_2026-10-17.md) §6J, §7 |
| **Architecture overall** | Baseline of lanes, live paths and governing direction | [`docs/architecture/ENGAIN_ARCHITECTURE_BASELINE_2026-10-16.md`](docs/architecture/ENGAIN_ARCHITECTURE_BASELINE_2026-10-16.md) (§8a is its own session handoff) |
| **Switchboard / authority delegation** | Spec v0.3, not implemented | `switchboard_authority_delegation/temporay implimentation spec and docs/` |
| **Mettaext (legacy)** | LIVE output; emits keyword-vote terrain labels, which cross a line Gen2 forbids | `tier3/mettaext/chapterroom/CHAPTERROOM_AUTHORITY_NOTE.md`, `tier3/mettaext/stageroom/STAGEROOM_HANDOFF_RULE.md` |
| **Mettaext Gen2** | Designed; first lever running; spatial/terrain/temporal/affect sections unimplemented; blocked on open decisions | [`mettaextgen2/METTAEXT_GEN2_DESIGN.md`](mettaextgen2/METTAEXT_GEN2_DESIGN.md) §11, `GEN2_OUTPUT_CONTRACT.md`, `DRAGON_HANDSHAKE_MAP.md` |
| **Topologist → Cartographer** (`tier2/topologist`, `tier2/cartographer`) | **Seam proofs: structural checks only, no consistency checking** (audited 2026-10-28, read-only).<br>• Contradictory, figurative and time-ordered relationships all pass Topologist's validator and gate as `accepted_spatial_truth`.<br>• Cartographer then records every relationship as "applied" without checking it.<br>• The consistency checking designed in Topologist's research doc (path-consistency, conflict resolution) was never built.<br>• **Don't take "accepted_spatial_truth", "topologically clean" or "applied" at face value.**<br>• No runtime caller; don't wire either into the runtime or Godot until consistency checking exists. | `tier2/topologist/research/Prose Geometrical Topologist Research.txt` (lines 125–160), `docs/architecture/MILESTONE_007_CARTOGRAPHER_METRIC_LAYOUT_PROOF.md` §13 |
| **Trixel 3.2D** (separate repo `../trixel3.2d`) | Pixel-geometry Phases A–D committed; Lane A done and tested, uncommitted | `../trixel3.2d/docs/TERRAIN_STATE_LANE_A_CONTRACT_V1.md`, `../trixel3.2d/docs/TRIXEL32D_FIRST_ART_ON_WORLD_FREEZE_RECEIPT.md` |
| **Dragon** (`/mnt/data-drive/godot_engain_3d_avatar`, HEAD `8f9982f` 2026-09-23; 137 uncommitted entries) | Runs on the old bound session; `--fresh-session` fails safely at the first Hermes response. **Elemental combat presenter** (`scripts/ElementalCombatPresentation3D.gd`, passive: displays resolved turns only, and never touches health, chains or identity) passed its focused test 2026-10-27: `godot --headless --path . --script tests/test_elemental_combat_presentation.gd` → `OK passive_elemental_presentation` (health and identity unchanged, unresolved visible, stale avatar rejected and rebound). Reported by Dragon and not rerun here; the presenter is untracked. This is focused verification, not suite green. | Tail of `mettaextgen2/mettaextgen2.md`; recovery handoff §4 |
| **Godot clients** | Two separate experiences: `~/Downloads/godotnew/semantic` and the EngAInOS Boot Shell. Keep them separate. | Baseline §2 |
| **Combat / magic design** | **FROZEN 2026-10-26.** Reference: GitHub `SmokesBowls/battletest` `4071e3e` | `../building_the_world/lore library/magic/SESSION_HANDOFF_2026-10-20.md`; `tier2/godotsim/ENGAIN_COMBAT_MAGIC_SPEC_v0.1.md` (untracked) |

The detailed commit, status and test record for 2026-10-27 is [`../RECOVERY_HANDOFF_2026-10-27.md`](../RECOVERY_HANDOFF_2026-10-27.md), outside the repo.

## 3. Unfinished work and deliberate stop points

**Uncommitted in EngAIn** (`git status --short`, 2026-10-27):
```
 M docs/architecture/ENGAIN_AUTHORITY_FINDINGS_2026-10-17.md   +80: §6J D18 identity map and architect questions (read-only audit)
 M runtime/sessions/5b5fd1f5…bdba2e.journal                    runtime journal; generated, don't hand-edit
 M tier1/engainos/server/presence_authority_server.py          +17/-2: quiet access logs for successful /claim and /release only
 M tier1/engainos/tests/test_presence_authority_server.py      +106: 7 tests for that logging change (not run 2026-10-27)
?? tier2/godotsim/ENGAIN_COMBAT_MAGIC_SPEC_v0.1.md              frozen magic spec
?? ENGAIN_MASTER_HANDOFF.md                                    this file
```
**Uncommitted in trixel3.2d:**
- Lane A: contract, plan, fixtures, `trixel/terrain_state/`, gate and 2 test files.
- A modified courtyard `.blend` and its `.blend1` backup.
- 5 PDFs in `proposals/`.

**Deliberate stops:**
- **D18 before any new client:** resolve it before exposing combat through any additional client (architect priority, 2026-10-18).
- **The §6J.7 repair is PROPOSED, NOT DECIDED:** a fixed server-side tier per HTTP entry point. It waits on the §6J.8 answers.
- **Lane A has no integration authority:** "Do not commit or push" until the user accepts it.
- **Dragon:** don't rotate the real session until the bootstrap-response parser is understood.
- **Magic and combat design:** frozen. The Dragon presenter predates the 2026-10-25 delivery-pattern decisions: it was written 2026-10-22 and treats `plasma` as a presentation form. Recheck it against "magic does not carry across attacks" when magic unfreezes.
- **Dragon (2026-10-27):** not being worked on.
  - The presenter's test fix replaced `Dictionary.pop()`, which doesn't exist in GDScript, with copy-then-`erase()`.
  - That run's verifier `hermes-verify-iH7mYP.sh` was removed.
  - **9 older `hermes-verify-*` files** are still in `/mnt/data-drive/EngAIn_Recovery/07_TMP/`.

## 4. Architectural decisions: don't casually reconnect

- **Authority:** the Python runtime and EngAInOS own state. Godot and UPBGE render or request changes (AGENTS.md §Client authority).
- **Three layers:** runtime / reusable engine integration / individual engine project. Never treat one project's choices as the universal contract (AGENTS.md).
- **Preserved isolations** are intentional; don't "fix" them (HANDSHAKES §11.6). AP rule engines are three distinct things (HANDSHAKES §9).
- **Trixel:** 3.2D is the only Trixel with a future (eviction decision 2026-07-16). The facade artwork bridge was removed on purpose (HANDSHAKES §7b).
- **Gen2:**
  - It inherits scene identity from Chapterroom and never creates it.
  - Cues are allowed; interpretations are forbidden.
  - EngAInOS governs twice: `ADMITTED_EVIDENCE`, then `ACCEPTED_DERIVED_TRUTH`.
  - MrLore is advisory in the Mettaext → EngAInOS flow.
- **Chapterroom:** scene boundaries stay drafts until accepted along the authority path. `authored_scene_boundaries_proven` is a source fact, not an acceptance.
- **Integrating a new system** needs an Integration Impact Statement (HANDSHAKES §11.8).

## 5. Next authorized action

**Safe without approval** (read-only or tests in isolation):
1. Run the presence-authority tests from a scratch copy, so nothing writes to real runtime logs, and report the result.
2. Review Lane A against its contract so the user can decide on acceptance.
3. Dragon: capture the raw first Hermes response, under the plan's constraints (audit first; don't rotate the session).

**Needs the user's or architect's decision first:**
- **D18:** the §6J.8 questions, before any code. Then the §6J.7 repair.
- Committing anything: Lane A; the presence-server logging change; the §6J findings.
- The Gen2 open decisions (Gen2 design §11): identity split, sequencing, proposal envelope, reconciler, registry scope.
- Which scene source is authoritative (D16).
- Unfreezing magic and combat.

---
*Maintenance: keep this file short. Put detail in subsystem docs and link to it. Date each update in the header.*
