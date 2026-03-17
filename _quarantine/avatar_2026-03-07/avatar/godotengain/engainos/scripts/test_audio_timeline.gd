# File: scripts/test_audio_timeline.gd
# Test harness for Pillar 2 — MV-CAR AudioTimeline
#
# Attach to a Node2D in a test scene. Simulates game_time advancing
# so you can SEE segment transitions and TTS events firing
# without the Python kernel running.
#
# Once verified, remove this. Real game_time comes from ZWRuntime snapshots.

extends Node2D

# ── Config ─────────────────────────────────────────────────────
const TIMELINE_PATH := "res://renders/tts/timeline.json"
var _playback_speed: float = 1.0 # 1.0 = real-time, 2.0 = double speed

# ── State ──────────────────────────────────────────────────────
var _audio_timeline: AudioTimeline = null
var _game_time: float = 0.0
var _is_running: bool = false
var _event_log: Array[String] = []
var _current_segment_display: String = "—"
var _current_arc: String = "—"
var _tts_flash_timer: float = 0.0
var _last_tts_line: int = -1
var _segment_flash_timer: float = 0.0

# ── UI refs ────────────────────────────────────────────────────
var _info_label: Label
var _log_label: RichTextLabel
var _instructions: Label


func _ready() -> void:
	# Create AudioTimeline instance (in production this is an autoload)
	_audio_timeline = AudioTimeline.new()
	_audio_timeline.name = "AudioTimeline"
	_audio_timeline.timeline_path = TIMELINE_PATH
	_audio_timeline.auto_load_on_ready = false # We'll load manually
	_audio_timeline.log_events = true
	add_child(_audio_timeline)
	
	# Connect signals
	_audio_timeline.timeline_loaded.connect(_on_timeline_loaded)
	_audio_timeline.segment_started.connect(_on_segment_started)
	_audio_timeline.segment_ended.connect(_on_segment_ended)
	_audio_timeline.tts_event.connect(_on_tts_event)
	_audio_timeline.playback_complete.connect(_on_playback_complete)
	
	# Build UI
	_build_ui()
	
	# Try loading
	if _audio_timeline.load_timeline(TIMELINE_PATH):
		_log("Timeline loaded from %s" % TIMELINE_PATH)
	else:
		_log("[WARN] No timeline at %s — loading test data inline" % TIMELINE_PATH)
		_load_inline_test_data()
	
	_log("Press SPACE to start/pause, R to reset, UP/DOWN for speed")


func _process(delta: float) -> void:
	if _is_running:
		_game_time += delta * _playback_speed
		_audio_timeline.update(_game_time)
	
	# Decay flash timers
	if _tts_flash_timer > 0.0:
		_tts_flash_timer -= delta
	if _segment_flash_timer > 0.0:
		_segment_flash_timer -= delta
	
	_update_display()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed:
		return
	
	match event.keycode:
		KEY_SPACE:
			_is_running = not _is_running
			_log("PLAY" if _is_running else "PAUSE")
		KEY_R:
			_game_time = 0.0
			_audio_timeline.reset()
			_is_running = false
			_current_segment_display = "—"
			_current_arc = "—"
			_last_tts_line = -1
			_log("RESET")
		KEY_UP:
			_playback_speed = minf(_playback_speed + 0.5, 8.0)
			_log("Speed: %.1fx" % _playback_speed)
		KEY_DOWN:
			_playback_speed = maxf(_playback_speed - 0.5, 0.5)
			_log("Speed: %.1fx" % _playback_speed)


# ── Signal handlers ────────────────────────────────────────────

func _on_timeline_loaded(seg_count: int, tts_count: int) -> void:
	_log("Loaded: %d segments, %d TTS events" % [seg_count, tts_count])


func _on_segment_started(segment_id: String, arc_role: String, time_sec: float) -> void:
	_current_segment_display = segment_id
	_current_arc = arc_role
	_segment_flash_timer = 0.5
	_log("▶ SEG: %s [%s] @ %.2fs" % [segment_id, arc_role, time_sec])


func _on_segment_ended(segment_id: String, time_sec: float) -> void:
	_log("■ END: %s @ %.2fs" % [segment_id, time_sec])


