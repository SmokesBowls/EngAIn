# Trixel Composer & Trixel World Dependency Map

This document establishes the structural roles, calling patterns, and paths for the semantic rendering tile server under `trixelcomposer/` and the procedural raster brush dynamics, palette color-contexts, and scaffolds under `trixelworld/`.

---

## 1. Semantic Rendering & Tile Server (`trixelcomposer`)

Responsible for hosting the FastAPI HTTP tile server, translating raw engine scene data/AP definitions into concrete rendering recipes, and generating consolidated terrain spritesheets matching standard GIMP/LibreSprite atlas configurations.

### [tile_server.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/tile_server.py)
* **File Path:** `trixelcomposer/tile_server.py`
* **Role:** High-level FastAPI HTTP server (default port `8766`). Serves procedurally rendered terrain tiles and replace-atlases to Godot client's `TrixelTileClient.gd` autoload.
* **Imports/Calls:** `trixel_render_bridge.compile_scene`, `trixel_render_bridge.render_scene`, `trixel_render_bridge.DEFAULT_TILE_DIR`, `atlas_composer.compose_atlas`, `atlas_composer.list_terrain_types`, `atlas_composer.read_atlas_meta`, `FastAPI`, `FileResponse`, `uvicorn`
* **Called By:** Started manually or via tmux stack script (`tools/engain_stack_tmux.sh`) to service Godot client.
* **Hardcoded Paths:** None (utilizes relative path discovery from `Path(__file__)`).
* **Safe to Move:** **Yes** (FastAPI wrapper module).
* **Notes:** Exposes endpoints `GET /health`, `GET /tile`, `GET /compile`, `GET /atlas`, `GET /atlas/list`, and `GET /tile.png`.

---

### [trixel_render_bridge.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/trixel_render_bridge.py)
* **File Path:** `trixelcomposer/trixel_render_bridge.py`
* **Role:** Translation bridge. Translates `godotengain` scene payload dictionaries to `trixelcomposer` schema format, coordinates scene recipe compilation, and triggers PNG raster generation via CLI or direct API.
* **Imports/Calls:** `scene_server.compile_recipe`, `terminal_trixel.TerminalTrixelComposer`
* **Called By:** `tile_server.py` (via `compile_scene` and `render_scene`), subprocess calls from `godotengain/engainos/core/scene_server.py`.
* **Hardcoded Paths:** `".zw/tiles"` (default local folder for compiled tiles).
* **Safe to Move:** **Yes** (Relies on dynamically inserting its directory to `sys.path` to ensure importability).
* **Notes:** Contains a detailed design comment explaining how to drop it directly into the godotengain scene server as a Python import.

---

### [scene_server.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/scene_server.py)
* **File Path:** `trixelcomposer/scene_server.py`
* **Role:** Recipe selection and compiler. Parses incoming scene hints, resolves keyword overrides (e.g. lava -> volcano), fetches corresponding template recipe files, and injects deterministic RNG seeds and normalized entity coordinates.
* **Imports/Calls:** `terminal_trixel.RecipeRenderer`, `terminal_trixel.TerminalCanvas` (during script testing/listing).
* **Called By:** `trixel_render_bridge.py` (via `compile_scene` and `render_scene`), `atlas_composer.py`.
* **Hardcoded Paths:** `"recipes"` and `"recipes/transitions"` (local template directories).
* **Safe to Move:** **Yes** (Ensures its subdirectory structure is resolved relative to script path).
* **Notes:** Drives deterministic seed generation utilizing `hashlib.md5(scene_id.encode())`.

---

### [terminal_trixel.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/terminal_trixel.py)
* **File Path:** `trixelcomposer/terminal_trixel.py`
* **Role:** Main controller for autonomous painting, canvas snapshots, learning preferences, and recipe execution. Orchestrates pixel manipulation in memory and writes output PNGs.
* **Imports/Calls:** `entity_layer` (local module), `PIL.Image` (optional), `ollama` (optional), `lmdb` (optional)
* **Called By:** `trixel_render_bridge.py` (via `TerminalTrixelComposer`).
* **Hardcoded Paths:** `".zw/snapshots.json"`, `".zw/memory.json"`, `".zw/sessions"`, `".zw/artwork"`, `".zw/experience_log.jsonl"`, `".zw/experience_counter.txt"`, `".zw/experience.lmdb"`, `".zw/keystrokes.jsonl"`, `".zw/art.intent"`
* **Safe to Move:** **Yes** (Keeps local dot-folders for session logs and weights).
* **Notes:** Implements `RecipeRenderer` which runs procedural step types: `gradient_fill`, `noise_scatter`, `h_band`, `v_crack`, and `ember_scatter`.

---

