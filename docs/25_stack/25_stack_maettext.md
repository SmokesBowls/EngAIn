mettaext profile: prose-to-ZON/game-scene pipeline
Stack verdict: AUTHORITY_WITH_FIX_FLAGS

mettaext owns the compiler lane between raw prose and engine-readable scene artifacts. It can segment prose, infer rough semantic atoms, merge explicit and inferred data, convert merged scenes into ZON/ZONJ memory fabric, convert ZON/ZONJ into game scene JSON, and build scene indexes. It does not own canon truth, final lore authority, runtime simulation, Godot rendering, AP mutation authority, or MrLore contradiction resolution.

The safest way to say it:

mettaext is not the lore judge.
mettaext is not the game runtime.
mettaext is the transformer.

It turns:

raw prose/chapter text
→ pass1 explicit segments
→ pass2 semantic inference
→ pass3 merged ZONJ scene
→ pass4 ZON/ZONJ memory fabric
→ pass5 game scene JSON
→ scene index / runtime-loadable scene payload

That basic role is confirmed by `pipeline_runner.py`, which says it chains the Scene Pipeline P1-P5, then runs the semantic compiler, then posts the result to the Godot simulation runtime. 

1. PROJECT ROLE

mettaext owns:

The prose segmentation layer. `pass1_explicit.py` takes raw text and emits structured semantic-unit lines such as narration, dialogue, internal monologue, blank, and scene header. 

The merge layer. `pass3_merge.py` takes Pass 1 explicit structure and Pass 2 metta inference output, then produces a single ZONJ JSON scene with `type`, `id`, `source_files`, `segments`, speaker fields, header attributes, and inferred speaker/thought data. 

The ZON/ZONJ bridge. `pass4_zon_bridge.py` converts Pass 3 ZONJ narrative scenes into ZON memory fabric with temporal anchoring, spatial anchoring, entity tracking, and terrain metadata.

The game-scene bridge. `pass5_game_bridge.py` converts ZON memory fabric into game scene JSON with `scene_id`, `description`, `entities`, `locations`, `events`, `initial_state`, `metadata`, terrain metadata, and level design. 

The local scene index / cache routing layer. `build_scene_index.py` and Pass 5’s `_build_scene_index()` generate scene lookup/index data for loaded or generated scene files. 

mettaext does not own:

Canon truth. That belongs upstream to `_mrlore` / canon contracts.

Entity ontology truth. `world_rules_loader.py` says `world_rules.json` is the single source of truth for entity classification, spawnability, render mode, and cardinality. 

Runtime truth. The runtime consumes or rejects scene payloads; mettaext only prepares them.

Godot display/autoload truth. GodotSim, engain_avatar, or zonjrender own rendering, autoloads, UI chooser, and runtime scene mounting.

AP/world mutation authority. mettaext can describe scenes; it must not decide permanent world mutation without AP/canon validation.

Neighboring projects that depend on mettaext:

_mrlore depends on mettaext to consume clean prose/canon contracts and not mutate Tier 0 prose.

EngAInOS / runtime depends on mettaext to produce stable game scene JSON and runtime-loadable scene IDs.

GodotSim / zonjrender depends on mettaext to produce usable scene files, scene indexes, terrain metadata, entities, and events.

Trixel / art generators depend on mettaext for terrain/environment/level-design hints, but should not treat generated hints as canon.

2. CURRENT WORKING STATUS

Confirmed working:

The stack has a clear intended pass chain. `pipeline_runner.py` runs `master_pipeline.py`, expects `<chapter>.zonj.json`, runs `zw_compiler.py`, emits `<chapter>_with_semantics.zonj.json`, prints a compiler report, and posts to `http://127.0.0.1:8080/scene/load`. 

Pass 1 exists and emits structured typed lines. It recognizes headers, blank lines, internal monologue, dialogue, dialogue tails, and narration. 

Pass 3 is reasonably robust. It explicitly preserves unknown Pass 1 header fields and tolerates extra or reordered Pass 2 atom attributes instead of exploding on format drift. 

