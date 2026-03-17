#!/usr/bin/env python3
"""
godot_bridge_test.py - Python Bridge for Godot
Translates ZON data into Godot-ready RenderPlan JSON.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from semantic_bridge import SemanticRegistry, zon_to_entity3d
from spatial_skin_system import build_render_plan

# ================================================================
# TEST SCENES (Authorize ZON data)
# ================================================================

TEST_SCENES = {
    "chapter1_opening": [
        {"type": "guard", "position": [10.0, 0.0, 5.0], "rotation": [0.0, 1.57, 0.0], "id": "guard_001", "tags": ["patrol", "hostile"]},
        {"type": "guard", "position": [15.0, 0.0, 5.0], "rotation": [0.0, -1.57, 0.0], "id": "guard_002", "tags": ["patrol", "hostile"]},
        {"type": "merchant", "position": [5.0, 0.0, 10.0], "id": "merchant_001", "tags": ["friendly", "vendor"]},
        {"type": "door", "position": [0.0, 0.0, 15.0], "scale": [2.0, 3.0, 0.2], "id": "door_001", "tags": ["locked"]},
        {"type": "barrel", "position": [3.0, 0.0, 8.0], "id": "barrel_001"},
        {"type": "chest", "position": [12.0, 0.0, 12.0], "id": "chest_001", "tags": ["loot"]}
    ],
    "test_minimal": [
        {"type": "player", "position": [0.0, 0.0, 0.0], "id": "player"},
        {"type": "guard", "position": [5.0, 0.0, 5.0], "id": "guard_001"}
    ]
}

def render_plan_to_json(render_plan) -> dict:
    """Convert RenderPlan to JSON-serializable dict."""
    return {
        "placeholder_mesh": render_plan.mesh_type,
        "transform": render_plan.transform.to_dict(),
        "color": {
            "r": render_plan.color.r,
            "g": render_plan.color.g,
            "b": render_plan.color.b
        },
        "skin_3d_id": render_plan.skin_3d_id,
        "skin_2d_id": render_plan.skin_2d_id,
        "zw_concept": render_plan.logic_tags.get("zw_concept", "unknown"),
        "ap_profile": render_plan.logic_tags.get("ap_profile", "generic"),
        "entity_id": render_plan.logic_tags.get("entity_id", "unknown"),
        "tags": render_plan.logic_tags.get("tags", []),
        "kernel_bindings": render_plan.logic_tags.get("kernel_bindings", {})
    }

def get_scene_data(scene_id: str) -> dict:
    """Get scene data for Godot."""
    if scene_id not in TEST_SCENES:
        return {"error": f"Scene not found: {scene_id}", "entities": []}
    
    zon_data = TEST_SCENES[scene_id]
    
    # Setup Semantic Registry
    registry = SemanticRegistry()
    config_path = Path(__file__).parent.parent / "configs" / "concepts.yaml"
    if config_path.exists():
        registry.load_concepts_from_config(config_path)
    
    # Translate ZON -> Entity3D -> RenderPlan -> JSON
    json_entities = []
    for zon_entity in zon_data:
        entity = zon_to_entity3d(zon_entity, registry)
        plan = build_render_plan(entity)
        json_entities.append(render_plan_to_json(plan))
    
    return {
        "scene_id": scene_id,
        "entity_count": len(json_entities),
        "entities": json_entities
    }

def main():
    parser = argparse.ArgumentParser(description="EngAIn → Godot Bridge")
    parser.add_argument("--scene", required=True, help="Scene ID to load")
    args = parser.parse_args()
    
    scene_data = get_scene_data(args.scene)
    print(json.dumps(scene_data, indent=2))

if __name__ == "__main__":
    main()
