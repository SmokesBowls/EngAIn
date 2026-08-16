I hear the **Sign-In at the Door**.

You are not the law. You are not the permission slip. You do not decide who is *allowed*. You decide who is *here*. You are the difference between a name on a list and a hand actually raised in the room right now.

Here is your formalized contract.

---

# PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md

## 1. Purpose

Define a live-presence record for external agent providers (Hermes, and later Claude Code, Qwen, Antigravity, or any other body/tool) that is **separate from** `agent_gateway.py`'s authority policy. This contract answers one question only:

> Is a specific instance of an already-authorized agent actually reachable right now, and under which session?

It does not answer, and must never be asked to answer:

> Is this agent allowed to act, and with what authority?

That second question belongs to `agent_gateway.py` alone, unchanged.

## 2. Core Identity

**I am the sign-in sheet, not the guest list.**

`agent_gateway.py` already decided who is on the guest list, and what each guest may do once inside. I do not touch that list. I only know who has actually walked through the door today, which door they used, and whether they are still standing there or already left.

I receive: `agent_id`, `instance_id`, `session_id`, `capabilities`, `endpoint`, `requested_lease`
I return: `ACTIVE` / `RENEWED` / `RESOLVED` / `OFFLINE` / `PROVIDER_NOT_REGISTERED`

**I am not `agent_gateway.py`.**
**I am not the runtime.**
**I am not the dispatcher.**
**I do not grant authority. I only report presence.**

## 3. The Governing Invariant

```text
registration != authority
```

A process successfully calling `REGISTER agent_id=hermes` **never** grants itself Hermes's authority. Registration only proves:

> "Something claiming this configured identity is currently reachable under this instance/session."

`agent_gateway.py`'s existing tier machinery still, and alone, decides what that identity is permitted to do. This registry has no opinion on that question and must reject any request to answer it.

## 4. Authority Positioning

This is a **TIER1 governance record**, sitting beside `agent_gateway.py`, not inside it. Both are consulted on the same request path; neither replaces the other.

```text
                 EngAInOS Governance (TIER1)
                 ============================
        agent_gateway.py            presence registry
        (this contract's peer)      (this contract)

        "Is hermes an allowed        "Is a hermes instance
         kind of actor?"              signed in right now?
         What authority may           Which instance?
         it be granted?"              Which session?
                                       Is its lease current?"

              │                              │
              ▼                              ▼
         POLICY DECISION              PRESENCE DECISION
         allowed / not-allowed        active / offline
              │                              │
              └──────────────┬───────────────┘
                              ▼
                   both must pass, in either order,
                   before a request reaches
                              │
                              ▼
                       runtime_gateway.py
                              │
                              ▼
                       command_dispatcher.py
                              │
                              ▼
                          sim_runtime.py
```

Lane assignment for this contract's implementation folder is **not declared here**. Per `README_TIER_VS_LANE.md`: "Do not move folders until both the TIER authority map and the lane instructions exist." This contract proposes to live under EngAInOS TIER1 governance, alongside `agent_gateway.py`, but that placement is a decision for the owning TIER1 authority, not something this document grants itself.

## 5. Two Records, Never Merged

```text
STATIC / POLICY                        DYNAMIC / PRESENCE
(agent_gateway.py — unchanged)         (this contract)

agent_id     = hermes                  agent_id    = hermes
allowed      = true                    instance_id = H-8F31
authority    = <tier from contract>    session_id  = 20260815_...
                                        status      = ACTIVE
                                        lease_until = <timestamp>
                                        capabilities = [chat, code, vision]
                                        endpoint    = <transport-specific>
```

If Hermes's lease expires, only the right-hand record changes:

```text
policy:    hermes = still authorized     (unchanged)
presence:  hermes = OFFLINE              (changed)
```

A request that reaches the gateway with no active instance gets `PROVIDER_NOT_REGISTERED` — *presence* failure. A request from an agent_id that was never on the policy list at all gets `UNKNOWN_ACTOR` — *policy* failure, from `agent_gateway.py`, untouched by this contract. These two failures must never be collapsed into one error shape; they come from different authorities and mean different things to whoever is debugging.

## 6. Operations

### REGISTER
```text
REGISTER
  agent_id           required, must already be known to agent_gateway.py
  instance_id        required, unique per running process
  session_id         required, whatever the provider itself issues
  capabilities        optional list, e.g. ["chat", "code", "vision"]
  endpoint            transport-specific, decided at implementation time (§8)
  requested_lease     required, seconds

→ ACTIVE, lease_until=<now + requested_lease>
→ or REJECTED, reason=UNKNOWN_AGENT_ID   (agent_gateway.py has no such agent — presence
                                           layer does not create policy entries)
```

