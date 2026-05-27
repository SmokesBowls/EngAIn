# ZW Protocol & Mechanimation Dependency Map

This document establishes the structural roles, calling patterns, and paths for the visual-semantic subsystems under `godotroot/` (Godot simulation client) and `mechanimation/` (rig locomotion physics).

---

## 1. Godot Client Simulation Layer (`godotroot`)

Core environment, interface, and AI director subsystems active in `godotroot/zonjrender/`.

### [TrixelTileClient.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/autoload/TrixelTileClient.gd)
* **File Path:** `godotroot/zonjrender/autoload/TrixelTileClient.gd`
* **Role:** Fetches procedurally generated terrain tile images from the local `trixel_composer` tile server (port 8766), loads and caches them as `ImageTextures`, and overrides materials on active MeshInstance3D nodes in the scene.
* **Imports/Calls:** `HTTPRequest`, `JSON`, `Image`, `ImageTexture`
* **Called By:** Connected to by `SemanticRenderer` to apply dynamic terrain/effect layers on top of base atlases.
* **Hardcoded Paths:** `http://127.0.0.1:8766/tile` (HTTP URL)
* **Safe to Move:** **Yes** (Standard Autoload script; requires updating the Autoload registry in `project.godot`).
* **Notes:** Features recently added print logging prefix `[TRIXEL_CLIENT]` for `_ready`, `enrich_terrain_meshes`, and `_on_tile_done`.

---

### [SemanticRenderer.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/SemanticRenderer.gd)
* **File Path:** `godotroot/zonjrender/scripts/SemanticRenderer.gd`
* **Role:** Coordinates dynamic 3D terrain grid building and rendering at runtime. Connects with `TrixelEnvironmentPlanner` and `TrixelRoleResolver` to load custom atlases, generate standard QuadMeshes/MeshInstance3Ds, map coordinate bounds, and handle physics raycasting for tile clicks.
* **Imports/Calls:** `@tool`, `TrixelEnvironmentPlanner.resolve_tile_alias`, `TrixelRoleResolver.resolve_role`, `StandardMaterial3D`, `QuadMesh`, `StaticBody3D`, `CollisionShape3D`, `BoxShape3D`
* **Called By:** Root scene editor hint and runtime nodes.
* **Hardcoded Paths:** `res://trixel/trixelassets`
* **Safe to Move:** **Later** (Relies on localized `res://trixel/trixelassets` directory structure and unified alias planners; best moved together with the environment system).
* **Notes:** Implements full cell click handlers that interactively morph tiles to `sand` for real-time testing.

---

### [Main.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/Main.gd)
* **File Path:** `godotroot/zonjrender/scripts/Main.gd`
* **Role:** High-level controller script for loading and spawning entity scenes from JSON files (e.g., `walk_intent.json` / chapters). Handles cleanups of active children nodes and maps rendering configurations.
* **Imports/Calls:** `res://entities/TrixelEntity3D.tscn` (preload), `res://scenes/DragonAvatar3D.tscn` (scene reference path)
* **Called By:** Root node initialization.
* **Hardcoded Paths:** `res://entities/TrixelEntity3D.tscn`, `res://scenes/DragonAvatar3D.tscn`, `res://`
* **Safe to Move:** **Yes** (Standalone level orchestrator).
* **Notes:** Standard entrypoint logic; can spawn default dragon avatars if no custom JSON plans are defined.

---

### [EngAInBridge.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/EngAInBridge.gd)
* **File Path:** `godotroot/zonjrender/scripts/EngAInBridge.gd`
* **Role:** Real-time AI Co-Director local bridge. Emits decision signals, tracks player stats/recent actions/narrative threads, and handles file-system based asynchronous messaging with EngAInOS/AP authority models.
* **Imports/Calls:** `Timer`, `Time`, `FileAccess`, `JSON`, `DirAccess`
* **Called By:** Attached to `DragonAvatar3D` or parent controller nodes.
* **Hardcoded Paths:** `res://engain_request.json`, `engain_response.json` (active files polled in root)
* **Safe to Move:** **Later** (Hardcoded to look in local directory/project paths for exchange files; moving may decouple it from active Python co-director watcher pathways).
* **Notes:** Uses a `Timer` checking every 100ms for incoming co-director decisions from python.

---

