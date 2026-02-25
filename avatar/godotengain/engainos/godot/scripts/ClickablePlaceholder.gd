extends MeshInstance3D

@export var entity_id: String = ""
@export var zw_concept: String = ""

signal clicked(entity_id: String, zw_concept: String)

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
