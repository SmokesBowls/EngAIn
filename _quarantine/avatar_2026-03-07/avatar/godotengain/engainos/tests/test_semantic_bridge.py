# tests/test_semantic_bridge.py

import sys
import os
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).parent.parent / "core"))

from semantic_bridge import SemanticRegistry, zon_to_entity3d, ConceptProfile
from spatial_skin_system import ColorRGB

def test_concept_resolution():
    registry = SemanticRegistry()
    
    # Manually add a concept for testing
    registry.concepts["guard"] = ConceptProfile(
        zw_concept="guard",
        placeholder_mesh="capsule",
        ap_profile="damageable_npc",
        collision_role="solid",
        default_color=ColorRGB(1, 0, 0),
        tags=["combat"]
    )
    
    registry.partial_matchers = {"tower_": "guard"}
    
    # 1. Exact match
    profile = registry.resolve_concept("guard")
    assert profile.zw_concept == "guard"
    
    # 2. Partial match
    profile = registry.resolve_concept("tower_guard")
    assert profile.zw_concept == "guard"
    
    # 3. Intelligent fallback (word analysis)
    profile = registry.resolve_concept("royal_knight")
    assert profile.zw_concept == "guard"  # 'knight' is in the fallback list for 'guard'
    
    # 4. Ultimate fallback
    profile = registry.resolve_concept("mysterious_void")
    assert profile.zw_concept == "mysterious_void"
    assert "fallback" in profile.tags

def test_zon_to_entity3d():
    registry = SemanticRegistry()
    registry.concepts["door"] = ConceptProfile(
        zw_concept="door",
        placeholder_mesh="cube",
        ap_profile="door_rule",
        collision_role="solid",
        default_color=ColorRGB(0.5, 0.5, 0.5),
        default_scale=(1, 2, 1)
    )
    
    zon_entity = {
        "id": "door_01",
        "type": "door",
        "position": [10, 0, 5],
        "rotation": [0, 1.57, 0]
    }
    
    entity = zon_to_entity3d(zon_entity, registry)
    
    assert entity.entity_id == "door_01"
    assert entity.zw_concept == "door"
    assert entity.transform.x == 10
    assert entity.transform.ry == 1.57
    assert entity.placeholder_mesh == "cube"
    assert entity.collision_role == "solid"
    assert entity.source_data["raw_concept"] == "door"

if __name__ == "__main__":
    test_concept_resolution()
    test_zon_to_entity3d()
    print("Semantic Bridge tests passed!")
