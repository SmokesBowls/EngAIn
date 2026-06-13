Mechanimation profile — pose, rig, walk-cycle, and biomechanical sprite animation authority.

1. PROJECT ROLE

Mechanimation owns the 2D segmented-body animation lane. Its authority is: loading a character rig, applying pose transforms, interpolating animation keyframes, applying biomechanical constraints, rendering layered sprite output, saving authored frame packages, and exporting spritesheets with metadata.

Its core engine role is split across several files. `primeanim_v4a.py` is described as the renderer/orchestrator: it loads rigs, interpolates keyframes, applies biomechanical constraints, handles z-order/layering, and outputs spritesheets. `biomechanical_constraints_fixed.py` is the physics/IK layer: thigh/shin IK, walk phase logic, pelvis bob, foreshortened shin logic, and arm swing. `pose_studio.py` is the human-facing editor layer with per-frame authored pose storage, frame strip, package save/load, and sheet+metadata export.  

Mechanimation does not own character identity, story/canon identity, semantic terrain, book parsing, Godot runtime behavior, TrixelComposer inpainting internals, or final game-scene placement. It can render a body, but it should not decide who the character is, what the story says, or how Godot should interpret the sprite once exported.

Neighboring projects depending on Mechanimation: TrixelComposer depends on Mechanimation for raw spritesheet and joint mask input; Godot/avatar/render lanes would depend on Mechanimation for final sprite sheets, frame metadata, and body-motion contracts; character/asset-authority lanes depend on it for rig validation feedback but not identity decisions.

2. CURRENT WORKING STATUS

Confirmed working: the renderer pipeline is real. The map says `primeanim_v4a.py` renders layered spritesheets, `biomechanical_constraints_fixed.py` applies IK/walk phases/pelvis bob, and project config exists. The same map lists multiple successful terminal renders and debug outputs. 

Confirmed working in Pose Studio: it has a real frame store. `pose_studio.py` declares `frames_data` as the independent per-frame authored pose store, separate from procedural pose, temporary overrides, and current locked transforms.  It also has import/export frame, load/save package, bake-to-anim, biomech toggle, joint overlay, and export sheet+metadata controls. 

Partially working: package I/O and sheet metadata are implemented enough to save authored frames into `frames/0001.pose.json` style files and write an `anim.json` manifest.  Sheet export collects frame index, sheet coordinates, bounding boxes, authored flags, and joint positions. 

Untested or not fully trusted: autonomous walk generation. The biomech layer has IK and phase logic, but the current files still show hard assumptions about `STANCE`, `LIFT`, `PASS`, sine-based swing arcs, `ground_y`, `foot_travel`, and pelvis bob. Those assumptions may not match the manually authored walk frames yet. 

Abandoned / legacy / proof-only: `pose_editor.py` is older than `pose_studio.py`. It has a single editor model using `base_pose`, `override_pose`, and `saved_pose`, not the stronger per-frame `frames_data` package model.   The older `version 2 mechanimation.txt` concept is historical/spec evidence rather than current authority. Exported PNG/GIF proof files prove rendering happened, but they are not source authority.

3. ERROR PROFILE

Import/path errors: high risk. `pose_studio.py` exits if `primeanim_v4a.py` or `biomechanical_constraints_fixed.py` is not beside it.  `trixel_bridge.py` inserts `trixel_composer/trixelcomposer-main` into `sys.path` and exits if `terminal_trixel.py` is not found. 

Missing files: joint mask generation is still a known gap. The architecture map says `trixel_bridge.py` requires a mask, but `primeanim_v4a.py` does not generate one yet. 

Duplicate files: there are at least two editor generations: `pose_editor.py` and `pose_studio.py`. `pose_studio.py` should be treated as current because it contains per-frame store, package I/O, strip indicators, and sheet metadata. `pose_editor.py` is useful historical evidence, not current authority.  

Stale backups / legacy drift: the architecture map calls `primeanim_v4a.py` v0.4.5 while the constraint engine is v0.5.2, creating version drift between renderer and physics. 

Schema mismatch: character rig v1 uses `socket`; character v2.1 biomech rig uses `attach` and `joint_type`. That is a real schema split.   If a loader expects `attach`, v1 may fail or attach incorrectly. If a tool expects `socket`, v2 may be misread.

Runtime bridge mismatch: `trixel_bridge.py` says it sends spritesheet plus joint mask to Trixel, but it also states `terminal_trixel.py` does not yet have `inpaint_with_mask`; the bridge is “ready” but not actually doing inpainting. 

Godot scene/autoload mismatch: not Mechanimation’s lane. Mechanimation should export body-motion data and rendered sheets. Godot must own scene import, autoloads, sprite playback, and runtime triggering.

Generated-output drift: high risk. Files like `walk_final_verification.png`, `walk_projective_v052.gif`, and many `walk_*.png` renders are proof artifacts. They do not override `rig.json`, `pose.json`, `anim.json`, or `sheet.json`.

