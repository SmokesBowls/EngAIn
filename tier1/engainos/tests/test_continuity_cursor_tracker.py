from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker


def test_unknown_native_session_reads_as_negative_one():
    tracker = ContinuityCursorTracker()
    assert tracker.last_seen_turn_id("hermes", "some-native-session") == -1


def test_advance_then_read_back():
    tracker = ContinuityCursorTracker()
    tracker.advance("hermes", "session-a", 3)
    assert tracker.last_seen_turn_id("hermes", "session-a") == 3


def test_different_provider_session_pairs_are_tracked_independently():
    """The whole point: (provider_id, provider_session_id) is the key —
    not agent_id alone, and not provider_id alone."""
    tracker = ContinuityCursorTracker()
    tracker.advance("hermes", "session-a", 5)
    assert tracker.last_seen_turn_id("hermes", "session-b") == -1
    assert tracker.last_seen_turn_id("claude_code", "session-a") == -1
    assert tracker.last_seen_turn_id("hermes", "session-a") == 5


def test_advance_is_monotonic_and_never_moves_backward():
    tracker = ContinuityCursorTracker()
    tracker.advance("hermes", "session-a", 5)
    tracker.advance("hermes", "session-a", 2)  # out of order — must not regress
    assert tracker.last_seen_turn_id("hermes", "session-a") == 5
