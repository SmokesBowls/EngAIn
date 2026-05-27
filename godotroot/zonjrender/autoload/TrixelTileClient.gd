extends Node
## TrixelTileClient.gd — Trixel Compositor tile client
## Add as Autoload: Project Settings → Autoload → Name: TrixelTileClient
##
## Fetches rendered terrain tiles from tile_server.py (port 8766),
## loads PNGs from the local filesystem, and caches ImageTextures by scene_id.
##
## Quickstart:
##     TrixelTileClient.fetch_tile("shore_01", "beach", "coastal")
##     TrixelTileClient.tile_ready.connect(_on_tile_ready)
##
## Integration with SemanticRenderer — add this block inside render_from_data()
## after the terrain meshes are built:
##
##     var tc := get_node_or_null("/root/TrixelTileClient")
##     if tc != null:
##         tc.enrich_terrain_meshes(terrain_meshes, data)

signal tile_ready(scene_id: String, terrain: String, texture: ImageTexture)
signal tile_failed(scene_id: String, error: String)
signal connection_changed(connected: bool)

const HOST := "127.0.0.1"
const PORT := 8766

var _cache: Dictionary = {}    # scene_id -> ImageTexture
var _pending: Dictionary = {}  # scene_id -> true  (guard against duplicate in-flight)
var _connected: bool = false


# ── Public API ──────────────────────────────────────────────────────────────

func fetch_tile(
	scene_id:    String,
	terrain:     String = "default",
	environment: String = "unknown",
) -> void:
	## Request a tile PNG from the tile server.  Emits tile_ready on success.
	## Deduplicates: a second call while one is in-flight is ignored.
	## Cache hit: re-emits tile_ready immediately without network round-trip.
	if _cache.has(scene_id):
		tile_ready.emit(scene_id, terrain, _cache[scene_id])
		return
	if _pending.has(scene_id):
		return

	var http := HTTPRequest.new()
	http.timeout = 10.0
	add_child(http)
	http.request_completed.connect(
		_on_tile_done.bind(scene_id, terrain, http),
		CONNECT_ONE_SHOT,
	)

	var url := "http://%s:%d/tile?scene_id=%s&terrain=%s&environment=%s" % [
		HOST, PORT,
		scene_id.uri_encode(),
		terrain.uri_encode(),
		environment.uri_encode(),
	]
	_pending[scene_id] = true
	http.request(url)


func get_cached_texture(scene_id: String) -> ImageTexture:
	## Returns the cached texture or null if not yet fetched.
	return _cache.get(scene_id, null)


func enrich_terrain_meshes(meshes: Array, data: Dictionary) -> void:
	## Fetch a trixelcomposer tile and apply it to a set of MeshInstance3D nodes
	## once it arrives.  Call this from SemanticRenderer after TerrainChunkBuilder
	## has already added nodes to the scene (the atlas texture is the fallback
	## until the trixelcomposer tile loads).
	var scene_id: String = str(data.get("scene_id", data.get("id", "scene")))
	var terrain:  String = str(data.get("terrain_family", data.get("terrain", "default")))
	var env:      String = str(data.get("environment", "unknown"))

	if _cache.has(scene_id):
		_apply_to_meshes(meshes, _cache[scene_id])
		return

	# Capture the mesh list so the lambda can close over it.
	var apply_once := func(sid: String, _ter: String, tex: ImageTexture) -> void:
		if sid == scene_id:
			_apply_to_meshes(meshes, tex)
	tile_ready.connect(apply_once, CONNECT_ONE_SHOT)

	fetch_tile(scene_id, terrain, env)


func is_server_connected() -> bool:
	return _connected


# ── Internals ────────────────────────────────────────────────────────────────

func _apply_to_meshes(meshes: Array, texture: ImageTexture) -> void:
	for node in meshes:
		if not node is MeshInstance3D:
			continue
		var mi := node as MeshInstance3D
		var mat := mi.get_active_material(0)
		if mat is StandardMaterial3D:
			var sm := mat as StandardMaterial3D
			sm.albedo_texture  = texture
			sm.albedo_color    = Color.WHITE
			sm.texture_filter  = BaseMaterial3D.TEXTURE_FILTER_NEAREST


func _on_tile_done(
	result:   int,
	code:     int,
	_headers: PackedStringArray,
	body:     PackedByteArray,
	scene_id: String,
	terrain:  String,
	http:     HTTPRequest,
) -> void:
	_pending.erase(scene_id)
	http.queue_free()

	var was_connected := _connected

	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		_connected = false
		if _connected != was_connected:
			connection_changed.emit(false)
		var msg := "HTTP %d / result %d" % [code, result]
		push_warning("[TrixelTileClient] tile fetch failed for '%s': %s" % [scene_id, msg])
		tile_failed.emit(scene_id, msg)
		return

	if not _connected:
		_connected = true
		connection_changed.emit(true)

	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		tile_failed.emit(scene_id, "Invalid JSON response")
		return

	var png_path: String = str(parsed.get("png", ""))
	if png_path.is_empty():
		tile_failed.emit(scene_id, "Response missing 'png' field")
		return

	var texture := _load_texture_from_file(png_path)
	if texture == null:
		tile_failed.emit(scene_id, "Image.load_from_file failed: " + png_path)
		return

	_cache[scene_id] = texture
	print("[TrixelTileClient] tile ready: %s  ->  %s" % [scene_id, png_path.get_file()])
	tile_ready.emit(scene_id, terrain, texture)


func _load_texture_from_file(path: String) -> ImageTexture:
	var img := Image.load_from_file(path)
	if img == null:
		push_warning("[TrixelTileClient] Cannot load image: " + path)
		return null
	return ImageTexture.create_from_image(img)
