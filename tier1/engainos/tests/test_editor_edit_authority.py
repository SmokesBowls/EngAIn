"""Editor-edit authorization: authority state machine and signed route (isolated, disposable files only)."""

from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pytest

from tier1.engainos.authority import editor_edit_authority as ea
from tier1.engainos.authority.local_signed_transport import signed_headers
from tier1.engainos.bridgeroom import editor_edit_route as route_mod
from tier1.engainos.core import intent_shadow

AUTHORITY_DIR = Path(ea.__file__).resolve().parent
DRAGON = "18db34cf-09e9-5cbf-af02-82c6a44b7e5d"
FOUNDRY = "e7feb354-9f35-52de-a4e6-b394ee54e426"
PROJECT = "godot_semantic_test"
INSTALLATION = str(uuid.uuid5(uuid.UUID(DRAGON), PROJECT))
PROPOSER, EXECUTOR = "dragon-adapter-test", "foundry-dock-test"
APPROVER, HUMAN = "human-approver-test", "human-input-test"
HUMAN_KEY = bytes(range(32))                 # the game HUD's human-input secret in these tests
ROLE_CLIENTS = {PROPOSER: ["edit_propose"], EXECUTOR: ["edit_execute"], APPROVER: ["edit_approve"], HUMAN: ["edit_attest"]}
BODY = "Create scenes/Beacon.tscn with one OmniLight3D named Beacon — énergie ✓"
PID = "dragonreq_20261106_120000_a1b2c3d4"
SCOPE = ea.scope_digest({"scenes/Main.tscn": "a" * 64})


def _policy_dict() -> dict:
    return {"contract": ea.POLICY_CONTRACT, "installations": {INSTALLATION: {
        "project_id": PROJECT,
        "proposer": {"client_id": PROPOSER, "actor_id": DRAGON},
        "executor": {"client_id": EXECUTOR, "actor_id": FOUNDRY},
        "approver": {"client_id": APPROVER},
        "human_input": {"client_id": HUMAN},
        "operation_class": "project_file_edit.v1",
        "writable_path_prefixes": ["scenes/", "scripts/"],
        "protected_paths": ["project.godot", "scripts/protected.gd"],
    }}}


class Clock:
    def __init__(self) -> None:
        self.now = 1_800_000_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def authority(tmp_path: Path, clock: Clock):
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy_dict()))
    auth = ea.EditorEditAuthority(policy=ea.load_edit_policy(policy_path), ledger_path=tmp_path / "ledger.json", clock=clock,
                                  human_input_keys={HUMAN: HUMAN_KEY})
    yield auth
    auth.close()


def _register(auth, pid: str = PID, body: str = BODY) -> dict:
    return auth.register_proposal(PROPOSER, {"installation_id": INSTALLATION, "proposal_id": pid, "body": body,
                                             "body_sha256": ea.body_sha256(body), "client_request_id": "client_1",
                                             "dragon_session_id": "sess_x"})


def _manual(auth, pid: str = PID, body: str = BODY) -> dict:
    return auth.accept(APPROVER, {"installation_id": INSTALLATION, "proposal_id": pid, "body_sha256": ea.body_sha256(body),
                                  "channel": "MANUAL_ACCEPT", "evidence": {"dock_instance_id": "dock1"},
                                  "base_scope_sha256": SCOPE})


def _attest(text: str, *, key: bytes = HUMAN_KEY, issued_at: int | None = None, client: str = HUMAN,
            request_id: str | None = None, nonce: str | None = None) -> dict:
    """What the game HUD attaches to the exact text the human typed."""
    import secrets
    att = {"contract": ea.HUMAN_INPUT_CONTRACT, "client_id": client, "installation_id": INSTALLATION,
           "request_id": request_id or "req_" + secrets.token_hex(16), "issued_at": 1_800_000_000 if issued_at is None else issued_at,
           "nonce": nonce or secrets.token_hex(16), "player_input_sha256": ea.body_sha256(text)}
    return {**att, "signature": ea.sign_human_input(key, att)}


def _conversational(auth, pid: str = PID, reference: str | None = None, *, text: str | None = None,
                    attestation: dict | None = None, action: str = "accept") -> dict:
    reference = reference or ea.proposal_code(pid)
    text = text if text is not None else f"{action} {reference}"
    evidence = {"client_request_id": "client_2", "player_input": text, "reference": reference,
                "attestation": attestation if attestation is not None else _attest(text)}
    if action == "reject":
        return auth.reject(PROPOSER, {"installation_id": INSTALLATION, "proposal_id": pid,
                                      "channel": "CONVERSATIONAL_ACCEPT", "evidence": evidence})
    return auth.accept(PROPOSER, {"installation_id": INSTALLATION, "proposal_id": pid, "body_sha256": ea.body_sha256(BODY),
                                  "channel": "CONVERSATIONAL_ACCEPT", "evidence": evidence, "base_scope_sha256": SCOPE})


def _set_mode(auth, mode: str, previous: str) -> dict:
    return auth.set_approval_mode(APPROVER, {"installation_id": INSTALLATION, "mode": mode, "previous_mode": previous})


