ENGINALITY profile: scene performance / ZON4D expression layer.

This profile is based only on the visible ENGINALITY 25-stack files provided here: `runtime_loop.py`, `bootstrap.py`, `zon4d_kernel.py`, `performer_engine.py`, `scene_track.py`, `task_types.py`, `task_system_merged.py`, `domain_views.py`, `dialogue_engine.py`, `audio_engine.py`, and `animation_engine.py`.

## 1. PROJECT ROLE

ENGINALITY owns the performance-expression layer that turns ZON4D/runtime state into scheduled performance work.

Its core job is:

Take authoritative runtime state or incoming ZON4D deltas, hydrate that into domain views, feed those views into performer sub-engines, convert dialogue/audio/animation clips into executable performance tasks, and emit a per-tick performance schedule.

The strongest ownership chain is:

`runtime_loop.py` accepts deltas and owns TickContext, Snapshots, Delta ordering, ZON4D mutation, domain view hydration, and performance scheduling. It explicitly calls PerformerEngine at Step 11. 

`zon4d_kernel.py` owns simple dict-based ZON4D mutation, inverse delta generation, rollback support, and validation. 

`domain_views.py` owns the current loose conversion from canonical ZON4D state into `narrative_view`, `audio_view`, `animation_view`, `spatial_view`, and `ap_rules_view`. 

`performer_engine.py` owns the scene performance pass: it maintains `SceneTrack`, feeds domain views into dialogue/audio/animation engines, and gathers newly-started clips into `PerformanceTask` output. 

`scene_track.py` owns clip timing, tracks, clip layering metadata, scene time advancement, and Clip → PerformanceTask concretization. 

`dialogue_engine.py`, `audio_engine.py`, and `animation_engine.py` own loose mapping from domain views into typed Clips.   

ENGINALITY does not own Godot rendering, final art assets, final audio playback, AP moral/canon law, book ingestion, ZONJ scene extraction, performer identity canon, or full game mechanics. It produces performance tasks and state updates; another project must execute them.

Neighboring projects that likely depend on ENGINALITY:

Godot / ZW / avatar layer depends on ENGINALITY for scheduled dialogue/audio/animation/camera/fx tasks.

ZON4D / runtime kernel depends on ENGINALITY’s simple kernel only if this package is being used as the prototype runtime. In a stricter architecture, ZON4D owns canonical state and ENGINALITY only consumes deltas/views.

Narrative / scene extraction projects depend on ENGINALITY’s inbound schema to tell it which speakers, lines, intents, timings, and animation/audio cues to perform.

Audio, animation, dialogue, and performer identity systems depend on ENGINALITY to preserve timing and task identity.

AP governance depends on ENGINALITY to stop before mutating unsafe canonical state, but the current AP implementation is not real authority.

## 2. CURRENT WORKING STATUS

Confirmed working:

The stack has a complete prototype runtime path: build runtime, accept deltas, apply ZON4D mutations, generate domain views, step performer, schedule tasks, and log performance output. `bootstrap.py` wires `SimpleAnchorStore`, `SimpleAPEngine`, `SimpleZON4DKernel`, `PerformerEngine`, and `LoggingPerformanceABI` into an `EnginalityRuntime`. 

The ZON4D kernel supports `set`, `delete`, `merge`, multi-op payloads, inverse deltas, and simple validation. It has inline smoke tests for those behaviors. 

The performance harness can simulate ticks and write tick packets to `/tmp/engain_performance_tick.latest.json` and `/tmp/engain_performance_tick.{tick:04d}.json`. It creates fake domain views for dialogue, audio, and animation and passes them through `PerformerEngine`. 

The task ABI is present as `PerformanceTask` with `id`, `tick_id`, `scene_time`, `task_type`, `payload`, and `priority`. 

Partially working:

Runtime-to-performer integration exists, but it is prototype-level. `runtime_loop.py` says Step 4/5/8 are Phase 2 and skipped, with ordered deltas treated as accepted. 

