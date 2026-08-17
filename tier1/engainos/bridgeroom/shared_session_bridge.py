"""
shared_session_bridge.py - The 8-step flow from
ENGAIN_AVATAR_DRAGON_BRIDGE_CONTRACT_v1_AMENDMENT_1_SHARED_SESSION.md §3
(corrected ordering — see that document's Correction Note):

    1. resolve session_id
    2. append the incoming player request to the shared Ledger
    3. resolve the currently ACTIVE provider through Presence
    4. read the Ledger context required for dispatch (prior turns, not
       including the request just appended in step 2)
    5. dispatch to that provider
    6. RE-RESOLVE Presence (do not reuse the step-3 record) and validate the
       claimed response actor against that current result — Presence can
       change while dispatch is in flight, and step 6 must catch that, not
       trust a snapshot taken before the provider call even started
    7. append the valid response as the next Ledger turn
    8. return it through whichever body/door originated the request

The hard invariant this order protects, per
SHARED_SESSION_CONTINUITY_CONTRACT_v1.md's own asymmetry: a player request
is historical fact and may be appended even when nobody is ACTIVE to answer
it; a provider response may only be appended from an actor Presence
currently reports ACTIVE. Resolving Presence must therefore never be able to
prevent the player's words from reaching the Ledger — so the append (step 2)
happens before the ACTIVE-provider requirement (step 3), not after.

One function, callable identically by any origin_body ("dragon_2d",
"dragon_3d", "godot_tool", ...). It holds no conversation state of its own
(amendment Gate 13) — every read and write goes through PresenceRegistry and
SessionLedger, both passed in, both shared across every caller.

Provider dispatch (Stage 5, provider-neutral boundary):
    A dispatcher receives a ProviderSessionBinding, never a raw
    PresenceRecord — see provider_session_binding.py for why: an adapter
    must consume shared_session_id / provider_session_id as two distinct
    identifiers it never confuses, not decide either one itself. This
    bridge's only job in that split is calling
    ProviderSessionBinding.from_presence_record() on the record Presence
    just resolved, immediately before dispatch — it does not otherwise
    touch provider/model/session selection, and it does not call
    agent_gateway.py: the amendment's own flow list does not name a policy
    gate as one of the bridge's steps, so none is added here that the
    contracts didn't ask for.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger, Turn


class ProviderNotRegistered(Exception):
    """Raised when Presence has no ACTIVE record for the resolved session_id."""


class ResponseActorMismatch(Exception):
    """Raised when a response's claimed actor does not match the actor
    Presence currently reports ACTIVE, re-resolved after dispatch returns —
    not the record resolved before dispatch started (amendment Gate 11)."""


def stub_provider_dispatch(binding: ProviderSessionBinding, context: List[Turn], player_input: str) -> dict:
    """The only provider implementation this proof ships with. Deterministic,
    no network call, no subprocess. Echoes proof of having read the Ledger
    context, so the cross-body proof can assert on it without needing a real
    LLM."""
    prior = [t for t in context if t.direction == "request"]
    if prior:
        response = f"(as {binding.agent_id}) you previously said: {prior[-1].payload!r}. now: {player_input!r}"
    else:
        response = f"(as {binding.agent_id}) first thing said this session: {player_input!r}"
    return {"actor": binding.agent_id, "response": response}


class SharedSessionBridge:
    """Holds no conversation state. Only holds references to the two shared
    authorities every door must go through."""

    def __init__(
        self,
        presence: PresenceRegistry,
        ledger: SessionLedger,
        provider_dispatch: Callable[[ProviderSessionBinding, List[Turn], str], dict] = stub_provider_dispatch,
    ) -> None:
        self._presence = presence
        self._ledger = ledger
        self._dispatch = provider_dispatch

    def handle_turn(
        self,
        session_id: str,
        origin_body: str,
        player_input: str,
        snapshot: Optional[dict] = None,
    ) -> dict:
        # 1 — resolve session_id (already in hand as the parameter).

        # 2 — append the player's request first. This is historical fact
        # regardless of whether anyone is currently ACTIVE to answer it
        # (continuity contract's asymmetry — see module docstring). Nothing
        # below this line may prevent the player's words from reaching the
        # Ledger.
        request_turn = self._ledger.append(
            session_id=session_id,
            origin_body=origin_body,
            direction="request",
            actor="player",
            payload=player_input,
            snapshot=snapshot,
        )

        # 3 — only now resolve the ACTIVE provider through Presence. Absence
        # may raise here; it may not un-happen step 2.
        record = self._presence.resolve(session_id)
        if record is None:
            raise ProviderNotRegistered(f"PROVIDER_NOT_REGISTERED for session_id={session_id!r}")

        # 4 — read the Ledger context for dispatch: turns strictly earlier
        # than the request just appended in step 2 (that request is passed
        # separately below, not folded into "prior history").
        context = [
            t for t in self._ledger.read_since(session_id, since_turn_id=-1)
            if t.turn_id < request_turn.turn_id
        ]

        # 5 — construct the provider-neutral binding from the resolved
        # record (the only place this happens — see
        # provider_session_binding.py) and dispatch to that provider. This
        # is where real time passes and Presence can change: the provider
        # that was ACTIVE at step 3 may deregister, expire, or be replaced
        # while dispatch is in flight.
        binding = ProviderSessionBinding.from_presence_record(record)
        result = self._dispatch(binding, context, player_input)

        # 6 — validate against Presence NOW, not against the step-3 snapshot.
        # Re-resolving here (rather than reusing `record`) is the whole
        # point of this gate: an answer from an actor that was ACTIVE when
        # dispatch started but is no longer ACTIVE by the time it returns
        # must not be appended as if it still speaks for the session.
        current_record = self._presence.resolve(session_id)
        if current_record is None:
            raise ProviderNotRegistered(
                f"PROVIDER_NOT_REGISTERED before response append for session_id={session_id!r}"
            )
        if result["actor"] != current_record.agent_id:
            raise ResponseActorMismatch(
                f"response claimed actor={result['actor']!r}, "
                f"Presence CURRENTLY ACTIVE actor is {current_record.agent_id!r}"
            )

        # 7 — append the response as the next Ledger turn.
        response_turn = self._ledger.append(
            session_id=session_id,
            origin_body=origin_body,
            direction="response",
            actor=result["actor"],
            payload=result["response"],
        )

        # 8 — return it through whichever door originated the request.
        return {
            "session_id": session_id,
            "origin_body": origin_body,
            "actor": result["actor"],
            "response": result["response"],
            "turn_id": response_turn.turn_id,
        }