### [SnapshotManager.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/SnapshotManager.gd)
* **File Path:** `godotroot/zonjrender/scripts/SnapshotManager.gd`
* **Role:** Persistent visual snapshot logger for ZW protocol audits. Periodically takes viewport screenshots, builds formatted metadata JSON containing active state variables (entropy, dream depth, scene path), and handles storage quota cleanups.
* **Imports/Calls:** `class_name SnapshotManager`, `Viewport`, `Time`, `FileAccess`, `DirAccess`, `ProjectSettings`
* **Called By:** Event triggers from `EventBus` and `EngAInDragon`.
* **Hardcoded Paths:** `res://snapshots/`, `snapshots/` (local relative)
* **Safe to Move:** **Yes** (Self-contained and decoupled utility).
* **Notes:** Handles critical retention times based on priority and cleans up storage when limits are exceeded.

---

### [dynamiccontextmanager.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/dynamiccontextmanager.gd)
* **File Path:** `godotroot/zonjrender/scripts/dynamiccontextmanager.gd`
* **Role:** Dynamic context parser. Monitors and polls the latest generated visual snapshot files, extracts structural context descriptions (location, environment, active interface panels), and replaces static templates with real visual indicators.
* **Imports/Calls:** `class_name DynamicContextManager`, `SnapshotManager`, `Time`, `FileAccess`, `DirAccess`, `JSON`
* **Called By:** Connected as a sibling/child of the main orchestrators.
* **Hardcoded Paths:** `snapshots/` (local path)
* **Safe to Move:** **Yes** (Standard parser node).
* **Notes:** Auto-updates context from visuals every 30s.

---

### [EventBus.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/EventBus.gd)
* **File Path:** `godotroot/zonjrender/scripts/EventBus.gd`
* **Role:** Global event broker defining signals for temporal collapses, Mandela locks, paradoxes, dream state corruptions, and ZW packets.
* **Imports/Calls:** `Node`
* **Called By:** Connected globally throughout the project.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure signal bus).
* **Notes:** Core communications artery.

---

### [TerrainChunkBuilder.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/TerrainChunkBuilder.gd)
* **File Path:** `godotroot/zonjrender/scripts/TerrainChunkBuilder.gd`
* **Role:** Pure stateless factory class. Reads terrain chunk data and bakes them using `SurfaceTool` with autotiling adjacency logic.
* **Imports/Calls:** `class_name TerrainChunkBuilder`, `SurfaceTool`, `Mesh`, `MeshInstance3D`, `StandardMaterial3D`, `FileAccess`, `JSON`
* **Called By:** Local loaders.
* **Hardcoded Paths:** `res://engain/tests/trixel/assets`
* **Safe to Move:** **Yes** (Decoupled helper class).
* **Notes:** No network hooks, `add_child` calls, or editor-dependent operations.

---

### [ControlHUD.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/ControlHUD.gd)
* **File Path:** `godotroot/zonjrender/scripts/ControlHUD.gd`
* **Role:** Coordinates screen UI input (CommandLine submissions) and prints RichText console logs for co-director events.
* **Imports/Calls:** `CanvasLayer`, `RichTextLabel`, `LineEdit`, `Button`
* **Called By:** Main HUD canvas overlay.
* **Hardcoded Paths:** `../../World/DragonAvatar3D/EngAInBridge` (export path)
* **Safe to Move:** **Yes** (Standard UI layer).
* **Notes:** Maps colors and prefixes to different kinds of messages (user, dragon, lore, sys, err).

---

### [DragonAvatar3D.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/DragonAvatar3D.gd)
* **File Path:** `godotroot/zonjrender/scripts/DragonAvatar3D.gd`
* **Role:** Local visual movement controller for the 3D dragon sprite. Handles smooth sine-based orbiting/bobbing, and triggers color modulates when signals arrive.
* **Imports/Calls:** `@tool`, `AnimatedSprite3D`, `Tween`
* **Called By:** Visual dragon nodes.
* **Hardcoded Paths:** `EngAInBridge`, `AnimatedSprite3D` (export node paths)
* **Safe to Move:** **Yes** (Follows parent local space).
* **Notes:** Standard cosmetic rig follower.

---

