# EngAIn TODO

Last updated: 2026-07-16. Origin: rehousing repair pass, authority-gate audit,
and out-of-root divergence audit (see commit messages 43bceb0..7e78e1a and
scratch/tier_relocation/TIER_REHOUSING_MAP.md).

See HANDSHAKES.md (root) for the who-asks / who-gives / payload inventory of every
inter-system contract, including which handshakes are broken today.

## Done (2026-07-15)

- [x] **Commit A** — `engain_control/` restored to root (`c453730`). 30 gate/control-center
      modules across tier1/mrlore, tier1/engainos, tier2/engionality import again.
- [x] **Commit B** — unique artifacts recovered (`f27431b`):
      `scratch/tier_relocation/TIER_REHOUSING_MAP.md` (AGENTS.md cites it; existed nowhere else),
      `scratch/verify_libra_gates.py`.
- [x] **Commit C** — bulk preservation (`7e78e1a`): `out of root/` (kimodo gitignored),
      `mechanimation/` (152/152 hash-identical to history), `APZWV.1/` (only copy of AP v1 doctrine).
- [x] **Rehousing repair** committed (`43bceb0`): ROOT_DIR resolution, kernel/adapter package
      imports, governance import to tier1.engainos.aproom, facade + authority_gate imports,
      `/health` subsystems block. All six seam validations passed.

## Done (2026-07-16)

- [x] **HANDSHAKES.md** authored — who-asks/who-gives/payload inventory of all
      inter-system contracts, with WIRED/BROKEN/HALF/DOC-ONLY statuses.
- [x] **Pre-move repo located & mined** — `/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn`
      (checkout f7a911f, direct ancestor of main); see "Pre-move repo recovered" below.
- [x] **ZW Empire Editor repaired + interactively verified (PASS)** — see the repair
      item under Known bugs for details. User's interactive proof: GUI launches; all 5
      templates (Container/NPC/Room/Item/Rule) populate valid ZW; Parse structures each;
      Stats performs the ZW-vs-JSON comparison with document-appropriate results
      (char savings — NPC 33.3%, Container 34.6%, Room 59.4%, Item 26.9%, Rule 47.5%);
      Pack ZONB reaches a real save dialog; saved Container and NPC ZONBs reopen and
      decode correctly (`repaired_1st_test_container.zonb`: 114 bytes, preserves
      container/flags/contents/item ID/quantity); sizes reported; shim path operational.
- [x] **Photorec ZW harvest** — 17 unique ZW-family recoveries + 1 TrixelToolkit file
      pulled from the 14,763 recovered .py files into
      `EngAIn_Recovery/04_CANDIDATE_IMPORTS/{gui_recovery/photorec_zw_harvest_20260716,
      trixel_recovery_20260716}/`.
- [x] **2D trixel evicted from EngAIn** (user decision: only trixel3.2d matters; all
      trixel stays out until 3.2d is done, then re-enters via the single trixel32d
      handshake). Moved to `~/Desktop/burdens_of_a_forgotten_past/trixel_legacy_2d/`
      (see EVICTION_MANIFEST.md there): godotsim trixel_composer.py, mechanimation
      trixel_bridge.py + trixel_composer/, out-of-root render/trixel.py, old
      TRIXEL_TIER1_AUTHORITY doctrine. Facade `/api/trixel/artwork/` endpoint deleted.
      KEPT: gate_trixel32d_handshake.py + test, TRIXEL32D contract doc, and the
      runtime `.trixel` skin-manifest consumer machinery (HANDSHAKES.md §7d).

## Known bugs, ready to fix

- [ ] `tier2/godotsim/scene_manager.py:32,41` bare imports — SceneExtractor and SemanticBridge
      silently disabled at boot (same bug class as the repair pass; files exist at tier2/godotsim/).
