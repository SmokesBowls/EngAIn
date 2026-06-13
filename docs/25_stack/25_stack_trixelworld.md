## trixelworld project awareness profile

Project identified as: **trixelworld — art-material runtime / surface behavior lab**

Stack verdict: **AUTHORITY_WITH_FIX_FLAGS**

trixelworld has real authority over the experimental brush/material rendering lane, but not over final GIMP brush truth, final pixel tooling, or final game-scene authority. The stack proves a working concept: normalized brush assets, recipes, surface vocabulary, deterministic stroke events, surface buffers, material sheets, tree rendering, atmosphere experiments, and stress scenes. But it also shows import drift, parser leakage, asset-source uncertainty, and several “future system” stubs that should not be mistaken for finished authority.

The most important truth: **current GIMP brush assets are evidence and input material, not final authority.** The stack itself says downstream systems should see normalized Trixel types, not raw GIMP format knowledge; `brush_models_mr.py` defines the normalized layer as “no parsing, no I/O, no GIMP knowledge,” with parsers converted through the adapter before downstream use. 

---

## 1. PROJECT ROLE

trixelworld owns the **art-material runtime lab**. Its core job is to answer: “Given a brush/material/surface intent, what kind of surface mark can we render into a buffer, and what lessons does that teach the final pixel toolchain?”

It owns:

Surface mark experimentation.

Brush asset normalization.

Brush recipe assembly.

Stroke sampling.

SurfaceBuffer rendering.

Material vocabulary sheets.

Behavior vocabulary for surfaces.

Render-kernel lessons for the future pixel chain.

Small proof scenes such as beach material sheets, tree material tests, and stress scenes.

It explicitly does **not** own:

Final GIMP brush-source authority.

Final human art direction.

Final trixelpixel implementation.

Final trixelcomposer scene orchestration.

Godot scene/autoload authority.

Canon/lore authority.

Runtime AP authority.

World-object truth beyond visual proof definitions.

The neighboring projects that depend on it are:

**trixelcomposer**, which needs behavior vocabulary, recipe lessons, material sheets, and stroke/material proof outputs.

**trixelpixel**, which should inherit the final pixel/brush kernel lessons after trixelworld proves them.

**trixelmap**, which may consume palette discipline, material layer logic, terrain strokes, and surface-buffer concepts.

**Godot / godotsim / zonjrender**, which may eventually display outputs, but should not import parser-layer or GIMP-layer assumptions directly.

**EngAInOS / runtime kernel**, which may need material intent contracts, but should not accept trixelworld as world authority.

---

## 2. CURRENT WORKING STATUS

Confirmed working, by file structure and declared interfaces:

The normalized brush data model exists. It defines brush shape assets, dynamics assets, presets, palettes, patterns, variant bundles, and assembled brush recipes. It also explicitly says downstream systems should see normalized models rather than parser internals. 

The material proof lane exists. `demo_beach_material_sheet.py` renders a vocabulary sheet whose purpose is to test whether each strip reads as a material without relying on its label. That is exactly the right kind of artifact for this project: not final art, but visual proof. 

The atmosphere lane exists as a mathematical rasterization experiment for flares, glows, rays, and secondaries. It is decoupled from brush shapes in intent, but the implementation currently imports registry and asset models directly, so it still needs cleanup. 

The GIMP parser layer is real. `.vbr`, `.gbr`, `.gih`, `.gdyn`, `.gpl`, `.ggr`, `.gfig`, `.gtp`, and gimpressionist parsing exist as recovery/adapter inputs. But these are **asset archaeology tools**, not final art authority.

Partially working:

The recipe layer works as named intent, but it is still too tied to recovered or stock GIMP names such as `Charcoal-01`, `Bristles-01`, `Acrylic 03`, and `Oils-01`.

The surface behavior vocabulary works conceptually, but some of it likely belongs upstream in trixelcomposer or downstream in trixelpixel depending on whether it describes artistic intent or pixel execution.

The tree renderer proves authored GFig-guided scaffolds and layered surface rendering, but it is too much “world object renderer” for trixelworld’s final role.

