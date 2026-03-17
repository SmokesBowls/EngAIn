# File: scripts/EngineSummaryHUD.gd
# Engine Summary HUD — Production Governed Reality Overlay
#
# Authority model:
#   Python engine_summary.py  →  flat EngineSummary (projection)
#   ZWRuntime                 →  polls /api/hud/engine_summary
#   This node                 →  renders labels. Nothing else.
#
# Contract shape (from /api/hud/engine_summary):
#   { game_time, scene_id, active_quests, completed_quests,
#     combat_state, reality_mode, player_health, player_health_max,
#     player_location, entities_count, tick_rate,
#     pillar_status: { engain, mvcar, tv } }
#
# No local state derivation. No snapshot parsing.
# If the endpoint changes shape, update this contract comment.

extends Control
class_name EngineSummaryHUD

# ── Configuration ────────────────────────────────────────────
@export var panel_width: float = 240.0
@export var show_pillars: bool = true
@export var show_tick_rate: bool = false

# ── Colors ───────────────────────────────────────────────────
@export var color_bg: Color = Color(0.06, 0.06, 0.08, 0.80)
@export var color_label: Color = Color(0.45, 0.45, 0.50)
@export var color_value: Color = Color(0.78, 0.78, 0.82)
@export var color_accent: Color = Color(0.4, 0.7, 0.9)

var color_combat_idle: Color = Color(0.5, 0.5, 0.5)
var color_combat_engaged: Color = Color(0.9, 0.6, 0.2)
var color_combat_dead: Color = Color(0.85, 0.2, 0.2)

var color_reality_waking: Color = Color(0.78, 0.78, 0.82)
var color_reality_dream: Color = Color(0.6, 0.4, 0.9)
var color_reality_memory: Color = Color(0.4, 0.7, 0.5)
var color_reality_liminal: Color = Color(0.9, 0.5, 0.6)

var color_pillar_running: Color = Color(0.3, 0.8, 0.4)
var color_pillar_idle: Color = Color(0.5, 0.5, 0.5)
var color_pillar_reserved: Color = Color(0.4, 0.4, 0.45)
var color_pillar_error: Color = Color(0.85, 0.2, 0.2)

# ── State (summary only) ────────────────────────────────────
var _summary: Dictionary = {}
var _has_data: bool = false


func _ready() -> void:
	ZWRuntime.engine_summary_updated.connect(_on_engine_summary)


func _process(_delta: float) -> void:
	queue_redraw()


func _on_engine_summary(summary: Dictionary) -> void:
	"""THE integration point. Feed EngineSummary from Python."""
	_summary = summary
	_has_data = true
	queue_redraw()


func _draw() -> void:
	if not _has_data:
		_draw_idle()
		return

	var y := 0.0
	var pad := 8.0
	var lh := 14.0
	var rows: Array = []

	var gt: float = _summary.get("game_time", 0.0)
	rows.append({"label": "TIME", "value": "%.1fs" % gt, "color": color_value})

	var scene: String = _summary.get("scene_id", "—")
	rows.append({"label": "SCENE", "value": scene, "color": color_accent})

	var reality: String = _summary.get("reality_mode", "waking")
	rows.append({"label": "REALITY", "value": reality.to_upper(), "color": _reality_color(reality)})

	var combat: String = _summary.get("combat_state", "idle")
	var hp: float = _summary.get("player_health", 0.0)
	var hp_max: float = _summary.get("player_health_max", 100.0)
	rows.append({"label": "COMBAT", "value": "%s  HP %.0f/%.0f" % [combat.to_upper(), hp, hp_max], "color": _combat_color(combat)})

	var aq: int = _summary.get("active_quests", 0)
	var cq: int = _summary.get("completed_quests", 0)
	rows.append({"label": "QUESTS", "value": "%d active  %d done" % [aq, cq], "color": color_value})

	var ec: int = _summary.get("entities_count", 0)
	rows.append({"label": "ENTITIES", "value": str(ec), "color": color_value})

	if show_tick_rate:
		var tr: float = _summary.get("tick_rate", 0.0)
		var fps_est := 1.0 / tr if tr > 0 else 0.0
		rows.append({"label": "TICK", "value": "%.1fms (%.0f fps)" % [tr * 1000, fps_est], "color": color_value})

	if show_pillars:
		var ps: Dictionary = _summary.get("pillar_status", {})
		rows.append({"label": "PILLARS", "value": "", "color": color_label})
		for key in ["engain", "mvcar", "tv"]:
			var st: String = ps.get(key, "unknown")
			rows.append({"label": "  " + key.to_upper(), "value": st, "color": _pillar_color(st)})

	var total_h := pad + rows.size() * lh + pad
	draw_rect(Rect2(0, 0, panel_width, total_h), color_bg)

	y = pad
	for row in rows:
		draw_string(ThemeDB.fallback_font, Vector2(pad, y + 10), row["label"], HORIZONTAL_ALIGNMENT_LEFT, -1, 9, color_label)
		if row["value"] != "":
			draw_string(ThemeDB.fallback_font, Vector2(pad + 70, y + 10), row["value"], HORIZONTAL_ALIGNMENT_LEFT, int(panel_width - pad - 78), 9, row["color"])
		y += lh

	custom_minimum_size = Vector2(panel_width, total_h)


func _combat_color(state: String) -> Color:
	match state:
		"engaged": return color_combat_engaged
		"dead": return color_combat_dead
		_: return color_combat_idle

func _reality_color(mode: String) -> Color:
	match mode:
		"dream": return color_reality_dream
		"memory": return color_reality_memory
		"liminal": return color_reality_liminal
		_: return color_reality_waking

func _pillar_color(status: String) -> Color:
	match status:
		"running": return color_pillar_running
		"idle": return color_pillar_idle
		"reserved": return color_pillar_reserved
		"error": return color_pillar_error
		_: return color_pillar_idle


func _draw_idle() -> void:
	var h := 28.0
	draw_rect(Rect2(0, 0, panel_width, h), color_bg)
	draw_string(ThemeDB.fallback_font, Vector2(8, 18), "ENGINE — awaiting state", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.35, 0.35, 0.4))
	custom_minimum_size = Vector2(panel_width, h)
