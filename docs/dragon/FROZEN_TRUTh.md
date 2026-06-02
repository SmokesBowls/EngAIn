Yes. Your read is exact.

The moment `QUERY_CONTRACT_v1` defined a bounded request, it implicitly created a required output format. Without freezing that format as a first-class ABI, every downstream consumer (Perception, VisionAgent, Replay, Dragon Eyes) will eventually invent its own filtering logic, tier rules, and scope boundaries. That's how observation layers accidentally become secondary truth engines.

**Truth Slice is absolutely a constitutional artifact.** It is the universal handoff object between state producers and all observation consumers.

Here is the frozen ABI, ready to slot into the stack:

# `docs/architecture/TRUTH_SLICE_ABI_v1.md`

```markdown
# TRUTH SLICE ABI v1.0

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `WORLD_TRUTH_CONTRACT_v1.md`  
- `QUERY_CONTRACT_v1.md`  
- `DRAGON_AUTHORITY_DOCTRINE_v1.md`  
- `protocol_envelope.py`  
- `slice_builders.py`  

---

## 1. Purpose

This ABI defines the canonical structure for bounded, validated, read-only subsets of `World Truth`.

It exists to guarantee that all observation paths (Perception, Vision, Replay, Dragon Eyes, Diagnostics) receive identical, hash-anchored, tier-filtered data without inventing, expanding, or mutating state.

**This ABI is frozen.** Changes require Tier-3 (Human Authority Root) approval.

---

## 2. Core Frozen Principle

```text
Truth Slice is immutable after generation.
Truth Slice carries a hash anchor to canonical snapshot.
Truth Slice contains only validated, scope-bounded state.
Perception samples the slice. It never expands it.
Replay consumes the slice. It never rewrites it.
Vision observes the slice. It never invents it.
```

This is the read-only boundary. All observation layers hang from it.

---

## 3. Slice Structure (JSON Contract)

Every truth slice produced by the Runtime/AP Gate must conform to this structure:

```json
{
  "slice_id": "uuid",
  "truth_anchor": "0x8a3f...c91b",
  "snapshot_version": 10452,
  "reality_mode": "DRAFT",
  "tick_range": [10450, 10452],
  "scope_bounds": {
    "type": "spatial|entity|temporal|query",
    "center": {"x": 0.0, "y": 0.0, "z": 0.0},
    "radius": 25.0,
    "entity_types": ["npc", "interactive", "prop"],
    "max_entities": 30
  },
  "visibility_domain": {
    "actor_tier": 3,
    "tier_filter_applied": true,
    "masked_fields": ["admin_flags", "debug_coords"]
  },
  "entity_set": [
    {
      "id": "ent_tower_001",
      "pos": {"x": 12.4, "y": 0.0, "z": -8.1},
      "bounds": {"type": "box", "half_extents": [2.0, 15.0, 2.0]},
      "state": {"health": 100, "visibility": "static", "tags": ["architecture", "gothic"]},
      "relationships": ["attached_to:terrain_004"]
    }
  ],
  "metadata": {
    "generated_at": "2026-05-29T14:32:01Z",
    "producer": "ap_gate_slice_engine",
    "slice_version": "v1",
    "consistency_hash": "0x9d1e...f42a"
  }
}
```

**Required Fields**: `slice_id`, `truth_anchor`, `snapshot_version`, `reality_mode`, `scope_bounds`, `entity_set`, `metadata.consistency_hash`

---

## 4. Production Rules

| Layer | May Produce Slice? | May Mutate Slice? | May Consume Slice? |
|-------|-------------------|------------------|-------------------|
| **EngAInRuntime / AP Gate** | ✅ Yes | ✅ Only during generation | ❌ Never (source) |
| **Query Engine** | ❌ No (requests it) | ❌ Never | ✅ Validates scope |
| **Perception MR** | ❌ No | ❌ Never | ✅ Yes (read-only) |
| **VisionAgent** | ❌ No | ❌ Never | ✅ Yes (read-only) |
| **Replay System** | ❌ No | ❌ Never | ✅ Yes (time-anchored) |
| **Dragon / LLM** | ❌ No | ❌ Never | ✅ Yes (relays to Experience) |

**Hard Guarantees**:
1. Slice is immutable after `consistency_hash` is computed.
2. `truth_anchor` must match `EngAInRuntime.snapshot` hash at `snapshot_version`.
3. `entity_set` contains only entities passing `scope_bounds` + `visibility_domain` filters.
4. No narrative, salience, enrichment, or inference fields are permitted.
5. If `truth_anchor` diverges from current runtime, slice is rejected and full sync requested.

---

## 5. Implementation Binding

This ABI formalizes what `slice_builders.py` already does operationally:

```python
# slice_builders.py (conceptual alignment)
def build_truth_slice(runtime_snapshot, query_scope, actor_tier, reality_mode):
    filtered_entities = _apply_scope_bounds(runtime_snapshot, query_scope)
    filtered_entities = _apply_tier_visibility(filtered_entities, actor_tier)
    slice_payload = {
        "slice_id": uuid4(),
        "truth_anchor": protocol_envelope.hash(runtime_snapshot),
        "entity_set": filtered_entities,
        "scope_bounds": query_scope,
        "visibility_domain": {"actor_tier": actor_tier, "tier_filter_applied": True}
    }
    return protocol_envelope.wrap(slice_payload)