The beach sheet proves material strips, but it is still demo/proof harness territory.

Untested or uncertain:

Full cross-project inbound/outbound contracts.

Real runtime bridge ingestion.

Godot display integration.

Whether all parser paths resolve consistently outside this flat 25-stack layout.

Whether all recovered GIMP assets are valid, stable, and legally/project-wise appropriate as defaults.

Whether surface buffer output has a final canonical serialization format.

Abandoned, legacy, or proof-only:

Direct reliance on stock GIMP brush names should be treated as **proof-only**.

GIMP brush recovery logic should be treated as **historical evidence / asset archaeology**, not production source.

The tree/world scene renderers are valuable experiments, but world-object rendering should eventually move out of trixelworld unless the object is only being used as a material test.

The material sheet is proof-only until it has pass/fail metadata and a stable outbound schema.

---

## 3. ERROR PROFILE

Import/path errors:

There is path drift around `brushes/` imports. Some files say parser modules live in `brushes/gbr_parser_mr.py`, `brushes/gih_parser_mr.py`, etc., while the uploaded stack also shows many parser files sitting as top-level files. That creates a high chance of `ModuleNotFoundError: No module named brushes...` unless the repo layout matches exactly.

`render_pictures.py` is a red flag because it imports `from brushes.engine_mr import SurfaceBuffer`, while the 25-stack has `engine_mr.py` at the project root. That is direct import drift.

Several scripts insert `sys.path` manually. That is useful for smoke tests but unsafe as architectural authority.

Missing files:

`world_tree_mr.py` expects `data/gfig/<species>_scaffold` files. If those scaffold assets are not present, tree influence fields quietly degrade.

The smoke runner references entrypoints like `debugerrors.py`, `debugnames.py`, `test_spacing_ratio.py`, `test_parse.py`, `test_gflare_loader.py`, `test_regression_mr.py`, `quick_testv2.py`, `quik_test.py`, `testing_space.py`, and `trixel_demo_mr.py`. They are not all present in this 25-stack, so the smoke script may describe a fuller repo state than the stack actually contains.

`atmosphere_mr.py` imports `FlareAsset` and `GradientAsset`; those must exist in `brush_models_mr.py`. If they are absent or only partly defined, atmosphere fails at import.

Duplicate files:

`atmosphere_mr.py` duplicates the same three imports twice: `FlareAsset, GradientAsset`, `SurfaceBuffer`, and `AssetRegistry`. That is small but confirms cleanup need. 

There are duplicate conceptual parsers: `lisp_parser_mr.py` exists, but `gtp_parser_mr.py` and `gdyn_parser_mr.py` still appear regex-driven in parts. That is not necessarily broken, but it suggests parser architecture has not fully converged.

Stale backups:

No explicit `.bak` files appear in the 25-stack list, but the dependency comments and mixed module names imply this stack may have been assembled during migration. Treat dependency comments as helpful but not authoritative until smoke-tested.

Schema mismatch:

`brush_models_mr.py` says `.gbr` spacing is converted from header integer as `spacing / 10.0` in the data-model comments, while the adapter search result indicates a corrected conversion using `raw / 10000.0`. That is a material contradiction and must be corrected in comments or code. The model’s top-level statement cannot disagree with adapter behavior.

Blend modes are lowercase in some recipe/behavior definitions, but `atmosphere_mr.py` checks uppercase `"ADDITION"` and `"SCREEN"`. That creates likely blend-mode mismatch.

Runtime bridge mismatch:

No stable runtime bridge contract is visible here. The stack outputs buffers and proof PNG/PGM/PPM files, not runtime events. That means trixelworld is not yet a runtime service.

Godot scene/autoload mismatch:

No Godot ownership appears in this stack. Any Godot display should consume exported proof artifacts or future schemas only. trixelworld must not claim Godot scene authority.

Generated-output drift:

Material sheets and stress scenes write images, but there is no stable manifest tying output image → recipe version → asset source → palette → seed. That means visual proof can drift between runs even when it looks “close.”

Old architecture still present:

GIMP-stock asset recovery is still close to the center. The adapter boundary is good, but the recipes still lean on GIMP asset names. trixelworld needs to graduate from “GIMP dissector” to “Trixel material behavior engine.”

