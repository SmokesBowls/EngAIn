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
from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger

SESSION_ID = "20260817_identity_boundary_test"


def _endpoint(provider_id: str, provider_session_id: str) -> str:
    return ProviderSessionBinding.encode_endpoint(
        provider_id=provider_id, model_id="m", provider_session_id=provider_session_id,
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
    bridge.handle_turn(SESSION_ID, "dragon_2d", "remember: copper rain")

    # Same actor label, but a different native session underneath.
    presence.register("hermes", "H-2", SESSION_ID, endpoint=_endpoint("hermes", "native-session-B"))
    bridge.handle_turn(SESSION_ID, "dragon_2d", "what did I say?")

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
    bridge.handle_turn(SESSION_ID, "dragon_2d", "remember: silver thread")

    presence.register("hermes", "H-1-renewed", SESSION_ID, endpoint=_endpoint("hermes", "replacement-session"))
    bridge.handle_turn(SESSION_ID, "dragon_2d", "what did I say?")

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

    bridge.handle_turn(SESSION_ID, "dragon_2d", "remember: copper rain")
    bridge.handle_turn(SESSION_ID, "dragon_3d", "still there?")  # same native session, different door

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
    bridge_hermes.handle_turn(SESSION_ID, "dragon_2d", "remember: copper rain")

    presence.register("claude_code", "CC-1", SESSION_ID, endpoint=_endpoint("claude_code", "session-B"))
    bridge_claude = SharedSessionBridge(presence, ledger, claude_dispatch, continuity_cursor_tracker=cursor)
    bridge_claude.handle_turn(SESSION_ID, "dragon_3d", "confirm the phrase")

    presence.register("hermes", "H-1-return", SESSION_ID, endpoint=_endpoint("hermes", "session-A"))
    bridge_hermes_2 = SharedSessionBridge(presence, ledger, hermes_dispatch, continuity_cursor_tracker=cursor)
    bridge_hermes_2.handle_turn(SESSION_ID, "dragon_2d", "what happened while I was away?")

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
    bridge_hermes.handle_turn(SESSION_ID, "dragon_2d", "first fact")
    bridge_hermes.handle_turn(SESSION_ID, "dragon_2d", "second fact")

    presence.register("claude_code", "CC-1", SESSION_ID, endpoint=_endpoint("claude_code", "brand-new-session"))
    bridge_claude = SharedSessionBridge(presence, ledger, _recording_dispatcher("claude_code", claude_calls), continuity_cursor_tracker=cursor)
    bridge_claude.handle_turn(SESSION_ID, "dragon_3d", "summarize everything")

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
        bridge.handle_turn(SESSION_ID, "dragon_2d", "hello")

    assert cursor.last_seen_turn_id("hermes", "flaky-session") == -1

    # A subsequent successful call to the same native session must still
    # recap the turn that was appended but never actually acknowledged.
    calls: list = []
    presence.register("hermes", "H-1-b", SESSION_ID, endpoint=_endpoint("hermes", "flaky-session"))
    bridge2 = SharedSessionBridge(presence, ledger, _recording_dispatcher("hermes", calls), continuity_cursor_tracker=cursor)
    bridge2.handle_turn(SESSION_ID, "dragon_2d", "are you there now?")

    assert "hello" in calls[0]
