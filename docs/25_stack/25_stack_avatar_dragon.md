## engain_avatar project awareness profile

Project: `engain_avatar`
Lane: `2D dragon/avatar shell`

This profile treats `engain_avatar` as the local Godot 2D dragon face, input shell, EventBus surface, snapshot/context helper, and file-bridge client. It does not treat it as the whole EngAIn runtime, the canonical world simulator, the 3D renderer, the trixel compositor, or the lore authority.

The stack is real and useful, but it is not clean authority yet. The strongest proof is that the README defines the intended Godot ↔ file bridge ↔ Python AI director architecture, with SnapshotManager and DynamicContextManager as support systems. It also says the expected setup is `engain_dolphin.py`, `EngAInBridge.gd`, `EngAInDragon.gd`, `SnapshotManager.gd`, and `DynamicContextManager.gd`. 

---

## 1. PROJECT ROLE

`engain_avatar` owns the visible 2D dragon/avatar shell. Its job is to show the dragon, accept user command text through the Godot UI, capture visual/context snapshots, pass command/state JSON outward, receive AI/co-director response JSON inward, and speak/display the result through the dragon.

It owns these local pieces:

`EngAInDragon.tscn` as the 2D scene shell.

`EngAInDragon.gd` as the dragon/player input controller.

`EngAInBridge.gd` as the Godot-side JSON bridge to the Python co-director.

`EventBus.gd` as the local signal surface/autoload event channel.

`SnapshotManager.gd` as the visual/event snapshot recorder.

`dynamiccontextmanager.gd` as the local context updater from snapshot metadata.

`idle_flap.png` and `idol_flap.png` as 2D dragon animation cargo.

It explicitly does not own the final AI mind, canonical story authority, Python runtime authority, 3D world authority, trixel rendering, scene ingestion, AP mutation authority, or cross-project schema governance. The Python side is an adjacent runtime. The README describes the system as Godot 4 ↔ File Bridge ↔ Python EngAIn AI Director, not Godot alone. 

Neighboring projects that depend on it are the Python AI director lane, any local co-director runtime that produces `engain_response.json`, the snapshot/vision lane that consumes `snapshots/`, and the broader EngAIn shell that needs a user-facing dragon interface.

---

## 2. CURRENT WORKING STATUS

Confirmed working, based on the stack and prior run evidence: the 2D scene opens, the dragon is visible, the input node exists, the bridge node exists, the SnapshotManager and DynamicContextManager nodes exist, and the EventBus autoload is configured. The scene is not theoretical.

Confirmed structurally working: the bridge design is JSON file exchange. The README’s data flow says player input goes from Godot into command plus visual snapshot, then context building, AI analysis, decision execution, and memory storage. 

Partially working: AI response handling. `EngAInBridge.gd` is aligned with `engain_dolphin.py` through `engain_request.json` and `engain_response.json`; `engain_dolphin.py` reads `engain_request.json`, processes `player_input` plus `game_state`, and writes `engain_response.json`. 

Partially working: visual context. The stack has SnapshotManager and a Python `VisionAgent`, and the README explicitly lists screenshot capture and visual analysis tracking as intended features.  But the actual vision layer still has placeholder behavior: it can describe interfaces, but it is not a real local vision model yet.

Untested or not proven in this 25-stack: real Ollama availability, real Dolphin-Mistral model presence, real end-to-end timing under Godot, durability of snapshot purging, DynamicContextManager feeding the bridge automatically, and EventBus being used consistently by all nodes.

Abandoned, legacy, or proof-only: `zw_file_bridge.py` is a competing/older bridge path. It waits for `godot_command.txt` and writes `python_response.json`, while the active co-director bridge uses `engain_request.json` and `engain_response.json`.  This is the biggest proof-only/legacy split.

---

## 3. ERROR PROFILE

Import/path errors: `zw_file_bridge.py` imports `VisualZWBridge` and `VisionAgent` from `VisionAgent.py`; that will work only if Python is launched from the folder containing both files or if the folder is on `PYTHONPATH`.  `engain_dolphin.py` requires `requests`, SQLite, and an Ollama server at localhost. 

