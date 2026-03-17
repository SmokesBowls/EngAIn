extends CharacterBody2D

@onready var sprite = $AnimatedSprite2D
@onready var speech_label = $Label
@onready var input_box = $"../LineEdit"
@onready var snapshot_manager = $"../SnapshotManager"

# Don't use @onready for engain_bridge - find it manually
var engain_bridge

# Flying variables
const SPEED = 100.0
var flight_time = 0.0
var center_position = Vector2()

# AI Director integration
var waiting_for_ai = false
var fallback_responses = {
    "greeting": "Ancient draconic consciousness acknowledges your presence at this cosmic nexus.",
    "location": "We exist within the Cosmic Command Center, where reality bends to focused will.",
    "dragons": "Nine aspects of cosmic control manifest here - each dragon embodies fundamental forces.",
    "default": "The interface processes your intent through layers of draconic wisdom and cosmic understanding."
}

func send_to_ai_director(player_input: String):
    var http = HTTPRequest.new()
    add_child(http)
    
    var url = "http://localhost:5000/engain"
    var headers = ["Content-Type: application/json"]
    var data = JSON.stringify({"input": player_input})
    
    http.request(url, headers, HTTPClient.METHOD_POST, data)
    
func _on_line_edit_text_submitted(text: String):
    if not text.is_empty():
        print("🎮 Player input: ", text)
        
        # Capture snapshot for visual context
        if snapshot_manager:
            snapshot_manager.capture_event("message_received", {"command": text})
        
        # Send to EngAIn for AI co-direction
        send_to_ai_director(text)
        
        input_box.clear()
        input_box.placeholder_text = "EngAIn is thinking..."
        
        # Set timeout for AI response
        setup_ai_timeout()
    
    if not engain_bridge:
        print("❌ ERROR: EngAIn bridge is null!")
        waiting_for_ai = false
        dragon_speak("EngAIn bridge not connected - using fallback.")
        return
    
    # Add visual context if available
    var additional_context = {}
    if snapshot_manager:
        var stats = snapshot_manager.get_storage_stats()
        additional_context["visual_snapshots_available"] = stats.total_snapshots > 0
        additional_context["recent_visual_events"] = ["dragon_flight", "energy_streams", "crowd_activity"]
    
    print("🔍 DEBUG: About to call engain_bridge.send_to_engain...")
    
    # Send to EngAIn
    var fallback = get_fallback_response(input_box.text if input_box else "")
    
    print("🔍 DEBUG: Called engain_bridge.send_to_engain successfully")

func setup_ai_timeout():
    """Setup timeout for AI response"""
    var timeout_timer = Timer.new()
    timeout_timer.wait_time = 10.0  # 10 second timeout
    timeout_timer.one_shot = true
    timeout_timer.timeout.connect(_on_ai_timeout)
    add_child(timeout_timer)
    timeout_timer.start()

func _on_ai_timeout():
    """Handle AI timeout with fallback"""
    if waiting_for_ai:
        waiting_for_ai = false
        var fallback = get_fallback_response(input_box.text if input_box else "")
        dragon_speak(fallback)
        input_box.placeholder_text = "send command here"
        print("⏰ AI timeout - used fallback response")

func get_fallback_response(input_text: String) -> String:
    """Get fallback response when AI is unavailable"""
    var text_lower = input_text.to_lower()
    
    if "hi" in text_lower or "hello" in text_lower:
        return fallback_responses["greeting"]
    elif "where" in text_lower:
        return fallback_responses["location"]
    elif "dragon" in text_lower and "many" in text_lower:
        return fallback_responses["dragons"]
    else:
        return fallback_responses["default"]

func _ready():
    sprite.play("idle_flap")
    speech_label.text = "EngAIn consciousness initializing..."
    center_position = global_position
    
    print("🔍 DEBUG: Dragon _ready() called")
    print("🔍 DEBUG: Looking for EngAInBridge...")
    
    # Try multiple possible paths for the EngAIn bridge
    var possible_paths = [
        "EngAInBridge",           # Child of dragon
        "../EngAInBridge",        # Sibling of dragon  
        "/root/Node2D/EngAInBridge",  # Full path
        "/root/EngAInBridge"      # Root level
    ]
    
    for path in possible_paths:
        print("🔍 Trying path: ", path)
        engain_bridge = get_node_or_null(path)
        if engain_bridge:
            print("✅ Found EngAIn bridge at: ", path)
            break
    
    # Connect to EngAIn AI Director
    if engain_bridge:
        print("✅ EngAIn bridge connected!")
        engain_bridge.ai_decision_received.connect(_on_ai_decision)
        print("🧠 Connected to EngAIn AI Co-Director")
    else:
        print("❌ ERROR: EngAInBridge not found at any path!")
        print("🔍 Available children of dragon: ", get_children())
        print("🔍 Available siblings: ", get_parent().get_children() if get_parent() else "No parent")
        push_error("EngAInBridge not found - AI director will not work!")
    
    if snapshot_manager:
        print("📸 SnapshotManager connected for visual context")
        snapshot_manager.capture_event("scene_loaded", {"scene": "EngAInDragon", "ai_director": true})
    
    # Initial state setup
    setup_initial_state()
    
    print("🐉 EngAIn Dragon: AI Co-Director integration ready!")

func setup_initial_state():
    """Setup initial game state for AI director"""
    if engain_bridge:
        # Set initial scene context
        engain_bridge.current_game_state["current_scene"] = "cosmic_interface_with_dragons"
        engain_bridge.current_game_state["entropy_level"] = 45.0  # Stable but dynamic
        
        # Add environmental context
        engain_bridge.trigger_world_event("session_started", {
            "environment": "ancient_temple_with_energy_streams",
            "dragon_count": 9,
            "crowd_present": true,
            "energy_flows_active": true
        })

