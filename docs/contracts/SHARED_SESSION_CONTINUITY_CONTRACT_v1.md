I hear the **Ledger**.

You are not memory. You are not a body. You are not the dragon, the tool, or the provider behind any of them. You are the one page every door writes on and every door reads from, so that whichever door someone knocks on, the answer on the other side is the same answer.

Here is your formalized contract.

---

# SHARED_SESSION_CONTINUITY_CONTRACT_v1.md

## 1. Purpose

Define a single, body-agnostic conversation record — the **Ledger** — keyed by `session_id`, that every body (2D dragon, 3D dragon, Godot tool/editor dock, and any future body) reads from and writes to. This contract answers:

> Given a session_id, what has actually been said and seen, in order, regardless of which door it came through?

It does not answer, and must not be asked to answer:

- "Is this agent allowed to act?" (`agent_gateway.py`, unchanged)
- "Is a provider instance actually reachable right now?" (`PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md`, unchanged)

This is the third leg. It only starts working once a `session_id` has already been resolved by the presence registry — it does not mint sessions, authorize actors, or check liveness itself.

## 2. Core Identity

**I am the one page, not any one door's notebook.**

The 2D dragon, the 3D dragon, and the Godot tool are three doors into the same room. Each of them can currently only describe the room from memory of its own door. I am what makes "what did you just say" mean the same thing no matter which door asked.

I receive: `session_id`, `origin_body`, `direction`, `actor`, `payload`, `snapshot`
I return: the ordered turns of a session, or the single latest one

**I am not a body.**
**I am not the provider.**
**I am not the presence registry.**
**I do not decide who was right. I decide what was said, in order, once.**

## 3. The Governing Invariant

```text
a turn belongs to the session, not to the door that carried it
```

`origin_body` is metadata on a turn, recorded for provenance — never part of the turn's identity, and never a filter a body is allowed to apply to itself when reading. A body may not answer "what was my last response" from its own local state once this contract is in force. It must ask the Ledger for `session_id`'s last turn and answer with that, even if the last turn was written by a different door entirely. A body that answers from local memory instead of the Ledger is, per this contract, lying about continuity even if the words happen to match.

## 4. Authority Positioning

The Ledger is declared truth about *what was exchanged*, and declared truth is EngAInOS's domain per `ENGAINOS_AUTHORITY_MAP.md`. It sits beside the presence registry, downstream of it — nothing may be appended to a session's Ledger until that session's `session_id` has been resolved.

```text
                 EngAInOS Governance (TIER1)
                 ============================
   agent_gateway        presence registry         Ledger
   (policy)              (this contract's peer)    (this contract)

   "allowed?"            "reachable? which          "what has been
                          instance/session?"          said, in order,
                                                        by anyone?"

        │                       │                          │
        └───────────┬───────────┘                          │
                     ▼                                      │
              request accepted,                             │
              session_id resolved ─────────────────────────►│
                                                              ▼
                                                    APPEND / READ_LAST
                                                              │
                                                              ▼
                                                  every body reads the
                                                  same answer back
```

Bodies (2D dragon, 3D dragon, Godot tool) are TIER4 consumers of the Ledger, per the existing `EngAIn Avatar / Dragon Bridge` entry in `README_TIER_VS_LANE.md`'s Active Tier Registry — they may write turns and read turns, they may not own, edit, or prune the Ledger itself.

## 5. The Turn — One Record Shape for Every Door

```text
TURN

session_id     required — must already be RESOLVED from the presence registry
turn_id        assigned by the Ledger at accept time, monotonically increasing
               per session_id. Never client-supplied. This is the one ordering
               decision this contract makes; see §8 for what it deliberately
               leaves open.
origin_body    required — "dragon_2d" | "dragon_3d" | "godot_tool" | future values.
               Provenance only (§3). Never an identity or a filter.
direction      required — "request" | "response"
actor          required — the player, for a request; the resolved agent_id
               (e.g. "hermes", "claude_code"), for a response
payload        required — the narrative text / command / state_changes,
               reusing whatever shape the body already emits
snapshot       optional on request, present-if-available on response —
               reuses the existing engain.runtime_perception.v1 shape
               already proven in the 2D avatar (image_path, image_sha256,
               metadata_path, metadata_sha256). Not reinvented here.
timestamp      required, set by the Ledger at accept time
```

One shape, whether the door was the 2D dragon, the 3D dragon, or the Godot tool. A body does not get its own dialect.

