"""local_signed_transport: integrity, replay, freshness, credentials, and deny-all policy."""

from __future__ import annotations

import json
import os
import stat

import pytest

from tier1.engainos.authority import local_signed_transport as t

SECRET = b"\x05" * 32
ROUTES = frozenset({"build", "consume"})


def _verifier(now=1_000_000.0):
    clock = {"now": now}
    return t.SignedRequestVerifier({"client-a": SECRET}, clock=lambda: clock["now"]), clock


def _headers(body=b"{}", path="/p", method="POST", now=1_000_000, client="client-a", secret=SECRET):
    return t.signed_headers(client, secret, method, path, body, now=now)


def test_valid_request_returns_the_client_id():
    verifier, _ = _verifier()
    assert verifier.verify("POST", "/p", _headers(), b"{}") == "client-a"


@pytest.mark.parametrize("method,path,body", [("GET", "/p", b"{}"), ("POST", "/q", b"{}"), ("POST", "/p", b"{ }")])
def test_any_signed_element_changed_fails(method, path, body):
    verifier, _ = _verifier()
    with pytest.raises(t.TransportAuthError, match="does not verify"):
        verifier.verify(method, path, _headers(), body)


def test_altered_timestamp_breaks_the_signature():
    verifier, _ = _verifier()
    headers = dict(_headers(), **{t.HEADER_TIMESTAMP: "1000001"})
    with pytest.raises(t.TransportAuthError, match="does not verify"):
        verifier.verify("POST", "/p", headers, b"{}")


@pytest.mark.parametrize("skew", [-31, 31])
def test_timestamps_outside_the_window_are_refused(skew):
    verifier, _ = _verifier()
    with pytest.raises(t.TransportAuthError, match="freshness"):
        verifier.verify("POST", "/p", _headers(now=1_000_000 + skew), b"{}")


def test_nonce_is_single_use_and_forgotten_after_the_window():
    verifier, clock = _verifier()
    headers = _headers()
    verifier.verify("POST", "/p", headers, b"{}")
    with pytest.raises(t.TransportAuthError, match="already used"):
        verifier.verify("POST", "/p", headers, b"{}")
    clock["now"] += 61  # the old request is now stale anyway
    with pytest.raises(t.TransportAuthError, match="freshness"):
        verifier.verify("POST", "/p", headers, b"{}")
    # The next accepted request prunes nonces that can no longer pass freshness.
    verifier.verify("POST", "/p", _headers(now=1_000_061), b"{}")
    assert len(verifier._seen) == 1 and headers[t.HEADER_NONCE] not in {n for _, n in verifier._seen}


def test_full_replay_cache_fails_closed(monkeypatch):
    monkeypatch.setattr(t, "MAX_PENDING_NONCES", 1)
    verifier, _ = _verifier()
    verifier.verify("POST", "/p", _headers(), b"{}")
    with pytest.raises(t.TransportAuthError, match="cache is full"):
        verifier.verify("POST", "/p", _headers(), b"{}")


@pytest.mark.parametrize("drop", [t.HEADER_CLIENT, t.HEADER_TIMESTAMP, t.HEADER_NONCE, t.HEADER_SIGNATURE])
def test_missing_header_is_unsigned(drop):
    verifier, _ = _verifier()
    headers = {k: v for k, v in _headers().items() if k != drop}
    with pytest.raises(t.TransportAuthError, match="not signed"):
        verifier.verify("POST", "/p", headers, b"{}")


@pytest.mark.parametrize("header,value", [(t.HEADER_NONCE, "XYZ"), (t.HEADER_TIMESTAMP, "-5"), (t.HEADER_SIGNATURE, "00")])
def test_malformed_headers_are_refused(header, value):
    verifier, _ = _verifier()
    with pytest.raises(t.TransportAuthError, match="malformed"):
        verifier.verify("POST", "/p", dict(_headers(), **{header: value}), b"{}")


def test_wrong_secret_is_refused():
    verifier, _ = _verifier()
    with pytest.raises(t.TransportAuthError, match="does not verify"):
        verifier.verify("POST", "/p", _headers(secret=b"\x06" * 32), b"{}")


def test_verifier_rejects_weak_credentials():
    with pytest.raises(ValueError):
        t.SignedRequestVerifier({"client-a": b"short"})


