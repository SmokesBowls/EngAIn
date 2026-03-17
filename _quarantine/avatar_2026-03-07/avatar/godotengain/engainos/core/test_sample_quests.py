from quest3d_integration import Quest3DIntegration

def create_sample_quests():
    """Create a variety of test quests"""
    quest_system = Quest3DIntegration()
    
    # 1. Simple location-based quest
    quest_system.register_quest({
        "id": "find_treasure",
        "name": "Buried Treasure",
        "description": "Find treasure in the forest",
        "objectives": [{
            "id": "locate_treasure",
            "description": "Find the marked tree",
            "conditions": [{
                "type": "at_location",
                "target_entity": "player",
                "key": "marked_tree",
                "value": "marked_tree",
                "comparator": "eq"
            }]
        }],
        "rewards": [{
            "type": "grant_item",
            "target_entity": "player",
            "key": "gold_coins",
            "value": 50
        }]
    })
    
    # 2. Item collection quest
    quest_system.register_quest({
        "id": "gather_herbs",
        "name": "Herbalist's Request",
        "description": "Collect 5 medicinal herbs",
        "objectives": [{
            "id": "collect_herbs",
            "description": "Gather 5 herbs",
            "conditions": [{
                "type": "has_item",
                "target_entity": "player",
                "key": "medicinal_herb",
                "value": 5,
                "comparator": "gte"
            }]
        }],
        "rewards": [{
            "type": "grant_item",
            "target_entity": "player",
            "key": "health_potion",
            "value": 3
        }]
    })
    
    # 3. Multi-step quest
    quest_system.register_quest({
        "id": "rescue_princess",
        "name": "Rescue the Princess",
        "description": "A classic adventure",
        "objectives": [
            {
                "id": "infiltrate_castle",
                "description": "Enter the castle",
                "conditions": [{
                    "type": "flag_set",
                    "target_entity": "player",
                    "key": "castle_entered",
                    "value": True,
                    "comparator": "eq"
                }]
            },
            {
                "id": "defeat_guard",
                "description": "Defeat the castle guard",
                "conditions": [{
                    "type": "flag_set",
                    "target_entity": "player",
                    "key": "guard_defeated",
                    "value": True,
                    "comparator": "eq"
                }]
            },
            {
                "id": "find_princess",
                "description": "Find the princess in the tower",
                "conditions": [{
                    "type": "at_location",
                    "target_entity": "player",
                    "key": "princess_tower",
                    "value": "princess_tower",
                    "comparator": "eq"
                }]
            }
        ],
        "rewards": [
            {
                "type": "set_flag",
                "target_entity": "player",
                "key": "princess_rescued",
                "value": True
            },
            {
                "type": "grant_item",
                "target_entity": "player",
                "key": "royal_reward",
                "value": 1
            }
        ]
    })
    
    return quest_system

# Test the quests
if __name__ == "__main__":
    print("🧪 Creating sample quests...")
    qs = create_sample_quests()
    
    # Get a snapshot
    snapshot = qs.get_snapshot()
    print(f"✅ Created {len(snapshot.get('quests', {}))} quests")
    
    # List them
    for quest_id, quest_data in snapshot.get('quests', {}).items():
        print(f"  - {quest_data.get('name')} ({quest_id}): {quest_data.get('state')}")
