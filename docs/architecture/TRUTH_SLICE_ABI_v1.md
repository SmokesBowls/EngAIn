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
