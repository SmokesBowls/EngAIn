# File: scripts/test_quest_tracker.gd
# Test harness for Quest3D — QuestTracker visual endpoint
#
# Attach to a Node2D in a test scene. Simulates the full quest
# lifecycle so you can SEE the tracker rendering without Python.
#
# Once verified, remove this. Real quest state comes from ZWRuntime.

extends Node2D

# ── State ──────────────────────────────────────────────────────
var _tracker: QuestTracker = null
var _game_time: float = 0.0
var _quest_state: Dictionary = {"quests": {}, "tick": 0.0}
var _event_log: Array[String] = []
var _auto_demo: bool = false
var _demo_phase: int = -1
var _demo_timer: float = 0.0

# ── UI refs ────────────────────────────────────────────────────
var _instructions: Label
var _log_label: RichTextLabel


func _ready() -> void:
	# Create QuestTracker instance
	_tracker = QuestTracker.new()
	_tracker.name = "QuestTracker"
	_tracker.position = Vector2(30, 30)
	_tracker.show_completed = true
	_tracker.show_failed = true
	_tracker.max_visible_quests = 6
	add_child(_tracker)

	# Connect signals
	_tracker.quest_state_changed.connect(func(qid, status):
		match status:
			"active": _log("▶ ACTIVATED: %s" % qid)
			"completed": _log("✓ COMPLETED: %s" % qid)
			"failed": _log("✗ FAILED: %s" % qid)
	)
	_tracker.objective_state_changed.connect(func(qid, oid, status):
		if status == "satisfied":
			_log("  ✓ OBJ: %s → %s" % [qid, oid])
	)

	# Build UI
	_build_ui()

	# Register sample quests
	_register_sample_quests()
	_push_state()

	_log("Press 1-7 for actions, A for auto-demo, R to reset")


func _process(delta: float) -> void:
	_game_time += delta

	if _auto_demo:
		_demo_timer -= delta
		if _demo_timer <= 0.0:
			_advance_demo()

	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed:
		return

	match event.keycode:
		KEY_1:
			_activate_quest("q_find_sword")
		KEY_2:
			_satisfy_objective("q_find_sword", "obj_go_ruins")
		KEY_3:
			_satisfy_objective("q_find_sword", "obj_get_sword")
		KEY_4:
			_activate_quest("q_timed_delivery")
		KEY_5:
			_fail_quest("q_timed_delivery")
		KEY_6:
			_activate_quest("q_chain_start")
		KEY_7:
			_satisfy_objective("q_chain_start", "obj_talk_elder")
		KEY_A:
			_auto_demo = not _auto_demo
			_demo_phase = -1
			_demo_timer = 0.0
			_log("Auto demo: %s" % ("ON" if _auto_demo else "OFF"))
		KEY_R:
			_reset()


# ── Quest manipulation ─────────────────────────────────────────

func _register_sample_quests() -> void:
	_quest_state = {
		"quests": {
			"q_find_sword": {
				"id": "q_find_sword",
				"title": "Find the Lost Sword",
				"description": "Retrieve the ancient blade from the ruins.",
				"status": "inactive",
				"objectives": [
					{"id": "obj_go_ruins", "description": "Travel to the ruins", "status": "pending", "optional": false},
					{"id": "obj_get_sword", "description": "Pick up the sword", "status": "pending", "optional": false},
				],
				"activated_at_tick": - 1.0,
				"completed_at_tick": - 1.0,
				"failed_at_tick": - 1.0,
			},
			"q_timed_delivery": {
				"id": "q_timed_delivery",
				"title": "Urgent Delivery",
				"description": "Deliver the package before time runs out.",
				"status": "inactive",
				"objectives": [
					{"id": "obj_get_package", "description": "Pick up the package", "status": "pending", "optional": false},
					{"id": "obj_deliver", "description": "Deliver to the market", "status": "pending", "optional": false},
				],
				"activated_at_tick": - 1.0,
				"completed_at_tick": - 1.0,
				"failed_at_tick": - 1.0,
			},
			"q_chain_start": {
				"id": "q_chain_start",
				"title": "The Elder's Request",
				"description": "Speak with the village elder.",
				"status": "inactive",
				"objectives": [
					{"id": "obj_talk_elder", "description": "Talk to the elder", "status": "pending", "optional": false},
					{"id": "obj_accept_task", "description": "Accept the task", "status": "pending", "optional": false},
					{"id": "obj_gather_herbs", "description": "Gather moonlit herbs", "status": "pending", "optional": true},
				],
				"activated_at_tick": - 1.0,
				"completed_at_tick": - 1.0,
				"failed_at_tick": - 1.0,
			},
		},
		"tick": 0.0
	}


