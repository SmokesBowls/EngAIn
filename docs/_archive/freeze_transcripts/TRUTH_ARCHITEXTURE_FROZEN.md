# `docs/architecture/WORLD_TRUTH_CONTRACT_v1.md`

```markdown
# WORLD TRUTH CONTRACT v1.0

**Status**: FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `DRAGON_AUTHORITY_DOCTRINE_v1.md`  
- `INTENT_CONTRACT_SCHEMA_v1.json`  
- `AUTHORITY_TIER_SPEC_v1.md`  
- `reality_mode.py`  
- `protocol_envelope.py`  
- `intent_shadow.py`  

---

## 1. Purpose

This document defines the singular, authoritative state of the EngAIn simulated world.

It consolidates all existing truth authorities into a single constitutional statement to prevent architectural drift into multi-truth, observer-defined, or renderer-mutated reality.

**This contract is frozen.** Changes require Tier-3 (Human Authority Root) approval and a new versioned document.

---

## 2. Core Frozen Principle

```text
Truth is singular, deterministic, and precedes observation.
Perception samples truth. Perception does not create truth.
Experience presents truth. Experience does not redefine truth.
```

This is the invariant. All simulation, perception, rendering, and narrative systems hang from it.

---

## 3. The Truth Stack

World truth is not a single value. It is a composite of validated, interlocking authorities. Each layer owns a specific dimension of reality.

| Truth Dimension | Definition | Code Artifact / Contract |
|----------------|------------|--------------------------|
| **Runtime Truth** | Live simulation SSOT at tick `N` | `EngAInRuntime.snapshot` (`sim_runtime.py`) |
| **Spatial Truth** | Canonical coordinates, transforms, adjacency | `Coordinate ABI` + `spatial3d_mr.py` |
| **Terrain/Substrate Truth** | Ground plane, elevation, biome rules, passability | `WorldField` contracts + terrain kernels |
| **Identity Truth** | Entity lifecycles, IDs, relationships, persistence | Entity Registry + `ZON` memory fabric |
| **Canon Truth** | What has survived promotion to authoritative narrative | Promotion Pipeline + `FINALIZED` reality mode |
| **Mutation Permission Truth** | Who may change truth, under what conditions | `AUTHORITY_TIER_SPEC_v1.md` + `ap_engine.py` |
| **Proposal Truth** | Structured intent before validation | `INTENT_CONTRACT_SCHEMA_v1.json` |

**Composite Rule**: World truth = intersection of all validated layers above. If any layer is inconsistent, state mutation halts until reconciliation.

---

## 4. Truth Invariants

1. **Single Source**: `EngAInRuntime.snapshot` is the only writable simulation state at tick `N`.
2. **Immutable Between Ticks**: Truth does not change mid-tick. Deltas are collected, validated, then applied atomically.
3. **Deterministic Evolution**: Same inputs + same tier + same reality mode + same seed → identical next truth.
4. **Protocol Enforcement**: Every truth snapshot is wrapped, versioned, and hashed via `protocol_envelope.py`. Hash mismatch = state corruption.
5. **No Observer Dependency**: Truth exists independently of Dragon, LLM, VisionAgent, renderer, or client connection state.
6. **Delta-Only Mutation**: Truth is never overwritten. It evolves through validated deltas only.
7. **Rejection Isolation**: Invalid proposals route to `intent_shadow.py`. They never touch truth.

---

## 5. Truth vs. Observation Boundary

| Layer | May Read Truth? | May Write Truth? | May Define Truth? |
|-------|----------------|------------------|-------------------|
| **User (Tier 3)** | ✅ Full | ✅ Via validated deltas | ✅ (Root override) |
| **Dragon / Relay** | ✅ Via AP-gated queries | ❌ Never | ❌ Never |
| **LLM / Dolphin** | ✅ Via enriched context | ❌ Never | ❌ Never |
| **Perception Layer** | ✅ Read-only sampling | ❌ Never | ❌ Never |
| **VisionAgent** | ✅ Snapshot/frame input | ❌ Never | ❌ Never |
| **Renderers (Godot/UPBGE)** | ✅ Snapshot / RenderPlan | ❌ Never | ❌ Never |
| **MR Kernels** | ✅ Immutable slice input | ✅ Via accepted deltas only | ❌ Never (math only) |

**Hard Rule**: If perception, rendering, or client state diverges from truth, the divergence is treated as a presentation bug, not a world update.

---

## 6. Validation & Enforcement Architecture

Truth is protected by a multi-layer gate system:

```text
Intent Contract
        ↓
