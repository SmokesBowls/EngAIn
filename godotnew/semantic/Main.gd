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
	if camera_3d != null:
		camera_3d.current = true
	_fetch_snapshot()

func _fetch_snapshot() -> void:
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_snapshot_received)
	http.request("http://127.0.0.1:8090/api/snapshot")

func _on_snapshot_received(result, code, headers, body) -> void:
	if code != 200:
		print("[Main] Snapshot fetch failed, code: ", code)
		return
	var txt = body.get_string_from_utf8()
	var data = JSON.parse_string(txt)
	if typeof(data) != TYPE_DICTIONARY:
		print("[Main] Snapshot parse failed")
		return
	print("[Main] Snapshot received, keys: ", data.keys())
	var payload = data.get("payload", {})
	print("[Main] Scene: ", payload.get("scene_id", "unknown"))
	print("[Main] Entities: ", payload.get("entities", {}).keys())
