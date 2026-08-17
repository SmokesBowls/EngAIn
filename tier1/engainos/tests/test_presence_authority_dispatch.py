"""
Real HTTP against a real (ephemeral-port) presence authority server's new
/dispatch endpoint — the avatar-integration boundary described in the
2026-08-17 receipt: a caller submits its own ProviderSessionBinding fields
plus a bare player_input, and gets back SharedSessionBridge.handle_turn()'s
own return shape, without ever importing SharedSessionBridge,
ContinuityCursorTracker, or ContinuityContextBuilder itself.

Dispatchers are swapped for deterministic fakes here (same discipline as
shared_session_bridge's own offline tests) — HermesDispatchError et al. are
real exception types raised by real code paths, but no real subprocess or
network call happens in this file. The live proof
(live_avatar_continuity_integration_proof.py) is what exercises this same
endpoint against real Hermes/Claude Code CLIs through the real dragon2d/
dragon3d worker code.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.bridgeroom.hermes_provider_adapter import HermesDispatchError
from tier1.engainos.core.continuity_cursor_tracker import ContinuityCursorTracker
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.session_claim_registry import SessionClaimRegistry
from tier1.engainos.core.session_ledger import SessionLedger
from tier1.engainos.server import presence_authority_server as authority_module
from tier1.engainos.server.presence_authority_server import PresenceAuthorityHandler


def _fake_dispatcher(actor: str, response_of: Any = None):
    def dispatch(binding, context, player_input):
        text = response_of(binding, context, player_input) if callable(response_of) else f"{actor}: {player_input}"
        return {"actor": actor, "response": text}
    return dispatch


@pytest.fixture()
def live_authority():
    authority_module.presence = PresenceRegistry()
    authority_module.claims = SessionClaimRegistry()
    authority_module.ledger = SessionLedger()
    authority_module.cursor = ContinuityCursorTracker()
    authority_module._PROVIDER_DISPATCHERS = {
        "hermes": _fake_dispatcher("hermes"),
        "claude_code": _fake_dispatcher("claude_code"),
    }

    server = ThreadingHTTPServer(("127.0.0.1", 0), PresenceAuthorityHandler)
    server.daemon_threads = True
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _post(base_url: str, path: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(base_url + path, data=data, method="POST",
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _hermes_body(**overrides: Any) -> Dict[str, Any]:
    body = {
        "shared_session_id": "shared-dispatch-test",
        "origin_body": "dragon_2d",
        "player_input": "hello",
        "provider_id": "hermes",
        "model_id": "gpt-5.6-sol",
        "provider_session_id": "hermes-native-1",
    }
    body.update(overrides)
    return body


def test_missing_required_field_is_400(live_authority):
    body = _hermes_body()
    del body["provider_session_id"]
    status, resp = _post(live_authority, "/dispatch", body)
    assert status == 400
    assert resp["error"] == "MISSING_FIELDS"
    assert "provider_session_id" in resp["fields"]


def test_unknown_provider_is_400(live_authority):
    status, resp = _post(live_authority, "/dispatch", _hermes_body(provider_id="carrier_pigeon"))
    assert status == 400
    assert resp["error"] == "UNKNOWN_PROVIDER"
    assert resp["known_providers"] == ["claude_code", "hermes"]


def test_basic_dispatch_returns_handle_turn_shape(live_authority):
    status, resp = _post(live_authority, "/dispatch", _hermes_body())
    assert status == 200
    assert resp["session_id"] == "shared-dispatch-test"
    assert resp["origin_body"] == "dragon_2d"
    assert resp["actor"] == "hermes"
    assert resp["response"] == "hermes: hello"
    assert isinstance(resp["turn_id"], int)


def test_second_turn_same_native_session_gets_no_recap(live_authority):
    """Same provider_session_id across two calls -> no missing turns ->
    ContinuityContextBuilder passes player_input through bare."""
    seen: List[str] = []

    def echo_capture(binding, context, player_input):
        seen.append(player_input)
        return player_input

    authority_module._PROVIDER_DISPATCHERS["hermes"] = _fake_dispatcher("hermes", echo_capture)

    _post(live_authority, "/dispatch", _hermes_body(player_input="first"))
    _post(live_authority, "/dispatch", _hermes_body(player_input="second"))
    assert seen == ["first", "second"]


def test_switch_provider_then_switch_back_recaps_only_missed_turn(live_authority):
    """dragon2d (hermes native A) -> switch to claude_code -> switch back
    to hermes native A: the return dispatch must recap exactly the
    intervening claude_code turn, not the whole history, and not nothing."""
    captured: List[str] = []

    def hermes_reply(binding, context, player_input):
        captured.append(player_input)
        return "hermes-ack"

    def claude_reply(binding, context, player_input):
        captured.append(player_input)
        return "claude-ack"

    authority_module._PROVIDER_DISPATCHERS["hermes"] = _fake_dispatcher("hermes", hermes_reply)
    authority_module._PROVIDER_DISPATCHERS["claude_code"] = _fake_dispatcher("claude_code", claude_reply)

    status, first = _post(live_authority, "/dispatch", _hermes_body(
        player_input="remember: violet key",
    ))
    assert status == 200

    status, second = _post(live_authority, "/dispatch", _hermes_body(
        provider_id="claude_code", model_id="claude-x", provider_session_id="claude-native-1",
        origin_body="dragon_3d", player_input="what did I ask you to remember?",
    ))
    assert status == 200

    status, third = _post(live_authority, "/dispatch", _hermes_body(
        player_input="what did the other assistant say?",
    ))
    assert status == 200

    # claude-native-1 has never seen turns 0/1 (they happened on hermes-A) -> recapped
    assert "remember: violet key" in captured[1]
    assert "hermes-ack" in captured[1]
    assert "what did I ask you to remember?" in captured[1]  # the "Now:" line

    # hermes-native-1's own cursor is at turn1 -> missing exactly turns 2/3
    assert "what did I ask you to remember?" in captured[2]  # turn2's recap
    assert "claude-ack" in captured[2]  # turn3's recap
    assert "remember: violet key" not in captured[2]  # already native to hermes-A
    assert "hermes-ack" not in captured[2]  # already native to hermes-A
    assert "what did the other assistant say?" in captured[2]  # the "Now:" line


def test_dispatch_failure_is_502(live_authority):
    def boom(binding, context, player_input):
        raise HermesDispatchError("simulated CLI failure")

    authority_module._PROVIDER_DISPATCHERS["hermes"] = boom
    status, resp = _post(live_authority, "/dispatch", _hermes_body())
    assert status == 502
    assert resp["error"] == "PROVIDER_DISPATCH_FAILED"


def test_response_actor_mismatch_is_409(live_authority):
    def wrong_actor(binding, context, player_input):
        return {"actor": "not-the-registered-agent", "response": "x"}

    authority_module._PROVIDER_DISPATCHERS["hermes"] = wrong_actor
    status, resp = _post(live_authority, "/dispatch", _hermes_body())
    assert status == 409
    assert resp["error"] == "RESPONSE_ACTOR_MISMATCH"