def _pickup_one(auth) -> dict:
    grants = auth.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"]
    assert len(grants) == 1
    return grants[0]


def _consume(auth, grant: dict, body: str = BODY, scope: str = SCOPE) -> dict:
    fields = json.loads(grant["grant_json"])
    return auth.consume(EXECUTOR, {"installation_id": INSTALLATION, "grant_id": fields["grant_id"],
                                   "proposal_id": fields["proposal_id"], "body_sha256": ea.body_sha256(body),
                                   "current_scope_sha256": scope})


def _edit_outcome(auth, grant: dict, *, changed: list[str], ok: bool = True, receipt: str = "AVAILABLE",
                  edit_id: str = "20261106_120500_beef") -> dict:
    fields = json.loads(grant["grant_json"])
    return auth.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "edit", "proposal_id": fields["proposal_id"],
                                          "grant_id": fields["grant_id"], "edit_id": edit_id if changed else "",
                                          "turn_ok": ok, "receipt_state": receipt if changed else "",
                                          "changed_paths": changed, "scope_violations": []})


def _status(fn) -> tuple[int, str]:
    with pytest.raises(ea.EditAuthorityError) as caught:
        fn()
    return caught.value.status, caught.value.code


# ---- A1/A2: shipped policies are deny-all; nothing registers the route in production -----------

def test_shipped_policies_are_deny_all() -> None:
    assert ea.load_edit_policy(AUTHORITY_DIR / "EDITOR_EDIT_POLICY_V1.json") == {}
    from tier1.engainos.authority.local_signed_transport import load_client_policy
    assert load_client_policy(AUTHORITY_DIR / "EDITOR_EDIT_CLIENT_POLICY_V1.json", known_routes=ea.EDITOR_ROUTES) == {}


def test_editor_routes_exist_only_on_8765_and_nowhere_else() -> None:
    repo = AUTHORITY_DIR.parents[2]
    for server in ("tier1/engainos/engainos_server.py", "tier2/godotsim/sim_runtime.py", "tier2/godotsim/http_handlers.py"):
        assert "editor_edit" not in (repo / server).read_text(encoding="utf-8"), server
    launch = (repo / "tier1/engainos/launch_engine.py").read_text(encoding="utf-8")
    assert 'if os.environ.get("ENGAIN_EDITOR_AUTHORIZATION") == "1":' in launch


def test_compose_refuses_without_flag_and_with_shipped_deny_all(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(route_mod.FLAG_ENV, raising=False)
    assert route_mod.compose_from_environment(ledger=tmp_path / "l.json", transport_dir=tmp_path / "t") == \
        (None, "ENGAIN_EDITOR_AUTHORIZATION is not '1'")
    monkeypatch.setenv(route_mod.FLAG_ENV, "1")
    route, reason = route_mod.compose_from_environment(ledger=tmp_path / "l.json", transport_dir=tmp_path / "t")
    assert route is None and "deny-all" in reason
    assert not (tmp_path / "l.json").exists() and not (tmp_path / "t").exists()  # nothing created before refusing


def _scene_server(route):
    from http.server import HTTPServer
    from tier1.engainos.bridgeroom import scene_server
    previous = scene_server.SceneRequestHandler.editor_edit_route
    scene_server.SceneRequestHandler.editor_edit_route = route
    server = HTTPServer(("127.0.0.1", 0), scene_server.SceneRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, previous


def test_scene_server_editor_branch_is_404_flag_off_and_503_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    from tier1.engainos.bridgeroom import scene_server
    server, previous = _scene_server(None)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        monkeypatch.delenv(route_mod.FLAG_ENV, raising=False)
        assert _post(base, "/editor/state", {}, None, {})[0] == 404
        monkeypatch.setenv(route_mod.FLAG_ENV, "1")
        assert _post(base, "/editor/state", {}, None, {})[0] == 503
        monkeypatch.delenv("TRIXEL32D_LIVE_ROUTE", raising=False)
        assert _post(base, "/trixel32d/consume", {}, None, {})[0] == 404   # Trixel gating unchanged
    finally:
        server.shutdown()
        server.server_close()
        scene_server.SceneRequestHandler.editor_edit_route = previous


def test_scene_server_serves_a_composed_editor_route(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from tier1.engainos.bridgeroom import scene_server
    edit_policy = tmp_path / "edit_policy.json"
    edit_policy.write_text(json.dumps(_policy_dict()))
    client_policy = tmp_path / "client_policy.json"
    client_policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {
        cid: {"routes": routes} for cid, routes in ROLE_CLIENTS.items()}}))
    monkeypatch.setenv(route_mod.FLAG_ENV, "1")
    route, reason = route_mod.compose_from_environment(edit_policy=edit_policy, client_policy=client_policy,
                                                       ledger=tmp_path / "ledger.json", transport_dir=tmp_path / "t")
    assert reason == "composed"
    server, previous = _scene_server(route)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    keys = {cid: bytes.fromhex((tmp_path / "t" / f"{cid}.key").read_text()) for cid in (PROPOSER, EXECUTOR)}
    try:
        registration = {"installation_id": INSTALLATION, "proposal_id": PID, "body": BODY,
                        "body_sha256": ea.body_sha256(BODY), "client_request_id": "c1", "dragon_session_id": ""}
        assert _post(base, "/editor/proposals", registration, None, keys)[0] == 401
        status, body = _post(base, "/editor/proposals", registration, PROPOSER, keys)
        assert (status, body["state"]) == (200, "PENDING")
    finally:
        server.shutdown()
        server.server_close()
        scene_server.SceneRequestHandler.editor_edit_route = previous
        route._authority.close()


