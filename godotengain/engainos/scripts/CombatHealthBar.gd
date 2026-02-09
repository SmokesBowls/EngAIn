# File: godot/scripts/CombatHealthBar.gd
# EngAInOS HUD consumer (polls /api/hud/combat)
# Authority:
#   NGAT-RT combat kernel => truth
#   EngAInOS facade       => stable HUD contract
#   This node             => visual only (lerp/ghost)

extends Control
class_name CombatHealthBar

@export var entity_id: String = "player"
@export var engainos_base_url: String = "http://127.0.0.1:8090"
@export var poll_hz: float = 10.0

@export var lerp_speed: float = 5.0
@export var damage_flash_speed: float = 2.0
@export var bar_height: float = 12.0
@export var bar_width: float = 200.0
@export var show_label: bool = true

@export var color_bg: Color = Color(0.12, 0.12, 0.12, 0.9)
@export var color_health: Color = Color(0.15, 0.85, 0.3, 1.0)
@export var color_damage_ghost: Color = Color(0.85, 0.15, 0.15, 0.6)
@export var color_heal_ghost: Color = Color(0.3, 0.9, 0.5, 0.4)
@export var color_low_health: Color = Color(0.9, 0.2, 0.1, 1.0)
@export var color_border: Color = Color(0.3, 0.3, 0.3, 0.8)

@export var low_health_threshold: float = 0.25

var actual_health: float = 100.0
var max_health: float = 100.0

var displayed_health: float = 100.0
var ghost_health: float = 100.0
var _pulse_time: float = 0.0
var _flash_alpha: float = 0.0
var _last_actual: float = 100.0

var _http: HTTPRequest
var _poll_timer: Timer
var _in_flight: bool = false


func _ready() -> void:
	custom_minimum_size = Vector2(bar_width, bar_height + (20.0 if show_label else 0.0))

	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)

	_poll_timer = Timer.new()
	_poll_timer.one_shot = false
	_poll_timer.wait_time = 1.0 / maxf(poll_hz, 1.0)
	add_child(_poll_timer)
	_poll_timer.timeout.connect(_poll_once)
	_poll_timer.start()

	_poll_once()


func _poll_once() -> void:
	if _in_flight:
		return
	_in_flight = true

	var url := "%s/api/hud/combat?entity=%s" % [engainos_base_url.rstrip("/"), Uri.encode_www_form(entity_id)]
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

	_apply_hud_combat(parsed)


func _apply_hud_combat(hud: Dictionary) -> void:
	# Expected:
	# { "entity":"player","health":100,"max_health":100,"alive":true,... }
	if not hud.has("health"):
		return

	var new_health := float(hud.get("health", actual_health))
	var new_max := float(hud.get("max_health", max_health))

	_last_actual = actual_health
	max_health = maxf(new_max, 1.0)
	actual_health = clampf(new_health, 0.0, max_health)

	if actual_health < _last_actual:
		ghost_health = _last_actual
		_flash_alpha = 1.0
	elif actual_health > _last_actual:
		ghost_health = _last_actual


func _process(delta: float) -> void:
	displayed_health = lerpf(displayed_health, actual_health, lerp_speed * delta)
	if absf(displayed_health - actual_health) < 0.1:
		displayed_health = actual_health

	if ghost_health > actual_health:
		ghost_health = lerpf(ghost_health, actual_health, damage_flash_speed * delta)
		if absf(ghost_health - actual_health) < 0.1:
			ghost_health = actual_health
	elif ghost_health < actual_health:
		ghost_health = lerpf(ghost_health, actual_health, lerp_speed * 1.5 * delta)
		if absf(ghost_health - actual_health) < 0.1:
			ghost_health = actual_health

	if _flash_alpha > 0.0:
		_flash_alpha = maxf(0.0, _flash_alpha - delta * 3.0)

	var ratio := actual_health / maxf(max_health, 1.0)
	if ratio <= low_health_threshold and actual_health > 0.0:
		_pulse_time += delta * 4.0
	else:
		_pulse_time = 0.0

	queue_redraw()


func _draw() -> void:
	var ratio_max := maxf(max_health, 1.0)
	var display_ratio := clampf(displayed_health / ratio_max, 0.0, 1.0)
	var ghost_ratio := clampf(ghost_health / ratio_max, 0.0, 1.0)
	var actual_ratio := clampf(actual_health / ratio_max, 0.0, 1.0)

	var y_offset := 0.0
	if show_label:
		var font := ThemeDB.fallback_font
		var font_size := 11
		var label_text := "%s: %d / %d" % [entity_id, ceili(displayed_health), ceili(max_health)]
		draw_string(font, Vector2(0, font_size), label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(0.8, 0.8, 0.8))
		y_offset = font_size + 4.0

	var bar_rect := Rect2(0, y_offset, bar_width, bar_height)
	draw_rect(bar_rect, color_bg)

	if ghost_ratio > display_ratio:
		draw_rect(Rect2(0, y_offset, bar_width * ghost_ratio, bar_height), color_damage_ghost)

	if ghost_ratio < display_ratio:
		draw_rect(Rect2(bar_width * ghost_ratio, y_offset, bar_width * (display_ratio - ghost_ratio), bar_height), color_heal_ghost)

	var health_color := color_health
	if actual_ratio <= low_health_threshold and actual_health > 0.0:
		var pulse := (sin(_pulse_time) + 1.0) * 0.5
		health_color = color_health.lerp(color_low_health, pulse)

	draw_rect(Rect2(0, y_offset, bar_width * display_ratio, bar_height), health_color)

	if _flash_alpha > 0.0:
		draw_rect(bar_rect, Color(1.0, 1.0, 1.0, _flash_alpha * 0.3))

	draw_rect(bar_rect, color_border, false, 1.0)

	for i in range(1, 4):
		var tick_x := bar_width * (i / 4.0)
		draw_line(Vector2(tick_x, y_offset), Vector2(tick_x, y_offset + bar_height), Color(0.0, 0.0, 0.0, 0.3), 1.0)

