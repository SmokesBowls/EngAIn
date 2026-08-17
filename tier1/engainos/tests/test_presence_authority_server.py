"""
Real HTTP against a real (locally bound, ephemeral-port) instance of the
presence authority server — not a mock, not an in-process object call.
This is the offline-but-real regression proof that the HTTP contract
behaves; the full live proof with two separate OS processes lives in
tier1/engainos/tools/live_presence_authority_race_proof.py.
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from http.server import ThreadingHTTPServer

from tier1.engainos.server import presence_authority_server as authority_module
from tier1.engainos.server.presence_authority_server import PresenceAuthorityHandler
from tier1.engainos.core.presence_registry import PresenceRegistry
from tier1.engainos.core.session_claim_registry import SessionClaimRegistry


@pytest.fixture()
def live_authority():
    """Binds a real socket on an OS-assigned ephemeral port, in a real
    background thread, with a fresh PresenceRegistry/SessionClaimRegistry
    swapped into the module (so tests don't share state across runs)."""
    authority_module.presence = PresenceRegistry()
    authority_module.claims = SessionClaimRegistry()

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


def _get(base_url: str, path: str) -> Tuple[int, Dict[str, Any]]:
    req = urllib.request.Request(base_url + path, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_health(live_authority):
    status, body = _get(live_authority, "/health")
    assert status == 200
    assert body["status"] == "healthy"


def test_register_then_resolve_round_trip(live_authority):
    status, body = _post(live_authority, "/presence/register", {
        "agent_id": "hermes",
        "instance_id": "worker-2d",
        "session_id": "shared-session-x",
        "capabilities": ["chat"],
        "endpoint": '{"provider": "openai-codex", "model": "gpt-5.6-sol"}',
        "requested_lease": 30.0,
    })
    assert status == 200
    assert body["agent_id"] == "hermes"

    status, body = _get(live_authority, "/presence/resolve?session_id=shared-session-x")
    assert status == 200
    assert body["instance_id"] == "worker-2d"


def test_resolve_unknown_session_is_404(live_authority):
    status, body = _get(live_authority, "/presence/resolve?session_id=nobody-here")
    assert status == 404
    assert body["error"] == "PROVIDER_NOT_REGISTERED"


def test_two_different_worker_processes_racing_for_one_claim(live_authority):
    """The actual point: two clients hitting the SAME server instance —
    standing in for the 2D worker process and the 3D worker process — and
    only one may hold the claim at a time."""
    status, first = _post(live_authority, "/claim", {
        "session_id": "shared-session-x", "agent_id": "hermes",
        "instance_id": "worker-2d", "lease_seconds": 30.0,
    })
    assert status == 200

    status, second = _post(live_authority, "/claim", {
        "session_id": "shared-session-x", "agent_id": "hermes",
        "instance_id": "worker-3d", "lease_seconds": 30.0,
    })
    assert status == 409
    assert second["reason"] == "SESSION_OCCUPIED"
    assert second["current_instance_id"] == "worker-2d"

    status, released = _post(live_authority, "/release", {
        "session_id": "shared-session-x", "claim_token": first["claim_token"],
    })
    assert status == 200
    assert released["released"] is True

    status, third = _post(live_authority, "/claim", {
        "session_id": "shared-session-x", "agent_id": "hermes",
        "instance_id": "worker-3d", "lease_seconds": 30.0,
    })
    assert status == 200
    assert third["instance_id"] == "worker-3d"