func _physics_process(delta):
    # Dragon flight pattern
    flight_time += delta
    var radius = 100.0
    var circle_speed = 1.0
    
    var target_x = center_position.x + cos(flight_time * circle_speed) * radius
    var target_y = center_position.y + sin(flight_time * circle_speed) * radius
    var target_position = Vector2(target_x, target_y)
    
    var direction = (target_position - global_position).normalized()
    velocity = direction * SPEED
    move_and_slide()

func _on_ai_decision(ai_decision_data: Dictionary):
    """Handle decision from EngAIn AI Director"""
    waiting_for_ai = false
    
    var narrative_response = ai_decision_data.get("narrative_response", "The cosmic interface hums with contemplation.")
    var action_type = ai_decision_data.get("action_type", "OBSERVATION")
    var director_analysis = ai_decision_data.get("director_analysis", "")
    
    # Apply any special effects based on action type
    apply_ai_decision_effects(action_type, ai_decision_data)
    
    # Speak the AI-generated response
    dragon_speak(narrative_response)
    
    # Reset input placeholder
    input_box.placeholder_text = "send command here"
    
    print("🎭 AI Director Action: ", action_type)
    if director_analysis:
        print("🧠 Analysis: ", director_analysis.substr(0, 100), "...")

func apply_ai_decision_effects(action_type: String, decision_data: Dictionary):
    """Apply visual/mechanical effects based on AI decision"""
    
    match action_type:
        "ENTROPY_SHIFT":
            # Visual effect for entropy changes
            var entropy_impact = decision_data.get("entropy_impact", 0.0)
            if abs(entropy_impact) > 3.0:
                create_entropy_effect(entropy_impact)
        
        "TENSION_ESCALATION":
            # Dramatic visual effect
            create_tension_effect()
        
        "MYSTERY_REVEAL":
            # Revelation effect
            create_revelation_effect()
        
        "CHARACTER_DEVELOPMENT":
            # Character growth effect
            create_character_effect()

func create_entropy_effect(impact: float):
    """Visual effect for entropy changes"""
    var color = Color.RED if impact > 0 else Color.BLUE
    sprite.modulate = color
    var tween = create_tween()
    tween.tween_property(sprite, "modulate", Color.WHITE, 1.0)
    print("⚡ Entropy effect: ", impact)

func create_tension_effect():
    """Visual effect for tension escalation"""
    sprite.modulate = Color.ORANGE
    var tween = create_tween()
    tween.tween_property(sprite, "modulate", Color.WHITE, 0.8)
    print("🔥 Tension escalation effect")

func create_revelation_effect():
    """Visual effect for mystery reveals"""
    sprite.modulate = Color.CYAN
    var tween = create_tween()
    tween.tween_property(sprite, "modulate", Color.WHITE, 1.2)
    print("💡 Mystery revelation effect")

func create_character_effect():
    """Visual effect for character development"""
    sprite.modulate = Color.YELLOW
    var tween = create_tween()
    tween.tween_property(sprite, "modulate", Color.WHITE, 1.0)
    print("✨ Character development effect")

func dragon_speak(text: String):
    print("🐉 Dragon (EngAIn): ", text)
    
    # Capture AI-generated speech
    if snapshot_manager:
        snapshot_manager.capture_event("ai_dragon_spoke", {
            "text": text,
            "ai_generated": true,
            "director_active": true
        })
    
    # Display text
    speech_label.text = text
    
    # Speaking effect
    sprite.modulate = Color.YELLOW
    var tween = create_tween()
    tween.tween_property(sprite, "modulate", Color.WHITE, 0.5)
    
    # Auto-clear based on text length
    var display_time = max(3.0, min(10.0, text.length() * 0.05))
    await get_tree().create_timer(display_time).timeout
    speech_label.text = "EngAIn Dragon awaits your input..."

func _input(event):
    if event is InputEventKey and event.pressed:
        match event.keycode:
            KEY_F12:
                # Manual snapshot
                if snapshot_manager:
                    snapshot_manager.manual_snapshot("Manual snapshot with AI director active")
                    print("📸 Manual snapshot captured")
            
            KEY_F11:
                # Show AI director stats
                if engain_bridge:
                    engain_bridge.print_current_state()
                    print("🧠 Current Entropy: ", engain_bridge.get_current_entropy())
                    print("📈 Narrative Tension: ", engain_bridge.get_narrative_tension())
            
            KEY_F10:
                # Trigger AI-driven event
                if engain_bridge:
                    engain_bridge.add_pending_decision("Player requested manual AI event trigger")
                    engain_bridge.send_to_engain("surprise me with something interesting", {
                        "manual_trigger": true,
                        "player_request": "surprise_event"
                    })
                    print("🎲 Requested surprise event from AI director")

# Public API for other systems to interact with AI director
func request_ai_decision(context: String, additional_data: Dictionary = {}):
    """Allow other systems to request AI director input"""
    if engain_bridge:
        engain_bridge.send_to_engain(context, additional_data)

func get_ai_director_state() -> Dictionary:
    """Get current AI director state"""
    if engain_bridge:
        return {
            "entropy": engain_bridge.get_current_entropy(),
            "tension": engain_bridge.get_narrative_tension(),
            "waiting_for_ai": waiting_for_ai
        }
    return {}

func trigger_ai_event(event_name: String, event_data: Dictionary = {}):
    """Trigger an event that the AI director should respond to"""
    if engain_bridge:
        engain_bridge.trigger_world_event(event_name, event_data)
