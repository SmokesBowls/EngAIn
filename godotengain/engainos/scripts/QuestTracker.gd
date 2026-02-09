# File: scripts/QuestTracker.gd
# Quest3D Godot Endpoint — Summary-Only Quest Tracker
#
# Authority model:
#   Python quest3d_mr.py          →  quest state (truth)
#   Python ap_quest_rules.py      →  lifecycle rules (AP)
#   Python get_quest_summaries()  →  flat summary list (projection)
#   This node                     →  renders summaries. Nothing else.
#
# This node consumes QuestSummary, NOT raw quest data.
# Summary shape (from kernel):
#   {
#     "id": str, "title": str, "status": str, "description": str,
#     "progress": float (0.0-1.0),
#     "objectives_done": int, "objectives_total": int,
#     "objectives": [{"id", "description", "status", "optional"}]
#   }
#
# Integration (one line):
#   ZWRuntime emits quest_summaries → QuestTracker.update_summaries(list)

extends Control
class_name QuestTracker

# ── Signals ────────────────────────────────────────────────────
signal quest_state_changed(quest_id: String, new_status: String)
signal objective_state_changed(quest_id: String, objective_id: String, new_status: String)

# ── Configuration ──────────────────────────────────────────────
@export var show_completed: bool = false
@export var show_failed: bool = false
@export var max_visible_quests: int = 5
@export var panel_width: float = 320.0
@export var compact_mode: bool = false

# ── Colors ─────────────────────────────────────────────────────
@export var color_bg: Color = Color(0.08, 0.08, 0.10, 0.85)
@export var color_header: Color = Color(0.75, 0.75, 0.80)
@export var color_active: Color = Color(0.9, 0.85, 0.4)
@export var color_completed: Color = Color(0.3, 0.85, 0.4)
@export var color_failed: Color = Color(0.85, 0.25, 0.2)
@export var color_inactive: Color = Color(0.4, 0.4, 0.4)
@export var color_obj_pending: Color = Color(0.55, 0.55, 0.55)
@export var color_obj_done: Color = Color(0.4, 0.8, 0.45)
@export var color_obj_failed: Color = Color(0.7, 0.25, 0.2)
@export var color_border: Color = Color(0.25, 0.25, 0.3, 0.6)
@export var color_bar_bg: Color = Color(0.15, 0.15, 0.18)
@export var color_bar_fill: Color = Color(0.4, 0.7, 0.9)

# ── State (summaries only — no quest internals) ────────────────
var _summaries: Array = []
var _prev_statuses: Dictionary = {}
var _prev_obj_statuses: Dictionary = {}
var _flash_timers: Dictionary = {}
var _obj_flash_timers: Dictionary = {}


func _ready() -> void:
	if has_node("/root/ZWRuntime"):
		var zw = get_node("/root/ZWRuntime")
		if zw.has_signal("quest_summaries_updated"):
			zw.quest_summaries_updated.connect(update_summaries)
		elif zw.has_signal("state_updated"):
			zw.state_updated.connect(_on_zw_state_updated)


func _process(delta: float) -> void:
	for key in _flash_timers.keys():
		_flash_timers[key] = maxf(0.0, _flash_timers[key] - delta)
	for key in _obj_flash_timers.keys():
		_obj_flash_timers[key] = maxf(0.0, _obj_flash_timers[key] - delta)
	queue_redraw()


# ── PUBLIC API ─────────────────────────────────────────────────

func update_summaries(summaries: Array) -> void:
	"""THE integration point. Feed QuestSummary list from kernel."""
	_detect_changes(summaries)
	_summaries = summaries
	queue_redraw()


# ── Fallback: extract summaries from raw snapshot ──────────────