Scene identity canonicalization exists. `scene_identity.py` defines canonical IDs as stable, zero-padded, lowercase strings like `scene.001_the_ethereal_vigil`, while keeping legacy aliases readable but not authoritative. 

World rules authority exists. Unknown entities are treated as unknown/non-spawnable and must be surfaced rather than silently accepted. 

Partially working:

Semantic extraction works as heuristic inference, not canon. `pass2_enhanced.py`, `pass2_event_builder.py`, `semantic_environment_extractor.py`, and keyword/voting terrain systems can infer speakers, emotions, actions, environment, and level-design hints, but they are not strong enough to be final authority.

Terrain metadata is duplicated between Pass 4 and Pass 5. Both have terrain keyword registries / weighted voting. That means terrain can drift depending on which pass gets final say.

Scene indexes exist, but the uploaded `scene_index.json` shows 109 scenes and includes suspicious duplicate-number patterns like `005_fairy_tale` and `005_the_garden_blooms`, `006_fairy_tale` and `006_the_first_coming`, etc. That means index output is useful evidence, not clean authority. 

Untested or not proven in this stack:

Full end-to-end canonical run from `_mrlore` raw canon manifest into mettaext into runtime, with duplicate-scene detection, canonical ID enforcement, and world-rules validation all enabled.

Whether `master_pipeline.py`, `engain_ingest.py`, `pipeline_runner.py`, `narrative_to_game.py`, and `run1time.py` agree on the same pass scripts and output filenames.

Whether every generated ZONJ uses `scene_identity.py` canonical IDs before indexing.

Whether `world_rules.json` is actually present at the expected path in this project stack.

Abandoned, legacy, or proof-only:

`narrative_to_game.py` looks legacy/proof-only because it calls `pass2_core.py`, uses older filenames like `zonj_out_pass1_<base>.txt`, and expects output names that conflict with the current `pass3_merge.py` / `pass4_zon_bridge.py` behavior.

`run1time.py` is a working smoke-style runner, but it hardcodes a vault cache path under `/home/mytruelove/Desktop/...`, so it is not portable authority.

Generated files such as `mechanical_lore.zonj.json`, `scene.mechanical_lore.json`, and `scene_index.json` are evidence only. They should not be treated as source authority.

3. ERROR PROFILE

Import/path errors:

Likely: `pass2_core.py` vs `pass2_enhanced.py`. `master_pipeline.py` uses `pass2_enhanced.py`, while `engain_ingest.py` and `narrative_to_game.py` refer to `pass2_core.py` in parts of the stack. That is a pass order / script naming contradiction.

Likely: `world_rules_loader.py` default path expects `../manifests/world_rules.json`. If mettaext is not located exactly relative to `manifests/world_rules.json`, entity validation silently fails or blocks everything. 

Likely: runtime post assumes `http://127.0.0.1:8080/scene/load`; if GodotSim/runtime is not running, `pipeline_runner.py` only warns after compilation. 

Missing files:

`world_rules.json` is required but not included in the visible 25-stack. The loader treats missing rules as an error. 

`engain_manifest.json` is expected by `pipeline_runner.py` helper `_load_manifest`, but that helper is not visibly used in the actual run path. This is a design smell: manifest authority is implied but not enforced. 

Duplicate files:

There are multiple pipeline runners: `master_pipeline.py`, `pipeline_runner.py`, `narrative_to_game.py`, `engain_ingest.py`, and `run1time.py`. They overlap authority.

There are multiple terrain/environment inference implementations: `semantic_environment_extractor.py`, Pass 4 terrain voting, Pass 5 terrain voting, and `build_scene_index.py` terrain inference.

There are multiple scene index builders: `build_scene_index.py` and Pass 5 `_build_scene_index()`.

Stale backups / stale architecture:

`narrative_to_game.py` appears stale because its filenames and pass assumptions do not match the current Pass 3 and Pass 4 pattern.

Any generated `_with_semantics.zonj.json` file is downstream output. It should not become source input unless explicitly marked as cached generated evidence.

Schema mismatch:

Old ZONJ format uses `{id, type, segments, source_files}`.

Newer game scene format uses `{scene_id, description, entities, locations, events, initial_state, metadata}`.

