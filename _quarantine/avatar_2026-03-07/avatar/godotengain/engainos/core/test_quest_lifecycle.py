from quest3d_integration import Quest3DIntegration

def test_quest_lifecycle():
    """Test a quest from start to finish"""
    print("🚀 Testing Quest Lifecycle")
    print("=" * 50)
    
    quest_system = Quest3DIntegration()
    
    # Create a quest
    quest_def = {
        "id": "lifecycle_test",
        "name": "Lifecycle Test",
        "description": "Test the full quest lifecycle",
        "objectives": [
            {
                "id": "step1",
                "description": "Get the key",
                "conditions": [{
                    "type": "has_item",
                    "target_entity": "player",
                    "key": "old_key",
                    "value": 1,
                    "comparator": "gte"
                }]
            },
            {
                "id": "step2",
                "description": "Unlock the door",
                "conditions": [
                    {
                        "type": "has_item",
                        "target_entity": "player",
                        "key": "old_key",
                        "value": 1,
                        "comparator": "gte"
                    },
                    {
                        "type": "at_location",
                        "target_entity": "player",
                        "key": "locked_door",
                        "value": "locked_door",
                        "comparator": "eq"
                    }
                ]
            }
        ],
        "rewards": [{
            "type": "set_flag",
            "target_entity": "player",
            "key": "door_unlocked",
            "value": True
        }]
    }
    
    # Register quest
    quest_system.register_quest(quest_def)
    
    # Create world state updates
    world_states = [
        # State 0: Quest registered, no progress
        {
            "entities": {
                "player": {
                    "flags": {},
                    "items": {},
                    "stats": {},
                    "location": "start"
                }
            },
            "quests": {},
            "time": 0
        },
        # State 1: Got the key (complete step1)
        {
            "entities": {
                "player": {
                    "flags": {},
                    "items": {"old_key": 1},
                    "stats": {},
                    "location": "cave"
                }
            },
            "quests": {},
            "time": 1
        },
        # State 2: At door with key (complete step2)
        {
            "entities": {
                "player": {
                    "flags": {},
                    "items": {"old_key": 1},
                    "stats": {},
                    "location": "locked_door"
                }
            },
            "quests": {},
            "time": 2
        }
    ]
    
    # Process each state
    for i, world in enumerate(world_states):
        print(f"\nStep {i}:")
        print(f"  Location: {world['entities']['player']['location']}")
        print(f"  Items: {world['entities']['player']['items']}")
        
        result = quest_system.tick(world, i)
        
        # Check quest state
        quest_state = result.get('quests', {}).get('lifecycle_test', {})
        if quest_state:
            print(f"  Quest state: {quest_state.get('state', 'unknown')}")
            
            # Check objectives
            for obj in quest_state.get('objectives', []):
                status = "✓" if obj.get('status') == 'satisfied' else "→" if obj.get('status') == 'pending' else "○"
                print(f"    {status} {obj.get('description')}")
    
    print("\n" + "=" * 50)
    print("✅ Lifecycle test complete!")
    
    return True

if __name__ == "__main__":
    test_quest_lifecycle()
