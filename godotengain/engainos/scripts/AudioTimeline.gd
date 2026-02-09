# File: scripts/AudioTimeline.gd
# Pillar 2 — MV-CAR Godot Scheduler
#
# Authority model:
#   Python MV-CAR pipeline  →  timeline.json (truth)
#   This node               →  schedules playback from that truth
#   Godot never generates timing. Ever.
#
# Usage:
#   Add as autoload: Project Settings → Autoload → AudioTimeline
#   Wire one line in ZWRuntime or _process:
#     AudioTimeline.update(game_time_sec)
#
# timeline.json shape (from mvcar_export_timeline.py):
# {
#   "work_id": "work_0001",
#   "bpm": 120,
#   "segments": [
#     { "segment_id": "seg_001", "start_sec": 0.0, "arc_role": "emergence",
#       "bars": [{"bar": 0, "start_sec": 0.0}, ...] }
#   ],
#   "tts": [
#     { "line": 0, "segment_id": "seg_001", "bar": 0, "time_sec": 0.0 }
#   ]
# }

extends Node
class_name AudioTimeline

# ── Signals (other nodes listen to these) ──────────────────────
signal timeline_loaded(segment_count: int, tts_count: int)
signal segment_started(segment_id: String, arc_role: String, time_sec: float)
signal segment_ended(segment_id: String, time_sec: float)
signal tts_event(line_index: int, segment_id: String, time_sec: float)
signal playback_complete()

# ── Configuration ──────────────────────────────────────────────
@export var timeline_path: String = "res://renders/tts/timeline.json"
@export var auto_load_on_ready: bool = true
@export var log_events: bool = true

# ── Timeline data (loaded from JSON — READ ONLY) ───────────────
var _work_id: String = ""
var _bpm: float = 120.0
var _segments: Array = []        # Sorted by start_sec
var _tts_events: Array = []      # Sorted by time_sec
var _total_duration: float = 0.0

# ── Playback state ─────────────────────────────────────────────
var _current_time: float = 0.0
var _is_playing: bool = false
var _current_segment_idx: int = -1
var _next_segment_idx: int = 0
var _next_tts_idx: int = 0
var _completed: bool = false

# ── Audio players (pooled) ─────────────────────────────────────
var _music_player: AudioStreamPlayer = null
var _voice_player: AudioStreamPlayer = null


func _ready() -> void:
	# Create audio player nodes
	_music_player = AudioStreamPlayer.new()
	_music_player.name = "MusicPlayer"
	_music_player.bus = "Music" if AudioServer.get_bus_index("Music") >= 0 else "Master"
	add_child(_music_player)
	
	_voice_player = AudioStreamPlayer.new()
	_voice_player.name = "VoicePlayer"
	_voice_player.bus = "Voice" if AudioServer.get_bus_index("Voice") >= 0 else "Master"
	add_child(_voice_player)
	
	if auto_load_on_ready:
		load_timeline(timeline_path)


# ── PUBLIC API ─────────────────────────────────────────────────

func update(game_time_sec: float) -> void:
	"""Call this every frame with authoritative game time from ZWRuntime.
	This is THE integration point. One line."""
	if _segments.is_empty():
		return
	
	_current_time = game_time_sec
	_is_playing = true
	
	_check_segments()
	_check_tts()
	
	# Check completion
	if not _completed and _current_time >= _total_duration:
		_completed = true
		if log_events:
			print("[AudioTimeline] Playback complete at %.2fs" % _current_time)
		playback_complete.emit()


func load_timeline(path: String) -> bool:
	"""Load and parse a timeline.json file."""
	if not FileAccess.file_exists(path):
		push_warning("[AudioTimeline] Timeline not found: %s" % path)
		return false
	
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("[AudioTimeline] Cannot open: %s" % path)
		return false
	
	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	file.close()
	
	if err != OK:
		push_error("[AudioTimeline] JSON parse error in %s: %s" % [path, json.get_error_message()])
		return false
	
	return _parse_timeline(json.data)


func load_timeline_from_dict(data: Dictionary) -> bool:
	"""Load timeline from an already-parsed Dictionary (useful for testing)."""
	return _parse_timeline(data)


func reset() -> void:
	"""Reset playback to beginning."""
	_current_time = 0.0
	_current_segment_idx = -1
	_next_segment_idx = 0
	_next_tts_idx = 0
	_is_playing = false
	_completed = false


func get_current_segment() -> Dictionary:
	"""Returns current active segment data, or empty dict."""
	if _current_segment_idx >= 0 and _current_segment_idx < _segments.size():
		return _segments[_current_segment_idx]
	return {}


func get_current_time() -> float:
	return _current_time


func get_total_duration() -> float:
	return _total_duration


func get_progress() -> float:
	"""Returns 0.0 to 1.0 playback progress."""
	if _total_duration <= 0.0:
		return 0.0
	return clampf(_current_time / _total_duration, 0.0, 1.0)


func is_loaded() -> bool:
	return not _segments.is_empty()


# ── INTERNAL: Parse ────────────────────────────────────────────

