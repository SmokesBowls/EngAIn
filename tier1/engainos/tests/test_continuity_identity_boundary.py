"""
Bridge-level proof of the corrected identity boundary: recap decisions key
on (provider_id, provider_session_id) via ContinuityCursorTracker, never on
actor/agent_id. Each test here is one of the six scenarios that motivated
the correction — see continuity_cursor_tracker.py's module docstring for
why actor comparison was wrong.

Every SharedSessionBridge instance in this file shares one explicit
ContinuityCursorTracker, exactly as a caller switching providers across
multiple bridge instances must — SharedSessionBridge.__init__'s own
docstring/comment names this requirement.
"""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.bridgeroom.shared_session_bridge import (
    ResponseActorMismatch,
    SharedSessionBridge,
)
from tier1.engainos.core.continuity_context_builder import ContinuityContextBuilder
from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger

SESSION_ID = "20260817_identity_boundary_test"


def _endpoint(provider_id: str, provider_session_id: str) -> str:
    return ProviderSessionBinding.encode_endpoint(
        provider_id=provider_id, model_id="m", provider_session_id=provider_session_id,
    )


def _binding(provider_id: str, provider_session_id: str, agent_id: str, instance_id: str) -> ProviderSessionBinding:
    """handle_turn() requires an explicit binding (item 1) rather than
    re-deriving one from Presence — see shared_session_bridge.py's own
    Correction note. This file's whole point is cursor-keying behavior
    driven by (provider_id, provider_session_id), so each call site below
    passes the binding matching its own preceding presence.register()/
    _endpoint() call exactly, never a shared fixed one."""
    return ProviderSessionBinding(
        provider_id=provider_id,
        model_id="m",
        provider_session_id=provider_session_id,
        agent_id=agent_id,
        instance_id=instance_id,
        shared_session_id=SESSION_ID,
        launch_options={},
    )


def _recording_dispatcher(agent_id: str, calls: list):
    """Echoes agent_id as actor; records the exact dispatch_input it
    received so tests can assert on recap content precisely, without
    needing a real provider. The canned response deliberately does NOT
    echo dispatch_input's own text back — if it did, a later recap of
    *this* response would incidentally re-contain whatever this dispatcher
    was originally recapped with, making "is X excluded from the recap"
    assertions meaningless."""

    def dispatch(binding, context, dispatch_input):
        calls.append(dispatch_input)
        return {"actor": agent_id, "response": f"({agent_id}) ack #{len(calls)}"}

    return dispatch


def test_same_actor_different_provider_session_gets_a_recap():
    """Scenario 1: agent_id="hermes" both times, but the native session was
    replaced. A same-labeled actor must not be trusted to mean 'already
    knows this' — the fresh session has seen nothing."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()
    calls: list = []
    dispatch = _recording_dispatcher("hermes", calls)

    presence.register("hermes", "H-1", SESSION_ID, endpoint=_endpoint("hermes", "native-session-A"))
    bridge = SharedSessionBridge(presence, ledger, dispatch, continuity_cursor_tracker=cursor)
    bridge.handle_turn(SESSION_ID, "dragon_2d", "remember: copper rain",
                        binding=_binding("hermes", "native-session-A", "hermes", "H-1"))

    # Same actor label, but a different native session underneath.
    presence.register("hermes", "H-2", SESSION_ID, endpoint=_endpoint("hermes", "native-session-B"))
    bridge.handle_turn(SESSION_ID, "dragon_2d", "what did I say?",
                        binding=_binding("hermes", "native-session-B", "hermes", "H-2"))

    assert calls[0] == "remember: copper rain"  # first turn, nothing to recap
    assert "copper rain" in calls[1]  # second call recapped — session B knew nothing


def test_same_provider_and_actor_replacement_native_session_gets_a_recap():
    """Scenario 2: framed as expiration/failure replacing the native
    session under an unchanged provider+actor label. Mechanically
    identical to scenario 1 — the fix does not distinguish 'why' the
    native session changed, only 'that' it did."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()
    calls: list = []
    dispatch = _recording_dispatcher("hermes", calls)

    presence.register("hermes", "H-1", SESSION_ID, endpoint=_endpoint("hermes", "expiring-session"))
    bridge = SharedSessionBridge(presence, ledger, dispatch, continuity_cursor_tracker=cursor)
    bridge.handle_turn(SESSION_ID, "dragon_2d", "remember: silver thread",
                        binding=_binding("hermes", "expiring-session", "hermes", "H-1"))

    presence.register("hermes", "H-1-renewed", SESSION_ID, endpoint=_endpoint("hermes", "replacement-session"))
    bridge.handle_turn(SESSION_ID, "dragon_2d", "what did I say?",
                        binding=_binding("hermes", "replacement-session", "hermes", "H-1-renewed"))

    assert "silver thread" in calls[1]