Domain view generation works only for a small set of flat state keys such as `narrative/active_speaker`, `audio/music`, `audio/sfx`, `animation/rig`, and `animation/pose`. 

Dialogue, audio, and animation engines consume loose schemas and assume required fields are present. Missing required keys such as `line_id`, `speaker_id`, `asset_id`, `rig_id`, or `pose_id` will likely raise runtime errors.   

SceneTrack can schedule new clips by time window, but it does not yet resolve collisions, overlapping exclusives, repeated updates, cancellation, sync groups, voice-to-viseme enforcement, or late/missed clips. 

Untested:

Inbound real scene events are not defined as a formal contract.

Performer identities are not formalized.

Dialogue line lookup is not connected to actual text.

Audio and animation assets are not validated.

Godot execution of output tasks is not wired in this stack.

Performance ABI writes/logs tasks, but there is no stable downstream bridge contract beyond JSON-like task dictionaries.

Abandoned, legacy, or proof-only:

`task_system_merged.py` is powerful but appears separate from the runtime’s active `PerformanceTask` path. It defines a broader universal task system with `Task`, `TaskTree`, `TaskRouter`, semantic facades, and handlers, but `runtime_loop.py` and `PerformerEngine` use `PerformanceTask` from `task_types.py`, not `Task` from `task_system_merged.py`.  

`SimpleAPEngine` in `bootstrap.py` is explicitly accept-everything Phase 1, so it is proof-only and not authority-ready. 

`LoggingPerformanceABI` is a bridge stub, not the final renderer/audio executor. 

## 3. ERROR PROFILE

Import/path errors:

Most files use relative imports like `.performer_engine`, `.task_types`, `.scene_track`, and `.runtime_loop`. This requires the files to live inside a real Python package folder with an `__init__.py`, imported as `ENGINALITY.*`, not run randomly as loose scripts. `performance_harness.py` imports `.performer_engine`, so direct execution outside package context can fail. 

`runtime_loop.py` imports `PerformerEngine`, while `performer_engine.py` imports `PerformanceTask`, `SceneTrack`, `DialogueEngine`, `AudioEngine`, and `AnimationEngine`. The current files avoid a hard cycle by importing `domain_views` inside Step 10, but package structure must be correct.  

Missing files:

The code references spec names such as `RUNTIME_LOOP_v0.1`, `PERFORMER_ENGINE_v1.0`, and ABI sections, but those spec files are not part of the visible stack.

There is no formal inbound event schema file.

There is no performer identity registry.

There is no dialogue line database.

There is no animation rig/pose registry.

There is no audio asset registry.

There is no Godot bridge schema consuming `PerformanceTask`.

Duplicate files:

`task_types.py` and `task_system_merged.py` both define task concepts, but they are not the same ABI. One is a compact performance task ABI; the other is a universal authoring/execution system. This is the biggest duplicate-task risk.  

Stale backups:

No explicit backup files are visible in this 25-stack sample. However, `task_system_merged.py` says “MERGED VERSION” and “COMPREHENSIVE system,” which suggests prior systems were merged into one file. That file may be current design material, but it is not the active runtime task path. 

Schema mismatch:

`Delta.payload` accepts any shape, but `zon4d_kernel.py` only mutates known dict/list op shapes. Unknown shapes become no-ops. That is safe mechanically, but dangerous semantically because malformed inbound events can appear accepted while doing nothing. 

`domain_views.py` expects flat string keys like `narrative/active_speaker`, while the bootstrap smoke test delta uses nested list paths like `["entities", "geralt", "hp"]`. Both are supported by the kernel, but they produce different state shapes. Domain hydration only watches the flat slash-key convention.  

`task_system_merged.py` uses `TaskDomain.NARRATIVE`, `TaskDomain.AUDIO`, `TaskDomain.ANIMATION`; `task_types.py` uses `PerformanceTaskType.DIALOGUE`, `AUDIO`, `ANIMATION`, `CAMERA`, `FX`, `RENDER`. They overlap but are not identical.  

