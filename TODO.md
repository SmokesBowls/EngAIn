# EngAIn TODO

Last updated: 2026-07-15. Origin: rehousing repair pass, authority-gate audit,
and out-of-root divergence audit (see commit messages 43bceb0..7e78e1a and
scratch/tier_relocation/TIER_REHOUSING_MAP.md).

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
      lane-theft gate treats it as a foreign lane either way.
- [ ] The 5 colliding `scratch/ap_*_report.json` generations — external runs say ACCEPTED,
      current runs say REJECTED. Which probe generation is trusted? (Both are preserved:
      current in `scratch/`, external in `out of root/scratch/`.)

## Not explored yet

- [ ] **Trixel systems (4–5)** — bulk of externalization b8a11b5 (~690 files: trixelworld,
      trixelcomposer, trixelmap, trixelpixel); in neither repo nor drop. Being repurposed
      elsewhere per user (2026-07-15). Need locations to audit divergence.
- [ ] **Older mrlore in ~/Downloads** — second mrlore version per user; unknown path and
      divergence vs `tier1/mrlore`. Hash-compare when path known.
- [ ] **Externalization remainder** — b8a11b5 removals not in the drop: `terrain/`, some
      `godotsim/` and `docs/` files. Deleted duplicates, tier-rehomed, or homeless?
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
