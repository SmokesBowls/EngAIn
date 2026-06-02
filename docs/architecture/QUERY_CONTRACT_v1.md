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
