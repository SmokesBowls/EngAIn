# Project Proposal: Mechanics-First Game Engine with Scene-Based Narrative and Asset Pipeline  
*(Revised to match project specifics)*

## 1. Overview / Vision

We are building a game engine that treats **mechanics as the skeleton**, with art and narrative as pluggable layers. The engine’s primary responsibility is to maintain a **canonical live world state** (positions, behaviors, quest states) that can be rendered by multiple symmetric clients (Godot, UPBGE) and edited through a unified interface. The source of truth for story and assets is an **Obsidian vault** (narrative) and a **Blender/Trixel pipeline** (art), while the runtime sim server holds the **live state and drafts**. This architecture enables:

- **Playable before pretty**: Mechanics are testable from day one with placeholders.
- **Iterative world‑building**: Scenes can be built in isolation, then connected.
- **Pluggable art**: Any entity can be skinned via GLB, Trixel sprites, or user uploads without changing game logic.
- **Editable narrative**: Dialogue and quest steps are stored as data, editable in‑game and committable back to the vault.

The first concrete milestone is a **Beach Scene MVP** that proves the loop: load a scene, see entities with behaviors, move a player, talk to an NPC, edit a line of dialogue, save, and reload.

## 2. Core Principles

- **Mechanics First** – Every feature must work with placeholders (capsules, labels, void) before any art is added.
- **Two‑Tier Truth** – The **vault** is the canonical source of authored content (scenes, dialogue, quests). The **runtime** is the canonical source of live state (transforms, visibility, quest flags, draft edits). A *commit* operation pushes draft changes back to the vault.
- **Scene as Unit** – Everything is organized around scenes (locations). Each scene has a spec that defines its environment, entity roster, zones, behaviors, and exits.
- **Data‑Driven Narrative** – Dialogue and quests are stored as structured data (not code), referenced by IDs, and editable without recompilation.
- **Asset Agnostic** – The engine only cares about `skin_id`; the actual mesh/texture can come from any pipeline (Blender, Trixel, user upload). Users can override `skin_id` per entity or globally.
- **Save/Reload Loop** – The editor (Godot) can save runtime state (draft) and optionally commit it to the vault (canon).

## 3. System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Obsidian      │     │  Blender/Trixel │     │   User Uploads  │
│   (Narrative    │────▶│   (Asset Gen)   │────▶│   (Custom Art)  │
│    Source)      │     │                 │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ (scene spec)           │ (skin_id → asset)    │ (skin_id override)
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Python Runtime (sim_runtime.py)            │
│                          (listens on :8080)                      │
│  • Maintains entity list, transforms, behaviors, quest state    │
│  • Publishes /snapshot (envelope + payload)                     │
│  • Publishes /transforms                                         │
│  • Accepts /command (move, spawn, edit, talk)                   │
│  • Loads scene spec from vault or draft                         │
└──────────────┬────────────────────────────────┬─────────────────┘
               │                                │
               │ (poll transforms)               │ (poll snapshot)
               ▼                                ▼
┌─────────────────────────┐          ┌─────────────────────────┐
│        Godot            │          │         UPBGE           │
│  • Primary editor       │          │  • Alternate renderer   │
│  • Free‑move player     │          │  • Asset authoring view │
│  • Manual move commands │          │  • Blender integration  │
│  • Render modes (void,  │          │                         │
│    labels, primitives,  │          │                         │
│    skins)               │          │                         │
└─────────────────────────┘          └─────────────────────────┘
```

**Data Flow Summary**  
- The **vault** provides the canonical scene spec (environment, entity archetypes, zones, dialogue).
- The **runtime** loads a scene spec, instantiates entities, and runs behaviors. It serves state via HTTP endpoints, wrapping responses in a consistent envelope:
  ```json
  {
    "protocol": "zonjrender-sim",
    "version": "1.0",
    "payload": { "scene_id": "...", "bridge_entities": [...], ... }
  }
  ```
- **Godot** and **UPBGE** poll the runtime and render entities according to their skin mappings and presence state (renderers only draw entities with presence ∈ `{visible, active}` unless in debug mode). They also send player input and edit commands back to the runtime.
- **Asset pipeline** produces assets keyed by `skin_id`. The runtime only stores the `skin_id`; renderers resolve it to a mesh.

## 4. Data Models

### 4.1 Scene Spec (JSON/YAML)

```yaml
scene_id: "scene.04_the_convergence"   # canonical scene identifier
environment:
  biome: "beach_coast"
  preset: "beach_coast_v0"      # built‑in placeholder
  override_asset: null          # user can supply path
  regions:                      # named areas for behavior
    - id: "shoreline"
      polygon: [[0,0], [20,0], [20,10], [0,10]]
      tags: ["sand", "walkable"]
    - id: "tree_line"
      polygon: [[15,5], [25,5], [25,15], [15,15]]
      tags: ["trees", "cover"]
    - id: "pier"
      polygon: [[5,-5], [15,-5], [15,0], [5,0]]
      tags: ["structure"]

