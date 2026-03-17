extends Control
## EntityEditor.gd — Click entities to edit, save overrides back to runtime.
##
## Setup: Add a Control node to your scene, attach this script.
## Needs: Camera3D + SemanticRenderer spawning BridgeEntity_ nodes.

@export var runtime_url: String = "http://localhost:8080"

# [PATCH ui-toggle V1]
@export var hide_search_ui_on_start: bool = true
var _search_ui_visible: bool = true

var panel: PanelContainer
var name_label: Label
var concept_label: Label
var type_option: OptionButton
var role_edit: LineEdit
var mood_edit: LineEdit
var desc_edit: TextEdit
var save_button: Button
var close_button: Button
var status_label: Label

var _selected_entity_id: String = ""
var _selected_node: Node3D = null
var _entity_data: Dictionary = {}
var _highlight_mat: StandardMaterial3D

var ENTITY_TYPES := ["character", "npc", "protagonist", "antagonist", "giant",
    "neferati", "nephilim", "guard", "creature", "door", "container",
    "furniture", "weapon", "artifact", "vrill_source", "structure"]


func _ready() -> void:
    _build_ui()
    
    _highlight_mat = StandardMaterial3D.new()
    _highlight_mat.albedo_color = Color(1, 1, 0, 0.3)
    _highlight_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    _highlight_mat.emission_enabled = true
    _highlight_mat.emission = Color(1, 1, 0)
    _highlight_mat.emission_energy_multiplier = 1.0
    
    panel.visible = false


    
    _search_ui_visible = not hide_search_ui_on_start
    
    _set_search_ui_visible(_search_ui_visible)

func _unhandled_input(event: InputEvent) -> void:

    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_F1:
            _search_ui_visible = not _search_ui_visible
            _set_search_ui_visible(_search_ui_visible)
            if not _search_ui_visible:
                panel.visible = false
                _deselect()
            accept_event()
            return
    if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
        if panel.visible and panel.get_global_rect().has_point(event.position):
            return
        _try_select_entity(event.position)


func _try_select_entity(screen_pos: Vector2) -> void:
    var camera := get_viewport().get_camera_3d()
    if not camera:
        return
    
    var best_node: Node3D = null
    var best_dist := 60.0
    
    for node in _find_bridge_entities():
        var center := node.global_position + Vector3(0, 0.9, 0)
        var screen := camera.unproject_position(center)
        var dist := screen.distance_to(screen_pos)
        if dist < best_dist:
            best_dist = dist
            best_node = node
    
    if best_node:
        _select_entity(best_node)
    else:
        _deselect()


func _find_bridge_entities() -> Array[Node3D]:
    var results: Array[Node3D] = []
    for child in get_tree().root.get_children():
        for grandchild in child.get_children():
            if grandchild is Node3D and grandchild.name.begins_with("BridgeEntity_"):
                results.append(grandchild)
    return results


func _select_entity(node: Node3D) -> void:
    _remove_highlight()
    _selected_node = node
    _selected_entity_id = node.name.replace("BridgeEntity_", "")
    _add_highlight(node)
    _fetch_entity_data()
    panel.visible = true


func _deselect() -> void:
    _remove_highlight()
    _selected_node = null
    _selected_entity_id = ""
    panel.visible = false


func _add_highlight(node: Node3D) -> void:
    for child in node.get_children():
        if child is MeshInstance3D and child.name == "Mesh":
            var outline := MeshInstance3D.new()
            outline.name = "SelectionHighlight"
            outline.mesh = child.mesh
            outline.material_override = _highlight_mat
            outline.scale = Vector3(1.2, 1.05, 1.2)
            outline.position = child.position
            node.add_child(outline)
            break


func _remove_highlight() -> void:
    if _selected_node and is_instance_valid(_selected_node):
        var h := _selected_node.get_node_or_null("SelectionHighlight")
        if h:
            h.queue_free()


# ═══ FETCH ═══

func _fetch_entity_data() -> void:
    var http := HTTPRequest.new()
    http.timeout = 5.0
    add_child(http)

    print("[HTTP DEBUG][control.gd] self_in_tree=", is_inside_tree(), " http_in_tree=", http.is_inside_tree(), " node=", get_path())

    http.request_completed.connect(func(_result, code, _hdrs, body_bytes):
        _on_examine_response(code, body_bytes)
        http.queue_free()
    )

    var body := JSON.stringify({
        "command": "examine " + _selected_entity_id
    })

    var err := http.request(
        runtime_url + "/command",
        ["Content-Type: application/json"],
        HTTPClient.METHOD_POST,
        body
    )

    if err != OK:
        push_error("control.gd HTTP request failed to start: %s" % err)
        http.queue_free()


func _on_examine_response(code: int, body: PackedByteArray) -> void:
    if code != 200:
        return
    var json := JSON.new()
    if json.parse(body.get_string_from_utf8()) != OK:
        return
    _entity_data = json.data.get("entity", {})
    _populate_panel()


func _populate_panel() -> void:
    var ent := _entity_data
    name_label.text = str(ent.get("name", _selected_entity_id))
    concept_label.text = "Mentions: %s | Knowledge: %s" % [
        str(ent.get("mention_count", "?")),
        str(ent.get("knowledge", []))
    ]
    
    var etype := str(ent.get("type", "character"))
    for i in range(type_option.item_count):
        if type_option.get_item_text(i) == etype:
            type_option.selected = i
            break
    
    role_edit.text = str(ent.get("role", ""))
    mood_edit.text = str(ent.get("mood", "neutral"))
    desc_edit.text = str(ent.get("description", ""))
    _set_status("Loaded: %s" % name_label.text)


