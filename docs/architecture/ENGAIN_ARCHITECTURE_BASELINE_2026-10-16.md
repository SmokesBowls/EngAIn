# EngAIn Architecture Baseline — 2026-10-16

Reference map of where the system stands before the architectural change.
Written at EngAIn `ac87402b`, trixel3.2d `fd39ff1`. Read this first in a new
session; re-verify anything you act on.

Status labels used throughout:

| Label | Meaning |
|---|---|
| **RUNNING** | Executed and passed on 2026-10-16 (from a scratch copy unless noted) |
| **LIVE** | Part of the running stack (`start_stack.fish`) and exercised by Godot |
| **PROOF ONLY** | Runs, but only from tests or hand-run proof scripts; nothing live calls it |
| **HISTORICAL** | Evidence it worked once (report, screenshot, log); not re-run |
| **UNTESTED** | Code exists; not run in this audit |
| **SPECIFIED** | Only in doctrine/contract text |
| **NOT FOUND** | Searched for; does not exist |

Report the stage that passed, never a broader claim. "Bouncer state 7" means
runtime load + snapshot sync, not a fully built scene.

---

## 1. Governing direction (architect-stated, 2026-10-16; not yet implemented)

1. **EngAIn authors reality.** A world object (identity, position, footprint,
   scale, relationships, state) exists as soon as the world model establishes
   it. Its existence never depends on artwork.
2. **Trixel is an optional artist, not an authority.** EngAIn does not summon
   Trixel just because an object lacks art. World loading must never depend on
   an artist, an image service, or a generation job.
3. **Placeholders are the default presentation of an object that already
   exists**, not a request for art. When art arrives, the visual is replaced;
   the identity and record stay.
4. **Four interchangeable visual sources** for the same object: placeholder,
   user upload, Trixel-generated, reused existing asset. All preserve the same
   object identity and authoritative state.
5. **Replacing a visual must not change collision, scale, topology, or gameplay
   state.** Those need their own authorized operations.
6. **Pixel art and brush art may both reach 3D surfaces** through a validated
   handoff; they may need different sampling rules (nearest-neighbour vs
   painted texture). WorldField and the geometry compiler should not care which
   artist made an image. *Current tests prove pixel-art preservation only.*
7. **Godot presents** whichever authorized representation is currently bound.
8. **The object owns its dimensions; the artwork does not.** World-object
   identity, placement, and dimensional constraints persist independently of
   visual assets. Replacing an appearance does not implicitly change authored
   dimensions, collision, topology, or gameplay state. Imported or generated
   art must be fitted, validated, rejected, or explicitly approved for a
   dimensional change.
   - Image resolution ≠ world size: a 16×16 and a 32×32 texture can cover the
     same surface (more pixels per unit area). A mismatched *aspect ratio*
     (32×16 on a square face) must be cropped, letterboxed, or rejected — never
     silently stretched.
   - 3D assets (e.g. `.obj`) carry their own geometry and often no declared
     unit. An imported mesh larger than the authored object is fitted or
     rejected; it never resizes the object.
   - Keep two things separate: **world-object constraints** (position, size,
     orientation, collision, relationships — authoritative) and **visual
     geometry** (mesh/sprite/material/texture — must obey the constraints but
     need not equal the collision shape; e.g. tree canopy, swinging sword).
   - EngAIn can hand Trixel the target dimensions up front, so generated art is
     made for the object instead of forced onto it.

### Authority layers (architect-stated, 2026-10-16; sequenced AFTER current authority is dialed in)

| Layer | Role |
|---|---|
| **Human** | Ultimate authority over the authored world. Can approve, reject, redirect, or override Dragon and every automated decision, including established dimensions. |
| **Dragon** | Delegated creative authority. Absolute toward EngAIn's automated creative operations and free to decide within its domain without asking permission; always below the human. |
| **Tier 1** | Supreme *system* authority: validates provenance, coordinates, records, enforces boundaries, preserves authoritative state. Does not treat a deliberate human (or authorized Dragon) correction as an error. Dragon does not bypass Tier 1 governance. |
| **Subsystems** | Do assigned work inside an authorized scope. Trixel chooses *how* to build, never rewrites authored dimensions. Godot presents and manipulates a representation, never silently redefines reality. |

Principle: **human intervention supersedes automated world-authoring
decisions. Tier 1 governs and preserves those decisions. No subsystem may
silently reverse an authorized human correction.** A correction must be
explicit, persistent, and traceable, or the next scene rebuild restores the
old value. Illustrative (not a schema): `object tower_037 · previous height
12 m (provisional) · approved 24 m · authority human_override · effect update
authored dimensions · downstream reconstruct geometry`.

A human correction changes the *world object*, not just its appearance
(contrast P5, where an art swap must change nothing else).