### [enhanced_trixel_core.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/enhanced_trixel_core.py)
* **File Path:** `trixelcomposer/enhanced_trixel_core.py`
* **Role:** Performance-optimized autonomous AI painter. Implements a dirty-region tracking repaint system, short-term and long-term memory structures, real-time creative feedback loops, and standalone PyQt5 GUI panels.
* **Imports/Calls:** `numpy`, `PIL.Image`, `PIL.ImageDraw`, `PyQt5.QtWidgets`, `PyQt5.QtGui`, `PyQt5.QtCore`
* **Called By:** Standalone UI executions and diagnostic scripts.
* **Hardcoded Paths:** `".zw/trixel.session"`, `".zw/tools"` (tutorial folder).
* **Safe to Move:** **Yes** (Independent optimization layer).
* **Notes:** Leverages NumPy arrays for high-performance canvas state analysis (dominant colors, center of mass, composition balance scores).

---

### [composer_abi_adapter.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/composer_abi_adapter.py)
* **File Path:** `trixelcomposer/composer_abi_adapter.py`
* **Role:** ABI facade layer. Bridges legacy or historical composer implementations safely into the `trixel_editor_action.v1` and `trixel_composer_plan.v1` schema definitions.
* **Imports/Calls:** `terminal_trixel.TerminalTrixelComposer`, `enhanced_trixel_core.EnhancedTrixelComposer`, `dataclasses`, `asyncio`, `hashlib`
* **Called By:** Authority validator or external multi-agent systems looking for standardized JSON action packages.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Strictly structural adapters).
* **Notes:** Normalizes suggestions from the `EmpireBridge` and provides PyQt/Terminal adapter classes (`TerminalTrixelComposerAdapter`, `EnhancedTrixelComposerAdapter`).

---

### [atlas_composer.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/atlas_composer.py)
* **File Path:** `trixelcomposer/atlas_composer.py`
* **Role:** Sprite compilation compiler. Stitches independent procedurally rendered terrain slices into consolidated spritesheets matching standard GIMP/LibreSprite atlas configurations.
* **Imports/Calls:** `scene_server.compile_recipe`, `terminal_trixel.RecipeRenderer`, `terminal_trixel.TerminalCanvas`, `PIL.Image`
* **Called By:** `tile_server.py` (via `compose_atlas`).
* **Hardcoded Paths:** `"assets"` (fallback local assets root), `".zw/atlases"` (atlas cache directory).
* **Safe to Move:** **Yes** (Paths determined relative to environment variables or script path).
* **Notes:** Reads UV layout guidelines from `atlas_meta.json` in the asset directory.

---

### [entity_layer.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/entity_layer.py)
* **File Path:** `trixelcomposer/entity_layer.py`
* **Role:** Entity overlay manager. Keeps semantic entity coordinate markers separate from the PNG raster canvas (to avoid baking immovable assets into pixels).
* **Imports/Calls:** `dataclasses.asdict`
* **Called By:** `terminal_trixel.py` (during `entity_marker` routing).
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure data mapping/saving module).
* **Notes:** Keeps dynamic markers aligned via `EntityMarker` schema containing `nx`, `marker_y`, and `color`.

---

### [tile_address.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/tile_address.py)
* **File Path:** `trixelcomposer/tile_address.py`
* **Role:** Spatial coordinate language. Translates 3D coordinates, outward normals, camera perspective, and visible faces into compact dot-separated addresses (e.g. `"d49.l19.f57"`).
* **Imports/Calls:** `re`, `dataclasses`
* **Called By:** Renderers, recipe selectors, and AI perception components.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure mathematical coordinate library).
* **Notes:** Defines face normals (`top`, `bottom`, `north`, `south`, `east`, `west`) and visible face descriptors (`wall`, `slope`, `edge`, `side`).

---

### [empire_bridge.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelcomposer/empire_bridge.py)
* **File Path:** `trixelcomposer/empire_bridge.py`
* **Role:** Network adapter connecting the local procedural canvas server to centralized AI gateway suggestion endpoints.
* **Imports/Calls:** `aiohttp` (optional)
* **Called By:** Autonomous painter run pipelines.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Handles non-blocking HTTP requests for design inputs.

---
---

## 2. Raster Stamp Painting Physics (`trixelworld`)

A deterministic, pure-functional biomechanical raster stamp drawing system. Samples GIMP brush dynamics, runs Inverse Kinematic curves, coordinates color context mappings, and renders spatial entities.

### [engine_mr.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/engine_mr.py)
* **File Path:** `trixelworld/engine_mr.py`
* **Role:** Pure functional drawing kernel. Stamping engine mapping brush tip geometry, dynamic pressure/velocity curves, and spacing ratios into high-fidelity SurfaceBuffers.
* **Imports/Calls:** `brush_models_mr.BrushRecipe`, `brushes.gbr_parser_mr`, `brushes.gih_parser_mr`
* **Called By:** `engine_debug_mr.py`, `world_tree_mr.py`, and diagnostic harness scripts.
* **Hardcoded Paths:** `"/usr/share/gimp/2.0/brushes"`, `"/usr/share/gimp/2.0/dynamics"` (fallback smoke-test directories only).
* **Safe to Move:** **Yes** (Pure functional design).
* **Notes:** Implements `SurfaceBuffer` (flat channel-last row-major RGBA array) and handles `StrokeEvent` metrics.

