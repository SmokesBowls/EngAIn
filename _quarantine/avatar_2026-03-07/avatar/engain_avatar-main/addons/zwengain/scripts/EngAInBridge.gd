# EngAInBridge.gd - Real AI Co-Director Integration
extends Node

signal ai_decision_received(decision_data)
signal state_sync_complete()

var engain_request_file = "engain_request.json"
var engain_response_file = "engain_response.json" 
var file_watcher_timer: Timer
var last_response_time = 0.0

# Game state tracking
var current_game_state = {
    "characters": {},
    "world_state": {},
    "player_stats": {"level": 1, "entropy_mastery": 0.0},
    "narrative_threads": [],
    "entropy_level": 50.0,
    "current_scene": "cosmic_interface",
    "pending_decisions": [],
    "recent_actions": []
}

func _ready():
    # Set up file watcher for EngAIn responses
    file_watcher_timer = Timer.new()
    file_watcher_timer.wait_time = 0.1
    file_watcher_timer.timeout.connect(_check_for_ai_response)
    add_child(file_watcher_timer)
    file_watcher_timer.start()
    
    # Initialize game state
    initialize_game_state()
    
    print("🧠 EngAIn Bridge: Ready for AI co-direction")
    print("📡 Communication channel: JSON file exchange")

func initialize_game_state():
    """Initialize the game state with current scene data"""
    current_game_state["characters"] = {
        "player": {
            "name": "Consciousness",
            "role": "reality_manipulator", 
            "loyalty": 1.0,
            "abilities": ["entropy_sight", "dimensional_awareness"]
        },
        "dragon_council": {
            "count": 9,
            "aspects": ["Time", "Space", "Memory", "Dream", "Paradox", "Entropy", "Anchor", "Echo", "Transformation"],
            "collective_wisdom": 0.8,
            "cooperation_level": 0.9
        }
    }
    
    current_game_state["world_state"] = {
        "location": "Cosmic Command Center",
        "environment": "Ancient temple with energy streams and crowds",
        "akashic_flows_discovered": false,
        "reality_stability": 0.75,
        "dimensional_anchors": ["TimelineAnchor", "MandelaLock"],
        "active_phenomena": ["dragon_flight_patterns", "energy_currents", "crowd_movement"]
    }
    
    sync_with_snapshot_manager()

func sync_with_snapshot_manager():
    """Sync state with SnapshotManager if available"""
    var snapshot_manager = get_node_or_null("../SnapshotManager")
    if snapshot_manager:
        print("🔄 Syncing state with SnapshotManager")

func send_to_engain(player_input: String, additional_context: Dictionary = {}):
    """Send player input and game state to EngAIn for AI decision"""
    
    # Update recent actions
    current_game_state["recent_actions"].append(extract_action_type(player_input))
    if current_game_state["recent_actions"].size() > 5:
        # Keep only the last 5 actions
        var keep_count = 5
        var total_count = current_game_state["recent_actions"].size()
        var new_actions = []
        for i in range(total_count - keep_count, total_count):
            new_actions.append(current_game_state["recent_actions"][i])
        current_game_state["recent_actions"] = new_actions
    
    # Build comprehensive request
    var engain_request = {
        "player_input": player_input,
        "game_state": current_game_state.duplicate(true),
        "additional_context": additional_context,
        "timestamp": Time.get_unix_time_from_system(),
        "request_id": generate_request_id()
    }
    
    # Write request file for EngAIn
    var full_path = ProjectSettings.globalize_path("res://") + engain_request_file
    print("🔍 DEBUG: Trying to write to: ", full_path)
    
    var file = FileAccess.open(engain_request_file, FileAccess.WRITE)
    if file:
        var json_content = JSON.stringify(engain_request, "\t")
        file.store_string(json_content)
        file.close()
        print("🎯 Sent to EngAIn: ", player_input)
        print("📁 Request file written to: ", full_path)
        print("📝 File size: ", FileAccess.get_file_as_bytes(engain_request_file).size(), " bytes")
        print("📊 Game State - Entropy: %.1f, Tension: %.1f" % [
            current_game_state["entropy_level"],
            calculate_current_tension()
        ])
        
        # Verify file exists immediately after writing
        if FileAccess.file_exists(engain_request_file):
            print("✅ File exists after write")
        else:
            print("❌ File does NOT exist after write")
    else:
        print("❌ Failed to open file for writing: ", engain_request_file)
        print("❌ Error: ", FileAccess.get_open_error())

func extract_action_type(input_text: String) -> String:
    """Extract action type for recent actions tracking"""
    var text_lower = input_text.to_lower()
    
    if "activate" in text_lower or "use" in text_lower:
        return "ACTION_TAKEN"
    elif "look" in text_lower or "see" in text_lower or "observe" in text_lower:
        return "EXPLORATION"
    elif "talk" in text_lower or "ask" in text_lower or "say" in text_lower:
        return "COMMUNICATION"
    elif "where" in text_lower or "how" in text_lower or "what" in text_lower:
        return "INQUIRY"
    else:
        return "GENERAL_INPUT"

func calculate_current_tension() -> float:
    """Calculate current narrative tension for context"""
    var tension = 0.0
    tension += current_game_state["entropy_level"] * 0.4
    tension += current_game_state["pending_decisions"].size() * 8.0
    tension += current_game_state["narrative_threads"].size() * 5.0
    return min(100.0, tension)

func generate_request_id() -> String:
    """Generate unique request ID"""
    return "req_" + str(Time.get_unix_time_from_system()).replace(".", "_")