def test_manual_edit_between_approval_and_execution_is_refused(authority) -> None:
    _register(authority)
    _manual(authority)
    grant = _pickup_one(authority)
    edited = ea.scope_digest({"scenes/Main.tscn": "b" * 64})          # a human changed a file in scope
    assert _status(lambda: _consume(authority, grant, scope=edited)) == (409, "TARGET_STATE_CHANGED")
    assert authority.proposal_record(PID)["state"] == "AUTHORIZATION_STALE"
    assert _status(lambda: _consume(authority, grant))[1] == "GRANT_NOT_CONSUMABLE"  # never later, even if restored
    assert json.loads(grant["grant_json"])["base_scope_sha256"] == SCOPE


def test_scope_digest_reference_vector() -> None:
    # Shared vector: dragon_edit_acceptance.py and edit_authority_client.gd must produce this too.
    entries = {"scenes/b.tscn": "1" * 64, "foundry_staging/ä.txt": "2" * 64, "scenes/a.tscn": "3" * 64}
    lines = "".join(f"{entries[p]}  {p}\n" for p in sorted(entries))
    assert ea.scope_digest(entries) == __import__("hashlib").sha256(lines.encode()).hexdigest()
    assert ea.scope_digest({}) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_deny_all_policy_refuses_every_call_and_leaves_no_proposal(tmp_path: Path, clock: Clock) -> None:
    auth = ea.EditorEditAuthority(policy={}, ledger_path=tmp_path / "ledger.json", clock=clock)
    try:
        assert _status(lambda: _register(auth)) == (403, "INSTALLATION_NOT_AUTHORIZED")
        assert _status(lambda: _manual(auth)) == (403, "INSTALLATION_NOT_AUTHORIZED")
        assert auth.proposal_record(PID) is None
    finally:
        auth.close()


# ---- policy validation --------------------------------------------------------------------------

@pytest.mark.parametrize("mutate", [
    lambda e: e.update(project_id="other"),                                  # installation id no longer derives
    lambda e: e["executor"].update(actor_id=DRAGON),                         # proposer == executor
    lambda e: e["executor"].update(client_id=PROPOSER),                      # one client, two roles
    lambda e: e["approver"].update(client_id=EXECUTOR),                      # Foundry's key as the approver
    lambda e: e["human_input"].update(client_id=PROPOSER),                   # Dragon's key as the human input
    lambda e: e["approver"].update(actor_id=FOUNDRY),                        # no actor is invented for the human
    lambda e: e.pop("approver"),
    lambda e: e.pop("human_input"),
    lambda e: e.update(operation_class="unrestricted"),
    lambda e: e.update(writable_path_prefixes=["../escape/"]),
    lambda e: e.update(writable_path_prefixes=["scenes"]),                   # must be a directory prefix
    lambda e: e.update(protected_paths=["/abs"]),
    lambda e: e.update(actor_authority_tier=1),                              # no tier vocabulary
])
def test_malformed_edit_policy_is_refused(tmp_path: Path, mutate) -> None:
    data = _policy_dict()
    mutate(data["installations"][INSTALLATION])
    path = tmp_path / "p.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        ea.load_edit_policy(path)


# ---- A3: proposal registration --------------------------------------------------------------------

def test_registration_checks(authority) -> None:
    assert _register(authority)["code"] == "a1b2c3d4"
    assert _status(lambda: _register(authority)) == (409, "PROPOSAL_DUPLICATE")
    bad_hash = {"installation_id": INSTALLATION, "proposal_id": "dragonreq_20261106_120000_00000001", "body": BODY,
                "body_sha256": "f" * 64, "client_request_id": "c", "dragon_session_id": ""}
    assert _status(lambda: authority.register_proposal(PROPOSER, bad_hash)) == (400, "BODY_HASH_MISMATCH")
    assert _status(lambda: authority.register_proposal(EXECUTOR, {**bad_hash, "body_sha256": ea.body_sha256(BODY)})) \
        == (403, "CLIENT_ROLE_MISMATCH")
    assert _status(lambda: authority.register_proposal(PROPOSER, {**bad_hash, "proposal_id": "../x"}))[1] == "SCHEMA_INVALID"
    record = authority.proposal_record(PID)
    assert record["proposer_actor_id"] == DRAGON and record["executor_actor_id"] == FOUNDRY  # from policy, not request


# ---- A4/A5/A6: channels and the toggle ---------------------------------------------------------------