---

### [brush_models_mr.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/brush_models_mr.py)
* **File Path:** `trixelworld/brush_models_mr.py`
* **Role:** Core data structure library. Defines frozen, normalized dataclasses for brush assets (shapes, dynamics, presets, palettes, recipes) completely decoupled from GIMP parsing formats.
* **Imports/Calls:** `dataclasses`
* **Called By:** All `trixelworld` modules (core interfaces).
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure data models library).
* **Notes:** Primary classes: `BrushShapeAsset`, `ActiveCurve`, `BrushDynamicsAsset`, `BrushPresetAsset`, `PaletteAsset`, `VariantBrushBundle`, and `BrushRecipe`.

---

### [trixel_brush_adapter.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/trixel_brush_adapter.py)
* **File Path:** `trixelworld/trixel_brush_adapter.py`
* **Role:** Registry and asset adapter. Translates raw format parser outputs into normalized `brush_models_mr` assets, resolves names, manages collisions, and builds finalized `BrushRecipe` payloads.
* **Imports/Calls:** `brush_models_mr`, `brushes.vbr_parser_mr`, `brushes.gbr_parser_mr`, `brushes.gdyn_parser_mr`, `brushes.gtp_parser_mr`, `brushes.gpl_parser_mr`, `brushes.gih_parser_mr`
* **Called By:** `world_tree_mr.py`, `engine_debug_mr.py`, and test setups.
* **Hardcoded Paths:** `"data/brushes"` (fallback test path).
* **Safe to Move:** **Yes** (Robustly handles guarded dynamic imports so parsers degrade gracefully).
* **Notes:** Hosts `AssetRegistry` which aggregates and indexes shapes, dynamics, presets, and palettes.

---

### [world_tree_mr.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/world_tree_mr.py)
* **File Path:** `trixelworld/world_tree_mr.py`
* **Role:** Gfig-backed procedural tree systems. Loads vector curve scaffold paths, scales coordinates into world space, samples hidden leaf/shadow influence fields, and issues brush strokes.
* **Imports/Calls:** `surface_behavior_mr`, `trixel_recipes_mr.build`, `engine_mr.stroke_to_events`, `engine_debug_mr.stamp_blended`, `brushes.gfig_parser_mr`
* **Called By:** `trixel_demo_mr.py` (during tree demo building).
* **Hardcoded Paths:** `"gfig"` (local scaffolds directory), GIMP share candidate paths (`"/usr/share/gimp/2.0"`, `"/usr/local/share/gimp/2.0"`, `".config/GIMP/2.10"`).
* **Safe to Move:** **Yes** (Discovers Gfig and brushes root relative to `__file__`).
* **Notes:** Supports pre-built tree configurations: `TREE_OAK`, `TREE_PINE`, `TREE_BIRCH`, and `TREE_DEAD`.

---

### [trixel_recipes_mr.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/trixel_recipes_mr.py)
* **File Path:** `trixelworld/trixel_recipes_mr.py`
* **Role:** Visual outcome declarations. Expresses named drawing styles and brush intents (e.g. continuous bristle overlap, charcoal grain, soft parametric washes) as cohesive definitions.
* **Imports/Calls:** `brush_models_mr`, `trixel_brush_adapter.AssetRegistry`
* **Called By:** `world_tree_mr.py`, `trixel_demo_mr.py`.
* **Hardcoded Paths:** `"/usr/share/gimp/2.0/brushes"`, `"/usr/share/gimp/2.0/dynamics"`, `"/usr/share/gimp/2.0/palettes"` (fallback CLI tests).
* **Safe to Move:** **Yes** (Modular dictionary registration).
* **Notes:** Declares recipes: `hard_pixel`, `hatch_texture`, `charcoal_grain`, `bristle_rake`, `oil_smear`, `acrylic_variant`, `terrain_stroke`, `nebula_wash`, `brass_grain`, `scale_panel`, and `void_accent`.

---

### [palette_mr.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/palette_mr.py)
* **File Path:** `trixelworld/palette_mr.py`
* **Role:** Color selection kernel. Evaluates active color selections, gradient interpolation along color ramps, alpha blends, and topography elevation snaps.
* **Imports/Calls:** `brush_models_mr.PaletteAsset` (for type hinting only).
* **Called By:** `engine_mr.py` (color interpolation passes).
* **Hardcoded Paths:** `"/usr/share/gimp/2.0/palettes"` (fallback CLI smoke test).
* **Safe to Move:** **Yes** (Pure mathematical operations).
* **Notes:** Defines `ColourContext` container that tracks stroke state and processes: `index`, `sequential`, `gradient`, `nearest`, `elevation`, `material`, and `dynamics` color strategies.