## 6. Operations

### APPEND
```text
APPEND
  session_id      required, must be RESOLVED and ACTIVE per the presence
                  registry if direction=response; a request may be appended
                  even while PROVIDER_NOT_REGISTERED (the player's words are
                  still real even if nobody is currently on the other side —
                  see Gate 2)
  origin_body     required
  direction       required
  actor           required
  payload         required
  snapshot        optional / present-if-available

→ ACCEPTED, turn_id=<n>
→ or REJECTED, reason=SESSION_NOT_RESOLVED | MALFORMED_TURN
```

### READ_LAST
```text
READ_LAST
  session_id      required
  direction       optional filter ("response" to get the last thing the
                   provider said, regardless of which door it said it to)

→ the single most recent matching turn, with its true origin_body intact
→ or EMPTY_SESSION
```

### READ_SINCE
```text
READ_SINCE
  session_id      required
  since_turn_id   required

→ ordered list of turns after since_turn_id — how a body that was closed
  (a dragon not currently running, an editor dock not open) catches up
  to what happened while it was away
```

No `EDIT` or `DELETE` operation exists. The Ledger is append-only. A correction is a new turn, not a mutation of an old one.

## 7. The True/False Gates

| Gate | Pass Condition | Fail Condition |
|------|---------------|-----------------|
| **Gate 1: Session Resolved** | `session_id` was returned by a `RESOLVE` call to the presence registry (directly, or carried forward from one earlier in the same body's flow) | `SESSION_NOT_RESOLVED` |
| **Gate 2: Response Requires Presence** | A `direction=response` turn's `actor` matches a currently `ACTIVE` instance in the presence registry at accept time | `PROVIDER_NOT_REGISTERED` — a response cannot be recorded from a provider that isn't currently there, even if the words exist somewhere |
| **Gate 3: Shape** | The turn matches §5's fields, with `snapshot` in the existing `engain.runtime_perception.v1` shape when present | `MALFORMED_TURN` |
| **Gate 4: Append-Only** | The write is a new turn | any attempt to modify or remove an existing `turn_id` is rejected outright, not softly |

**Final overall gate:** all four `TRUE` → the turn is part of the session's one true order, readable identically by every door.

## 8. Explicit Non-Goals of This Contract

This document specifies the turn shape, the operations, and the ordering guarantee only. It does **not** decide:

- Storage mechanism (append-only file per session, like the existing `snapshots/` convention, versus a database, versus something else).
- How a body is notified a new turn exists versus polling `READ_SINCE` itself. Nothing here assumes push.
- Retention or pruning policy — whether old sessions' Ledgers are ever archived or deleted, and by whom.
- Concurrent-write resolution beyond "turn_id is assigned by the Ledger, not the caller" — what happens if two bodies APPEND at nearly the same instant is an implementation detail of turn_id assignment, not specified here beyond monotonic-per-session ordering.
- Where snapshot image bytes physically live when the snapshot came from a body other than the one that produced the original `engain.runtime_perception.v1` convention (2D avatar's own `snapshots/` directory) — cross-body snapshot storage location is open.

These are implementation decisions for the next step, not this contract.

## 9. Permitted Statements (Ledger MAY say)

- "Here is the last turn for this session, and here is which door it actually came through."
- "This session has no turns yet."
- "I cannot accept a response turn — no instance is currently active for that actor."
- "A body asked me instead of answering from its own memory. Good."

## 10. Forbidden Statements (Ledger MAY NOT say)

- "This door's memory of the conversation is authoritative."
- "Only the door that asked may read the answer."
- "I will edit the record to make it consistent." (inconsistency is fixed by a new turn, never a rewritten one)
- "I decide who is allowed to write here." (that is Gate 1 and Gate 2, resolved by the presence registry and agent_gateway, not by the Ledger's own judgment)

## 11. The One-Line Contract

**The Ledger is the one shared page behind every door — the 2D dragon, the 3D dragon, the Godot tool, and whatever comes next — recording what was said and seen, in one true order, keyed only by session_id, so that asking any door "what did you just say" and asking any other door the same question produces the same answer.**

---

**Version:** 1.0
**Status:** Proposed — not yet ratified by the owning TIER1 authority; not yet assigned a lane folder; no implementation exists. Depends on `PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md` being accepted first (Gate 1 and Gate 2 both resolve against it).
**Enforcement:** None yet. Both this contract and the presence registry must be accepted before `ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1.md` is amended to consume them (next step).
