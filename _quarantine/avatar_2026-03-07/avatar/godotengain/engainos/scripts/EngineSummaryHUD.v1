# File: scripts/EngineSummaryHUD.gd
# Engine Summary HUD — Governed Reality Overlay (EngAInOS contract)
#
# Authority model:
#   NGAT-RT runtime kernels   => truth
#   EngAInOS /api/hud/*       => stable HUD contract (read-only)
#   This node                 => renders labels only
#
# Primary input:
#   GET http://127.0.0.1:8090/api/hud/engine_summary
#
# Optional: if you still run a local ZWRuntime signal bus, you can keep the
# signal hooks enabled, but this file does not require them.

extends Control
class_name EngineSummaryHUD

# ── Configuration ──────────────────────────────────────────────
@export var panel_width: float = 240.0
@export var show_pillars: bool = true
@export var show_tick_rate: bool = false

@export var engainos_base_url: String = "http://127.0.0.1:8090"
@export var poll_hz: float = 5.0
@export var reality_mode: String = "waking"
@export var scene_id: String = ""          # optional override

# If true: will accept /root/ZWRuntime signals as a secondary source.
@export var allow_zwruntime_signals: bool = false

# ── Colors ─────────────────────────────────────────────────────
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

# ── State (summary only) ──────────────────────────────────────
var _summary: Dictionary = {}
var _last_tick: float = 0.0

# HTTP plumbing
var _http: HTTPRequest
var _poll_timer: Timer
var _in_flight: bool = false


func _ready() -> void:
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)

	_poll_timer = Timer.new()
	_poll_timer.one_shot = false
	_poll_timer.wait_time = 1.0 / maxf(poll_hz, 1.0)
	add_child(_poll_timer)
	_poll_timer.timeout.connect(_poll_once)
	_poll_timer.start()

	# Optional legacy signal path
	if allow_zwruntime_signals:
		_try_connect_zwruntime()

	_poll_once()


func _try_connect_zwruntime() -> void:
	if has_node("/root/ZWRuntime"):
		var zw = get_node("/root/ZWRuntime")
		if zw.has_signal("engine_summary_updated"):
			zw.engine_summary_updated.connect(update_summary)
		elif zw.has_signal("state_updated"):
			zw.state_updated.connect(_on_zw_state_updated)


func _poll_once() -> void:
	if _in_flight:
		return
	_in_flight = true

	var base := engainos_base_url.rstrip("/")
	var sid := scene_id
	var rm := reality_mode
	# Add small query params so EngAInOS can echo intended HUD context.
	# (Even if server ignores them, harmless.)
	var url := "%s/api/hud/engine_summary?scene_id=%s&reality_mode=%s" % [
		base,
		Uri.encode_www_form(sid),
		Uri.encode_www_form(rm),
	]

	var err := _http.request(url)
	if err != OK:
		_in_flight = false


func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray) -> void:
	_in_flight = false
	if response_code < 200 or response_code >= 300:
		return

	var text := body.get_string_from_utf8()
	var parsed := JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return

	# Basic monotonic protection if server provides tick
	var t := float(parsed.get("tick", 0.0))
	if t > 0.0 and t < _last_tick:
		# Ignore out-of-order responses
		return
	if t > 0.0:
		_last_tick = t

	update_summary(parsed)


func _process(_delta: float) -> void:
	queue_redraw()


# ── PUBLIC API ─────────────────────────────────────────────────

func update_summary(summary: Dictionary) -> void:
	_summary = summary
	queue_redraw()


# ── Optional fallback: build summary from raw snapshot (legacy) ─

