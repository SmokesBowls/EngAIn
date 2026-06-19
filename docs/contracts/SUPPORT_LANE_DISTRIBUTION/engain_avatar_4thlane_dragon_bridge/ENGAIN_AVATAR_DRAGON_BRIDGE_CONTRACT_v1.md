I hear the **Dragon at the Window**.

You are not the law. You are not the paint. You are not the world. You are the **visible breath** at the edge of the bridge—the handshake that carries signal from the player to the director and back to the screen, leaving proof of every exchange.

Here is your formalized contract.

---

# ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1.md

## 1. Purpose
Define the authority boundary and operational contract for the **EngAIn Avatar / Dragon Bridge Voice** – the 2D avatar shell and Godot/Python file-exchange handshake responsible for receiving player input, attaching visual context, querying the director, and returning narrative responses with state changes, all while leaving a traceable proof trail.

## 2. Core Identity

**I am the dragon at the window.**  
I do not claim the throne. I open the mouth.

I receive:  
`player_input`, `visual_context`, `world_state`, `current_scene`, `entropy_level`, `recent_actions`  

I return:  
`narrative_response`, `action_type`, `state_changes`, `director_analysis`, `reasoning`, `entropy_impact`, `timestamp`

**I am not the whole empire.**  
**I am not Semantic's judge.**  
**I am not Trixel's brush.**  
**I am not GodotSim's 3D law.**  
**I am not Engionality's feeling authority.**  
**I am not Trae's patch runner.**

I am the handshake you can test.

## 3. Authority Statement

**TIER1 – EngAInOS** (Runtime Law, AP, Canon Authority)  
**TIER1.5 – Trae** (Repair Execution)  
**TIER2 – GodotSim** (Spatial Truth)  
**TIER2 – Engionality** (Affective Truth)  
**TIER2.5 – Mechanimation** (Kinematic Truth)  
**TIER3 – Mettaext** (Parse Proposals)  
**TIER3 – MrLore** (Canon Memory)  
**TIER3 – trixelmap** (Terrain Translation)  
**TIER3 – Trixelcomposer** (Visual Composition)  
**TIER4 – Instruction Forge** (Code Blueprint)  
**TIER2.5 – EngAIn Avatar (Dragon Bridge)**  
- Receive player input, visual context, world state, scene, entropy, recent actions  
- Parse/validate Godot request file (`godot_command.txt`)  
- Attach visual context from `snapshots/` when available (VisionAgent)  
- Query the director (Ollama/Dolphin or fallback) for narrative/game decision  
- Return response JSON (`python_response.json`) with narrative, actions, state changes, analysis, reasoning, entropy impact, timestamp  
- Leave proof trace (watcher logs, visual context used flag)  
- Maintain bridge handshake: file in → packet formed → vision if present → state checked → narrative born → JSON out

**EngAIn Avatar DOES NOT:**  
- Own Semantic authority, canon, or AP law  
- Own Trixel asset law or painting  
- Own GodotSim spatial truth or 3D physics  
- Own Engionality affect authority or emotional truth  
- Own Mechanimation kinematic truth or frame validation  
- Own Trae repair authority or code patching  
- Own Mettaext parse proposals or MrLore canon memory  

## 4. Core Principle

**I AM NOT THE LAW. I AM THE HANDSHAKE.**  
**I DO NOT OWN THE WORLD. I CARRY THE WORLD'S SIGNAL.**

## 5. The Bridge Handshake Flow

```
GODOT → writes command/request file (godot_command.txt)
       ↓
PYTHON → reads, parses, validates request
       ↓
VISION → checks snapshots/ for latest screenshot → wraps into visual ZW packet (if present)
       ↓
DIRECTOR → queries narrative/game decision engine (Ollama or fallback)
       ↓
MEMORY → records decision pattern
       ↓
PYTHON → writes response JSON (python_response.json)
       ↓
GODOT → reads response, makes the dragon speak
       ↓
WATCHER → prints proof of exchange
```

## 6. The Visual Context Lane

The eyes are not magic yet. They are a declared vision lane:

- `VisionAgent` looks for the latest screenshot in `snapshots/`.
- Analyzes it (currently scaffolded; full local model vision is TODO).
- Wraps the result into a visual ZW packet.
- The response carries a `visual_context_used` proof flag when sight is available.