func _parse_timeline(data: Dictionary) -> bool:
	_segments.clear()
	_tts_events.clear()
	reset()
	
	_work_id = str(data.get("work_id", "unknown"))
	_bpm = float(data.get("bpm", 120))
	
	# Parse segments
	var raw_segments: Array = data.get("segments", [])
	for seg in raw_segments:
		_segments.append({
			"segment_id": str(seg.get("segment_id", "")),
			"start_sec": float(seg.get("start_sec", 0.0)),
			"arc_role": str(seg.get("arc_role", "")),
			"bars": seg.get("bars", []),
		})
	
	# Sort by start time (should already be, but enforce)
	_segments.sort_custom(func(a, b): return a["start_sec"] < b["start_sec"])
	
	# Calculate end times (each segment ends when next begins)
	for i in range(_segments.size()):
		if i + 1 < _segments.size():
			_segments[i]["end_sec"] = _segments[i + 1]["start_sec"]
		else:
			# Last segment: estimate from bars or add default duration
			var bars: Array = _segments[i].get("bars", [])
			if bars.size() > 1:
				var bar_dur: float = bars[1].get("start_sec", 0.0) - bars[0].get("start_sec", 0.0)
				_segments[i]["end_sec"] = _segments[i]["start_sec"] + bar_dur * bars.size()
			else:
				_segments[i]["end_sec"] = _segments[i]["start_sec"] + 8.0  # Fallback
	
	# Parse TTS events
	var raw_tts: Array = data.get("tts", [])
	for evt in raw_tts:
		_tts_events.append({
			"line": int(evt.get("line", 0)),
			"segment_id": str(evt.get("segment_id", "")),
			"bar": int(evt.get("bar", 0)),
			"time_sec": float(evt.get("time_sec", 0.0)),
		})
	
	# Sort by time
	_tts_events.sort_custom(func(a, b): return a["time_sec"] < b["time_sec"])
	
	# Total duration
	if _segments.size() > 0:
		_total_duration = _segments[-1].get("end_sec", 0.0)
	
	if log_events:
		print("[AudioTimeline] Loaded timeline '%s'" % _work_id)
		print("  BPM: %.1f" % _bpm)
		print("  Segments: %d" % _segments.size())
		print("  TTS events: %d" % _tts_events.size())
		print("  Duration: %.2fs" % _total_duration)
	
	timeline_loaded.emit(_segments.size(), _tts_events.size())
	return true


# ── INTERNAL: Scheduling ───────────────────────────────────────

func _check_segments() -> void:
	# Fire segment_started when we cross into a new segment
	while _next_segment_idx < _segments.size():
		var seg: Dictionary = _segments[_next_segment_idx]
		if _current_time >= seg["start_sec"]:
			# End previous segment
			if _current_segment_idx >= 0:
				var prev_seg: Dictionary = _segments[_current_segment_idx]
				segment_ended.emit(prev_seg["segment_id"], _current_time)
				if log_events:
					print("[AudioTimeline] Ended segment '%s'" % prev_seg["segment_id"])
			
			# Start new segment
			_current_segment_idx = _next_segment_idx
			_next_segment_idx += 1
			
			if log_events:
				print("[AudioTimeline] Started segment '%s' (arc: %s) at %.2fs" % [
					seg["segment_id"], seg["arc_role"], seg["start_sec"]
				])
			
			segment_started.emit(seg["segment_id"], seg["arc_role"], seg["start_sec"])
			
			# Try to play music file for this segment
			_try_play_music(seg["segment_id"])
		else:
			break


func _check_tts() -> void:
	# Fire tts_event when we pass a TTS line's scheduled time
	while _next_tts_idx < _tts_events.size():
		var evt: Dictionary = _tts_events[_next_tts_idx]
		if _current_time >= evt["time_sec"]:
			_next_tts_idx += 1
			
			if log_events:
				print("[AudioTimeline] TTS line %d (seg: %s, bar: %d) at %.2fs" % [
					evt["line"], evt["segment_id"], evt["bar"], evt["time_sec"]
				])
			
			tts_event.emit(evt["line"], evt["segment_id"], evt["time_sec"])
			
			# Try to play voice file
			_try_play_voice(evt["line"])
		else:
			break


# ── INTERNAL: Audio playback ───────────────────────────────────

func _try_play_music(segment_id: String) -> void:
	"""Try to load and play a music WAV for this segment.
	Looks for: res://renders/music/seg_XXX.wav (or .ogg, .mp3)"""
	var base_path := "res://renders/music/%s" % segment_id
	for ext: String in [".wav", ".ogg", ".mp3"]:
		var path := base_path + ext
		if ResourceLoader.exists(path):
			var stream = load(path)
			if stream:
				_music_player.stream = stream
				_music_player.play()
				if log_events:
					print("[AudioTimeline] Playing music: %s" % path)
				return
	# No audio file found — that's fine, signals still fire


func _try_play_voice(line_index: int) -> void:
	"""Try to load and play a TTS WAV for this line.
	Looks for: res://renders/tts/line_NNNN.wav (or .ogg, .mp3)"""
	var base_path := "res://renders/tts/line_%04d" % line_index
	for ext: String in [".wav", ".ogg", ".mp3"]:
		var path := base_path + ext
		if ResourceLoader.exists(path):
			var stream = load(path)
			if stream:
				_voice_player.stream = stream
				_voice_player.play()
				if log_events:
					print("[AudioTimeline] Playing voice: %s" % path)
				return
	# No audio file — signals still fire, consumers can handle
