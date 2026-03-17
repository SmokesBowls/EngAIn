from quest3d_integration import Quest3DIntegration, handle_quest_http_request
import json

def test_http_requests():
    """Test the HTTP bridge that Godot would use"""
    print("🌐 Testing HTTP Bridge (Godot Simulation)")
    print("=" * 50)
    
    quest_system = Quest3DIntegration()
    
    # Simulate Godot sending quest registration
    register_request = {
        "method": "POST",
        "path": "/quest/register",
        "body": json.dumps({
            "quest": {
                "id": "godot_quest",
                "name": "From Godot",
                "description": "Quest registered from Godot UI",
                "objectives": [{
                    "id": "test_objective",
                    "description": "Test objective",
                    "conditions": [{
                        "type": "flag_set",
                        "target_entity": "player",
                        "key": "test_flag",
                        "value": True,
                        "comparator": "eq"
                    }]
                }],
                "rewards": []
            }
        })
    }
    
    print("1. Handling registration request...")
    response = handle_quest_http_request(quest_system, register_request)
    print(f"   Response: {json.dumps(response, indent=2)}")
    
    # Simulate Godot requesting active quests
    get_request = {
        "method": "GET",
        "path": "/quests/active"
    }
    
    print("\n2. Handling GET active quests request...")
    response = handle_quest_http_request(quest_system, get_request)
    print(f"   Response status: {response.get('status')}")
    
    # Simulate Godot updating world state
    update_request = {
        "method": "POST",
        "path": "/quest/tick",
        "body": json.dumps({
            "world": {
                "entities": {
                    "player": {
                        "flags": {"test_flag": True},
                        "items": {},
                        "stats": {},
                        "location": "test"
                    }
                },
                "quests": {},
                "time": 0
            },
            "delta_time": 1.0
        })
    }
    
    print("\n3. Handling tick update...")
    response = handle_quest_http_request(quest_system, update_request)
    print(f"   Response keys: {list(response.keys())}")
    
    print("\n" + "=" * 50)
    print("✅ HTTP bridge test complete!")
    
    return True

if __name__ == "__main__":
    test_http_requests()
