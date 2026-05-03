# VaultClient.gd
# VaultClient.gd — Obsidian Vault Linker for Godot
# ==================================================
# Autoload this as "VaultClient" in Project Settings.
#
# Sends vault.manifest.json to sim_runtime's /vault/link endpoint.
# Once linked, all Obsidian markdown files become available as
# ZONJ scenes that can be loaded via SimClient.
#
# Usage from boot.gd or any script:
#     VaultClient.link_vault("/path/to/vault", manifest_dict)
#     VaultClient.check_status()
#
# Signals:
#     vault_linked(result: Dictionary)  — link succeeded
#     vault_failed(error: String)       — link failed
#     vault_status(status: Dictionary)  — status response

extends Node

signal vault_linked(result: Dictionary)
signal vault_failed(error: String)
signal vault_status(status: Dictionary)
signal vault_search_results(result: Dictionary)

@export var runtime_base: String = "http://127.0.0.1:8080"

## Path to the vault root on disk (set this or pass to link_vault)
@export var default_vault_root: String = "/run/media/mytruelove/storage1/pop/obsidian/obsidianburdenNov25"

## Path to vault.manifest.json relative to vault root (or absolute)
@export var default_manifest_path: String = "vault.manifest.json"

var _http: HTTPRequest
var _pending_action: String = ""

# Last manifest used for linking (loaded from disk or passed in).
# boot.gd can read this to configure optional services (e.g., scene_api_base).
var last_manifest: Dictionary = {}
var last_vault_root: String = ""


func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)
	print("[VaultClient] ready. runtime=%s" % runtime_base)


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------

func link_vault(vault_root: String = "", manifest: Dictionary = {}) -> void:
	"""
	Link an Obsidian vault to the runtime.

	If vault_root is empty, uses default_vault_root.
	If manifest is empty, loads from default_manifest_path.
	"""
	var vroot := vault_root if vault_root != "" else default_vault_root
	if vroot == "":
		vault_failed.emit("vault_root is empty — set default_vault_root or pass it")
		return

	var mfst := manifest
	if mfst.is_empty():
		mfst = _load_manifest_from_disk(vroot)
		if mfst.is_empty():
			vault_failed.emit("could not load vault.manifest.json from %s" % vroot)
			return

	# Persist the manifest that will be sent to the runtime.
	last_vault_root = vroot
	last_manifest = mfst.duplicate(true)

	var payload := {
		"vault_root": vroot,
		"manifest": mfst
	}

	_pending_action = "link"
	_post("/vault/link", payload)


func check_status() -> void:
	"""Check current vault linkage status."""
	_pending_action = "status"
	_request_get("/vault/status")


func link_default() -> void:
	"""Convenience: link using export defaults."""
	link_vault()


func search(query: String, limit: int = 20, mode: String = "all") -> void:
	"""Search across all linked vault scenes."""
	if query.strip_edges() == "":
		_emit_fail("search query is empty")
		return
	_pending_action = "search"
	var encoded_q := query.uri_encode()
	var path := "/vault/search?q=%s&limit=%d" % [encoded_q, limit]
	_request_get(path)


# ------------------------------------------------------------------
# HTTP PLUMBING
# ------------------------------------------------------------------

func _post(path: String, payload: Dictionary) -> void:
	var url := runtime_base + path
	var body := JSON.stringify(payload)
	var headers := PackedStringArray(["Content-Type: application/json"])
	var err := _http.request(url, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		_emit_fail("transport error: %d" % err)


func _get(property: StringName) -> Variant:
	if property == &"last_manifest":
		return last_manifest
	return null


func _request_get(path: String) -> void:
	var url := runtime_base + path
	var headers := PackedStringArray(["Accept: application/json"])
	var err := _http.request(url, headers, HTTPClient.METHOD_GET)
	if err != OK:
		_emit_fail("transport error: %d" % err)


func _on_request_completed(result: int, response_code: int,
		_headers: PackedStringArray, body: PackedByteArray) -> void:
	var action := _pending_action
	_pending_action = ""

	if result != HTTPRequest.RESULT_SUCCESS:
		_emit_fail("transport fail result=%d http=%d" % [result, response_code])
		return

	if response_code < 200 or response_code >= 300:
		var raw := body.get_string_from_utf8()
		_emit_fail("http %d: %s" % [response_code, raw.left(400)])
		return

	var text := body.get_string_from_utf8()
	var j := JSON.new()
	var perr := j.parse(text)
	if perr != OK:
		_emit_fail("json parse error: %s" % j.get_error_message())
		return

	var data := j.data as Dictionary

	match action:
		"link":
			var status_str: String = str(data.get("status", "unknown"))
			if status_str == "ok":
				print("[VaultClient] LINKED: vault_id=%s scenes=%d" % [
					str(data.get("vault_id", "?")),
					int(data.get("scenes_extracted", 0))
				])
				vault_linked.emit(data)
			else:
				_emit_fail("link returned status=%s error=%s" % [
					status_str,
					str(data.get("error", "unknown"))
				])

		"status":
			print("[VaultClient] status: linked=%s scenes=%d" % [
				str(data.get("linked", false)),
				int(data.get("scene_count", 0))
			])
			vault_status.emit(data)

		"search":
			vault_search_results.emit(data)
			print("[VaultClient] search hits=%d total_scenes=%d" % [
				int(data.get("count", 0)),
				int(data.get("total_scenes", 0)),
			])

		_:
			print("[VaultClient] unexpected action: %s data=%s" % [action, str(data)])


func _emit_fail(detail: String) -> void:
	print("[VaultClient] FAIL: %s" % detail)
	vault_failed.emit(detail)


# ------------------------------------------------------------------
# MANIFEST LOADER
# ------------------------------------------------------------------

func _load_manifest_from_disk(vault_root: String) -> Dictionary:
	"""Load vault.manifest.json from vault root directory."""
	var mpath: String
	if default_manifest_path.begins_with("/"):
		mpath = default_manifest_path
	else:
		mpath = vault_root.path_join(default_manifest_path)

	if not FileAccess.file_exists(mpath):
		print("[VaultClient] manifest not found: %s" % mpath)
		return {}

	var f := FileAccess.open(mpath, FileAccess.READ)
	if f == null:
		print("[VaultClient] cannot open manifest: %s" % mpath)
		return {}

	var raw := f.get_as_text()
	f.close()

	var j := JSON.new()
	var err := j.parse(raw)
	if err != OK:
		print("[VaultClient] manifest parse error: %s" % j.get_error_message())
		return {}

	if j.data is Dictionary:
		print("[VaultClient] loaded manifest: vault_id=%s" % str(j.data.get("vault_id", "?")))
		return j.data as Dictionary

	return {}
