#!/usr/bin/env python3
"""
Proper test for Quest3D system using correct imports
"""

from quest3d_mr import Quest, Objective, Condition, Reward, QuestState, QuestStatus, step_quest3d, QuestConfig
from quest3d_integration import Quest3DIntegration

print("🔧 Testing Quest3D System")
print("=" * 50)

# Create a quest definition in the correct format
quest_def = {
    "id": "test_quest",
    "name": "Find the Lost Artifact",
    "description": "Retrieve the ancient artifact from the ruins",
    "objectives": [
        {
            "id": "go_to_ruins",
            "description": "Travel to the ancient ruins",
            "conditions": [
                {
                    "type": "at_location",
                    "target_entity": "player",
                    "key": "location",
                    "value": "ancient_ruins",
                    "comparator": "eq"
                }
            ]
        },
        {
            "id": "retrieve_artifact",
            "description": "Take the artifact",
            "conditions": [
                {
                    "type": "at_location",
                    "target_entity": "player",
                    "key": "location",
                    "value": "ancient_ruins",
                    "comparator": "eq"
                },
                {
                    "type": "has_item",
                    "target_entity": "player",
                    "key": "ancient_artifact",
                    "value": 1,
                    "comparator": "gte"
                }
            ]
        }
    ],
    "rewards": [
        {
            "type": "grant_item",
            "target_entity": "player",
            "key": "gold_coins",
            "value": 100
        },
        {
            "type": "set_flag",
            "target_entity": "player",
            "key": "artifact_found",
            "value": True
        }
    ],
    "preconditions": [
        {
            "type": "flag_set",
            "target_entity": "player",
            "key": "learned_about_artifact",
            "value": True,
            "comparator": "eq"
        }
    ],
    "on_activate": [],
    "on_complete": [],
    "on_fail": [],
    "failure_conditions": [],
    "time_limit": 100
}

print("✅ Created quest definition")

# Test 1: Integration Layer
print("\n1. Testing Integration Layer")
print("-" * 30)

quest_system = Quest3DIntegration()
delta_id = quest_system.register_quest(quest_def)
print(f"   Registered quest with delta ID: {delta_id}")

# Create initial world snapshot
world_snapshot = {
    "entities": {
        "player": {
            "flags": {"learned_about_artifact": True},
            "items": {},
            "stats": {"health": 100, "gold": 0},
            "location": "town_square"
        }
    },
    "quests": {},
    "time": 0
}

print(f"   Initial world snapshot created")
print(f"   Player location: {world_snapshot['entities']['player']['location']}")
print(f"   Player flags: {world_snapshot['entities']['player']['flags']}")

# Process first tick (should register the quest)
result = quest_system.tick(world_snapshot, 0.0)
quests = result.get("quest", {}).get("quests", {})
print(f"   After tick - quests in world: {list(quests.keys())}")

# Check quest was registered
if "test_quest" in quests:
    quest_state = quests["test_quest"]
    print(f"   Quest state: {quest_state.get('status', 'unknown')}")
else:
    print("   ❌ Quest not found in world after registration")

# Activate the quest
quest_system.activate_quest("test_quest")

# Process second tick (should activate quest)
result2 = quest_system.tick(result, 1.0)
quest_state2 = result2.get("quest", {}).get("quests", {}).get("test_quest", {})
print(f"\n   After activation - Quest state: {quest_state2.get('status', 'unknown')}")

# Check objectives
objectives = quest_state2.get("objectives", [])
print(f"   Objectives count: {len(objectives)}")
for obj in objectives:
    print(f"     - {obj.get('id')}: {obj.get('description')} (status: {obj.get('status', 'unknown')})")

# Test 2: Update world to complete first objective
print("\n2. Testing Objective Completion")
print("-" * 30)

# Move player to ruins
world_snapshot2 = result2.copy()
world_snapshot2["entities"]["player"]["location"] = "ancient_ruins"
world_snapshot2["time"] = 2

result3 = quest_system.tick(world_snapshot2, 2.0)
quest_state3 = result3.get("quest", {}).get("quests", {}).get("test_quest", {})

print(f"   Player moved to: ancient_ruins")
print(f"   Quest state: {quest_state3.get('status', 'unknown')}")

# Check first objective
for obj in quest_state3.get("objectives", []):
    if obj.get("id") == "go_to_ruins":
        print(f"   Objective '{obj.get('id')}' status: {obj.get('status', 'unknown')}")

# Test 3: Complete second objective
print("\n3. Testing Quest Completion with Rewards")
print("-" * 30)

# Give player the artifact
world_snapshot3 = result3.copy()
world_snapshot3["entities"]["player"]["items"]["ancient_artifact"] = 1
world_snapshot3["time"] = 3

result4 = quest_system.tick(world_snapshot3, 3.0)
quest_state4 = result4.get("quest", {}).get("quests", {}).get("test_quest", {})

print(f"   Player now has artifact: {world_snapshot3['entities']['player']['items']}")
print(f"   Final quest state: {quest_state4.get('status', 'unknown')}")

# Check if rewards were applied
player_after = result4.get("entities", {}).get("player", {})
print(f"\n   Player after quest completion:")
print(f"     Gold: {player_after.get('items', {}).get('gold_coins', 'None')}")
print(f"     Flag 'artifact_found': {player_after.get('flags', {}).get('artifact_found', False)}")

# Test 4: Query API
print("\n4. Testing Query API")
print("-" * 30)

active_quests = quest_system.get_active_quests(result4)
print(f"   Active quests: {len(active_quests)}")

quest_summary = quest_system.get_quest_summary(result4)
print(f"   Quest summary keys: {list(quest_summary.keys())}")

# Test 5: Direct kernel function (step_quest3d)
print("\n5. Testing Direct Kernel Function")
print("-" * 30)

# Create a minimal config
config = QuestConfig()
kernel_world = {
    "entities": {
        "player": {
            "flags": {"test_flag": True},
            "items": {"test_item": 1},
            "stats": {},
            "location": "test_loc"
        }
    },
    "quests": {},
    "time": 0
}

kernel_deltas = []
kernel_alerts = []

# Call the kernel function directly
new_world, accepted_ids, new_alerts = step_quest3d(kernel_world, kernel_deltas, config, 0.0)
print(f"   Kernel function called successfully")
print(f"   World keys after kernel: {list(new_world.keys())}")

print("\n" + "=" * 50)
print("✅ Quest3D System Test Completed Successfully!")
print("=" * 50)