Runtime bridge mismatch:

`runtime_loop.py` calls `performance_abi.schedule_performance(tick_id, tasks)` with `PerformanceTask` objects. `performance_harness.py` writes serialized task dictionaries to `/tmp`. These are two different bridge modes: direct ABI call versus file packet.  

Godot scene/autoload mismatch:

No Godot scene or autoload files are present in this stack. ENGINALITY does not currently prove a Godot consumer exists for `/tmp/engain_performance_abi.json` or `/tmp/engain_performance_tick.latest.json`.

Generated-output drift:

`performance_harness.py` includes `domain_views` inside the output packet “for debug; remove later if too noisy.” That means output shape is not stable. 

`LoggingPerformanceABI` writes only `id`, `tick_id`, `type`, `priority`, and `payload`, omitting `scene_time`. But `PerformanceTask` requires `scene_time`. That is a real outbound schema drift.  

Old architecture still present:

`task_system_merged.py` looks like a broader universal task router waiting to replace or absorb the smaller `PerformanceTask` path. Until a single task ABI is chosen, ENGINALITY has two architectures: compact performance ABI and universal task tree/router. 

## 4. CONTRADICTION PROFILE

Contradiction against own stated role:

ENGINALITY claims to be scene performance / ZON4D expression layer, but `runtime_loop.py` owns a full authoritative runtime loop: snapshots, deltas, rollback, AP placeholder, anchor store interface, and canonical state mutation. That exceeds “expression layer” unless ENGINALITY is also the prototype runtime. 

Contradiction with another project’s role:

ZON4D kernel authority is inside ENGINALITY here. If another project is supposed to own ZON4D canon, this stack should consume ZON4D deltas/views rather than own `SimpleZON4DKernel`. 

AP authority is stubbed inside ENGINALITY, but the actual project law says AP authority must not be faked. `SimpleAPEngine` accepts everything. That is acceptable for proof-only but not authority. 

Current home/project decisions:

This stack looks like a package named `ENGINALITY`, not Godot, not avatar, not trixelcomposer, not scene API. It should stay in the performance expression lane.

File naming contradictions:

`task_system_merged.py` sounds authoritative and comprehensive, but active runtime code uses `task_types.py`.

`domain_views.py` says “Step 10” and “Step 7 Hydration” in the same header, while `runtime_loop.py` calls domain generation Step 10. That creates spec-number drift.  

Schema name contradictions:

`DialogueEngine` consumes `narrative_view`, but outputs `DIALOGUE` performance tasks.

`task_system_merged.py` calls dialogue-like tasks `NARRATIVE`, while `task_types.py` calls them `DIALOGUE`.   

Old vs new pipeline behavior:

The new compact runtime pipeline is:

Delta → ZON4D state → domain views → clips → PerformanceTasks.

The merged task system pipeline is:

TaskTree → Task → TaskRouter → handlers.

Those are different execution philosophies. They can coexist only if one becomes authoring/precompile and the other remains runtime ABI.

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

System name: ENGINALITY Performance ABI v1

Implied by:

`task_types.py` defines `PerformanceTask` and `Clip`. 

`scene_track.py` converts clips into `PerformanceTask`. 

`runtime_loop.py` defines `PerformanceABI.schedule_performance`. 

`bootstrap.py` has `LoggingPerformanceABI` as the temporary bridge. 

Missing before real:

A stable JSON schema for `PerformanceTask`.

A stable file/socket/HTTP transport.

Required inclusion of `scene_time` in every outbound packet.

Consumer acknowledgement, dropped-task behavior, retry behavior, and late-task behavior.

Godot-side task executor.

System name: Performer Identity / Rig Binding Layer

Implied by:

`dialogue_engine.py` uses `speaker_id`. 

