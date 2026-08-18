from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.bridgeroom.mailbox_request_handler import (
    MailboxRequestError,
    handle_mailbox_request,
)
from tier1.engainos.bridgeroom.shared_session_bridge import SharedSessionBridge
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.provider_session_binding import ProviderSessionBinding
from tier1.engainos.core.session_ledger import SessionLedger

SESSION_ID = "20260817_mailbox_test"
TEST_ENDPOINT = ProviderSessionBinding.encode_endpoint(
    provider_id="hermes", model_id="test-model", provider_session_id="provider-native-x"
)
# handle_mailbox_request() now requires an explicit binding, matching
# handle_turn()'s own required-parameter contract (item 1) — see
# mailbox_request_handler.py's module docstring.
TEST_BINDING = ProviderSessionBinding(
    provider_id="hermes",
    model_id="test-model",
    provider_session_id="provider-native-x",
    agent_id="hermes",
    instance_id="H-1",
    shared_session_id=SESSION_ID,
    launch_options={},
)


def _bridge_with_registered_hermes() -> SharedSessionBridge:
    presence = PresenceRegistry()
    presence.register("hermes", "H-1", SESSION_ID, ["chat"], endpoint=TEST_ENDPOINT)
    return SharedSessionBridge(presence=presence, ledger=SessionLedger())


def test_real_request_file_produces_a_real_response_file(tmp_path: Path):
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    request_path.write_text(json.dumps({
        "shared_session_id": SESSION_ID,
        "origin_body": "dragon_2d",
        "player_input": "hello?",
    }))

    bridge = _bridge_with_registered_hermes()
    result = handle_mailbox_request(request_path, response_path, bridge, TEST_BINDING)

    assert response_path.exists()
    on_disk = json.loads(response_path.read_text())
    assert on_disk == result
    assert result["actor"] == "hermes"
    assert result["origin_body"] == "dragon_2d"


def test_the_ledger_records_the_bare_request_with_no_manually_constructed_recap(tmp_path: Path):
    """The point of this whole layer: a caller writes a plain request file
    with no recap text of its own, and the Ledger's own request turn is
    exactly that bare text — any continuity handling happens inside the
    bridge, not because this handler or its caller pre-authored anything."""
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    bare_input = "what did I just say?"
    request_path.write_text(json.dumps({
        "shared_session_id": SESSION_ID,
        "origin_body": "dragon_3d",
        "player_input": bare_input,
    }))

    presence = PresenceRegistry()
    presence.register("hermes", "H-1", SESSION_ID, ["chat"], endpoint=TEST_ENDPOINT)
    ledger = SessionLedger()
    bridge = SharedSessionBridge(presence=presence, ledger=ledger)

    handle_mailbox_request(request_path, response_path, bridge, TEST_BINDING)

    recorded_request = ledger.read_last(SESSION_ID, direction="request")
    assert recorded_request.payload == bare_input


def test_missing_required_field_raises_mailbox_request_error(tmp_path: Path):
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    request_path.write_text(json.dumps({"shared_session_id": SESSION_ID, "origin_body": "dragon_2d"}))
    # player_input missing

    bridge = _bridge_with_registered_hermes()
    with pytest.raises(MailboxRequestError, match="player_input"):
        handle_mailbox_request(request_path, response_path, bridge, TEST_BINDING)

    assert not response_path.exists()


def test_malformed_json_raises_mailbox_request_error(tmp_path: Path):
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    request_path.write_text("{not valid json")

    bridge = _bridge_with_registered_hermes()
    with pytest.raises(MailboxRequestError, match="not valid JSON"):
        handle_mailbox_request(request_path, response_path, bridge, TEST_BINDING)


def test_response_directory_is_created_if_it_does_not_exist(tmp_path: Path):
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "nested" / "dir" / "response.json"
    request_path.write_text(json.dumps({
        "shared_session_id": SESSION_ID, "origin_body": "dragon_2d", "player_input": "hi",
    }))

    bridge = _bridge_with_registered_hermes()
    handle_mailbox_request(request_path, response_path, bridge, TEST_BINDING)

    assert response_path.exists()