Old architecture still present: yes. The stack still contains older spec/history, older editor, renderer/physics version mismatch, and proof-output artifacts beside source files.

4. CONTRADICTION PROFILE

Contradiction with own role: Mechanimation claims biomechanical authority, but the current architecture still depends on Trixel for joint inpainting and seam correction. That means Mechanimation owns pose/rig/body motion, not final polished body-pixel continuity.

Contradiction with neighboring project role: `trixel_bridge.py` reaches toward TrixelComposer by importing `terminal_trixel.py`, but `engine_target.yml` says `cross_surface.allow: []`, meaning cross-surface communication is currently restricted.  This makes the bridge a proposed edge, not a fully authorized production path.

Contradiction in current home/project decisions: `engine_target.yml` shown in the stack references `/home/burdens/Downloads/EngAIn/mechanimation/`, while your wider project rule says not to use Downloads. Treat that path as historical/current-evidence path, not desired canonical future home. 

File naming contradiction: `anim.json` is not an animation clip; it is a package manifest with `mechanimation_package`, `rig`, `anim`, `total_frames`, `fps`, and `frame_index`.  That name can confuse package authority with motion authority.

Schema name contradiction: v1 rig says `"name": "character_v1"` and uses `socket`; v2.1 rig says `"Character v2.1 Biomechanical Rig"` and uses `attach` plus `joint_type`.   No uploaded file proves a v3 source authority. So `character_v3` is suspected drift only, not confirmed authority in this 25-stack.

Old vs new pipeline behavior: older `pose_editor.py` stores overrides globally. New `pose_studio.py` stores authored frame data per frame.   The new architecture wins.

5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

The proposed system is: “Mechanimation body-motion package plus AI seam enhancement pipeline.”

Files implying it: `pose_studio.py`, `trixel_bridge.py`, `mechanimation_architectual_map.txt`, `3_step.sheet.json`, `anim.json`, and `biomechanical_constraints_fixed.py`.

What exists: a frame-backed Pose Studio, package save/load, authored pose JSON frames, sheet metadata with joint coordinates, rig definitions, biomech constraints, and bridge stub.

What is missing before it becomes real: joint mask generation, stable package schema naming, official body-motion contract, v1/v2 rig adapter or migration, Trixel inpainting method, A/B validation between manual poses and generated biomech, and a clear rule that PNG/GIF outputs are proof artifacts only.

6. INBOUND SCHEMA

Inbound item: character identity.
Source project: character/canon/avatar authority.
Expected filename/schema: `character.identity.json` or equivalent.
Required fields: `character_id`, `display_name`, `asset_family`, `body_type`, `canonical_parts_profile`.
Optional fields: style tags, faction, costume variant, scale, palette.
Failure behavior: Mechanimation may use placeholder identity but must not claim canon identity.

Inbound item: motion intent.
Source project: animation planner, gameplay, or human Pose Studio.
Expected filename/schema: `walk_intent.anim.json`, `idle.anim.json`, or `motion_intent.anim.json`.
Required fields: `name`, `duration`, `fps`, `keyframes`, each keyframe with `time` and `poses`. Current examples use `duration`, `fps`, and keyframes with `poses`. 
Optional fields: labels, loop flag, biomech preset, phase tags such as `contact`, `down`, `passing`, `up`.
Failure behavior: render static/empty pose or reject with schema error; do not invent gait phase authority.

Inbound item: body part assets.
Source project: asset generator / Trixel / human art lane.
Expected filename/schema: `assets/<character>/parts/*.png`.
Required fields: actual image files named by rig entries: torso, head, hip, limbs, wrists, hands, feet. Rig files reference images by name. 
Optional fields: masks, alternates, damaged/costume variants.
Failure behavior: invisible part warning or render failure; do not silently substitute body anatomy.

Inbound item: rig definition.
Source project: rig authority / Mechanimation itself after human approval.
Expected filename/schema: `character.biomech.rig.json`.
Required fields: `name`, `version`, `parts_dir`, `hierarchy`, `image`, `pivot`, child attach/socket data. v2.1 adds `joint_type`. 
Optional fields: `render_order`, constraints, mirror map, aliases.
Failure behavior: block biomech render if v1/v2 schema not adapted.

Inbound item: animation request.
Source project: Godot, gameplay, user, or animation planner.
Expected filename/schema: `animation_request.json`.
Required fields: `character_id`, `motion_name`, `frame_count`, `fps`, `camera_angle`, `output_type`.
Optional fields: emotion, intensity, loop, biomech preset, export package path, proof request.
Failure behavior: create candidate output only; no authority-ready export.

7. OUTBOUND SCHEMA

Outbound item: pose JSON.
Destination project: Pose Studio, package loader, future motion planner.
Expected filename/schema: `frames/0001.pose.json`.
Required fields: part names with transform values: `rotation`, `translate_x`, `translate_y`. Current pose files follow that structure. 
Optional fields: authored flag, phase label, lock/pin info, source method.
Stability level: candidate.