---

## 4. CONTRADICTION PROFILE

Contradiction against own role:

trixelworld says it is a brush/material runtime lab, but `world_tree_mr.py` acts like a world-object visual system. Tree rendering is useful as a test case, but trixelworld should not become the owner of trees as game/world objects.

Contradiction against neighboring roles:

Surface behavior definitions partially overlap with trixelcomposer. If a behavior says “bark is porous, directional, weathered,” that may belong to trixelcomposer as material intent. If it says “stamp this bitmap with this pressure and spacing into this buffer,” that belongs to trixelworld or trixelpixel.

The final pixel renderer should be trixelpixel, not trixelworld. trixelworld should produce lessons, kernels, and proofs.

Contradiction in file naming:

Dependency comments refer to `brushes/gbr_parser_mr.py` and similar paths, but the current uploaded stack includes parser files at root-level names. This is direct import path drift.

`vbr_parser_mr.py` identifies itself in the header as `module_vbr/parser.py`, which suggests it came from a module folder and was flattened or renamed later. 

Schema-name contradictions:

`BrushRecipe.to_dict()` claims a neutral export for ZW/ZONJ/AP/Godot with no GIMP-specific top-level field names, but nested fields still include `source_format` values like `vbr`, `gbr`, `pgm`, `gpl`, and `gih`. That is acceptable for traceability, but not final neutral schema unless marked as provenance-only. 

Old vs new pipeline behavior:

Old behavior: GIMP brushes are treated as the source.

New behavior: GIMP brushes are parsed into normalized Trixel assets, then used only as inputs. The stack is halfway through that transition.

---

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

Proposed system: **Trixel Material Intent Compiler**

Implied by:

`surface_behavior_mr.py`

`trixel_recipes_mr.py`

`palette_mr.py`

`brush_models_mr.py`

`trixel_brush_adapter.py`

Missing before real:

A stable `MaterialIntent` schema.

A resolver from material intent → surface behavior → recipe candidates.

A scoring layer that can say why a recipe fits bark, sand, foam, cloud, water, etc.

A versioned material vocabulary registry.

A no-GIMP fallback set of native parametric Trixel brushes.

Proposed system: **Surface Behavior Vocabulary API**

Implied by:

`surface_behavior_mr.py`

`world_tree_mr.py`

`demo_beach_material_sheet.py`

Missing before real:

A clear split between semantic behavior and pixel behavior.

A small canonical vocabulary with allowed values.

Ownership decision: trixelcomposer owns high-level behavior requests; trixelworld/trixelpixel owns render execution.

Proposed system: **Brush Adapter Quarantine Layer**

Implied by:

`trixel_brush_adapter.py`

all parser files

`brush_models_mr.py`

Missing before real:

Parser package isolation.

No parser imports outside adapter.

Stable adapter error reports.

Asset provenance manifest.

Source trust flag: stock GIMP / recovered GIMP / custom / generated / unknown.

Proposed system: **Atmosphere Raster Kernel**

Implied by:

`atmosphere_mr.py`

`ggr_parser_mr.py`

scene atmosphere definitions

Missing before real:

Duplicate import cleanup.

Blend-mode normalization.

Gradient asset stability.

Separation from `AssetRegistry`.

Test images and regression hashes.

Proposed system: **Material Proof Sheet Standard**

Implied by:

`demo_beach_material_sheet.py`

`engine_debug_mr.py`

`stress_scene_mr.py`

Missing before real:

Output manifest.

Pass/fail metadata.

Human review notes.

Recipe versions.

Input asset hashes.

Deterministic seed declaration.

Proposed system: **Final Pixel Toolchain Lessons Export**

Implied by:

`engine_mr.py`

`engine_debug_mr.py`

`stress_scene_mr.py`

`demo_beach_material_sheet.py`

Missing before real:

`render_kernel_lessons.json`

List of behaviors that worked.

List of behaviors that failed.

Rules for trixelpixel implementation.

Explicit “do not carry forward” notes.

---

## 6. INBOUND SCHEMA