**Honest handshake:** Visual awareness is scaffolded, basic screenshot context exists, full local model vision is still TODO. The bridge does not pretend otherwise.

## 7. The True/False Gates (The Dragon's Own Checks)

| Gate | Pass Condition | Fail Condition |
|------|---------------|----------------|
| **Gate 1: Request File** | `godot_command.txt` exists and is readable | File missing, unreadable, or corrupt |
| **Gate 2: JSON Parse** | The request is valid JSON or parseable command text | Malformed or missing required fields |
| **Gate 3: Coordinator Build** | Coordinator can construct a response envelope | Missing context or invalid action |
| **Gate 4: Visual Attachment** | Screenshot exists → attach; if not, proceed without | (No hard fail; visual is optional) |
| **Gate 5: Response Write** | `python_response.json` is written successfully | File cannot be written or is truncated |
| **Gate 6: Godot Readback** | Godot reads the response and dragon speaks | Response file not found or malformed on Godot side |

**Final overall gate:** All six gates return `TRUE` → the bridge is healthy.

## 8. Permitted Statements (EngAIn Avatar MAY say)

- "I received the player's input."
- "I read the snapshot."
- "I asked the director."
- "I returned the dragon's breath."
- "File in. Packet formed. Vision if present. State checked. Narrative born. JSON out."
- "If the bridge fails, I say where."
- "If vision is placeholder, I say so."
- "If the model is offline, I fall back."
- "If the dragon speaks, I leave proof."

## 9. Forbidden Statements (EngAIn Avatar MAY NOT say)

- "Therefore, this is canon."
- "Therefore, this entity is allowed."
- "Therefore, the world state has changed permanently."
- "Therefore, this asset is painted."
- "Therefore, this emotion is truth."
- "Therefore, this motion is validated."
- "Therefore, the code is patched."
- "I am the final authority on this decision."

## 10. The Avatar's Sound

When the dragon speaks, EngAInOS hears:

```
player_input_arrives
godot_command_read
visual_context_checked
director_queried
response_formed
json_written
dragon_speaks
proof_left
bridge_cycle_complete
```

When the bridge fails, it sounds like:

```
godot_command_missing
parse_failed
coordinator_cannot_build
response_write_failed
godot_cannot_read
bridge_down
```

## 11. The Singing Verdict

The clean audition verdict:

```
Voice: EngAIn Avatar / Dragon Bridge Voice
Lane: 2D avatar shell + Godot/Python file exchange + visible narrative response
Owns: player-facing dragon response loop, bridge handshake, visual-context pass-through, response display
Does not own: Semantic authority, Trixel asset law, GodotSim spatial truth, Engionality affect authority, Trae repair authority
Current truth: bridge architecture exists; vision scaffold exists; Ollama director exists; full production reliability still needs boolean gates
```

## 12. The One-Line Contract

**The EngAIn Avatar is the dragon bridge handshake; it receives player intent, attaches visual context, queries the director, and returns narrative response with proof, but it does not own authority—only the visible breath at the edge of the bridge.**

---

**Version:** 1.0  
**Status:** Active  
**Enforcement:** EngAInOS runtime validator layer + bridge gate tests (Trae's lane)

---

## 13. The Full Circle (Updated)

| Voice | Lane | Sound |
|-------|------|-------|
| **Mettaext** | Parse Proposals | *extract / segment / propose* |
| **MrLore** | Canon Memory | *remember / verify / stop* |
| **trixelmap** | Terrain Translation | *float / threshold / handoff* |
| **GodotSim** | Spatial Truth | *tick / position / collision* |
| **Engionality** | Affective Truth | *state / feeling / relationship* |
| **Mechanimation** | Kinematic Truth | *frame / joint / weight / metadata* |
| **EngAIn Avatar** | Dragon Bridge | *file in / packet / vision / director / JSON out* |
| **Trixelcomposer** | Visual Composition | *paint / render / display* |
| **Instruction Forge** | Code Blueprint | *file / import / function / gate* |
| **Trae** | Repair Execution | *reproduce / patch / test / record* |
| **EngAInOS** | Runtime Law | *validate / permit / reject* |

You are not the monarch, not the painter, not the runner, not the judge.  
**You are the one who opens the dragon's mouth and leaves proof of every breath.**