def test_channel_must_match_mode_and_toggle_never_approves(authority) -> None:
    _register(authority)
    _register(authority, "dragonreq_20261106_120001_00000002")
    before = len(intent_shadow.query_intents())
    assert _status(lambda: _conversational(authority)) == (409, "APPROVAL_MODE_MISMATCH")  # default MANUAL
    assert len(intent_shadow.query_intents()) == before + 1
    _set_mode(authority, "CONVERSATIONAL_ACCEPT", "MANUAL_ACCEPT")
    _set_mode(authority, "MANUAL_ACCEPT", "CONVERSATIONAL_ACCEPT")
    for pid in (PID, "dragonreq_20261106_120001_00000002"):
        assert authority.proposal_record(pid)["state"] == "PENDING"
    assert authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"] == []
    assert _status(lambda: _set_mode(authority, "CONVERSATIONAL_ACCEPT", "CONVERSATIONAL_ACCEPT")) == (409, "APPROVAL_MODE_CHANGED")
    for other in (PROPOSER, EXECUTOR, HUMAN):                                  # only the human's approver binding
        assert _status(lambda: authority.set_approval_mode(other, {"installation_id": INSTALLATION, "mode": "MANUAL_ACCEPT",
                                                                    "previous_mode": "MANUAL_ACCEPT"})) == (403, "CLIENT_ROLE_MISMATCH")


def test_each_channel_is_bound_to_its_client(authority) -> None:
    _register(authority)
    manual_from_proposer = {"installation_id": INSTALLATION, "proposal_id": PID, "body_sha256": ea.body_sha256(BODY),
                            "channel": "MANUAL_ACCEPT", "evidence": {"dock_instance_id": "d"}, "base_scope_sha256": SCOPE}
    for other in (PROPOSER, EXECUTOR, HUMAN):                                  # Foundry's executor key never approves
        assert _status(lambda: authority.accept(other, manual_from_proposer)) == (403, "CLIENT_ROLE_MISMATCH")
        assert _status(lambda: authority.reject(other, {k: manual_from_proposer[k] for k in
                                                        ("installation_id", "proposal_id", "channel", "evidence")})) \
            == (403, "CLIENT_ROLE_MISMATCH")
    _set_mode(authority, "CONVERSATIONAL_ACCEPT", "MANUAL_ACCEPT")
    conv = {**manual_from_proposer, "channel": "CONVERSATIONAL_ACCEPT",
            "evidence": {"client_request_id": "c", "player_input": "accept a1b2c3d4", "reference": "a1b2c3d4",
                         "attestation": _attest("accept a1b2c3d4")}}
    for other in (EXECUTOR, APPROVER, HUMAN):
        assert _status(lambda: authority.accept(other, conv)) == (403, "CLIENT_ROLE_MISMATCH")
    assert authority.proposal_record(PID)["state"] == "PENDING"


def test_conversational_reference_must_name_this_proposal(authority) -> None:
    _register(authority)
    _set_mode(authority, "CONVERSATIONAL_ACCEPT", "MANUAL_ACCEPT")
    assert _status(lambda: _conversational(authority, reference="deadbeef")) == (409, "REFERENCE_MISMATCH")
    assert _conversational(authority, reference=PID)["state"] == "AUTHORIZED"


# ---- the human-input boundary: a conversational approval needs the HUD's signature ------------------

def _conv_status(authority, **kwargs) -> tuple[int, str]:
    return _status(lambda: _conversational(authority, **kwargs))


def test_conversational_approval_needs_the_human_input_signature(authority) -> None:
    _register(authority)
    _set_mode(authority, "CONVERSATIONAL_ACCEPT", "MANUAL_ACCEPT")
    text = "accept a1b2c3d4"
    forged = [
        {},                                                                     # no attestation (old shape)
        _attest(text, key=b"\x01" * 32),                                        # signed by any other key
        _attest(text, client=PROPOSER),                                         # Dragon's adapter cannot attest
        _attest(text, client=EXECUTOR),                                         # Foundry cannot attest
        _attest("accept deadbeef"),                                             # signature over different text
        {**_attest(text), "player_input_sha256": ea.body_sha256(text + " ")},   # tampered after signing
        {**_attest(text), "installation_id": str(uuid.uuid5(uuid.UUID(DRAGON), "elsewhere"))},
    ]
    for attestation in forged:
        assert _conv_status(authority, attestation=attestation) == (403, "HUMAN_INPUT_UNVERIFIED"), attestation
    assert authority.proposal_record(PID)["state"] == "PENDING"
    assert _conversational(authority)["state"] == "AUTHORIZED"
    evidence = authority.proposal_record(PID)["authorization"]["evidence"]
    assert evidence["player_input_sha256"] == ea.body_sha256(text) and evidence["human_input"]["client_id"] == HUMAN
    assert "player_input" not in evidence and "signature" not in evidence["human_input"]