func _check_for_ai_response():
    """Check for EngAIn's response"""
    if FileAccess.file_exists(engain_response_file):
        print("📥 Found AI response file!")
        var file = FileAccess.open(engain_response_file, FileAccess.READ)
        if file:
            var response_text = file.get_as_text()
            file.close()
            
            var json = JSON.new()
            var parse_result = json.parse(response_text)
            
            if parse_result == OK:
                var ai_decision = json.data
                var response_time = ai_decision.get("timestamp", 0.0)
                
                if response_time > last_response_time:
                    last_response_time = response_time
                    DirAccess.remove_absolute(engain_response_file)
                    
                    # Process AI decision
                    process_ai_decision(ai_decision)
                    
                    print("🧠 EngAIn Decision: ", ai_decision.get("action_type", "unknown"))
                    print("💭 Reasoning: ", ai_decision.get("reasoning", "").substr(0, 100), "...")

func process_ai_decision(ai_decision: Dictionary):
    """Process and apply EngAIn's decision"""
    
    # Apply state changes from AI
    var state_changes = ai_decision.get("state_changes", {})
    apply_state_changes(state_changes)
    
    # Update entropy based on AI decision
    var entropy_impact = ai_decision.get("entropy_impact", 0.0)
    if entropy_impact != 0.0:
        current_game_state["entropy_level"] += entropy_impact
        current_game_state["entropy_level"] = clampf(current_game_state["entropy_level"], 0.0, 100.0)
        print("⚡ Entropy changed by %.1f to %.1f" % [entropy_impact, current_game_state["entropy_level"]])
    
    # Add to narrative threads if this creates new story elements
    var action_type = ai_decision.get("action_type", "")
    if action_type in ["NARRATIVE_BRANCH", "MYSTERY_REVEAL", "CHARACTER_DEVELOPMENT"]:
        add_narrative_thread(ai_decision)
    
    # Emit signal with AI decision data
    ai_decision_received.emit(ai_decision)

func apply_state_changes(changes: Dictionary):
    """Apply state changes from EngAIn"""
    
    # Update world state
    if changes.has("world_state"):
        for key in changes["world_state"]:
            current_game_state["world_state"][key] = changes["world_state"][key]
            print("🌍 World updated: ", key, " = ", changes["world_state"][key])
    
    # Update characters
    if changes.has("characters"):
        for char_name in changes["characters"]:
            if not current_game_state["characters"].has(char_name):
                current_game_state["characters"][char_name] = {}
            
            for prop in changes["characters"][char_name]:
                current_game_state["characters"][char_name][prop] = changes["characters"][char_name][prop]
            print("👤 Character updated: ", char_name)
    
    # Update player stats
    if changes.has("player_stats"):
        for stat in changes["player_stats"]:
            current_game_state["player_stats"][stat] = changes["player_stats"][stat]
            print("📊 Player stat updated: ", stat, " = ", changes["player_stats"][stat])

func add_narrative_thread(ai_decision: Dictionary):
    """Add new narrative thread based on AI decision"""
    var thread = {
        "id": generate_request_id(),
        "type": ai_decision.get("action_type", "unknown"),
        "description": ai_decision.get("director_analysis", "AI-generated narrative thread"),
        "urgency": calculate_thread_urgency(ai_decision),
        "created_time": Time.get_unix_time_from_system()
    }
    
    current_game_state["narrative_threads"].append(thread)
    print("📖 New narrative thread: ", thread["type"])

func calculate_thread_urgency(ai_decision: Dictionary) -> float:
    """Calculate urgency of narrative thread"""
    var action_type = ai_decision.get("action_type", "")
    var urgency_map = {
        "TENSION_ESCALATION": 0.9,
        "CONSEQUENCE_TRIGGER": 0.8,
        "ENTROPY_SHIFT": 0.7,
        "PLAYER_CHOICE": 0.6,
        "NARRATIVE_BRANCH": 0.5,
        "CHARACTER_DEVELOPMENT": 0.4,
        "MYSTERY_REVEAL": 0.3,
        "WORLD_BUILDING": 0.2
    }
    return urgency_map.get(action_type, 0.5)

# Public API functions
func get_current_entropy() -> float:
    return current_game_state["entropy_level"]

func get_narrative_tension() -> float:
    return calculate_current_tension()

func add_pending_decision(decision_description: String):
    current_game_state["pending_decisions"].append({
        "description": decision_description,
        "timestamp": Time.get_unix_time_from_system()
    })
    print("⚠️ Pending decision added: ", decision_description)

func resolve_pending_decision(index: int):
    if index < current_game_state["pending_decisions"].size():
        var resolved = current_game_state["pending_decisions"][index]
        current_game_state["pending_decisions"].remove_at(index)
        print("✅ Decision resolved: ", resolved["description"])

func update_character_relationship(char_name: String, property: String, value):
    if not current_game_state["characters"].has(char_name):
        current_game_state["characters"][char_name] = {}
    
    current_game_state["characters"][char_name][property] = value
    print("💫 Character relationship updated: ", char_name, ".", property, " = ", value)

func trigger_world_event(event_name: String, event_data: Dictionary = {}):
    current_game_state["world_state"][event_name + "_triggered"] = true
    current_game_state["world_state"][event_name + "_data"] = event_data
    print("🌟 World event triggered: ", event_name)

# Debug functions
func print_current_state():
    print("=== CURRENT GAME STATE ===")
    print("Entropy: ", current_game_state["entropy_level"])
    print("Scene: ", current_game_state["current_scene"])
    print("Characters: ", current_game_state["characters"].keys())
    print("Narrative Threads: ", current_game_state["narrative_threads"].size())
    print("Pending Decisions: ", current_game_state["pending_decisions"].size())
    print("Recent Actions: ", current_game_state["recent_actions"])
    print("=========================")