Inbound item: **brush/material intent**

Source project: trixelcomposer or human art director.

Expected filename/schema name: `material_intent.trixel.json` or `BrushMaterialIntent.v1`.

Required fields:

`material_id`

`target_surface`

`desired_read`

`scale`

`density`

`edge_character`

`fill_character`

`variation_mode`

`age_mode`

`palette_ref`

`seed`

Optional fields:

`preferred_recipe`

`avoid_assets`

`reference_image`

`pressure_profile`

`blend_preference`

`export_size`

Failure behavior if missing:

If `material_id` is missing, reject.

If `target_surface` is missing, default to `generic_surface`.

If `palette_ref` is missing, render grayscale or default debug palette.

If `seed` is missing, generate deterministic seed from material_id but mark output as candidate.

Inbound item: **palette rules**

Source project: trixelmap, trixelcomposer, or palette authority.

Expected filename/schema name: `palette_rules.v1.json`.

Required fields:

`palette_id`

`colors`

`mode`

`allowed_selection_modes`

Optional fields:

`labels`

`material_slots`

`biome_tags`

`elevation_mapping`

`nearest_snap`

Failure behavior if missing:

If palette missing, recipe may still render but must mark output as `palette_unverified`.

Inbound item: **surface behavior request**

Source project: trixelcomposer.

Expected filename/schema name: `surface_behavior_request.v1.json`.

Required fields:

`surface_name`

`edge`

`fill`

`variation`

`age`

`colour_mode`

`blend_mode`

`opacity_range`

`density`

Optional fields:

`direction_bias`

`material_family`

`world_object_ref`

`camera_distance`

Failure behavior if missing:

If behavior request missing, trixelworld can run canned demos only. It should not invent production material behavior.

Inbound item: **optional visual recipe**

Source project: human, trixelcomposer, or recovered asset lab.

Expected filename/schema name: `visual_recipe_hint.v1.json`.

Required fields:

`recipe_name`

`shape_ref` or `bundle_ref`

`colour_mode`

`blend_mode`

Optional fields:

`dynamics_ref`

`palette_ref`

`spacing_override`

`notes`

Failure behavior if missing:

Use recipe search or default proof recipes; mark as generated candidate.

---

## 7. OUTBOUND SCHEMA

Outbound item: **surface buffer**

Destination project: trixelpixel, trixelcomposer, Godot proof viewer.

Expected filename/schema name: `surface_buffer.v1`.

Required fields:

`width`

`height`

`channels`

`data`

`origin`

`coordinate_convention`

Optional fields:

`format`

`seed`

`recipe_id`

`material_id`

`bbox`

Stability level: **candidate**

Reason: `SurfaceBuffer` exists and has PGM/PPM exports, but a cross-project stable file contract is not yet visible.

Outbound item: **material sheet**

Destination project: human review, trixelcomposer.

Expected filename/schema name: `material_sheet.v1.png` plus `material_sheet_manifest.v1.json`.

Required fields:

`sheet_id`

`materials`

`strip_bounds`

`recipe_ids`

`asset_sources`

`seed`

`output_path`

Optional fields:

`human_pass_fail`

`review_notes`

`thumbnail_path`

Stability level: **candidate**

Reason: beach material sheet exists and has explicit visual review purpose: if a strip needs the label to be understood, the recipe needs tuning. 

Outbound item: **stroke-rendered proof**

Destination project: trixelpixel and human review.

Expected filename/schema name: `stroke_proof.v1`.

Required fields:

`proof_id`

`recipe_id`

`stroke_events`

`surface_size`

`output_image`

`seed`

Optional fields:

`debug_log`

`bbox`

`blend_mode`

`pressure_curve_summary`

Stability level: **candidate**

Outbound item: **behavior vocabulary**

Destination project: trixelcomposer.

Expected filename/schema name: `surface_behavior_vocab.v1.json`.

Required fields:

`edge_types`

`fill_types`

`variation_modes`

`age_modes`

`blend_modes`

`colour_modes`

Optional fields:

`examples`

`known_good_recipes`

`known_bad_recipes`

Stability level: **candidate**

