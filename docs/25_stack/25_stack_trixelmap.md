Trixelmap tastes like a real spatial cartographer, but not yet a trusted authority layer. It has the right skeleton: extract spatial facts, normalize authority, solve a 100×100 map, build tile intent, and hand that to Trixelcomposer. The problem is that the stack is currently mixing three vocabularies: narrative extraction relations, YAML/world-authority relations, and solver vectors. Those do not fully agree yet.

## 1. PROJECT ROLE

Trixelmap owns spatial cartography.

It owns location extraction, spatial-relation extraction, authority scoring, candidate/confirmed location registry, normalized spatial authority, deterministic layout solving, region centroids, region bounds, terrain-field tile intent, and Trixelcomposer map handoff contracts.

It does not own canon truth, chapter prose, world-rule decisions, runtime simulation, Godot rendering, creature behavior, AP authority, combat, quest logic, or final art rendering. It can say “this map claim is extractable,” “this location is noisy,” or “these bounds overlap.” It cannot decide whether Ironspire’s lore is canon, whether a chapter should be changed, or whether Trixelcomposer must render a particular style.

Neighboring projects depending on it are Trixelcomposer, Trixelworld/world runtime, MrLore/vault processing, EngAInOS/AP authority, Godot/Godotsim visualization, and any downstream atlas renderer.

## 2. CURRENT WORKING STATUS

Confirmed working: the pipeline shape exists. `trixelmap_build.py` explicitly reads relationship YAML, ZONJ JSON, scene JSON, and vault markdown, then writes `spatial_authority.json`, `resolved_layout.json`, `terrain_field.json`, `trixelcomposer_recipe.json`, and `trixelcomposer_atlas_plan.json`. 

Confirmed working: generated outputs exist. The current `spatial_authority.json` has 8 regions and 6 relation edges from the Azureth YAML authority file.  The current `resolved_layout.json` has centroids and bounds for those 8 regions.  The current recipe and atlas files are also present.  

Partially working: the vault parser and location ranker are useful but noisy. They detect a lot of candidates, score them, and produce reports, but many scored “locations” are dialogue fragments or ordinary phrases. Examples include `we_keep`, `strange`, `return_the_camp`, `our_mountain`, `split_the_marsh`, and `spire_the_spire`.  

Untested or not trustworthy yet: strict relation solving, bounds collision avoidance, biome consistency, recipe compatibility, and end-to-end import stability.

Proof-only / stub: the terrain smoothing is a stub. `_smooth()` currently pads the array instead of applying a real blur, so the comment says “Gaussian blur approx,” but the function does not actually smooth; it changes the array shape. 

Legacy / abandoned signs: relation names like `attached_southwest`, `descends_to`, `borders_east`, `borders_south`, and `borders_southeast` are present in authority input/output, but the solver’s vector vocabulary only knows `north_of`, `south_of`, `east_of`, `west_of`, `above`, `below`, `overlooks`, `adjacent_to`, `connected_to`, and `contained_by`.  

## 3. ERROR PROFILE

Import/path errors: `terrain_field_builder.py` and `trixel_recipe_writer.py` use `Any` in type annotations but import only `Dict` and `List`, not `Any`. That can break import on Python versions/settings that evaluate annotations. Both should use:

```python
from typing import Any, Dict, List
```

Also, `trixelmap_build.py` imports `yaml`, so PyYAML is required. `spatial_layout_solver.py` and `terrain_field_builder.py` require NumPy.   

Missing files: the atlas plan references `terrain_palette.png`, but the stack does not prove that palette exists. 

Duplicate files: not a direct file duplication issue in this 25-stack, but there are duplicate conceptual layers: location scoring exists inside both `vault_spatial_parser.py` and `location_ranker.py`, with overlapping but not perfectly identical scoring logic.  

Stale backups: none visible in the supplied trixelmap stack.

Schema mismatch: the biggest mismatch is relation vocabulary. The YAML uses `attached_southwest`, `descends_to`, `borders_east`, `borders_south`, and `borders_southeast`; the pattern matcher emits `north_of`, `south_of`, `east_of`, `west_of`, `above`, `below`, `contained_by`, `adjacent_to`, and `connected_to`; the solver only has vectors for the second set.   