func _on_tts_event(line_index: int, segment_id: String, time_sec: float) -> void:
	_last_tts_line = line_index
	_tts_flash_timer = 0.8
	_log("🔊 TTS line %d (seg: %s) @ %.2fs" % [line_index, segment_id, time_sec])


func _on_playback_complete() -> void:
	_is_running = false
	_log("✓ PLAYBACK COMPLETE")


# ── UI ─────────────────────────────────────────────────────────

func _build_ui() -> void:
	_info_label = Label.new()
	_info_label.position = Vector2(30, 30)
	_info_label.add_theme_font_size_override("font_size", 14)
	_info_label.add_theme_color_override("font_color", Color(0.9, 0.9, 0.9))
	add_child(_info_label)
	
	_log_label = RichTextLabel.new()
	_log_label.position = Vector2(30, 200)
	_log_label.size = Vector2(500, 300)
	_log_label.bbcode_enabled = true
	_log_label.scroll_following = true
	_log_label.add_theme_font_size_override("normal_font_size", 11)
	add_child(_log_label)
	
	_instructions = Label.new()
	_instructions.position = Vector2(30, 510)
	_instructions.add_theme_font_size_override("font_size", 11)
	_instructions.add_theme_color_override("font_color", Color(0.4, 0.4, 0.4))
	_instructions.text = "SPACE: play/pause  |  R: reset  |  UP/DOWN: speed  |  Two-Pillar Validation Test"
	add_child(_instructions)


func _update_display() -> void:
	var progress := _audio_timeline.get_progress()
	var duration := _audio_timeline.get_total_duration()
	var state_str := "▶ PLAYING" if _is_running else "⏸ PAUSED"
	
	_info_label.text = "%s  [%.1fx]\n" % [state_str, _playback_speed]
	_info_label.text += "Time: %.2f / %.2f sec  (%.0f%%)\n" % [_game_time, duration, progress * 100]
	_info_label.text += "Segment: %s\n" % _current_segment_display
	_info_label.text += "Arc: %s\n" % _current_arc
	if _last_tts_line >= 0:
		_info_label.text += "Last TTS: line %d" % _last_tts_line
		if _tts_flash_timer > 0.0:
			_info_label.text += " ◀"


func _draw() -> void:
	# Progress bar
	var bar_x := 30.0
	var bar_y := 150.0
	var bar_w := 500.0
	var bar_h := 20.0
	
	# Background
	draw_rect(Rect2(bar_x, bar_y, bar_w, bar_h), Color(0.12, 0.12, 0.12))
	
	# Segment regions (color-coded by arc)
	var duration := _audio_timeline.get_total_duration()
	if duration > 0:
		for seg in _audio_timeline._segments:
			var sx: float = bar_x + (seg["start_sec"] / duration) * bar_w
			var ex: float = bar_x + (seg.get("end_sec", seg["start_sec"]) / duration) * bar_w
			var arc_color := _arc_color(seg.get("arc_role", ""))
			arc_color.a = 0.3
			draw_rect(Rect2(sx, bar_y, ex - sx, bar_h), arc_color)
		
		# TTS event markers
		for evt in _audio_timeline._tts_events:
			var tx: float = bar_x + (evt["time_sec"] / duration) * bar_w
			draw_line(Vector2(tx, bar_y), Vector2(tx, bar_y + bar_h), Color(0.9, 0.9, 0.2, 0.7), 1.5)
		
		# Playhead
		var px: float = bar_x + _audio_timeline.get_progress() * bar_w
		draw_line(Vector2(px, bar_y - 4), Vector2(px, bar_y + bar_h + 4), Color(1, 1, 1, 0.9), 2.0)
	
	# Border
	draw_rect(Rect2(bar_x, bar_y, bar_w, bar_h), Color(0.3, 0.3, 0.3, 0.8), false, 1.0)
	
	# Segment flash
	if _segment_flash_timer > 0.0:
		var flash_alpha := _segment_flash_timer * 0.6
		draw_rect(Rect2(bar_x, bar_y, bar_w, bar_h), Color(0.3, 0.8, 1.0, flash_alpha))
	
	# TTS flash
	if _tts_flash_timer > 0.0:
		var flash_rect := Rect2(bar_x, bar_y + bar_h + 6, bar_w, 4)
		draw_rect(flash_rect, Color(0.9, 0.8, 0.1, _tts_flash_timer))
	
	# Arc legend
	var legend_y := bar_y + bar_h + 16
	var legend_x := bar_x
	for arc in ["emergence", "tension", "conflict", "resolution"]:
		var c := _arc_color(arc)
		draw_rect(Rect2(legend_x, legend_y, 10, 10), c)
		draw_string(ThemeDB.fallback_font, Vector2(legend_x + 14, legend_y + 10), arc, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.5, 0.5, 0.5))
		legend_x += 110