func _on_zw_state_updated(snapshot: Dictionary) -> void:
	# Only used if allow_zwruntime_signals = true
	var entities: Dictionary = snapshot.get("entities", {})
	var player: Dictionary = entities.get("player", {})
	var combat: Dictionary = player.get("combat", {})
	var quest_data: Dictionary = snapshot.get("quest", {})
	var quests: Dictionary = quest_data.get("quests", {})

	var active := 0
	var completed := 0
	for qid in quests:
		var st: String = quests[qid].get("status", "")
		if st == "active": active += 1
		elif st == "completed": completed += 1

	var health: float = float(combat.get("health", 0.0))
	var combat_state := "idle"
	if health <= 0: combat_state = "dead"
	elif bool(combat.get("in_combat", false)) or bool(combat.get("engaged", false)): combat_state = "engaged"

	update_summary({
		"game_time": float(quest_data.get("tick", 0.0)),
		"scene_id": str(player.get("location", "unknown")),
		"active_quests": active,
		"completed_quests": completed,
		"combat_state": combat_state,
		"reality_mode": str(snapshot.get("reality_mode", "waking")),
		"player_health": health,
		"player_health_max": float(combat.get("max_health", 100.0)),
		"player_location": str(player.get("location", "unknown")),
		"entities_count": int(entities.size()),
		"tick_rate": float(snapshot.get("delta_time", 0.0)),
		"pillar_status": snapshot.get("pillar_status", {"engain": "running", "mvcar": "idle", "tv": "reserved"})
	})


# ── DRAWING ────────────────────────────────────────────────────

func _draw() -> void:
	if _summary.is_empty():
		_draw_idle()
		return

	var y := 0.0
	var pad := 8.0
	var lh := 14.0
	var rows: Array = []

	# Game time
	var gt: float = float(_summary.get("game_time", 0.0))
	rows.append({"label": "TIME", "value": "%.1fs" % gt, "color": color_value})

	# Scene / Location
	var scene: String = str(_summary.get("scene_id", "—"))
	rows.append({"label": "SCENE", "value": scene, "color": color_accent})

	# Reality mode
	var reality: String = str(_summary.get("reality_mode", "waking"))
	rows.append({"label": "REALITY", "value": reality.to_upper(), "color": _reality_color(reality)})

	# Combat
	var combat: String = str(_summary.get("combat_state", "idle"))
	var hp: float = float(_summary.get("player_health", 0.0))
	var hp_max: float = float(_summary.get("player_health_max", 100.0))
	var combat_text := "%s  HP %.0f/%.0f" % [combat.to_upper(), hp, hp_max]
	rows.append({"label": "COMBAT", "value": combat_text, "color": _combat_color(combat)})

	# Quests
	var aq: int = int(_summary.get("active_quests", 0))
	var cq: int = int(_summary.get("completed_quests", 0))
	rows.append({"label": "QUESTS", "value": "%d active  %d done" % [aq, cq], "color": color_value})

	# Entities
	var ec: int = int(_summary.get("entities_count", 0))
	rows.append({"label": "ENTITIES", "value": str(ec), "color": color_value})

	# Tick rate
	if show_tick_rate:
		var tr: float = float(_summary.get("tick_rate", 0.0))
		var fps_est := 1.0 / tr if tr > 0.0 else 0.0
		rows.append({"label": "TICK", "value": "%.1fms (%.0f fps)" % [tr * 1000.0, fps_est], "color": color_value})

	# Pillars
	if show_pillars:
		var ps: Dictionary = _summary.get("pillar_status", {})
		rows.append({"label": "PILLARS", "value": "", "color": color_label})
		for key in ["engain", "mvcar", "tv"]:
			var st: String = str(ps.get(key, "unknown"))
			rows.append({"label": "  " + key.to_upper(), "value": st, "color": _pillar_color(st)})

	var total_h := pad + rows.size() * lh + pad
	draw_rect(Rect2(0, 0, panel_width, total_h), color_bg)

	y = pad
	for row in rows:
		var label_text: String = row["label"]
		var value_text: String = row["value"]
		var val_color: Color = row["color"]

		draw_string(ThemeDB.fallback_font, Vector2(pad, y + 10), label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, color_label)
		if value_text != "":
			draw_string(ThemeDB.fallback_font, Vector2(pad + 70, y + 10), value_text, HORIZONTAL_ALIGNMENT_LEFT, int(panel_width - pad - 78), 9, val_color)
		y += lh

	custom_minimum_size = Vector2(panel_width, total_h)


# ── Color helpers ──────────────────────────────────────────────

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

