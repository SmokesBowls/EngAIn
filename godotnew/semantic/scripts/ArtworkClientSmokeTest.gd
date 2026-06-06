extends SceneTree

var _client: Node

func _initialize() -> void:
	var script: Script = load("res://autoload/ArtworkClient.gd")
	if script == null:
		push_error("[ArtworkClientSmokeTest] failed to load ArtworkClient.gd")
		quit(1)
		return

	_client = script.new()
	root.add_child(_client)

	# Let Godot run _ready() on the manually-created client.
	await process_frame

	_client.artwork_loaded.connect(_on_artwork_loaded)
	_client.artwork_failed.connect(_on_artwork_failed)

	print("[ArtworkClientSmokeTest] requesting latest artwork...")
	_client.get_latest_artwork()

	await create_timer(8.0).timeout
	push_error("[ArtworkClientSmokeTest] timed out waiting for artwork response")
	quit(1)

func _on_artwork_loaded(scene_id: String, texture: Texture2D) -> void:
	print("[ArtworkClientSmokeTest] loaded=%s size=%dx%d" % [
		scene_id,
		texture.get_width(),
		texture.get_height()
	])
	quit(0)

func _on_artwork_failed(scene_id: String, detail: String, status_code: int) -> void:
	push_error("[ArtworkClientSmokeTest] failed=%s status=%d detail=%s" % [
		scene_id,
		status_code,
		detail
	])
	quit(1)