Missing files: `EngAInDragon.tscn` references a background or generated texture under `res://assets/generation-6d2a77ce-fe3b-4b62-a899-c9d4c258d1f7(2).png`. That file was not part of the visible mounted cargo list. If it is absent in the real repo, Godot will show a missing texture warning or load error. The dragon flap PNGs are present, so the core avatar can still survive.

Duplicate files: there are two bridge names: `EngAInBridge.gd` and `engainbridge.gd`. The lowercase `engainbridge.gd` is only `extends Node`, so it is probably a stale stub. The real bridge is `EngAInBridge.gd`.

Stale backups: `zw_file_bridge.py` appears stale relative to `engain_dolphin.py`. It has its own symbolic/narrative mini-agent, its own command file names, and its own output schema. 

Schema mismatch: active bridge expects Python response fields like `narrative_response`, `action_type`, `state_changes`, `director_analysis`, `reasoning`, `entropy_impact`, and `timestamp`; `engain_dolphin.py` produces those fields.  But `zw_file_bridge.py` produces `narrative`, `world_state`, `visual_analysis_used`, and `timestamp`, which does not match the active Godot bridge. 

Runtime bridge mismatch: `EngAInDragon.gd` still contains an HTTP path assumption to `http://localhost:5000/engain` in one function, while the declared active bridge path is JSON file exchange. That HTTP function looks leftover or unused. The README identifies file bridge JSON exchange as the technical architecture. 

Godot scene/autoload mismatch: `project.godot` autoloads EventBus, but most bridge flow does not appear to require EventBus to send commands. EventBus is present, but the real command path is direct node call into `EngAInBridge.gd`.

Generated-output drift: the current scene has “cosmic command center” placeholder language deeply embedded in Python fallback and bridge context. That is useful for proof, but it can drift from real EngAIn story/world state unless the canonical runtime replaces it.

Old architecture still present: `zw_engine_plugin.gd` is a minimal editor plugin stub. `animated_sprite_2d.gd` is also a minimal stub. These are harmless, but they are cargo until a real plugin or sprite controller contract exists.

---

## 4. CONTRADICTION PROFILE

The biggest contradiction is between the two file bridge protocols.

Active lane:

Godot writes `engain_request.json`.

Python `engain_dolphin.py` reads it.

Python writes `engain_response.json`.

Godot reads `engain_response.json`.

Legacy/proof lane:

Python `zw_file_bridge.py` waits for `godot_command.txt`.

It writes `python_response.json`.

It returns `narrative`, not `narrative_response`. 

That means `zw_file_bridge.py` cannot be treated as the active bridge unless Godot is changed to match it.

Second contradiction: README says add `EngAInBridge` as a child of the scene root, but the actual scene places `EngAInBridge` as a child of `CharacterBody2D`. The dragon script compensates with multiple possible node paths, so this is survivable, but it is not clean.

Third contradiction: `DynamicContextManager` says it replaces static templates, but the bridge and fallback systems still hard-code “Cosmic Command Center,” “RealityManipulator,” entropy dials, TimelineAnchor, MandelaLock, and cosmic interface language. 

Fourth contradiction: README describes real AI direction with local LLM, memory, and screenshot analysis, but `VisionAgent.py` still marks local and cloud vision implementation as TODO/placeholder. So the claim is architecturally intended, not fully implemented.

Fifth contradiction: file naming varies: `EngAInBridge.gd`, `engainbridge.gd`, `EngAInDragon.gd`, `engain_dolphin.py`, `zw_file_bridge.py`. This makes it too easy for another agent to wire the wrong file.

---

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

Proposed system name: `EngAIn Avatar Co-Director Bridge v1`.

Files that imply it: `README.TXT`, `EngAInBridge.gd`, `EngAInDragon.gd`, `engain_dolphin.py`, `SnapshotManager.gd`, `dynamiccontextmanager.gd`, `VisionAgent.py`.

What exists: file-based JSON bridge, dragon UI shell, snapshot capture design, AI director prompt, SQLite memory tables, local Ollama client, and a response schema. `engain_dolphin.py` defines the co-director as a local Ollama-backed decision system with memory and a structured game-state dataclass. 

