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


# --- Item 1: concurrent-/dispatch mutex --------------------------------
#
# Real HTTP, real threads, against the same live_authority fixture above —
# matching this file's own existing discipline (deterministic fakes, no
# real subprocess/network calls, but genuine concurrency via real OS
# threads, not simulated).

def _blocking_dispatcher(actor: str, entered: threading.Event, release: threading.Event):
    """Lets a test hold a dispatch open exactly as long as it needs to, so
    a second, concurrent request can be sent while the first is
    provably still inside the provider call — never relying on sleep."""
    def dispatch(binding, context, player_input):
        entered.set()
        assert release.wait(timeout=5), "test never released the blocked dispatcher"
        return {"actor": actor, "response": f"{actor}: {player_input}"}
    return dispatch


def test_dispatch_busy_when_same_provider_and_provider_session_contended(live_authority):
    """Case 1 of the design note's three-way comparison: same
    (provider_id, provider_session_id) must serialize."""
    entered = threading.Event()
    release = threading.Event()
    authority_module._PROVIDER_DISPATCHERS["hermes"] = _blocking_dispatcher("hermes", entered, release)

    results: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def send_a():
        results["a"] = _post(live_authority, "/dispatch", _hermes_body(player_input="from A"))

    t = threading.Thread(target=send_a)
    t.start()
    assert entered.wait(timeout=5), "first dispatch never entered the provider call"

    status_b, resp_b = _post(live_authority, "/dispatch", _hermes_body(player_input="from B", instance_id="req-b"))
    assert status_b == 409
    assert resp_b["error"] == "DISPATCH_BUSY"
    assert resp_b["provider_id"] == "hermes"
    assert resp_b["provider_session_id"] == "hermes-native-1"

    release.set()
    t.join(timeout=5)
    assert results["a"][0] == 200


def test_same_provider_different_provider_sessions_dispatch_concurrently(live_authority):
    """Case 2: same provider, different provider_session_id — must not
    contend with each other (provider_id alone would be too coarse a key)."""
    results: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def send(label: str, provider_session_id: str) -> None:
        results[label] = _post(live_authority, "/dispatch", _hermes_body(
            provider_session_id=provider_session_id, player_input=label,
        ))

    t1 = threading.Thread(target=send, args=("a", "hermes-native-1"))
    t2 = threading.Thread(target=send, args=("b", "hermes-native-2"))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert results["a"][0] == 200
    assert results["b"][0] == 200


def test_different_providers_same_textual_session_id_dispatch_concurrently(live_authority):
    """Case 3: session_id "123" colliding as text across two different
    providers names two unrelated native transcripts — must not contend
    (bare session_id alone would be too coarse a key)."""
    results: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def send(label: str, provider_id: str, model_id: str) -> None:
        results[label] = _post(live_authority, "/dispatch", _hermes_body(
            provider_id=provider_id, model_id=model_id, provider_session_id="123", player_input=label,
        ))

    t1 = threading.Thread(target=send, args=("a", "hermes", "gpt-5.6-sol"))
    t2 = threading.Thread(target=send, args=("b", "claude_code", "claude-x"))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert results["a"][0] == 200
    assert results["b"][0] == 200


def test_same_declared_caller_still_contends_because_claim_owner_is_fresh(live_authority):
    """Two requests declaring the identical agent_id/instance_id (as a
    single misbehaving or retrying caller might) must still correctly
    contend — the claim's own owner identity is a UUID minted fresh per
    /dispatch call, never copied from the body, precisely so this case
    cannot be mistaken for the same caller reentrantly refreshing its own
    claim (design note §6)."""
    entered = threading.Event()
    release = threading.Event()
    # actor matches the overridden agent_id below, so step 6's (pre-
    # existing, unrelated) response-actor check passes once A resumes —
    # this test is only about the claim, not that separate gate.
    authority_module._PROVIDER_DISPATCHERS["hermes"] = _blocking_dispatcher("dragon_2d", entered, release)

    results: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def send_a():
        results["a"] = _post(live_authority, "/dispatch", _hermes_body(
            agent_id="dragon_2d", instance_id="dragon-worker", player_input="from A",
        ))

    t = threading.Thread(target=send_a)
    t.start()
    assert entered.wait(timeout=5)

    status_b, resp_b = _post(live_authority, "/dispatch", _hermes_body(
        agent_id="dragon_2d", instance_id="dragon-worker", player_input="from B",
    ))
    assert status_b == 409
    assert resp_b["error"] == "DISPATCH_BUSY"

    release.set()
    t.join(timeout=5)
    assert results["a"][0] == 200