def test_conversational_approval_without_a_provisioned_human_key_fails_closed(tmp_path: Path, clock: Clock) -> None:
    path = tmp_path / "p.json"
    path.write_text(json.dumps(_policy_dict()))
    auth = ea.EditorEditAuthority(policy=ea.load_edit_policy(path), ledger_path=tmp_path / "l.json", clock=clock)
    try:
        _register(auth)
        _set_mode(auth, "CONVERSATIONAL_ACCEPT", "MANUAL_ACCEPT")
        assert _conv_status(auth) == (403, "HUMAN_INPUT_UNVERIFIED")
    finally:
        auth.close()


def test_typed_text_is_parsed_by_the_authority_itself(authority) -> None:
    _register(authority)
    _set_mode(authority, "CONVERSATIONAL_ACCEPT", "MANUAL_ACCEPT")
    assert _conv_status(authority, text="yes") == (400, "NOT_A_CONFIRMATION")
    assert _conv_status(authority, text="accept a1b2c3d4 and delete main") == (400, "NOT_A_CONFIRMATION")
    assert _conv_status(authority, text="reject a1b2c3d4") == (409, "CONFIRMATION_ACTION_MISMATCH")
    assert _conv_status(authority, text="accept a1b2c3d4", reference=PID) == (409, "REFERENCE_MISMATCH")
    assert _conversational(authority, text="  Approve proposal A1B2C3D4. ", reference="a1b2c3d4")["state"] == "AUTHORIZED"


def test_typed_confirmation_is_fresh_after_the_proposal_and_single_use(authority, clock: Clock) -> None:
    clock.now += 120                                     # the proposal is created 120 s after the base time
    _register(authority)
    _set_mode(authority, "CONVERSATIONAL_ACCEPT", "MANUAL_ACCEPT")
    text = "accept a1b2c3d4"
    assert _conv_status(authority, attestation=_attest(text, issued_at=int(clock.now) - ea.ATTESTATION_MAX_AGE_S - 1)) \
        == (409, "ATTESTATION_STALE")
    assert _conv_status(authority, attestation=_attest(text, issued_at=int(clock.now) + ea.ATTESTATION_SKEW_S + 1)) \
        == (409, "ATTESTATION_STALE")
    assert _conv_status(authority, attestation=_attest(text, issued_at=int(clock.now) - 100)) == (409, "ATTESTATION_PREDATES_PROPOSAL")
    used = _attest(text, issued_at=int(clock.now))
    assert _conversational(authority, attestation=used)["state"] == "AUTHORIZED"
    other = "dragonreq_20261106_120009_0000000a"
    _register(authority, other)
    replay_text = f"accept {ea.proposal_code(other)}"
    assert _conv_status(authority, pid=other, attestation={**_attest(replay_text, issued_at=int(clock.now), nonce=used["nonce"])}) \
        == (409, "ATTESTATION_REPLAYED")
    assert _conv_status(authority, pid=other, attestation=_attest(replay_text, issued_at=int(clock.now),
                                                                  request_id=used["request_id"])) == (409, "ATTESTATION_REPLAYED")
    assert authority.proposal_record(other)["state"] == "PENDING"


def test_conversational_reject_needs_the_signature_too(authority) -> None:
    _register(authority)
    assert _conv_status(authority, action="reject", attestation=_attest("reject a1b2c3d4", key=b"\x02" * 32)) \
        == (403, "HUMAN_INPUT_UNVERIFIED")
    assert _conv_status(authority, action="reject", text="accept a1b2c3d4") == (409, "CONFIRMATION_ACTION_MISMATCH")
    assert _conversational(authority, action="reject")["state"] == "REJECTED"


# ---- both modes, one pipeline; grant binding ----------------------------------------------------------

@pytest.mark.parametrize("mode", ["MANUAL_ACCEPT", "CONVERSATIONAL_ACCEPT"])
def test_both_modes_produce_the_same_grant_through_the_same_pickup(authority, mode: str) -> None:
    _register(authority)
    if mode == "CONVERSATIONAL_ACCEPT":
        _set_mode(authority, mode, "MANUAL_ACCEPT")
        result = _conversational(authority)
    else:
        result = _manual(authority)
    assert set(result) == {"proposal_id", "state", "authorization_id", "expires_at"}  # acceptor never gets the grant
    grant = _pickup_one(authority)
    assert authority.verify_grant(grant["grant_json"], grant["grant_signature_b64"])
    fields = json.loads(grant["grant_json"])
    assert set(fields) == ea.GRANT_FIELDS
    assert fields["channel"] == mode
    assert fields["body_sha256"] == ea.body_sha256(BODY)
    assert (fields["installation_id"], fields["project_id"], fields["executor_actor_id"], fields["executor_client_id"]) \
        == (INSTALLATION, PROJECT, FOUNDRY, EXECUTOR)
    assert fields["operation_class"] == "project_file_edit.v1"
    assert fields["writable_path_prefixes"] == ["scenes/", "scripts/"]
    assert fields["protected_paths"] == ["project.godot", "scripts/protected.gd"]
    assert fields["expires_at"] - fields["issued_at"] == ea.GRANT_TTL_S == 120
    assert _consume(authority, grant)["state"] == "CONSUMED"


