# EngAIn Combat & Magic — Consolidated Draft v0.1

> Compiled from discussion, not final law. Individual modules are also in the ZIP.



---

# EngAIn — Combat & Magic Design Archive

**Version:** 0.1 — conversation-derived design capture, 2026-10-19  
**Status:** DRAFT / PROVISIONAL, not an implemented or approved authority contract.  
**Purpose:** Preserve the author's decisions from the design discussion, recover original magic ideas, and make future implementation/auditing possible without redefining ZW, AP, or Combat3D.

## Contents

| File | Focus |
|---|---|
| `01_BATTLEFIELD_SPATIAL.md` | Four-character arena, platforms, base forms, entity footprints, facing and movement |
| `02_COMBO_LOCKS_PROGRESS.md` | Platform combo locks, dual/triple qualifications, mastery |
| `03_MAGIC_TARGETING_PROPAGATION.md` | Single, chain, AoE, Lightning routing, collision and spell state |
| `04_ELEMENTAL_RULES_AND_EXAMPLES.md` | Original recovered spell examples and provisional integration |
| `05_COMBAT_RUNTIME_CONTRACT.md` | Simulation ownership, effects, AP/ZW boundaries, event design and pseudocode |
| `06_TEST_CALIBRATION_PLAN.md` | Phased implementation and nonlethal combat measurement |
| `07_OPEN_DECISIONS_AND_PROVENANCE.md` | Unresolved ambiguities, preservation/source notes, decisions checklist |

## Evidence hierarchy

- **AUTHOR RULE** — explicitly established or corrected by the author in this conversation.
- **RECOVERED DOCUMENT** — content read from the author's Google Drive magic documents; *historical source*, not necessarily current canon.
- **DESIGN PROPOSAL** — suggested during discussion, useful but not author-approved.
- **OPEN** — conflicting, incomplete or still to be determined.

Don't promote proposals to canonical rules without author review. Do not mistake implementation suggestions for existing code.

## Scope and non-goals

- EngAIn remains **manuscript-agnostic** and **rendering-engine-agnostic**.
- ZW supplies semantic definitions, AP remains the authority boundary, Combat3D resolves actions, runtime snapshot owns authoritative simulation state, Godot or other clients present results.
- No hardcoded Burdens-specific names in universal runtime rules.
- This archive contains **design**, not an assertion that Combat3D currently implements magic, platforms, status effects, or combo progression.
- Preserve original lore documents; no destructive moves, canon rewrites or code changes were made.

## Prior art and source references