### [EntitySpawner.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/EntitySpawner.gd)
* **File Path:** `godotroot/zonjrender/scripts/EntitySpawner.gd`
* **Role:** Pure factory class parsing spawn command configurations to return MeshInstance3D capsules with auto-generated names/billboards.
* **Imports/Calls:** `class_name EntitySpawner`, `MeshInstance3D`, `CapsuleMesh`, `StandardMaterial3D`, `Label3D`
* **Called By:** Scene loaders.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Stateless helper).
* **Notes:** No scene-tree dependencies.

---

### [EngAInBridge3D.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/EngAInBridge3D.gd)
* **File Path:** `godotroot/zonjrender/scripts/EngAInBridge3D.gd`
* **Role:** visual character movement (move_and_slide) and fallback animation selection for the dragon sprite.
* **Imports/Calls:** `CharacterBody3D`, `AnimatedSprite3D`
* **Called By:** Spawning script layers.
* **Hardcoded Paths:** `../AnimatedSprite3D`
* **Safe to Move:** **Yes**
* **Notes:** Decoupled rig control script.

---

### [EngAInDragon.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/EngAInDragon.gd)
* **File Path:** `godotroot/zonjrender/scripts/EngAInDragon.gd`
* **Role:** 2D CharacterBody2D character representing the EngAInDragon that moves in a flight loop, handles UI submissions, formats output for speech, calls `/engain` at `http://localhost:5000/engain` via `HTTPRequest`, and coordinates with `EngAInBridge.gd` and `SnapshotManager.gd`.
* **Imports/Calls:** `CharacterBody2D`, `AnimatedSprite2D`, `Label`, `LineEdit`, `SnapshotManager`, `HTTPRequest`, `HTTPClient`, `JSON`, `Timer`
* **Called By:** Spawned scenes.
* **Hardcoded Paths:** `http://localhost:5000/engain` (HTTP endpoint)
* **Safe to Move:** **Later** (Relies on several sibling path expectations like `../LineEdit`, `../SnapshotManager`, `EngAInBridge`, `../EngAInBridge`).
* **Notes:** Coordinates rate-limited F12 manual snapshots and F11 debug states.

---

### [VisionAgent.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scenes/VisionAgent.py)
* **File Path:** `godotroot/zonjrender/scenes/VisionAgent.py`
* **Role:** Python visual assistant backend. Checks local paths for game screenshots and runs them through OpenAI/Claude/Gemini APIs or local CLIP/LLaVA instances to return a descriptive markdown summary of current layout status.
* **Imports/Calls:** `base64`, `json`, `requests`, `PIL.Image`, `os`, `time`
* **Called By:** `zw_file_bridge.py`
* **Hardcoded Paths:** `snapshots/` (screenshots directory)
* **Safe to Move:** **Later** (Coupled closely with `snapshots/` folder paths).
* **Notes:** Includes default descriptors for the specialized cosmic control panel and layout.

---