`animation_engine.py` uses `rig_id`, `pose_id`, and `viseme_curve_id`. 

`audio_engine.py` has `voice_track_id` but does not yet consume voice events. 

Missing before real:

A performer registry mapping `speaker_id` to voice, rig, face rig, animation set, spatial anchor, and display name.

A dialogue line registry mapping `line_id` to text and optionally voice asset.

A rule for linking dialogue line → voice clip → viseme curve → facial animation.

System name: Scene Event Inbound Contract

Implied by:

`domain_views.py` currently extracts loose events from flat ZON4D state keys. 

`runtime_loop.py` accepts `domain_views` externally but also generates them from post-delta state. 

Missing before real:

Formal inbound event schema.

Required fields for scene events, performer identities, dialogue lines, animation intents, audio intents, and ZON4D deltas.

A failure contract when an inbound event references missing assets or missing identities.

System name: Universal Task Authoring + Runtime Router

Implied by:

`task_system_merged.py` defines `TaskTree`, `Task`, `TaskRouter`, `Quest`, `Behavior`, `Sequence`, `Conversation`, `Maintenance`, `Routine`, navigation, interaction, camera, and physics facades. 

Missing before real:

A bridge from `TaskTree` / `Task` to `PerformanceTask`.

A decision whether `TaskRouter` runs inside ENGINALITY or outside it.

Handlers that actually execute tasks instead of logging.

Clear priority mapping between `TaskPriority` and `PerformanceTask.priority`.

## 6. INBOUND SCHEMA

Inbound item: scene events

Source project: scene extractor / scene API / ZONJ runtime.

Expected filename or schema name: `scene_events.v1.json` or `ENGINALITY_SCENE_EVENTS_v1`.

Required fields:

`event_id`

`scene_id`

`tick_id` or `scene_time`

`event_type`

`payload`

Optional fields:

`source_id`

`temporal_scope`

`parent_ids`

`priority`

`tags`

Failure behavior if missing:

If `event_id` missing, reject event.

If `scene_id` missing, accept only if current scene already active; otherwise reject.

If timing missing, schedule at current `scene_time` but warn.

If `event_type` unknown, preserve as debug event but do not emit performance task.

Inbound item: performer identities

Source project: character registry / performer registry / canon identity system.

Expected filename or schema name: `performer_registry.v1.json`.

Required fields:

`performer_id`

`display_name`

`speaker_id`

`rig_id`

Optional fields:

`voice_id`

`face_rig_id`

`default_emotion`

`animation_profile`

`spatial_anchor`

`pronunciation_key`

Failure behavior if missing:

If `performer_id` or `speaker_id` missing, reject dialogue/animation binding.

If `rig_id` missing, allow dialogue/audio but block body/facial animation.

If `voice_id` missing, emit text dialogue task but no voice audio task.

Inbound item: dialogue lines

Source project: dialogue compiler / narrative parser / canon text registry.

Expected filename or schema name: `dialogue_lines.v1.json`.

Required fields:

`line_id`

`speaker_id`

`text`

Optional fields:

`emotion`

`intensity`

`duration`

`voice_asset_id`

`viseme_curve_id`

`conversation_id`

Failure behavior if missing:

If `line_id` missing, reject.

If `speaker_id` missing, reject or route to narrator fallback if configured.

If `text` missing but `voice_asset_id` exists, allow voice-only playback but warn.

If `duration` missing, use `DialogueEngineConfig.default_duration`, currently 2.0 seconds. 

Inbound item: animation intents

Source project: animation planner / Godot rig layer / performer identity layer.

Expected filename or schema name: `animation_intents.v1.json`.

Required fields:

`rig_id`

`pose_id` or `viseme_curve_id`

`duration`

Optional fields:

`layer`

`blend_in`

`blend_out`

`weight`

`audio_clip_id`

`offset`

Failure behavior if missing:

If `rig_id` missing, reject animation event.

If body event lacks `pose_id`, reject body clip.

