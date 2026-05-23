extends Control

@export var renderer_path: NodePath

@onready var _renderer: Node = get_node_or_null(renderer_path)
@onready var _list: ItemList = $Panel/VBox/ChapterList

var _scene_ids: Array[String] = []

func _ready() -> void:
	SceneClient.scenes_listed.connect(_on_scenes_listed)
	SceneClient.request_failed.connect(_on_request_failed)
	SceneClient.list_scenes()

func _on_scenes_listed(scenes: Array) -> void:
	_list.clear()
	_scene_ids.clear()

	for id_v in scenes:
		var id: String = String(id_v)
		_scene_ids.append(id)
		_list.add_item(id)

	if _scene_ids.is_empty():
		push_warning("[ChapterSelector] Server returned 0 scenes")

func _on_request_failed(kind: String, detail: String, _status: int) -> void:
	if kind == "list_scenes":
		push_warning("[ChapterSelector] list_scenes failed: %s" % detail)

func _on_ChapterList_item_activated(index: int) -> void:
	if index < 0 or index >= _scene_ids.size():
		return
	SceneClient.load_scene(_scene_ids[index])
