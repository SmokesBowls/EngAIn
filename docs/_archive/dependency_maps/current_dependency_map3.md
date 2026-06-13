# ENGINALITY & Mechanimation Dependency Map

This document establishes the structural roles, calling patterns, and paths for the authoritative animation scheduler under `ENGINALITY/` and the rig locomotion physics pipeline under `mechanimation/`.

---

## 1. Authoritative Performance & Tick Scheduler (`ENGINALITY`)

Manages the core simulation loop, evaluates temporal deltas, handles state rollbacks, and schedules dialogue, audio, and animation tasks on the scene tracks.

### [runtime_loop.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/runtime_loop.py)
* **File Path:** `ENGINALITY/runtime_loop.py`
* **Role:** Core engine loop orchestrator (v0.1). Initializes engine ticks, ingests/orders incoming temporal Deltas, computes inverse deltas for state rollbacks (fast vs slow paths), validates ZON4D state, hydrates domain views, and invokes the PerformerEngine.
* **Imports/Calls:** `performer_engine.PerformerEngine`, `task_types.PerformanceTask`, `time`
* **Called By:** Test harness runs and external execution scripts.
* **Hardcoded Paths:** None (Strictly memory and parameter-driven).
* **Safe to Move:** **Yes** (Stateless loop scheduler relying on interface Protocols).
* **Notes:** Defines critical interfaces like `AnchorStore`, `APEngine`, `ZON4DKernel`, and `PerformanceABI`.

---

### [performer_engine.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/performer_engine.py)
* **File Path:** `ENGINALITY/performer_engine.py`
* **Role:** Performance orchestrator. Maintains the unified `SceneTrack`, feeds domain views (dialogue, audio, animation) to their respective sub-engines, and gathers newly-started PerformanceTasks.
* **Imports/Calls:** `scene_track.SceneTrack`, `dialogue_engine.DialogueEngine`, `audio_engine.AudioEngine`, `animation_engine.AnimationEngine`, `task_types.PerformanceTask`
* **Called By:** `runtime_loop.py` (during Step 11: Performance Pass Scheduling).
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure middleware orchestrator).
* **Notes:** Decoupled config structure (`PerformerEngineConfig`).

---

### [dialogue_engine.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/dialogue_engine.py)
* **File Path:** `ENGINALITY/dialogue_engine.py`
* **Role:** Sub-engine mapping high-level narrative dialogue views into concrete timeline Dialogue `Clips` placed on the SceneTrack.
* **Imports/Calls:** `scene_track.SceneTrack`, `task_types.Clip`, `task_types.ClipType`
* **Called By:** `performer_engine.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Resolves speech timers and tracks viseme triggers.

---

### [audio_engine.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/audio_engine.py)
* **File Path:** `ENGINALITY/audio_engine.py`
* **Role:** Sub-engine mapping incoming audio views into concrete Music and SFX `Clips` placed on the SceneTrack.
* **Imports/Calls:** `scene_track.SceneTrack`, `task_types.Clip`, `task_types.ClipType`
* **Called By:** `performer_engine.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Manages mixing bus volumes and asset ids.

---

### [animation_engine.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/animation_engine.py)
* **File Path:** `ENGINALITY/animation_engine.py`
* **Role:** Sub-engine mapping body/facial events into concrete rig animation `Clips` placed on the SceneTrack.
* **Imports/Calls:** `scene_track.SceneTrack`, `task_types.Clip`, `task_types.ClipType`
* **Called By:** `performer_engine.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Manages rig pose blending weights, viseme curves, and layering.

---

### [scene_track.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/scene_track.py)
* **File Path:** `ENGINALITY/scene_track.py`
* **Role:** Timeline manager. Maintains standard and additive Tracks, advance time indexes, and converts newly-started Clips in time windows into concrete `PerformanceTask` ABI execution units.
* **Imports/Calls:** `task_types.Clip`, `task_types.ClipType`, `task_types.PerformanceTask`, `task_types.PerformanceTaskType`
* **Called By:** `performer_engine.py`, `dialogue_engine.py`, `audio_engine.py`, `animation_engine.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Stateless temporal organizer).
* **Notes:** Contains the core Clip-to-Task concretization layer.

---

### [domain_views.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/domain_views.py)
* **File Path:** `ENGINALITY/domain_views.py`
* **Role:** State hydrator. Transforms the raw ZON4D state dict into specialized domain view structures (narrative, audio, animation, spatial) ready to be scheduled by sub-engines.
* **Imports/Calls:** None (Pure state translation functions).
* **Called By:** `runtime_loop.py` (during Step 10: Domain View Generation).
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure data mapping function).
* **Notes:** Serves as the critical integration link between database state and performer scheduling.

---

### [task_types.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/task_types.py)
* **File Path:** `ENGINALITY/task_types.py`
* **Role:** Data structures definitions. Declares the core enums and schemas for `Clip`, `ClipType`, `PerformanceTask`, and `PerformanceTaskType`.
* **Imports/Calls:** `Enum`, `dataclass`
* **Called By:** All ENGINALITY subsystems.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure types library).
* **Notes:** Aligns with standard Performer Engine ABI definitions.

---

### [performance_harness.py](file:///home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/ENGINALITY/performance_harness.py)
* **File Path:** `ENGINALITY/performance_harness.py`
* **Role:** Diagnostic test environment. Feeds mock tick states to the performer subsystems and prints generated task logs.
* **Imports/Calls:** `performer_engine.PerformerEngine`, `performer_engine.PerformerEngineConfig`
* **Called By:** Hand-run developer checks.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes** (Pure test sandbox).
* **Notes:** Evaluates viseme timings and sfx task priorities.

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