Sequencing: first establish authority and responsibility boundaries inside
EngAIn and between EngAIn, Trixel, and Godot; then place the human/Dragon
override layer on top so corrections propagate through the existing
handshakes without bypassing their safeguards.

**Current reality (verified 2026-10-14 audit):** no actor authentication
exists. `actor_authority_tier` is a field the client sends; the 8090 gate
trusts the claimed tier; the trixel32d executor hard-codes its authority.
Human and Dragon cannot be told apart today.

### Object Spatial Reasoner (proposed responsibility; owner not decided)

A missing responsibility, distinct from Topologist (relationships/structure),
Cartographer (where things go in the world layout), and Trixel/WorldField
(how to build). It answers: *how large should this object be, given what it
is and its surroundings?*

- Inputs: object type and narrative evidence (any stated measurements),
  neighbouring scale (roads, buildings, terrain), who must use it (doorways
  fit the creature that passes through — a giant's house is not human scale),
  and the current outputs of Topologist, Cartographer, and WorldField.
- Output: proposed dimensions, proportions, clearances, environmental fit —
  each with a status: **authored** (stated by source), **inferred**,
  **provisional**, **Dragon-decided**, **human-approved**.
- Conflicts are reported, not silently resolved: a 30 ft bridge estimate vs
  riverbanks the Cartographer placed 60 ft apart is an architectural conflict.
  The reasoner may propose an adjustment; it may not move the banks or
  stretch the bridge on its own.
- Owned by EngAIn (sizing is a world-authoring decision). Trixel receives the
  resulting dimensional requirements.
- Unknown measurements stay explicitly unknown until the reasoner (or an
  authority) supplies a value with provenance; a Godot render default must
  never become a world fact.

Target lifecycle to verify next:

```
object exists → placeholder renders → user/Trixel supplies asset
              → visual binding changes → object persists across scene rebuilds
```

Conceptual record fields (NOT a schema proposal — check existing registries
first): `object_id`, `world_state`, `visual_binding`, `visual_source`,
`asset_provenance`, `revision`.

### Existing hooks relevant to the lifecycle (exist; NOT traced yet)

| Hook | Location | Known fact |
|---|---|---|
| Spatial skin system | `tier2/godotsim/spatial_skin_system.py` (107 lines) | untraced |
| Embodiment contract builder | `tier2/godotsim/embodiment_contract_builder.py` (`trixel_embodiment.v1`) | kept in EngAIn at the 2026-07-16 Trixel eviction as the consumer side |
| Semantic bridge / `.trixel` skin manifests | `tier2/godotsim/semantic_bridge.py`, `tier1/engainos/bridgeroom/zon_to_entities.py` | kept at eviction |
| Embodiment HTTP routes | `http_handlers.py`: `/embodiment/pending`, `/embodiment/apply` | `/embodiment/apply` has no gate (2026-10-14 audit) |
| Asset pack manifest | `engain_manifest.json` → `asset_packs.debug_placeholders` | the manifest file it points to is **missing**, so Main.gd spawns capsule placeholders only |
| Godot render policy | Semantic `trixel/RenderPolicy.gd` | has `atlas_2d`, `recipe_3d`, `composer_2_3d`, `custom_upload` modes (legacy generation) |
| Bridge entities | `/snapshot` `bridge_entities` + `bridge_entities_scene_id` | rebuilt from the scene doc on each snapshot (persistence across rebuilds unverified) |

---

## 2. Live system today

```
start_stack.fish → 8080 sim_runtime (tier2/godotsim)   LIVE
                   8765 engainos / AP scene server       LIVE
                   8090 authority gate                   LIVE
                   (8766 Trixel tile server: NOT started)
```

| Path | Route | Status |
|---|---|---|
| Boot search box | Stageroom passroom scene → 8765 SceneClient → Boot.gd → SimClient → 8080 `/scene/load` | LIVE (045 verified 2026-10-15) |
| Main scene chooser | `engain_manifest.json` → `tier3/mettaext/loaded/scene_index.json` → legacy `.engain_cache/parsed/scenes/*.zonj.json` → 8080 | LIVE (006 verified by user 2026-10-16: load + snapshot sync, Bouncer state 7) |
| Snapshot ownership | `sim_runtime._bridge_owner_scene_id` (marker only for real, active, doc-matching ids) | LIVE, committed `ac87402b` |

Godot clients (two different experiences — keep separate):

| Client | Location | Notes |
|---|---|---|
| Semantic world | `~/Downloads/godotnew/semantic` (not a git repo) | Frozen copy of the May–June 2026 Trixel generation; lived in EngAIn at `godotnew/semantic` 2026-05-21..06-17 |
| EngAInOS Boot Shell | EngAIn `project.godot`, `scenes/EngAInOSBootShell.tscn` | File-command input bridge; not on the 8080 snapshot path |

---

## 3. Lanes and their real status

| Lane | Location | Status |
|---|---|---|
| Mettaext (legacy) | `tier3/mettaext` stageroom/passroom | LIVE output. Emits keyword-vote terrain labels (`cosmic`, `beach`…) — crosses the lane line Gen2's contract forbids |
| MettaextGen2 | `tier3/mettaextgen2` | RUNNING. Entities, locations, presence, aliases. Spatial/terrain/distance/temporal/affect/event sections are `UNIMPLEMENTED_SECTIONS` (always empty) |
| WorldField | `tier2/worldfield` (rehoused `dd324c59`, 2026-07-17) | PROOF ONLY. Adapter CLI runs; `grid_facts_emitter` called only by tests. Unsculpted field = all `grass` |
| Topologist | `tier2/topologist` | PROOF ONLY. `passroom_signal_converter` turns legacy pass1 spatial signals into links (006: 1–3 links per scene) |
| Cartographer | `tier2/cartographer` | No runtime caller (2026-10-15 census) |
| Paradox Machine, Engionality, MrLore | tier1/tier2 | No runtime caller (2026-10-15 census) |
| Trixel 3.2D | `~/Desktop/burdens_of_a_forgotten_past/trixel3.2d` | The only Trixel with a future (eviction decision 2026-07-16). See §4 |

---

## 4. Trixel landscape

| System | Location | Status |
|---|---|---|
| Recipe → texture pixels | trixel3.2d `trixel_recipe_renderer.py`, `recipes/terrain` (10), `recipes/transitions` (5) | RUNNING (gates) |
| WorldField → WorldCell projection | trixel3.2d `trixel32d_worldfield_to_worldcell_projection.py` | RUNNING (gate) |
| Pixel-geometry compiler (ramps, folds, wraps, fractional, art fold) | trixel3.2d `trixel/pixel_geometry/` | RUNNING (24 gates; 28/28 gates total, 85 tests + 100 subtests) |
| 2D image → pixel field → built surface | trixel3.2d `trixel32d_image_ingress.py` → `surface_consumer` | RUNNING (tests) |
| Terrain-state water accounting (Lane A) | trixel3.2d `trixel/terrain_state/` (untracked) | RUNNING, isolated by contract |
| EngAIn ⇄ Trixel file-drop handshake | EngAIn `bridgeroom/trixel32d_*`, `gates/gate_trixel32d_handshake.py`; trixel3.2d `tools/consume_trixel32d_request_drop.py` (entry point) | PROOF ONLY (`executors/trixel32d_request_loop_proof_v1.py` passes; `GODOT_RUNTIME_EXECUTED false`) |
| Blender output | trixel3.2d `tools/*_blend.py`, `fixtures/*.blend` | RUNNING (headless inspection of courtyard .blend) |
| Godot apply of built surface | report `runtime/godot_reports/GODOT_TRIXEL32D_APPLY_EXECUTOR_V1.report.json` (2026-08-16) | HISTORICAL; producing script NOT FOUND |
| Legacy brush/GIMP engine (gbr/gih/gpl/vbr…, recipes, trees, material sheet) | `conductor/conductor_building_blocks/trixelworld/` (untracked in conductor git) | RUNNING (demos, trees, stress scene, 16-row building material sheet) |
| Legacy 8766 tile/atlas server | `conductor/.../trixelcomposer/tile_server.py` | UNTESTED; not started |
| Legacy "autonomous artist" | `terminal_trixel.py`, `enhanced_trixel_core.py` | UNTESTED. Random pixels on 16×16; "brush" is a label; no visual inspection, no correction; quality = heuristic + random |
| "Class 1 conductor" | — | NOT FOUND in any text or code; switchboard spec marks it UNKNOWN |
| LibreSprite brushes | contracts in `trixel_legacy_2d/.../libresprite_parser_family/` | SPECIFIED |

Architect's note: 3.2D was not meant to carry every Trixel version — the legacy
artists were proofs of concept. Each can make art; placing it in 3D was the open
question, and 3.2D geometry now exists.

---

## 5. Missing connections (why the full path does not run)

1. Nothing turns scene/book data into WorldField elevations (tests use
   hand-set elevations; `--demo` uses noise; Gen2 terrain evidence unbuilt).
2. No live caller of request assembly/dispatch — only tests and proof scripts.
3. trixel3.2d is invoked only by hand-run proofs (found as sibling folder).
4. No live Godot consumer of `trixel32d_surface_built`.
5. `TERRAIN_TO_RECIPE` (grid_facts_emitter) is EngAIn's proposal, trixel3.2d
   concurrence pending; `scree`, `fog_waste`, `cracked_soil`,
   `ash_plain_dark`, `pier` unmapped.
6. Recipe-textured geometry + Blender output come from tools, not the
   request/surface route.
7. Legacy brush engine has no link into trixel3.2d.
8. No persistent visual binding verified (the lifecycle in §1).

---

## 6. Known defects (each its own change; do not mix)

| Defect | Location | State |
|---|---|---|
| Main.gd re-poll has no retry limit (Step 2) | `Main.gd:682,692,698,719` | open, approved in principle later |
| Boot adapter drops `layout_proof`, `description`, metadata | `Boot.gd` ~596-617 | open |
| Main ignores snapshots for Boot-initiated loads | `Main.gd:685` | open |
| Trixel planner hard-codes moved adapter path | `TrixelEnvironmentPlanner.gd:12` (`EngAIn/terrain/...`) | open — architectural, not a path fix |
| No `cosmic` tile mapping → grass | `primitive_vocabulary_bindings.json` | open |
| Legacy cache `game_metadata.level_design` not read | `Boot.gd` level_design lookup | open |
| Boot Shell `text_submitted` passed to `is_action_pressed` | `godot/input/GodotInputListenerBridgeConsumeCommand.gd:210-215` | ON HOLD (fix: skip names without `InputMap.has_action`) |
| `/scene/load` accepts id-less docs as `scene.unknown` | `http_handlers.py:370-393` | open (overlay now refuses ownership) |
| scene_manager bridge import fails; fixing it enables SceneExtractor synthetic entities | `scene_manager.py:41` | decision needed |
| Vault Linker Part B | routes, VaultClient autoload, fallback | ON HOLD |
| Git author is a placeholder email | repo config | open |

---

## 7. Commit ledger (this work)

| Commit | What |
|---|---|
| `a835f3f2` | Retire Vault Linker synthetic scene generation; preserve Vault API |
| `ac87402b` | Snapshot ownership: zero-entity scenes owned; marker bound to active scene |

---

## 8. Working rules

- Audits are read-only. Run things from scratch copies.
- Never edit `AGENTS.md`, `HANDSHAKES.md`, `mettaextgen2/mettaextgen2.md`, the runtime journal.
- Check `git rev-parse HEAD` first; stop if the baseline moved.
- Server and client changes never in the same step.
- Never auto-promote from `out of root`; Stageroom/runtime separation is intentional.
- Do not infer implementation from doctrine. Do not equate a handshake stage with a finished scene.

## 8a. Handoff at session close (2026-10-16)

- EngAIn HEAD `ac87402b`; only this file is untracked (commit it or not — your call). Stack appears stopped (`.run/*.pid` gone).
- trixel3.2d `fd39ff1` with its own pre-existing untracked work (terrain_state Lane A, proposals, plans) — untouched.
- Nothing was implemented this session after `ac87402b`. All audits ran from scratch copies.
- Evidence scripts and copies live in the Claude scratchpad
  (`/mnt/data-drive/EngAIn_Recovery/07_TMP/claude-1000/-mnt-data-drive-zw/<session>/scratchpad/`):
  `live_verify/repro_ownership.py`, `step1/step1.v2.diff`, `mettaext_eval/env_census.py`,
  `trixel_audit/` (copies + gate/proof logs). Treat as disposable; everything needed
  to resume is in this file.
- Suggested first step next session (read-only): trace the visual-binding
  lifecycle (§1) through the existing hooks, and inventory how authority is
  claimed today (`actor_authority_tier`, 8090 gate, executor-hard-coded
  authority) as the start of "dialing in current authority".
- Live page copy: https://claude.ai/artifact/3tuobDmpwU3tRzfmQpQEc4 (private).

## 9. Open decisions for the architect

1. Where the persistent visual binding lives (existing registry vs new).
2. Placeholder source: restore `debug_placeholders` asset pack or define defaults elsewhere.
3. Which Godot client is the target for the new architecture (Semantic is a frozen legacy-generation copy).
4. Whether Gen2's spatial/terrain extractors come before or after the binding lifecycle.
5. How brush art vs pixel art are sampled on 3D surfaces.
6. Whether authored dimensions are always exact measurements, or whether an
   object may start with **provisional** dimensions until the narrative or the
   user establishes its true size (and who may promote provisional → exact).
7. Unit convention for imported meshes that declare none (`.obj`).
8. When Dragon sets a value with no human instruction: accepted world state
   at once, or held for review? Advisor's inclination: accepted immediately,
   permanently tagged as Dragon-authored and eligible for human override.
9. Whether the Object Spatial Reasoner is a new subsystem or extends an
   existing one, and which tier owns it.
10. How human and Dragon are distinguished when both reach EngAIn through
    the same interfaces (no actor authentication exists today).
