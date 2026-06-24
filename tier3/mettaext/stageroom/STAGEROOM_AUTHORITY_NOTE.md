# Stageroom Authority Note

STAGEROOM_STATUS = METTAEXT_INPUT_OUTPUT_WORKSPACE

Purpose:
- `stageroom/` is the active input/output workspace for Mettaext.
- Generated chapterroom and passroom outputs belong here.
- Source code does not belong here.
- Canon truth is not established by presence in stageroom.

Room boundaries:
- `chapterroom/` contains ABC source code.
- `passroom/` contains Pass 1–5 source code.
- `stageroom/` contains input, output, and proof artifacts.

Authority:
- ABC provides scene packets.
- Passroom compiles scene packets.
- MrLore owns canon review.
- EngAInOS owns runtime acceptance.
- Stageroom output is not accepted runtime truth unless validated/promoted by the proper authority path.

Do not:
- Do not scatter generated output into chapterroom or passroom.
- Do not treat stageroom artifacts as canon by filename or presence.
- Do not overwrite accepted runtime artifacts from stageroom without validator proof.

## Legacy Pipeline Work Relocation

LEGACY_PIPELINE_WORK_REAL_PATH = mettaext/stageroom/output/legacy_pipeline_work
LEGACY_PIPELINE_WORK_COMPAT_PATH = mettaext/compiled/pipeline_work

Rule:
- `mettaext/stageroom/output/legacy_pipeline_work/` is the real home of old compiled pipeline artifacts.
- `mettaext/compiled/pipeline_work` may remain as a symlink for compatibility while loaders are still being remapped.
- New generated output should go to `stageroom/`.
- The symlink does not make `compiled/` the authority owner; it is a compatibility bridge only.

## ABC Clean ID Proof

ABC_CLEAN_ID_PROOF = TRUE

Old bad smoke ID:
- `chapter.999_chapter_999_abc_smoke`

Correct smoke ID:
- `chapter.999_abc_smoke`

Correct scene IDs:
- `scene.999_abc_smoke.scene001`
- `scene.999_abc_smoke.scene002`
- `scene.999_abc_smoke.scene003`

Rule:
- Pass A must prefer the chapter heading title for the slug when a chapter heading exists.
- Filename chapter prefixes must not be duplicated into the chapter slug.
- ABC may propose scene boundaries, but `authored_scene_boundaries_proven` remains false until upgraded by the required authority path.

## Clean ABC → Passroom Proof

CLEAN_ABC_ID_TO_PASSROOM = TRUE
PASSROOM_STILL_WORKS_AFTER_ID_CLEANUP = TRUE
STAGEROOM_OUTPUT_ONLY = TRUE

Proof output:
- `mettaext/stageroom/output/passroom/scene.999_abc_smoke.scene001/out_pass1_scene.999_abc_smoke.scene001.txt`
- `mettaext/stageroom/output/passroom/scene.999_abc_smoke.scene001/out_pass2_scene.999_abc_smoke.scene001.metta`
- `mettaext/stageroom/output/passroom/scene.999_abc_smoke.scene001/zonj_scene.999_abc_smoke.scene001.json`
- `mettaext/stageroom/output/passroom/scene.999_abc_smoke.scene001/999_abc_smoke.scene001.zon`
- `mettaext/stageroom/output/passroom/scene.999_abc_smoke.scene001/999_abc_smoke.scene001.zonj.json`
- `mettaext/stageroom/output/passroom/scene.999_abc_smoke.scene001/game_scenes/scene.999_abc_smoke.scene001.json`
- `mettaext/stageroom/output/passroom/scene.999_abc_smoke.scene001/game_scenes/scene_index.json`

Known non-blocking warning:
- Pass 4 semantic_environment_extractor import needs package cleanup.

## Pass 4 Package Import Cleanup

PASS4_SEMANTIC_EXTRACTOR_IMPORT_CLEANUP = TRUE
PASS4_PACKAGE_MODE_IMPORT = TRUE
PASS4_OUTPUT_WRITTEN = TRUE
PASS5_OUTPUT_WRITTEN = TRUE
STAGEROOM_RULE_AFTER_PASS4_CLEANUP = TRUE

Change:
- `pass4_zon_bridge.py` no longer imports `semantic_environment_extractor` as a loose top-level script.
- It imports the extractor through the `mettaext` package boundary.

Proof:
- `python3 -m py_compile mettaext/passroom/pass4_zon_bridge.py`
- `python3 -m mettaext.passroom.pass4_zon_bridge ...` ran without the semantic extractor import warning.
- `python3 -m mettaext.passroom.pass5_game_bridge ...` emitted game scene JSON.
- `./toolroom/check_stageroom_rule.sh` returned `STAGEROOM_RULE=TRUE`.

Authority:
- No authority changed.
- No lane ownership changed.
- Passroom remains code-only.
- Stageroom remains the generated output workspace.

## Passmap Live Witness

PASSMAP_STRUCTURE = TRUE
PASSMAP_NORMAL_EXIT_ZERO = TRUE
PASSMAP_LIVE_EXIT_ZERO = TRUE
PASSMAP_ROOT_DETECTION = TRUE
PASSMAP_LIVE_COUNTS_TRUTHFUL = TRUE

Proof:
- `./toolroom/passmap.sh` returned exit code 0.
- `./toolroom/passmap.sh --live` returned exit code 0.
- Header root resolved to `mettaext`, not `mettaext/toolroom`.
- Live mode detected real stageroom artifacts for Pass A, Pass B, Pass C, Pass 1, Pass 2, Pass 3, Pass 4, and Pass 5.

Authority:
- Passmap is a witness tool only.
- Passmap does not create output.
- Passmap does not promote artifacts.
- Passmap does not decide canon, runtime, or acceptance.

## Mettaext Stageroom Handoff Final Proof

METTAEXT_STAGEROOM_HANDOFF_FINAL = TRUE
METTAEXT_NO_DISPATCH = TRUE
METTAEXT_DONE_MANIFEST_WRITTEN = TRUE
METTAEXT_DONE_MANIFEST_VALID_JSON = TRUE
ABC_1_TO_5_FULL_PIPELINE = TRUE
STAGEROOM_RULE = TRUE
PASSMAP_LIVE_COUNTS_TRUTHFUL = TRUE

Final doctrine:
- Mettaext reads source prose.
- Mettaext runs chapterroom ABC.
- Mettaext runs passroom Pass 1–5.
- Mettaext writes evidence into stageroom.
- Mettaext writes `mettaext/stageroom/mettaext_done_manifest.json`.
- Mettaext stops.

No dispatch:
- No runtime POST.
- No localhost runtime call.
- No EngAInOS call.
- No MrLore call.
- No GodotSim call.
- No Engionality call.

Consumer rule:
- Consumers pull from stageroom.
- Presence in stageroom is evidence only.
- Presence in stageroom is not canon.
- Presence in stageroom is not runtime truth.
- Acceptance belongs to the owning authority.