func _activate_quest(quest_id: String) -> void:
	var quest = _quest_state["quests"].get(quest_id)
	if quest and quest["status"] == "inactive":
		quest["status"] = "active"
		quest["activated_at_tick"] = _game_time
		_log("Activated: %s" % quest_id)
		_push_state()
	else:
		_log("Cannot activate: %s (status=%s)" % [quest_id, quest["status"] if quest else "missing"])


func _satisfy_objective(quest_id: String, obj_id: String) -> void:
	var quest = _quest_state["quests"].get(quest_id)
	if not quest or quest["status"] != "active":
		_log("Quest not active: %s" % quest_id)
		return

	var objectives: Array = quest["objectives"]
	for obj in objectives:
		if obj["id"] == obj_id and obj["status"] == "pending":
			obj["status"] = "satisfied"
			_log("Satisfied: %s → %s" % [quest_id, obj_id])

			# Check if all required objectives done
			var required = objectives.filter(func(o): return not o.get("optional", false))
			if required.all(func(o): return o["status"] == "satisfied"):
				quest["status"] = "completed"
				quest["completed_at_tick"] = _game_time
				_log("QUEST COMPLETED: %s" % quest_id)

			_push_state()
			return

	_log("Objective not found/already done: %s" % obj_id)


func _fail_quest(quest_id: String) -> void:
	var quest = _quest_state["quests"].get(quest_id)
	if quest and quest["status"] == "active":
		quest["status"] = "failed"
		quest["failed_at_tick"] = _game_time
		_log("FAILED: %s" % quest_id)
		_push_state()


func _push_state() -> void:
	_quest_state["tick"] = _game_time
	_tracker.load_from_dict(_quest_state)


func _reset() -> void:
	_auto_demo = false
	_demo_phase = -1
	_game_time = 0.0
	_register_sample_quests()
	_tracker._prev_statuses.clear()
	_tracker._prev_obj_statuses.clear()
	_push_state()
	_log("RESET")


# ── Auto demo ──────────────────────────────────────────────────

func _advance_demo() -> void:
	_demo_phase += 1
	_demo_timer = 1.5

	match _demo_phase:
		0: _activate_quest("q_find_sword")
		1: _activate_quest("q_timed_delivery")
		2: _satisfy_objective("q_find_sword", "obj_go_ruins")
		3: _activate_quest("q_chain_start")
		4: _satisfy_objective("q_timed_delivery", "obj_get_package")
		5: _satisfy_objective("q_find_sword", "obj_get_sword") # completes quest
		6: _fail_quest("q_timed_delivery")
		7: _satisfy_objective("q_chain_start", "obj_talk_elder")
		8: _satisfy_objective("q_chain_start", "obj_accept_task") # completes (herbs optional)
		9:
			_log("Demo complete")
			_auto_demo = false


# ── UI ─────────────────────────────────────────────────────────

func _build_ui() -> void:
	_instructions = Label.new()
	_instructions.position = Vector2(30, 520)
	_instructions.add_theme_font_size_override("font_size", 10)
	_instructions.add_theme_color_override("font_color", Color(0.35, 0.35, 0.4))
	_instructions.text = "1: Activate Sword Quest  2: Obj→Ruins  3: Obj→Sword  4: Activate Delivery  5: Fail Delivery\n6: Activate Elder  7: Obj→Talk  A: Auto-Demo  R: Reset"
	add_child(_instructions)

	_log_label = RichTextLabel.new()
	_log_label.position = Vector2(380, 30)
	_log_label.size = Vector2(350, 480)
	_log_label.bbcode_enabled = true
	_log_label.scroll_following = true
	_log_label.add_theme_font_size_override("normal_font_size", 10)
	add_child(_log_label)


func _log(msg: String) -> void:
	var ts := "%.1f" % _game_time
	_event_log.append("[%s] %s" % [ts, msg])
	if _event_log.size() > 40:
		_event_log = _event_log.slice(-40)

	if _log_label:
		_log_label.clear()
		_log_label.append_text("[color=#666]Quest Event Log[/color]\n")
		for entry in _event_log:
			_log_label.append_text(entry + "\n")
