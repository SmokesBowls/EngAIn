extends Area2D
## TrixelEntity.gd
## A live entity node spawned from sim_runtime data.
## Supports three asset modes: auto | upload | draw
## Place at: res://entities/TrixelEntity.gd

signal asset_changed(entity_id: String, mode: String)

# --- Entity identity (set by boot.gd on spawn) ---
var entity_id: String = ""
var entity_type: String = "character"
var entity_name: String = "Unknown"

# --- Asset mode: auto | upload | draw ---
var asset_mode: String = "auto"

# --- Internal refs ---
@onready var sprite: Sprite2D = $Sprite2D
@onready var label: Label = $Label
@onready var editor_panel: Panel = $EditorPanel
@onready var pixel_canvas: SubViewport = $EditorPanel/PixelCanvas
@onready var upload_dialog: FileDialog = $FileDialog

# Placeholder colors per type so blobs are distinguishable immediately
const TYPE_COLORS := {
	"character": Color(0.2, 0.4, 1.0),    # blue
	"npc":       Color(0.2, 0.8, 0.3),    # green
	"enemy":     Color(1.0, 0.2, 0.2),    # red
	"item":      Color(1.0, 0.8, 0.1),    # gold
	"trigger":   Color(0.8, 0.2, 1.0),    # purple
}
const DEFAULT_COLOR := Color(0.5, 0.5, 0.5)   # gray fallback


func _ready() -> void:
	# Connect click
	input_event.connect(_on_input_event)
	editor_panel.visible = false

	# Apply auto asset on spawn
	if asset_mode == "auto":
		_apply_auto_asset()


# ================================================================
# PUBLIC: called by boot.gd after add_child()
# ================================================================

func setup(id: String, type: String, display_name: String, pos: Vector2) -> void:
	entity_id = id
	entity_type = type
	entity_name = display_name
	position = pos
	label.text = display_name
	_apply_auto_asset()


# ================================================================
# ASSET MODES
# ================================================================

func _apply_auto_asset() -> void:
	## Generates a colored placeholder image based on entity type.
	## When trixel_composer output exists at the expected path, loads that instead.
	asset_mode = "auto"

	# Check if trixel composer already generated a PNG for this type
	var trixel_path := "res://assets/trixels/%s.png" % entity_type
	if ResourceLoader.exists(trixel_path):
		sprite.texture = load(trixel_path)
		return

	# Otherwise: colored blob placeholder (16x16, scaled 4x)
	var img := Image.create(16, 16, false, Image.FORMAT_RGBA8)
	var col: Color = TYPE_COLORS.get(entity_type, DEFAULT_COLOR)

	# Fill circle
	for y in range(16):
		for x in range(16):
			var dx := x - 8.0
			var dy := y - 8.0
			if dx * dx + dy * dy < 49.0:   # radius 7
				img.set_pixel(x, y, col)
			else:
				img.set_pixel(x, y, Color(0, 0, 0, 0))

	sprite.texture = ImageTexture.create_from_image(img)
	asset_changed.emit(entity_id, "auto")


func open_upload_dialog() -> void:
	## Opens a file picker. User selects a PNG or mesh file.
	asset_mode = "upload"
	upload_dialog.popup_centered()


func open_draw_editor() -> void:
	## Opens the onboard pixel draw panel for this entity.
	asset_mode = "draw"
	editor_panel.visible = true


func apply_uploaded_texture(path: String) -> void:
	## Called after user picks a file in the upload dialog.
	if path.ends_with(".png") or path.ends_with(".jpg") or path.ends_with(".webp"):
		var tex := load(path) as Texture2D
		if tex:
			sprite.texture = tex
			asset_changed.emit(entity_id, "upload")


func apply_drawn_texture(img: Image) -> void:
	## Called by the pixel editor when user confirms their drawing.
	sprite.texture = ImageTexture.create_from_image(img)
	editor_panel.visible = false
	asset_changed.emit(entity_id, "draw")


# ================================================================
# INTERACTION
# ================================================================

func _on_input_event(_viewport, event: InputEvent, _shape_idx: int) -> void:
	if event is InputEventMouseButton and event.pressed:
		match event.button_index:
			MOUSE_BUTTON_LEFT:
				_show_context_menu()
			MOUSE_BUTTON_RIGHT:
				open_draw_editor()


func _show_context_menu() -> void:
	## Left click: show a small popup with asset options.
	## For now prints to console — wire to a UI popup when ready.
	print("[TrixelEntity] '%s' (%s) clicked. Options: auto / upload / draw" % [entity_name, entity_id])
	print("  Right-click to open draw editor")
	print("  Call open_upload_dialog() to upload an asset")


# ================================================================
# FILE DIALOG SIGNAL
# ================================================================

func _on_file_dialog_file_selected(path: String) -> void:
	apply_uploaded_texture(path)


func _close_editor() -> void:
	editor_panel.visible = false
