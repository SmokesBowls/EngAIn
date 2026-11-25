# OP_D — Connect WorldField's grid-facts emitter

OPERATION_ID: OP_D
SYSTEM: Tier 2 WorldField
SCRIPT_PATH: tier2/worldfield/trixel_world_adapter.py (field_from_elevation_grid, new); grid_facts_emitter.py (unchanged)
FUNCTION: field_from_elevation_grid(elevations, profile_id, chunk_size=32) -> (world_field, bridge, adapter); emit_grid_facts(world_field, adapter)
INPUT_ARTIFACT: a declared numerical elevation grid (rows=field_y, cols=field_x, [0,1])
OUTPUT_ARTIFACT: worldfield_grid_facts.v1

GATES:
  real_scene_input_not_demo: BLOCKED (no real scene declares an elevation field; see blockers)
  numerical_substrate_populated: TRUE (values written into WorldField chunks; dirty-chunk sync classifies)
  classification_and_elevation_agree: TRUE (every cell: terrain == value_to_terrain(elevation, profile))
  dense_row_major: TRUE
  cell_count_equals_w_x_h: TRUE
  unmapped_terrain_reported: TRUE
  missing_recipes_block_construction: TRUE (assembler refuses recipe=null; existing behaviour)
  elevation_not_reconstructed_from_labels: TRUE (one direction only: elevation -> classification)
  recipes_exist_in_trixel_registry: TRUE (all 9 TERRAIN_TO_RECIPE targets are trixel3.2d/recipes/terrain/*.json)
  existing_emitter_smoke: TRUE

FINDING: the legacy region-contract path (load_region_contract / --contract CLI) sculpts a side matrix from a 0.5 base, classifies it into the adapter and never writes the nucleus, so emit_grid_facts on that field reads 0.0 elevations under non-matching terrain. Left untouched (legacy demo); the new builder is the path that keeps one field. Material swaps (e.g. ash -> coarse_sediment_dark) are appearance and are not folded into terrain classification.

FILES_CREATED: tier2/worldfield/tests/{__init__.py,test_scene_grid_facts.py}
FILES_MODIFIED: tier2/worldfield/trixel_world_adapter.py (+field_from_elevation_grid)
TESTS_EXECUTED: tier2/worldfield/tests (5, incl. the existing `python -m tier2.worldfield.grid_facts_emitter` smoke)
TESTS_PASSED: 5 (+5 subtests)
TESTS_FAILED: 0
PRE_EXISTING_FAILURES: none in scope
DEPENDENCY_BLOCKERS:
  - PRODUCTION BLOCKED: no producer of real scene elevation exists. Pass 5 scenes carry no terrain; the only region contract with elevation is scene.proof.001 under retired MrLore; environment_manager's keyword terrain is Blender-gated (T03-R1). A manuscript-sourced elevation field for a selected scene is a missing upstream capability (WorldField/Mettaext lane), not invented here.
AUTHORITY_BOUNDARY: WorldField holds elevation and classification; recipe choice is the existing explicit table; nothing guessed.
GIT_COMMIT: (this commit)
