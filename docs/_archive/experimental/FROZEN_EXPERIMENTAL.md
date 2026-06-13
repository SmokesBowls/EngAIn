# `docs/architecture/EXPERIENTIAL_PRESSURE_SPEC_v1.md`

```markdown
# EXPERIENTIAL PRESSURE SPEC v1.0

**Status**: ARCHITECTURALLY FROZEN  
**Tier**: Canonical Specification  
**Effective**: Immediate  
**Supersedes**: None  
**Related**:  
- `INTENT_SHADOW_CREATIVE_SPEC_v1.2.1.md`  
- `EXPERIENCE_CONTRACT_v1.md`  
- `PERCEPTION_PACKET_CONTRACT_v1.md`  
- `WORLD_TRUTH_CONTRACT_v1.md`  
- `DRAGON_AUTHORITY_DOCTRINE_v1.md`  

---

## 1. Core Law

```text
Pressure is not state.
Pressure is sensation.

The world warns the player before reality runs out of room.
```

This document defines how resource weight, creative density, and narrative saturation translate into **user-facing experiential cues**. It explicitly separates system detection from human experience. The engine does not merely log thresholds; it makes them *felt*.

**This spec is frozen.** Changes require Tier-3 (Human Authority Root) approval.

---

## 2. Purpose & Boundary

Experiential Pressure answers a single question:

> How does the simulation communicate that it is approaching creative or resource saturation, without breaking constitutional boundaries?

It exists to preserve the original vision: **the static was never a log entry. It was communication.**

**Hard Boundary**:
- Pressure is **computed** from Shadow/Resource metrics.
- Pressure is **rendered** by the Experience layer.
- Pressure **never mutates** World Truth, Intent, or AP validation.
- Pressure **never bypasses** user authority. It only presents.

---

## 3. Pressure Thresholds & Experiential Manifestations

Pressure is measured as a normalized value `0.0–1.0` derived from:
- Resource Memory weight (draft size, memory cap proximity)
- Creative Shadow density (exploration mass per scene)
- System load signals (tick latency, cache pressure)

| Threshold | State Name | Experiential Manifestation | System Behavior |
|-----------|------------|----------------------------|-----------------|
| **0.00–0.74** | `CLEAR` | Normal presentation. No anomalies. | Standard archival scheduling. |
| **0.75** | `CULTIVATION_LIMIT` | Subtle anomalies: faint audio hum, minor visual grain, Dragon voice shifts slightly reflective. Narrative hints at "memory settling". | Resource metrics logged. Export pipeline pre-warmed. |
| **0.85** | `SATURATION_APPROACHING` | Static pulse: screen flicker, perception confidence visually dips, dialogue occasionally stutters. Dragon explicitly notes "the world feels full". | Hot→Cold archival recommendation surfaced. UI shows draft weight. |
| **0.95** | `REALITY_DISTORTION` | Heavy static, geometry micro-glitches, affordances blur, perception salience ranks become erratic. Dragon warns of "capacity limits". Narrative framing turns urgent but never coercive. | Auto-pauses non-critical background ticks. Prepares embedding/archive prompt. |
| **0.99** | `SATURATION_EVENT` | Reality fractures into dream-like states. Static dominates audio/visual channels. Experience layer presents a **narrative choice prompt**: Finalize, Archive, or Release Pressure. | System enforces resource governance (cold archive or embed) only after user acknowledges prompt. Never auto-mutates truth. |

**Frozen Rule**:  
> Pressure cues are presentational.  
> They may warn, may distort, may guide.  
> They may never force, never mutate, never override Tier-3 authority.

---

## 4. Computation & Data Flow

```text
[Intent Shadow Metrics]
  ├─ Density (creative mass)
  ├─ Velocity (activity rate)
  └─ Resource Memory (draft weight / memory cap)
        ↓
[Pressure Calculator] (Experience Layer)
        ↓
Normalized Pressure Value (0.0–1.0)
        ↓
