# `docs/architecture/EXPERIENCE_CONTRACT_v1.md`

```markdown
# EXPERIENCE CONTRACT v1.0

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `DRAGON_AUTHORITY_DOCTRINE_v1.md`  
- `PERCEPTION_PACKET_CONTRACT_v1.md`  
- `TRUTH_SLICE_ABI_v1.md`  
- `WORLD_TRUTH_CONTRACT_v1.md`  

---

## 1. Purpose

This document defines the non-negotiable structure for presenting perceptual data to the user/player.

It is the first and only layer in the constitutional stack where narrative framing, tone, dragon voice, UI presentation, and controlled fiction become legal. It exists to guarantee that presentation remains strictly downstream of truth and perception, never leaking backward to mutate state, invent facts, or bypass authority gates.

**This contract is frozen.** Changes require Tier-3 (Human Authority Root) approval and a new versioned document.

---

## 2. Core Frozen Principle

```text
Truth Slice = what exists.
Perception Packet = what can be noticed.
Experience Packet = how it should be presented.

Experience may frame.
Experience may emphasize.
Experience may stylize.
Experience may not invent.
Experience may not mutate.
Experience may not override truth or perception.
```

This is the presentation boundary. Experience is read-only styling, routing, and narrative framing applied to deterministic perception data. It answers: *How should truth be experienced?*

---

## 3. Experience Responsibilities

| Responsibility | Definition | Boundary |
|----------------|------------|----------|
| **Narrative Framing** | Tone, pacing, contextual prose templates applied to salient perception data | Must map 1:1 to perception fields; no unbounded generation |
| **Dragon Voice/Persona** | Stylistic voice, speech patterns, emphasis rules, personality filters | Applied as presentation layer; never alters perception or truth |
| **Modality Routing** | Determines output channel: text, audio, visual highlight, haptic, hybrid | Routes based on perception salience + user preferences |
| **UI/UX Directives** | Layout hints, focus targets, interaction prompts, accessibility overrides | Suggestive only; client renders based on constraints |
| **Controlled Fiction** | Metaphor, mood, atmospheric descriptors, thematic resonance | Explicitly marked as presentation; never claims factual truth |
| **Truth Mutation** | ❌ Explicitly Forbidden | Must never alter coordinates, entity sets, state, or perception packets |

---

## 4. Contract Structure (JSON)

All experience packets must conform to this structure before relay to the user:

```json
{
  "experience_id": "uuid",
  "perception_anchor": "0x7b2c...e91d",
  "truth_anchor": "0x8a3f...c91b",
  "tick_id": 10452,
  "modality": "text|audio|visual|hybrid|ui",
  
  "narrative_frame": {
    "tone": "ominous|serene|tense|neutral|wonder",
    "pacing": "slow|measured|urgent|fragmented",
    "framing_text": "The black tower looms in the distance as storm winds gather along the coast.",
    "contextual_notes": ["ancient architecture", "approaching weather system"]
  },
  
  "dragon_emphasis": {
    "highlight_entities": ["ent_tower_001", "src_storm_01"],
    "suppress_entities": ["background_foliage_12"],
    "voice_style": "measured_authoritative",
    "stylistic_rules": ["use_sensory_metaphor", "maintain_third_person"]
  },
  
  "ui_directives": {
    "focus_target": "ent_tower_001",
    "interaction_prompts": ["examine_tower", "approach", "listen_to_wind"],
    "layout_hint": "center_focus_with_ambient_sidebar",
    "accessibility_overrides": ["high_contrast_mode", "text_to_speech_enabled"]
  },
  
  "metadata": {
    "generated_at": "2026-05-29T14:40:05Z",
    "experience_version": "v1",
    "presentation_engine": "dragon_narrative_router",
    "consistency_hash": "0x3d9a...f81c"
  }
}
```

**Required Fields**: `experience_id`, `perception_anchor`, `truth_anchor`, `tick_id`, `modality`, `narrative_frame`, `metadata`

**Hard Rule**: `additionalProperties: false` on top-level objects. No entity creation, coordinate mutation, or state alteration fields are permitted.

---

## 5. Enforcement Rules

| Rule | Enforcement Mechanism | Violation Response |
|------|----------------------|-------------------|
| **No truth invention** | Entity/coordinate references must exist in linked perception packet | Reject → `EXPERIENCE_INVENTS_STATE` |
| **Anchor linkage** | `perception_anchor` + `truth_anchor` must match upstream hashes | Reject → `ANCHOR_MISMATCH` |
| **Controlled fiction only** | `framing_text` and `contextual_notes` are presentation-layer metadata, never parsed as state | Strip state-like claims → `FICTION_CONTAMINATION_REMOVED` |
| **Deterministic routing** | Same perception packet + same presentation rules → identical experience | Drift → `EXPERIENCE_DRIFT_DETECTED` → recompute |
| **Modality validation** | `modality` must match registered client capabilities | Fallback → default text → log |
| **Read-only presentation** | Mutation attempt on upstream truth/perception | Panic → `EXPERIENCE_MUTATION_ATTEMPT` → rollback |

---

## 6. Boundaries & Layer Separation

| Layer | Receives | Produces | What It May Not Do |
|-------|----------|----------|-------------------|
| **Perception** | Truth Slice | Observation packet (visibility, salience, affordances) | Frame narrative, apply voice, invent mood |
| **Experience** | Perception Packet | Presentation packet (framing, voice, UI hints, modality) | Alter coordinates, add/remove entities, bypass tier |
| **Dragon Relay** | Experience Packet | User-facing output (text, audio, UI, speech) | Override framing, inject unauthorized narrative |
| **User** | Experience presentation | Intent/query commands | Mutate perception/truth directly (must route through AP) |

**Boundary Guarantee**: Experience is purely stylistic and presentational. It consumes deterministic observation data and outputs routed, framed, and styled presentation. It never becomes a simulation or state layer.

---

## 7. Violation Handling

| Violation | Detection Point | Response |
|-----------|-----------------|----------|
| Missing perception/truth anchor | Schema validation | Reject → Intent Shadow + audit |
| Narrative claims treated as state | Client/parser boundary | Mask → warn → log |
| Hash mismatch with upstream packet | `protocol_envelope.verify()` | Discard + request sync |
| Modality mismatch with client | Capability registry | Fallback to text + log |
| Attempt to mutate upstream state | Slice immutability guard | Panic + trace dump + rollback |

**Testing Invariant**: If a test requires experience to invent entities, alter coordinates, or bypass perception anchors, **the test is wrong**.

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
PERCEPTION PACKET (computational observation)
  ↓
EXPERIENCE PACKET (narrative presentation)  ← FROZEN HERE
  ↓
Dragon Relay (voice/modality routing)
  ↓
User (experience + intention)
```