func _arc_color(arc_role: String) -> Color:
	match arc_role:
		"emergence": return Color(0.2, 0.7, 0.4)
		"tension": return Color(0.8, 0.6, 0.1)
		"conflict": return Color(0.9, 0.2, 0.15)
		"resolution": return Color(0.3, 0.4, 0.9)
		_: return Color(0.4, 0.4, 0.4)


func _log(msg: String) -> void:
	var timestamp := "%.2f" % _game_time
	_event_log.append("[%s] %s" % [timestamp, msg])
	# Keep last 30 entries
	if _event_log.size() > 30:
		_event_log = _event_log.slice(-30)
	
	if _log_label:
		_log_label.clear()
		_log_label.append_text("[color=#666666]Event Log[/color]\n")
		for entry in _event_log:
			_log_label.append_text(entry + "\n")


# ── Inline test data (fallback if no file) ─────────────────────

func _load_inline_test_data() -> void:
	var test_data := {
		"work_id": "inline_test",
		"bpm": 120,
		"ppq": 480,
		"bars_per_segment": 4,
		"segments": [
			{"segment_id": "seg_001", "start_sec": 0.0, "arc_role": "emergence",
			  "bars": [ {"bar": 0, "start_sec": 0.0}, {"bar": 1, "start_sec": 2.0}, {"bar": 2, "start_sec": 4.0}, {"bar": 3, "start_sec": 6.0}]},
			{"segment_id": "seg_002", "start_sec": 8.0, "arc_role": "tension",
			  "bars": [ {"bar": 0, "start_sec": 8.0}, {"bar": 1, "start_sec": 10.0}, {"bar": 2, "start_sec": 12.0}, {"bar": 3, "start_sec": 14.0}]},
			{"segment_id": "seg_003", "start_sec": 16.0, "arc_role": "conflict",
			  "bars": [ {"bar": 0, "start_sec": 16.0}, {"bar": 1, "start_sec": 18.0}, {"bar": 2, "start_sec": 20.0}, {"bar": 3, "start_sec": 22.0}]},
			{"segment_id": "seg_004", "start_sec": 24.0, "arc_role": "resolution",
			  "bars": [ {"bar": 0, "start_sec": 24.0}, {"bar": 1, "start_sec": 26.0}, {"bar": 2, "start_sec": 28.0}, {"bar": 3, "start_sec": 30.0}]},
		],
		"tts": [
			{"line": 0, "segment_id": "seg_001", "bar": 0, "time_sec": 0.5},
			{"line": 1, "segment_id": "seg_001", "bar": 2, "time_sec": 4.5},
			{"line": 2, "segment_id": "seg_002", "bar": 0, "time_sec": 8.5},
			{"line": 3, "segment_id": "seg_002", "bar": 2, "time_sec": 12.5},
			{"line": 4, "segment_id": "seg_003", "bar": 1, "time_sec": 18.5},
			{"line": 5, "segment_id": "seg_003", "bar": 3, "time_sec": 22.5},
			{"line": 6, "segment_id": "seg_004", "bar": 0, "time_sec": 24.5},
			{"line": 7, "segment_id": "seg_004", "bar": 3, "time_sec": 30.5},
		]
	}
	_audio_timeline.load_timeline_from_dict(test_data)
	_log("Loaded inline test data (4 segments, 8 TTS events)")