---

### [surface_behavior_mr.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/surface_behavior_mr.py)
* **File Path:** `trixelworld/surface_behavior_mr.py`
* **Role:** Vocabulary descriptor. Declares high-level visual categories (e.g. edge characters, fill patterns, age modes, and blend preferences) mapping semantic shapes to correct rendering strategies.
* **Imports/Calls:** None (Standard library only).
* **Called By:** `world_tree_mr.py` (and future facade descriptors for terrain/buildings).
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure descriptor definitions).
* **Notes:** Pre-defines standard categories: `TREE_BARK`, `TREE_SHADOW_MASS`, `TREE_LEAF_MASS`, `TREE_CANOPY_EDGE`, `HOUSE_WALL_PLASTER`, `HOUSE_TIMBER`, `HOUSE_ROOF_SHINGLE`, `HOUSE_WEATHERING`, `WATER_DEPTH_BAND`, and `WATER_SURFACE_RIPPLE`.

---

### [atmosphere_mr.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/atmosphere_mr.py)
* **File Path:** `trixelworld/atmosphere_mr.py`
* **Role:** Atmospheric renderer. Performs math calculations for GIMP Gradient Flares (glow diameters, radial ray calculations, ghost secondaries, and additive blends) decoupled from brushes or shapes.
* **Imports/Calls:** `brush_models_mr.FlareAsset`, `brush_models_mr.GradientAsset`, `engine_mr.SurfaceBuffer`, `trixel_brush_adapter.AssetRegistry`
* **Called By:** Atmosphere composite scripts.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Decoupled rendering math).
* **Notes:** Implements GIMP GFlare composites: `render_flare_glow`, `render_flare_rays`, `render_flare_secondaries`, and `render_flare`.

---

### [brushes/ Subsystem Parsers](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld/brushes/)
* **Directory Path:** `trixelworld/brushes/`
* **Role:** Low-level GIMP asset format parsing files. Parses raw binary or text documents from standard paint catalogs.
* **Parsers:**
  * `vbr_parser_mr.py`: Parses parametric brushes (radius, spikes, hardness).
  * `gbr_parser_mr.py`: Parses GIMP binary brushes (alpha masks, spacings, dimensions).
  * `gih_parser_mr.py`: Parses image hose brushes (multi-cell variant stamps).
  * `gdyn_parser_mr.py`: Parses dynamics files (mapping pressure/random coordinates to LUTs).
  * `gtp_parser_mr.py`: Parses tool presets (snapshot states).
  * `gpl_parser_mr.py`: Parses color palette files.
  * `gfig_parser_mr.py`: Parses Gfig vector paths (tree scaffolds).
  * `gflare_parser_mr.py`: Parses flare templates.
  * `ggr_parser_mr.py`: Parses gradient color segment curves.
  * `gimpressionist_parser_mr.py`: Parses Impressionist filters.
  * `lisp_parser_mr.py`: Parses Script-Fu lisp files.
* **Called By:** `trixel_brush_adapter.py` (via protected dynamic imports).
* **Hardcoded Paths:** None (Strictly read binary buffers or file descriptors).
* **Safe to Move:** **Yes** (Compact parser files).

---

### Demonstration, Diagnostics & Stress-Test Harnesses
* **File Paths:**
  * `trixelworld/trixel_demo_mr.py`: Massive diagnostic rendering demonstration script compiling named recipes and rendering rich text/graphic patterns.
  * `trixelworld/stress_scene_mr.py`: Heavy procedural render tester generating large forests of oak/pine/birch trees to capture engine tick limits.
  * `trixelworld/demo_beach_material_sheet.py`: Standard beach terrain generator rendering sand waves and shoreline foam.
  * `trixelworld/demo_building_material_sheet.py`: Structural brick and roofing shingle layout testbed.
  * `trixelworld/demo_bestiary_fauna_sheet.py`: Procedural creature/fauna texture composite.
  * `trixelworld/demo_bestiary_flora_sheet.py`: Dense foliage and ground-flora rendering sheets.
* **Imports/Calls:** `world_tree_mr`, `trixel_brush_adapter.AssetRegistry`, `engine_mr.SurfaceBuffer`, `engine_debug_mr`
* **Called By:** CLI diagnostic harness scripts and local test setups.
* **Hardcoded Paths:** `/usr/share/gimp/2.0` (as fallback asset directory).
* **Safe to Move:** **Yes** (Self-contained test code).
* **Notes:** Writes output images locally to `/tmp/trixel_demo` or customized output folder parameters.
