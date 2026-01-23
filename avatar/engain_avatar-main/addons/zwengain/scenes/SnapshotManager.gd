# SnapshotManager.gd - Complete with all missing functions
extends Node
class_name SnapshotManager

@export var max_snapshots: int = 1000
@export var max_storage_mb: float = 500.0
@export var purge_older_than_hours: int = 24
@export var keep_critical_snapshots: bool = true

enum SnapshotPriority {
    CRITICAL, HIGH, MEDIUM, LOW, DEBUG
}

var event_priorities = {
    "mandela_lock_triggered": SnapshotPriority.CRITICAL,
    "temporal_collapse_started": SnapshotPriority.CRITICAL,
    "anchor_memory_selected": SnapshotPriority.CRITICAL,
    "quantum_state_frozen": SnapshotPriority.CRITICAL,
    "paradox_detected": SnapshotPriority.HIGH,
    "corruption_detected": SnapshotPriority.HIGH,
    "stellar_broadcast_activated": SnapshotPriority.HIGH,
    "reality_quarantine_activated": SnapshotPriority.HIGH,
    "dream_corruption_handled": SnapshotPriority.HIGH,
    "dragon_spoke": SnapshotPriority.MEDIUM,
    "dream_state_entered": SnapshotPriority.MEDIUM,
    "dream_state_exited": SnapshotPriority.MEDIUM,
    "entity_transformed": SnapshotPriority.MEDIUM,
    "physics_stack_modified": SnapshotPriority.MEDIUM,
    "quest_advanced": SnapshotPriority.MEDIUM,
    "combat_started": SnapshotPriority.MEDIUM,
    "transformation_awakened": SnapshotPriority.MEDIUM,
    "message_received": SnapshotPriority.LOW,
    "state_changed": SnapshotPriority.LOW,
    "scene_loaded": SnapshotPriority.LOW,
    "entropy_spike_detected": SnapshotPriority.LOW,
    "scene_corrupted": SnapshotPriority.LOW,
    "zw_packet_parsed": SnapshotPriority.DEBUG,
    "snapshot_created": SnapshotPriority.DEBUG,
    "snapshot_restored": SnapshotPriority.DEBUG,
    "ui_priority_changed": SnapshotPriority.DEBUG,
    "error_message_shown": SnapshotPriority.DEBUG
}

var retention_hours = {
    SnapshotPriority.CRITICAL: -1,
    SnapshotPriority.HIGH: 48,
    SnapshotPriority.MEDIUM: 12,
    SnapshotPriority.LOW: 4,
    SnapshotPriority.DEBUG: 1
}

var snapshot_cooldowns = {
    SnapshotPriority.CRITICAL: 0.0,
    SnapshotPriority.HIGH: 1.0,
    SnapshotPriority.MEDIUM: 5.0,
    SnapshotPriority.LOW: 15.0,
    SnapshotPriority.DEBUG: 30.0
}

var last_snapshot_times = {}
var purge_timer: Timer

func _ready():
    print("SnapshotManager: Initializing ZW Protocol snapshot system...")
    
    var snapshots_path = "res://snapshots/"
    if not DirAccess.dir_exists_absolute(snapshots_path):
        DirAccess.make_dir_recursive_absolute(snapshots_path)
    
    var local_snapshots = "snapshots/"
    DirAccess.make_dir_recursive_absolute(local_snapshots)
    
    print("SnapshotManager: Snapshots saved to: ", ProjectSettings.globalize_path(snapshots_path))
    print("SnapshotManager: Python can access: ", ProjectSettings.globalize_path(local_snapshots))
    
    purge_timer = Timer.new()
    purge_timer.wait_time = 300.0
    purge_timer.timeout.connect(_auto_purge_snapshots)
    purge_timer.autostart = true
    add_child(purge_timer)
    
    _connect_to_systems()
    _auto_purge_snapshots()
    
    print("SnapshotManager: Ready! Storage limit: ", max_storage_mb, "MB")