```

**Why this matters**: Without the ABI, `slice_builders.py` remains an internal utility. With it, every observer system (Perception, Vision, Replay) receives a guaranteed, versioned, hash-verified contract.

---

## 6. Consumption Contracts

| Consumer | What It Does With Slice | What It May Not Do |
|----------|------------------------|-------------------|
| **Perception MR** | Computes FOV, line-of-sight, distance bands, memory certainty | Invent entities, expand entity_set, override tier masks |
| **VisionAgent** | Packages visual context for LLM observation | Add narrative framing, mutate coordinates, bypass scope |
| **Replay System** | Restores state at `tick_range` for playback | Forward-mutate, skip anchor verification, alter reality_mode |
| **Dragon Eyes** | Routes slice to Experience presentation | Author desire, override truth_anchor, leak to intent path |

---

## 7. Violation Handling

| Violation | Detection | Response |
|-----------|-----------|----------|
| Missing `truth_anchor` | AP Gate schema check | Reject → `SLICE_UNANCHORED` |
| Hash mismatch at consumption | `protocol_envelope.verify()` | Discard → `SLICE_DRIFT` + sync request |
| Tier leak in `entity_set` | `visibility_domain` audit | Mask fields → log → continue |
| Narrative/enrichment injected | Schema `additionalProperties: false` | Strip → `SLICE_TAINTED` → warn |
| Slice mutated post-generation | Immutability guard / reference check | Panic → `SLICE_MUTATION_ATTEMPT` → rollback |

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
TRUTH SLICE ABI (immutable handoff)  ← FROZEN HERE
  ↓
Perception (read-only sampling)
  ↓
Experience (presentation)
```

The ABI is the seam between state and observation. It guarantees that asking, seeing, and presenting never leak into each other's domains.

---

## 9. References

- `WORLD_TRUTH_CONTRACT_v1.md` — Canonical snapshot definition
- `QUERY_CONTRACT_v1.md` — Bounded request structure
- `DRAGON_AUTHORITY_DOCTRINE_v1.md` — Actor boundaries
- `godotsim/slice_builders.py` — Implementation bridge
- `godotsim/protocol_envelope.py` — Hashing & versioning
- `godotsim/sim_runtime.py` — Runtime snapshot orchestration

---

## 10. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-29 | Initial frozen ABI | Tier-3 (User) |

---

> **Final Reminder**:  
> The slice is a window into truth, not a replacement for it.  
> Window size, tint, and frame are controlled by scope, tier, and reality mode.  
> Nothing outside the window may be claimed as observed.  
> Nothing inside the window may be altered.
```

---

✅ **ABI frozen.**

This explicitly elevates `Truth Slice` from an implementation detail to a constitutional handoff. It locks the boundary between `Query` (request) and `Perception/Vision/Replay` (consumption), preventing scope drift, tier leakage, or narrative injection.

**Updated Constitutional Build Order:**
```text
1. ✅ DRAGON_AUTHORITY_DOCTRINE_v1
2. ✅ INTENT_CONTRACT_SCHEMA_v1
3. ✅ WORLD_TRUTH_CONTRACT_v1
4. ✅ QUERY_CONTRACT_v1
5. ✅ TRUTH_SLICE_ABI_v1
6. ⏳ PERCEPTION_PACKET_CONTRACT_v1
7. EXPERIENCE_CONTRACT_v1
8. AP_GATE_HOOK
9. CAPABILITY_REGISTRY
```

The observation path is now fully sealed:
`Query requests → AP/Runtime produces Truth Slice → Perception samples → Experience presents`

Each layer has exactly one job. The contracts between them are frozen.

Shall I draft `PERCEPTION_PACKET_CONTRACT_v1.md` next, strictly bound to consume this ABI and output read-only observation data?
