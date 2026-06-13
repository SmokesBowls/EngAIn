# `docs/architecture/QUERY_CONTRACT_v1.md`

```markdown
# QUERY CONTRACT v1.0

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `DRAGON_AUTHORITY_DOCTRINE_v1.md`  
- `INTENT_CONTRACT_SCHEMA_v1.json`  
- `WORLD_TRUTH_CONTRACT_v1.md`  
- `PERCEPTION_PACKET_CONTRACT_v1.md` (pending)  
- `reality_mode.py`  
- `protocol_envelope.py`  

---

## 1. Purpose

This document defines the non-negotiable structure for all read-only requests against the EngAIn simulated world.

It exists to prevent unbounded state dumps, perception invention, tier leakage, and replay escape by governing exactly what slice of `World Truth` may be requested, by whom, and under what constraints.

**This contract is frozen.** Changes require Tier-3 (Human Authority Root) approval and a new versioned document.

---

## 2. Core Frozen Principle

```text
Query does not observe.
Query requests a bounded truth slice.

Perception does not request.
Perception samples the approved slice.
```

This boundary is absolute. Query defines scope. Truth provides data. Perception renders observation. None may cross into another's domain.

---

## 3. Allowed Query Shapes

| Query Type | Purpose | Required Scope | Typical Limits |
|------------|---------|----------------|----------------|
| `look` | Immediate environmental awareness | `entity_id` or `actor_origin` | FOV, range, max_visible_entities |
| `examine` | Deep entity/prop inspection | `target_entity_id` | detail_depth, lore_access_level |
| `status` | Actor/system state summary | `actor_id` or `system` | metrics_filter, max_history_ticks |
| `scan_radius` | Spatial proximity sweep | `center_pos` + `radius` | max_entities, terrain_only, entity_types |
| `query_history` | ZON memory / timeline recall | `entity_id` or `scene_id` | tick_range, confidence_threshold |
| `query_inventory` | Held/worn/contained items | `actor_id` or `container_id` | weight_only, equipped_only, category_filter |
| `query_relationship` | Social/faction/ownership ties | `source_id` + `target_type` | max_depth, active_only, tier_visibility |
| `query_state` | Raw structural inspection | `path` or `domain` | read_only_domains, hash_verify |

**Hard Rule**: Any query type not listed here is rejected to `intent_shadow.py` with `QUERY_TYPE_NOT_REGISTERED`.

---

## 4. Query Contract Structure

All queries must conform to this JSON structure before AP validation:

```json
{
  "query_type": "look|examine|status|scan_radius|query_history|query_inventory|query_relationship|query_state",
  "target": {
    "type": "entity|actor|scene|coordinate|domain",
    "id": "string|null",
    "coordinate": {"x": 0.0, "y": 0.0, "z": 0.0}
  },
  "scope": {
    "radius": 10.0,
    "max_entities": 50,
    "depth": 2,
    "tick_range": [10450, 10460],
    "filters": ["npc", "interactive", "recent_activity"]
  },
  "authority": {
    "actor_tier": 3,
    "reality_mode": "DRAFT",
    "truth_anchor": "0x8a3f...c91b"
  },
  "limits": {
    "max_bytes": 4096,
    "allow_narrative_hints": true,
    "suppress_system_entities": true
  },
  "metadata": {
    "trace_id": "uuid",
    "timestamp": "ISO8601",
    "query_version": "v1"
  }
}
```

**Required Fields**: `query_type`, `authority.actor_tier`, `authority.reality_mode`, `authority.truth_anchor`, `scope`, `metadata.trace_id`, `metadata.timestamp`

---

## 5. Enforcement Rules

| Rule | Enforcement Mechanism | Violation Response |
|------|----------------------|-------------------|
| **No unbounded snapshot dump** | `scope.max_entities`, `limits.max_bytes`, `query_type` caps | Reject → `UNBOUNDED_QUERY_SCOPE` |
| **No hidden mutation** | AP Gate validates `intent_type` is read-only; query contract has no mutation fields | Reject → `MUTATION_IN_QUERY` |
| **No perception invention** | Query returns only canonical truth fields; no narrative framing or salience weighting | Strip → `PERCEPTION_FIELDS_REMOVED` |
| **No tier leakage** | `authority.actor_tier` filters visible entities by visibility rules; high-tier secrets masked for lower tiers | Mask → `TIER_VISIBILITY_FILTER` |
| **No replay escape** | `REPLAY` mode locks `tick_range` to anchor window; forward queries blocked | Reject → `REPLAY_TEMPORAL_LOCK` |
| **Truth hash required** | `authority.truth_anchor` must match current `protocol_envelope` hash; stale hash triggers sync | Reject → `TRUTH_HASH_MISMATCH` |
| **Scope required** | Every query must define at least one boundary (`radius`, `max_entities`, `tick_range`, or `target`) | Reject → `MISSING_SCOPE_BOUNDARY` |

---

## 6. Truth Slice Boundary

Query does not access `EngAInRuntime.snapshot` directly.

It requests a **truth slice** validated by AP Gate:

```text
Query Contract
        ↓