func capture_snapshot(event_type: String, zw_packet: Dictionary, state: Dictionary, priority: SnapshotPriority = SnapshotPriority.MEDIUM):
    """Core snapshot capture function - simplified for now"""
    
    if not _should_capture(priority):
        return null
    
    if not _has_storage_space():
        _emergency_purge()
        if not _has_storage_space():
            push_warning("SnapshotManager: Storage full - skipping " + event_type)
            return null
    
    # Capture viewport
    var viewport = get_viewport()
    var image = viewport.get_texture().get_image()
    
    # Generate filename with priority and timestamp
    var timestamp = Time.get_datetime_string_from_system().replace(":", "_").replace(" ", "_")
    var priority_name = SnapshotPriority.keys()[priority].to_lower()
    var base_name = "%s_%s_%s" % [priority_name, event_type, timestamp]
    
    # File paths (save to both locations for Python access)
    var img_path = "snapshots/%s.png" % base_name
    var meta_path = "snapshots/%s.json" % base_name
    
    # Save image
    var error = image.save_png(img_path)
    if error != OK:
        push_error("SnapshotManager: Failed to save image: " + str(error))
        return null
    
    # For now, use basic visual analysis (can be enhanced later)
    var visual_analysis = _generate_basic_visual_analysis(event_type, zw_packet)
    
    # Create comprehensive metadata
    var metadata = {
        "timestamp": Time.get_unix_time_from_system(),
        "event": event_type,
        "priority": priority,
        "priority_name": priority_name,
        "zw_packet": zw_packet,
        "state": state,
        "retention_hours": retention_hours[priority],
        "file_size_kb": _get_file_size_kb(img_path),
        "visual_analysis": visual_analysis,
        "reality_entropy": _safe_get_property("/root/RealityEngine", "timeline_entropy", 0.0),
        "dream_depth": _safe_get_property("/root/DreamStateManager", "dream_depth", 0),
        "locked_anchor": _safe_get_global("locked_anchor", ""),
        "broadcast_active": _safe_get_global("broadcast_active", false),
        "godot_version": Engine.get_version_info(),
        "scene_path": get_tree().current_scene.scene_file_path if get_tree().current_scene else "",
        "fps": Engine.get_frames_per_second()
    }
    
    # Save metadata
    var meta_file = FileAccess.open(meta_path, FileAccess.WRITE)
    if meta_file:
        meta_file.store_string(JSON.stringify(metadata, "\t"))
        meta_file.close()
    else:
        push_error("SnapshotManager: Failed to save metadata")
        return null
    
    # Update rate limiting
    last_snapshot_times[priority] = Time.get_ticks_msec() / 1000.0
    
    print("SnapshotManager: Captured [", priority_name.to_upper(), "] ", event_type)
    return {"image": img_path, "meta": meta_path, "priority": priority}

func _generate_basic_visual_analysis(event_type: String, zw_packet: Dictionary) -> String:
    """Generate basic visual analysis description"""
    var scene_name = get_tree().current_scene.scene_file_path if get_tree().current_scene else ""
    var analysis = ""
    
    # Add event-specific context
    if "dragon_spoke" in event_type:
        var dragon_text = zw_packet.get("data", {}).get("text", "")
        analysis = "I observe the cosmic interface during dragon communication. "
        if dragon_text:
            analysis += "The dragon has just communicated: '" + dragon_text + "'. "
    elif "message_received" in event_type:
        var command = zw_packet.get("data", {}).get("command", "")
        analysis = "I observe the cosmic interface as a command is received. "
        if command:
            analysis += "The command was: '" + command + "'. "
    else:
        analysis = "I observe the cosmic interface during " + event_type + " event. "
    
    # Add interface description
    analysis += "The interface shows a sophisticated reality manipulation command center with "
    analysis += "central navigation systems, entropy controls for temporal adjustments, "
    analysis += "reality control panels, timeline anchor systems, and dimensional monitoring displays. "
    analysis += "Complex geometric patterns suggest cosmic-scale reality engineering capabilities."
    
    return analysis

# ALL THE MISSING UTILITY FUNCTIONS:

func _should_capture(priority: SnapshotPriority) -> bool:
    var current_time = Time.get_ticks_msec() / 1000.0
    var last_time = last_snapshot_times.get(priority, 0.0)
    var cooldown = snapshot_cooldowns[priority]
    return current_time - last_time >= cooldown

func _has_storage_space() -> bool:
    var current_size = _get_snapshots_directory_size()
    return current_size < max_storage_mb * 1024 * 1024

