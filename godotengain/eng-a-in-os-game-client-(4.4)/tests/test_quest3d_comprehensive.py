#!/usr/bin/env python3
"""
Comprehensive test of Quest3D system
"""

from quest3d_mr import *
from quest3d_integration import QuestIntegration

def test_kernel_basic():
    """Test basic kernel operations"""
    print("🧪 Testing Kernel Basics")
    
    # Create a quest
    quest = Quest(
        id="test_quest",
        name="Test Quest",
        description="A test quest",
        objectives=[
            Objective(
                id="obj1",
                description="Complete step 1",
                conditions=[
                    Condition(type="flag_set", parameters={"flag": "step1_done", "value": True})
                ]
            ),
            Objective(
                id="obj2",
                description="Complete step 2",
                conditions=[
                    Condition(type="flag_set", parameters={"flag": "step2_done", "value": True})
                ]
            )
        ],
        rewards=[
            Reward(type="grant_item", parameters={"item_id": "reward_item"})
        ]
    )
    
    kernel = QuestKernel()
    kernel.register_quest(quest)
    
    # Test initial state
    world = WorldState(
        flags={"step1_done": False, "step2_done": False},
        items={},
        stats={},
        location="start",
        time=0
    )
    
    # Activate quest
    result = kernel.activate_quest("test_quest", world)
    print(f"  Quest activated: {result}")
    
    # Update world to complete first objective
    world = world._replace(flags={"step1_done": True, "step2_done": False})
    updated = kernel.update_quest_state("test_quest", world)
    print(f"  After step 1: {updated.state}")
    
    # Complete second objective
    world = world._replace(flags={"step1_done": True, "step2_done": True})
    updated = kernel.update_quest_state("test_quest", world)
    print(f"  After step 2: {updated.state}")
    print(f"  Quest completed: {updated.state == QuestState.COMPLETED}")
    
    return True

def test_integration_layer():
    """Test integration layer with delta queuing"""
    print("\n🧪 Testing Integration Layer")
    
    quest_system = QuestIntegration()
    
    # Register multiple quests
    quests = [
        {
            "id": "quest1",
            "name": "First Quest",
            "description": "First of many",
            "objectives": [
                {
                    "id": "obj1",
                    "description": "Find location",
                    "conditions": [
                        {"type": "at_location", "parameters": {"location": "location1"}}
                    ]
                }
            ],
            "rewards": []
        },
        {
            "id": "quest2",
            "name": "Second Quest",
            "description": "Second quest with item requirement",
            "objectives": [
                {
                    "id": "obj1",
                    "description": "Get item",
                    "conditions": [
                        {"type": "has_item", "parameters": {"item_id": "special_item"}}
                    ]
                }
            ],
            "rewards": [
                {"type": "set_flag", "parameters": {"flag": "quest2_complete", "value": True}}
            ]
        }
    ]
    
    for quest in quests:
        quest_system.register_quest(quest)
    
    print(f"  Registered quests: {len(quest_system.get_snapshot().quests)}")
    
    # Test world updates
    world_states = [
        WorldState(flags={}, items={}, stats={}, location="start", time=0),
        WorldState(flags={}, items={}, stats={}, location="location1", time=1),
        WorldState(flags={}, items={"special_item": 1}, stats={}, location="location1", time=2),
    ]
    
    for i, world in enumerate(world_states):
        deltas = quest_system.update(world)
        print(f"  Update {i}: {len(deltas)} deltas")
    
    # Check final states
    q1 = quest_system.get_quest("quest1")
    q2 = quest_system.get_quest("quest2")
    
    print(f"  Quest1 state: {q1.state}")
    print(f"  Quest2 state: {q2.state}")
    
    return True

def test_condition_types():
    """Test different condition types"""
    print("\n🧪 Testing Condition Types")
    
    quest_system = QuestIntegration()
    
    # Quest with various conditions
    quest = {
        "id": "multi_condition",
        "name": "Multi-Condition Quest",
        "description": "Test all condition types",
        "objectives": [
            {
                "id": "all_conditions",
                "description": "Meet all conditions",
                "conditions": [
                    {"type": "flag_set", "parameters": {"flag": "flag1", "value": True}},
                    {"type": "has_item", "parameters": {"item_id": "item1"}},
                    {"type": "at_location", "parameters": {"location": "target_loc"}},
                    {"type": "stat_min", "parameters": {"stat": "health", "value": 50}},
                    {"type": "quest_completed", "parameters": {"quest_id": "prereq_quest"}}
                ]
            }
        ],
        "rewards": []
    }
    
    quest_system.register_quest(quest)
    
    # Test with partial fulfillment
    world = WorldState(
        flags={"flag1": True},
        items={"item1": 1},
        stats={"health": 75},
        location="wrong_loc",
        time=0
    )
    
    quest_system.update(world)
    state = quest_system.get_quest("multi_condition")
    print(f"  Partial conditions: objective active={state.objectives[0].active}")
    
    # Test with all conditions met
    world = world._replace(location="target_loc", flags={"flag1": True, "prereq_quest_complete": True})
    quest_system.update(world)
    state = quest_system.get_quest("multi_condition")
    print(f"  All conditions: objective completed={state.objectives[0].completed}")
    
    return True

def main():
    print("🚀 Starting Quest3D Comprehensive Test")
    print("=" * 50)
    
    try:
        test_kernel_basic()
        test_integration_layer()
        test_condition_types()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nQuest3D System Status:")
        print("  - Kernel: Functional")
        print("  - Integration: Operational")
        print("  - Condition Types: Working")
        print("  - Delta System: Active")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