What is missing before it becomes real authority: one canonical bridge schema file, one canonical bridge filename pair, EventBus integration rules, real vision model or explicit “placeholder vision” label, snapshot retention tests, Godot headless smoke test, and a contract saying which project owns command interpretation versus display.

Proposed system name: `Avatar Visual Context Loop`.

Files that imply it: `SnapshotManager.gd`, `dynamiccontextmanager.gd`, `VisionAgent.py`, `zw_file_bridge.py`, README visual context tracking section.

What is missing: a guaranteed metadata schema for snapshots, a direct feed from DynamicContextManager into EngAInBridge request payload, a proven screenshot path visible to both Godot and Python, and actual image analysis beyond placeholder descriptions.

Proposed system name: `EventBus Avatar ABI`.

Files that imply it: `EventBus.gd`, `project.godot`, `SnapshotManager.gd`, `EngAInBridge.gd`, `EngAInDragon.gd`.

What is missing: a stable event list, payload schemas per signal, and proof that the bridge emits and listens through EventBus instead of bypassing it with direct node references.

---

## 6. INBOUND SCHEMA

Inbound item: user command text.
Source project: Godot UI / player input.
Expected filename or schema name: direct `LineEdit.text_submitted` into `EngAInDragon.gd`, then `send_to_engain(player_input, additional_context)`.
Required fields: `player_input: String`.
Optional fields: `additional_context: Dictionary`, recent visual stats, command event name.
Failure behavior if missing: dragon should not send empty commands; fallback response may trigger if bridge is unavailable.

Inbound item: JSON bridge messages from Python AI director.
Source project: Python co-director runtime.
Expected filename or schema name: `engain_response.json`.
Required fields: `narrative_response`, `action_type`, `state_changes`, `director_analysis`, `reasoning`, `entropy_impact`, `timestamp`.
Optional fields: extra state payloads, debug metadata, memory IDs.
Failure behavior if missing: Godot waits until timeout, then dragon uses fallback response. README lists “AI timeout - used fallback response” as a known issue when Python is not receiving requests or Ollama is not responding. 

Inbound item: snapshot/context updates.
Source project: SnapshotManager / DynamicContextManager.
Expected filename or schema name: `snapshots/*.json` metadata and `snapshots/*.png`.
Required fields: event type, timestamp, visual analysis/description, image path or metadata path.
Optional fields: priority, scene path, command, state, storage stats.
Failure behavior if missing: visual context disabled; command bridge can still run with text-only context.

Inbound item: AI co-director response.
Source project: `engain_dolphin.py`.
Expected schema name: `EngAInDirectorDecision`.
Required fields before formatting: `analysis`, `recommended_action`, `narrative_response`, `state_modifications`, `reasoning`, `entropy_impact`. The prompt in `engain_dolphin.py` explicitly asks the model to return this JSON structure. 
Optional fields: extended world changes, character changes, confidence, memory reference.
Failure behavior if missing: `engain_dolphin.py` fills missing required fields or falls back to a safe decision. 

---

## 7. OUTBOUND SCHEMA

Outbound item: avatar display state.
Destination project: Godot scene/UI.
Expected filename or schema name: local node state, not currently a file.
Required fields: dragon speech text, animation state, entropy effect, input placeholder state.
Optional fields: facial expression, animation mood, visual effect type, speech history.
Stability level: candidate.

Outbound item: command JSON.
Destination project: Python co-director runtime.
Expected filename or schema name: `engain_request.json`.
Required fields: `player_input`, `game_state`, `timestamp`, `request_id`.
Optional fields: `additional_context`, snapshot stats, recent visual events.
Stability level: stable candidate, because `engain_dolphin.py` already consumes `player_input` and `game_state`. 

Outbound item: snapshots.
Destination project: Python vision/context lane.
Expected filename or schema name: `snapshots/<base>.png` and `snapshots/<base>.json`.
Required fields: image path, metadata path, timestamp, event type, scene info.
Optional fields: visual analysis, priority, ZW packet, state payload.
Stability level: candidate.

Outbound item: context packets.
Destination project: Python AI director / DynamicContextManager consumers.
Expected filename or schema name: `current_context` dictionary or request `additional_context`.
Required fields: `visual_description`, `location`, `environment`, `timestamp`.
Optional fields: source snapshot, confidence, scene path, event type.
Stability level: unknown/candidate.

