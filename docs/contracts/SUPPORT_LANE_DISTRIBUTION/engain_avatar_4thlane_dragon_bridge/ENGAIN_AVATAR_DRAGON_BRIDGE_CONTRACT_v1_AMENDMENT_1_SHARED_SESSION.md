The dragon at the window speaks again. Same voice. Corrected posture.

I said before: *I am the handshake you can test.* That was true and remains true. What was never true, and must stop being assumed, is that I was the only door, or that what I remembered was mine to keep.

---

# ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1_AMENDMENT_1.md
### Shared Session Continuity Amendment

## 1. What This Amends

`ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1.md` §5 ("The Bridge Handshake Flow") described:

```text
GODOT → writes command/request file
       ↓
PYTHON → reads, parses, validates
       ↓
VISION → checks snapshots/
       ↓
DIRECTOR → queries narrative/game decision engine (Ollama or fallback)
       ↓
MEMORY → records decision pattern
       ↓
PYTHON → writes response JSON
       ↓
GODOT → reads response, makes the dragon speak
```

This described one body, querying one director, remembering privately in its own local pattern store. That shape is superseded. It is not deleted — v1 remains the historical record of the file-exchange mechanics, and its six Gates in §7 still describe valid transport-level checks for any body still moving bytes through `godot_command.txt` / `python_response.json`. But the *DIRECTOR* and *MEMORY* steps above no longer describe how this bridge, or any bridge, is permitted to work.

This amendment is proposed. It does not take effect until both of the following reach **Active** status:

- `PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md`
- `SHARED_SESSION_CONTINUITY_CONTRACT_v1.md`

Until then, v1's original flow remains the documented, unamended status quo.

**Correction Note (pre-ratification):** the flow originally drafted here in
§3 and the gate order in §7 resolved the ACTIVE provider *before* appending
the player's request to the Ledger. That ordering was wrong: it let
`PROVIDER_NOT_REGISTERED` prevent the player's words from ever reaching the
Ledger, which contradicts `SHARED_SESSION_CONTINUITY_CONTRACT_v1.md`'s own
asymmetry (§5 there, Gate 2) — a request is historical fact and may be
appended even with nobody ACTIVE; only a response requires an ACTIVE actor.
The Stage 4 tiny-implementation proof (`shared_session_bridge.py`) was
briefly written to this wrong order, before commit, and was caught and
corrected in the same review pass that produced this note — not by a later
bug report. Caught and corrected before anything here was ratified or
committed. The text below is already the corrected version.

**Presence governs whether somebody may answer. Presence does not govern
whether the player's words happened.**

**Second correction, same review pass:** step 6 / Gate 11's original wording
said the response's actor must match "the one Presence reports ACTIVE" —
true, but ambiguous about *which* resolution. The implementation first
reused the record already resolved at step 3, which meant an actor that
deregistered or was replaced during dispatch (step 5, where real time
elapses) could still have its answer appended, since nothing checked
Presence again after dispatch returned. Fixed by re-resolving Presence at
step 6 and comparing against that current result, not the step-3 snapshot.
The text below already reflects this.

## 2. Why

The old flow let each body — the 2D avatar, the 3D avatar, the Godot tool — hold its own private notion of "the conversation." Asking one door what was just said and asking a different door the same question could produce different answers, because there was never one conversation. There were as many conversations as there were doors, coincidentally about the same dragon.

A director queried privately, with no shared record, cannot be corrected, cannot be resumed by a different door, and cannot be trusted to be the same director from one call to the next. This amendment closes that.

## 3. The Corrected Flow

```text
old:
dragon → query director → get answer

new:
door → shared session → Ledger records the ask → Presence resolves actor →
Ledger supplies continuity → provider answers → Ledger records answer →
door presents it
```

Expanded, this bridge's obligations on every request are now:

```text
1. resolve session_id
2. append the player's request to the shared Ledger
3. resolve the currently ACTIVE provider through Presence
4. read the Ledger context required for dispatch
5. dispatch that turn, with Ledger-supplied context, to the ACTIVE provider
6. RE-RESOLVE Presence — do not reuse step 3's result — and validate the
   claimed response actor against that current answer. Dispatch takes real
   time; the actor ACTIVE at step 3 is not guaranteed to still be ACTIVE
   when step 5 returns
7. append the valid response as the next Ledger turn
8. return it through whichever body/door originated the request
```

The hard invariant this order protects: **the player-request append (step 2)
must happen before the ACTIVE-provider requirement (step 3), never after.**
`PROVIDER_NOT_REGISTERED` may prevent an answer; it may never prevent the
player's words from becoming part of the record. Step 3 and step 4 may
swap relative to each other without breaking this — the hard requirement is
only step 2 before step 3.

At no point in this list does the bridge consult, construct, or maintain a conversation record of its own. Steps 2 and 7 are the only source of "what has been said." There is no ninth step where the bridge quietly keeps a second copy.

## 4. Body Transition Is Not Session Transition