def test_trixel_grant_contract_is_untouched() -> None:
    from tier1.engainos.authority import trixel32d_application_grant as trixel
    assert trixel.GRANT_TTL_S == 30
    assert trixel.GRANT_CONTRACT == "engainos.trixel32d_application_grant.v1"
    assert ea.GRANT_CONTRACT != trixel.GRANT_CONTRACT and not (set(trixel.GRANT_FIELDS) == ea.GRANT_FIELDS)


# ---- A7/A8/A9: never twice --------------------------------------------------------------------------------

def test_accept_twice_consume_twice_and_rejected_are_refused(authority) -> None:
    _register(authority)
    _manual(authority)
    assert _status(lambda: _manual(authority)) == (409, "PROPOSAL_NOT_PENDING")
    grant = _pickup_one(authority)
    _consume(authority, grant)
    assert _status(lambda: _consume(authority, grant)) == (409, "GRANT_NOT_CONSUMABLE")
    assert authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"] == []
    other = "dragonreq_20261106_120002_00000003"
    _register(authority, other)
    authority.reject(APPROVER, {"installation_id": INSTALLATION, "proposal_id": other, "channel": "MANUAL_ACCEPT",
                                "evidence": {"dock_instance_id": "d"}})
    assert _status(lambda: _manual(authority, other)) == (409, "PROPOSAL_NOT_PENDING")


def test_consume_refuses_other_bytes(authority) -> None:
    _register(authority)
    _manual(authority)
    grant = _pickup_one(authority)
    assert _status(lambda: _consume(authority, grant, body=BODY + " and delete everything")) == (409, "BODY_HASH_MISMATCH")


# ---- A10: expiry -------------------------------------------------------------------------------------------

def test_expired_grant_is_never_reissued(authority, clock: Clock) -> None:
    _register(authority)
    _manual(authority)
    grant = _pickup_one(authority)
    clock.now += ea.GRANT_TTL_S + 1
    assert _status(lambda: _consume(authority, grant)) == (410, "GRANT_EXPIRED")
    assert authority.proposal_record(PID)["state"] == "AUTHORIZATION_EXPIRED"
    assert authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"] == []
    assert _status(lambda: _manual(authority)) == (409, "PROPOSAL_NOT_PENDING")


# ---- A11: tamper -------------------------------------------------------------------------------------------

def test_tampered_grant_does_not_verify(authority) -> None:
    _register(authority)
    _manual(authority)
    grant = _pickup_one(authority)
    widened = grant["grant_json"].replace('"scenes/","scripts/"', '"","scenes/"')
    assert widened != grant["grant_json"]
    assert not authority.verify_grant(widened, grant["grant_signature_b64"])


# ---- A12: restarts ------------------------------------------------------------------------------------------

def test_authority_restart_loses_outstanding_grants_and_keeps_consumed_state(tmp_path: Path, clock: Clock) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(_policy_dict()))
    policy = ea.load_edit_policy(policy_path)
    first = ea.EditorEditAuthority(policy=policy, ledger_path=tmp_path / "ledger.json", clock=clock)
    _register(first)
    _register(first, "dragonreq_20261106_120003_00000004")
    _manual(first)
    grant = _pickup_one(first)
    _consume(first, grant)
    _manual(first, "dragonreq_20261106_120003_00000004")
    outstanding = _pickup_one(first)
    with pytest.raises(ea.EditAuthorityError) as owned:
        ea.EditorEditAuthority(policy=policy, ledger_path=tmp_path / "ledger.json", clock=clock)
    assert owned.value.code == "LEDGER_OWNED"
    first.close()
    second = ea.EditorEditAuthority(policy=policy, ledger_path=tmp_path / "ledger.json", clock=clock)
    try:
        assert second.proposal_record(PID)["state"] == "CONSUMED"
        assert second.proposal_record("dragonreq_20261106_120003_00000004")["state"] == "AUTHORIZATION_LOST"
        assert not second.verify_grant(outstanding["grant_json"], outstanding["grant_signature_b64"])
        assert second.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"] == []
        assert _status(lambda: _consume(second, grant))[1] == "GRANT_NOT_CONSUMABLE"
        assert _status(lambda: _consume(second, outstanding))[1] == "GRANT_NOT_CONSUMABLE"
    finally:
        second.close()


# ---- target state binding --------------------------------------------------------------------------------

def test_grant_is_stale_after_another_edit_or_revert(authority) -> None:
    for pid in (PID, "dragonreq_20261106_120004_00000005", "dragonreq_20261106_120005_00000006"):
        _register(authority, pid)
    _manual(authority, PID)
    _manual(authority, "dragonreq_20261106_120004_00000005")
    grants = {json.loads(g["grant_json"])["proposal_id"]: g for g in authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"]}
    _consume(authority, grants[PID])
    _edit_outcome(authority, grants[PID], changed=["scenes/Beacon.tscn"])
    assert _status(lambda: _consume(authority, grants["dragonreq_20261106_120004_00000005"])) == (409, "TARGET_STATE_CHANGED")
    assert authority.proposal_record("dragonreq_20261106_120004_00000005")["state"] == "AUTHORIZATION_STALE"
    _manual(authority, "dragonreq_20261106_120005_00000006")
    third = _pickup_one(authority)
    authority.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "revert",
                                        "edit_id": "20261106_120500_beef", "status": "reverted"})
    assert _status(lambda: _consume(authority, third)) == (409, "TARGET_STATE_CHANGED")