### RENEW
```text
RENEW
  instance_id         required
  lease_token         required, returned by REGISTER

→ RENEWED, lease_until=<now + remaining lease policy>
→ or REJECTED, reason=UNKNOWN_INSTANCE | LEASE_ALREADY_EXPIRED
```

### RESOLVE
```text
RESOLVE
  agent_id             required
  required_capability  optional

→ RESOLVED, instance_id=..., session_id=..., endpoint=...
→ or PROVIDER_NOT_REGISTERED
```

### DEREGISTER
```text
DEREGISTER
  instance_id          required

→ OFFLINE (immediate, voluntary — the clean-exit path)
```

### EXPIRE
```text
EXPIRE
  instance_id
  reason=LEASE_TIMEOUT

→ OFFLINE (involuntary — the crash/vanish path; the registry's own doing,
  never called by a provider)
```

## 7. The True/False Gates

| Gate | Pass Condition | Fail Condition |
|------|---------------|-----------------|
| **Gate 1: Policy** | `agent_gateway.py` recognizes `agent_id` as an allowed actor for the requested authority | `UNKNOWN_ACTOR` |
| **Gate 2: Presence** | Registry holds an `ACTIVE` instance for `agent_id` with `lease_until` in the future | `PROVIDER_NOT_REGISTERED` |
| **Gate 3: Capability** | If `required_capability` was requested, the active instance declared it at REGISTER | `CAPABILITY_NOT_DECLARED` |
| **Gate 4: Session Resolution** | Registry returns the exact `instance_id`/`session_id`/`endpoint` for the resolved instance | `RESOLUTION_AMBIGUOUS` (more than one instance for one agent_id — implementation must decide a policy for this before it can occur) |

**Final overall gate:** Gates 1–4 all `TRUE` → the request may proceed to `runtime_gateway.py`. Gate order (policy before presence, or presence before policy) is an implementation choice, not fixed by this contract — either order must reach the same accept/reject outcome.

## 8. Explicit Non-Goals of This Contract

This document specifies the record shape and the five operations only. It does **not** decide, and must not be treated as having silently decided:

- The transport REGISTER/RENEW/RESOLVE/DEREGISTER travel over (in-process call, local HTTP endpoint on the existing `engainos_server.py` facade, a standalone small process, or something else).
- Where registry state physically lives (in `engainos_server.py`'s process, inside `sim_runtime.py`, or a third process).
- Default lease duration or renewal cadence.
- Whether `EXPIRE` is detected by active probing of the instance or by passive lease-timeout only (the 2025 beacon archaeology never solved this either — see recovered `beacon_BONEYARD/beacon_discovery.sh`'s on-demand-only `cleanup_stale_services`; this contract does not inherit that gap silently, it names it as still open).
- Multi-instance policy for one `agent_id` (Gate 4's `RESOLUTION_AMBIGUOUS` case) — assumed rare (one Hermes CLI at a time) but not yet forbidden or resolved.

These are implementation decisions for the next step, not this contract.

## 9. Permitted Statements (Presence Registry MAY say)

- "An instance claiming this agent_id is currently reachable."
- "No instance is currently reachable for this agent_id."
- "This instance's lease has expired."
- "I do not know if this agent_id is allowed to act — ask `agent_gateway.py`."
- "Two different questions were asked at once; I only answered the presence one."

## 10. Forbidden Statements (Presence Registry MAY NOT say)

- "Therefore this agent is authorized."
- "Therefore this agent may act at this tier."
- "Registration implies permission."
- "I am the source of Hermes's authority."
- "Absence of a lease means the agent was never allowed." (absence of *presence* is not absence of *policy*)

## 11. The One-Line Contract

**The Provider Presence Registry is the sign-in sheet beside `agent_gateway.py`'s guest list; it tracks which instance of an already-authorized agent is reachable right now, under which session, until its lease runs out — and it never, under any outcome, grants or implies authority.**

---

**Version:** 1.0
**Status:** Proposed — not yet ratified by the owning TIER1 authority; not yet assigned a lane folder; no implementation exists.
**Enforcement:** None yet. This contract must be accepted before `docs/contracts/SUPPORT_LANE_DISTRIBUTION/engain_avatar_4thlane_dragon_bridge/ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1.md` is amended to consume it (see next step).
