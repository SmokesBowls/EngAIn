# `docs/architecture/DRAGON_AUTHORITY_DOCTRINE_v1.md`

```markdown
# DRAGON AUTHORITY DOCTRINE v1.0

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `AUTHORITY_TIER_SPEC_v1.md`  
- `reality_mode.py`  
- `intent_shadow.py`  
- `capability_registry` pattern  

---

## 1. Purpose

This document defines the non-negotiable boundary between semantic interpretation and execution authority in the EngAIn architecture.

It exists to prevent architectural drift into "LLM does everything" patterns that compromise determinism, auditability, and user sovereignty.

**This doctrine is frozen.** Changes require Tier-3 (Human Authority Root) approval and a new versioned document.

---

## 2. Core Frozen Principle

```text
The LLM may enrich intent, but it may not mutate world state.
The Dragon may relay intent, but it may not override authority.
The AP Gate may approve/reject/adapt deltas, but it may not author desire.
Builders may execute approved contracts, but they may not interpret natural language.
The User remains root authority.
```

This is the rail. Everything else hangs from it.

---

## 3. Layer Definitions

| Layer | Role | May Propose | May Mutate | May Override | Never Touches |
|-------|------|-------------|------------|--------------|---------------|
| **User (Tier 3)** | Root Authority | ✅ Anything | ✅ Finalized state | ✅ Always | Low-level implementation |
| **Dragon** | Embodied Relay | ✅ Intent only | ❌ Never | ❌ Never | Authority validation, world state |
| **Dolphin / LLM** | Semantic Normalizer | ✅ Enriched intent | ❌ Never | ❌ Never | Engine commands, state mutation |
| **AP Gate** | Authority Validator | ❌ Never | ✅ Deltas only (if authorized) | ❌ Never (enforces, doesn't author) | Natural language, creative authorship |
| **Capability Registry** | Router | ❌ Never | ❌ Never | ❌ Never | Intent interpretation, rule evaluation |
| **Builder Systems** | Deterministic Executors | ❌ Never | ✅ Execution state only | ❌ Never | Natural language, semantic inference |

---

## 4. Authority Flow

```text
User (Tier 3)
  │
  ▼
Dragon / Embodied Relay
  │  • Speaks intent in natural language
  │  • Receives feedback, errors, confirmations
  │  • Never validates, never executes
  │
  ▼
Dolphin / Semantic Normalizer (LLM)
  │  • Input: natural language + context (ZW/ZON)
  │  • Output: structured intent contract (JSON)
  │  • May enrich: style, mood, features, constraints
  │  • Must not: invent capabilities, bypass rules, mutate state
  │
  ▼
Intent Contract
  │  • Schema-validated JSON structure
  │  • Contains: intent_type, asset_family, constraints, metadata
  │  • Bound to registered capability signature
  │
  ▼
AP Gate / Authority Validator
  │  • Checks: actor tier, reality_mode, WORLD_RULES, resource limits
  │  • Decision: APPROVE / REJECT / ADAPT
  │  • If ADAPT: produces minimal delta, logs rationale
  │  • If REJECT: routes to Intent Shadow, no state mutation
  │
  ▼
Capability Registry
  │  • Maps approved intent → registered builder function
  │  • Validates signature match
  │  • Dispatches with structured args only
  │
  ▼
Builder Systems (Deterministic)
  │  • Receive: structured args, no natural language
  │  • Execute: terrain placement, mesh generation, registry update
  │  • Return: execution result or error
  │  • Never interpret, never infer, never propose
  │
  ▼
Godot / Blender / Trixel / Renderer
  │  • Render final artifact
  │  • Report visual state back to snapshot