- [ ] Author `tier1/engainos/rules/runtime_mutation/` AP registry + first authority-gate unit
      tests. Until then `authority_gate.evaluate()` raises APRuleLoadError on any mutating/unknown
      action instead of failing closed. Note: the ap/0.1 .zon grammar exists only in
      ap_rule_loader.py/ap_rule_evaluator.py — no spec doc anywhere (APZWV.1 covers the OTHER
      AP engine, aproom/ap_engine.py on 8765).
- [ ] Governance gaps (authority audit, verdict VALUABLE_BUT_PARTIALLY_WIRED):
      - ungated mutation endpoints: `/vault/link`, `/world/sync`, `/world/load_mirror`,
        `/embodiment/apply`
      - IntentShadow is in-memory only — rejection records vanish on restart
      - `actor_authority_tier` is self-declared on live paths (no authentication)
      - `evaluate()` stage-2 tier/reality validation is a stubbed TODO (authority_gate.py:548)
      - complex rules can never fire: they match `attacker`/`amount` keys but the live combat
        path sends `source`/`damage`
      - `load_scene_from_file` (sim queue) reads arbitrary caller-supplied filesystem paths
- [ ] Minor backlog: duplicate `combat3d_mr.py` (godotsim top level vs authoritative `kernels/`
      copy — they differ); stale vault-ingest paths in `http_handlers.py:635-637`
      (`ROOT_DIR/engain_ingest.py`, `ROOT_DIR/mettaext` → now under tier3/mettaext/);
      `sim_runtime.py:33` inserts tier2/ on sys.path intending repo root; `ap_engine.py`
      pre-rehousing identity constant; `tier3/mettaext/run1time.py` reads nonexistent
      tier3/manifests path; AGENTS.md-referenced `run_tests.sh` missing from root.

## Decisions needed (user)

- [ ] `gui/` home — and where the ZW parser canonically lives (`out of root/gui/zw/zw_parser.py`
      is the only copy in the ecosystem; the external zw_gui.py fix points at nonexistent
      `tier1/engainos/core/zw/`).
- [ ] `tools/` union — external 34 pre-externalization scripts (incl. AGENTS.md-referenced
      `engain_stack_tmux.sh`) vs current 11 gameproof-era files. Zero path collisions; pure union.
- [ ] `mechanimation/` — tracked root sibling (current state) vs own repository. Topologist
      lane-theft gate treats it as a foreign lane either way. (Its embedded trixel copies
      were evicted 2026-07-16; what remains is pure motion/frames material.)
- [ ] The 5 colliding `scratch/ap_*_report.json` generations — external runs say ACCEPTED,
      current runs say REJECTED. Which probe generation is trusted? (Both are preserved:
      current in `scratch/`, external in `out of root/scratch/`.)

## Pre-move repo recovered (2026-07-16)

Unzipped pre-move working copy found at `/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn`
(git checkout at `f7a911f`, which is a direct ancestor of current main). Tree listing:
`LEGACY_TREE_OUTPUT.md` at root. Consequences:

- **Trixel systems FOUND** — trixelcomposer/trixelworld/trixelmap/trixelpixel are
  (a) tracked at `f7a911f`, so 1,873 files across trixel+terrain+gui+tools are already
  in current git history (`git checkout f7a911f -- <dir>`), and (b) on disk in the
  legacy copy, including gitignored material history never captured:
  `trixelcomposer/.zw/` (39 files incl. the artwork PNGs the facade endpoint serves)
  and `trixelcomposer/.claude/`.
- **Externalization remainder resolved** — `terrain/` (6 tracked +4 ignored), legacy
  `gui/`, `run_tests.sh` (AGENTS.md-referenced), 33-script `tools/` all present.
- **Semantic POC Godot client located** — `godotnew/semantic/` (Main.gd, SimClient.gd,
  Boot.gd) with UNCOMMITTED modifications in the legacy working tree; also uncommitted:
  `godotsim/{scene_manager,http_handlers,bridge_integration}.py`, 6 untracked `docs/`
  files (boolean switch registries), `godotnew/semantic/pass_to_render/`. Diff these
  before ever discarding the legacy copy — they exist nowhere else.
