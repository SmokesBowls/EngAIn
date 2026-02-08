# MV-CAR AudioTimeline — Drop-In Integration Guide
## Pillar 2 Godot Endpoint

### What This Is

Godot scheduler that loads `timeline.json` (produced by MV-CAR Python pipeline)
and fires segment/TTS events at their scheduled absolute times.
Same pattern as CombatHealthBar: data from Python is truth, Godot just renders.

### Authority Model

```
Python mvcar_export_timeline.py  →  timeline.json  (TRUTH)
AudioTimeline.gd                 →  schedules playback from that truth
Godot never generates timing. Ever.
```

---

### Step 1: Copy Files

```bash
cp AudioTimeline.gd         ~/Downloads/EngAIn/godotengain/engainos/scripts/
cp test_audio_timeline.gd    ~/Downloads/EngAIn/godotengain/engainos/scripts/
cp test_timeline.json        ~/Downloads/EngAIn/godotengain/engainos/renders/tts/timeline.json
```

Create the renders directory if it doesn't exist:
```bash
mkdir -p ~/Downloads/EngAIn/godotengain/engainos/renders/tts
mkdir -p ~/Downloads/EngAIn/godotengain/engainos/renders/music
```

### Step 2: Test Standalone (No Python Needed)

1. Open your Godot project
2. Create a new scene (Node2D root)
3. Attach `test_audio_timeline.gd` to the root node
4. Run the scene

**You should see:**
- Color-coded progress bar showing 4 segments (emergence → tension → conflict → resolution)
- Yellow tick marks for TTS events
- White playhead advancing in real-time
- Event log showing segment transitions and TTS fires
- Arc role legend at bottom

**Keyboard controls:**
- `SPACE` — Play / Pause
- `R` — Reset to beginning
- `UP` — Increase speed (up to 8x)
- `DOWN` — Decrease speed (down to 0.5x)

**Even without timeline.json on disk**, the test harness has inline fallback data.
It will always work.

### Step 3: Wire to ZWRuntime (Production)

Once the visual looks right, remove the test harness and set up AudioTimeline as autoload:

1. **Project → Project Settings → Autoload**
2. Add `scripts/AudioTimeline.gd` with name `AudioTimeline`
3. In your ZWRuntime (or wherever game time advances), add ONE line:

```gdscript
# In ZWRuntime._on_snapshot_received() or _process():
func _on_zw_state_updated(snapshot: Dictionary):
    var game_time = snapshot.get("time_sec", 0.0)
    AudioTimeline.update(game_time)  # ← THIS IS ALL IT TAKES
```

4. Connect to signals from any game node:

```gdscript
func _ready():
    AudioTimeline.segment_started.connect(_on_segment)
    AudioTimeline.tts_event.connect(_on_voice)

func _on_segment(segment_id, arc_role, time_sec):
    # Switch music, update atmosphere, etc.
    pass

func _on_voice(line_index, segment_id, time_sec):
    # Play voice line, show subtitle, etc.
    pass
```

### Step 4: Add Audio Files (When Ready)

AudioTimeline auto-discovers files by convention:
- Music: `res://renders/music/seg_001_emergence.wav` (or .ogg, .mp3)
- Voice: `res://renders/tts/line_0000.wav` (or .ogg, .mp3)

No audio files? No problem. Signals still fire, event log still works.
Add WAVs later when MV-CAR renders them.

### What You're Proving

This is Phase 1 completion: **Two pillars talking through one clock.**
- Pillar 1 (EngAIn) → ZWRuntime → game_time
- Pillar 2 (MV-CAR) → AudioTimeline.update(game_time) → audio events

Same `game_time_sec` drives both combat snapshots AND audio scheduling.
Single clock. Two outputs. No sync drift.

### Validation Criteria (from THREE_PILLAR_ARCHITECTURE.json)

```
Metric: Music/voice plays on schedule, synced to game time
Test:   Trigger combat → music switches immediately
Pass:   Audio events fire within 100ms of schedule
```

### Next Slice Options

After this works:
- **Pass2 CORE+ hardening** — back to core (pronoun chains, emotion keywords)
- **Quest3D kernel** — new subsystem following Combat3D pattern
- **Real MV-CAR render** — generate actual WAVs from your Python pipeline