Pass 5 reads `@id`, `@when`, `@where`, `@entities`, and `=segments`; Pass 3 produces plain `id`, `type`, and `segments`. Pass 4 must be the mandatory conversion boundary or Pass 5 will receive incomplete shape.

Runtime bridge mismatch:

`pipeline_runner.py` posts the semantic ZONJ directly to `/scene/load`, but Pass 5 produces game-scene JSON. Human review must decide whether runtime `/scene/load` wants ZONJ or game scene JSON. Right now both are plausible, which is dangerous.

Godot scene/autoload mismatch:

Not directly owned by mettaext. mettaext can only guarantee scene payloads and indexes. If Godot UI chooser expects `active_scenes` but another index builder writes `count/scenes`, GodotSim must declare the accepted index schema.

Generated-output drift:

The uploaded `scene_index.json` claims `count: 109`, includes generated file paths, and marks scenes `playable`. Because it contains duplicate chapter numbers and cache paths, it should be treated as a build report, not authority. 

Old architecture still present:

The old architecture is still present in `narrative_to_game.py` and probably in `run1time.py`. These are useful as smoke scripts but should not own architecture.

4. CONTRADICTION PROFILE

Contradiction with own stated role:

mettaext says it is a compiler/transformer, but some files drift into ontology authority. `world_rules_loader.py` correctly says world rules own ontology, but Pass 5 has its own `_is_spawnable()` behavior that returns `True` for unknown entities when no world rules are loaded. That contradicts the stricter loader contract that unknowns are non-spawnable and must be surfaced. 

Contradiction with another project’s role:

`zw_world_rules_compiler.py` enriches `world_rules.json` from `.zw` lore files. That touches canon/entity authority and must be mediated by `_mrlore` or a canon/world-rules owner before becoming trusted runtime law.

Contradiction with current home/project decisions:

The stack still contains hardcoded paths under `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/...`. That contradicts portable project-root discipline.

File naming contradictions:

`pass2_enhanced.py` vs `pass2_core.py`.

`zonj_<base>.json` vs `<base>.zonj.json` vs `<base>_with_semantics.zonj.json`.

`scene.<base>.json` vs `<scene_id>.json`.

`id` vs `@id` vs `scene_id`.

Schema name contradictions:

ZONJ sometimes means merged scene JSON from Pass 3.

ZONJ sometimes means Pass 4 memory-fabric JSON with `@id`, `@when`, and `=segments`.

Game scene JSON sometimes still gets called scene JSON or ZONJ-loaded scene.

Old vs new pipeline behavior:

Newer behavior wants Pass 1 → Pass 2 → Pass 3 → Pass 4 → Pass 5.

`pipeline_runner.py` says P1-P5, then ZW compiler, then runtime post. 

But `pipeline_runner.py` posts the semantic ZONJ, not the Pass 5 game scene, which means the final runtime contract is still ambiguous.

5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

Name: Canon-Gated Narrative Scene Compiler

Files implying it:

`pipeline_runner.py` implies one-button P1-P5 + semantic compiler + runtime push. 

`world_rules_loader.py` implies a canonical ontology gate where unknown entities are surfaced and not guessed. 

`scene_identity.py` implies a canonical scene identity service that all outputs must use. 

`pass2_entity_filter.py` implies extraction-noise filtering that defers ontology truth to `world_rules_loader.py`.

`pass2_event_builder.py` implies a future structured event layer.

`zw_world_rules_compiler.py` implies ZW lore can enrich world rules, AP rules, and event seeds.

What is missing before it becomes real:

One canonical runner.

One canonical pass list.

One canonical scene ID function used by every pass before writing.

One declared runtime input schema: ZONJ or game scene JSON, not both.

One required inbound `_mrlore` canon contract.

One required `world_rules.json` path or manifest field.

One duplicate-scene detector that blocks index generation when canonical IDs collide.

One “generated output is not source authority” marker in every cache/output directory.

6. INBOUND SCHEMA

Inbound item: raw prose/chapter text

Source project: `_mrlore` or human canon vault.

Expected filename/schema: `.md` or `.txt` chapter file.

Required fields: prose body; stable chapter filename or manifest ID; chapter number/title if available.

