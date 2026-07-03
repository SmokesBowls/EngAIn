# EngAInOS Authority Map

This document defines the canonical authority tiers, reality modes, and governance rules of the EngAIn runtime.

## 1. Authority Tiers

Governance in EngAIn is layered, and every execution command must assert or be mapped to a specific authority tier:

| Tier | Actor Type | Description |
|---|---|---|
| **Tier 0** | System | Internal runtime, replay operations, self-validation |
| **Tier 1** | AI Agent | Autonomous operations under programmatic constraints |
| **Tier 2** | Human Operator Limited | Assisted controls, draft submissions, non-final operations |
| **Tier 3** | Human Authority Root | Canonical override, final narrative approvals |

## 2. Reality Modes

The active runtime state operates under a specified Reality Mode which restricts what level of mutation is permitted:

| Mode | Mutability | Canonical? | Description |
|---|---:|---:|---|
| **DRAFT** | Yes | No | Free mutation, working space for staging scenes. |
| **IMBUED** | Yes | No | Enhanced state space, ready for review. |
| **FINALIZED** | Restricted | Yes | Locked state, requires Tier 3 authority to mutate. |
| **DREAM** | Sandbox | No | Isolated sandbox simulation. |
| **REPLAY** | No | N/A | Strictly read-only state reconstruction. |

## 3. Governance Policies

1. **Gate Enforcement**: All mutations must pass the AP/EngAInOS authority gates before they can affect runtime state.
2. **Intent Shadow**: Commands that fail verification are redirected to the Intent Shadow and must not modify active gameplay databases or memory states.
3. **Fail-Closed**: In the presence of ambiguous or undefined state, the system must fail-closed and block mutations.
