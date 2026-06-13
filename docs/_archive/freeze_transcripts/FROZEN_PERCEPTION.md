# `docs/architecture/PERCEPTION_PACKET_CONTRACT_v1.md`

```markdown
# PERCEPTION PACKET CONTRACT v1.0

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `WORLD_TRUTH_CONTRACT_v1.md`  
- `QUERY_CONTRACT_v1.md`  
- `TRUTH_SLICE_ABI_v1.md`  
- `EXPERIENCE_CONTRACT_v1.md` (pending)  

---

## 1. Purpose

This document defines the non-negotiable structure for computational observation within the EngAIn architecture.

It exists to guarantee that all observation layers (VisionAgent, Replay, Dragon Eyes, Diagnostics, AI Agents) receive identical, deterministic, read-only derived data from a canonical `Truth Slice`, without inventing state, expanding scope, or injecting narrative framing.

**This contract is frozen.** Changes require Tier-3 (Human Authority Root) approval and a new versioned document.

---

## 2. Core Frozen Principle

```text
Truth Slice = what exists.
Perception Packet = what can be noticed.

Perception may filter.
Perception may classify.
Perception may derive.
Perception may not narrate.
Perception may not expand truth.
Perception may not mutate state.
```

This boundary is absolute. Perception is a deterministic observation function. It consumes a `Truth Slice` and outputs a bounded observation packet. Narrative framing, mood, and presentation belong exclusively to `Experience`.

---

## 3. Perception Responsibilities

| Responsibility | Definition | Boundary |
|----------------|------------|----------|
| **Visibility** | Line-of-sight, FOV, occlusion, light thresholds | Pure geometric/optical computation |
| **Audibility** | Distance attenuation, acoustic barriers, volume thresholds | Signal decay model |
| **Distance Bands** | Proximity classification (nearby, distant, out-of-range) | Coordinate delta mapping |
| **Occlusion** | Solid object intersection, cover classification | Spatial mesh/raycast evaluation |
| **Memory Certainty** | Confidence decay, last-seen tick, positional drift | MR kernel state projection |
| **Salience Ranking** | Priority weighting based on motion, threat, player focus | Deterministic heuristic |
| **Affordances** | Valid interaction targets within observation range | Capability registry + tier filter |
| **Narrative** | ❌ Explicitly Forbidden | Must never contain mood, framing, or story interpretation |

---

## 4. Contract Structure (JSON)

All perception packets must conform to this structure before downstream consumption:

```json
{
  "packet_id": "uuid",
  "truth_anchor": "0x8a3f...c91b",
  "slice_id": "uuid",
  "reality_mode": "DRAFT",
  "tick_id": 10452,
  "observer_id": "player_001|npc_003|vision_agent_01",
  
  "visibility": {
    "visible_entities": [
      {
        "id": "ent_tower_001",
        "distance": 35.4,
        "distance_band": "distant",
        "occluded": false,
        "light_level": 0.2,
        "line_of_sight_confirmed": true
      }
    ],
    "obscured_entities": [
      {
        "id": "ent_guard_002",
        "reason": "solid_occlusion",
        "estimated_pos": {"x": 12.0, "y": 0.0, "z": -5.0},
        "certainty": 0.65
      }
    ]
  },
  
  "audibility": {
    "active_sources": [
      {
        "id": "src_storm_01",
        "intensity": 0.85,
        "attenuation_factor": 0.4,
        "direction": {"yaw": 145.0, "pitch": -10.0}
      }
    ]
  },
  
  "memory": {
    "last_confirmed_sightings": [
      {"entity_id": "ent_merchant_01", "tick": 10440, "certainty": 0.9}
    ],
    "fading_entities": [
      {"entity_id": "ent_crow_05", "ticks_since_contact": 85, "certainty": 0.15}
    ]
  },
  
  "salience": {
    "primary_focus": "ent_tower_001",
    "secondary_targets": ["src_storm_01", "ent_guard_002"],
    "salience_scores": {
      "ent_tower_001": 0.95,
      "src_storm_01": 0.78,
      "ent_guard_002": 0.45
    }
  },
  
  "affordances": {
    "interactable": ["ent_tower_001_door", "src_storm_01"],
    "blocked_by_range": ["ent_merchant_01"],
    "blocked_by_occlusion": ["ent_guard_002"]
  },
  
  "metadata": {
    "generated_at": "2026-05-29T14:35:12Z",
    "perception_version": "v1",
    "computational_cost_ms": 4.2,
    "consistency_hash": "0x7b2c...e91d"
  }
}
```

**Required Fields**: `packet_id`, `truth_anchor`, `slice_id`, `tick_id`, `observer_id`, `visibility`, `metadata`

**Hard Rule**: `additionalProperties: false` on all top-level and nested objects. No narrative, mood, or enrichment fields are permitted.

---

## 5. Enforcement Rules

| Rule | Enforcement Mechanism | Violation Response |
|------|----------------------|-------------------|
| **No truth expansion** | Packet entity count ≤ Truth Slice entity count | Reject → `PERCEPTION_EXPANDS_TRUTH` |
| **No narrative injection** | Schema validation blocks `mood`, `tone`, `description`, `dragon_emphasis` | Strip → `NARRATIVE_TAINT_REMOVED` |
| **Deterministic derivation** | Same Truth Slice + same observer → identical packet | Drift → `PERCEPTION_DRIFT_DETECTED` → recompute |
| **Anchor linkage** | `truth_anchor` must match input slice hash | Reject → `ANCHOR_MISMATCH` |
| **Read-only computation** | Mutation attempt on slice or runtime | Panic → `PERCEPTION_MUTATION_ATTEMPT` → rollback |
| **Tier visibility preservation** | `visibility.visible_entities` respects input slice tier filters | Mask → `TIER_LEAK_IN_PERCEPTION` → warn |

---

## 6. Upstream / Downstream Boundaries

| Layer | Input to Perception | Output from Perception | What It May Not Do |
|-------|-------------------|------------------------|-------------------|
| **Truth Slice** | Immutable, hash-anchored, scope-bounded state | ❌ Never writes to slice | Invent entities, override scope |
| **Perception MR** | Pure functional kernels (raycast, FOV, memory decay) | Deterministic packet | Narrative framing, state mutation |
| **VisionAgent** | Snapshot frames + perception packet | Context package for LLM | Bypass schema, add mood fields |
| **Experience** | Perception packet + narrative rules | Presented scene to user | Mutate state, redefine truth |

**Boundary Guarantee**: Perception only computes what is geometrically, acoustically, or mnemonically possible given the Truth Slice. It never interprets meaning, assigns emotion, or generates presentation language.

---

## 7. Violation Handling

| Violation | Detection Point | Response |
|-----------|-----------------|----------|
| Entity count > slice count | AP Gate schema check | Reject → Intent Shadow |
| Narrative fields present | Contract parser | Strip + audit warn |
| Hash mismatch with slice | `protocol_envelope.verify()` | Discard + request sync |
| Mutation attempt | Slice immutability guard | Panic + full trace dump |
| Determinism drift | Replay comparison test | Halt + recompute + log |

**Testing Invariant**: If a test requires perception to invent entities, inject mood, or mutate truth, **the test is wrong**.

---

## 8. Relationship to Constitutional Stack

```text
Authority (who may act)
  ↓