func _on_zw_state_updated(snapshot: Dictionary) -> void:
	"""Fallback: if ZWRuntime sends raw snapshots, build summaries here."""
	var quests: Dictionary = snapshot.get("quest", {}).get("quests", {})
	var summaries: Array = []
	for qid in quests:
		var q: Dictionary = quests[qid]
		var objectives: Array = q.get("objectives", [])
		var total := objectives.size()
		var done := objectives.filter(func(o): return o.get("status") == "satisfied").size()
		summaries.append({
			"id": qid,
			"title": q.get("title", qid) as String,
			"status": q.get("status", "inactive") as String,
			"description": q.get("description", "") as String,
			"progress": float(done) / float(total) if total > 0 else 0.0,
			"objectives_done": done,
			"objectives_total": total,
			"objectives": objectives.map(func(o: Dictionary): return {
				"id": o.get("id", "") as String,
				"description": o.get("description", "") as String,
				"status": o.get("status", "pending") as String,
				"optional": o.get("optional", false) as bool,
			})
		})
	update_summaries(summaries)


# ── Manual API (testing) ───────────────────────────────────────

func load_from_dict(quest_data: Dictionary) -> void:
	_on_zw_state_updated({"quest": quest_data})


# ── Change detection ───────────────────────────────────────────

func _detect_changes(new_summaries: Array) -> void:
	for summary in new_summaries:
		var qid: String = summary.get("id", "")
		var new_status: String = summary.get("status", "")
		var old_status: String = _prev_statuses.get(qid, "")
		if old_status != "" and old_status != new_status:
			_flash_timers[qid] = 1.0
			quest_state_changed.emit(qid, new_status)
		_prev_statuses[qid] = new_status

		for obj in summary.get("objectives", []):
			var oid: String = obj.get("id", "")
			var key := "%s:%s" % [qid, oid]
			var new_obj: String = obj.get("status", "")
			var old_obj: String = _prev_obj_statuses.get(key, "")
			if old_obj != "" and old_obj != new_obj:
				_obj_flash_timers[key] = 1.0
				objective_state_changed.emit(qid, oid, new_obj)
			_prev_obj_statuses[key] = new_obj


# ── DRAWING ────────────────────────────────────────────────────

func _draw() -> void:
	var visible: Array = _get_visible()
	if visible.is_empty():
		_draw_empty()
		return

	var y := 0.0
	var pad := 10.0
	var lh := 16.0 if not compact_mode else 13.0
	var gap := 8.0 if not compact_mode else 4.0

	# Header
	var hh := 24.0
	draw_rect(Rect2(0, y, panel_width, hh), color_bg)
	var active_n: int = visible.filter(func(s): return s.get("status") == "active").size()
	draw_string(ThemeDB.fallback_font, Vector2(pad, y + 16), "QUESTS (%d active)" % active_n, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color_header)
	y += hh + 2.0

	var shown := 0
	for summary in visible:
		if shown >= max_visible_quests:
			break

		var qid: String = summary.get("id", "")
		var status: String = summary.get("status", "inactive")
		var title: String = summary.get("title", qid)
		var desc: String = summary.get("description", "")
		var progress: float = summary.get("progress", 0.0)
		var obj_done: int = summary.get("objectives_done", 0)
		var obj_total: int = summary.get("objectives_total", 0)
		var objectives: Array = summary.get("objectives", [])

		var entry_h := _calc_height(summary, lh)

		# Background + flash
		var bg: Color = color_bg
		var flash: float = _flash_timers.get(qid, 0.0)
		if flash > 0.0:
			var fc: Color = _status_color(status)
			fc.a = flash * 0.15
			bg = bg.blend(fc)
		draw_rect(Rect2(0, y, panel_width, entry_h), bg)

		# Title
		draw_string(ThemeDB.fallback_font, Vector2(pad, y + lh), "%s %s" % [_status_icon(status), title], HORIZONTAL_ALIGNMENT_LEFT, int(panel_width - pad * 2), 12, _status_color(status))
		y += lh + 2.0

		# Description
		if not compact_mode and desc != "":
			var short_desc := desc.substr(0, 47) + "..." if desc.length() > 50 else desc
			draw_string(ThemeDB.fallback_font, Vector2(pad + 8, y + lh - 2), short_desc, HORIZONTAL_ALIGNMENT_LEFT, int(panel_width - pad * 2 - 8), 10, Color(0.45, 0.45, 0.5))
			y += lh - 2.0

		# Progress bar
		if not objectives.is_empty():
			var bx := pad + 8.0
			var bw := panel_width - pad * 2 - 16.0
			draw_rect(Rect2(bx, y + 4, bw, 4.0), color_bar_bg)
			if progress > 0.0:
				draw_rect(Rect2(bx, y + 4, bw * progress, 4.0), color_bar_fill)
			draw_string(ThemeDB.fallback_font, Vector2(bx + bw + 4, y + 10), "%d/%d" % [obj_done, obj_total], HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.5, 0.5, 0.55))
			y += 14.0

			# Objectives
			if not compact_mode:
				for obj in objectives:
					var oid: String = obj.get("id", "")
					var obj_status: String = obj.get("status", "pending")
					var obj_color := _obj_color(obj_status)
					var obj_key := "%s:%s" % [qid, oid]
					var oflash: float = _obj_flash_timers.get(obj_key, 0.0)
					if oflash > 0.0:
						obj_color = obj_color.lerp(Color.WHITE, oflash * 0.5)
					var obj_text: String = obj.get("description", oid)
					if obj.get("optional", false):
						obj_text += " (optional)"
					draw_string(ThemeDB.fallback_font, Vector2(pad + 16, y + lh - 2), "%s %s" % [_obj_icon(obj_status), obj_text], HORIZONTAL_ALIGNMENT_LEFT, int(panel_width - pad * 2 - 24), 10, obj_color)
					y += lh - 2.0

		draw_line(Vector2(pad, y + gap * 0.5), Vector2(panel_width - pad, y + gap * 0.5), color_border, 1.0)
		y += gap
		shown += 1

	if visible.size() > max_visible_quests:
		draw_string(ThemeDB.fallback_font, Vector2(pad, y + 12), "+ %d more..." % (visible.size() - max_visible_quests), HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.4, 0.4, 0.45))
		y += 18.0

	custom_minimum_size = Vector2(panel_width, y)


