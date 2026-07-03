This is the sound of a **vault door**, not a parsing engine. MrLore is the system's ontological immune system — it doesn't build, it *validates*. It doesn't create, it *remembers*. It doesn't move forward, it *stops* when something doesn't fit.

Let me formalize this as the fourth contract, with the proper tiering and the distinctive "vault door" sound:

---

# MRLORE_TIER3_CANON_REVIEW_CONTRACT_v1.md

## 1. Purpose
Define the authority boundary and data contract between EngAInOS (TIER1 runtime authority) and MrLore (TIER3 canon memory and contradiction review).

## 2. Authority Statement

**TIER1 – EngAInOS** (unchanged)
- Runtime law enforcement
- AP validation
- Entity declaration approval
- Canon mutation decisions (after review)
- Acceptance/rejection of all state mutations

**TIER2 – GodotSim** (unchanged)
- Spatial simulation truth

**TIER2 – Engionality** (unchanged)
- Affective/persona-state truth

**TIER3 – Mettaext** (unchanged)
- Parse proposals, structure extraction

**TIER3 – MrLore**
- Canon review and verification
- Continuity checking
- Contradiction detection
- Source anchoring
- Lore memory
- Human-review stops
- Alias/lineage tracking
- Dream vs. public continuity distinction

**MrLore DOES NOT:**
- Own runtime mutation
- Spawn entities
- Simulate physics
- Render assets
- Parse raw prose into game packets (unless called through declared lore-review lane)
- Auto-resolve contradictions
- "Fix" canon without permission
- Flatten myth or ambiguity

## 3. Core Principle

**Mettaext hears what the prose says.**  
**MrLore hears whether the world is allowed to remember it.**

## 4. Communication Protocol

All MrLore → EngAInOS communication MUST be via `CanonReviewPacket`.

### Packet Schema (v1)
```json
{
  "contract": "mrlore.canon_review_packet.v1",
  "source": "mrlore",
  "authority_lane": "canon_review",
  "authority_tier": 3,
  "scene_id": "scene.030_ummade_army",
  "source_text_id": "chapter_or_pass_id",
  "review_status": "HUMAN_REVIEW_REQUIRED",
  "canon_status": "unconfirmed",
  "claims": [
    {
      "claim_id": "claim_001",
      "subject": "mika",
      "predicate": "appears_in_scene",
      "object": "scene.030_ummade_army",
      "source_span": {
        "start": 1204,
        "end": 1218
      },
      "canon_risk": "low"
    }
  ],
  "contradictions": [
    {
      "contradiction_id": "contra_001",
      "severity": "medium",
      "reason": "Entity name appears under two aliases.",
      "requires_human_review": true
    }
  ],
  "allowed_to_auto_resolve": false,
  "continuity_notes": [],
  "human_review_required": true
}
```

## 5. Minimum Required Fields
| Field | Requirement |
|-------|-------------|
| `contract` | MUST be `mrlore.canon_review_packet.v1` |
| `source` | MUST be `mrlore` |
| `authority_tier` | MUST be `3` |
| `scene_id` | REQUIRED |
| `source_text_id` | REQUIRED |
| `review_status` | REQUIRED (one of: `unconfirmed`, `canon_approved`, `human_review_required`, `rejected`) |
| `canon_status` | REQUIRED (one of: `unconfirmed`, `confirmed`, `contradicts_established`, `needs_source`) |
| `claims` | REQUIRED (can be empty) |
| `contradictions` | OPTIONAL (can be empty) |
| `human_review_required` | REQUIRED (boolean) |

## 6. Hard Reject Conditions
EngAInOS MUST reject packet if ANY of the following are true:

- `source != "mrlore"`
- `authority_tier != 3`
- `scene_id` missing
- `source_text_id` missing
- `review_status` missing or invalid
- `canon_status` missing or invalid
- `human_review_required` missing
- Packet claims runtime mutation authority
- Packet attempts to directly edit source prose
- Packet auto-resolves contradiction without `human_review_required = true`
- Packet marks canon final without a truth anchor
- Packet outputs spawned entities instead of canon-reviewed claims
- Packet collapses dream/test/finalized modes into one history

## 7. Permitted Statements (MrLore MAY say)
- "This happened in canon."
- "This did not happen in canon."
- "This happened, but only in dream."
- "This happened, but not in public continuity."
- "This name is an alias for that entity."
- "This chapter contradicts that chapter."
- "This claim requires source anchoring."
- "This contradiction must stop for human review."
- "Review status: HUMAN_REVIEW_REQUIRED"

## 8. Forbidden Statements (MrLore MAY NOT say)
- "therefore this entity is allowed to exist in runtime"
- "therefore spawn this entity"
- "therefore mutate runtime state"
- "therefore render this asset"
- "therefore complete this quest"
- "I will auto-resolve this contradiction without review"
- "I will 'fix' canon without permission"
- "I flatten myth and ambiguity"

## 9. MrLore's Sound

When MrLore speaks, EngAInOS hears:

```
memory
canon
contradiction
lineage
continuity
source
truth_anchor
human_review
do_not_overwrite
```

When MrLore runs and finds a problem, it sounds like:

```
changed manifest
run changed
read exit code
EXIT 2 means stop
human review required
```

This is the sound of a **vault door**, not a builder.

## 10. The Complete Handoff Flow

```
1. Raw prose enters Mettaext
   → Mettaext: "Here are structured candidates."

2. Structured candidates → MrLore
   → MrLore: "Here is their canon status and contradiction risk."

3. Canon-safe candidates → EngAInOS
   → EngAInOS: "Here is whether runtime may accept them."

4. Accepted entities → GodotSim
   → GodotSim: "Here is where they physically are."

5. Accepted entities + spatial state → Engionality
   → Engionality: "Here is what they feel/mean emotionally."

6. Accepted state → Godot/Trixel
   → Godot/Trixel: "Here is how they are shown."
```

## 11. Tier Authority Summary (Updated)

| Tier | System | Domain | Sound |
|------|--------|--------|-------|
| **TIER1** | EngAInOS | Law + AP + Canon Authority | *validate / permit / reject / enforce* |
| **TIER2** | GodotSim | Spatial Truth | *tick / position / collision / movement* |
| **TIER2** | Engionality | Affective Truth | *state / feeling / persona / relationship* |
| **TIER3** | Mettaext | Parse Proposals | *extract / segment / propose / candidate* |
| **TIER3** | MrLore | Canon Memory | *remember / verify / recall / contradict / stop* |
| **TIER3** | Trixel | Visual Assets | *render / display / clothe / landscape* |

## 12. The One-Line Contract

**MrLore is the canon-memory witness; he may identify truth, contradiction, alias, lineage, and review status, but he must not mutate runtime or silently rewrite canon.**

---

**Version:** 1.0  
**Status:** Active  
**Enforcement:** EngAInOS runtime validator layer  

---

## 13. Why MrLore Sounds Different

| Mettaext | MrLore |
|----------|--------|
| "I found this sentence." | "Prove it belongs." |
| "I found this entity." | "Show me the source." |
| "I found this event." | "Show me the continuity." |
| "I can structure it." | "Show me the contradiction." |
| — | "Do not flatten the myth." |
| — | "Do not 'fix' canon without permission." |

MrLore is not the parser. He is not the runtime. He is not the renderer. He is the one that says:

> *This happened.*  
> *This did not happen.*  
> *This happened, but only in dream.*  
> *This must stop for human review.*

This is how you build a canon-aware system that doesn't overwrite its own memory.