Optional fields: book/epoch/act/campaign; scene headings; speaker formatting; REGION annotations.

Failure behavior if missing: Pass 1 cannot run without file; if headings are missing, Pass 1 creates default/weak structure; scene ID may drift to filename-derived fallback.

Inbound item: canon/world rules

Source project: `_mrlore`, EngAInOS canon/world-rules authority, or manifests lane.

Expected filename/schema: `manifests/world_rules.json`.

Required fields per entity: `entity_type`, `cardinality`, `spawnable`, `render_as`. The validator explicitly checks those fields. 

Optional fields: `canonical_name`, `runtime_projection`, `ap_constraints`, `zw_tags`, source references.

Failure behavior if missing: loader reports missing file; unknown entities should be blocked/non-spawnable and surfaced for canon review. 

Inbound item: scene identity rules

Source project: mettaext local identity authority, but approved by neighboring runtime/Godot projects.

Expected filename/schema: `scene_identity.py`.

Required fields/functions: `canonical_scene_id(raw)`, `scene_id_aliases(raw)`, `to_canonical_scene_id(raw)`.

Optional fields: alias registry, collision report, source manifest mapping.

Failure behavior if missing: duplicate IDs, non-zero-padded IDs, stale aliases, and cache collisions.

Inbound item: MrLore semantic contracts

Source project: `_mrlore`.

Expected filename/schema: proposed `MRLORE_SEMANTIC_CONTRACT_v1.json` or similar.

Required fields: canonical chapter ID; source file path; prose immutability hash; canon entities; canon locations; timeline anchors; world-rule references; contradiction status; allowed extraction scope.

Optional fields: factions, power systems, weather phase, act/campaign mapping, forbidden interpretations, human review flags.

Failure behavior if missing: mettaext may still generate scenes, but output is candidate-only and cannot be promoted to authority.

Inbound item: runtime load contract

Source project: GodotSim / EngAInOS runtime.

Expected filename/schema: `SCENE_LOAD_CONTRACT_v1`.

Required fields: accepted payload type; endpoint path; required keys; accepted scene ID format; error codes.

Optional fields: hot reload behavior; cache location; UI chooser index schema.

Failure behavior if missing: mettaext may post the wrong artifact type to `/scene/load`.

7. OUTBOUND SCHEMA

Outbound item: Pass 1 explicit segments

Destination project: Pass 2, Pass 3.

Expected filename/schema: `out_pass1_<base>.txt`.

Required fields per line: `{type:<type>}` and text.

Optional fields: `speaker`.

Stability level: stable candidate.

Outbound item: Pass 2 semantic metta

Destination project: Pass 3, Pass 2 event builder.

Expected filename/schema: `out_pass2_<base>.metta`.

Required fields: metta atoms such as speaker/action/emotion/thought with line numbers and confidence.

Optional fields: ambiguity, visual, traits, relationships.

Stability level: candidate.

Outbound item: Pass 3 merged ZONJ scene

Destination project: Pass 4.

Expected filename/schema: `zonj_<base>.json`.

Required fields: `type`, `id`, `source_files`, `segments`.

Optional fields: `inferred`, `header_attrs`, `speaker`.

Stability level: candidate. Pass 3 is tolerant by design but not final authority. 

Outbound item: Pass 4 ZON/ZONJ memory fabric

Destination project: Pass 5, runtime if runtime accepts ZONJ.

Expected filename/schema: `<base>.zon` and `<base>.zonj.json`.

Required fields: `@id`, `@when`, `@where`, `@scope`, `@entities`, `=segments`.

Optional fields: terrain/environment metadata, region metadata, ZON blocks.

Stability level: candidate until runtime contract is clarified.

Outbound item: Pass 5 game scene JSON

Destination project: GodotSim / EngAInOS runtime / zonjrender.

Expected filename/schema: `scene.<canonical_id>.json` or `<scene_id>.json`.

Required fields: `scene_id`, `description`, `entities`, `locations`, `events`, `initial_state`, `metadata`.

Optional fields: `terrain_metadata`, `level_design`, `environment_inference`.

