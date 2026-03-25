extends Node3D

@onready var world: Node3D = $World
@onready var camera_rig: Node3D = $World/CameraRig
@onready var camera_3d: Camera3D = $World/CameraRig/Camera3D
@onready var semantic_renderer: Node3D = $World/SemanticRenderer
@onready var actors: Node3D = $World/Actors
@onready var ui: Node = $UI

func _ready() -> void:
	print("[Main] Loaded")
	print("[Main] World ok: ", world != null)
	print("[Main] Camera ok: ", camera_3d != null)
	print("[Main] SemanticRenderer ok: ", semantic_renderer != null)
	print("[Main] Actors ok: ", actors != null)
	print("[Main] UI ok: ", ui != null)
	print("[Main] Loaded")

	if camera_3d != null:
		camera_3d.current = true
