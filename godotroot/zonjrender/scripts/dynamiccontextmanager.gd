# DynamicContextManager.gd - Fixed node path
extends Node
class_name DynamicContextManager

signal context_updated(new_context: Dictionary)

var current_context = {}
var snapshot_manager: SnapshotManager
var last_visual_analysis = ""
var context_update_timer: Timer

func _ready():
    # Find SnapshotManager - try multiple possible paths
    snapshot_manager = get_node_or_null("../SnapshotManager")  # Sibling in scene
    if not snapshot_manager:
        snapshot_manager = get_node_or_null("/root/Node2D/SnapshotManager")  # Full path
    if not snapshot_manager:
        snapshot_manager = get_node_or_null("/root/SnapshotManager")  # Root level
    if not snapshot_manager:
        # Search for it in the scene tree
        snapshot_manager = _find_snapshot_manager(get_tree().root)
    
    if not snapshot_manager:
        print("WARNING: DynamicContextManager: SnapshotManager not found! Visual context disabled.")
        return
    else:
        print("DynamicContextManager: Found SnapshotManager at: ", snapshot_manager.get_path())
    
    # Set up automatic context updates - MUCH less frequent
    context_update_timer = Timer.new()
    context_update_timer.wait_time = 30.0  # Update every 30 seconds instead of 2
    context_update_timer.timeout.connect(_update_context_from_visuals)
    context_update_timer.autostart = true
    add_child(context_update_timer)
    
    print("DynamicContextManager: Ready to replace static templates!")

func _find_snapshot_manager(node: Node) -> SnapshotManager:
    """Recursively search for SnapshotManager in scene tree"""
    if node is SnapshotManager:
        return node
    
    for child in node.get_children():
        var result = _find_snapshot_manager(child)
        if result:
            return result
    
    return null

func _update_context_from_visuals():
    """Replace static context with current visual analysis"""
    if not snapshot_manager:
        return
    
    # Get latest screenshot analysis
    var latest_analysis = get_latest_visual_analysis()
    if latest_analysis.is_empty():
        return
    
    # Build dynamic context from what we actually see
    var new_context = {
        "location": extract_location_from_visual(latest_analysis),
        "environment": extract_environment_from_visual(latest_analysis),
        "interface_elements": extract_interface_elements(latest_analysis),
        "visual_description": latest_analysis,
        "timestamp": Time.get_unix_time_from_system()
    }
    
    # Only update if context actually changed
    if new_context != current_context:
        current_context = new_context
        context_updated.emit(new_context)
        print("DynamicContextManager: Updated context from visual analysis")

func get_latest_visual_analysis() -> String:
    """Get the most recent visual analysis from snapshots"""
    # Use project-relative path where Python saves screenshots
    var snapshots_dir = "snapshots/"
    
    if not DirAccess.dir_exists_absolute(snapshots_dir):
        print("DynamicContextManager: Snapshots directory not found: ", snapshots_dir)
        return ""
    
    # Find most recent .json metadata file
    var dir = DirAccess.open(snapshots_dir)
    if not dir:
        print("DynamicContextManager: Cannot open snapshots directory")
        return ""
    
    var files = []
    
    dir.list_dir_begin()
    var file_name = dir.get_next()
    while file_name != "":
        if file_name.ends_with(".json"):
            files.append(file_name)
        file_name = dir.get_next()
    
    if files.is_empty():
        print("DynamicContextManager: No snapshot metadata files found")
        return ""
    
    # Sort by timestamp (newest first)
    files.sort()
    var latest_file = files[-1]
    
    # Read the metadata
    var file = FileAccess.open(snapshots_dir + latest_file, FileAccess.READ)
    if not file:
        print("DynamicContextManager: Cannot read metadata file: ", latest_file)
        return ""
    
    var json_text = file.get_as_text()
    file.close()
    
    var json = JSON.new()
    var parse_result = json.parse(json_text)
    
    if parse_result == OK and json.data.has("visual_analysis"):
        return json.data["visual_analysis"]
    
    print("DynamicContextManager: No visual_analysis in metadata")
    return ""

func extract_location_from_visual(analysis: String) -> String:
    """Extract location description from visual analysis"""
    if "interface" in analysis.to_lower() or "control" in analysis.to_lower():
        return "Cosmic Command Center"
    elif "temple" in analysis.to_lower():
        return "Ancient Temple"
    elif "forest" in analysis.to_lower():
        return "Forest Area"
    else:
        return "Unknown Location"

func extract_environment_from_visual(analysis: String) -> String:
    """Extract environment description from visual analysis"""
    if "control panels" in analysis.to_lower():
        return "Advanced technological interface with monitoring systems"
    elif "geometric patterns" in analysis.to_lower():
        return "Complex interface with geometric navigation elements"
    else:
        return "Environment description pending visual analysis"

func extract_interface_elements(analysis: String) -> Array:
    """Extract interface elements from visual analysis"""
    var elements = []
    
    if "control panels" in analysis.to_lower():
        elements.append("control_panels")
    if "monitoring" in analysis.to_lower():
        elements.append("monitoring_systems")
    if "geometric" in analysis.to_lower():
        elements.append("geometric_patterns")
    if "navigation" in analysis.to_lower():
        elements.append("navigation_elements")
    
    return elements

func get_current_context() -> Dictionary:
    """Get the current dynamic context (not static template!)"""
    return current_context

func force_context_update():
    """Force an immediate context update from current visuals"""
    _update_context_from_visuals()

func get_contextual_description() -> String:
    """Get current description based on actual visuals, not templates"""
    if current_context.has("visual_description"):
        return current_context["visual_description"]
    else:
        return "Analyzing current environment..."
