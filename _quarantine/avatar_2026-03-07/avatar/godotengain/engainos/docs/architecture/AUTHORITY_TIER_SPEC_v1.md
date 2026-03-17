# AUTHORITY TIER SPEC v1 — FROZEN

**Status:** LOCKED  
**Scope:** Core / Engine-Agnostic  
**Applies to:** Gateway → Empire → Kernel → Memory

---

## 1. Purpose

Define who may mutate state, when, and under what conditions — independent of renderer, engine, or client.  
This spec is normative. Tests must conform to it.

---

## 2. Authority Tiers (Immutable)

| Tier | Actor Type              | Description                              |
|------|-------------------------|------------------------------------------|
| 0    | System                  | Internal runtime (replay, validation)    |
| 1    | AI Agent                | Trae, NPC AI — autonomous but constrained |
| 2    | Human Operator (Limited)| Assisted control, non-final              |
| 3    | Human Authority (Root)  | Canonical override                       |

**Rule:** A tier is *necessary but not sufficient* for mutation.

---

## 3. Reality Modes (Immutable)

| Mode     | Mutability | Canonical? | Enforcement                        |
|----------|-----------:|-----------:|------------------------------------|
| DRAFT    | Yes        | No         | Minimal                            |
| IMBUED   | Yes        | No         | AP enforced                        |
| FINALIZED| Restricted | Yes        | Hard AP + Tier gate                |
| DREAM    | Sandbox    | No         | Symbolic only, discardable         |
| REPLAY   | No         | N/A        | Read-only, absolute                |

---

## 4. Authority × Reality Matrix (Law)

**Mutation Permission Matrix**

- ✅ = mutation allowed (subject to AP etc.)  
- ❌ = mutation forbidden (gateway must reject)

| Mode ↓ / Tier → | T1 (AI) | T2 (Human) | T3 (Root) |
|-----------------|---------|------------|-----------|
| DRAFT           | ✅      | ✅         | ✅        |
| IMBUED          | ✅      | ✅         | ✅        |
| FINALIZED       | ❌      | ❌         | ✅        |
| DREAM           | ✅*     | ✅*        | ✅*       |
| REPLAY          | ❌      | ❌         | ❌        |

\* DREAM mutations are non-canonical and discardable.

---

## 5. Gateway Enforcement Rules (Hard)

1. **REPLAY blocks everything**
   - No exceptions.  
   - No shadow → canon leakage.  

2. **FINALIZED requires Tier 3**
   - Tier 1/2 attempts are rejected.  
   - Rejections are recorded in Intent Shadow.  

3. **Tier escalation is impossible**
   - No actor may self-promote.  
   - Tier is injected externally (context).  

4. **Success path**
   - Allowed → routed to Empire → Kernel.  
   - Canonical only if mode permits.  

5. **Failure path**
   - Rejected → Intent Shadow.  
   - No world mutation.

---

## 6. Memory Guarantees

| Outcome                  | Stored Where          |
|--------------------------|----------------------|
| Rejected command         | Intent Shadow        |
| Accepted, non-canon      | History (non-canon)  |
| Accepted in FINALIZED    | Canonical History    |
| DREAM execution          | Sandbox history only |
| REPLAY                   | No writes            |

---

## 7. Determinism Constraint

Authority enforcement must not introduce nondeterminism.

Same inputs + same tier + same reality mode → identical results.  
Governance is a pure function of context, not time.

---

## 8. Test Law (Binding)

❌ Tests may NOT assume:

- AI can mutate FINALIZED.  
- Tier bypass.  
- Replay mutation.  

✅ Tests MUST assert:

- Correct rejection paths.  
- Correct shadow recording.  
- Correct canonical gating.  

If a test fails this spec, the test is wrong.

---

## 9. Versioning

**Authority Tier Spec v1 — FROZEN**

Backward-incompatible changes require:

- `v2` namespace.  
- Migration tests.  
- Explicit opt-in.

---

## 10. Final Invariant (Non-Negotiable)

Authority is contextual, not intrinsic.  
Reality mode outranks intent.  
Canon outranks convenience.
