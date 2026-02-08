# File: godot/scripts/CombatHealthBar.gd
# Fix #3 — Health Bar Smoothing
# Pure visual layer. Kernel owns actual_health, this node lerps display.
#
# Authority model:
#   Python combat3d_mr.py  →  actual_health (truth)
#   This node              →  displayed_health (visual only)
#   Godot never modifies actual_health. Ever.
#
# Drop into your Combat3D scene. Connects to ZWRuntime snapshot signal.

extends Control
class_name CombatHealthBar

# ── Configuration ──────────────────────────────────────────────
@export var entity_id: String = "player"
@export var lerp_speed: float = 5.0        # Higher = snappier response
@export var damage_flash_speed: float = 2.0 # Ghost bar trails behind
@export var bar_height: float = 12.0
@export var bar_width: float = 200.0
@export var show_label: bool = true

# ── Colors ─────────────────────────────────────────────────────
@export var color_bg: Color = Color(0.12, 0.12, 0.12, 0.9)
@export var color_health: Color = Color(0.15, 0.85, 0.3, 1.0)
@export var color_damage_ghost: Color = Color(0.85, 0.15, 0.15, 0.6)
@export var color_heal_ghost: Color = Color(0.3, 0.9, 0.5, 0.4)
@export var color_low_health: Color = Color(0.9, 0.2, 0.1, 1.0)
@export var color_border: Color = Color(0.3, 0.3, 0.3, 0.8)

# ── Thresholds ─────────────────────────────────────────────────
@export var low_health_threshold: float = 0.25  # Below 25% = red + pulse

# ── State (from kernel snapshot — READ ONLY) ───────────────────
var actual_health: float = 100.0
var max_health: float = 100.0

# ── Visual state (this node owns these) ────────────────────────
var displayed_health: float = 100.0
var ghost_health: float = 100.0   # Trails behind on damage, leads on heal
var _pulse_time: float = 0.0
var _flash_alpha: float = 0.0
var _last_actual: float = 100.0   # For detecting damage/heal events


func _ready() -> void:
	custom_minimum_size = Vector2(bar_width, bar_height + (20.0 if show_label else 0.0))
	
	# Connect to ZWRuntime if it exists as autoload
	if Engine.has_singleton("ZWRuntime"):
		var zw = Engine.get_singleton("ZWRuntime")
		if zw.has_signal("state_updated"):
			zw.state_updated.connect(_on_zw_state_updated)
	elif has_node("/root/ZWRuntime"):
		var zw = get_node("/root/ZWRuntime")
		if zw.has_signal("state_updated"):
			zw.state_updated.connect(_on_zw_state_updated)


