extends Control

@export var renderer_path: NodePath

@onready var _renderer: Node = get_node_or_null(renderer_path)
@onready var _list: ItemList = $Panel/VBox/ChapterList

var _chapters: Array[String] = []

func _ready() -> void:
	if _renderer == null:
		push_warning("[ChapterSelector] SemanticRenderer not found")
		return

	_load_local_chapters()

func _load_local_chapters() -> void:
	_list.clear()
	_chapters.clear()

	var dir := DirAccess.open("res://chapters")
	if dir == null:
		push_warning("[ChapterSelector] No res://chapters folder")
		return

	dir.list_dir_begin()
	var file_name := dir.get_next()

	while file_name != "":
		if file_name.ends_with(".json"):
			var full_path := "res://chapters/%s" % file_name
			_chapters.append(full_path)
			_list.add_item(file_name)
		file_name = dir.get_next()

	dir.list_dir_end()

func _on_ChapterList_item_activated(index: int) -> void:
	if index < 0 or index >= _chapters.size():
		return

	var path := _chapters[index]

	if _renderer and _renderer.has_method("load_chapter"):
		_renderer.call("load_chapter", path)
	else:
		push_warning("[ChapterSelector] SemanticRenderer missing load_chapter()")