def test_claim_released_after_successful_dispatch(live_authority):
    status1, _ = _post(live_authority, "/dispatch", _hermes_body(player_input="first"))
    assert status1 == 200
    # Same (provider_id, provider_session_id) as the first call — only
    # succeeds if the first call's claim was actually released.
    status2, _ = _post(live_authority, "/dispatch", _hermes_body(player_input="second"))
    assert status2 == 200


def test_claim_released_after_dispatch_failure(live_authority):
    def boom(binding, context, player_input):
        raise HermesDispatchError("simulated CLI failure")

    authority_module._PROVIDER_DISPATCHERS["hermes"] = boom
    status1, resp1 = _post(live_authority, "/dispatch", _hermes_body(player_input="first"))
    assert status1 == 502
    assert resp1["error"] == "PROVIDER_DISPATCH_FAILED"

    authority_module._PROVIDER_DISPATCHERS["hermes"] = _fake_dispatcher("hermes")
    status2, _ = _post(live_authority, "/dispatch", _hermes_body(player_input="second"))
    assert status2 == 200


def test_presence_overwrite_during_dispatch_does_not_redirect_either_caller(live_authority):
    """The regression test for the corrected design (item 1 design note
    §9, amendment to the original §8a). Forces the exact interleaving
    that broke the first draft, deterministically via real synchronization
    primitives rather than sleep:

        A claims (hermes, native-A-123)
        B claims (claude_code, native-B-456)
        A registers Presence for the shared shared_session_id
        B overwrites that same Presence record (different provider)
        A continues
        B continues

    and proves each caller's dispatcher still receives its OWN originally
    requested (provider_id, provider_session_id) — never the other's —
    despite the overwrite landing squarely between A's claim and A's
    dispatch."""
    real_register = authority_module.presence.register
    a_registered = threading.Event()
    b_registered = threading.Event()

    def synced_register(*, agent_id, instance_id, session_id, capabilities=None, endpoint=None, requested_lease=300.0):
        if instance_id == "req-b":
            # B's real register (the overwrite) must not happen until
            # A's own real register has already completed.
            assert a_registered.wait(timeout=5), "A never registered — synchronization broken"
        record = real_register(
            agent_id=agent_id, instance_id=instance_id, session_id=session_id,
            capabilities=capabilities, endpoint=endpoint, requested_lease=requested_lease,
        )
        if instance_id == "req-a":
            a_registered.set()
            # A must not proceed into handle_turn() until B has overwritten
            # Presence — this is the exact worst-case ordering from the
            # design note's trace.
            assert b_registered.wait(timeout=5), "B never registered — synchronization broken"
        elif instance_id == "req-b":
            b_registered.set()
        return record

    authority_module.presence.register = synced_register

    received: Dict[str, Tuple[str, str]] = {}

    def make_recording_dispatcher(label: str):
        def dispatch(binding, context, player_input):
            received[label] = (binding.provider_id, binding.provider_session_id)
            return {"actor": binding.agent_id, "response": f"{label}-ack"}
        return dispatch

    authority_module._PROVIDER_DISPATCHERS["hermes"] = make_recording_dispatcher("A")
    authority_module._PROVIDER_DISPATCHERS["claude_code"] = make_recording_dispatcher("B")

    shared_session_id = "shared-presence-overwrite-race"
    results: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def send_a():
        results["a"] = _post(live_authority, "/dispatch", {
            "shared_session_id": shared_session_id, "origin_body": "dragon_2d",
            "player_input": "hi from A", "provider_id": "hermes",
            "model_id": "gpt-5.6-sol", "provider_session_id": "native-A-123",
            "agent_id": "hermes", "instance_id": "req-a",
        })

    def send_b():
        results["b"] = _post(live_authority, "/dispatch", {
            "shared_session_id": shared_session_id, "origin_body": "dragon_3d",
            "player_input": "hi from B", "provider_id": "claude_code",
            "model_id": "claude-x", "provider_session_id": "native-B-456",
            "agent_id": "claude_code", "instance_id": "req-b",
        })

    t_a = threading.Thread(target=send_a)
    t_b = threading.Thread(target=send_b)
    t_a.start()
    t_b.start()
    t_a.join(timeout=10)
    t_b.join(timeout=10)

    assert a_registered.is_set() and b_registered.is_set(), "synchronized interleaving never completed"
    # The actual regression proof: each dispatcher was invoked with
    # exactly its own caller's binding, never the other's — this is
    # decided at dispatch time, before step 6 ever runs, so it holds
    # regardless of either call's eventual HTTP status.
    assert received["A"] == ("hermes", "native-A-123")
    assert received["B"] == ("claude_code", "native-B-456")


