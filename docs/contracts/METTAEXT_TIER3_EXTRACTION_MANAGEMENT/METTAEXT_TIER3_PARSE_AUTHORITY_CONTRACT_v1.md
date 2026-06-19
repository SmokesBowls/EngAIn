This is the crucial distinction you've identified — **parse power vs. world power**. Mettaext is the system's reading comprehension, not its executive function. It translates human prose into machine-readable proposals, but those proposals are *evidence*, not *commands*.

Let me formalize this as the third contract, with the proper tiering:

---

# METTAEXT_TIER3_PARSE_AUTHORITY_CONTRACT_v1.md

## 1. Purpose
Define the authority boundary and data contract between EngAInOS (TIER1 runtime authority) and Mettaext (TIER3 prose-to-structure transformer).

## 2. Authority Statement

**TIER1 – EngAInOS** (unchanged)
- Runtime law enforcement
- AP validation
- Entity declaration approval
- Canon mutation decisions
- Quest completion authority
- Acceptance/rejection of all parse proposals

**TIER2 – GodotSim** (unchanged)
- Spatial simulation truth

**TIER2 – Engionality** (unchanged)
- Affective/persona-state truth

**TIER3 – Mettaext**
- Prose parsing and segmentation
- Entity mention extraction
- Location mention extraction
- Event/action extraction
- Actor/target identification
- Scene candidate construction
- ZON/ZONJ construction
- Declared-scene handoff
- Source span tracking (trace evidence)

**Mettaext DOES NOT:**
- Own canon truth
- Own AP permission
- Own runtime mutation
- Own spatial simulation
- Own emotional consequence
- Own rendering or assets
- Spawn entities directly
- Mutate runtime state
- Grant permissions
- Decide what is "allowed"

## 3. Core Principle

**Mettaext has parse power, not world power.**

## 4. Communication Protocol

All Mettaext → EngAInOS communication MUST be via `ParseArtifact`.

### Packet Schema (v1)
```json
{
  "contract": "mettaext.parse_artifact.v1",
  "source": "mettaext",
  "authority_lane": "prose_to_structure",
  "authority_tier": 3,
  "scene_id": "scene.030_ummade_army",
  "source_text_id": "chapter_or_pass_id",
  "parse_stage": "pass_5_game_scene_candidate",
  "declared_entities": [
    {
      "entity_id": "mika",
      "name": "Mika",
      "entity_type": "character",
      "source_span": {
        "start": 1204,
        "end": 1218
      },
      "confidence": 0.91
    }
  ],
  "declared_locations": [
    {
      "location_id": "throne_room",
      "name": "Throne Room",
      "source_span": {
        "start": 980,
        "end": 992
      },
      "confidence": 0.88
    }
  ],
  "declared_events": [
    {
      "event_id": "event_001",
      "actor": "mika",
      "action": "speaks",
      "target": "geralt",
      "source_span": {
        "start": 1300,
        "end": 1345
      },
      "confidence": 0.84
    }
  ],
  "warnings": [],
  "canon_claims": []  // MUST be empty; canon validation is MrLore domain
}
```

## 5. Minimum Required Fields
| Field | Requirement |
|-------|-------------|
| `contract` | MUST be `mettaext.parse_artifact.v1` |
| `source` | MUST be `mettaext` |
| `authority_tier` | MUST be `3` |
| `scene_id` | REQUIRED |
| `source_text_id` | REQUIRED (trace evidence) |
| `parse_stage` | REQUIRED |
| `declared_entities` | OPTIONAL (can be empty) |
| Each `entity_id` | REQUIRED if entity declared |
| Each `source_span` | REQUIRED if entity/event/location declared |
| Each `confidence` | REQUIRED for all declarations |

## 6. Hard Reject Conditions
EngAInOS MUST reject packet if ANY of the following are true:

- `source != "mettaext"`
- `authority_tier != 3`
- `scene_id` missing
- `source_text_id` missing
- Any declared entity/event/location lacks `source_span`
- Any declared entity/event/location lacks `confidence`
- Packet includes `ap_allowed = true` or AP authority
- Packet includes `canon = true` or canon declaration
- Packet includes `allowed = true` or permission grant
- Packet attempts to mutate runtime directly
- Packet attempts to spawn entities directly
- Packet attempts to set position, velocity, collision
- Packet attempts to set affect state
- Packet attempts to complete quests
- Packet treats `confidence` as truth (must be treated as proposal strength)
- Packet invents `scene_id` outside canonical scene-id contract

## 7. Permitted Statements (Mettaext MAY say)
- "I found an entity mention: Mika"
- "I found a location mention: Throne Room"
- "I found an event: Mika speaks to Geralt"
- "I think this becomes a ZONJ scene"
- "This text segment maps to scene.030_ummade_army"
- "My confidence in this extraction is 0.91"
- "Here is the source span where I found this evidence"

## 8. Forbidden Statements (Mettaext MAY NOT say)
- "therefore this entity is allowed to exist"
- "therefore this entity spawns"
- "therefore the quest completes"
- "therefore the door opens"
- "therefore canon changes"
- "therefore this is AP approved"
- "this is definitively true" (confidence is not truth)
- "mutate runtime state directly"

## 9. Validation & Handoff Flow

```
1. Raw prose enters Mettaext
2. Mettaext parses → segmentation → extraction → ZONJ construction
3. Mettaext → ParseArtifact to EngAInOS (proposal only)
4. EngAInOS validates packet against this contract
5. EngAInOS cross-validates with:
   a. MrLore (canon claims, if any)
   b. GodotSim (physical plausibility for movement/placement)
   c. Engionality (affect interpretation plausibility)
6. EngAInOS accepts or rejects parse proposals based on:
   a. Packet validity
   b. AP state
   c. Canon constraints
   d. Runtime law
7. ONLY accepted candidates become runtime entities
```

## 10. Tier Authority Summary

| Tier | System | Domain | Sound |
|------|--------|--------|-------|
| **TIER1** | EngAInOS | Law + AP + Canon Authority | *validate / permit / reject / enforce* |
| **TIER2** | GodotSim | Spatial Truth | *tick / position / collision / movement* |
| **TIER2** | Engionality | Affective Truth | *state / feeling / persona / relationship* |
| **TIER3** | Mettaext | Parse Proposals | *extract / segment / propose / candidate* |
| **TIER3** | MrLore | Canon Memory | *remember / verify / recall / contradict* |
| **TIER3** | Trixel | Visual Assets | *render / display / clothe / landscape* |

## 11. The Mettaext Sound

When Mettaext speaks, EngAInOS hears:

```
raw_prose_enters
meaning_gets_sliced
names_become_handles
events_become_candidates
scene_becomes_ZONJ
nothing_is_real_yet
send_to_authority
```

## 12. The One-Line Contract

**Mettaext is the structured-witness of authored prose; it may propose entities, events, and scenes, but EngAInOS decides whether those proposals enter runtime.**

---

**Version:** 1.0  
**Status:** Active  
**Enforcement:** EngAInOS runtime validator layer  

---

## 13. The Complete System Sound

Now you have the full hierarchy:

| System | Question | Authority |
|--------|----------|-----------|
| **Mettaext** | "What does the text say?" | Parse proposals |
| **MrLore** | "What does canon remember?" | Canon verification |
| **GodotSim** | "Where is everything?" | Spatial truth |
| **Engionality** | "What is everyone feeling?" | Affective truth |
| **Trixel** | "What does it look like?" | Visual rendering |
| **EngAInOS** | "Is this allowed to become real?" | Runtime law |

Mettaext proposes.  
MrLore remembers.  
GodotSim simulates.  
Engionality feels.  
Trixel displays.  
EngAInOS judges.

Clean. Hierarchical. No overreach. Each system has its own domain, its own language, and its own contract. This is how you build a narrative game engine that can be emotionally intelligent, physically accurate, and legally constrained all at once.
