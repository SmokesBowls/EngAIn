# Unified Pipeline Quick Start

## Basic Usage
```bash
# Single chapter
python3 narrative_to_game.py chapter.txt

# Multiple chapters
python3 narrative_to_game.py book/*.txt

# Custom output directory
python3 narrative_to_game.py chapter.txt --output game_scenes/
```

## Output Format

Game scenes are JSON files containing:
- Character entities (health, position, name)
- Narrative events (dialogue, thoughts, actions)
- Initial game state (combat, spatial, locations)
- Metadata (scene ID, location, description)

## Pipeline Stages

1. **Pass 1:** Segmentation (narrative → typed segments)
2. **Pass 2:** Inference (entity resolution)
3. **Pass 3:** Merge (unified ZONJ)
4. **Pass 4:** ZON Bridge (memory fabric)
5. **Pass 5:** Game Bridge (scene JSON)

## Example
```bash
python3 narrative_to_game.py book/03_Fist_contact.txt
```

Output: `game_scenes/03_Fist_contact.json` with 8 characters and 12 events.

**Ready for Godot, Unity, or any game engine.**