Outbound item: anim JSON.
Destination project: renderer, Pose Studio, Godot importer.
Expected filename/schema: `idle.anim.json`, `walk_intent.anim.json`, `walk_test.anim.json`.
Required fields: `name`, `duration`, `fps`, `keyframes`, `time`, `poses`. 
Optional fields: `description`, `loops`, labels, biomech preset.
Stability level: candidate.

Outbound item: rig JSON.
Destination project: renderer, Pose Studio, rig validator.
Expected filename/schema: `character.biomech.rig.json`.
Required fields: `name`, `version`, `parts_dir`, `hierarchy`, `image`, `pivot`, `attach`, `joint_type`. 
Optional fields: render order, mirror map, constraint metadata.
Stability level: candidate; v1 is legacy.

Outbound item: proof spritesheet/GIF.
Destination project: human review, Godot visual import, QA.
Expected filename/schema: `walk_final_verification.png`, `walk_projective_v052.gif`, `*_spritesheet.png`.
Required fields: image only.
Optional fields: matching `.sheet.json`.
Stability level: proof-only. PNG/GIF is evidence, not authority.

Outbound item: sheet metadata.
Destination project: Godot importer, QA automation, Trixel mask generator.
Expected filename/schema: `<sheet>.sheet.json`.
Required fields: `mechanimation_sheet`, `sheet_file`, `total_frames`, `cols`, `rows`, `frame_w`, `frame_h`, `fps`, `frames`; each frame has `frame`, `sheet_x`, `sheet_y`, `bbox`, `authored`, and `joints`. 
Optional fields: root/origin aliases, body bounds, contact foot, phase label, validation hash.
Stability level: candidate leaning stable.

Outbound item: body motion contract.
Destination project: Godot/gameplay/semantic runtime.
Expected filename/schema: `body_motion.contract.json`.
Required fields: `character_id`, `rig_version`, `motion_name`, `fps`, `frame_count`, `loop`, `phase_map`, `contact_map`, `sheet_file`, `sheet_meta_file`.
Optional fields: emotion, speed, gait class, camera angle, biomech preset.
Stability level: not yet built / candidate-only.

8. AUTHORITY BOUNDARIES

Mechanimation must stop and ask another project when character identity is unknown, when lore/canon changes body meaning, when Godot needs scene/autoload/runtime behavior, when Trixel must inpaint joints, when asset generation changes the body parts, or when a generated gait conflicts with human-authored pose truth.

Other projects must stop and ask Mechanimation when they need part names, pivot/attach points, rig schema, pose transforms, frame timing, sheet coordinates, body joint coordinates, contact-phase labels, or validation of whether a PNG/GIF matches the source pose data.

9. TOP 10 QUESTIONS FOR HUMAN REVIEW

10. Is `character.biomech.rig.json` v2.1 the current canonical rig, and is v1 officially legacy?

11. Is there a real `character_v3` source file outside this stack, or is “v3” just suspected drift?

12. Should rig schema standardize on `attach` and `joint_type`, with `socket` only supported by migration?

13. Is `pose_studio.py` now the only active editor, with `pose_editor.py` archived?

14. Should `anim.json` be renamed to `package.anim.json` or `mechanimation.package.json` to avoid confusing package manifest with motion clip?

15. Which file is the source of truth for walk motion: `walk_intent.anim.json`, authored `frames/*.pose.json`, or baked output?

16. Should autonomous biomech generate only candidate breakdowns, while human-authored poses remain higher authority?

17. What is the official phase model: 3-step, 4-key walk, 12-frame walk, or semantic phase labels like contact/down/pass/up?

18. Should Trixel bridge be allowed despite `cross_surface.allow: []`, or must engine target be updated first?

19. What must be present before Godot can consume a Mechanimation export: PNG only, PNG+sheet JSON, package folder, or body motion contract?

20. STACK VERDICT

AUTHORITY_WITH_FIX_FLAGS.

Mechanimation is not proof-only anymore. It has a real renderer, real biomech layer, real Pose Studio, real per-frame authored state, real package I/O, and real sheet metadata. The files support its authority over pose, rig, walk-cycle, and biomechanical sprite animation.

But it is not clean AUTHORITY_READY yet because the stack still has fix flags: v1/v2 rig schema drift, no confirmed v3 authority, renderer/physics version mismatch, old editor still present, joint mask generator missing, Trixel bridge not actually wired to inpainting, `cross_surface.allow: []` versus bridge intent, package naming ambiguity, and generated PNG/GIF proof files sitting close enough to source files to cause authority confusion.

The clean authority rule should be:

Source authority: rig JSON, pose JSON, anim JSON, package manifest, sheet metadata.

Proof authority: PNG/GIF renders only prove a render happened.

External authority: Trixel owns seam inpainting; Godot owns runtime playback; canon/avatar lanes own character identity.

Mechanimation owns the body moving.
