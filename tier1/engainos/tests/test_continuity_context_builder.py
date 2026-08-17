from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.core.continuity_context_builder import ContinuityContextBuilder
from tier1.engainos.core.session_ledger import SessionLedger

SESSION_ID = "20260817_builder_test"


def _ledger_with_hermes_turn() -> tuple[SessionLedger, list]:
    ledger = SessionLedger()
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "remember: copper rain")
    ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "noted.")
    return ledger, ledger.read_since(SESSION_ID, since_turn_id=-1)


def test_first_turn_with_no_context_is_passed_through_unmodified():
    builder = ContinuityContextBuilder()
    result = builder.build(context=[], player_input="hello?", target_agent_id="hermes")
    assert result == "hello?"


def test_same_provider_continuing_gets_no_recap():
    """The rule this exists to enforce: a provider resuming its own prior
    turn already has that memory natively via --resume. Injecting a recap
    anyway would be the second, competing memory the adapters forbid."""
    _ledger, context = _ledger_with_hermes_turn()
    builder = ContinuityContextBuilder()
    result = builder.build(context=context, player_input="what did I just say?", target_agent_id="hermes")
    assert result == "what did I just say?"


def test_provider_switch_gets_a_recap_containing_the_prior_exchange():
    _ledger, context = _ledger_with_hermes_turn()
    builder = ContinuityContextBuilder()
    result = builder.build(context=context, player_input="what did I just say?", target_agent_id="claude_code")

    assert result != "what did I just say?"
    assert "remember: copper rain" in result
    assert "noted." in result
    assert "hermes" in result  # names which provider produced the recapped turn
    assert result.endswith("Now: what did I just say?")


def test_recap_includes_every_turn_in_context_not_just_the_last_pair():
    ledger = SessionLedger()
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "first thing")
    ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "first reply")
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "second thing")
    ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "second reply")
    context = ledger.read_since(SESSION_ID, since_turn_id=-1)

    builder = ContinuityContextBuilder()
    result = builder.build(context=context, player_input="summarize", target_agent_id="claude_code")

    assert "first thing" in result
    assert "first reply" in result
    assert "second thing" in result
    assert "second reply" in result


def test_switching_back_to_the_original_provider_recaps_the_intervening_switch():
    """Mirrors the live proof's decisive step: hermes -> claude_code ->
    hermes again must still get a recap, even though hermes was the
    provider two turns ago — what matters is who produced the *most
    recent* response, not provider history further back."""
    ledger = SessionLedger()
    ledger.append(SESSION_ID, "dragon_2d", "request", "player", "remember: copper rain")
    ledger.append(SESSION_ID, "dragon_2d", "response", "hermes", "noted.")
    ledger.append(SESSION_ID, "dragon_3d", "request", "player", "what did I say?")
    ledger.append(SESSION_ID, "dragon_3d", "response", "claude_code", "copper rain")
    context = ledger.read_since(SESSION_ID, since_turn_id=-1)

    builder = ContinuityContextBuilder()
    result = builder.build(context=context, player_input="confirm the phrase", target_agent_id="hermes")

    assert result != "confirm the phrase"
    assert "copper rain" in result
    assert "claude_code" in result