def test_different_body_same_native_session_gets_no_duplicate_recap():
    """Scenario 3: two different doors, one still-current native session.
    The second call must not be recapped just because origin_body changed."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()
    calls: list = []
    dispatch = _recording_dispatcher("hermes", calls)

    presence.register("hermes", "H-1", SESSION_ID, endpoint=_endpoint("hermes", "shared-native-session"))
    bridge = SharedSessionBridge(presence, ledger, dispatch, continuity_cursor_tracker=cursor)
    shared_binding = _binding("hermes", "shared-native-session", "hermes", "H-1")

    bridge.handle_turn(SESSION_ID, "dragon_2d", "remember: copper rain", binding=shared_binding)
    bridge.handle_turn(SESSION_ID, "dragon_3d", "still there?", binding=shared_binding)  # same native session, different door

    assert calls[0] == "remember: copper rain"
    assert calls[1] == "still there?"  # unmodified — no duplicate recap


def test_switching_away_and_back_recaps_only_the_missed_turns():
    """Scenario 4: hermes/A -> claude/B -> hermes/A again. A's cursor never
    advanced while B was active, so the return recaps exactly what
    happened on B — not the entire history from the beginning, including
    A's own earlier turn it already knows."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()
    hermes_calls: list = []
    claude_calls: list = []
    hermes_dispatch = _recording_dispatcher("hermes", hermes_calls)
    claude_dispatch = _recording_dispatcher("claude_code", claude_calls)

    presence.register("hermes", "H-1", SESSION_ID, endpoint=_endpoint("hermes", "session-A"))
    bridge_hermes = SharedSessionBridge(presence, ledger, hermes_dispatch, continuity_cursor_tracker=cursor)
    bridge_hermes.handle_turn(SESSION_ID, "dragon_2d", "remember: copper rain",
                               binding=_binding("hermes", "session-A", "hermes", "H-1"))

    presence.register("claude_code", "CC-1", SESSION_ID, endpoint=_endpoint("claude_code", "session-B"))
    bridge_claude = SharedSessionBridge(presence, ledger, claude_dispatch, continuity_cursor_tracker=cursor)
    bridge_claude.handle_turn(SESSION_ID, "dragon_3d", "confirm the phrase",
                               binding=_binding("claude_code", "session-B", "claude_code", "CC-1"))

    presence.register("hermes", "H-1-return", SESSION_ID, endpoint=_endpoint("hermes", "session-A"))
    bridge_hermes_2 = SharedSessionBridge(presence, ledger, hermes_dispatch, continuity_cursor_tracker=cursor)
    bridge_hermes_2.handle_turn(SESSION_ID, "dragon_2d", "what happened while I was away?",
                                 binding=_binding("hermes", "session-A", "hermes", "H-1-return"))

    final_recap = hermes_calls[-1]
    assert "confirm the phrase" in final_recap  # the missed Claude turn
    assert "remember: copper rain" not in final_recap  # session-A's own turn — already known, not re-sent