If facial event lacks `viseme_curve_id`, reject facial clip.

If duration missing, engine uses 0.5 fallback in animation clip creation. 

Inbound item: audio intents

Source project: audio planner / music system / dialogue voice system.

Expected filename or schema name: `audio_intents.v1.json`.

Required fields:

`asset_id`

`channel` or event bucket: `music_events`, `sfx_events`, `voice_events`

Optional fields:

`action`

`duration`

`volume_db`

`pan`

`pitch_semitones`

`envelope`

`spatial`

Failure behavior if missing:

If `asset_id` missing, reject.

If action missing, default to `play`. 

If duration missing, music defaults to 5.0 seconds and sfx defaults to 1.0 second inside `AudioEngine`. 

Inbound item: ZON4D deltas

Source project: ZON4D kernel / AP-approved mutation stream / runtime event bridge.

Expected filename or schema name: `zon4d_delta.v1.json`.

Required fields:

`id`

`source_id`

`entity_ref`

`temporal_index`

`temporal_scope`

`parent_ids`

`payload`

Optional fields:

`metadata`

Failure behavior if missing:

`runtime_loop.py` rejects malformed deltas when `id`, `source_id`, or `entity_ref` are missing, when temporal scope is reversed, or when `parent_ids` exceeds 64. 

If payload shape is unknown, `SimpleZON4DKernel` treats it as no-op rather than rejecting. That must be changed before authority use. 

## 7. OUTBOUND SCHEMA

Outbound item: performance timeline

Destination project: Godot / ZW renderer / performance consumer.

Expected filename or schema name: `performance_timeline.v1.json`.

Required fields:

`epoch`

`tick`

`delta_time`

`scene_time`

`tasks`

Optional fields:

`domain_views`

`trace`

Current producer:

`performance_harness.py` writes tick packets with those fields to `/tmp/engain_performance_tick.latest.json` and `/tmp/engain_performance_tick.{tick:04d}.json`. 

Stability level: candidate.

Reason: debug fields are still included and marked removable.

Outbound item: dialogue execution tasks

Destination project: Godot dialogue HUD / voice system / avatar mouth system.

Expected filename or schema name: `performance_task.dialogue.v1`.

Required fields:

`id`

`tick_id`

`scene_time`

`type: dialogue`

`payload.track_id`

`payload.clip_id`

`payload.duration`

`payload.payload.line_id`

`payload.payload.speaker_id`

Optional fields:

`emotion`

`intensity`

`conversation_id`

`tags`

Stability level: candidate.

Reason: generated by `DialogueEngine` → Clip → `SceneTrack`, but no final downstream schema exists.  

Outbound item: audio tasks

Destination project: Godot audio bus / external audio engine.

Expected filename or schema name: `performance_task.audio.v1`.

Required fields:

`id`

`tick_id`

`scene_time`

`type: audio`

`payload.payload.asset_id`

`payload.payload.channel`

`payload.payload.action`

Optional fields:

`volume_db`

`pan`

`pitch_semitones`

`envelope`

`spatial`

`duration`

Stability level: candidate.

Reason: music and sfx are supported, but voice track is configured and not yet consumed from a `voice_events` schema. 

Outbound item: animation tasks

Destination project: Godot animation player / rig controller / facial animation layer.

Expected filename or schema name: `performance_task.animation.v1`.

Required fields:

`id`

`tick_id`

`scene_time`

`type: animation`

`payload.payload.rig_id`

Either `payload.payload.pose_asset_id` or `payload.payload.viseme_curve_id`

Optional fields:

`blend_in`

`blend_out`

`layer`

`weight`

`linked_audio_clip_id`

`offset`

`tags`

Stability level: candidate.

Reason: body and facial clips exist, but rig registry and downstream executor are missing. 

Outbound item: performer state updates

Destination project: performer registry / scene runtime / Godot actor state.

Expected filename or schema name: `performer_state_update.v1`.

Required fields:

`performer_id`

