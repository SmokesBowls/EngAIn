extends MeshInstance3D

@export var entity_id: String = ""
@export var zw_concept: String = ""
@export var rule_id: String = ""

signal clicked(entity_id: String, zw_concept: String)

func _ready():
    add_to_group("ap_cubes")

func _input_event(
        _camera: Camera3D,
        event: InputEvent,
        _pos: Vector3,
        _normal: Vector3,
        _shape_idx: int
    ) -> void:
    if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        clicked.emit(entity_id, zw_concept)
        print("[CLICK] ", zw_concept, " (", entity_id, ")")

func set_color(color: Color):
    var mat = material_override as StandardMaterial3D
    if not mat:
        mat = StandardMaterial3D.new()
        material_override = mat
    mat.albedo_color = color

func show_reason(reason: String):
    # For now, just print it. In a real UI this would be a label 3D or hover text.
    print("[AP REASON] ", entity_id, " blocked by: ", reason)
