# EngAInOS HUD Contract Specification
# Version: 1.0
# Date: 2026-02-09
#
# These JSON shapes are the contract between Python (sim_runtime.py)
# and Godot (UI panels). Changes to these shapes require updating
# both sides. Godot panels are view-only consumers.
#
# ════════════════════════════════════════════════════════════════

## GET /api/hud/engine_summary

```json
{
  "game_time": 123.45,
  "scene_id": "dark_forest",
  "active_quests": 2,
  "completed_quests": 1,
  "combat_state": "engaged",
  "reality_mode": "liminal",
  "player_health": 50.0,
  "player_health_max": 100.0,
  "player_location": "dark_forest",
  "entities_count": 5,
  "tick_rate": 0.016,
  "pillar_status": {
    "engain": "running",
    "mvcar": "idle",
    "tv": "reserved"
  }
}
```

### Field Reference
| Field              | Type   | Values / Range                          |
|--------------------|--------|-----------------------------------------|
| game_time          | float  | Seconds since runtime start             |
| scene_id           | string | Current scene identifier                |
| active_quests      | int    | Count of status="active" quests         |
| completed_quests   | int    | Count of status="completed" quests      |
| combat_state       | string | "idle" | "engaged" | "dead"             |
| reality_mode       | string | "waking" | "dream" | "memory" | "liminal" |
| player_health      | float  | 0.0 to player_health_max                |
| player_health_max  | float  | Positive float                          |
| player_location    | string | Entity location ID                      |
| entities_count     | int    | Total entities in world                 |
| tick_rate          | float  | Seconds per tick (0.016 = 60fps)        |
| pillar_status      | dict   | Keys: engain, mvcar, tv                 |
| pillar_status.*    | string | "running" | "idle" | "reserved" | "error" |

### Godot Consumer
- `EngineSummaryHUD.gd` → `update_summary(dict)`
- Signal: `ZWRuntime.engine_summary_updated`


## GET /api/hud/quest_summaries

```json
{
  "summaries": [
    {
      "quest_id": "q_find_sword",
      "title": "Find the Lost Sword",
      "description": "Retrieve the ancient blade from the ruins.",
      "status": "active",
      "objectives_completed": 1,
      "objectives_total": 2,
      "progress_percent": 50.0
    },
    {
      "quest_id": "q_talk_elder",
      "title": "The Elder's Request",
      "description": "Speak with the village elder.",
      "status": "completed",
      "objectives_completed": 1,
      "objectives_total": 1,
      "progress_percent": 100.0
    }
  ]
}
```

### Field Reference
| Field                | Type   | Values / Range                     |
|----------------------|--------|------------------------------------|
| quest_id             | string | Unique quest identifier            |
| title                | string | Human-readable quest name          |
| description          | string | Quest description text             |
| status               | string | "active" | "completed" | "failed" | "inactive" |
| objectives_completed | int    | Count of completed objectives      |
| objectives_total     | int    | Total objectives in quest          |
| progress_percent     | float  | 0.0 to 100.0                       |

### Godot Consumer
- `QuestTracker.gd` → `update_summaries(Array)`
- Signal: `ZWRuntime.quest_summaries_updated`


## GET /api/hud/combat?entity={entity_id}

```json
{
  "entity_id": "player",
  "health": 75.0,
  "max_health": 100.0,
  "wound_state": "wounded",
  "combat_state": "engaged",
  "damage_events": [],
  "heal_events": []
}
```

### Field Reference
| Field         | Type   | Values / Range                                     |
|---------------|--------|----------------------------------------------------|
| entity_id     | string | Requested entity identifier                        |
| health        | float  | Current health value                               |
| max_health    | float  | Maximum health value                               |
| wound_state   | string | "healthy" | "wounded" | "badly_wounded" | "dead"   |
| combat_state  | string | "idle" | "engaged" | "dead"                        |
| damage_events | array  | Recent damage entries (cleared after read)          |
| heal_events   | array  | Recent heal entries (cleared after read)            |

### Godot Consumer
- `CombatHealthBar.gd` → `_on_combat_updated(dict)`
- Signal: `ZWRuntime.combat_updated`


## GET /snapshot (existing, extended)

Full world state snapshot wrapped in NGAT-RT v1.0 protocol envelope.
Now includes `quest` and `ap_state` keys.

```json
{
  "protocol": "NGAT-RT",
  "version": "1.0",
  "payload": {
    "entities": { ... },
    "quest": {
      "quests": { ... },
      "tick": 123.45
    },
    "ap_state": {
      "reality_mode": "waking",
      "combat_state": "idle",
      "entropy": 10.0
    }
  }
}
```

### Godot Consumer
- `ZWRuntime.gd` → `state_updated` signal (all panels can consume)
- Used as fallback by CombatHealthBar if dedicated endpoint unavailable


# ════════════════════════════════════════════════════════════════
# RULES
# ════════════════════════════════════════════════════════════════
#
# 1. Python runtime is the ONLY producer of these shapes.
# 2. Godot panels are view-only consumers.
# 3. Adding a field is non-breaking (Godot uses .get() with defaults).
# 4. Removing or renaming a field is BREAKING — update both sides.
# 5. All numeric types are float unless explicitly int.
# 6. All string enums are lowercase.
# 7. Empty/missing data returns empty dict/array, never null.
