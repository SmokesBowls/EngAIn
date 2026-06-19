#!/usr/bin/env python3
"""
fetch_scene_once.py - Diagnostic probe for EngAIn Engine

Fetches and prints scene data via the godot_adapter.
Useful for verifying engine state without starting the full daemon.

Usage:
    python3 fetch_scene_once.py test_scene
    python3 fetch_scene_once.py /path/to/my_scene.json
"""

import sys
import os
import json
from pathlib import Path

# Add core to path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
CORE_DIR = ROOT_DIR / "core"
sys.path.insert(0, str(CORE_DIR))

try:
    from godot_adapter import GodotAdapter
except ImportError:
    print("Error: Could not import godot_adapter. Ensure this script is in the tools/ directory.")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_scene_once.py <scene_id_or_path>")
        sys.exit(1)

    scene_input = sys.argv[1]
    
    # Try to resolve relative paths
    path = Path(scene_input)
    if not path.is_absolute() and not path.exists():
        # Maybe it's in game_scenes?
        game_scenes_path = ROOT_DIR / "game_scenes" / f"{scene_input}.json"
        if game_scenes_path.exists():
            scene_input = str(game_scenes_path)
    
    adapter = GodotAdapter()
    if not adapter.load_scene(scene_input):
        print(json.dumps({
            "error": f"Scene not found: {scene_input}",
            "entities": []
        }, indent=2))
        sys.exit(1)

    # Output processed scene data
    print(json.dumps(adapter.get_render_data(), indent=2))

if __name__ == "__main__":
    main()
