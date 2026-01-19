extends Control

## GovernedHUD.gd - High-fidelity visual monitor for the EngAIn system.
## Uses semi-transparent panels and neon accents.

@onready var zw_runtime = get_tree().get_first_node_in_group("zw_runtime")

func _ready() -> void:
	# Set up visual style (simulated glassmorphism via shader/modulate)
	$Panel.modulate = Color(0, 0.5, 0.8, 0.6) # Semi-transparent Cyan
	
	if zw_runtime:
		zw_runtime.state_changed.connect(_on_state_updated)

func _on_state_updated(state: Dictionary) -> void:
	# Update UI elements with state data
	_update_history_feed(state.get("history", []))
	_update_shadow_pulse(state.get("shadow", {}))

func _update_history_feed(history: Array) -> void:
	if history.size() > 0:
		var latest = history.back()
		print("[GovernedHUD] New Causality Event: ", latest)
		# Flash neon cyan for Xeon history
		_trigger_causality_flash(Color(0, 1, 1, 0.8))

func _trigger_causality_flash(flash_color: Color) -> void:
	# Create a temporary flash overlay
	var flash = ColorRect.new()
	flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	flash.color = flash_color
	add_child(flash)
	
	var tween = create_tween()
	tween.tween_property(flash, "modulate:a", 0.0, 0.5)
	tween.tween_callback(flash.queue_free)

func _update_shadow_pulse(_shadow: Dictionary) -> void:
	# Flash a red light if new failures are detected
	pass

func _on_attack_button_pressed() -> void:
	# Example user interaction: trigger a governed attack
	if zw_runtime:
		zw_runtime.submit_attack("player", "warden", 10.0, 2) # Tier 2 Soft Override