Runtime bridge mismatch: trixelmap is sidecar/offline JSON production. It does not yet expose a runtime API or Godot bridge. Any project expecting live map mutation or runtime streaming from trixelmap will be wrong.

Godot scene/autoload mismatch: none directly in this stack. Trixelmap produces data, not Godot scenes.

Generated-output drift: severe. The generated `resolved_layout.json` places both `gruulith_mountain` and `northern_faraxar` at centroid `(5,5)`, causing a hard overlap, even though their quadrant hints are northwest and east. 

Old architecture still present: the solver says it is “strength-weighted,” but normalized YAML edges use `weight`, while the solver reads `strength`, defaulting to `0.5` if missing. So YAML authority says `weight: 1.0`, but the solver does not use it as strength unless converted.  

## 4. CONTRADICTION PROFILE

The stack says trixelmap is spatial authority, but the current solved map violates the authority it was given.

Relation vocabulary conflicts:
`attached_southwest`, `descends_to`, `borders_east`, `borders_south`, and `borders_southeast` are accepted into `spatial_authority.json`, but they are not recognized by `RELATION_VECTORS`. The solver therefore treats them as `(0,0)` relation vectors plus sibling spacing, not true directional constraints.  

Centroid/bounds overlap errors:
I found these current overlaps in `resolved_layout.json`:

```text
gruulith_mountain overlaps northern_faraxar: 144 tiles
crescent_mountain_range overlaps southern_faraxar: 126 tiles
crescent_mountain_range overlaps ironspire: 36 tiles
crescent_mountain_range overlaps dragondeep_water: 104 tiles
southern_faraxar overlaps ironspire: 12 tiles
southern_faraxar overlaps dragondeep_water: 100 tiles
ironspire overlaps dragondeep_water: 55 tiles
```

That means the solver is producing a map, but not yet a collision-safe map.

Authority score contradictions:
`ironspire` is scored `169.0` and confirmed despite having `0` spatial claims. `falcon_ridge` is scored `87.0` with `0` spatial claims. `we_keep` is scored as confirmed at `23.0` with `0` spatial claims. This means “mentioned in many files” can overpower “is this actually a place with spatial evidence?” 

Terrain field mismatch:
The authority input includes `isolated_peak` and `deep_water`, but the terrain builder and recipe biome mapper do not know those terrain classes. They fall back to biome `5`, the default biome.   

Vault parser noise:
The parser has hygiene filters, but the output still contains noisy names such as `orange`, `our_mountain`, `my_home`, `no_water`, `like_water`, `you_keep`, `we_keep`, and `strange`.  The filter design is good, but the final reports prove it is not strict enough yet.

Trixelcomposer recipe mismatch:
The recipe uses `elevation_center` but fills it from centroid `x`, not centroid `y` or an actual elevation calculation. That means `elevation_center` is mislabeled data. 

Generated output drift:
The generated `terrain_field.json` assigns early tiles to `gruulith_mountain` while showing biome/elevation values that reflect overlap with `northern_faraxar` and nearby regions. The first tiles show `region_id: gruulith_mountain` but `biome_id: 3`, which is arid plains, not frozen volcanic peak. 

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

Name: Spatial Authority Cartographer v1.

Files implying it: `trixelmap_build.py`, `spatial_pattern_matcher.py`, `vault_spatial_parser.py`, `location_ranker.py`, `spatial_authority_extractor.py`, `spatial_layout_solver.py`, `terrain_field_builder.py`, `trixel_recipe_writer.py`, and the generated JSON outputs.

What is missing before it becomes real:

The stack needs a canonical relation vocabulary adapter. It must translate `borders_east` to `east_of` or an adjacency constraint with east-side contact. It must translate `attached_southwest`, `descends_to`, and `borders_southeast` into solver-known vectors.

It needs bounds collision resolution after centroid solving.

It needs terrain-class registry alignment between authority YAML, terrain field, and Trixelcomposer biome IDs.

It needs a strict “location candidate quarantine” tier so `we_keep`, `strange`, `return_the_camp`, and pronoun/dialogue fragments cannot become confirmed map authorities.