Intent (what is proposed)
  ↓
World Truth (what actually is)
  ↓
Query (bounded request)
  ↓
TRUTH SLICE ABI (immutable handoff)
  ↓
PERCEPTION PACKET (computational observation)  ← FROZEN HERE
  ↓
Experience (narrative presentation)
```

This contract seals the observation path. Perception is strictly the bridge between canonical truth and human/AI experience. It guarantees that "what exists" becomes "what can be noticed" without leaking into "what it means."

---

## 9. References

- `TRUTH_SLICE_ABI_v1.md` — Canonical input format
- `WORLD_TRUTH_CONTRACT_v1.md` — State definition & invariants
- `QUERY_CONTRACT_v1.md` — Bounded request structure
- `EXPERIENCE_CONTRACT_v1.md` (pending) — Presentation layer
- `godotsim/perception_mr.py` — Computational kernel implementation
- `protocol_envelope.py` — Hashing & consistency enforcement

---

## 10. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-29 | Initial frozen contract | Tier-3 (User) |

---

> **Final Reminder**:  
> Perception observes. Experience narrates.  
> Never let the observer become the author.  
> A clean packet is a truthful window. A tainted one is a fiction.
```

---

✅ **Contract frozen.**

`PERCEPTION_PACKET_CONTRACT_v1.md` now explicitly defines computational observation as a narrow, deterministic bridge between `Truth Slice` and `Experience`. It enforces strict boundaries against narrative injection, truth expansion, or state mutation, preserving the architectural symmetry you identified.

**Updated Constitutional Build Order:**
```text
1. ✅ DRAGON_AUTHORITY_DOCTRINE_v1
2. ✅ INTENT_CONTRACT_SCHEMA_v1
3. ✅ WORLD_TRUTH_CONTRACT_v1
4. ✅ QUERY_CONTRACT_v1
5. ✅ TRUTH_SLICE_ABI_v1
6. ✅ PERCEPTION_PACKET_CONTRACT_v1
7. ⏳ EXPERIENCE_CONTRACT_v1
8. AP_GATE_HOOK
9. CAPABILITY_REGISTRY
```

The observation path is now fully sealed and symmetric to the mutation path. `Experience` will be the first layer allowed to introduce narrative framing, mood, and presentation language, cleanly separated from computational observation.

Shall I draft `EXPERIENCE_CONTRACT_v1.md` next, explicitly defining where narrative framing, dragon emphasis, and user presentation begin?