```

---

## 5. Mutation Rules Matrix

| Actor | DRAFT | IMBUED | FINALIZED | DREAM | REPLAY |
|-------|-------|--------|-----------|-------|--------|
| User (Tier 3) | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ❌ Read-only |
| Dragon | ❌ Never | ❌ Never | ❌ Never | ❌ Never | ❌ Never |
| LLM / Dolphin | ❌ Never | ❌ Never | ❌ Never | ❌ Never | ❌ Never |
| AP Gate | ✅ Adapt only | ✅ Adapt only | ❌ Tier-3 required | ✅ Adapt only | ❌ Never |
| Builders | ✅ Execute approved | ✅ Execute approved | ✅ Execute approved (Tier-3) | ✅ Execute approved | ❌ Never |

**Hard Rules**:
1. A tier is necessary but not sufficient for mutation.
2. `REPLAY` blocks all mutation, regardless of tier.
3. `FINALIZED` requires Tier-3 for any change.
4. AI agents (Tier 1) cannot mutate `FINALIZED` under any circumstance.
5. Tier escalation is impossible from inside the actor.
6. Rejected commands go to Intent Shadow and must not mutate world state.
7. Governance must be deterministic: same inputs + same tier + same reality mode → same result.

---

## 6. Intent Contract Schema (Reference)

All LLM outputs must conform to this structure before AP validation:

```json
{
  "intent_type": "create_structure|modify_entity|trigger_event|query_state",
  "asset_family": "tower|character|prop|terrain|effect",
  "style": "gothic|organic|industrial|...",
  "mood": "ominous|peaceful|chaotic|...",
  "materials": ["black_stone", "iron"],
  "features": ["tall_profile", "pointed_arches", "spires"],
  "constraints": {
    "max_height": 100,
    "allowed_zones": ["wilderness", "ruins"],
    "prohibited_effects": ["fire", "explosion"]
  },
  "metadata": {
    "source_tier": 3,
    "reality_mode": "DRAFT",
    "llm_model": "dolphin-vX",
    "confidence": 0.92
  }
}
```

**Validation**: Schema enforcement occurs at AP Gate entry. Invalid contracts are rejected to Intent Shadow with diagnostic.

---

## 7. Violation Handling

| Violation Type | Detection Point | Response |
|---------------|-----------------|----------|
| LLM proposes state mutation | AP Gate schema check | Reject → Intent Shadow + audit log |
| Dragon attempts override | Authority validator | Block + Tier-3 alert |
| Builder receives natural language | Capability dispatch | Reject + builder-side assertion |
| AP Gate authors desire | Code review / invariant test | Fail build + doctrine violation report |
| User command bypasses gate | Runtime invariant | Panic + full traceback + state rollback |

**Intent Shadow**: All rejected intents are logged to `intent_shadow.py` with:
- Original proposal
- Rejection rationale
- Actor tier + reality mode
- Timestamp + trace ID
- No world state mutation occurs.

---

## 8. Testing Invariant

If a test conflicts with this doctrine, **the test is wrong**.

Tests must verify:
- LLM output is structured intent only, never executable code
- AP Gate rejects unauthorized mutations deterministically
- Builders receive only validated, structured args
- Dragon never bypasses validation
- User Tier-3 override always succeeds (in non-REPLAY modes)

---

## 9. References

- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md` — Tier definitions
- `godotengain/engainos/core/reality_mode.py` — Mutability modes
- `godotengain/engainos/core/intent_shadow.py` — Rejection logging
- `godotsim/protocol_envelope.py` — State consistency hashing
- `mettaext/docs/NARRATIVE_TO_GAME_PROOF.md` — Narrative as machine-readable authority

---

## 10. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-29 | Initial frozen doctrine | Tier-3 (User) |

---

> **Final Reminder**:  
> This repository is not just code. It is code plus lore, canon, protocol doctrine, and recovery history.  
> Work like a careful archivist-engineer: preserve first, classify before changing, respect authority, verify on the right port, never let convenience outrank canon.
```

---

✅ **Doctrine frozen.**  

This document is now the reference contract. No subsequent script, adapter, or integration should violate its boundaries.

**Next in build order**:  
2. `docs/schema/INTENT_CONTRACT_SCHEMA_v1.json` — Formal JSON Schema for Dolphin output  
3. `godotengain/engainos/core/ap_gate_hook.py` — AP validation entry point  
4. `godotengain/engainos/core/capability_registry.py` — Builder dispatch router  
5. `godotengain/engainos/core/intent_shadow.py` — Rejection logging (extend existing)  
6. `tests/integration/test_gothic_tower_flow.py` — End-to-end mock  

Shall I proceed to **Step 2: Intent Contract Schema**?