AP Gate (Tier + Reality Mode + World Rules)
        ↓
MR Kernels (Pure Functional Slices)
        ↓
Delta Validation + Protocol Hashing
        ↓
EngAInRuntime.snapshot (Atomic Apply)
        ↓
World Truth (vN, hash: 0x...)
```

- **AP Gate**: Validates actor tier, reality mode, and domain rules before delta acceptance.
- **Slice Protection**: `slice_builders.py` provides read-only views to kernels. Direct mutation throws `KernelContractError`.
- **Protocol Envelope**: Wraps truth with version, timestamp, and stable hash. Clients verify before trusting.
- **Intent Shadow**: All rejected deltas are logged. Truth remains untouched.

---

## 7. Relationship to Perception & Experience

This contract explicitly defines the downstream boundary:

```text
World Truth (vN)
        ↓
Perception Packet (read-only sampling, salience, affordances)
        ↓
Experience Presentation (narrative framing, audio/visual rendering)
```

**Perception Rules**:
- Must derive exclusively from validated truth.
- Must never invent entities, coordinates, or relationships.
- Must carry metadata linking back to truth version/hash.
- Divergence from truth triggers correction, not state mutation.

**Experience Rules**:
- Is a presentation layer, not a state layer.
- May emphasize, suppress, or stylize truth for UX/narrative pacing.
- Must never feed back into truth without passing through Intent → AP → Validation pipeline.

---

## 8. Violation Handling

| Violation Type | Detection Point | Response |
|---------------|-----------------|----------|
| Perception attempts state mutation | AP Gate / Slice guard | Reject → Intent Shadow + audit log |
| Client/renderer overrides truth | Protocol hash check | Discard packet + request full sync |
| MR kernel mutates in-place | Slice invariant test | Panic + state rollback + trace dump |
| Truth hash mismatch across ticks | Protocol envelope verify | Halt simulation → diagnostic → reload anchor |
| AP Gate bypassed by adapter | Import boundary / invariant test | Fail build + doctrine violation report |

**Testing Invariant**: If a test requires perception to write state or truth to depend on observation, **the test is wrong**.

---

## 9. References

- `godotsim/sim_runtime.py` — Runtime snapshot orchestration
- `godotsim/protocol_envelope.py` — State hashing & versioning
- `godotsim/slice_builders.py` — Read-only kernel views
- `godotengain/engainos/core/ap_engine.py` — Authority validation
- `godotengain/engainos/core/reality_mode.py` — Mutability modes
- `godotengain/engainos/core/intent_shadow.py` — Rejection isolation
- `docs/architecture/AUTHORITY_TIER_SPEC_v1.md` — Tier definitions
- `docs/schema/INTENT_CONTRACT_SCHEMA_v1.json` — Proposal structure
- `DRAGON_AUTHORITY_DOCTRINE_v1.md` — Actor boundaries

---

## 10. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-29 | Initial frozen contract | Tier-3 (User) |

---

> **Final Reminder**:  
> Truth is not negotiated. It is computed, validated, hashed, and persisted.  
> Observation samples it. Experience presents it. Authority governs its mutation.  
> Never let convenience, rendering, or narrative framing outrank canonical state.
```

---

✅ **Contract frozen.**

This document explicitly consolidates the scattered truth authorities into a single constitutional boundary. It positions `World Truth` as the immutable center that `Perception` samples and `Experience` presents, but never defines.

**Updated Build Order (confirmed):**
```text
1. ✅ DRAGON_AUTHORITY_DOCTRINE_v1
2. ✅ INTENT_CONTRACT_SCHEMA_v1
3. ✅ WORLD_TRUTH_CONTRACT_v1
4. ⏳ PERCEPTION_PACKET_CONTRACT_v1
5. AP_GATE_HOOK
6. CAPABILITY_REGISTRY
```

The path is now clean. Perception can only exist as a read-only projection of this truth. Experience can only exist as a presentation of perception. Nothing upstream is allowed to leak downward.

Shall I draft `PERCEPTION_PACKET_CONTRACT_v1.md` now, strictly bound to this truth contract?
