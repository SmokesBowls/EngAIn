"""
Test spatial_skin_system.py - Validates placeholder/skin separation

Tests the core principle:
- Placeholder mesh = game object (logic, collision, AP)
- Art skins = optional overlays (2D/3D)
- Game runs with cubes if no art exists
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from spatial_skin_system import (
    Entity3D, Transform3D, ColorRGB, RenderPlan,
    PlaceholderMesh, build_render_plan, build_scene_render_plans,
    SkinRegistry, register_2d_skin, register_3d_skin, get_skin_registry
)


def test_spatial_skin_system():
    print("=== SPATIAL SKIN SYSTEM TEST ===\n")
    
    # TEST 1: Entity with no art (pure placeholder)
    print("TEST 1: Pure placeholder (no art)")
    guard = Entity3D(
        zw_concept="guard",
        ap_profile="damageable_npc",
        kernel_bindings={"combat": True, "faction": "Empire"},
        placeholder_mesh="capsule",
        transform=Transform3D(x=10.0, y=0.0, z=5.0),
        color=ColorRGB(r=0.8, g=0.2, b=0.2),  # Red tint
        entity_id="guard_001"
    )
    
    plan = build_render_plan(guard)
    assert plan.mesh_type == "capsule"
    assert plan.has_any_art() is False
    assert plan.art_priority() == "placeholder"
    assert plan.logic_tags["zw_concept"] == "guard"
    print(f"  ✓ Placeholder: {plan.mesh_type}")
    print(f"  ✓ Color fallback: {plan.color.to_hex()}")
    print(f"  ✓ Art priority: {plan.art_priority()}")
    
    # TEST 2: Entity with 2D art (sprite billboard)
    print("\nTEST 2: 2D sprite overlay")
    merchant = Entity3D(
        zw_concept="merchant",
        ap_profile="interactable",
        kernel_bindings={"dialogue": True, "inventory": True},
        placeholder_mesh="capsule",
        transform=Transform3D(x=5.0, y=0.0, z=10.0),
        skin_2d_id="sprites/merchant_idle.png",
        entity_id="merchant_001"
    )
    
    plan = build_render_plan(merchant)
    assert plan.mesh_type == "capsule"
    assert plan.has_2d_art() is True
    assert plan.has_3d_art() is False
    assert plan.art_priority() == "2d"
    print(f"  ✓ Placeholder: {plan.mesh_type}")
    print(f"  ✓ 2D skin: {plan.skin_2d_id}")
    print(f"  ✓ Art priority: {plan.art_priority()}")
    
    # TEST 3: Entity with 3D art (full model)
    print("\nTEST 3: 3D model overlay")
    door = Entity3D(
        zw_concept="door",
        ap_profile="destructible",
        kernel_bindings={"physics": True},
        placeholder_mesh="cube",
        transform=Transform3D(x=0.0, y=0.0, z=15.0, sx=2.0, sy=3.0, sz=0.2),
        skin_3d_id="models/wooden_door.glb",
        entity_id="door_001"
    )
    
    plan = build_render_plan(door)
    assert plan.mesh_type == "cube"
    assert plan.has_3d_art() is True
    assert plan.art_priority() == "3d"
    print(f"  ✓ Placeholder: {plan.mesh_type}")
    print(f"  ✓ 3D skin: {plan.skin_3d_id}")
    print(f"  ✓ Art priority: {plan.art_priority()}")
    
    # TEST 4: Entity with BOTH 2D and 3D (3D wins)
    print("\nTEST 4: Both 2D and 3D (3D priority)")
    boss = Entity3D(
        zw_concept="boss",
        ap_profile="boss_enemy",
        kernel_bindings={"combat": True, "ai": "aggressive"},
        placeholder_mesh="cylinder",
        transform=Transform3D(x=20.0, y=0.0, z=20.0, sx=2.0, sy=2.0, sz=2.0),
        skin_2d_id="sprites/boss_fallback.png",  # Fallback
        skin_3d_id="models/boss_full.glb",       # Preferred
        entity_id="boss_001"
    )
    
    plan = build_render_plan(boss)
    assert plan.has_2d_art() is True
    assert plan.has_3d_art() is True
    assert plan.art_priority() == "3d"  # 3D takes precedence
    print(f"  ✓ Has both 2D and 3D")
    print(f"  ✓ Art priority: {plan.art_priority()} (3D wins)")
    
    # TEST 5: Scene with mixed art levels
    print("\nTEST 5: Mixed scene (placeholder + 2D + 3D)")
    entities = [guard, merchant, door, boss]
    plans = build_scene_render_plans(entities)
    
    assert len(plans) == 4
    priorities = [p.art_priority() for p in plans]
    assert priorities == ["placeholder", "2d", "3d", "3d"]
    print(f"  ✓ Scene: {len(plans)} entities")
    print(f"  ✓ Art mix: {priorities}")
    
    # TEST 6: Transform serialization
    print("\nTEST 6: Transform export")
    transform = Transform3D(
        x=10.0, y=5.0, z=3.0,
        rx=0.5, ry=1.0, rz=0.0,
        sx=2.0, sy=1.0, sz=1.5
    )
    data = transform.to_dict()
    assert data["position"]["x"] == 10.0
    assert data["rotation"]["y"] == 1.0
    assert data["scale"]["x"] == 2.0
    print(f"  ✓ Transform exported to dict")
    
    # TEST 7: Skin registry
    print("\nTEST 7: Skin registry")
    registry = SkinRegistry()
    
    registry.register_2d("guard_idle", "sprites/guard_idle.png")
    registry.register_2d("guard_walk", "sprites/guard_walk.png")
    registry.register_3d("guard_model", "models/guard.glb")
    
    assert registry.has_2d("guard_idle") is True
    assert registry.has_3d("guard_model") is True
    assert registry.has_2d("nonexistent") is False
    
    assert registry.get_2d("guard_idle") == "sprites/guard_idle.png"
    assert registry.get_3d("guard_model") == "models/guard.glb"
    print(f"  ✓ Registry tracks 2D and 3D assets")
    
    # TEST 8: Global registry
    print("\nTEST 8: Global registry")
    register_2d_skin("test_sprite", "test.png")
    register_3d_skin("test_model", "test.glb")
    
    global_reg = get_skin_registry()
    assert global_reg.has_2d("test_sprite") is True
    assert global_reg.has_3d("test_model") is True
    print(f"  ✓ Global registry working")
    
    # TEST 9: Logic tags preservation
    print("\nTEST 9: Logic metadata")
    entity = Entity3D(
        zw_concept="test",
        ap_profile="test_profile",
        kernel_bindings={"test": True},
        placeholder_mesh="cube",
        transform=Transform3D(0, 0, 0),
        tags=["important", "quest_item"]
    )
    
    plan = build_render_plan(entity)
    assert plan.logic_tags["zw_concept"] == "test"
    assert plan.logic_tags["ap_profile"] == "test_profile"
    assert "important" in plan.logic_tags["tags"]
    print(f"  ✓ Logic tags preserved in render plan")
    
    print("\n" + "="*60)
    print("✅ SPATIAL SKIN SYSTEM: ALL TESTS PASS")
    print("="*60)
    print("\nProven:")
    print("  ✓ Placeholder mesh = game object (always present)")
    print("  ✓ Art skins = optional overlays")
    print("  ✓ 3D art > 2D art > colored placeholder")
    print("  ✓ Logic metadata preserved")
    print("  ✓ Engine-agnostic data structures")
    print("  ✓ Asset registry working")
    print("\n🎨 Art is optional. Game logic is eternal.")


if __name__ == "__main__":
    test_spatial_skin_system()
