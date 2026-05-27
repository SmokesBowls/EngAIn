class_name RenderPolicy
extends RefCounted
## Asset-source policy — decides which visual source wins for each terrain/asset.
##
## Two resolution levels:
##   1. Asset override:   policy.assets["sand"] = {render_mode: "atlas_2d"}
##   2. Scene default:    policy.default_render_mode = "composer_2_3d"
##
## Render modes:
##   atlas_2d       — static atlas.png only; TrixelTileClient never contacted
##   recipe_3d      — trixelcomposer output only; static atlas shown while pending
##   composer_2_3d  — static atlas as first frame, trixelcomposer overlaid when ready
##   custom_upload  — asset_path texture; falls back to atlas_2d if path is missing
##
## Typical policy JSON (res://render_policy.json):
##   {
##     "default_render_mode": "composer_2_3d",
##     "assets": {
##       "sand":       { "render_mode": "atlas_2d" },
##       "shoreline":  { "render_mode": "composer_2_3d" },
##       "volcano":    { "render_mode": "recipe_3d" },
##       "hero_cloak": { "render_mode": "custom_upload",
##                       "asset_path": "/abs/path/or/res://path.png" }
##     }
##   }

const MODE_ATLAS_2D      := "atlas_2d"
const MODE_RECIPE_3D     := "recipe_3d"
const MODE_COMPOSER_2_3D := "composer_2_3d"
const MODE_CUSTOM_UPLOAD := "custom_upload"

const VALID_MODES := [
	MODE_ATLAS_2D,
	MODE_RECIPE_3D,
	MODE_COMPOSER_2_3D,
	MODE_CUSTOM_UPLOAD,
]

const FALLBACK_MODE := MODE_COMPOSER_2_3D

var default_render_mode: String = FALLBACK_MODE
var _assets: Dictionary = {}  # terrain/asset name → {render_mode, asset_path?}


# ── Factory ───────────────────────────────────────────────────────────────────

static func default_policy() -> RenderPolicy:
	var p := RenderPolicy.new()
	p.default_render_mode = FALLBACK_MODE
	return p


static func from_dict(d: Dictionary) -> RenderPolicy:
	var p := RenderPolicy.new()
	var mode: String = String(d.get("default_render_mode", FALLBACK_MODE))
	p.default_render_mode = mode if mode in VALID_MODES else FALLBACK_MODE
	var assets_v: Variant = d.get("assets", {})
	if typeof(assets_v) == TYPE_DICTIONARY:
		p._assets = assets_v as Dictionary
	return p


static func from_json_file(path: String) -> RenderPolicy:
	if not FileAccess.file_exists(path):
		push_warning("[RenderPolicy] Not found: %s — using defaults" % path)
		return default_policy()
	var raw: String = FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("[RenderPolicy] Invalid JSON in %s — using defaults" % path)
		return default_policy()
	var p := from_dict(parsed as Dictionary)
	print("[RenderPolicy] Loaded: default=%s  overrides=%d" % [p.default_render_mode, p._assets.size()])
	return p


# ── Resolution ────────────────────────────────────────────────────────────────

func resolve(terrain: String) -> Dictionary:
	## Returns {render_mode, asset_path} for this terrain/asset.
	## Asset-level override wins over default_render_mode.
	if _assets.has(terrain):
		var v: Variant = _assets[terrain]
		if typeof(v) == TYPE_DICTIONARY:
			var ov: Dictionary = v as Dictionary
			var mode: String = String(ov.get("render_mode", default_render_mode))
			return {
				"render_mode": mode if mode in VALID_MODES else default_render_mode,
				"asset_path":  String(ov.get("asset_path", "")),
			}
	return {"render_mode": default_render_mode, "asset_path": ""}


func set_asset_override(terrain: String, mode: String, asset_path: String = "") -> void:
	## Programmatic override — useful for runtime hot-swap without reloading JSON.
	if not mode in VALID_MODES:
		push_warning("[RenderPolicy] Unknown mode '%s' — ignoring" % mode)
		return
	_assets[terrain] = {"render_mode": mode, "asset_path": asset_path}


func to_dict() -> Dictionary:
	return {"default_render_mode": default_render_mode, "assets": _assets.duplicate(true)}