It needs a generated-output validator that fails the build on overlap, unknown biome class, unknown relation, impossible containment, or recipe/terrain mismatch.

## 6. INBOUND SCHEMA

Inbound item: vault/chapter spatial evidence.
Source project: MrLore / vault parser / chapter corpus.
Expected filename or schema name: `location_spatial_evidence.json`.
Required fields: `canonical_id`, `aliases`, `files_mentioned`, `evidence`, `confidence`, `conflicts`.
Optional fields: `terrain_hint`, `distance_hint`, `placement_status`, `authority_tier`.
Failure behavior if missing: trixelmap may still build from YAML, but it must mark vault-derived location authority unavailable and refuse to claim canon-wide map confidence.

Inbound item: location names.
Source project: MrLore / Canon registry / scene extraction.
Expected schema: location registry or canonical location list.
Required fields: `id`, `aliases`, `canon_status`.
Optional fields: `terrain_class`, `world`, `region`, `chapter_refs`.
Failure behavior: extracted location names remain candidates only. No confirmed tier from mentions alone.

Inbound item: relation phrases.
Source project: vault parser / spatial pattern matcher / canon rules.
Expected schema: relation vocabulary map.
Required fields: `source_phrase`, `canonical_relation`, `inverse_relation`, `confidence`, `solver_vector`.
Optional fields: `distance_hint`, `containment_hint`, `edge_contact_hint`.
Failure behavior: unknown relations must stop the layout build or be downgraded to `adjacent_to_unresolved`, not silently treated as `(0,0)`.

Inbound item: world rules.
Source project: EngAInOS / AP world authority.
Expected schema: world spatial constraints.
Required fields: `world_id`, `allowed_regions`, `forbidden_overlaps`, `scale`, `coordinate_space`.
Optional fields: `era`, `act`, `sky_state`, `travel_graph`.
Failure behavior: trixelmap may generate a draft map only, not an authoritative world map.

Inbound item: canon constraints.
Source project: MrLore / canon authority.
Expected schema: canon spatial constraints.
Required fields: `location_id`, `canon_status`, `allowed_aliases`, `must_not_merge_with`.
Optional fields: `known_parent_region`, `known_neighbors`, `chapter_evidence`.
Failure behavior: alias resolution must stay conservative; do not merge `mars_spire`, `mars_void_spire`, `martian_void_spire`, and `void_spire` without canon approval.

## 7. OUTBOUND SCHEMA

Outbound item: `spatial_authority.json`.
Destination project: spatial solver, Trixelcomposer, EngAInOS review, human cartography review.
Required fields: `version`, `source`, `regions`, `edges`. Region required fields: `id`, `quadrant_hint`, `terrain_class`, `size_hint`. Edge required fields: `from`, `to`, `relation`.
Optional fields: `type`, `landmarks`, `raw`, `validation_predicates`, `weight`.
Stability level: candidate. It exists, but relation vocabulary is not stable.

Outbound item: `resolved_layout.json`.
Destination project: terrain field builder, debug SVG, Trixelcomposer.
Required fields: `version`, `grid_size`, `regions`, with each region having `centroid`, `bounds`, and `terrain_class`.
Optional fields: `type`, `landmarks`.
Stability level: candidate with fix flags. It currently contains hard overlap errors.

Outbound item: `terrain_field.json`.
Destination project: Trixelcomposer / atlas renderer / map preview tools.
Required fields: `version`, `grid_size`, `tiles`; each tile has `x`, `y`, `elevation`, `moisture`, `biome_id`, `region_id`.
Optional fields: none currently, but should add `terrain_class`, `source_region_bounds`, and `confidence`.
Stability level: candidate/unstable. The biome/region mismatch proves drift.

Outbound item: `trixelcomposer_recipe.json`.
Destination project: Trixelcomposer.
Required fields: `version`, `type`, `grid_size`, `regions`, `transitions`, `landmarks`.
Optional fields: transition rules, moisture profile.
Stability level: candidate. It is structurally useful, but `elevation_center` is not actually elevation.