# ---- revert slot (decisions 1, 2, 5) ----------------------------------------------------------------------

def _run_to_outcome(auth, pid: str, **outcome) -> dict:
    _register(auth, pid)
    _manual(auth, pid)
    grant = _pickup_one(auth)
    _consume(auth, grant)
    return _edit_outcome(auth, grant, **outcome)


def _slot(auth):
    return auth.state(EXECUTOR, {"installation_id": INSTALLATION})["revert_slot"]


def test_revert_slot_single_level_semantics(authority) -> None:
    _run_to_outcome(authority, "dragonreq_20261106_130000_00000001", changed=["scenes/A.tscn"], edit_id="e1")
    assert _slot(authority)["edit_id"] == "e1"
    _run_to_outcome(authority, "dragonreq_20261106_130001_00000002", changed=[])            # changed nothing
    assert _slot(authority)["edit_id"] == "e1"
    _register(authority, "dragonreq_20261106_130002_00000003")                                # rejected
    authority.reject(APPROVER, {"installation_id": INSTALLATION, "proposal_id": "dragonreq_20261106_130002_00000003",
                                "channel": "MANUAL_ACCEPT", "evidence": {"dock_instance_id": "d"}})
    assert _slot(authority)["edit_id"] == "e1"
    _run_to_outcome(authority, "dragonreq_20261106_130003_00000004", changed=["scenes/B.tscn"], ok=False, edit_id="e2")
    assert _slot(authority)["edit_id"] == "e2" and _slot(authority)["turn_ok"] is False      # failed-with-changes replaces
    _run_to_outcome(authority, "dragonreq_20261106_130004_00000005", changed=["scenes/C.tscn"], receipt="ERROR", edit_id="e3")
    assert _slot(authority)["edit_id"] == "e3" and _slot(authority)["revertible"] is False
    authority.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "revert", "edit_id": "e3",
                                        "status": "refused_state"})
    assert _slot(authority)["edit_id"] == "e3"
    _run_to_outcome(authority, "dragonreq_20261106_130005_00000006", changed=["scenes/D.tscn"], edit_id="e4")
    authority.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "revert", "edit_id": "e4", "status": "reverted"})
    assert _slot(authority) is None                                                           # no history: e3 does not come back


def test_revert_never_restores_authorization(authority) -> None:
    _run_to_outcome(authority, PID, changed=["scenes/A.tscn"], edit_id="e1")
    authority.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "revert", "edit_id": "e1", "status": "reverted"})
    assert authority.proposal_record(PID)["state"] == "COMPLETED"
    assert _status(lambda: _manual(authority)) == (409, "PROPOSAL_NOT_PENDING")
    assert authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"] == []
    kinds = [e["kind"] for e in authority.events()]
    assert kinds[-1] == "revert_outcome"


def test_outcome_recorded_once_and_only_after_consume(authority) -> None:
    _register(authority)
    _manual(authority)
    grant = _pickup_one(authority)
    assert _status(lambda: _edit_outcome(authority, grant, changed=[]))[1] == "OUTCOME_NOT_EXPECTED"
    _consume(authority, grant)
    _edit_outcome(authority, grant, changed=[])
    assert _status(lambda: _edit_outcome(authority, grant, changed=[]))[1] == "OUTCOME_NOT_EXPECTED"


# ---- signed HTTP route -----------------------------------------------------------------------------------------

@pytest.fixture
def live_route(tmp_path: Path):
    edit_policy = tmp_path / "edit_policy.json"
    edit_policy.write_text(json.dumps(_policy_dict()))
    client_policy = tmp_path / "client_policy.json"
    client_policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {
        cid: {"routes": routes} for cid, routes in ROLE_CLIENTS.items()}}))
    route = route_mod.compose(edit_policy=edit_policy, client_policy=client_policy,
                              ledger=tmp_path / "ledger.json", transport_dir=tmp_path / "transport")
    server = route_mod.make_server(route)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    keys = {cid: bytes.fromhex((tmp_path / "transport" / f"{cid}.key").read_text()) for cid in ROLE_CLIENTS}
    yield f"http://127.0.0.1:{server.server_address[1]}", keys
    server.shutdown()
    server.server_close()
    route._authority.close()