func _process(delta: float) -> void:
	# ── Lerp displayed_health toward actual_health ──
	var prev_displayed := displayed_health
	displayed_health = lerpf(displayed_health, actual_health, lerp_speed * delta)
	
	# Snap if close enough (avoid infinite asymptotic crawl)
	if absf(displayed_health - actual_health) < 0.1:
		displayed_health = actual_health
	
	# ── Ghost bar logic ──
	if ghost_health > actual_health:
		# Damage ghost: trails behind, fades slowly
		ghost_health = lerpf(ghost_health, actual_health, damage_flash_speed * delta)
		if absf(ghost_health - actual_health) < 0.1:
			ghost_health = actual_health
	elif ghost_health < actual_health:
		# Heal: ghost catches up faster
		ghost_health = lerpf(ghost_health, actual_health, lerp_speed * 1.5 * delta)
		if absf(ghost_health - actual_health) < 0.1:
			ghost_health = actual_health
	
	# ── Flash on damage ──
	if _flash_alpha > 0.0:
		_flash_alpha = maxf(0.0, _flash_alpha - delta * 3.0)
	
	# ── Low health pulse ──
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
	
	# ── Label ──
	if show_label:
		var font := ThemeDB.fallback_font
		var font_size := 11
		var label_text := "%s: %d / %d" % [entity_id, ceili(displayed_health), ceili(max_health)]
		var text_pos := Vector2(0, font_size)
		draw_string(font, text_pos, label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, Color(0.8, 0.8, 0.8))
		y_offset = font_size + 4.0
	
	var bar_rect := Rect2(0, y_offset, bar_width, bar_height)
	
	# ── Background ──
	draw_rect(bar_rect, color_bg)
	
	# ── Ghost bar (damage trail — red, behind current) ──
	if ghost_ratio > display_ratio:
		var ghost_rect := Rect2(0, y_offset, bar_width * ghost_ratio, bar_height)
		draw_rect(ghost_rect, color_damage_ghost)
	
	# ── Ghost bar (heal trail — green glow, ahead of current) ──
	if ghost_ratio < display_ratio:
		var heal_rect := Rect2(bar_width * ghost_ratio, y_offset, bar_width * (display_ratio - ghost_ratio), bar_height)
		draw_rect(heal_rect, color_heal_ghost)
	
	# ── Main health bar ──
	var health_color := color_health
	if actual_ratio <= low_health_threshold and actual_health > 0.0:
		# Pulse between health and low_health colors
		var pulse := (sin(_pulse_time) + 1.0) * 0.5
		health_color = color_health.lerp(color_low_health, pulse)
	
	var health_rect := Rect2(0, y_offset, bar_width * display_ratio, bar_height)
	draw_rect(health_rect, health_color)
	
	# ── Damage flash overlay ──
	if _flash_alpha > 0.0:
		var flash_color := Color(1.0, 1.0, 1.0, _flash_alpha * 0.3)
		draw_rect(bar_rect, flash_color)
	
	# ── Border ──
	draw_rect(bar_rect, color_border, false, 1.0)
	
	# ── Tick marks at 25% intervals ──
	for i in range(1, 4):
		var tick_x := bar_width * (i / 4.0)
		draw_line(
			Vector2(tick_x, y_offset),
			Vector2(tick_x, y_offset + bar_height),
			Color(0.0, 0.0, 0.0, 0.3),
			1.0
		)


# ── Snapshot consumer ──────────────────────────────────────────
# This is the ONLY place actual_health gets updated.
# Python is authority. Godot just renders.

func _on_zw_state_updated(snapshot: Dictionary) -> void:
	# Expected snapshot shape from combat3d_integration.py:
	# {
	#   "entities": {
	#     "player": {
	#       "combat": { "health": 75.0, "max_health": 100.0, ... }
	#     }
	#   }
	# }
	var entities: Dictionary = snapshot.get("entities", {})
	var entity_data: Dictionary = entities.get(entity_id, {})
	var combat: Dictionary = entity_data.get("combat", {})
	
	if combat.is_empty():
		return
	
	var new_health: float = float(combat.get("health", actual_health))
	var new_max: float = float(combat.get("max_health", max_health))
	
	_last_actual = actual_health
	max_health = new_max
	actual_health = new_health
	
	# Detect damage vs heal for ghost bar seeding
	if new_health < _last_actual:
		# Damage: ghost stays at old value, trails down
		ghost_health = _last_actual
		_flash_alpha = 1.0
	elif new_health > _last_actual:
		# Heal: ghost stays at old value, main bar leads
		ghost_health = _last_actual


# ── Manual API (for testing without ZWRuntime) ─────────────────

func set_health(health: float, max_hp: float = -1.0) -> void:
	"""Call this directly for testing. In production, use snapshot signal."""
	if max_hp > 0.0:
		max_health = max_hp
	_last_actual = actual_health
	actual_health = clampf(health, 0.0, max_health)
	
	if actual_health < _last_actual:
		ghost_health = _last_actual
		_flash_alpha = 1.0
	elif actual_health > _last_actual:
		ghost_health = _last_actual


func apply_damage(amount: float) -> void:
	"""Convenience: subtract from current. Kernel should be authority, but useful for testing."""
	set_health(actual_health - amount)


func apply_heal(amount: float) -> void:
	"""Convenience: add to current."""
	set_health(actual_health + amount)
