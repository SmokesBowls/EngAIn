#!/usr/bin/env python3
"""
godot_adapter.py - Python Bridge for Godot

Handles entity conversion and scene data preparation for the Godot runtime.
Supports both internal test scenes and external JSON scene files.

Usage:
    python3 godot_adapter.py --scene chapter1_opening
    python3 godot_adapter.py --scene path/to/scene.json
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add core to path
CORE_DIR = Path(__file__).resolve().parent
if CORE_DIR not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from zon_to_entities import zon_scene_to_entities
from spatial_skin_system import build_render_plan


# ================================================================
# TEST SCENES (Fallback test data)
# ================================================================

TEST_SCENES = {
    "chapter1_opening": {
        "scene_id": "chapter1_opening",
        "entities": [
            {
                "type": "guard",
                "position": [10.0, 0.0, 5.0],
                "rotation": [0.0, 1.57, 0.0],
                "id": "guard_001",
                "tags": ["patrol", "hostile"]
            },
            {
                "type": "guard",
                "position": [15.0, 0.0, 5.0],
                "rotation": [0.0, -1.57, 0.0],
                "id": "guard_002",
                "tags": ["patrol", "hostile"]
            },
            {
                "type": "merchant",
                "position": [5.0, 0.0, 10.0],
                "id": "merchant_001",
                "tags": ["friendly", "vendor"]
            }
        ]
    },
    
    "test_minimal": {
        "scene_id": "test_minimal",
        "entities": [
            {
                "type": "player",
                "position": [0.0, 0.0, 0.0],
                "id": "player"
            }
        ]
    }
}


class GodotAdapter:
    """
    Adapter to bridge EngAIn backend data to Godot frontend.
    """
    
    def __init__(self, scene_id: str = None):
        self.active_scene_id = scene_id
        self.active_scene_data = None
        
        if scene_id:
            self.load_scene(scene_id)
            
    def load_scene(self, scene_input: str) -> bool:
        """
        Load scene data from path or internal registry.
        """
        # 1. Check if it's a file path
        path = Path(scene_input)
        if path.exists() and path.is_file():
            try:
                with path.open('r') as f:
                    self.active_scene_data = json.load(f)
                    self.active_scene_id = path.stem
                    return True
            except Exception as e:
                print(f"Error loading scene file {scene_input}: {e}", file=sys.stderr)
        
        # 2. Check internal test scenes
        if scene_input in TEST_SCENES:
            self.active_scene_data = TEST_SCENES[scene_input]
            self.active_scene_id = scene_input
            return True
            
        return False

    def get_render_data(self) -> dict:
        """
        Get processed render data for Godot.
        """
        if not self.active_scene_data:
            return {
                "error": f"Scene not found or not loaded: {self.active_scene_id}",
                "entities": []
            }
        
        # Convert ZON format to Entity3D objects
        # Note: zon_scene_to_entities expects dict with 'entities' list
        entities = zon_scene_to_entities(self.active_scene_data, auto_bind_skins=False)
        
        # Build RenderPlans using the skin system
        render_plans = [build_render_plan(entity) for entity in entities]
        
        # Convert RenderPlans to JSON-friendly dicts
        json_entities = [self._render_plan_to_dict(plan) for plan in render_plans]
        
        return {
            "scene_id": self.active_scene_id,
            "entity_count": len(json_entities),
            "entities": json_entities
        }

    def _render_plan_to_dict(self, plan) -> dict:
        """Helper to serialize RenderPlan"""
        return {
            "placeholder_mesh": plan.mesh_type,
            "transform": plan.transform.to_dict(),
            "color": {
                "r": plan.color.r,
                "g": plan.color.g,
                "b": plan.color.b
            },
            "skin_3d_id": plan.skin_3d_id,
            "skin_2d_id": plan.skin_2d_id,
            "zw_concept": plan.logic_tags.get("zw_concept", "unknown"),
            "ap_profile": plan.logic_tags.get("ap_profile", "generic"),
            "entity_id": plan.logic_tags.get("entity_id", "unknown"),
            "tags": plan.logic_tags.get("tags", []),
            "kernel_bindings": plan.logic_tags.get("kernel_bindings", {})
        }

    def run_loop(self):
        """
        Interactive loop for use as a bridge script.
        """
        # For now, just output once and exit to maintain compatibility with existing bridge calls
        data = self.get_render_data()
        print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="EngAIn → Godot Adapter")
    parser.add_argument("--scene", required=True, help="Scene ID or path to JSON scene file")
    
    args = parser.parse_args()
    
    adapter = GodotAdapter()
    if not adapter.load_scene(args.scene):
        print(json.dumps({
            "error": f"Scene not found: {args.scene}",
            "entities": []
        }, indent=2))
        return

    # Output processed scene data
    print(json.dumps(adapter.get_render_data(), indent=2))


if __name__ == "__main__":
    main()
