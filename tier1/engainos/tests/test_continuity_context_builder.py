"""
Pure ContinuityContextBuilder tests: given context, player_input, and a
last_seen_turn_id (the ContinuityCursorTracker's answer for one specific
native session — see that module), does build() recap exactly the right
turns? No actor comparison anywhere — that was the bug this version fixes.
Bridge-level tests for how last_seen_turn_id itself gets computed and
advanced live in test_continuity_identity_boundary.py.
"""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.core.continuity_context_builder import ContinuityContextBuilder
from tier1.engainos.core.session_ledger import SessionLedger

SESSION_ID = "20260817_builder_test"


def _ledger_with_hermes_turn() -> list:
    ledger = SessionLedger()
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "remember: copper rain")
    ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "noted.")
    return ledger.read_since(SESSION_ID, since_turn_id=-1)


def test_first_turn_with_no_context_is_passed_through_unmodified():
    builder = ContinuityContextBuilder()
    result = builder.build(context=[], player_input="hello?", last_seen_turn_id=-1)
    assert result == "hello?"


def test_last_seen_covering_all_context_gets_no_recap():
    """The corrected rule: what matters is whether this cursor value
    already covers everything in context — not any actor comparison."""
    context = _ledger_with_hermes_turn()
    builder = ContinuityContextBuilder()
    # last_seen_turn_id=1 covers both turn 0 and turn 1 (the whole context).
    result = builder.build(context=context, player_input="what did I just say?", last_seen_turn_id=1)
    assert result == "what did I just say?"


def test_last_seen_below_context_gets_a_recap_of_the_missing_turns():
    context = _ledger_with_hermes_turn()
    builder = ContinuityContextBuilder()
    result = builder.build(context=context, player_input="what did I just say?", last_seen_turn_id=-1)

    assert result != "what did I just say?"
    assert "remember: copper rain" in result
    assert "noted." in result
    assert "hermes" in result  # names which provider produced the recapped turn
    assert result.endswith("Now: what did I just say?")


def test_coordination_report_is_labeled_and_never_merged_into_player_input():
    """coordination_report is carried separately from player_input (see
    SharedSessionBridge.handle_turn()'s own parameter of the same name) —
    it must appear as its own labeled block, and player_input's own text
    must appear byte-for-byte, never rewritten to include report content."""
    builder = ContinuityContextBuilder()
    report = {"status": "applied", "execution_summary": "Modified 1 file(s)."}
    result = builder.build(
        context=[], player_input="what happened?", last_seen_turn_id=-1, coordination_report=report
    )
    assert result != "what happened?"
    assert "status: applied" in result
    assert "Modified 1 file(s)." in result
    assert "not something the player said" in result
    assert result.endswith("Now: what happened?")


def test_coordination_report_absent_matches_old_behavior_exactly():
    """Regression pin: omitting coordination_report (its default) must
    leave every pre-existing case byte-for-byte unchanged."""
    builder = ContinuityContextBuilder()
    assert builder.build(context=[], player_input="hello?", last_seen_turn_id=-1) == "hello?"


def test_coordination_report_and_missing_context_recap_combine_without_dropping_either():
    context = _ledger_with_hermes_turn()
    builder = ContinuityContextBuilder()
    report = {"status": "failed", "execution_summary": "", "body": "hermes exited 1"}
    result = builder.build(
        context=context,
        player_input="what did I just say?",
        last_seen_turn_id=-1,
        coordination_report=report,
    )
    assert "status: failed" in result
    assert "hermes exited 1" in result  # falls back to body when execution_summary is empty
    assert "remember: copper rain" in result  # the missing-context recap is still present
    assert "noted." in result
    assert result.endswith("Now: what did I just say?")


def test_recap_includes_only_turns_strictly_after_last_seen():
    """Not "all of context" once any recap is warranted — only the
    genuinely missing suffix. This is what makes 'recap only the turns it
    missed' possible instead of always recapping from the beginning."""
    ledger = SessionLedger()
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "first thing")
    ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "first reply")
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "second thing")
    ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "second reply")
    context = ledger.read_since(SESSION_ID, since_turn_id=-1)

    builder = ContinuityContextBuilder()
    # last_seen_turn_id=1 means turns 0 and 1 ("first thing"/"first reply")
    # were already seen by this native session; only 2 and 3 are missing.
    result = builder.build(context=context, player_input="summarize", last_seen_turn_id=1)

    assert "first thing" not in result
    assert "first reply" not in result
    assert "second thing" in result
    assert "second reply" in result
