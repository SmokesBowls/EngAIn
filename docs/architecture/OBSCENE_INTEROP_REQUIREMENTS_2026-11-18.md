# EngAIn ↔ Ob-Scene future interoperability requirements

Recorded: 2026-11-18. Status: requirements and open conflicts only. **Ob-Scene integration is not authorized.** Do not refactor Semantic, Ob-Scene, or the existing Ob-Scene Godot adapter for this purpose.

## Intent

Ob-Scene (`/mnt/data-drive/ob-scene-workspace`) is planned as an interactive edition of the actual book, read in Obsidian. From the prose a reader can request an environment preview, launch gameplay, resume a save slot, and open linked entities and their rendered assets. EngAIn is built first; Ob-Scene connects once EngAIn can reliably load a chapter's environment and launch a scene.

Scene views (owner direction, 2026-11-18): one Mettaext scene output, consumed whole by three views — a static showcase (each item, weapon, player, NPC rendered alone; per-player variants), an environment walkthrough (level, dialogue, decoration only; no items, quests, timers, mechanics), and the game (the scene loaded as if from a save). Renders and environments pull from assets only. No separate path that dismantles scenes.

Sources: `/home/mytruelove/Downloads/obsidianburdenNov25` is the Obsidian vault and EngAIn's development/test manuscript. The owner's working manuscript on `/mnt` is never touched by pipeline work. `/mnt/data-drive/codex/ob-codex` is reference material.

## Requirements to preserve while developing EngAIn

1. Distinct Book, Chapter, Scene and Entity identities, with explicit relationships and source provenance.
2. Never treat temporary catalog file identifiers as permanent narrative or entity identities.
3. Environment preview, scene loading and gameplay-state mutation stay separate operations.
4. Reading position and game-save state stay independent.
5. Capabilities are exposed through modular, versioned interfaces, not project-specific shortcuts.
6. Manuscript discovery, Mettaext extraction, Stageroom output, Godotsim authority and Godot presentation stay separate responsibilities.
7. Consult existing Ob-Scene contracts (`ob-scene-workspace/contracts/`) before any decision that could create future incompatibility.

Related decision (2026-11-18): Lexicon is the shared authority for vocabulary and source-occurrence IDs. Ob-Scene consumes Lexicon references; Mettaext eventually consumes the same floor; Ob-Scene keeps scene decomposition, source-witness relationships and Codex processes; EngAInOS keeps canonical entity identity. Ob-Scene T1 contracts are preserved until inspected.

## Potential conflicts found so far (for later review)

| # | Conflict | Where | Today's handling |
|---|---|---|---|
| C1 | `catalog_id` (`<book folder>/<file name>`) is stable across edits but not across rename or move. Persistent bookmarks and links need durable document identity or a migration record. | `tier1/engainos/tools/chapter_discovery.py` (V03) | Used only for the live selector and M01a output paths. Not a permanent identity. |
| C2 | Three chapter identities with no mapping: `catalog_id`, legacy/Mettaext `chapter_id` (file stem), Codex `ch060`. | V03 catalog, Chapterroom, ob-codex | None. |
| C3 | Scene identity is per system: `narrative_to_game` emits one scene per chapter (id from Pass 4 `@id`), Chapterroom `scene_packets` ids, Codex `ch060-sn01`, runtime `canonical_scene_id` rewrites. | tier3/mettaext, tier2/godotsim | None. |
| C4 | Mettaext Pass 5 entity ids are slugs of names, regenerated per run; no EngAInOS admission. A Codex link to "item42" cannot yet find the same object in a built environment. Run output also contains non-entities ("Someone", "Unknown"). | `tier3/mettaext/passroom/pass5_game_bridge.py`; M01a run of `book_01_book_of_genesis/003_first_contact.md` | None. Identity design needed before large-scale generation. |
| C5 | Ob-Scene T1 source witnesses vs Lexicon occurrences. | ob-scene contracts | Decided: Lexicon is authority; T1 preserved until inspected. |
| C6 | Codex chapter text differs from the test vault (33 of 138 files), so Ob-Scene witness hashes will not match EngAIn `source_sha256`. | ob-codex vs Downloads vault | Downloads is the test source; Codex is reference. |
| C7 | Stageroom rule "Godot may display only accepted state" vs showing Mettaext candidates. | `tier3/mettaext/stageroom/STAGEROOM_HANDOFF_RULE.md` | Inspection shows output labelled "candidate — not accepted" (owner did not object). Acceptance step still to be defined. |
| C8 | `POST 8080 /scene/load` mutates the runtime snapshot. An environment preview must not go through it (requirement 3). | `tier2/godotsim/http_handlers.py` | Preview/inspection reads served output only; nothing is posted to 8080. |
| C9 | Save slots: not inspected whether 8080 can save or restore a snapshot. | tier2/godotsim | Unknown. |
| C10 | 8765 `/list_scenes` and `/list_chapters` list Chapterroom scene ids, unrelated to the catalog. | `tier1/engainos/bridgeroom/scene_server.py` | Left unchanged for compatibility; `/chapters/catalog` is the catalog interface. |