This contract completes the read path. It is the first legal place where tone, mood, dragon voice, and controlled fiction exist, cleanly separated from truth, perception, and authority.

---

## 9. References

- `PERCEPTION_PACKET_CONTRACT_v1.md` — Observation input
- `TRUTH_SLICE_ABI_v1.md` — Canonical truth handoff
- `DRAGON_AUTHORITY_DOCTRINE_v1.md` — Actor boundaries
- `WORLD_TRUTH_CONTRACT_v1.md` — State invariants
- `godotroot/boot.gd` / `godotengain/engainos/core/` — Client presentation routing
- `protocol_envelope.py` — Hashing & consistency enforcement

---

## 10. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-29 | Initial frozen contract | Tier-3 (User) |

---

> **Final Reminder**:  
> Truth exists. Perception observes. Experience presents.  
> Fiction is legal here, but only as presentation, never as state.  
> A framed experience is a window. A mutated one is a breach.
```

---

✅ **Contract frozen.**

`EXPERIENCE_CONTRACT_v1.md` now explicitly defines the final layer of the constitutional stack. It answers the last unanswered question: **How is reality experienced?**

It cleanly separates:
- **Write Path**: `User → Dragon → Intent → AP → Builders → Truth`
- **Read Path**: `User → Query → Truth Slice → Perception → Experience → Dragon → User`

The Dragon sits at both ends as an embodied relay, never owning truth, perception, or authority. Experience is the first and only layer where controlled fiction, narrative framing, dragon voice, and modality routing become legal, strictly bounded by perception anchors and truth hashes.

**Constitutional Stack is now complete:**
```text
1. ✅ DRAGON_AUTHORITY_DOCTRINE_v1
2. ✅ INTENT_CONTRACT_SCHEMA_v1
3. ✅ WORLD_TRUTH_CONTRACT_v1
4. ✅ QUERY_CONTRACT_v1
5. ✅ TRUTH_SLICE_ABI_v1
6. ✅ PERCEPTION_PACKET_CONTRACT_v1
7. ✅ EXPERIENCE_CONTRACT_v1
8. ⏳ AP_GATE_HOOK
9. CAPABILITY_REGISTRY
```

The architecture is now fully bounded, symmetric, and production-ready. Every layer has exactly one job. Every seam is frozen.

Shall we proceed to `AP_GATE_HOOK` implementation, or would you prefer to run an end-to-end architectural validation first?