Author's Google Drive documents examined in conversation:
- [Single chains](https://docs.google.com/document/d/1J75TY9TbLd-G1AMM33inEnTAhofJD-t8_bCOWpgDy5c/edit)
- [Triple chains.txt](https://drive.google.com/file/d/1DpZvKPowTtZGFn7OjRvmqVTr3FXl2nrc/view)
- [Earth chain.txt](https://drive.google.com/file/d/1T7zFnJeQxa08cDbw0mrU3QOSvI228lYR/view)
- [Water chain.txt](https://drive.google.com/file/d/1JoBoE1Ok38j9uscvuKjjbijRG1iqSPep/view)
- [Fire chain.txt](https://drive.google.com/file/d/1rCdJa07KvQGgeYgfMxpkL1U8WA5k_bJe/view)

Also author-described local files under `building_the_world/`: `vale magic.txt`, `magic tree.txt`, `magic tree 2.txt`, character-specific magic files, `character effects.txt`. Their contents were **not comprehensively audited** in this session.

Original drawings and screenshots were supplied in conversation. The labels in text below are a working transcription; use the original images to confirm the exact orientation and routing before encoding geometry.


---

# Battlefield, Platform Topology and Base Forms

## 1. Battle presentation [AUTHOR RULE]

- Old-school Final Fantasy-style battle screen, modified: **four party characters stacked vertically on one side**, enemies and larger combat space on the remainder.
- An attacking character runs toward the target instead of the old bounce-forward-three-times convention.
- After attacking, the character chooses **Stay** near the enemy or **Return** to party formation.
- Stay: defense advantage against the enemy whose platform the character occupies; rear attack exposure reduces guard. Front/side incoming attacks have **no added directional guard modifier** (the enemy-specific stay bonus is its own condition).
- Return: temporarily lowered guard while back-turned during return. Timing and precise modifiers OPEN.
- Two characters may occupy the same platform. This is allowed, but creates **very high combo obstruction/failure risk**; no numerical failure probability selected.
- On-object platforms (body/back/shoulder etc.) are **boss/special encounters only** and must be explicitly authored. Regular battle pads surround enemy footprint.

## 2. Six platform *types* [AUTHOR RULE]

The author drew and numbered six types; platform numbers are **configuration-local labels** reused by any enemy of that type. They are not global unique instance IDs.

| Type | Count | Labels | Initial access |
| --- | ---: | --- | --- |
| 1 | 1 | 1 | Introductory enemies |
| 2 | 2 | 2–3 | Introductory enemies |
| 3 | 4 | 4–7 | Introductory enemies |
| 4 | 6 | 8–13 | Combo-capable encounters |
| 5 | 8 | 14–21 | Combo-capable encounters |
| 6 | 10 | 22–31 | Larger/later encounters |

Total **31 type-specific labels** across the six layouts, **not** 31 pads concurrently on one enemy.

The author's final screenshot/diagram is the geometric reference. An earlier assistant transcription placed type 4 and later pads by top/bottom, but the author also discussed attack-facing orientation; **do not infer global front/back from screenshot page orientation alone.** Preserve the numbering and verify placement vectors from author drawings before writing coordinates.

### Address identity

Correct: `(battle_id, enemy_instance_id, platform_label)` e.g. `(b_017, wolf_b, 6)`.

Incorrect: `platform_6` as a battlefield-global primary key: three enemies can each have a pad 6 simultaneously.

## 3. Three spatial concepts [AUTHOR RULE]

1. **Enemy footprint**: actual space occupied by entity; potentially spans several terrain cells; influences collision/position and directional attack propagation.
2. **Launch / landing pads (numbered platform positions)**: relative to enemy; where characters stand after attacks, where magic contacts a configured enemy, and where local chain routes or combo locks apply.
3. **Base forms (environmental grid)**: fixed terrain cells beneath and extending beyond the enemy footprint and landing pads. Same grid scale as pads in the author's diagrams, but **not** the same state object.

Effects to distinguish:
- Direct entity effect (HP, slow, burning etc.) attached to entity for declared lifetime.
- Spatial/environmental effect (unstable ground, mud, lava, steam) attached to **base-form cells**; remains at world location if enemies move away.
- Pad route/occupancy/numbering is spatial interface, **not persistent terrain storage**.
- AoE footprint may cover pink standing locations. Any eligible occupant of affected cells can be hit, including allies if that spell's friendly-fire policy permits it. Source of AoE is not constrained to pad network.

**OPEN:** How to preserve a spell's *chain qualification* at an attack contact when enemy pads follow moving enemies but terrain conditions remain fixed. Candidate: resolve current pad's world-overlapped base-form cells at moment of contact; no automatic attachment of old terrain condition to moving enemy.

## 4. Geometry and connections [AUTHOR RULE / OPEN]

- A platform geometry template may be proportionally placed around enemy physical dimensions, not around arbitrary HP levels.
- **Combination-lock connections**, **Lightning traversal connections**, and **terrain-cell adjacency** are distinct graphs. They must not be silently assumed identical.
- Actual physical proximity is not sufficient to make a character combo valid; authored lock relationships decide.
- The field has a broader environmental grid on which enemies can reposition and attacks can pass through.
- A 10-pad arrangement has side middle pads 24 and 29; author floated **90% rather than 100%** effect for them. Not finalized.
- Attack-direction penetration percentages **100%, 60%, 20%, 5%** were proposed as test settings, not canonical damage constants. They indicate first/front-facing hit, rear-facing hit, further/behind hit, far rear hit in examples. Exact relationship to facing, actual targets and damage math OPEN.

## 5. Spatial declaration sketch [DESIGN PROPOSAL ONLY]

```text
Battle:
  entities: [<instance ids>]
  base_forms: world_grid[<cell ids and persistent effects>]
  enemy_instances:
    <enemy_instance_id>:
      platform_type: 4
      footprint: <authored or derived extent>
      orientation: <facing>
      platforms:
        8: {local_position: ?, occupants: []}
        9: {local_position: ?, occupants: []}
        ...
      combo_locks: <authored references>
      lightning_paths: <authored local edges>
```

Positions/edges shown with `?` are intentionally missing rather than invented.


---

# Character Combos: Locks, Obstruction and Learning

## 1. Author-approved platform progression

- Types 1–3 (pads 1–7) are early enemies; no character combination availability is required.
- Type 4 (6 pads) introduces defined two-character locks.
- Type 5 (8 pads) adds paired pads along multiple sides.
- Type 6 (10 pads) supports pairs and dedicated three-along-side triples.
- **Combo availability is not identical to elemental chain magic**. Character team formations and spell-element progressions are separate mechanics that can interact.

## 2. Specified two-character combo pad locks [AUTHOR RULE]

| Type | Dual pad locks explicitly specified |
| --- | --- |
| 4 (8–13) | `{8,13}`, `{10,11}` |
| 5 (14–21) | `{14,21}`, `{15,16}`, `{17,18}`, `{19,20}` |
| 6 (22–31) | **OPEN** exact authored pairs. Prior assistant *proposed* `{22,31}`, `{26,27}`, `{23,24}`, `{24,25}`, `{28,29}`, `{29,30}`. Not yet author ratified. |

Here `{a,b}` denotes a **platform pair lock** for character combo eligibility, NOT a Lightning path or world-grid adjacency.

## 3. Three-character combos [AUTHOR RULE / INFERENCE]

- Author suggested **three along left side** and **three along right side** of the 10-pad configuration as basic positional triple locks.
- Based on numbered diagram, likely candidate groups are `{23,24,25}` and `{28,29,30}` **[DESIGN PROPOSAL; verify exact side assignments]**.
- Triple combination eligibility itself requires a learn/unlock condition; position alone doesn't grant skill.
- At **mastered triple** level, any *valid two-platform lock* may accept an eligible third platform in a permitted relation, even on the 6-pad enemy.

Author's concrete advanced examples:

| Existing dual lock | Eligible added single | Advanced triple |
| --- | --- | --- |
| 8+13 | 9 | 8+13+9 |
| 8+13 | 12 | 8+13+12 |
| 10+11 | 9 | 10+11+9 |
| 10+11 | 12 | 10+11+12 |

These are explicit examples, not proof that **any** third pad qualifies for **every** dual lock.

## 4. Obstruction [AUTHOR RULE]

- Multiple allies can stand on one enemy platform.
- An attempted combination using overcrowded/overlapping positions has an **extremely high chance of failure**, not automatic disqualification.
- Do not invent the exact failure chance; tuning is empirical.
- 'Cannot attempt' (no eligible lock/qualification) differs from 'valid attempted combo that fails' (obstruction/random result).

## 5. Learning progression [AUTHOR INTENT; implementation details PROPOSED]

Author: use combinations to improve them; a qualifying condition must exist to learn combos **at all**, and another to learn/perform triple combos.

Suggested separate facts:

- Known/unlocked ability for character(s)
- Qualified participants and required learned skills
- Pair/trio coordination progression through actual use
- Attack-specific proficiency
- Eligibility of current physical platform lock

Do not silently tie combo mastery to elemental chain mastery. Exact thresholds, experience awards, failed-attempt learning, and whether learning is per party/pair/trio are OPEN.

## 6. Action lifecycles

Character attacks enemy → chooses stay/return → formation occupancy updated → if eligible members occupy pads satisfying a lock, allow combo action when learned and other conditions hold → roll obstruction if overlapping → resolve combo's authored effects. Enemy response, timing and cooldowns remain OPEN.


---

# Magic Targeting, Routing and Reaction Semantics

## 1. Spell categories [AUTHOR RULE]

1. **Single-target**: a spell impacts one selected/rolled enemy pad/target; no implicit AoE. Damage, entity status and base-form terrain effects may have separate scopes.
2. **Directional chain propagation**: paths between local pads and eligible inter-enemy entry pads; randomized **among valid exits**, never through arbitrary consecutive integers.
3. **Area-of-effect (AoE)**: aim at a **world-grid location within caster range**; AoE geometry comes from the particular spell and covers its actual base-form cells, not its enemy pad numbers. Character may miss enemies completely. Optional fallback for early implementation: target/snap to cells/pads, without redefining spell laws.
4. **Elemental combo reaction**: a traveling spell contacts a qualifying existing spell/element state and yields a named interaction; propagation's continuation depends on **the elements/reaction**, not one general rule.
5. **Triple chain**: qualifying third element strikes a prepared double chain; author currently says third-chain interaction **terminates incoming Lightning path** while enhancing the triple effect. May be refined later.
6. **Physical weapon attacks**: initial scope basic strike/double/retaliate and visually compelling animations; must not bypass guard, health, existing physical damage surfaces or authoritative kernel.

## 2. Chain trigger, resolution ordering [AUTHOR RULE + OPEN]

- Earth spell at pad/base-form contact may establish Earth prime.
- Later Water aimed/landed at **that same qualifying contact** triggers Earth→Water **Mudstorm** instead of full standalone Tidal Surge. A different contact executes normal Water.
- Later Fire at that same valid Earth→Water chain triggers **Volcanic Eruption**.
- After triggering, chain output creates entity damage/status and **persistent spatial terrain changes on base forms** as defined.
- **Do not** apply full triggering base spell and full combo spell twice by default. Keep effects from previous turns according to their own duration unless explicitly consumed/transformed; exact stacking and consumption OPEN.
- Encountering a primed location is not always a forced stop. For Lightning specifically: Water may allow/strengthen continuation; Earth grounds/stops; Fire creates Plasma; triple-chain interaction currently stops incoming Lightning's regular traversal while the triple reaction resolves.
- Fallback from unlisted ordered combination to a reverse-ordered definition was proposed for Water→Lightning using Lightning+Water, **not** approved as universal commutativity. Direction/order of elements matters in source documents.

## 3. Lightning path rules [AUTHOR RULE]

- Lightning follows an explicit **directional local-pad network** on each enemy, plus valid spatial jumps between different enemy entities.
- At an internal pad choose left/right relative to incoming trajectory, **only among valid exits**. No backwards traversal, no illegal straight shortcut through the same enemy, and no hopping over required intermediate pads.
- Cross-enemy jumps can be straight or diagonal according to actual enemy layout. Destination pad number can be **lower** and need not be the next number. Different enemies can have identical local pad labels.
- If outward jump to another enemy is unavailable, Lightning continues along an available permitted local-pad path; if no path exists, it fizzles.
- Example four-pad local paths: `4→5→6`, `4→7→6`; not `4→6` directly. Pad 5 or 7 may exit to another enemy when eligible, otherwise proceed toward 6. At pad 6, try valid inter-enemy exit or fizzle.
- Example eight-pad: 15 must first go to 16 before seeking another enemy; 16 may continue toward 17 or exit, depending on layout. An authored illustrative path was `14→15→16` to reach a Water-prime at 16.
- Examples of inter-enemy jumps: `6→2`; `17→31` and `18→22` as diagonally preferred possibilities for particular enemy arrangements. These numbers belong to **different enemy instances**, not one creature.
- Pad 1 is a terminal for Lightning (no onward pad); Type 2 may traverse `2→3` and jump outward. Early enemy health is independent from route definition.
- Multiple enemies each with type 3 all use labels 4–7; use composite instance+label ID.

## 4. Target count vs pad hops [IMPORTANT OPEN CONFLICT]

Recovered **Thunder's Wrath** says basic Lightning may chain to **one additional nearby target for 50% base damage**. Author wants many pad *contacts* to form a route within one enemy; contacts do not automatically mean distinct damaged enemies.

Potential model [PROPOSAL]:
- `pad_contacts` for path traversal;
- `distinct_entity_hits` counts additional target allowance;
- `level/skill` governs how many distinct additional enemies can be hit;
- an elemental combo like Aqua Lightning may have its own hit allowance and propagation policy.

**Not established:** how many local pad hops a level-one Lightning cast may make, whether each contact damages the same enemy again, whether the full path is permitted when no secondary target is available, and how original 'nearest' language coexists with directed trajectory. Do not implement inferred answer as canon.

## 5. Elemental encounter routing [AUTHOR RULE; behavior table partly provisional]

| Incoming | Contact state | Outcome | Continue ordinary Lightning path? |
| --- | --- | --- | --- |
| Lightning | Water | Conductive interaction / Aqua Lightning (historical file: Lightning+Water) | Yes, may continue; exact additional hops/hits OPEN |
| Lightning | Earth | Grounding interaction | **No**, current authored rule |
| Lightning | Fire | Plasma transformation / Blazing Plasma | Reaction effect occurs; onward propagation OPEN |
| Lightning | Qualifying preexisting double | Triple-chain interaction | **No** for original Lightning route per latest summary; triple has independent effects |
| Any | Unrecognized element | Evaluate authored rule or explicitly unresolved | No guessed universal stop or conversion |

Author explicitly corrected assistant's earlier 'every combo stops Lightning' assumption.

## 6. AoE footprint families [DESIGN PROPOSAL, NOT LOCKED]

Author drawings illustrated radial/eruption, three-way branch, forward line/pierce and other directional effects. Pattern geometry is spell-specific and independent of the enemy pad topology.

- `single` — one grid cell/occupant
- `line` — world-grid trajectory with optional penetration
- `fork_3` — three-direction spread relative to cast orientation
- `cross_4` — center + orthogonal neighbors
- `radial` — authored blast radius/shape
- `chain_jumps` — **different mechanic**, graph traversal, not ordinary AoE

These strings are suggestions, not actual existing ZW opcodes. Accuracy/scatter, self-hit, friendly fire, cover, resistance and terrain conversion need explicit spell rules.

## 7. Randomness [AUTHOR RULE]

- Impact choice may be randomized within permitted pads, so chain priming is not guaranteed.
- Lightning left/right choices randomized when both options valid.
- Proficiency may tune hit probability and extent, but no functions/thresholds approved.
- Keep seed and roll trail in diagnostic output for deterministic replay; does not authorize simulation mutation from presentation.


---

# Recovered Magic Examples and Rule Interpretation

**Caution:** This file is a partial summary of original Drive magic text *plus* author's later corrections. It is NOT a complete reproduction of the original eight-chain corpus. Refer to originals for exact terms and variants.

## 1. Original eight primary elements [RECOVERED DOCUMENT]

Earth, Fire, Ice, Lightning, Moon, Shadow, Spirit, Water; also **Triple Chains**. Original file list described by author as largely from 2025.

Additional concepts **Vril, Graviton, Void** are later/current design candidates. They must be compared against baseline; do not assume they use the same elemental chain rules or grant them universal status. Keen's spirit walking and Vale's Graviton character magic should be preserved in their individual profiles.

## 2. Ground Tremor — Earth [RECOVERED DOCUMENT + AUTHOR INTERPRETATION]

- Base Earth spell.
- Moderate single-target damage (original file does not specify an absolute number).
- Movement speed **−20% for 2 turns** (enemy status).
- Creates unstable ground; original describes **−10% evasion for 2 turns** as a battlefield effect.
- Author clarified environmental penalty belongs to **affected base-form terrain**, not necessarily a portable direct enemy debuff. When enemy leaves, terrain effect does not follow.
- Contact can prime local environmental cell/impact for later Earth+Water reaction.

## 3. Tidal Surge — Water [RECOVERED DOCUMENT]

- Direct damage to primary target.
- Applies **Soaked**: +15% Lightning damage, −15% Fire damage for **3 turns**.
- Moderate adjacent tile splash = **50% of primary damage**.
- Author still needs to define scope/mapping of 'adjacent tiles' to underlying base-form grid (not hero/launch-pad network by default).

## 4. Mudstorm — Earth then Water [RECOVERED DOCUMENT + AUTHOR RULE]

When Water lands on a qualifying Earth-primed contact, resolve Mudstorm rather than the full standalone Tidal Surge:

- Damage-over-time **10% of Earth's base damage for 3 turns**.
- Enemy **movement −30%** (duration unspecified in excerpt).
- Creates **Mudfields** on environmental base forms.
- Mudfields **+15% subsequent Earth damage** and **−10% evasion** to entities subject to their terrain effects.
- The author caught an earlier reading mistake: environmental bonuses/penalties shouldn't be double-counted as a second direct enemy status.
- Stacking or replacing existing Ground Tremor's 20% slowdown with Mudstorm's 30% is OPEN. Don't invent '24%' enhancement.

## 5. Volcanic Eruption — Earth + Water + Fire [RECOVERED DOCUMENT]

- High AoE damage **150% of Earth's base damage**.
- Burning **10% damage over time for 3 turns**; base for that 10% remains **OPEN** (author considered 10% of eruption's 150%; source does not explicitly say).
- Creates **Lava Field** for **3 turns**.
- Lava Field **+15% subsequent Fire and Earth damage**.
- Author wishes triple eruption AoE to spread to adjacent **enemy-impact/base-form cells**, not automatically to unrelated hero positions. Actual blast geometry authored by spell; any occupant of covered world cells is subject to that spell's eligibility/friendly-fire rules.

## 6. Thunder's Wrath — Lightning [RECOVERED DOCUMENT]

- High single-target damage, critical-hit and chain-reaction emphasis.
- **25% chance** Shocked, **−15% evasion for 2 turns**.
- Base additional target: chains to **1 nearby target for 50% base damage**.
- Leveling may increase allowance [AUTHOR INTENT]; exact progression/hops OPEN.
- Original document does not describe the new directional pad-routing mechanic. It must be reconciled without losing either authored behavior.

## 7. Aqua Lightning — Lightning + Water [RECOVERED DOCUMENT]

- High AoE damage **125% of Lightning's base damage**.
- **Chains to 2 additional targets**.
- Creates **Conductive Zone**, +25% subsequent Lightning damage for **2 turns**.
- Author says Water reaction **does not inherently terminate Lightning's propagation**. Actual selection of the 2 targets and how these interact with the route remain OPEN.
- Water→Lightning wasn't separately authored in one source; use of Lightning+Water as fallback was discussed for this instance only.

## 8. Blazing Plasma — Lightning + Fire [RECOVERED DOCUMENT]

- AoE damage **150% of Lightning base damage**.
- Burning **10% Fire damage over 2 turns**.
- Plasma Field: **−15% enemy armor for 3 turns**.
- Author: Fire + Lightning makes Plasma. Whether transformed Plasma follows another trajectory is OPEN.

## 9. Other recovered triple chain examples [RECOVERED DOCUMENT]

- **Superheated Storm** = Fire + Water + Lightning: AoE DoT 75% of Fire base, 3 additional Lightning targets, stun 1 turn; Steam Zone +25% Lightning damage, −10% enemy accuracy, 3 turns.
- **Cleansing Flood** = Water + Earth + Spirit: heal allies 25% HP, cleanse debuffs; Restorative Pool +10% Water/Earth abilities and −10% incoming damage for 2 turns.
- **Energy Overload** = Lightning + Earth + Spirit: 125% Lightning base AoE, stun 1 turn; Charged Ground boosts Earth defense and Lightning damage for 2 turns.

## 10. Explicit distinctions

- An elemental sequence might be **ordered**: e.g. Fire+Water (`Steamforged Blast`) and Water+Fire (`Steamforged Tempest`) were differently named in recovered files. These are historical documents and may reflect authored directionality or evolving drafts; check variants before canonicalizing.
- Elemental reactions may **continue, transform, amplify, branch or terminate** propagation. These behavior categories were proposed during discussion; the **specific author-approved examples** prevail.
- Named character first/second magics are distinct from common NPC/basic elemental chains; character profiles should not each implement a separate independent combat engine.


---

# Shared Combat Runtime — Proposed Integration Contract

**Status: DESIGN PROPOSAL.** This document is NOT a claim about live API signatures or present kernel coverage.

## Authority and agnosticism

- **ZW** expresses authored character spells, elemental chains, conditional rules, topology and geometry/relationships without hardcoding one game's narrative.
- **AP** authorizes state-changing actions, including trusted actor identity and context. Runtime must not bypass AP or allow client-supplied authority to stand in for a trusted issuer.
- **EngAInRuntime snapshot / runtime owner** is the authoritative simulation state for entities and battlefield conditions.
- **Combat3D** resolves attacks and produces effects/events; **spatial/topology subsystem** resolves footprint and addresses. Avoid duplicate owners of mutable combat state.
- **Godot/Dragon** animates and renders; no independent combat HP, elemental-chain or spatial truth.
- Do not conflate 8080 gateway rules, 8090 authority gate, or 8765 independent AP runtime—previous audits found they were not a unified magic execution path.
- Existing Combat3D implements some health/damage/death behavior according to Dragon's read-only audit. **Magic/surface layers/formation coverage must be audited in code**, not assumed.

## Semantic entities and states [PROPOSED]

```text
BattleState
  combatants: entity_id -> {hp, status, facing, position, ...}
  enemy_footprints: entity_id -> occupied_world_cells
  pad_instances: (enemy_id, pad_label) -> {world_anchor, occupants, ...}
  base_forms: world_cell_id -> {terrain, active_effects, expiry, provenance}
  encounter: {turn, initiative, rng_seed, sequence_id, ...}
  combo_proficiency: (participants, combo_id) -> qualification/progress

SpellDefinition
  id, element(s), caster_requirements
  targeting_policy, range
  impact_policy, propagation_policy
  direct_entity_effects, environment_effects
  elemental_reaction_conditions and overrides

CombatAction
  source_entity, action_id, selection
  target_entity? target_pad_instance? target_world_cell?
  trusted_authority_context [server issued, not client asserted]
```

This is pseudostructure, not a ZW schema. Actual ZW envelope and vocabulary must be derived from existing contracts.

## Event pipeline [PROPOSED]

1. Receive authenticated, AP-governed action request.
2. Resolve current world position, valid range, target cell or `(enemy,pad)`; preserve seed/roll log.
3. Resolve impact landing (may be randomized), check actual base-form environmental and contact chain states.
4. Select correct spell/reaction *before* applying normal triggering-spell effects; avoid double resolution.
5. Resolve action-specific graph traversal or AoE cells, and any elemental transform/fallback/stop behavior.
6. Determine affected entities by cell occupancy/footprint intersection, including permitted allies/objects, and apply surface/defense/status rules.
7. Update authoritative entity and base-form state atomically and persist expiry/chain provenance.
8. Emit event trail describing every hit, contact, chosen path, reaction, terrain conversion, interruption, fizzle and guard/obstruction resolution.
9. Presentation consumes events/snapshot and renders; it does not recalculate outcomes.

## Key invariants [PROPOSED]

- Pad label only unique within a platform **type**; use enemy instance identity.
- Environmental effects live at **world cells** and never automatically follow moving entities.
- Attack pads may follow enemy position; contact resolution re-evaluates overlapped world cells.
- Combo lock graph != Lightning local path graph != world-grid AoE geometry.
- Pad hops != distinct damaged entity hits.
- Randomizer chooses only valid outgoing routes; no backwards hop along a forbidden Lightning path.
- Existing attack effects are not repeated merely because a reaction was triggered at another pad.
- Damage direct/DoT/terrain/penetration tracked separately for balancing.
- A spell can affect unoccupied terrain; target needn't be an enemy.
- Replayable seed/roll log required for diagnosing nondeterministic chains.

## Counterexample test cases

- Three enemies each have pad `6`: no shared chain state or occupancy due to duplicate label.
- Earth primes one world base form; enemy moves; mud remains behind, no phantom movement of field.
- Lightning at `4` cannot jump locally straight to `6`; route through `5` or `7` if valid.
- Lightning at `7` with no outward enemy continues toward `6`, then fizzles if no onward eligible exit.
- Fire encounters Lightning and resolves Plasma without incorrectly applying full base Fire and full Plasma damage twice.
- Type 4 combo pair `8+13` plus `9` only meets *mastered* triple when learned.
- Two party characters on same pad remain able to try qualifying action but roll severe obstruction risk.
- AoE aimed at empty world cell changes terrain even if no enemy is struck.


---

# Combat Test Harness & Balance Calibration

## Design goal

Build a **working test environment before fixing enemy HP**. Keep authored spell magnitudes and behavior; calibrate durability to observed damage, healing demand, action economy, combo frequency and desired encounter rounds.

## Harness rules [AUTHOR INTENT]

- Four player characters; one or more enemies on numbered platform types; environment base-form grid.
- First isolate basic physical attacks, Earth/Water/Fire; then add elemental chains, Lightning routing, AoE, combos.
- Target can be made **nonlethal for calibration** while retaining normal damage accounting. Do not let an 'unlimited HP' placeholder overflow counters or accidentally trigger death/health logic; record virtual damage in the harness without rewriting Combat3D law.
- After offensive baseline, **realistic combat** must have enemy counterattacks between player actions: healing, defending and movement may consume party actions that otherwise could deal damage.
- Use repeated simulations and deterministic seeds to compare random route outcomes.

## Two calibration modes

### A. Offensive ceiling

Enemy disabled from responding and cannot die. Four characters execute permitted actions. Measure per cast:
- normal hit, chain trigger, missed prime, combo attempt, random landing
- direct damage vs damage over time vs area splash vs propagated target damage
- status change, terrain effects, penetration, mitigations
- aggregate by party round and three-round cumulative total

### B. Realistic combat

Enemy actively attacks. Record for each party round:
- attacks used / heals / defenses / reposition / interrupts
- actual damage (including DoT only when tick occurs)
- enemy damage and survivability, actions diverted to healing
- chain windows missed because sequence interrupted
- combo availability and obstruction failure rate
- encounter completion rounds, remaining player HP/MP and deaths

## HP derivation

If party deals total **70 damage per full round**, an uninterrupted three rounds produce **210**. Choosing enemy HP **greater than 210** ensures survival through those three rounds **only for that measured scenario** (and ignoring same-time DoT/timing). The realistic three-round result may be lower due to healing, or higher when magic chains/procs apply. Therefore:

1. Record cumulative per-round damage distribution under many seeds/scenarios.
2. Pick desired earliest/typical survival round per enemy tier.
3. Choose HP against observed cumulative damage *and* combat survivability, rather than weakening original attacks to fit arbitrary HP=100.
4. Re-test with character mastery, terrain, enemy count, and spell upgrades.
5. Tune provisional penetration percentages (100/60/20/5, optional 90 for middle pad) if simulation shows the geometry produces bad outcomes.

## Suggested test milestones [PROPOSED]

- **M0 Contract audit:** inventory existing Combat3D, AP trust path, ZW data structures, entity surfaces, movement, spatial owners. No edits.
- **M1 Geometry:** spawn four party positions, one enemy with type 1–6 pad layout and fixed world base forms; deterministic coordinates.
- **M2 Basic hit:** physical attack, guard, stay/return, event inspection.
- **M3 Environmental singles:** Ground Tremor, Tidal Surge; entity vs base-form effects, movement out of mud.
- **M4 Double/triple:** Earth→Water→Fire, no double counting, AoE coverage, expiries.
- **M5 Lightning:** deterministic path + RNG branch + multi-enemy jump + Water/Fire/Earth reactions.
- **M6 Team locks:** dual/triple pad validation, learning, mastery, obstruction.
- **M7 Balance:** offensive-ceiling and realistic enemy-response runs, derive starting HP.
- **M8 Godot rendering:** show movement, spell footprint, target numbers and snapshots; render only after authoritative results.

Do not silently mutate repository, alter AP laws, promote archival spell drafts, or reorganize source tree while conducting design review.


---

# Open Decisions, Clarifications and Preservation Notes

This list is intentionally explicit: these decisions must not be filled in by assistant guesswork.

## Critical design choices still OPEN

1. **Numbered diagrams / facing:** confirm top-down coordinates, exact IDs on each edge, true front/back and type 6 pad placement against original drawings.
2. **Type 6 combo locks:** ratify which dual pairs and left/right side triple groups are approved (earlier assistant suggested several).
3. **Environment-to-pad chain lookup:** if a moving enemy shifts launch pads over fixed base-form cells, what spatial overlap qualifies a pad as water/earth-primed? What happens to a preexisting double-chain when its enemy moves?
4. **Status stacking:** Ground Tremor slow −20% versus Mudstorm slow −30%; replace, additive, max-only, independent durations? Terrain modifiers apply only while in affected cells.
5. **Chain lifetime:** priming duration, consumption on trigger, clearing/transformation of base-form effects and whether unconsumed old effects persist.
6. **Reactions by element:** continuing/transforming/terminating Lightning; Earth stops; Water continues; Fire→Plasma; triple stops original travel currently. Need other elements and elemental sequence order.
7. **Basic Lightning allowance:** hop path over multiple pads vs one additional *distinct target* at level 1. How are repeated hits to same enemy prevented or scaled?
8. **Aqua Lightning additional targets:** use authored directional pad topology or other target-selection logic? Relationship to incoming Lightning's remaining allowance and conductivity.
9. **Randomizer:** aim accuracy, landing rules, range, roll distribution, difficulty/mastery scaling and seed model.
10. **AoE geometry:** spell-specific grids (radial, straight, trident), collision/cover, friendly fire, occupant footprint intersection and whether triple explosion extends to adjacent pad-base intersections.
11. **Penetration/facing:** author floated 100/60/20/5 and 90% for pad 24/29; no fixed formula. Determine impact on armor/surface layers; no silent stacking.
12. **Character combo learning:** discover vs learned vs successfully demonstrated, qualification gates, duo/trio-specific mastery and failure learning.
13. **Physical combat:** audit existing surface-layer/weapon rules, don't reduce to plain HP.
14. **Spell document discrepancies:** Fire+Water vs Water+Fire names/effects; potential alternate copies; DoT percentages' bases.
15. **Additional powers:** Vril, Graviton, Void, named first/second magics and Spirit Walking compatibility. Never silently merge with original eight elements.
16. **NPC chain library:** verify exact spell source files, skill tiers and progression for generic NPC/basic magic.
17. **Encounter timing:** initiative, interrupts, turns, effects ticking relative to player action and enemy response.
18. **Authority:** trusted AP issuer, existing rule registry and 8090/8080/8765 path integration; no fail-open, no untrusted client authority claims.

## Source classification reminders

- Numbered pad scheme **1, 2–3, 4–7, 8–13, 14–21, 22–31**: author-approved from final sketch.
- Character duo locks Type 4 + Type 5: author-specified.
- Advanced triple `8+13+9`, `8+13+12`, `10+11+9`, `10+11+12`: author-specified examples.
- Local Lightning route and branching/jump logic: author described across several turns, assistant diagrams illustrative only.
- 'Three chain effects': author mentioned three, but their exact original formal category names **have not been recovered**. Do not equate with single/double/triple by assumption.
- Standard AoE aim within character range independent from launch pads: author preference; pad snapping fallback allowed if needed.
- Physical attack damage values, nonlethal test mode, Combat3D snapshot integration: design only.
- The magic docs are historical source text; original exact copies and variants have not been exported/deduplicated into this ZIP.

## Safe source-recovery plan

1. Preserve originals of all local and Drive magic documents without renaming/moving.
2. Obtain alternate variants and compare byte hashes and meaning before consolidating.
3. Review `vale magic.txt` as **completeness reference** for named-character first/second magic; verify every named character separately.
4. Compare `Single chains`, `triple chains.txt`, and per-element files against new platform and area rules, without retroactively rewriting historical originals.
5. Author explicitly approves any final ZW definition and AP authority changes after read-only code audit.

## Original discussions vs this document

This is an authored **summary/specification draft derived from conversation**, not a verbatim chat transcript. If full history is needed, export the chat separately and keep alongside this archive as provenance. Screenshots and diagrams are conversation attachments, not necessarily included here; collect originals as controlled references before geometry encoding.