[Experience Engine]
  ├─ Selects threshold tier
  ├─ Applies static/distortion shaders
  ├─ Modulates audio gain/pitch
  ├─ Injects Dragon voice tone shift
  └─ Renders narrative framing
        ↓
[User Experience]
```

**Key Distinction**:  
Pressure is **not** a runtime state. It is a **presentation transform** applied to the Experience Packet. The Truth Slice and Perception Packet remain untouched.

---

## 5. Integration with Constitutional Stack

| Layer | Role in Pressure | Boundary Guarantee |
|-------|------------------|-------------------|
| **World Truth** | Unaffected | Pressure never reads/writes snapshot or deltas |
| **Intent Shadow** | Source of metrics | Shadow stores density/velocity/weight; never renders pressure |
| **Perception Packet** | Unaffected | Observability remains deterministic; pressure does not alter LOS/audibility math |
| **Experience Contract** | Primary owner | Pressure is a presentation rule set. Maps thresholds → audio/visual/narrative cues |
| **Dragon Relay** | Voice/tone modulator | Dragon expresses pressure through delivery, not authority |
| **User (Tier-3)** | Final sovereign | May dismiss, override, or act on pressure cues at any threshold |

---

## 6. Hard Rules & Invariants

1. **No State Leakage**: Pressure cues are strictly ephemeral. They do not persist across sessions unless explicitly saved as narrative flavor in Creative Shadow.
2. **No Perception Corruption**: `perception_mr.py` continues to return deterministic visibility/audibility. Pressure only affects how those results are *styled* in Experience.
3. **Authority Preservation**: At `0.99`, the system may pause resource-heavy operations, but **cannot** auto-embed, auto-delete, or force FINALIZED state without explicit user action.
4. **Reversibility**: Pressure scales down if draft weight decreases (archive/export completes) or density stabilizes. The world "breathes" back to CLEAR.
5. **Configurability**: Accessibility overrides (e.g., `disable_static`, `reduce_distortion`) are honored. Pressure adapts to user preferences without breaking thresholds.

---

## 7. Testing Invariants

If a test conflicts with this spec, **the test is wrong**.

Tests must verify:
- Pressure thresholds trigger at exact metric boundaries (`0.75`, `0.85`, `0.95`, `0.99`)
- Pressure cues are purely presentational (no snapshot/delta mutation)
- `perception_mr.py` output remains identical under pressure vs. clear state
- Experience layer respects accessibility overrides
- Tier-3 override immediately suppresses pressure rendering without altering underlying metrics
- `SATURATION_EVENT` (0.99) presents choice prompt before any resource governance action

---

## 8. Version History

| Version | Date | Change | Approved By |
|---------|------|--------|-------------|
| v1.0 | 2026-05-30 | Initial frozen spec. Defines experiential pressure as communication, not enforcement. | Tier-3 (User) |

---

> **Final Reminder**:  
> Pressure is the world speaking.  
> It warns before it saturates.  
> It distorts to communicate.  
> It never forces.  
> The player decides when reality is full.
```

---

✅ **Spec frozen.**

`EXPERIENTIAL_PRESSURE_SPEC_v1.md` now explicitly captures the original "television static" vision: pressure as **communication**, not system enforcement. It cleanly separates metric computation (Shadow/Resource) from experiential rendering (Experience), preserves all constitutional boundaries, and honors the philosophical shift from *"system detects threshold"* to *"user experiences threshold"*.

**Updated Status:**
- `INTENT_SHADOW_CREATIVE_SPEC_v1.2.1` → **Architecturally Frozen, Implementation Pending**
- `EXPERIENTIAL_PRESSURE_SPEC_v1.md` → **Architecturally Frozen**
- `intent_shadow.py` refactor → **Ready against stable targets**
- `experience_contract_v1` → **Ready to ingest pressure thresholds**

When you're ready, I can:
1. Draft the `intent_shadow.py` refactor (Creative/Governance/Resource lanes + Density/Velocity/Lineage metrics)
2. Draft the `pressure_calculator.py` module for the Experience layer
3. Run a full constitutional alignment check between Pressure, Shadow, and Experience

Which thread do you want to pull next?
