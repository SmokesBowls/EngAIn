#!/usr/bin/env python3
"""
engine_summary.py — EngineSummary Projection

Pure function that produces a flat, read-only summary of engine state
for the Godot HUD overlay. Same pattern as get_quest_summaries().

EngineSummary shape:
    {
        "game_time": float,
        "scene_id": str,
        "active_quests": int,
        "completed_quests": int,
        "combat_state": str,        # "idle" | "engaged" | "dead"
        "reality_mode": str,        # "waking" | "dream" | "memory" | "liminal"
        "player_health": float,
        "player_health_max": float,
        "player_location": str,
        "entities_count": int,
        "tick_rate": float,         # delta_time from last step
        "pillar_status": {
            "engain": str,          # "running" | "paused" | "error"
            "mvcar": str,
            "tv": str
        }
    }

NO internals. NO kernel state. NO quest details. Just the dashboard.
"""

from typing import Dict


def get_engine_summary(
    world: Dict,
    delta_time: float = 0.0,
    scene_id: str = "",
    pillar_status: Dict = None,
    reality_mode: str = "waking"
) -> Dict:
    """
    Generate flat EngineSummary from world snapshot.
    Pure function — no side effects.

    Args:
        world: Full world state (entities + quest + combat etc.)
        delta_time: Last frame delta
        scene_id: Current scene identifier
        pillar_status: Override pillar statuses
        reality_mode: Current consciousness mode

    Returns:
        Flat EngineSummary dict for Godot HUD
    """
    entities = world.get("entities", {})
    player = entities.get("player", {})
    quest_data = world.get("quest", {})
    quests = quest_data.get("quests", {})

    # Quest counts
    active_quests = sum(1 for q in quests.values()
                        if _get_status(q) == "active")
    completed_quests = sum(1 for q in quests.values()
                          if _get_status(q) == "completed")

    # Combat state
    combat = player.get("combat", {})
    player_health = combat.get("health", 0.0)
    player_health_max = combat.get("max_health", 100.0)
    if player_health <= 0:
        combat_state = "dead"
    elif combat.get("in_combat", False) or combat.get("engaged", False):
        combat_state = "engaged"
    else:
        combat_state = "idle"

    # Pillar status
    if pillar_status is None:
        pillar_status = {
            "engain": "running",
            "mvcar": "running" if quest_data.get("tick", 0) > 0 else "idle",
            "tv": "reserved"
        }

    return {
        "game_time": quest_data.get("tick", 0.0),
        "scene_id": scene_id or player.get("location", "unknown"),
        "active_quests": active_quests,
        "completed_quests": completed_quests,
        "combat_state": combat_state,
        "reality_mode": reality_mode,
        "player_health": player_health,
        "player_health_max": player_health_max,
        "player_location": player.get("location", "unknown"),
        "entities_count": len(entities),
        "tick_rate": delta_time,
        "pillar_status": pillar_status
    }


def _get_status(quest) -> str:
    """Get status from quest dict or object."""
    if isinstance(quest, dict):
        return quest.get("status", "inactive")
    return getattr(quest, "status", "inactive")


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Testing EngineSummary...")
    print("=" * 60)

    passed = 0

    # ── Test 1: Basic summary from populated world ──
    print("\n[Test 1] Populated world summary")
    world = {
        "entities": {
            "player": {
                "flags": {"talked_to_healer": True},
                "items": {"sword": 1},
                "location": "village_square",
                "combat": {"health": 75.0, "max_health": 100.0}
            },
            "npc_elder": {"location": "temple"},
            "npc_guard": {"location": "gate"},
        },
        "quest": {
            "quests": {
                "q1": {"status": "active", "title": "Find Sword"},
                "q2": {"status": "active", "title": "Deliver Message"},
                "q3": {"status": "completed", "title": "Talk to Elder"},
                "q4": {"status": "inactive", "title": "Secret Quest"},
                "q5": {"status": "failed", "title": "Timed Quest"},
            },
            "tick": 42.5
        }
    }
    summary = get_engine_summary(world, delta_time=0.016, scene_id="ch01_village")
    assert summary["game_time"] == 42.5
    assert summary["scene_id"] == "ch01_village"
    assert summary["active_quests"] == 2
    assert summary["completed_quests"] == 1
    assert summary["combat_state"] == "idle"
    assert summary["player_health"] == 75.0
    assert summary["player_health_max"] == 100.0
    assert summary["player_location"] == "village_square"
    assert summary["entities_count"] == 3
    assert summary["tick_rate"] == 0.016
    assert summary["reality_mode"] == "waking"
    assert summary["pillar_status"]["engain"] == "running"
    print("  ✅ All fields correct")
    passed += 1

    # ── Test 2: Combat states ──
    print("\n[Test 2] Combat state detection")
    # Dead
    world_dead = {"entities": {"player": {"combat": {"health": 0}}}, "quest": {"quests": {}, "tick": 0}}
    assert get_engine_summary(world_dead)["combat_state"] == "dead"
    # Engaged
    world_fight = {"entities": {"player": {"combat": {"health": 50, "in_combat": True}}}, "quest": {"quests": {}, "tick": 0}}
    assert get_engine_summary(world_fight)["combat_state"] == "engaged"
    # Idle
    world_idle = {"entities": {"player": {"combat": {"health": 100}}}, "quest": {"quests": {}, "tick": 0}}
    assert get_engine_summary(world_idle)["combat_state"] == "idle"
    print("  ✅ dead / engaged / idle detected correctly")
    passed += 1

    # ── Test 3: Empty world ──
    print("\n[Test 3] Empty world (graceful defaults)")
    empty = {}
    summary_e = get_engine_summary(empty)
    assert summary_e["game_time"] == 0.0
    assert summary_e["active_quests"] == 0
    assert summary_e["combat_state"] == "dead"  # health 0
    assert summary_e["entities_count"] == 0
    assert summary_e["player_location"] == "unknown"
    print("  ✅ Graceful defaults on empty world")
    passed += 1

    # ── Test 4: Reality modes ──
    print("\n[Test 4] Reality mode passthrough")
    for mode in ["waking", "dream", "memory", "liminal"]:
        s = get_engine_summary(empty, reality_mode=mode)
        assert s["reality_mode"] == mode
    print("  ✅ All reality modes pass through")
    passed += 1

    # ── Test 5: Determinism ──
    print("\n[Test 5] Determinism")
    import copy
    s1 = get_engine_summary(copy.deepcopy(world), delta_time=0.016)
    s2 = get_engine_summary(copy.deepcopy(world), delta_time=0.016)
    assert s1 == s2
    print("  ✅ Same input → same output")
    passed += 1

    print("\n" + "=" * 60)
    print(f"EngineSummary: {passed} passed, 0 failed")
    print("=" * 60)