Stability level: candidate/stable after world_rules and scene_id gates are enforced. 

Outbound item: scene index

Destination project: Godot UI chooser / scene loader.

Expected filename/schema: `scene_index.json`.

Required fields: must be standardized. Current stack has more than one shape: one index style uses `count/scenes`, another uses `active_scenes`.

Optional fields: display title, cache file, source file, where, when, terrain family, playable status.

Stability level: unknown until GodotSim declares accepted schema.

Outbound item: semantic event/entity payloads

Destination project: runtime, AP, game mechanics, canon debugger.

Expected filename/schema: event/entity JSON inside ZONJ or game scene JSON.

Required fields: entity ID/name/type/spawnability; event type/actor/action/timestamp/source line.

Optional fields: confidence, source excerpt, actor cardinality, emotional/cognitive/physical/system category.

Stability level: candidate.

8. AUTHORITY BOUNDARIES

mettaext must stop and ask `_mrlore` when:

A generated entity is unknown.

A generated scene contradicts canon.

A chapter number/title collision appears.

A generated semantic event implies permanent canon change.

A world rule, faction rule, power rule, or timeline rule would be created or modified.

A generated output is being promoted from cache evidence into canon authority.

mettaext must stop and ask GodotSim / runtime when:

Changing scene load payload shape.

Changing scene index schema.

Changing coordinate/spatial layout expectations.

Changing terrain metadata names consumed by Godot.

Changing whether runtime loads ZONJ or game scene JSON.

Other projects must stop and ask mettaext when:

They change raw-prose input expectations.

They change ZON/ZONJ field names.

They change Pass 1/2/3/4/5 artifact names.

They consume generated scenes as authority.

They need duplicate scene ID resolution.

They need to know whether a scene came from raw prose, generated cache, or manually edited source.

9. TOP 10 QUESTIONS FOR HUMAN REVIEW

10. Which runner is canonical: `engain_ingest.py`, `master_pipeline.py`, `pipeline_runner.py`, `run1time.py`, or a new single runner?

11. Is `pass2_core.py` retired, and should all callers use `pass2_enhanced.py`?

12. Should runtime `/scene/load` receive Pass 4 ZONJ or Pass 5 game scene JSON?

13. Should every scene ID be forced through `scene_identity.py` before any file is written?

14. What is the official scene index schema: `count/scenes` or `active_scenes`?

15. Are duplicate chapter numbers allowed when titles differ, such as `005_fairy_tale` and `005_the_garden_blooms`, or must chapter numbers be unique?

16. Where is the authoritative `world_rules.json`, and does mettaext load it by manifest instead of relative path?

17. What exact `_mrlore` contract must arrive before mettaext can call output “canon-safe”?

18. Are mechanical lore files allowed to become scenes, or should they compile only into world rules/game mechanics?

19. Should generated `_with_semantics.zonj.json` files ever be re-ingested, or must raw prose always be the only re-ingestable source?

20. STACK VERDICT

AUTHORITY_WITH_FIX_FLAGS

Reason:

mettaext has enough structure to be the authority for prose-to-scene transformation. The pass chain exists. The scene identity module exists. The world-rules authority boundary exists. Pass 1, Pass 3, Pass 4, Pass 5, semantic extraction, game-scene generation, and indexing are all represented in the 25-stack.

But it cannot be AUTHORITY_READY yet because the stack has fix flags:

`pass2_core.py` vs `pass2_enhanced.py` mismatch.

Multiple runners with different assumptions.

Multiple scene index schemas.

ZONJ means more than one thing depending on pass stage.

Pass 5 can allow unknown entities if world rules are not loaded, which conflicts with the stricter ontology contract.

Generated outputs are present in the stack and must not be treated as source authority.

`scene_index.json` shows likely duplicate scene-number drift and cache-path authority leakage.

Missing inbound `_mrlore` semantic contract prevents canon-safe promotion.

Clean ruling:

mettaext is the right pipeline.
mettaext is not broken.
mettaext is not fully trusted yet.
It needs one canonical runner, one scene ID gate, one world-rules path, one runtime schema, and one `_mrlore` inbound contract before it can be promoted to AUTHORITY_READY.
