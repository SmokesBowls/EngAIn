# TIER3 Mettaext Relocation Lock

TIER3_METTAEXT_RELOCATION_FINAL = TRUE
TIER3_METTAEXT_PROOF_ERRORS_FOUND = FALSE

Real home:
- `tier3/mettaext`

Old root:
- `mettaext`
- absent

Old-root wrapper:
- `OLD_ROOT_METTAEXT_WRAPPER = FALSE`

Acceptance lock:
- `TIER3_METTAEXT_REAL_HOME = TRUE`
- `OLD_ROOT_METTAEXT_REQUIRED = FALSE`
- `OLD_ROOT_METTAEXT_WRAPPER = FALSE`
- `TIER3_METTAEXT_IMPORTS = TRUE`
- `TIER3_METTAEXT_PIPELINE = TRUE`
- `TIER3_METTAEXT_DONE_MANIFEST_VALID_JSON = TRUE`
- `TIER3_METTAEXT_STAGEROOM_RULE = TRUE`
- `TIER3_METTAEXT_NO_DISPATCH = TRUE`

Important fixes:
- Internal subprocess module calls now use `tier3.mettaext.*`.
- Stageroom defaults now use `tier3/mettaext/stageroom`.
- Active imports were updated in GodotSim, EngAInOS bridgeroom, semantic extraction, and scene audit tooling.
- Active path references were updated in start tools, smoke tools, vault manager, and proof scripts.
- `world_rules_loader` now resolves the root `manifests/world_rules.json`.

Compatibility note:
- `tier3/mettaext/compiled/pipeline_work` remains a compatibility symlink to:
  `tier3/mettaext/stageroom/output/legacy_pipeline_work`
- This is not an old-root Mettaext wrapper.
- This bridge belongs inside the real `tier3/mettaext` home.

Final doctrine:
- Mettaext is TIER3 structured witness/source parse lane.
- Mettaext finds/indexes text, stages text, parses text, writes evidence, writes done manifest, and stops.
- Mettaext does not dispatch.
- Presence in stageroom is evidence only, not canon and not runtime truth.