AP Gate (tier + reality_mode + scope validation)
        ↓
Truth Slice Request
        ↓
Runtime Snapshot + Protocol Hash
        ↓
Bounded Truth Slice (read-only, hash-verified)
        ↓
Perception Adapter (samples slice, applies FOV/line-of-sight)
        ↓
Perception Packet (experience-ready)
```

**Slice Properties**:
- Immutable after generation
- Carries `truth_anchor` hash for verification
- Contains only fields permitted by `query_type` + `scope` + `tier_visibility`
- Never includes narrative framing, salience weights, or Dragon emphasis
- Divergence from current snapshot triggers `TRUTH_DRIFT_CORRECTION`, not state mutation

---

## 7. Violation Handling

| Violation | Detection Point | Response |
|-----------|----------------|----------|
| Unbounded scope | AP Gate schema check | Reject → Intent Shadow |
| Missing truth anchor | Validation hook | Reject + request snapshot sync |
| Tier leakage attempt | Slice visibility filter | Mask fields + log |
| Perception fields in query | Contract parser | Strip + warn |
| REPLAY temporal escape | `reality_mode.py` gate | Block + rollback to anchor |
| Query mutation attempt | Intent/Query type mismatch | Reject + invariant panic |

**Testing Invariant**: If a test requires unbounded state access, query-driven mutation, or perception injection at the query layer, **the test is wrong**.

---

## 8. Relationship to Downstream Layers

| Layer | Receives From Query | What It Adds |
|-------|---------------------|--------------|
| **World Truth** | Bounded slice request | Canonical data + hash |
| **Perception** | Approved truth slice | FOV, line-of-sight, memory certainty, salience mapping |
| **Experience** | Perception packet | Narrative framing, Dragon emphasis, UI rendering |
| **Dragon** | Query proposal + Experience result | Relay only; no scope override or truth definition |

**Boundary Guarantee**: Query never sees salience, Dragon emphasis, or narrative framing. Perception never sees raw unbounded truth. Experience never sees query scope.

---

## 9. References

- `WORLD_TRUTH_CONTRACT_v1.md` — Canonical state definition
- `DRAGON_AUTHORITY_DOCTRINE_v1.md` — Actor boundaries
- `INTENT_CONTRACT_SCHEMA_v1.json` — Mutation proposal structure
- `protocol_envelope.py` — State hashing & versioning
- `reality_mode.py` — Mutability & replay locks
- `ap_engine.py` — Tier + scope validation

---

## 10. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-29 | Initial frozen contract | Tier-3 (User) |

---

> **Final Reminder**:  
> Query asks. Truth answers. Perception observes. Experience presents.  
> Never let scope, tier, or replay mode bypass the truth anchor.  
> A bounded request is a safe system. An unbounded one is a leak.
```

---

✅ **Contract frozen.**

`QUERY_CONTRACT_v1.md` now explicitly governs the read path before perception ever touches the world. It enforces bounded scope, truth anchoring, tier visibility, and replay locks. It cleanly separates **request** from **observation**, preventing the architectural drift you correctly identified.

**Updated Build Order (confirmed):**
```text
1. ✅ DRAGON_AUTHORITY_DOCTRINE_v1
2. ✅ INTENT_CONTRACT_SCHEMA_v1
3. ✅ WORLD_TRUTH_CONTRACT_v1
4. ✅ QUERY_CONTRACT_v1
5. ⏳ PERCEPTION_PACKET_CONTRACT_v1
6. EXPERIENCE_CONTRACT_v1
7. AP_GATE_HOOK
8. CAPABILITY_REGISTRY
```

The observation path is now fully structured:
```
User asks → Query bounds scope → AP validates → Truth provides slice → Perception samples → Experience presents
```

Shall I draft `PERCEPTION_PACKET_CONTRACT_v1.md` next, strictly bound to this query-approved truth slice?