def test_ledger_lock_does_not_serialize_behind_a_slow_concurrent_dispatch(live_authority):
    """Item 2's per-shared_session_id Ledger lock (SessionLedger.append())
    must never be held across a provider call — it's scoped tightly
    around turn_id assignment + insertion alone. Proves it against the
    real, running server: while caller A's real dispatch is blocked in
    flight (holding item 1's claim on its own native session), caller B
    — a DIFFERENT (provider_id, provider_session_id), same
    shared_session_id — must be able to append its request, dispatch,
    and append its response, all while A is still blocked. If the Ledger
    lock had accidentally grown to span handle_turn()'s dispatch call,
    B would hang here until A's release fires."""
    entered = threading.Event()
    release = threading.Event()
    authority_module._PROVIDER_DISPATCHERS["hermes"] = _blocking_dispatcher("hermes", entered, release)
    authority_module._PROVIDER_DISPATCHERS["claude_code"] = _fake_dispatcher("claude_code")

    shared_session_id = "shared-ledger-lock-no-serialize"
    results: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def send_a():
        results["a"] = _post(live_authority, "/dispatch", {
            "shared_session_id": shared_session_id, "origin_body": "dragon_2d",
            "player_input": "from A", "provider_id": "hermes",
            "model_id": "gpt-5.6-sol", "provider_session_id": "native-A",
        })

    t = threading.Thread(target=send_a)
    t.start()
    assert entered.wait(timeout=5), "A never entered its blocking dispatch"

    status_b, resp_b = _post(live_authority, "/dispatch", {
        "shared_session_id": shared_session_id, "origin_body": "dragon_3d",
        "player_input": "from B", "provider_id": "claude_code",
        "model_id": "claude-x", "provider_session_id": "native-B",
    })
    # The actual proof: B completed (didn't hang behind A's still-open
    # dispatch) — status alone would be ambiguous if this line had
    # blocked for seconds instead of returning immediately, so what
    # matters here is that execution reached this point at all while A
    # is still inside its blocking dispatcher.
    assert status_b == 200, resp_b

    release.set()
    t.join(timeout=5)
    assert "a" in results, "A's call never returned — release() failed to unblock it"
    # A's own status is governed by the same pre-existing, unrelated
    # Gate 11 (response-actor authorization) item 1's own regression test
    # already documents: both calls share one shared_session_id, and B's
    # registration (which could only happen after A's, since B's request
    # was sent only after A confirmed it had already entered its blocking
    # dispatch) means Presence reports "claude_code" ACTIVE by the time
    # A's own response is validated — deterministically rejected as
    # stale. Not a defect, and not what this test is checking — that's
    # B's timing above, which is the actual proof.
    assert results["a"][0] == 409, results["a"]
    assert results["a"][1]["error"] == "RESPONSE_ACTOR_MISMATCH"