Outbound item: **render-kernel lessons for final pixel toolchain**

Destination project: trixelpixel.

Expected filename/schema name: `render_kernel_lessons.v1.md` or `.json`.

Required fields:

`lesson_id`

`source_test`

`finding`

`recommended_action`

`do_not_carry_forward`

Optional fields:

`image_path`

`failure_case`

`human_review`

Stability level: **unknown/candidate**

Reason: lessons are implied by debug/proof files but not yet formalized.

---

## 8. AUTHORITY BOUNDARIES

trixelworld must stop and ask another project when:

It needs final game/world object meaning. Ask trixelcomposer or the world authority.

It needs final pixel architecture. Ask trixelpixel.

It needs Godot scene integration. Ask Godot/godotsim/zonjrender.

It needs canonical lore, biome, or object identity. Ask MrLore / EngAInOS / trixelmap depending on the object.

It needs AP mutation permission. Ask EngAInOS/AP authority.

It needs final human art taste. Ask the human.

Another project must stop and ask trixelworld when:

It wants to know whether a material recipe has a visual proof.

It wants to use a brush recipe generated from GIMP assets.

It wants a surface buffer rendered from a brush/material intent.

It wants the current behavior vocabulary.

It wants to know which brush/parser assumptions are unsafe.

It wants render-kernel lessons before implementing trixelpixel.

---

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Are stock GIMP brushes allowed as temporary source assets, or only as reference specimens?

2. Which assets are recovered/custom and which are freshly installed stock defaults?

3. Should trixelworld keep any parser files, or should all parsers move into a quarantined `asset_importers/` package?

4. Should `surface_behavior_mr.py` stay in trixelworld, or move to trixelcomposer as high-level material vocabulary?

5. Should `world_tree_mr.py` remain as a material proof scene, or move out because it is becoming world-object rendering?

6. What is the canonical output format for `SurfaceBuffer`: raw bytes, PNG, PPM/PGM, JSON metadata plus binary, or Godot Image import?

7. Are GIMP source-format fields allowed in outbound schemas as provenance, or must they be fully stripped before ZW/ZONJ/AP/Godot?

8. What blend-mode spelling is canonical: lowercase `screen/additive/multiply/normal`, uppercase GIMP names, or enum IDs?

9. Which material proofs must pass first: beach, tree, terrain, atmosphere, or brush contact sheet?

10. What project owns final brush feel: trixelworld, trixelpixel, human art direction, or a separate brush/material authority?

---

## 10. STACK VERDICT

**AUTHORITY_WITH_FIX_FLAGS**

Reason:

trixelworld has enough working structure to be an authority over the **lab layer**: normalized brush models, recipes, surface behaviors, stroke rendering, material sheets, and proof scenes. It is not merely historical evidence. It is also not authority-ready, because the stack still contains path drift, parser leakage, duplicate imports, recipe dependence on GIMP names, unclear outbound schemas, and unfinished ownership boundaries.

The clean verdict card:

```text
trixelworld
Status: AUTHORITY_WITH_FIX_FLAGS

Owns:
  art-material runtime experiments
  brush normalization lessons
  surface behavior vocabulary drafts
  SurfaceBuffer proof rendering
  material sheets
  stroke-rendered proofs
  render-kernel lessons for trixelpixel

Does not own:
  final GIMP brush authority
  final pixel toolchain
  final scene/world authority
  Godot scene/autoload wiring
  AP/runtime authority

Primary fix flags:
  1. Quarantine parser layer behind adapter only.
  2. Fix import path drift: root files vs brushes/ package.
  3. Normalize blend-mode spelling.
  4. Remove duplicate atmosphere imports and decouple registry from raster math.
  5. Stop treating stock GIMP assets as final authority.
  6. Move high-level surface behavior decisions toward trixelcomposer unless they are pixel-execution rules.
  7. Convert material sheets into manifest-backed proof artifacts.
  8. Export render-kernel lessons for trixelpixel.
```

Bottom line: this stack tastes like a **real experimental art-material engine**, not a final renderer yet. The bones are good. The danger is letting recovered GIMP brush archaeology pretend to be the future architecture.
