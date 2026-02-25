extends Node3D

func _ready() -> void:
    # Add the AP Simulation Debugger to the scene
    var debugger = load("res://APSimulationDebugger.gd").new()
    add_child(debugger)

    # Spawn test entities mapped to AP rules
    # 1. The Key (mapped to pickup_key)
    spawn_entity({
        "entity_id": "key",
        "zw_concept": "Iron Key",
        "placeholder_mesh": "cube",
        "transform": {"x": 2.0, "y": 0.5, "z": 0.0},
        "color": {"r": 0.8, "g": 0.8, "b": 0.2}
    })

    # 2. The Door (mapped to unlock_door)
    spawn_entity({
        "entity_id": "door",
        "zw_concept": "Locked Gate",
        "placeholder_mesh": "cube",
        "transform": {"x": - 2.0, "y": 1.0, "z": 0.0},
        "color": {"r": 0.4, "g": 0.2, "b": 0.1}
    })

func spawn_entity(entity_data: Dictionary) -> void:
    var mesh: MeshInstance3D = MeshInstance3D.new()
    mesh.set_script(load("res://ClickablePlaceholder.gd"))

    mesh.entity_id = entity_data.get("entity_id", "")
    mesh.zw_concept = entity_data.get("zw_concept", "")
    
    # Map entity to rule for the debugger (demo logic)
    if mesh.entity_id == "key": mesh.rule_id = "unknown_pickup_key"
    elif mesh.entity_id == "door": mesh.rule_id = "unknown_unlock_door"

    mesh.mesh = BoxMesh.new()

    var t: Dictionary = entity_data.get("transform", {})
    mesh.position = Vector3(
        float(t.get("x", 0.0)),
        float(t.get("y", 0.0)),
        float(t.get("z", 0.0))
    )

    var col: Dictionary = entity_data.get("color", {})
    var mat: StandardMaterial3D = StandardMaterial3D.new()
    mat.albedo_color = Color(
        float(col.get("r", 1.0)),
        float(col.get("g", 1.0)),
        float(col.get("b", 1.0))
    )
    mesh.material_override = mat

    var shape: CollisionShape3D = CollisionShape3D.new()
    shape.shape = BoxShape3D.new()
    mesh.add_child(shape)

    add_child(mesh)
    mesh.clicked.connect(_on_placeholder_clicked)

func _on_placeholder_clicked(entity_id: String, zw_concept: String) -> void:
    print(">> CLICKED:", zw_concept, "(", entity_id, ")")
    var bridge = get_node_or_null("/root/EngAInBridge")
    if bridge and bridge.has_method("submit_command"):
        bridge.submit_command({
            "type": "interaction",
            "action": "click",
            "entity_id": entity_id,
            "zw_concept": zw_concept
        })
