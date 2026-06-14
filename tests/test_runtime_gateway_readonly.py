import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GODOTSIM = os.path.join(ROOT, "godotsim")
CORE = os.path.join(ROOT, "godotengain", "engainos", "core")
for path in (ROOT, GODOTSIM, CORE):
    if path not in sys.path:
        sys.path.insert(0, path)

from reality_mode import RealityMode, set_mode
from runtime_gateway import RuntimeGateway


class FakeRuntime:
    def __init__(self):
        self.snapshot = {"scene_id": "draft_scene"}


class RecordingDispatcher:
    def __init__(self):
        self.seen = []

    def dispatch(self, raw_input):
        self.seen.append(raw_input)
        return {"type": "result", "text": "dispatched"}


def make_gateway():
    dispatcher = RecordingDispatcher()
    gateway = RuntimeGateway(FakeRuntime(), dispatcher)
    return gateway, dispatcher


def test_legacy_entities_command_is_read_only_without_mutation_identity():
    set_mode(RealityMode.DRAFT)
    gateway, dispatcher = make_gateway()

    decision = gateway.submit({"command": "entities"})

    assert decision.accepted is True
    assert decision.result == {"type": "result", "text": "dispatched"}
    assert dispatcher.seen == [{"command": "entities"}]


def test_legacy_text_segments_command_is_read_only_without_mutation_identity():
    set_mode(RealityMode.DRAFT)
    gateway, dispatcher = make_gateway()

    decision = gateway.submit({"text": "segments"})

    assert decision.accepted is True
    assert dispatcher.seen == [{"text": "segments"}]


def test_generic_command_shape_is_subclassified_by_text_not_allowed_generically():
    set_mode(RealityMode.DRAFT)
    gateway, dispatcher = make_gateway()

    decision = gateway.submit({"action": "command", "text": "entities"})

    assert decision.accepted is True
    assert dispatcher.seen == [{"action": "command", "text": "entities"}]


def test_unknown_legacy_command_still_requires_mutation_identity():
    set_mode(RealityMode.DRAFT)
    gateway, dispatcher = make_gateway()

    decision = gateway.submit({"command": "teleport_everyone"})

    assert decision.accepted is False
    assert decision.status_code == 400
    assert "Missing required mutation identity fields" in decision.reason
    assert dispatcher.seen == []


def test_read_only_command_is_allowed_in_replay_mode():
    set_mode(RealityMode.REPLAY)
    try:
        gateway, dispatcher = make_gateway()

        decision = gateway.submit({"command": "entities"})

        assert decision.accepted is True
        assert dispatcher.seen == [{"command": "entities"}]
    finally:
        set_mode(RealityMode.DRAFT)