# ═══ SAVE OVERRIDES ═══

func _on_save_pressed() -> void:
    if _selected_entity_id.is_empty():
        return
    
    var fields := {
        "type": type_option.get_item_text(type_option.selected),
        "role": role_edit.text.strip_edges(),
        "mood": mood_edit.text.strip_edges(),
        "description": desc_edit.text.strip_edges(),
    }
    
    var count := 0
    for field in fields:
        if fields[field].is_empty():
            continue
        var cmd := "override %s %s %s" % [_selected_entity_id, field, fields[field]]
        _send_command(cmd)
        count += 1
    
    _set_status("Saved %d overrides → %s" % [count, _selected_entity_id])
    
    # Refresh renderer
    await get_tree().create_timer(0.5).timeout
    for sibling in get_parent().get_children():
        if sibling.has_method("force_refresh"):
            sibling.force_refresh()
            break


func _send_command(cmd: String) -> void:
    var http := HTTPRequest.new()
    http.timeout = 5.0
    add_child(http)
    http.request_completed.connect(func(_r, _c, _h, _b): http.queue_free())
    http.request(runtime_url + "/command",
        ["Content-Type: application/json"],
        HTTPClient.METHOD_POST,
        JSON.stringify({"command": cmd}))


func _on_close_pressed() -> void:
    _deselect()


func _set_status(msg: String) -> void:
    if status_label:
        status_label.text = msg


# ═══ BUILD UI (no .tscn needed) ═══

func _build_ui() -> void:
    panel = PanelContainer.new()
    panel.custom_minimum_size = Vector2(300, 0)
    panel.anchor_left = 1.0; panel.anchor_right = 1.0
    panel.anchor_top = 0.0; panel.anchor_bottom = 1.0
    panel.offset_left = -310; panel.offset_right = -10
    panel.offset_top = 10; panel.offset_bottom = -10
    add_child(panel)
    
    var style := StyleBoxFlat.new()
    style.bg_color = Color(0.1, 0.1, 0.14, 0.95)
    style.border_color = Color(0.3, 0.5, 0.8, 0.8)
    style.set_border_width_all(2)
    style.set_corner_radius_all(6)
    style.set_content_margin_all(12)
    panel.add_theme_stylebox_override("panel", style)
    
    var scroll := ScrollContainer.new()
    scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    panel.add_child(scroll)
    
    var vbox := VBoxContainer.new()
    vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    vbox.add_theme_constant_override("separation", 6)
    scroll.add_child(vbox)
    
    # Header
    var h := Label.new()
    h.text = "ENTITY EDITOR"
    h.add_theme_font_size_override("font_size", 18)
    h.add_theme_color_override("font_color", Color(0.4, 0.7, 1.0))
    h.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    vbox.add_child(h)
    vbox.add_child(HSeparator.new())
    
    # Name + concept
    name_label = Label.new()
    name_label.text = "(click an entity)"
    name_label.add_theme_font_size_override("font_size", 16)
    name_label.add_theme_color_override("font_color", Color(1, 0.9, 0.4))
    vbox.add_child(name_label)
    
    concept_label = Label.new()
    concept_label.add_theme_font_size_override("font_size", 11)
    concept_label.add_theme_color_override("font_color", Color(0.5, 0.5, 0.6))
    vbox.add_child(concept_label)
    vbox.add_child(HSeparator.new())
    
    # Type
    vbox.add_child(_lbl("Type:"))
    type_option = OptionButton.new()
    for t in ENTITY_TYPES:
        type_option.add_item(t)
    vbox.add_child(type_option)
    
    # Role
    vbox.add_child(_lbl("Role:"))
    role_edit = LineEdit.new()
    role_edit.placeholder_text = "protagonist, elder, mystic..."
    vbox.add_child(role_edit)
    
    # Mood
    vbox.add_child(_lbl("Mood:"))
    mood_edit = LineEdit.new()
    mood_edit.placeholder_text = "protective, hostile, curious..."
    vbox.add_child(mood_edit)
    
    # Description
    vbox.add_child(_lbl("Description:"))
    desc_edit = TextEdit.new()
    desc_edit.custom_minimum_size = Vector2(0, 80)
    desc_edit.placeholder_text = "Author override..."
    vbox.add_child(desc_edit)
    
    # Buttons
    var spacer := Control.new()
    spacer.custom_minimum_size = Vector2(0, 16)
    vbox.add_child(spacer)
    
    var btn_row := HBoxContainer.new()
    btn_row.add_theme_constant_override("separation", 8)
    vbox.add_child(btn_row)
    
    save_button = Button.new()
    save_button.text = "Save Overrides"
    save_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    save_button.pressed.connect(_on_save_pressed)
    btn_row.add_child(save_button)
    
    close_button = Button.new()
    close_button.text = "Close"
    close_button.pressed.connect(_on_close_pressed)
    btn_row.add_child(close_button)
    
    # Status
    status_label = Label.new()
    status_label.text = "Click entity in 3D to edit"
    status_label.add_theme_font_size_override("font_size", 11)
    status_label.add_theme_color_override("font_color", Color(0.4, 0.6, 0.4))
    status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    vbox.add_child(status_label)


func _lbl(text: String) -> Label:
    var l := Label.new()
    l.text = text
    l.add_theme_font_size_override("font_size", 13)
    l.add_theme_color_override("font_color", Color(0.7, 0.7, 0.8))
    return l

func _set_search_ui_visible(v: bool) -> void:
    var p := get_parent()
    if p == null:
        return
    var sr := p.get_node_or_null("SearchRow")
    if sr:
        sr.visible = v
    var body := p.get_node_or_null("Body")
    if body:
        body.visible = v