Outbound item: EventBus messages.
Destination project: local Godot systems.
Expected filename or schema name: Godot signals.
Required fields: signal name plus dictionary payload.
Optional fields: timestamp, source node, severity, event type.
Stability level: unknown, because EventBus exists but is not yet the sole command backbone.

---

## 8. AUTHORITY BOUNDARIES

`engain_avatar` must stop and ask the Python AI director when a player command needs narrative interpretation, state mutation, entropy decision, character relationship update, or co-director reasoning.

It must stop and ask the canonical runtime/world project before claiming a location, entity list, quest state, scene ID, combat state, or lore truth.

It must stop and ask the 3D/trixel lanes before producing geometry, tiles, terrain, spatial maps, or 3D world state.

It must stop and ask AP/governance before mutating authoritative canon, player progression, world flags, or irreversible state.

Other projects must stop and ask `engain_avatar` before changing the Godot node layout, renaming `EngAInBridge`, changing the request/response filenames used by the avatar shell, changing snapshot folder layout, replacing dragon assets, or redefining the avatar input/output behavior.

---

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Is `EngAInBridge.gd` plus `engain_dolphin.py` the official bridge, and should `zw_file_bridge.py` be retired or quarantined?

2. Should the canonical file pair be `engain_request.json` / `engain_response.json`, with `godot_command.txt` / `python_response.json` marked legacy?

3. Should `EngAInBridge` live under `CharacterBody2D` as the scene currently does, or under the scene root as README says?

4. Is `EventBus` required for all avatar messages, or is it only optional local signaling?

5. Should `DynamicContextManager` feed context directly into `EngAInBridge.gd`, or should Python read snapshot metadata itself?

6. Is `VisionAgent.py` allowed to remain placeholder, or must it be replaced with a real local vision model before authority?

7. Should the “Cosmic Command Center” placeholder language remain in this avatar shell, or move to a demo profile?

8. Is the missing/generated background asset required, or should it be removed from the scene to avoid asset cargo?

9. Should lowercase `engainbridge.gd`, `animated_sprite_2d.gd`, and `zw_engine_plugin.gd` be marked cargo/stub/legacy?

10. What is the official outbound avatar state schema: plain speech text only, or speech plus animation, mood, entropy effect, and snapshot reference?

---

## 10. STACK VERDICT

Verdict: `AUTHORITY_WITH_FIX_FLAGS`.

Reason: `engain_avatar` is real enough to own the 2D dragon/avatar shell. It has a working Godot scene, visible dragon lane, bridge node, input UI, snapshot/context managers, and a clear JSON co-director architecture. The README and Python runtime agree on the main direction: Godot sends player input and game state, Python analyzes with local LLM/memory, and Godot receives a decision response. 

But it cannot be `AUTHORITY_READY` until the bridge split is resolved. The active bridge and the old ZW file bridge use different filenames and different response fields.  The vision system is also still candidate/placeholder, and EventBus is present but not yet the enforced backbone.

Clean stack card:

```text
engain_avatar
Status: AUTHORITY_WITH_FIX_FLAGS
Role: 2D dragon/avatar shell; Godot input/display; local JSON bridge client; snapshot/context support; EventBus surface.
Owns: EngAInDragon.tscn, EngAInDragon.gd, EngAInBridge.gd, EventBus.gd, SnapshotManager.gd, dynamiccontextmanager.gd, 2D dragon assets.
Does not own: canonical AI mind, lore truth, 3D world, trixel render, AP authority, scene ingestion, final schema governance.
Main fix flags:
1. Retire or quarantine zw_file_bridge.py unless converted to engain_request/engain_response.
2. Delete or label lowercase engainbridge.gd as stub.
3. Choose one EngAInBridge node path.
4. Define EventBus payload schema.
5. Define snapshot metadata schema.
6. Replace or label placeholder vision.
7. Remove old/missing generated asset cargo.
```

Final taste: this is not a wrong merge. It is a working 2D avatar lane with some old bridge cargo still riding in the trunk.
