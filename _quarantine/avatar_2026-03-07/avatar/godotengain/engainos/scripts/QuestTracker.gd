# File: scripts/QuestTracker.gd
# QuestTracker — Production View-Only Quest Display
#
# Authority model:
#   Python quest3d_mr.py     →  quest lifecycle (truth)
#   Python ap_quest_rules.py →  activation/completion/failure
#   ZWRuntime                →  polls /api/hud/quest_summaries
#   This node                →  renders quest list. Nothing else.
#
# Contract shape (from /api/hud/quest_summaries):
#   { "summaries": [
#       { "quest_id", "title", "description", "status",
#         "objectives_completed", "objectives_total",
#         "progress_percent" }
#     ]
#   }

extends Control
class_name QuestTracker

# ── Configuration ────────────────────────────────────────────
@export var panel_width: float = 260.0
@export var max_visible_quests: int = 6
@export var show_completed: bool = true

# ── Colors ───────────────────────────────────────────────────
@export var color_bg: Color = Color(0.06, 0.06, 0.08, 0.85)
@export var color_header: Color = Color(0.5, 0.6, 0.8)
@export var color_active: Color = Color(0.8, 0.8, 0.85)
@export var color_completed: Color = Color(0.3, 0.75, 0.4)
@export var color_failed: Color = Color(0.8, 0.25, 0.2)
@export var color_inactive: Color = Color(0.4, 0.4, 0.42)
@export var color_progress_bg: Color = Color(0.15, 0.15, 0.18)
@export var color_progress_fill: Color = Color(0.3, 0.55, 0.8)
@export var color_dim: Color = Color(0.35, 0.35, 0.4)

# ── State ────────────────────────────────────────────────────
var _summaries: Array = []
var _has_data: bool = false


func _ready() -> void:
	ZWRuntime.quest_summaries_updated.connect(_on_quest_summaries)


func _process(_delta: float) -> void:
	queue_redraw()


func _on_quest_summaries(summaries: Array) -> void:
	_summaries = summaries
	_has_data = true
	queue_redraw()


func _draw() -> void:
	if not _has_data or _summaries.is_empty():
		_draw_idle()
		return

	var pad := 8.0
	var lh := 16.0
	var bar_h := 4.0
	var y := pad

	var visible_quests: Array = []
	for s in _summaries:
		var status: String = s.get("status", "")
		if status == "completed" and not show_completed:
			continue
		visible_quests.append(s)

	if visible_quests.is_empty():
		_draw_idle()
		return

	visible_quests.sort_custom(func(a, b):
		var order := {"active": 0, "completed": 1, "failed": 2, "inactive": 3}
		return order.get(a.get("status", ""), 4) < order.get(b.get("status", ""), 4)
	)

	var count := mini(visible_quests.size(), max_visible_quests)
	var total_h := pad + lh + (count * (lh + bar_h + 6.0)) + pad

	draw_rect(Rect2(0, 0, panel_width, total_h), color_bg)

	var active_count := 0
	for s in _summaries:
		if s.get("status", "") == "active":
			active_count += 1
	draw_string(ThemeDB.fallback_font, Vector2(pad, y + 10), "QUESTS (%d active)" % active_count, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, color_header)
	y += lh + 2

	for i in range(count):
		var q: Dictionary = visible_quests[i]
		var status: String = q.get("status", "active")
		var title: String = q.get("title", "Unknown Quest")
		var progress: float = q.get("progress_percent", 0.0)
		var obj_done: int = q.get("objectives_completed", 0)
		var obj_total: int = q.get("objectives_total", 0)

		var icon := ""
		var text_color := color_active
		match status:
			"active":
				icon = "◆"
				text_color = color_active
			"completed":
				icon = "✓"
				text_color = color_completed
			"failed":
				icon = "✗"
				text_color = color_failed
			_:
				icon = "○"
				text_color = color_inactive

		var title_str := "%s %s" % [icon, title]
		if status == "active" and obj_total > 0:
			title_str += "  %d/%d" % [obj_done, obj_total]
		draw_string(ThemeDB.fallback_font, Vector2(pad, y + 10), title_str, HORIZONTAL_ALIGNMENT_LEFT, int(panel_width - pad * 2), 9, text_color)
		y += lh

		if status == "active" and obj_total > 0:
			var bar_x := pad
			var bar_w := panel_width - pad * 2
			draw_rect(Rect2(bar_x, y, bar_w, bar_h), color_progress_bg)
			var fill_w := bar_w * clampf(progress / 100.0, 0.0, 1.0)
			if fill_w > 0:
				draw_rect(Rect2(bar_x, y, fill_w, bar_h), color_progress_fill)

		y += bar_h + 6.0

	if visible_quests.size() > max_visible_quests:
		var more := visible_quests.size() - max_visible_quests
		draw_string(ThemeDB.fallback_font, Vector2(pad, y + 8), "+%d more..." % more, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, color_dim)
		total_h += 14.0

	custom_minimum_size = Vector2(panel_width, total_h)


func _draw_idle() -> void:
	var h := 28.0
	draw_rect(Rect2(0, 0, panel_width, h), color_bg)
	draw_string(ThemeDB.fallback_font, Vector2(8, 18), "QUESTS — awaiting state", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.35, 0.35, 0.4))
	custom_minimum_size = Vector2(panel_width, h)
