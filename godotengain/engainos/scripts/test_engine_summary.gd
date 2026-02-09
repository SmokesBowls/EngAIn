# File: scripts/test_engine_summary.gd
# Test harness for EngineSummaryHUD
#
# Attach to a Node2D. Simulates engine state changes.
# Once verified, remove. Real data comes from ZWRuntime.

extends Node2D

var _hud: EngineSummaryHUD = null
var _game_time: float = 0.0
var _running: bool = true
var _reality_mode: String = "waking"
var _combat_state: String = "idle"
var _health: float = 100.0
var _active_quests: int = 2
var _completed_quests: int = 1
var _location: String = "village_square"
var _entities: int = 5
var _pillar_mvcar: String = "idle"

var _reality_modes: Array = ["waking", "dream", "memory", "liminal"]
var _reality_idx: int = 0
var _locations: Array = ["village_square", "ancient_ruins", "dark_forest", "crystal_cave", "throne_room"]
var _location_idx: int = 0

var _log_label: RichTextLabel
var _instructions: Label


func _ready() -> void:
	_hud = EngineSummaryHUD.new()
	_hud.name = "EngineSummaryHUD"
	_hud.position = Vector2(40, 40)
	_hud.show_pillars = true
	_hud.show_tick_rate = true
	add_child(_hud)

	_build_ui()
	_push_state()


func _process(delta: float) -> void:
	if _running:
		_game_time += delta
		_push_state()


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed:
		return

	match event.keycode:
		KEY_SPACE:
			_running = not _running
			_log("Paused" if not _running else "Running")
		KEY_R:
			_reality_idx = (_reality_idx + 1) % _reality_modes.size()
			_reality_mode = _reality_modes[_reality_idx]
			_log("Reality → %s" % _reality_mode)
		KEY_C:
			match _combat_state:
				"idle": _combat_state = "engaged"
				"engaged": _combat_state = "dead"
				"dead": _combat_state = "idle"
			if _combat_state == "dead":
				_health = 0.0
			elif _combat_state == "engaged":
				_health = clampf(_health, 1.0, 100.0)
			else:
				_health = 100.0
			_log("Combat → %s (HP: %.0f)" % [_combat_state, _health])
		KEY_L:
			_location_idx = (_location_idx + 1) % _locations.size()
			_location = _locations[_location_idx]
			_log("Location → %s" % _location)
		KEY_Q:
			_active_quests = (_active_quests + 1) % 8
			_log("Active quests → %d" % _active_quests)
		KEY_D:
			_completed_quests += 1
			_log("Completed quests → %d" % _completed_quests)
		KEY_M:
			match _pillar_mvcar:
				"idle": _pillar_mvcar = "running"
				"running": _pillar_mvcar = "error"
				"error": _pillar_mvcar = "idle"
			_log("MV-CAR → %s" % _pillar_mvcar)
		KEY_UP:
			_health = clampf(_health + 10, 0, 100)
			_log("HP → %.0f" % _health)
		KEY_DOWN:
			_health = clampf(_health - 10, 0, 100)
			if _health <= 0:
				_combat_state = "dead"
			_log("HP → %.0f" % _health)


func _push_state() -> void:
	_hud.update_summary({
		"game_time": _game_time,
		"scene_id": _location,
		"active_quests": _active_quests,
		"completed_quests": _completed_quests,
		"combat_state": _combat_state,
		"reality_mode": _reality_mode,
		"player_health": _health,
		"player_health_max": 100.0,
		"player_location": _location,
		"entities_count": _entities,
		"tick_rate": get_process_delta_time(),
		"pillar_status": {
			"engain": "running",
			"mvcar": _pillar_mvcar,
			"tv": "reserved"
		}
	})


func _build_ui() -> void:
	_instructions = Label.new()
	_instructions.position = Vector2(40, 320)
	_instructions.add_theme_font_size_override("font_size", 10)
	_instructions.add_theme_color_override("font_color", Color(0.35, 0.35, 0.4))
	_instructions.text = "SPACE: pause  R: reality mode  C: combat state  L: location\nQ: +quest  D: +completed  M: mvcar status  UP/DOWN: HP"
	add_child(_instructions)

	_log_label = RichTextLabel.new()
	_log_label.position = Vector2(320, 40)
	_log_label.size = Vector2(280, 260)
	_log_label.bbcode_enabled = true
	_log_label.scroll_following = true
	_log_label.add_theme_font_size_override("normal_font_size", 10)
	add_child(_log_label)
	_log_label.append_text("[color=#666]Engine Summary Log[/color]\n")


func _log(msg: String) -> void:
	var ts := "%.1f" % _game_time
	if _log_label:
		_log_label.append_text("[%s] %s\n" % [ts, msg])
