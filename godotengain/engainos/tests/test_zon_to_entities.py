"""
Test zon_to_entities.py - ZON → Entity3D Wiring

Tests the glue layer that connects narrative extraction to spatial system.
Uses fake ZON data (no file dependencies).
"""

import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from zon_to_entities import (
    zon_entity_to_entity3d,
    zon_scene_to_entities,
    get_concept_mapping,
    register_concept_mapping,
    ConceptMapping,
    get_entity_statistics
)
from spatial_skin_system import ColorRGB


def test_zon_to_entities():
    print("=== ZON → ENTITY3D WIRING TEST ===\n")
    
    # TEST 1: Concept mapping lookup
    print("TEST 1: Concept mapping")
    guard_mapping = get_concept_mapping("guard")
    assert guard_mapping.zw_concept == "guard"
    assert guard_mapping.ap_profile == "damageable_npc"
    assert guard_mapping.placeholder_mesh == "capsule"
    print(f"  ✓ guard → {guard_mapping.placeholder_mesh}, {guard_mapping.ap_profile}")
    
    door_mapping = get_concept_mapping("door")
    assert door_mapping.placeholder_mesh == "cube"
    print(f"  ✓ door → {door_mapping.placeholder_mesh}")
    
    # TEST 2: Unknown concept fallback
    print("\nTEST 2: Unknown concept fallback")
    unknown_mapping = get_concept_mapping("alien_spaceship")
    assert unknown_mapping.zw_concept == "unknown"
    assert unknown_mapping.placeholder_mesh == "cube"
    assert unknown_mapping.default_color.r == 1.0  # Magenta error color
    print(f"  ✓ unknown concept → {unknown_mapping.placeholder_mesh} (magenta)")
    
    # TEST 3: Single ZON entity conversion
    print("\nTEST 3: Single ZON entity → Entity3D")
    zon_guard = {
        "type": "guard",
        "position": [10.0, 0.0, 5.0],
        "rotation": [0.0, 1.57, 0.0],  # Facing direction
        "id": "guard_001",
        "tags": ["patrol", "hostile"]
    }
    
    entity = zon_entity_to_entity3d(zon_guard, auto_bind_skins=False)
    
    assert entity.zw_concept == "guard"
    assert entity.placeholder_mesh == "capsule"
    assert entity.transform.x == 10.0
    assert entity.transform.y == 0.0
    assert entity.transform.z == 5.0
    assert entity.transform.ry == 1.57
    assert entity.entity_id == "guard_001"
    assert "patrol" in entity.tags
    print(f"  ✓ Converted: {entity.zw_concept}")
    print(f"  ✓ Position: ({entity.transform.x}, {entity.transform.y}, {entity.transform.z})")
    print(f"  ✓ Placeholder: {entity.placeholder_mesh}")
    
    # TEST 4: Scene with multiple entities
    print("\nTEST 4: ZON scene → Multiple entities")
    zon_scene = {
        "scene_id": "chapter1_opening",
        "entities": [
            {"type": "guard", "position": [10, 0, 5], "id": "guard_001"},
            {"type": "guard", "position": [15, 0, 5], "id": "guard_002"},
            {"type": "merchant", "position": [5, 0, 10], "id": "merchant_001"},
            {"type": "door", "position": [0, 0, 15], "id": "door_001"},
            {"type": "barrel", "position": [3, 0, 8], "id": "barrel_001"}
        ]
    }
    
    entities = zon_scene_to_entities(zon_scene, auto_bind_skins=False)
    
    assert len(entities) == 5
    assert entities[0].zw_concept == "guard"
    assert entities[2].zw_concept == "merchant"
    assert entities[3].zw_concept == "door"
    print(f"  ✓ Converted: {len(entities)} entities")
    
    # Verify correct placeholder meshes
    assert entities[0].placeholder_mesh == "capsule"  # guard
    assert entities[2].placeholder_mesh == "capsule"  # merchant
    assert entities[3].placeholder_mesh == "cube"     # door
    assert entities[4].placeholder_mesh == "cylinder" # barrel
    print(f"  ✓ Placeholders: capsule, capsule, cube, cylinder")
    
    # TEST 5: Entity statistics
    print("\nTEST 5: Entity statistics")
    stats = get_entity_statistics(entities)
    
    assert stats["total_entities"] == 5
    assert stats["concept_counts"]["guard"] == 2
    assert stats["concept_counts"]["merchant"] == 1
    assert stats["concept_counts"]["door"] == 1
    assert stats["concept_counts"]["barrel"] == 1
    print(f"  ✓ Total: {stats['total_entities']}")
    print(f"  ✓ Concepts: {stats['concept_counts']}")
    print(f"  ✓ Placeholders: {stats['placeholder_counts']}")
    
    # TEST 6: Default values (scale, no rotation)
    print("\nTEST 6: Default transform values")
    minimal_entity = {
        "type": "chest",
        "position": [5, 0, 5]
        # No rotation, no scale specified
    }
    
    entity = zon_entity_to_entity3d(minimal_entity, auto_bind_skins=False)
    
    assert entity.transform.rx == 0.0
    assert entity.transform.ry == 0.0
    assert entity.transform.rz == 0.0
    assert entity.transform.sx == 1.0
    assert entity.transform.sy == 1.0
    assert entity.transform.sz == 1.0
    print(f"  ✓ Defaults applied: rotation=(0,0,0), scale=(1,1,1)")
    
    # TEST 7: Custom concept registration
    print("\nTEST 7: Custom concept mapping")
    boss_mapping = ConceptMapping(
        zw_concept="dragon_boss",
        ap_profile="boss_enemy",
        placeholder_mesh="sphere",
        collision_role="solid",
        default_color=ColorRGB(1.0, 0.0, 0.0),  # Red
        kernel_bindings={"combat": True, "ai": "boss"}
    )
    register_concept_mapping(boss_mapping)
    
    zon_boss = {"type": "dragon_boss", "position": [20, 5, 20]}
    entity = zon_entity_to_entity3d(zon_boss, auto_bind_skins=False)
    
    assert entity.zw_concept == "dragon_boss"
    assert entity.ap_profile == "boss_enemy"
    assert entity.placeholder_mesh == "sphere"
    assert entity.kernel_bindings["ai"] == "boss"
    print(f"  ✓ Custom concept: {entity.zw_concept} → {entity.placeholder_mesh}")
    
    # TEST 8: Partial concept matching
    print("\nTEST 8: Partial concept matching")
    zon_tower_guard = {"type": "tower_guard", "position": [0, 10, 0]}
    entity = zon_entity_to_entity3d(zon_tower_guard, auto_bind_skins=False)
    
    # Should match "guard" from "tower_guard"
    assert entity.ap_profile == "damageable_npc"
    assert entity.placeholder_mesh == "capsule"
    print(f"  ✓ 'tower_guard' → matched 'guard' → capsule")
    
    # TEST 9: Kernel bindings
    print("\nTEST 9: Kernel bindings")
    guard_entity = zon_entity_to_entity3d(
        {"type": "guard", "position": [0, 0, 0]},
        auto_bind_skins=False
    )
    
    assert "combat" in guard_entity.kernel_bindings
    assert guard_entity.kernel_bindings["combat"] is True
    assert guard_entity.kernel_bindings.get("faction") == "Empire"
    print(f"  ✓ Guard bindings: {guard_entity.kernel_bindings}")
    
    merchant_entity = zon_entity_to_entity3d(
        {"type": "merchant", "position": [0, 0, 0]},
        auto_bind_skins=False
    )
    
    assert "dialogue" in merchant_entity.kernel_bindings
    assert "inventory" in merchant_entity.kernel_bindings
    print(f"  ✓ Merchant bindings: {merchant_entity.kernel_bindings}")
    
    # TEST 10: Color defaults
    print("\nTEST 10: Default colors")
    guard = zon_entity_to_entity3d(
        {"type": "guard", "position": [0, 0, 0]},
        auto_bind_skins=False
    )
    merchant = zon_entity_to_entity3d(
        {"type": "merchant", "position": [0, 0, 0]},
        auto_bind_skins=False
    )
    player = zon_entity_to_entity3d(
        {"type": "player", "position": [0, 0, 0]},
        auto_bind_skins=False
    )
    
    assert guard.color.r > 0.7  # Red-ish
    assert merchant.color.g > 0.7  # Green-ish
    assert player.color.b > 0.7  # Blue-ish
    print(f"  ✓ Guard: red-ish")
    print(f"  ✓ Merchant: green-ish")
    print(f"  ✓ Player: blue-ish")
    
    print("\n" + "="*60)
    print("✅ ZON → ENTITY3D WIRING: ALL TESTS PASS")
    print("="*60)
    print("\nProven:")
    print("  ✓ ZON entity → Entity3D conversion")
    print("  ✓ Concept → placeholder mapping")
    print("  ✓ Transform extraction (position, rotation, scale)")
    print("  ✓ Default value handling")
    print("  ✓ Scene batch conversion")
    print("  ✓ Statistics generation")
    print("  ✓ Custom concept registration")
    print("  ✓ Partial concept matching")
    print("  ✓ Kernel bindings")
    print("  ✓ Color defaults")
    print("\n🔌 Pure glue. Story → Playable Scene.")


if __name__ == "__main__":
    test_zon_to_entities()