- Legacy `gui/` does NOT contain `zw/zw_parser.py` — the `out of root/gui/` copy remains
  the only one; it post-dates f7a911f.

## Not explored yet

- [ ] **Legacy uncommitted diffs** — diff the modified godotsim/godotnew/godotengain
      files in the legacy copy against f7a911f and against current tier2/godotsim;
      salvage anything not already incorporated.
- [ ] **Older mrlore in ~/Downloads** — second mrlore version per user; unknown path and
      divergence vs `tier1/mrlore`. Hash-compare when path known.
- [ ] **ZW Empire Editor: repaired + user-verified PASS; original zw_core.py still
      lost** — the tool IS `out of root/gui/older_zw_gui_enhanced.py` (+ `old_`
      sibling): Open ZW → Parse → Validate → Stats (ZW-vs-JSON token/char compression
      measurement) → Pack ZONB. The lost file was `core/zw_core.py` (parse_zw
      provider). Repaired 2026-07-16: validator+spec_rules restored from `archive_gui/`
      to `gui/`, `core/zw_core.py` recreated as a DOCUMENTED SHIM over
      `gui/zw/zw_parser.py`, packer name aliases (`pack_to_zonb`/`unpack_from_zonb`)
      added. 9/9 gui tests pass + full interactive proof (see Done). Launch:
      `cd "out of root" && python3 -m gui.older_zw_gui_enhanced`.
      Remaining: the ORIGINAL zw_core.py may still be in the photorec field under a
      lost name — 17 ZW recoveries harvested to
      `/mnt/data-drive/EngAIn_Recovery/04_CANDIDATE_IMPORTS/gui_recovery/photorec_zw_harvest_20260716/`
      (see README); none matches zw_core so far. If a distinctive string from inside
      it is remembered, re-sweep the 14,763 recovered .py files on that signature.
- [ ] **trixel32d seam: three missing pieces** (direction corrected 2026-07-16 after
      user caught HANDSHAKES.md implying trixel emits its own request) — EngAIn is the
      REQUESTER (authors `trixel32d_surface_request` from world data), trixel3.2d is
      the BUILDER (returns `trixel32d_surface_built`). What exists: the contract doc
      (both packets) + a pre-flight request validator gate with ZERO callers. What
      doesn't: (1) the requester that builds packets from world data, (2) the
      invocation route (HTTP/file-drop/library), (3) the `surface_built` consumer
      that turns geometry into runtime/Godot state. Blocked on 3.2d completion.
- [ ] **2D trixel state assessment** (user, 2026-07-16: 2D trixel is NOT trash) —
      once 3.2d stabilizes, fix legacy 2D to a known-good state so we know what to
      change if developed further; candidate future role: 2D UI rendering over 3D
      gameplay (outside EngAIn). A recovered `TrixelToolkit` (2,686-line canvas/PNG
      agent file) is at
      `/mnt/data-drive/EngAIn_Recovery/04_CANDIDATE_IMPORTS/trixel_recovery_20260716/`.
- [ ] **Unclassified**: `out of root/facade/` vs `command_center/` feature parity;
      `mini-game-modules/` and `star_needle_toolbag_patch/` intent (future work or residue?);
      whether anything reads `manifests/ap_rules.json` at runtime.

## Reference facts

- Two AP rule systems exist: doctrine-backed ZW engine (`aproom/ap_engine.py`, APZWV.1 specs,
  port 8765) and the governance ap/0.1 registry (loader/evaluator implemented, zero rule files).
- Live governance on 8080 `/command` is `tier2/godotsim/runtime_gateway.py` (RuntimeGateway),
  not `authority_gate.evaluate()` — the latter is reached only via the 8090 facade.
- Active manifest inputs live at `tier1/engainos/assets/` (world_rules.json, engain_manifest.json);
  the `out of root/manifests/` copies are historical.