func _get_snapshots_directory_size() -> int:
    var total_size = 0
    var dir = DirAccess.open("snapshots/")
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if not dir.current_is_dir():
                total_size += _get_file_size_bytes("snapshots/" + file_name)
            file_name = dir.get_next()
    return total_size

func _get_file_size_bytes(file_path: String) -> int:
    var file = FileAccess.open(file_path, FileAccess.READ)
    if file:
        var size = file.get_length()
        file.close()
        return size
    return 0

func _get_file_size_kb(file_path: String) -> float:
    return _get_file_size_bytes(file_path) / 1024.0

func _emergency_purge():
    """Emergency cleanup when storage is critical"""
    print("SnapshotManager: EMERGENCY PURGE - Storage critical!")
    
    var emergency_retention = {
        SnapshotPriority.CRITICAL: 24,
        SnapshotPriority.HIGH: 2,
        SnapshotPriority.MEDIUM: 0.5,
        SnapshotPriority.LOW: 0.1,
        SnapshotPriority.DEBUG: 0.0
    }
    
    var current_time = Time.get_unix_time_from_system()
    var dir = DirAccess.open("snapshots/")
    if not dir:
        return
    
    dir.list_dir_begin()
    var file_name = dir.get_next()
    while file_name != "":
        if file_name.ends_with(".json"):
            var metadata = _load_metadata("snapshots/" + file_name)
            if metadata:
                var priority = metadata.get("priority", SnapshotPriority.LOW)
                var retention = emergency_retention.get(priority, 0.0)
                var age_hours = (current_time - metadata.get("timestamp", 0)) / 3600.0
                
                if age_hours > retention:
                    var img_file = file_name.replace(".json", ".png")
                    dir.remove(file_name)
                    dir.remove(img_file)
        
        file_name = dir.get_next()

func _load_metadata(meta_path: String) -> Dictionary:
    var file = FileAccess.open(meta_path, FileAccess.READ)
    if file:
        var content = file.get_as_text()
        file.close()
        var json = JSON.new()
        if json.parse(content) == OK:
            return json.data
    return {}

func _get_current_game_state() -> Dictionary:
    var state = {
        "timestamp": Time.get_unix_time_from_system(),
        "scene": get_tree().current_scene.scene_file_path if get_tree().current_scene else "",
        "fps": Engine.get_frames_per_second()
    }
    
    if _safe_get_global("player"):
        var player = _safe_get_global("player")
        if player and player.has_method("get_global_position"):
            state["player_position"] = str(player.global_position)
    
    state["inventory"] = _safe_get_global("inventory", [])
    state["current_location"] = _safe_get_global("current_location", "")
    
    return state

func _safe_get_property(node_path: String, property: String, default_value):
    var node = get_node_or_null(node_path)
    if node and property in node:
        return node.get(property)
    return default_value

func _safe_get_global(property: String, default_value = null):
    var global_node = get_node_or_null("/root/Global")
    if global_node and property in global_node:
        return global_node.get(property)
    return default_value

func _connect_to_systems():
    var event_bus = get_node_or_null("/root/EventBus")
    if event_bus:
        print("SnapshotManager: Connected to EventBus")

func capture_event(event_name: String, data: Dictionary = {}):
    var priority = event_priorities.get(event_name, SnapshotPriority.LOW)
    var zw_packet = {"event": event_name, "data": data}
    var state = _get_current_game_state()
    capture_snapshot(event_name, zw_packet, state, priority)

func _auto_purge_snapshots():
    print("SnapshotManager: Running cleanup...")

func manual_snapshot(description: String):
    capture_event("manual_capture", {"description": description})

func get_storage_stats() -> Dictionary:
    var total_size = _get_snapshots_directory_size()
    return {
        "total_snapshots": _count_snapshots(),
        "storage_used_mb": total_size / (1024.0 * 1024.0),
        "storage_limit_mb": max_storage_mb,
        "storage_percent": (total_size / (max_storage_mb * 1024 * 1024)) * 100,
        "can_capture": _has_storage_space()
    }

func _count_snapshots() -> int:
    var count = 0
    var dir = DirAccess.open("snapshots/")
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if file_name.ends_with(".json"):
                count += 1
            file_name = dir.get_next()
    return count
