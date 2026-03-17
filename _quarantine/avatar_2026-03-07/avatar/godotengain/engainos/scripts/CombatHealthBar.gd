# File: scripts/CombatHealthBar.gd
# CombatHealthBar — Production View-Only Health Display
#
# Authority model:
#   Python combat3d_mr.py  →  actual_health (truth)
#   ZWRuntime               →  polls /api/hud/combat, emits combat_updated
#   This node               →  lerps + renders. Nothing else.
#
# Contract shape (from /api/hud/combat?entity=player):
#   { "entity_id", "health", "max_health", "wound_state",
#     "damage_events": [...], "heal_events": [...] }
#
# No local health rules. No apply_damage(). Python owns all combat math.

extends Control
class_name CombatHealthBar

# ── Configuration ────────────────────────────────────────────
@export var entity_id: String = "player"
@export var lerp_speed: float = 5.0
@export var damage_flash_speed: float = 2.0
@export var bar_height: float = 12.0
@export var bar_width: float = 200.0
@export var show_label: bool = true

# ── Colors ───────────────────────────────────────────────────
@export var color_bg: Color = Color(0.12, 0.12, 0.12, 0.9)
@export var color_health: Color = Color(0.15, 0.85, 0.3, 1.0)
@export var color_damage_ghost: Color = Color(0.85, 0.15, 0.15, 0.6)
@export var color_heal_ghost: Color = Color(0.3, 0.9, 0.5, 0.4)
@export var color_low_health: Color = Color(0.9, 0.2, 0.1, 1.0)
@export var color_border: Color = Color(0.3, 0.3, 0.3, 0.8)

# ── Thresholds ───────────────────────────────────────────────
@export var low_health_threshold: float = 0.25

# ── State (from Python — READ ONLY) ─────────────────────────
var actual_health: float = 100.0
var max_health: float = 100.0

# ── Visual state (this node owns these) ─────────────────────
var displayed_health: float = 100.0
var ghost_health: float = 100.0
var _pulse_time: float = 0.0
var _flash_alpha: float = 0.0
var _last_actual: float = 100.0
var _has_data: bool = false


func _ready() -> void:
	custom_minimum_size = Vector2(bar_width, bar_height + (20.0 if show_label else 0.0))
	ZWRuntime.combat_updated.connect(_on_combat_updated)


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
	if not _has_data:
		_draw_idle()
		return

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


# ── Signal consumers ─────────────────────────────────────────

func _on_combat_updated(data: Dictionary) -> void:
	var eid: String = data.get("entity_id", "")
	if eid != entity_id and eid != "":
		return
	_apply_health_change(float(data.get("health", actual_health)), float(data.get("max_health", max_health)))


func _apply_health_change(new_health: float, new_max: float) -> void:
	_has_data = true
	_last_actual = actual_health
	max_health = new_max
	actual_health = new_health
	if new_health < _last_actual:
		ghost_health = _last_actual
		_flash_alpha = 1.0
	elif new_health > _last_actual:
		ghost_health = _last_actual


func _draw_idle() -> void:
	var h := bar_height + (20.0 if show_label else 0.0)
	draw_rect(Rect2(0, 0, bar_width, h), color_bg)
	draw_string(ThemeDB.fallback_font, Vector2(4, 12), "HP — awaiting state", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.35, 0.35, 0.4))
