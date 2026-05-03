@tool
extends Node
# ─────────────────────────────────────────────
#  SemanticRendererTool.gd  —  EDITOR ONLY
#  Attach as a sibling or child of SemanticRenderer
#  in the scene tree. Stripped or dormant on export.
#
#  Handles: inspector buttons, undo/redo, owner
#           assignment, live HTTP fetch in editor.
#  Never touches: rendering math, mesh building,
#                 entity logic, runtime signals.
# ─────────────────────────────────────────────

## Path to SemanticRenderer node (sibling or parent)
@export_node_path("Node3D") var renderer_path: NodePath = NodePath("../SemanticRenderer")

## Scene ID to preview
@export var preview_scene_id: String = "03_Fist_contact"

## Tick to fetch from live server and build preview
@export var refresh_preview: bool = false:
	set(v):
		refresh_preview = false
		if Engine.is_editor_hint():
			_editor_refresh()

## Tick to wipe the preview root
@export var clear_preview: bool = false:
	set(v):
		clear_preview = false
		if Engine.is_editor_hint():
			_editor_clear()

@export_file("*.json") var fallback_json_path: String = ""

# Editor-only typed — safe because @tool scripts are never exported to release
var _plugin: EditorPlugin
var _undo_redo: EditorUndoRedoManager
var _TerrainBuilder = TerrainChunkBuilder.new()
var _EntitySpawner = EntitySpawner.new()


func _ready() -> void:
	if not Engine.is_editor_hint():
		# In exported game this node does nothing
		set_process(false)
		return
	_plugin    = EditorPlugin.new()
	_undo_redo = _plugin.get_undo_redo()


# ── Editor refresh ─────────────────────────────
func _editor_refresh() -> void:
	var data := _fetch_data()
	if data.is_empty():
		push_warning("[SemanticRendererTool] No data — check server or fallback_json_path")
		return
	_build_preview(data)


func _fetch_data() -> Dictionary:
	# Try live server first
	var svc = get_node_or_null("/root/SceneNetworkService")
	if svc != null:
		var data: Dictionary = svc.fetch_scene_sync(preview_scene_id)
		if not data.is_empty():
			return data

	# Fallback: JSON file on disk
	if fallback_json_path != "" and FileAccess.file_exists(fallback_json_path):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(fallback_json_path))
		if typeof(parsed) == TYPE_DICTIONARY:
			var wrapped := parsed as Dictionary
			return wrapped.get("data", wrapped) as Dictionary

	return {}


# ── Preview build ──────────────────────────────
func _build_preview(data: Dictionary) -> void:
	var preview_root := _get_or_create_preview_root()
	_editor_clear_root(preview_root)

	var scene_root := _plugin.get_editor_interface().get_edited_scene_root()

	# Terrain
	var terrain_meshes: Array = _TerrainBuilder.build(data)
	for mi in terrain_meshes:
		_editor_add(mi, preview_root, scene_root)

	# Entities
	var entities: Array = _EntitySpawner.build(data)
	for ent in entities:
		_editor_add(ent, preview_root, scene_root)
		# Children (Body, NameLabel) also need owner
		for child in ent.get_children():
			child.owner = scene_root

	_plugin.get_editor_interface().mark_scene_as_unsaved()
	print("[SemanticRendererTool] Preview built — %d terrain, %d entities" \
		% [terrain_meshes.size(), entities.size()])


func _editor_add(node: Node, parent: Node, scene_root: Node) -> void:
	_undo_redo.create_action("SemanticRendererTool: add " + node.name)
	_undo_redo.add_do_method(parent,    "add_child",  node)
	_undo_redo.add_do_method(node,      "set_owner",  scene_root)
	_undo_redo.add_undo_method(parent,  "remove_child", node)
	_undo_redo.commit_action()


# ── Clear ──────────────────────────────────────
func _editor_clear() -> void:
	var pr = _get_preview_root()
	if pr == null: return
	_editor_clear_root(pr)
	_plugin.get_editor_interface().mark_scene_as_unsaved()

func _editor_clear_root(root: Node) -> void:
	for c in root.get_children():
		_undo_redo.create_action("SemanticRendererTool: remove " + c.name)
		_undo_redo.add_do_method(root, "remove_child", c)
		_undo_redo.add_undo_method(root, "add_child", c)
		_undo_redo.commit_action()
		c.queue_free()


# ── Preview root helpers ───────────────────────
func _get_renderer() -> Node3D:
	return get_node_or_null(renderer_path) as Node3D

func _get_preview_root() -> Node3D:
	var renderer := _get_renderer()
	if renderer == null: return null
	return renderer.get_node_or_null("PreviewEntities") as Node3D

func _get_or_create_preview_root() -> Node3D:
	var existing := _get_preview_root()
	if existing != null: return existing
	var renderer := _get_renderer()
	if renderer == null:
		push_error("[SemanticRendererTool] SemanticRenderer node not found at: " + str(renderer_path))
		return null
	var root := Node3D.new()
	root.name = "PreviewEntities"
	var scene_root := _plugin.get_editor_interface().get_edited_scene_root()
	_undo_redo.create_action("SemanticRendererTool: create PreviewEntities")
	_undo_redo.add_do_method(renderer,  "add_child",    root)
	_undo_redo.add_do_method(root,      "set_owner",    scene_root)
	_undo_redo.add_undo_method(renderer,"remove_child", root)
	_undo_redo.commit_action()
	return root