# ── Policy ───────────────────────────────────────────────────────────

def _policy(tmp_path, clients, **top):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"contract": t.POLICY_CONTRACT, "clients": clients, **top}))
    return path


ENTRY = {"actor_id": "actor-x", "actor_authority_tier": 2, "routes": ["build"]}


def test_missing_policy_is_deny_all(tmp_path):
    assert t.load_client_policy(tmp_path / "absent.json", ROUTES) == {}


def test_valid_policy_loads(tmp_path):
    policy = t.load_client_policy(_policy(tmp_path, {"client-a": ENTRY}), ROUTES)
    assert policy == {"client-a": t.ClientAssignment("actor-x", 2, frozenset({"build"}))}


@pytest.mark.parametrize("entry", [
    dict(ENTRY, actor_authority_tier=0),      # internal system tier is never a transport client
    dict(ENTRY, actor_authority_tier=4),
    dict(ENTRY, actor_authority_tier=True),
    dict(ENTRY, actor_id=""),
    dict(ENTRY, routes=[]),
    dict(ENTRY, routes=["build", "build"]),
    dict(ENTRY, routes=["admin"]),
    dict(ENTRY, reality_mode="DRAFT"),        # reality mode is runtime state, never policy
    {"actor_id": "actor-x", "routes": ["build"]},
    dict(ENTRY, routes=["consume"]),          # consume carries no authority: no actor or tier
    {"actor_authority_tier": 2, "routes": ["observe"]},
    {"routes": ["observe"], "extra": 1},
])
def test_invalid_entries_are_refused(tmp_path, entry):
    with pytest.raises(ValueError):
        t.load_client_policy(_policy(tmp_path, {"client-a": entry}), ROUTES)


def test_invalid_policy_shapes_are_refused(tmp_path):
    with pytest.raises(ValueError):
        t.load_client_policy(_policy(tmp_path, {"Bad Id": ENTRY}), ROUTES)
    with pytest.raises(ValueError):
        t.load_client_policy(_policy(tmp_path, {}, extra=1), ROUTES)
    dup = tmp_path / "dup.json"
    dup.write_text('{"contract": "%s", "clients": {}, "clients": {}}' % t.POLICY_CONTRACT)
    with pytest.raises(ValueError, match="duplicate"):
        t.load_client_policy(dup, ROUTES)


# ── Credentials ──────────────────────────────────────────────────────

def test_credentials_are_private_and_rotate(tmp_path):
    directory = tmp_path / "creds"
    first = t.provision_credentials(directory, ["client-a"])
    key = directory / "client-a.key"
    assert stat.S_IMODE(os.stat(directory).st_mode) == 0o700
    assert stat.S_IMODE(os.stat(key).st_mode) == 0o600
    assert bytes.fromhex(key.read_text()) == first["client-a"]
    second = t.provision_credentials(directory, ["client-a"])
    assert second["client-a"] != first["client-a"]
    assert sorted(p.name for p in directory.iterdir()) == ["client-a.key"]


def test_non_actor_roles_declare_routes_only(tmp_path):
    policy = t.load_client_policy(_policy(tmp_path, {"godot-presenter": {"routes": ["consume", "observe"]}}), t.KNOWN_ROUTES)
    assert policy == {"godot-presenter": t.ClientAssignment(None, None, frozenset({"consume", "observe"}))}


def test_compose_verifier_provisions_only_this_servers_clients(tmp_path):
    policy = {"client-a": t.ClientAssignment("actor-x", 2, frozenset({"build"})),
              "client-b": t.ClientAssignment(None, None, frozenset({"observe"}))}
    verifier, clients = t.compose_verifier(policy, frozenset({"observe"}), tmp_path / "8080")
    assert set(clients) == {"client-b"} and sorted(p.name for p in (tmp_path / "8080").iterdir()) == ["client-b.key"]


@pytest.mark.parametrize("length,status", [(None, 411), ("abc", 411), (str(t.MAX_SIGNED_BODY_BYTES + 1), 413)])
def test_body_length_is_bounded_before_reading(length, status):
    headers = {} if length is None else {"Content-Length": length}
    with pytest.raises(t.TransportAuthError) as err:
        t.bounded_content_length(headers)
    assert err.value.status == status
    assert t.bounded_content_length({"Content-Length": "12"}) == 12
