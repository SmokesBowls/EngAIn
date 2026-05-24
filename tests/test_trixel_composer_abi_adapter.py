import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixelcomposer.composer_abi_adapter import (
    EnhancedTrixelComposerAdapter,
    EmpireBridgeProposalAdapter,
    TerminalTrixelComposerAdapter,
)


class FakeTerminalAction:
    def __init__(self, tool="brush", x=1, y=2, color=(3, 4, 5), pressure=0.75, reasoning="legacy"):
        self.tool = tool
        self.x = x
        self.y = y
        self.color = color
        self.pressure = pressure
        self.reasoning = reasoning
        self.timestamp = 123.0
        self.artistic_success = 0.5


class FakeTerminalComposer:
    def __init__(self):
        self.session_id = "terminal-test"
        self.executed = []
        self.saved = False
        self.canvas = type("Canvas", (), {"canvas": [[[0, 0, 0]]]})()

    def perceive(self):
        return {"canvas_stats": {"completion": 0.1}, "memory_state": {"preferred_tool": "brush"}}

    def plan_action(self, perception):
        assert perception["canvas_stats"]["completion"] == 0.1
        return FakeTerminalAction(tool="brush")

    def execute_action(self, action):
        self.executed.append(action)
        return 0.8

    def save_session(self):
        self.saved = True


class FakeEnhancedComposer:
    def __init__(self):
        self.session_id = "enhanced-test"
        self.executed = []
        self.persisted = False
        self.canvas = [[[0, 0, 0]]]

    def perceive(self):
        return {"canvas": self.canvas, "tool": "brush", "memory_context": {}}

    async def _autonomous_plan(self, perception):
        assert perception["tool"] == "brush"
        return {"tool": "fill", "x": 2, "y": 3, "color": (9, 8, 7), "pressure": 0.6, "reasoning": "async"}

    def _execute_action(self, action):
        self.executed.append(action)
        return 0.7

    def _save_autonomous_session(self):
        self.persisted = True


class ComposerThatMustNotBeActed:
    def __init__(self):
        self.session_id = "bridge-test"
        self.act_calls = 0

    def act(self, plan):
        self.act_calls += 1
        raise AssertionError("EmpireBridgeProposalAdapter must not execute composer.act()")


@pytest.mark.parametrize(
    "adapter",
    [
        TerminalTrixelComposerAdapter(FakeTerminalComposer()),
        EnhancedTrixelComposerAdapter(FakeEnhancedComposer()),
    ],
)
def test_composer_adapters_expose_required_abi_methods(adapter):
    for method_name in ("perceive", "plan", "act", "persist"):
        assert callable(getattr(adapter, method_name))


def test_terminal_adapter_plan_is_proposed_and_act_returns_act_result_envelope():
    adapter = TerminalTrixelComposerAdapter(FakeTerminalComposer())

    plan = adapter.plan()
    assert plan["schema_version"] == "trixel_composer_plan.v1"
    assert plan["authority_level"] == "editor_only"
    assert plan["authoritative"] is False
    assert plan["artifact_kind"] == "editor_action_plan"
    assert plan["source"] == "terminal_trixel"
    assert plan["session_id"] == "terminal-test"
    assert plan["status"] == "proposed"
    assert plan["action"]["tool"] == "brush"
    assert "legacy_payload" in plan

    result = adapter.act(plan)
    assert result["schema_version"] == "trixel_composer_act_result.v1"
    assert result["authority_level"] == "editor_only"
    assert result["authoritative"] is False
    assert result["artifact_kind"] == "editor_action_result"
    assert result["source"] == "terminal_trixel"
    assert result["session_id"] == "terminal-test"
    assert result["status"] == "applied"
    assert result["applied_action"]["tool"] == "brush"
    assert "deterministic_seed" in result or result["status"] == "non_deterministic"


def test_enhanced_adapter_handles_async_autonomous_plan_safely_and_acts():
    adapter = EnhancedTrixelComposerAdapter(FakeEnhancedComposer())

    plan = adapter.plan()
    assert plan["schema_version"] == "trixel_composer_plan.v1"
    assert plan["status"] == "proposed"
    assert plan["source"] == "enhanced_trixel_core"
    assert plan["session_id"] == "enhanced-test"
    assert plan["action"]["tool"] == "fill"
    assert "legacy_payload" in plan

    result = adapter.act(plan)
    assert result["schema_version"] == "trixel_composer_act_result.v1"
    assert result["status"] == "applied"
    assert result["applied_action"]["tool"] == "fill"


def test_empire_bridge_adapter_returns_proposal_only_never_calls_composer_act_and_normalizes_action_to_tool():
    composer = ComposerThatMustNotBeActed()
    adapter = EmpireBridgeProposalAdapter(composer=composer, session_id="bridge-session")
    legacy_suggestion = {
        "!zw/art.action": {
            "tool": "brush",
            "x": 4,
            "y": 5,
            "color": [1, 2, 3],
            "reasoning": "paint here",
        }
    }

    proposal = adapter.normalize_ai_suggestion(legacy_suggestion)

    assert composer.act_calls == 0
    assert proposal["schema_version"] == "trixel_ai_suggestion.v1"
    assert proposal["authority_level"] == "editor_only"
    assert proposal["authoritative"] is False
    assert proposal["artifact_kind"] == "ai_suggestion"
    assert proposal["source"] == "empire_bridge"
    assert proposal["session_id"] == "bridge-session"
    assert proposal["status"] == "proposed"
    assert proposal["plan"]["schema_version"] == "trixel_composer_plan.v1"
    assert proposal["plan"]["status"] == "proposed"
    assert proposal["plan"]["action"]["tool"] == "brush"
    assert "action" not in proposal["plan"]["action"]
    assert proposal["plan"]["action"]["legacy_payload"]["tool"] == "brush"
    assert "legacy_payload" in proposal


def test_empire_bridge_adapter_normalizes_legacy_action_field_to_tool():
    adapter = EmpireBridgeProposalAdapter(composer=ComposerThatMustNotBeActed(), session_id="bridge-session")

    proposal = adapter.normalize_ai_suggestion({"action": "fill", "x": 6, "y": 7, "color": [8, 9, 10]})

    assert proposal["plan"]["action"]["tool"] == "fill"
    assert "action" not in proposal["plan"]["action"]
