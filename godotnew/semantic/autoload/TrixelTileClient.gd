extends Node
## TrixelTileClient.gd — Trixel Compositor tile client
## Add as Autoload: Project Settings → Autoload → Name: TrixelTileClient
##
## Two modes:
##
##  1. ATLAS mode (preferred) — fetch_atlas(terrain, environment)
##     Generates a full replacement atlas PNG (same UV layout as atlas_meta.json).
##     SemanticRenderer._load_atlas_for() checks get_cached_atlas(terrain) first.
##     Atlas hit → semantic surface; miss → static atlas.png fallback (no change).
##
##  2. TILE mode — fetch_tile(scene_id, terrain, environment)
##     Fetches a single 16×16 tile for a given scene.  Used for per-scene overrides.
##
## Quickstart:
##     TrixelTileClient.fetch_atlas("shoreline", "coastal")
##     TrixelTileClient.atlas_ready.connect(_on_atlas_ready)

signal tile_ready(scene_id: String, terrain: String, texture: ImageTexture)
signal tile_failed(scene_id: String, error: String)
signal atlas_ready(terrain: String, texture: ImageTexture)
signal atlas_failed(terrain: String, error: String)
signal connection_changed(connected: bool)

const HOST := "127.0.0.1"
const PORT := 8766

var _tile_cache:  Dictionary = {}  # scene_id -> ImageTexture
var _atlas_cache: Dictionary = {}  # terrain  -> ImageTexture
var _pending:     Dictionary = {}  # key -> true  (dedup guard)
var _connected:   bool = false


func _ready() -> void:
	print("[TRIXEL_CLIENT] ready")


# ── Public API ──────────────────────────────────────────────────────────────

## ── Atlas API (preferred) ────────────────────────────────────────────────────

func fetch_atlas(terrain: String, environment: String = "unknown", seed: int = 42) -> void:
	## Request a semantic replacement atlas for a terrain type.
	## Emits atlas_ready(terrain, texture) on success.
	## The returned ImageTexture has the same UV layout as the original atlas.png.
	var key := "atlas:" + terrain
	if _atlas_cache.has(terrain):
		atlas_ready.emit(terrain, _atlas_cache[terrain])
		return
	if _pending.has(key):
		return

	var http := HTTPRequest.new()
	http.timeout = 30.0  # atlas generation takes longer than a single tile
	add_child(http)
	http.request_completed.connect(
		_on_atlas_done.bind(terrain, http),
		CONNECT_ONE_SHOT,
	)

	var url := "http://%s:%d/atlas?terrain=%s&environment=%s&seed=%d" % [
		HOST, PORT,
		terrain.uri_encode(),
		environment.uri_encode(),
		seed,
	]
	_pending[key] = true
	http.request(url)


func get_cached_atlas(terrain: String) -> ImageTexture:
	## Synchronous cache read — null if atlas not yet fetched.
	## SemanticRenderer._load_atlas_for() calls this before loading static atlas.png.
	return _atlas_cache.get(terrain, null)


## ── Tile API ─────────────────────────────────────────────────────────────────

func fetch_tile(
	scene_id:    String,
	terrain:     String = "default",
	environment: String = "unknown",
) -> void:
	## Request a tile PNG from the tile server.  Emits tile_ready on success.
	## Deduplicates: a second call while one is in-flight is ignored.
	## Cache hit: re-emits tile_ready immediately without network round-trip.
	if _tile_cache.has(scene_id):
		tile_ready.emit(scene_id, terrain, _tile_cache[scene_id])
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
	## Returns the cached tile texture or null if not yet fetched.
	return _tile_cache.get(scene_id, null)


func is_server_connected() -> bool:
	return _connected


# ── Internals ────────────────────────────────────────────────────────────────

func _on_atlas_done(
	result:  int,
	code:    int,
	_h:      PackedStringArray,
	body:    PackedByteArray,
	terrain: String,
	http:    HTTPRequest,
) -> void:
	var key := "atlas:" + terrain
	_pending.erase(key)
	http.queue_free()

	_update_connected(result == HTTPRequest.RESULT_SUCCESS and code == 200)

	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		var msg := "HTTP %d / result %d" % [code, result]
		push_warning("[TrixelTileClient] atlas fetch failed for '%s': %s" % [terrain, msg])
		atlas_failed.emit(terrain, msg)
		return

	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		atlas_failed.emit(terrain, "Invalid JSON response")
		return

	var png_path: String = str(parsed.get("png", ""))
	if png_path.is_empty():
		atlas_failed.emit(terrain, "Response missing 'png' field")
		return

	var texture := _load_texture_from_file(png_path)
	if texture == null:
		atlas_failed.emit(terrain, "Image.load_from_file failed: " + png_path)
		return
	texture.set_meta("source_path", png_path)

	_atlas_cache[terrain] = texture
	print("[TrixelTileClient] atlas ready: %s  ->  %s" % [terrain, png_path.get_file()])
	atlas_ready.emit(terrain, texture)


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

	_update_connected(result == HTTPRequest.RESULT_SUCCESS and code == 200)

	if result != HTTPRequest.RESULT_SUCCESS or code != 200:
		var msg := "HTTP %d / result %d" % [code, result]
		push_warning("[TrixelTileClient] tile fetch failed for '%s': %s" % [scene_id, msg])
		tile_failed.emit(scene_id, msg)
		return

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

	_tile_cache[scene_id] = texture
	print("[TrixelTileClient] tile ready: %s  ->  %s" % [scene_id, png_path.get_file()])
	tile_ready.emit(scene_id, terrain, texture)


func _update_connected(is_ok: bool) -> void:
	if is_ok != _connected:
		_connected = is_ok
		connection_changed.emit(_connected)


func _load_texture_from_file(path: String) -> ImageTexture:
	var img := Image.load_from_file(path)
	if img == null:
		push_warning("[TrixelTileClient] Cannot load image: " + path)
		return null
	return ImageTexture.create_from_image(img)