Outbound item: `trixelcomposer_atlas_plan.json`.
Destination project: Trixelcomposer / renderer.
Required fields: `version`, `type`, `layers`, `tile_size`, `export_format`, `seed`.
Optional fields: palettes, modes, z-indexes.
Stability level: candidate. It references palette assets not proven in stack.

Outbound item: location authority report.
Destination project: human review, MrLore, canon registry.
Expected filename: `location_authority_report.md` and `location_authority_registry.json`.
Required fields: location ID, score, tier, files, evidence count, aliases, conflicts.
Optional fields: confidence, spatial claims.
Stability level: useful but not authority-ready. The scoring confirms noisy items too easily.

## 8. AUTHORITY BOUNDARIES

Trixelmap must stop and ask MrLore/canon authority when alias merges change story meaning. It cannot decide whether `mars_void_spire`, `martian_void_spire`, `void_spire`, `earth_void_spire`, and `light_the_void_spire` are separate places, nested places, bad extractions, or era/world variants.

Trixelmap must stop and ask EngAInOS/AP authority before world rules become executable runtime rules.

Trixelmap must stop and ask Trixelcomposer before changing recipe or atlas schema names.

Trixelmap must stop and ask the human when a location has many mentions but zero spatial evidence and is being promoted to confirmed.

Other projects must stop and ask trixelmap before consuming `resolved_layout.json`, `terrain_field.json`, or atlas plans as final map authority. Trixelmap owns whether a layout is collision-safe, relation-consistent, and biome-consistent.

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Is `trixelmap` allowed to be the canonical 2D spatial authority, or only a draft cartographer?

2. Should “multi-file mention count” be enough to confirm a location, or must every confirmed location require at least one spatial claim?

3. Are `void_spire`, `earth_void_spire`, `mars_void_spire`, `martian_void_spire`, and `umbrageous_void_spire` separate locations, aliases, nested locations, or world/era variants?

4. Should `we_keep`, `you_keep`, `return_the_camp`, `our_mountain`, `strange`, and similar phrases be automatically quarantined forever?

5. What is the canonical relation vocabulary: `north_of/east_of/contained_by`, `borders_east/descends_to`, or both with an adapter?

6. Should `attached_southwest` mean the source is southwest of the target, or that the source attaches to the target’s southwest edge?

7. Should `descends_to` affect elevation only, position only, or both?

8. Are `isolated_peak` and `deep_water` valid terrain classes? If yes, what biome IDs should they map to?

9. Should overlapping bounds ever be legal, for example a mountain range containing Ironspire, or should every overlap require explicit `contains/contained_by` authority?

10. Does Trixelcomposer expect `elevation_center`, or should the recipe field be renamed to `centroid_x`, `centroid`, or replaced with real terrain elevation stats?

## 10. STACK VERDICT

AUTHORITY_WITH_FIX_FLAGS.

This is not proof-only. It has real files, real generated outputs, a real sidecar build pipeline, a real solver, a real terrain field, and real Trixelcomposer handoff contracts. But it cannot be called `AUTHORITY_READY` yet because the current outputs contain relation vocabulary drift, bounds overlap errors, terrain-class fallback errors, noisy vault candidates, and recipe/terrain mismatches.

The immediate fix flags are:

```text
FIX 1: import Any in terrain_field_builder.py and trixel_recipe_writer.py
FIX 2: normalize relation vocabulary before solve_layout()
FIX 3: convert edge weight -> strength or teach solver to read weight
FIX 4: add unknown-relation validator
FIX 5: add bounds-overlap validator
FIX 6: add terrain_class -> biome_id registry shared by terrain and recipe
FIX 7: add isolated_peak and deep_water biome mappings
FIX 8: quarantine noisy vault parser candidates before ranker confirmation
FIX 9: replace _smooth() padding stub with real smoothing or remove smoothing
FIX 10: rename or correct recipe elevation_center
```

My clean lane summary:

```text
trixelmap owns spatial cartography intelligence.
It may extract, score, solve, validate, and hand off map contracts.
It must not claim canon truth.
It must not render final art.
It must not silently accept unknown relations.
It must not promote noisy vault phrases into map authority without review.
Current verdict: AUTHORITY_WITH_FIX_FLAGS.
```