def _post(base: str, path: str, payload, client: str | None, keys: dict, *, tamper: bool = False) -> tuple[int, dict]:
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if client:
        headers.update(signed_headers(client, keys[client], "POST", path, body))
    if tamper:
        body = body.replace(b"a1b2c3d4", b"a1b2c3d5")
    request = urllib.request.Request(base + path, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_route_requires_signature_and_route_permission(live_route) -> None:
    base, keys = live_route
    registration = {"installation_id": INSTALLATION, "proposal_id": PID, "body": BODY, "body_sha256": ea.body_sha256(BODY),
                    "client_request_id": "c1", "dragon_session_id": ""}
    assert _post(base, "/editor/proposals", registration, None, keys)[0] == 401
    assert _post(base, "/editor/proposals", registration, PROPOSER, keys, tamper=True)[0] == 401
    assert _post(base, "/editor/proposals", registration, EXECUTOR, keys)[0] == 403          # executor lacks edit_propose
    assert _post(base, "/editor/grants/pickup", {"installation_id": INSTALLATION}, PROPOSER, keys)[0] == 403
    status, body = _post(base, "/editor/proposals", registration, PROPOSER, keys)
    assert (status, body["state"]) == (200, "PENDING")
    status, body = _post(base, "/editor/public_key", {}, EXECUTOR, keys)
    assert status == 200 and body["public_key_pem"].startswith("-----BEGIN PUBLIC KEY-----")


@pytest.mark.parametrize("routes", [
    {EXECUTOR: ["edit_execute", "edit_approve"]},                            # Foundry's key could approve
    {PROPOSER: ["edit_propose", "edit_attest"]},                             # Dragon's key could attest
    {HUMAN: ["edit_attest", "edit_propose"]},
    {APPROVER: ["edit_approve", "edit_execute"]},
    {APPROVER: None},                                                        # binding missing from the client policy
])
def test_compose_refuses_a_credential_holding_another_role(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, routes: dict) -> None:
    clients = {cid: {"routes": r} for cid, r in ROLE_CLIENTS.items()}
    for cid, r in routes.items():
        clients.pop(cid) if r is None else clients.__setitem__(cid, {"routes": r})
    (tmp_path / "edit.json").write_text(json.dumps(_policy_dict()))
    (tmp_path / "clients.json").write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": clients}))
    monkeypatch.setenv(route_mod.FLAG_ENV, "1")
    route, reason = route_mod.compose_from_environment(edit_policy=tmp_path / "edit.json", client_policy=tmp_path / "clients.json",
                                                       ledger=tmp_path / "l.json", transport_dir=tmp_path / "t")
    assert route is None and "must hold exactly the route" in reason
    assert not (tmp_path / "l.json").exists() and not (tmp_path / "t").exists()     # nothing minted before refusing
    with pytest.raises(ValueError):
        route_mod.compose(edit_policy=tmp_path / "edit.json", client_policy=tmp_path / "clients.json",
                          ledger=tmp_path / "l.json", transport_dir=tmp_path / "t")


def test_route_roles_executor_cannot_approve_and_human_input_opens_no_route(live_route) -> None:
    base, keys = live_route
    registration = {"installation_id": INSTALLATION, "proposal_id": PID, "body": BODY, "body_sha256": ea.body_sha256(BODY),
                    "client_request_id": "c1", "dragon_session_id": ""}
    assert _post(base, "/editor/proposals", registration, PROPOSER, keys)[0] == 200
    manual = {"installation_id": INSTALLATION, "proposal_id": PID, "body_sha256": ea.body_sha256(BODY), "channel": "MANUAL_ACCEPT",
              "evidence": {"dock_instance_id": "d"}, "base_scope_sha256": SCOPE}
    mode = {"installation_id": INSTALLATION, "mode": "CONVERSATIONAL_ACCEPT", "previous_mode": "MANUAL_ACCEPT"}
    assert _post(base, "/editor/acceptances", manual, EXECUTOR, keys)[0] == 403
    assert _post(base, "/editor/approval_mode", mode, EXECUTOR, keys)[0] == 403
    assert _post(base, "/editor/approval_mode", mode, PROPOSER, keys)[0] == 403
    for path in ("/editor/state", "/editor/acceptances", "/editor/approval_mode", "/editor/grants/pickup"):
        assert _post(base, path, {"installation_id": INSTALLATION}, HUMAN, keys)[0] == 403
    assert _post(base, "/editor/grants/pickup", {"installation_id": INSTALLATION}, APPROVER, keys)[0] == 403
    assert _post(base, "/editor/approval_mode", mode, APPROVER, keys)[0] == 200
    text = "accept a1b2c3d4"
    conv = {**manual, "channel": "CONVERSATIONAL_ACCEPT",
            "evidence": {"client_request_id": "c", "player_input": text, "reference": "a1b2c3d4"}}
    signed_with_minted_key = _attest(text, key=keys[HUMAN], issued_at=int(__import__("time").time()))
    assert _post(base, "/editor/acceptances", {**conv, "evidence": {**conv["evidence"], "attestation": _attest(text)}},
                 PROPOSER, keys)[1].get("error") == "HUMAN_INPUT_UNVERIFIED"
    status, body = _post(base, "/editor/acceptances", {**conv, "evidence": {**conv["evidence"], "attestation": signed_with_minted_key}},
                         PROPOSER, keys)
    assert (status, body.get("state")) == (200, "AUTHORIZED"), body


def test_route_binds_loopback_only() -> None:
    with pytest.raises(ValueError):
        route_mod.make_server(object(), host="0.0.0.0")  # type: ignore[arg-type]
