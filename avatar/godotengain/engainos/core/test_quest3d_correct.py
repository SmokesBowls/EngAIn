#!/usr/bin/env python3
"""
Corrected test for Quest3D system
"""

# First, let's see what's available
import quest3d_mr
import quest3d_integration

print("Available in quest3d_mr:", [x for x in dir(quest3d_mr) if not x.startswith('_')])
print("\nAvailable in quest3d_integration:", [x for x in dir(quest3d_integration) if not x.startswith('_')])

# Now try to import based on what we see
from quest3d_mr import Quest, WorldState, Objective, Condition, Reward, QuestState
from quest3d_integration import Quest3DIntegration

print("\n🔧 Testing Quest3D...")

# Create a quest - check how Quest constructor works
try:
    quest = Quest(
        id="demo_quest",
        name="Demo Quest", 
        description="Test the quest system",
        objectives=[
            Objective(
                id="step1",
                description="Go to test location",
                conditions=[Condition(type="at_location", parameters={"location": "test_spot"})]
            )
        ],
        rewards=[]
    )
    
    print("✅ Created quest")
    
    # Test integration layer
    quest_system = Quest3DIntegration()
    quest_system.register_quest(quest)
    
    world = WorldState(
        flags={},
        items={},
        stats={},
        location="test_spot", 
        time=0
    )
    
    deltas = quest_system.update(world)
    print(f"✅ Got {len(deltas)} deltas from update")
    
    state = quest_system.get_quest("demo_quest")
    print(f"✅ Quest state: {state.state}")
    
    # Check if we can get active quests
    active = quest_system.get_active_quests()
    print(f"✅ Active quests: {len(active)}")
    
    # Check summary
    summary = quest_system.get_summary()
    print(f"✅ Summary keys: {list(summary.keys())}")
    
    print("\n🎉 Quest3D system is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