entities:
  - entity_id: "player"
    archetype: "human"
    role: "player"
    spawn_zone: "shoreline"
    behavior: "free_move"
    skin_id: "capsule_blue"
    tags: ["player"]
    importance: 100   # always visible
    presence: "active"

  - entity_id: "neph_001"
    archetype: "nephoretti"
    spawn_zone: "shoreline"
    behavior: "wander"
    behavior_params:
      zone_id: "shoreline"
      speed: 1.2
      pause_range: [2,5]
    skin_id: "neph_default"
    tags: ["crowd"]
    importance: 10
    presence: "visible"

  - entity_id: "giant_elder"
    archetype: "giant"
    spawn_zone: "tree_line"
    behavior: "patrol"
    behavior_params:
      path: [[17,8], [20,10], [23,8]]
      loop: true
      speed: 0.8
    skin_id: "giant_elder"
    presence: "hidden"          # hidden until trigger
    reveal_trigger: "enter_zone tree_line"
    tags: ["quest_npc"]
    importance: 90

  # ... additional Nephoretti entries

exits:
  - id: "exit_to_trail"
    position: [25,5]
    target_scene: "scene.05_the_trail"
    target_exit: "entry_from_beach"
    label: "Path to Trail"
```

### 4.2 Entity Runtime Representation

The runtime maintains for each entity:

- `entity_id`
- `transform` (position, rotation)
- `archetype`
- `skin_id`
- `presence` (planned, hidden, visible, active)
- `tags` (list)
- `importance`
- `behavior_state` (current path index, etc.)
- `dialogue_state` (if interactive)

### 4.3 Dialogue Data

Dialogue is stored as nodes, referenced by ID:

```yaml
dialogue_id: "giant_elder_greeting"
nodes:
  - id: "start"
    text: "Welcome, child. The tide brings you here."
    choices:
      - text: "Who are you?"
        next: "who"
      - text: "I'm looking for someone."
        next: "look"
  - id: "who"
    text: "I am Elder Korath, guardian of this shore."
    choices:
      - text: "Tell me about the Nephoretti."
        next: "neph"
      - text: "Farewell."
        next: "end"
  - id: "neph"
    text: "They are my children, playing in the surf."
    choices:
      - text: "I see. Goodbye."
        next: "end"
  - id: "end"
    text: "May the waves guide you."
    end: true
```

### 4.4 Quest Steps

```yaml
quest_id: "beach_intro"
steps:
  - id: "step1"
    description: "Talk to Elder Korath"
    trigger: "dialogue_end giant_elder_greeting"
    next: "step2"
  - id: "step2"
    description: "Go to the pier"
    trigger: "enter_zone pier"
    next: "step3"
  - id: "step3"
    description: "Find the hidden shell"
    objective: "collect item shell_001"
    reward: "key_pier"