### [zw_file_bridge.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scenes/zw_file_bridge.py)
* **File Path:** `godotroot/zonjrender/scenes/zw_file_bridge.py`
* **Role:** File bridge watcher daemon. Loops continuously checking for `godot_command.txt`, uses `VisionAgent` to enrich the context with local screenshots, runs a symbolic and narrative agent mapping, and outputs replies to `python_response.json`.
* **Imports/Calls:** `os`, `time`, `json`, `VisionAgent.VisualZWBridge`, `VisionAgent.VisionAgent`
* **Called By:** Independent background terminal processes.
* **Hardcoded Paths:** `godot_command.txt`, `python_response.json`, `snapshots/`
* **Safe to Move:** **No** (Directly relies on relative paths to interact with Godot's text exchanges).
* **Notes:** Core communication bridge between python LLM processes and running client instances.

---

### [SemanticRendererEditor.gd](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/scripts/SemanticRendererEditor.gd)
* **File Path:** `godotroot/zonjrender/scripts/SemanticRendererEditor.gd`
* **Role:** Extensive Editor plugin (@tool) allowing developers to build, view, and test autotiling grids directly from the inspector interface, using undo-redo APIs.
* **Imports/Calls:** `EditorPlugin`, `SurfaceTool`, `StandardMaterial3D`, `MeshInstance3D`, `Label3D`, `Camera3D`, `JSON`, `FileAccess`
* **Called By:** Editor UI.
* **Hardcoded Paths:** `res://engain/tests/trixel/assets`, `res://entities/TrixelEntity3D.tscn`
* **Safe to Move:** **Later** (Coupled to editor plugins).
* **Notes:** Highly useful for visual prototyping of atlas pieces.

---
---

## 2. Rig Locomotion Pipeline (`mechanimation`)

A modular biomechanical animation pipeline to proceduralize walking paths via Inverse Kinematics, compile sprite frames into spritesheet structures, and export skeletal linkages.

### [primeanim_v4a.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mechanimation/primeanim_v4a.py)
* **File Path:** `mechanimation/primeanim_v4a.py`
* **Role:** Pipeline orchestrator (v0.5.2). Loads rig JSONs, performs easing interpolation on keyframes, integrates the locomotion preset layers, renders layered PNG assemblies in correct z-orders, and generates joint-mask assets.
* **Imports/Calls:** `json`, `math`, `argparse`, `PIL.Image`, `PIL.ImageDraw`, `yaml`, `biomechanical_constraints_fixed`
* **Called By:** Terminal CLI scripts.
* **Hardcoded Paths:** `engine_target.yml` (relative to script path)
* **Safe to Move:** **Yes** (Strictly parameter-driven, though expects presets/constraints sibling files).
* **Notes:** Generates an additional `_mask.png` visual joint overlay indicating joint pivots.

---

### [biomechanical_constraints_fixed.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mechanimation/biomechanical_constraints_fixed.py)
* **File Path:** `mechanimation/biomechanical_constraints_fixed.py`
* **Role:** Dynamic biomechanical physics solver (v0.5.2). Calculates phase state cycles (STANCE, LIFT, PASS) for walking, applies pelvis bob heights, arm counters swings, solve leg trigonometry (solve_ik), and runs foreshortened shin corrections.
* **Imports/Calls:** `math`, `pathlib.Path`, `PIL.Image` (within length functions)
* **Called By:** `primeanim_v4a.py`, `pose_editor.py`, `pose_studio.py`
* **Hardcoded Paths:** None (Extracts lengths organically from image sizes).
* **Safe to Move:** **Yes** (Self-contained IK/phase solver class).
* **Notes:** Houses the core presets configuration registry (`BIOMECH_PRESETS`).

---

### [trixel_bridge.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mechanimation/trixel_bridge.py)
* **File Path:** `mechanimation/trixel_bridge.py`
* **Role:** AI Enhancement post-processing link. Passes the generated spritesheets and joint masks to TrixelComposer CLI utilities to reconstruct seams and blend layers.
* **Imports/Calls:** `sys`, `json`, `pathlib.Path`, `terminal_trixel` (TrixelComposer)
* **Called By:** Post-render CLI builders.
* **Hardcoded Paths:** `trixel_composer/trixelcomposer-main` (relative to script path)
* **Safe to Move:** **Later** (Uses hardcoded nested relative paths for the `trixel_composer` vendor dependencies).
* **Notes:** Ready to link with `terminal_trixel.py` once mask inpainting is active.

---

### [pose_editor.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mechanimation/pose_editor.py)
* **File Path:** `mechanimation/pose_editor.py`
* **Role:** Interactive Tkinter control panel allowing developers to pose character rigs, select walking velocities/presets, slide keyframes, and save configuration plans.
* **Imports/Calls:** `tkinter`, `json`, `math`, `PIL.Image`, `PIL.ImageTk`, `primeanim_v4a`, `biomechanical_constraints_fixed`
* **Called By:** Local execution.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Tkinter application).
* **Notes:** Integrates all spinbox sliders and live canvas views.

---

### [pose_studio.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mechanimation/pose_studio.py)
* **File Path:** `mechanimation/pose_studio.py`
* **Role:** Large, high-end production-grade studio utility with custom industrial-dark styling, play/pause controls, hotkey mappings, frame strip displays, skeleton links, and automation bakers.
* **Imports/Calls:** `tkinter`, `json`, `math`, `sys`, `PIL.Image`, `PIL.ImageTk`, `PIL.ImageDraw`, `primeanim_v4a`, `biomechanical_constraints_fixed`
* **Called By:** Standalone execution.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Standalone studio tool).
* **Notes:** High quality Amber-on-Steel aesthetic (`#131318`).