# ── Helpers ────────────────────────────────────────────────────

func _get_visible() -> Array:
	var sorted_s: Array = _summaries.duplicate()
	sorted_s.sort_custom(func(a, b):
		return _status_priority(a.get("status", "")) < _status_priority(b.get("status", ""))
	)
	var result: Array = []
	for s in sorted_s:
		var st: String = s.get("status", "inactive")
		if st == "active" or (st == "completed" and show_completed) or (st == "failed" and show_failed):
			result.append(s)
	return result

func _status_priority(status: String) -> int:
	match status:
		"active": return 0
		"completed": return 1
		"failed": return 2
		_: return 3

func _calc_height(summary: Dictionary, lh: float) -> float:
	var h := lh + 4.0
	if not compact_mode and summary.get("description", "") != "":
		h += lh - 2.0
	var objs: Array = summary.get("objectives", [])
	if not objs.is_empty():
		h += 14.0
		if not compact_mode:
			h += objs.size() * (lh - 2.0)
	return h

func _status_icon(s: String) -> String:
	match s:
		"active": return "◆"
		"completed": return "✓"
		"failed": return "✗"
		_: return "○"

func _status_color(s: String) -> Color:
	match s:
		"active": return color_active
		"completed": return color_completed
		"failed": return color_failed
		_: return color_inactive

func _obj_icon(s: String) -> String:
	match s:
		"satisfied": return "✓"
		"failed": return "✗"
		_: return "○"

func _obj_color(s: String) -> Color:
	match s:
		"satisfied": return color_obj_done
		"failed": return color_obj_failed
		_: return color_obj_pending

func _draw_empty() -> void:
	draw_rect(Rect2(0, 0, panel_width, 36.0), color_bg)
	draw_string(ThemeDB.fallback_font, Vector2(10, 22), "QUESTS — None active", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.4, 0.4, 0.45))
	custom_minimum_size = Vector2(panel_width, 36.0)
