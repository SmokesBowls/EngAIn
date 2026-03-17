extends Node3D
# ^^^ make sure this is the FIRST non-comment line in the file

func _ready() -> void:
    var dummy: Dictionary = {
        "entity_id": "test_1",
        "zw_concept": "test cube",
        "placeholder_mesh": "cube",
        "transform": {"x": 0.0, "y": 1.0, "z": 0.0},
        "color": {"r": 0.8, "g": 0.2, "b": 0.2}
    }
    spawn_entity(dummy)

func spawn_entity(entity_data: Dictionary) -> void:
    var mesh: MeshInstance3D = MeshInstance3D.new()
    mesh.set_script(load("res://ClickablePlaceholder.gd"))

    mesh.entity_id = entity_data.get("entity_id", "")
    mesh.zw_concept = entity_data.get("zw_concept", "")

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
    
    # Send interaction event back to the EngAIn bridge
    var bridge = get_node_or_null("/root/EngAInBridge")
    if bridge and bridge.has_method("submit_command"):
        var command: Dictionary = {
            "type": "interaction",
            "action": "click",
            "entity_id": entity_id,
            "zw_concept": zw_concept
        }
        bridge.submit_command(command)