`scene_id`

`scene_time`

`state`

Optional fields:

`current_line_id`

`current_audio_clip_id`

`current_animation_clip_id`

`emotion`

`intensity`

`track_ids`

Stability level: unknown.

Reason: the current stack does not explicitly emit performer state updates. It emits tasks that imply performer state.

## 8. AUTHORITY BOUNDARIES

Where ENGINALITY must stop and ask another project:

It must ask AP/canon authority before treating `SimpleAPEngine` decisions as real. The current AP engine accepts everything. 

It must ask ZON4D authority before changing the canonical state schema. Right now it mutates dicts using loose paths.

It must ask performer identity authority before inventing `speaker_id`, `rig_id`, voice assets, or viseme curves.

It must ask dialogue/narrative authority before inventing line text for `line_id`.

It must ask Godot/render authority before deciding final task execution format, autoload names, scene node paths, or animation player structure.

It must ask audio authority before finalizing channel names, bus names, spatial audio fields, or voice event behavior.

Where other projects must stop and ask ENGINALITY:

Other projects must ask ENGINALITY before changing `PerformanceTask` shape.

Other projects must ask ENGINALITY before changing timing rules for scene ticks, scene time, clip start windows, or task priority.

Other projects must ask ENGINALITY before renaming `narrative_view`, `audio_view`, or `animation_view`.

Other projects must ask ENGINALITY before treating `TaskTree`/`TaskRouter` as the active runtime path. That is not currently the same as `PerformanceTask`.

Other projects must ask ENGINALITY before feeding inbound deltas that expect nested state to hydrate into domain views, because `domain_views.py` currently mostly watches flat slash-key state.

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Is ENGINALITY allowed to own a prototype runtime loop, or should it only consume already-approved ZON4D state/views?

2. Is `task_types.py` the real runtime ABI, or should `task_system_merged.py` become the master task model?

3. Should `TaskTree` be treated as authoring/precompile only, with `PerformanceTask` as the only runtime output?

4. What is the official inbound scene event schema?

5. What is the official performer identity schema mapping speaker → rig → voice → face rig?

6. Should ZON4D state use flat slash keys like `narrative/active_speaker`, nested dict paths like `["narrative", "active_speaker"]`, or both?

7. Should unknown ZON4D delta payloads be no-ops, warnings, rejects, or breaches?

8. What is the exact outbound transport to Godot: file JSON, HTTP, WebSocket, stdin/stdout, or engine plugin?

9. How should dialogue, voice audio, and viseme animation synchronize? One task group? Separate tasks with shared sync id? Clip dependency graph?

10. What should happen when a clip starts before the current window, arrives late, overlaps an exclusive clip, or references a missing asset?

## 10. STACK VERDICT

Verdict: AUTHORITY_WITH_FIX_FLAGS.

Why:

ENGINALITY is more than proof-only because the core mechanical path exists: runtime tick, delta application, domain hydration, performer pass, scene track, clips, and performance task output are all present and wired. `bootstrap.py` can build a runtime, `performance_harness.py` can produce tick packets, and the sub-engines can generate dialogue/audio/animation clips.   

But it is not `AUTHORITY_READY`.

The fix flags are serious:

`SimpleAPEngine` accepts everything.

`task_types.py` and `task_system_merged.py` are competing task models.

Inbound event schema is missing.

Performer identity schema is missing.

Dialogue/audio/animation assets are not validated.

`LoggingPerformanceABI` omits `scene_time`, even though `PerformanceTask` owns it.

Godot execution bridge is not present in this stack.

Domain hydration uses loose flat state keys and does not enforce a stable ZON4D contract.

So the clean verdict is:

`AUTHORITY_WITH_FIX_FLAGS`

ENGINALITY can be trusted as the candidate scene performance / ZON4D expression layer, but only after task ABI consolidation, inbound schema creation, performer identity binding, and downstream Godot/audio/animation bridge contracts are locked.
