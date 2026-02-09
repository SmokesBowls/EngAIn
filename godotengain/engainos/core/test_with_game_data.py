# Test with your actual game entities and locations
from quest3d_integration import Quest3DIntegration

# Load your actual game world state
def load_game_world():
    """Load your actual game world (customize this)"""
    return {
        "entities": {
            "player": {
                "flags": {},
                "items": {"sword": 1, "potion": 3},
                "stats": {"health": 100, "mana": 50},
                "location": "town_square"
            },
            "npc_merchant": {
                "flags": {},
                "items": {},
                "stats": {},
                "location": "market"
            }
        },
        "quests": {},
        "time": 0
    }

# Create a quest that uses your game's actual locations/items
quest_def = {
    "id": "game_integration_test",
    "name": "Game Integration Test",
    "description": "Test with actual game data",
    "objectives": [{
        "id": "visit_market",
        "description": "Go to the market",
        "conditions": [{
            "type": "at_location",
            "target_entity": "player",
            "key": "market",
            "value": "market",
            "comparator": "eq"
        }]
    }],
    "rewards": []
}

# Run the test
quest_system = Quest3DIntegration()
quest_system.register_quest(quest_def)

world = load_game_world()
result = quest_system.tick(world, 1.0)

print(f"World after tick: {result.keys()}")
print(f"Player location: {result['entities']['player']['location']}")

# Move player to market
world['entities']['player']['location'] = 'market'
result2 = quest_system.tick(world, 2.0)

quest_state = result2.get('quests', {}).get('game_integration_test', {})
print(f"\nQuest state after moving to market: {quest_state.get('state', 'unknown')}")
