This is clean. Tight. Necessary.

The contract you're defining is essentially **spatial due process** — GodotSim provides physical evidence, EngAInOS renders legal judgment on runtime mutation. No conflation of simulation with narrative, no simulation overreach.

Let me formalize this as the actual contract document:

---

# GODOTSIM_TIER2_SPATIAL_SIM_CONTRACT_v1.md

## 1. Purpose
Define the authority boundary and data contract between EngAInOS (TIER1 runtime authority) and GodotSim (TIER2 spatial simulation authority).

## 2. Authority Statement

**TIER1 – EngAInOS**  
- Runtime law enforcement  
- AP (Authority Permission) validation  
- Entity declaration approval  
- Canon mutation decisions  
- Render asset selection authority  
- Acceptance/rejection of all state mutations  

**TIER2 – GodotSim**  
- Spatial simulation truth: position, rotation, velocity, collision, proximity, reachability, scene occupancy, sim tick  
- Physical evidence provider  
- No authority to mutate runtime state independently  
- No authority to declare entities  
- No authority to decide canon  
- No authority to choose assets  
- No authority to grant AP  
- No authority to convert narrative to runtime entities  

## 3. Communication Protocol

All GodotSim → EngAInOS communication MUST be via `SpatialSimPacket`.

### Packet Schema (v1)
```json
{
  "contract": "godotsim.spatial_sim_packet.v1",
  "source": "godotsim",
  "authority_tier": 2,
  "scene_id": "string",
  "sim_tick": 1042,
  "entities": [
    {
      "entity_id": "string",
      "position": [0.0, 0.0, 0.0],       // REQUIRED
      "collision_role": "solid",          // REQUIRED
      "rotation": [0.0, 0.0, 0.0],       // OPTIONAL
      "velocity": [0.0, 0.0, 0.0],       // OPTIONAL
      "grounded": true,                   // OPTIONAL
      "bounds": {},                       // OPTIONAL
      "navigation_state": {},             // OPTIONAL
      "reachable_targets": [],            // OPTIONAL
      "blocked_paths": []                 // OPTIONAL
    }
  ],
  "contacts": [],         // OPTIONAL
  "proximity": [],        // OPTIONAL
  "physics_flags": {}     // OPTIONAL
}
```

## 4. Minimum Required Fields
| Field | Requirement |
|-------|-------------|
| `contract` | MUST be `godotsim.spatial_sim_packet.v1` |
| `source` | MUST be `godotsim` |
| `authority_tier` | MUST be `2` |
| `scene_id` | REQUIRED |
| `sim_tick` or `time` | REQUIRED |
| `entities` | REQUIRED |
| `entity_id` | REQUIRED per entity |
| `position` | REQUIRED per entity |
| `collision_role` | REQUIRED per entity, must be from known set |

## 5. Hard Reject Conditions
EngAInOS MUST reject packet if ANY of the following are true:

- `source != "godotsim"`
- `authority_tier != 2`
- `scene_id` missing
- Any `entity_id` missing
- Any `position` missing (outside DRAFT/TEST mode)
- Any `collision_role` not in known enum set
- Packet includes `ap_allowed = true` or similar AP authority field
- Packet includes `canon_truth` or similar canon declaration
- Packet includes `render_asset_authority` or similar asset selection
- Packet declares new entities without prior EngAInOS approval
- Packet attempts to include narrative meaning (quest completion, door open, etc.)

## 6. Permitted Statements (GodotSim MAY say)
- "Entity A is at position X"
- "Entity A touched entity B"
- "Entity A cannot reach entity B"
- "Entity A collided with wall C"
- "Entity A is inside region R"
- "Entity A is moving at velocity V"

## 7. Forbidden Statements (GodotSim MAY NOT say)
- "therefore the quest completes"
- "therefore the door opens"
- "therefore canon changes"
- "therefore this entity is allowed"
- "therefore spawn this undeclared thing"

## 8. Validation & Handoff Flow

```
1. Mettaext declares entities (narrative → entity spec)
2. EngAInOS validates entity declaration authority
3. GodotSim simulates physical state → generates SpatialSimPacket
4. EngAInOS validates packet against this contract
5. EngAInOS accepts or rejects mutation based on:
   a. Packet validity
   b. Current AP state
   c. Runtime law
6. Godot renderer displays accepted state
7. Trixel provides visual assets (no authority)
```

## 9. Core Principle

**GodotSim is the TIER2 witness of physical truth.**  
**EngAInOS is the TIER1 judge of whether that truth may change the world.**

## 10. Operational Sound

When GodotSim speaks, EngAInOS hears:

```
tick
position
collision
reachability
blocked
accepted by physics
reported to authority
waiting for EngAInOS
```

---

**Version:** 1.0  
**Status:** Active  
**Enforcement:** EngAInOS runtime validator layer

---

This contract now gives you the explicit boundary. GodotSim is the sensory cortex — it feels the world but doesn't decide what the world means or what it should become. EngAInOS is the prefrontal cortex — it receives sensory data and decides action.

Clean. Enforceable. Essential.