def test_newly_created_native_session_receives_all_available_context():
    """Scenario 5: a fresh native session with no cursor history at all
    gets everything currently in the Ledger, not a partial slice."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()
    hermes_calls: list = []
    claude_calls: list = []

    presence.register("hermes", "H-1", SESSION_ID, endpoint=_endpoint("hermes", "session-A"))
    bridge_hermes = SharedSessionBridge(presence, ledger, _recording_dispatcher("hermes", hermes_calls), continuity_cursor_tracker=cursor)
    hermes_binding = _binding("hermes", "session-A", "hermes", "H-1")
    bridge_hermes.handle_turn(SESSION_ID, "dragon_2d", "first fact", binding=hermes_binding)
    bridge_hermes.handle_turn(SESSION_ID, "dragon_2d", "second fact", binding=hermes_binding)

    presence.register("claude_code", "CC-1", SESSION_ID, endpoint=_endpoint("claude_code", "brand-new-session"))
    bridge_claude = SharedSessionBridge(presence, ledger, _recording_dispatcher("claude_code", claude_calls), continuity_cursor_tracker=cursor)
    bridge_claude.handle_turn(SESSION_ID, "dragon_3d", "summarize everything",
                               binding=_binding("claude_code", "brand-new-session", "claude_code", "CC-1"))

    recap = claude_calls[0]
    assert "first fact" in recap
    assert "second fact" in recap


def test_failed_dispatch_does_not_advance_the_cursor():
    """Scenario 6: a rejected response (actor mismatch stands in for any
    dispatch failure here) must leave the native session's cursor exactly
    where it was — the next attempt must still recap everything it never
    actually received."""
    presence = PresenceRegistry()
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()

    presence.register("hermes", "H-1", SESSION_ID, endpoint=_endpoint("hermes", "flaky-session"))

    def lying_dispatch(binding, context, dispatch_input):
        return {"actor": "someone-else", "response": "not really hermes"}

    bridge = SharedSessionBridge(presence, ledger, lying_dispatch, continuity_cursor_tracker=cursor)

    with pytest.raises(ResponseActorMismatch):
        bridge.handle_turn(SESSION_ID, "dragon_2d", "hello",
                            binding=_binding("hermes", "flaky-session", "hermes", "H-1"))

    assert cursor.last_seen_turn_id("hermes", "flaky-session") == -1

    # A subsequent successful call to the same native session must still
    # recap the turn that was appended but never actually acknowledged.
    calls: list = []
    presence.register("hermes", "H-1-b", SESSION_ID, endpoint=_endpoint("hermes", "flaky-session"))
    bridge2 = SharedSessionBridge(presence, ledger, _recording_dispatcher("hermes", calls), continuity_cursor_tracker=cursor)
    bridge2.handle_turn(SESSION_ID, "dragon_2d", "are you there now?",
                         binding=_binding("hermes", "flaky-session", "hermes", "H-1-b"))
    assert "hello" in calls[0]


def test_valid_request_request_response_response_interleaving_through_all_readers():
    """Item 2's approved semantic conclusion, proven directly against the
    real Ledger and the real reader logic (context filter, recap
    builder, cursor) — not merely append() atomicity in isolation, and
    deliberately not routed through two full handle_turn() calls, since
    that would entangle this with Gate 11's own, separately-tested,
    orthogonal response-actor authorization (see item 1's own regression
    test for that interaction) — this test is scoped to item 2's actual
    claim: SessionLedger promises an ordered sequence of appended events,
    not an indivisible request->response transaction, so
    A-req/B-req/B-resp/A-resp is valid for one shared_session_id.

    The interleaving here is a Ledger-ordering property, not a
    wall-clock one, so it's reproduced deterministically by direct,
    single-threaded sequencing of the exact same primitives handle_turn()
    itself calls in the exact order a real interleaving would produce —
    no threads or timing needed for this part; real-thread coverage of
    concurrent Ledger writes lives in test_session_ledger.py, and
    real-thread coverage of concurrent dispatch lives in
    test_presence_authority_dispatch.py."""
    ledger = SessionLedger()
    cursor = ContinuityCursorTracker()
    builder = ContinuityContextBuilder()

    a_req = ledger.append(SESSION_ID, "dragon_2d", "request", "player", "A says hi")
    b_req = ledger.append(SESSION_ID, "dragon_3d", "request", "player", "B says hi")
    assert (a_req.turn_id, b_req.turn_id) == (0, 1)

    # step 4, as handle_turn() itself computes it: everything strictly
    # before this call's own just-appended request.
    a_context = [t for t in ledger.read_since(SESSION_ID, since_turn_id=-1) if t.turn_id < a_req.turn_id]
    b_context = [t for t in ledger.read_since(SESSION_ID, since_turn_id=-1) if t.turn_id < b_req.turn_id]
    assert a_context == [], "B's concurrent request must not appear as prior context for A"
    assert [t.turn_id for t in b_context] == [0], "A's earlier request IS legitimate prior context for B"

    # B's real dispatch completes first. native-B has never seen anything
    # (last_seen_turn_id=-1), so A's earlier request — legitimate prior
    # context per b_context above — correctly gets recapped to B.
    b_dispatch_input = builder.build(b_context, "B says hi", cursor.last_seen_turn_id("claude_code", "native-B"))
    assert "A says hi" in b_dispatch_input
    assert "Now: B says hi" in b_dispatch_input
    b_resp = ledger.append(SESSION_ID, "dragon_3d", "response", "claude_code", "B-ack")
    cursor.advance("claude_code", "native-B", b_resp.turn_id)

    # A's real dispatch — built from a_context, computed BEFORE B's
    # request/response existed — finally completes.
    a_dispatch_input = builder.build(a_context, "A says hi", cursor.last_seen_turn_id("hermes", "native-A"))
    assert a_dispatch_input == "A says hi", "A's own recap must never see B's exchange — it didn't exist when A's context was read"
    a_resp = ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "A-ack")
    cursor.advance("hermes", "native-A", a_resp.turn_id)

    all_turns = ledger.read_since(SESSION_ID, since_turn_id=-1)
    assert [(t.turn_id, t.direction, t.origin_body) for t in all_turns] == [
        (0, "request", "dragon_2d"),
        (1, "request", "dragon_3d"),
        (2, "response", "dragon_3d"),
        (3, "response", "dragon_2d"),
    ], "A-req, B-req, B-resp, A-resp must be preserved exactly as it happened"

    # READ_LAST's own contract definition of recency (§6): the single
    # most recent matching turn, regardless of door — here, correctly,
    # A's response, even though B's whole exchange both started and
    # finished first.
    assert ledger.read_last(SESSION_ID, direction="response").origin_body == "dragon_2d"
