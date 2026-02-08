# File: godot/scripts/test_combat_healthbar.gd
# Test harness for Fix #3 — Combat Health Bar Smoothing
#
# Attach this to a Node in your test scene.
# It creates a CombatHealthBar and fires dummy damage/heal events
# so you can SEE the lerp, ghost trail, and pulse working
# without needing the Python kernel running.
#
# Once verified, remove this script. The real data comes from
# ZWRuntime snapshots via combat3d_integration.py.

extends Node

var health_bar: CombatHealthBar
var _test_timer: float = 0.0
var _test_phase: int = 0
var _label: Label


func _ready() -> void:
	# ── Create the health bar ──
	health_bar = CombatHealthBar.new()
	health_bar.entity_id = "player"
	health_bar.bar_width = 300.0
	health_bar.bar_height = 16.0
	health_bar.show_label = true
	health_bar.position = Vector2(40, 40)
	add_child(health_bar)
	
	# ── Info label ──
	_label = Label.new()
	_label.position = Vector2(40, 90)
	_label.add_theme_font_size_override("font_size", 13)
	_label.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))
	add_child(_label)
	
	# ── Instruction label ──
	var instructions := Label.new()
	instructions.position = Vector2(40, 120)
	instructions.add_theme_font_size_override("font_size", 12)
	instructions.add_theme_color_override("font_color", Color(0.4, 0.4, 0.4))
	instructions.text = "Press 1: Small hit  |  2: Big hit  |  3: Heal  |  4: Full heal  |  5: Kill  |  R: Reset"
	add_child(instructions)
	
	# Start the auto-demo sequence
	_update_label()


func _process(delta: float) -> void:
	_update_label()
	
	# ── Manual input for testing ──
	if Input.is_action_just_pressed("ui_text_delete"):  # Key 1
		pass  # Fallback to _unhandled_input
	
	# ── Auto-demo (runs if you don't touch anything) ──
	_test_timer += delta
	if _test_timer > 2.5:
		_test_timer = 0.0
		_run_auto_phase()


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed:
		return
	
	match event.keycode:
		KEY_1:
			health_bar.apply_damage(15.0)
			_reset_auto()
		KEY_2:
			health_bar.apply_damage(40.0)
			_reset_auto()
		KEY_3:
			health_bar.apply_heal(20.0)
			_reset_auto()
		KEY_4:
			health_bar.set_health(health_bar.max_health)
			_reset_auto()
		KEY_5:
			health_bar.set_health(0.0)
			_reset_auto()
		KEY_R:
			health_bar.set_health(100.0, 100.0)
			health_bar.displayed_health = 100.0
			health_bar.ghost_health = 100.0
			_test_phase = 0
			_test_timer = 0.0


func _run_auto_phase() -> void:
	match _test_phase:
		0:  # Small hit
			health_bar.apply_damage(12.0)
		1:  # Another small hit
			health_bar.apply_damage(18.0)
		2:  # Big hit
			health_bar.apply_damage(35.0)
		3:  # Partial heal
			health_bar.apply_heal(25.0)
		4:  # Critical hit (should trigger low-health pulse)
			health_bar.apply_damage(45.0)
		5:  # Heal back up
			health_bar.set_health(80.0)
		6:  # Reset
			health_bar.set_health(100.0, 100.0)
			health_bar.displayed_health = 100.0
			health_bar.ghost_health = 100.0
			_test_phase = -1  # Will wrap to 0
	
	_test_phase = (_test_phase + 1) % 7


func _reset_auto() -> void:
	_test_timer = 0.0
	_test_phase = 0


func _update_label() -> void:
	if _label and health_bar:
		_label.text = "actual: %.1f  |  displayed: %.1f  |  ghost: %.1f  |  max: %.1f" % [
			health_bar.actual_health,
			health_bar.displayed_health,
			health_bar.ghost_health,
			health_bar.max_health
		]