```

### 4.5 Zone Triggers

Triggers are simple conditions evaluated by the runtime:

- `enter_zone <zone_id>`
- `dialogue_end <dialogue_id>`
- `item_collected <item_id>`
- `timer <seconds>`
- `world_var <name> <op> <value>`

## 5. Beach Scene MVP (Minimal Viable Product)

The goal of the MVP is to prove the entire pipeline with minimal art and content. It must be **playable, editable, and savable**.

### 5.1 Requirements

- **Scene loads** from a spec (hardcoded or from vault) with a beach environment (sand plane, water plane, tree placeholders).
- **Entity roster** includes:
  - Player (free‑move, capsule)
  - 10 Nephoretti (wandering capsules, cyan)
  - 1 Giant (hidden, patrols a path, red capsule when revealed)
- **Behaviors**:
  - Nephoretti wander in shoreline zone.
  - Giant patrols a simple path in tree zone, initially hidden.
- **Interaction**:
  - Press 'E' near Giant → dialogue UI appears with 2‑3 lines.
  - Dialogue lines are editable in‑game (overlay) and persist in runtime draft.
- **Player movement** with ground collision (entity collision optional for MVP; can be added later).
- **Exit marker** (visual placeholder) that does nothing yet.
- **Render modes** toggleable: Void (black), Labels (names only), Primitives (capsules), Skins (if any).
- **Save/Reload**:
  - Save current transforms, dialogue overrides, visibility to a draft file.
  - Reload from draft to continue editing.
- **All without external assets** – everything works with engine‑built placeholders.

### 5.2 MVP Checklist

- [ ] Python runtime (`sim_runtime.py`) can parse a scene spec and instantiate entities.
- [ ] Runtime runs simple behaviors (wander, patrol) and updates transforms.
- [ ] Runtime exposes:
  - `GET /snapshot` → envelope with payload containing scene_id, bridge_entities, environment, exits.
  - `GET /transforms` → mapping of entity_id → {pos, rot}.
  - `POST /command` → accepts `move_entity`, `edit_dialogue`, `spawn_entity`, `save_draft`, etc.
- [ ] Godot polls runtime, renders capsules with labels (color‑coded by archetype). Uses presence field to decide visibility.
- [ ] Godot implements free‑move player (WASD) and sends player transform to runtime via `/command move_entity`.
- [ ] Godot implements interaction raycast and dialogue UI.
- [ ] Dialogue UI allows in‑place text editing and saves override to runtime (`/command edit_dialogue`).
- [ ] Runtime stores dialogue overrides and serves them in snapshot.
- [ ] Exit marker is a visible object that can be clicked (logs message).
- [ ] Save/load runtime state to/from disk (`/command save_draft`, `/command load_draft`).
- [ ] Toggle render modes via UI keys (F1‑F4).

## 6. Development Phases

### Phase 0: Foundation (2‑4 weeks)
- Set up Python runtime server with basic HTTP endpoints.
- Implement `/snapshot` and `/transforms` (static data for now).
- Build Godot client that polls and displays primitives.
- Establish communication protocol (JSON over HTTP) with envelope format.

### Phase 1: Beach MVP (4‑6 weeks)
- Implement scene spec parser (JSON).
- Add behavior engine (wander, patrol) with simple time‑based ticks.
- Add player movement and transform updates via `/command move_entity`.
- Add dialogue system and in‑game editing.
- Add save/load draft.
- Add render modes.
- Test with beach scene (`scene.04_the_convergence`).

### Phase 2: Scene Transitions (2‑3 weeks)
- Implement exits in spec.
- Runtime handles scene switch (load new spec, preserve player state).
- Godot fades/loads new environment.

### Phase 3: Asset Integration (ongoing)
- Implement skin resolution in Godot: map `skin_id` to GLB or sprite.
- Add upload endpoint to runtime to register new skins and mint entities.
- Integrate Trixel output format.

### Phase 4: Quest System (4‑6 weeks)
- Add quest step tracking to runtime.
- Add trigger evaluation (enter zone, collect, etc.).
- Extend dialogue to trigger quest updates.
- Add quest log UI in Godot.

### Phase 5: Full Production
- Connect Obsidian vault as source of truth (export scene specs).
- Polish editor features (drag entities, property panels).
- Scale to large crowds with LOD and visibility budgeting.

## 7. Technical Specifications (API Contracts)

### 7.1 Runtime Endpoints

- `GET /snapshot` – returns full scene state in an envelope:
  ```json
  {
    "protocol": "zonjrender-sim",
    "version": "1.0",
    "payload": {
      "scene_id": "scene.04_the_convergence",
      "environment": { "biome": "beach_coast", "preset": "beach_coast_v0" },
      "bridge_entities": [
        { "id": "player", "archetype": "human", "skin_id": "capsule_blue",
          "presence": "active", "tags": ["player"], "importance": 100,
          "dialogue_state": null },
        ...
      ],
      "exits": [ { "id": "exit_to_trail", "position": [25,5], "label": "to trail" } ]
    }
  }
  ```
- `GET /transforms` – returns position/orientation for all entities:
  ```json
  { "player": { "pos": [1.2, 0, 3.4], "rot": [0, 0, 0] }, ... }
  ```
- `POST /command` – accepts actions:
  ```json
  { "command": "move_entity", "entity_id": "player", "pos": [2,0,4] }
  { "command": "edit_dialogue", "entity_id": "giant_elder", "node_id": "start", "new_text": "..." }
  { "command": "spawn_entity", "archetype": "nephoretti", "pos": [10,0,10], "skin_id": "..." }
  { "command": "save_draft", "path": "user://scene_draft.json" }
  { "command": "load_draft", "path": "user://scene_draft.json" }
  ```

### 7.2 Scene Spec Format (Vault Export)

See 4.1. Initially, the spec can be a simple JSON file loaded by the runtime. Later, it will be generated from Obsidian notes.

### 7.3 Skin Mapping

Renderers maintain a dictionary:
```
skin_id → { type: "glb"|"sprite"|"capsule", path: "res://skins/..." }
```
Built‑in fallbacks:
- `capsule_blue`, `capsule_red`, `capsule_cyan`, etc.
- `label_only` (in labels mode)

Users can override `skin_id` for any entity via runtime command or by providing an asset with a matching ID.

## 8. Conclusion

This proposal outlines a sustainable, mechanics‑first approach to building a game engine that separates state, rendering, and content. The Beach Scene MVP is the first critical milestone—it proves the loop and establishes a factory for producing scenes. Subsequent phases add transitions, quests, and full asset integration, all while keeping the core principles intact.

By following this plan, we ensure that every new feature is testable with placeholders, that art and narrative can be developed in parallel, and that the final game remains editable and extensible long after release.
“This project builds a mechanics-first scene engine where the simulation runtime is the canonical live state and renderers are interchangeable views. Scenes are authored as data specs, playable immediately with placeholders, and progressively upgraded via skin pipelines and editable narrative/quest graphs. The Beach Scene MVP proves the complete loop: load, simulate, render, interact, edit, save, reload.”