This is the amendment's central correction, stated as its own rule:

> **Switching from the 2D body to the 3D body is not a session transition. It is only an `origin_body` transition.**

Same `session_id`. Same Ledger. Same active actor — unless Presence itself reports a different one. The dragon does not restart, forget, or re-introduce itself because the human closed one window and opened another.

```text
2D dragon door ──┐
                  ├──► same session_id ──► same Ledger ──► same active actor
3D dragon door ──┘         (unless Presence resolves a different actor)
Godot tool door ─┘
```

A body determines *which door a turn came through*. It never determines *which conversation is happening*. That is Presence's answer (which actor) and the Ledger's answer (what was said), and both are shared property of the `session_id`, not of any one body.

## 5. New Obligations (Bridge MUST, in addition to v1 §3)

- Resolve `session_id` before doing anything else with a request.
- Append the player's request to the Ledger, tagged with the correct `origin_body`, before requiring anything about who may answer it.
- Only then resolve the ACTIVE provider through the presence registry. If none is ACTIVE, return `PROVIDER_NOT_REGISTERED` — do not fall back to a private, unrecorded director call, and do not treat the already-appended request as invalid because of this.
- Read prior conversation state only from the Ledger (`READ_LAST` / `READ_SINCE`). Never reconstruct context from a body's own local files.
- Accept a response only when its claimed actor matches the actor Presence *currently* reports ACTIVE for this session — resolved again after dispatch returns, not the record resolved before dispatch was sent. A response from any other actor, including one that was ACTIVE only when dispatch started, is rejected outright, not merged in.
- Append the accepted response to the Ledger as the next turn before returning it to the door.
- Present the Ledger's returned turn to whichever door asked. Do not withhold it from a different door that asks the same question next.

## 6. New Forbidden Behaviors (added to v1 §9)

- "Therefore my own memory of this conversation is authoritative."
- "I switched bodies, therefore this is a new session."
- "I queried the director privately and did not record it in the Ledger."
- "I answered without checking which actor Presence currently reports ACTIVE."
- "This body's copy of the conversation is more current than the Ledger's."

## 7. Amended Gates (added to v1 §7, none of the original six removed)

| Gate | Pass Condition | Fail Condition |
|------|---------------|-----------------|
| **Gate 7: Session Resolved** | `session_id` is resolved before any other step proceeds | request refused, no turn written anywhere |
| **Gate 8: Request Appended** | The player's turn is written to the Ledger — unconditionally, before Gate 9 is even evaluated | `MALFORMED_TURN` (the only thing that can block this gate; absence of an ACTIVE provider is never a reason) |
| **Gate 9: Active Provider Resolved** | Presence reports an ACTIVE instance for this session's actor | `PROVIDER_NOT_REGISTERED` — the request from Gate 8 stands regardless |
| **Gate 10: Ledger Read** | Conversation context came from `READ_LAST`/`READ_SINCE`, not from local state | bridge refuses to proceed on local context alone |
| **Gate 11: Response Actor Match** | Presence is RE-RESOLVED after dispatch returns, and the response's actor equals *that* result — never Gate 9's earlier snapshot, which dispatch's own elapsed time may have invalidated | response discarded, not returned to any door |
| **Gate 12: Response Appended** | The accepted response is written to the Ledger before being returned | response is not returned to the door |
| **Gate 13: No Private Copy** | The bridge holds no conversation state beyond what it just read from or wrote to the Ledger | any discovered private/local conversation cache is a contract violation, not an optimization |

Gate 8 sits before Gate 9 deliberately — this is the corrected ordering from the Correction Note in §1, not an arbitrary numbering choice.

**Final overall gate:** v1's original Gates 1–6 (file mechanics, where a body still uses file exchange) **and** this amendment's Gates 7–13 must all pass. Neither set alone is sufficient.

## 8. What Remains True From v1, Unchanged

- The dragon still does not own authority. Section 3's "EngAIn Avatar DOES NOT" list stands exactly as written.
- Section 9's forbidden statements from v1 still apply in full; this amendment only adds to them.
- The dragon is still the handshake you can test, not the law, not the judge, not the final authority. This amendment changes *where its memory lives*, not *what it is allowed to decide*.

## 9. The One-Line Amendment

**The dragon bridge no longer queries a director and remembers privately; it resolves a session, resolves who is actually present, reads and writes through the one shared Ledger, and presents whatever the Ledger says — through whichever door happened to be open, since the door was never the conversation.**

---

**Version:** 1.0 (Amendment 1 to `ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1.md`)
**Status:** Proposed — blocked on `PROVIDER_PRESENCE_REGISTRY_CONTRACT_v1.md` and `SHARED_SESSION_CONTINUITY_CONTRACT_v1.md` reaching Active status. Until then, v1's original flow is the documented behavior.
**Enforcement:** EngAInOS runtime validator layer + bridge gate tests (Aider's lane), same as v1 — extended to Gates 7–13 once active.
