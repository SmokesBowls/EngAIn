"""Standing mandates (FULL_SCENE / ENTIRE_GAME) and workspace promotion: authority state machine (disposable files only)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from tier1.engainos.authority import editor_edit_authority as ea
from tier1.engainos.bridgeroom import editor_edit_route as route_mod

DRAGON = "18db34cf-09e9-5cbf-af02-82c6a44b7e5d"
FOUNDRY = "e7feb354-9f35-52de-a4e6-b394ee54e426"
PROJECT = "godot_semantic_test"
INSTALLATION = str(uuid.uuid5(uuid.UUID(DRAGON), PROJECT))
PROPOSER, EXECUTOR = "dragon-adapter-test", "foundry-dock-test"
APPROVER, HUMAN = "human-approver-test", "human-input-test"
GOAL = "Build the courtyard scene: a stone floor, four torches and a gate."
DOCK = {"dock_instance_id": "dock1"}


def _policy(modes: list[str] | None = None) -> dict:
    entry = {
        "project_id": PROJECT,
        "proposer": {"client_id": PROPOSER, "actor_id": DRAGON},
        "executor": {"client_id": EXECUTOR, "actor_id": FOUNDRY},
        "approver": {"client_id": APPROVER}, "human_input": {"client_id": HUMAN},
        "operation_class": "project_file_edit.v1",
        "writable_path_prefixes": ["scenes/", "scripts/"],
        "protected_paths": ["project.godot", "scenes/locked/"],
    }
    if modes is not None:
        entry["mandate_modes"] = modes
    return {"contract": ea.POLICY_CONTRACT, "installations": {INSTALLATION: entry}}


class Clock:
    def __init__(self) -> None:
        self.now = 1_800_000_000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> Clock:
    return Clock()


def _authority(tmp_path: Path, clock: Clock, modes: list[str] | None = ("FULL_SCENE", "ENTIRE_GAME")):
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps(_policy(None if modes is None else list(modes))))
    return ea.EditorEditAuthority(policy=ea.load_edit_policy(policy), ledger_path=tmp_path / "ledger.json", clock=clock)


@pytest.fixture
def authority(tmp_path: Path, clock: Clock):
    auth = _authority(tmp_path, clock)
    yield auth
    auth.close()


def _create(auth, mode="FULL_SCENE", prefixes=("scenes/courtyard/",), workspace="", max_edits=3, ttl=3600, client=APPROVER):
    return auth.create_mandate(client, {"installation_id": INSTALLATION, "mode": mode, "goal": GOAL,
                                        "writable_path_prefixes": list(prefixes), "workspace_id": workspace,
                                        "max_edits": max_edits, "ttl_s": ttl, "evidence": DOCK})


_counter = iter(range(10_000))


def _propose(auth, mandate_id: str | None, body="Add four torches to scenes/courtyard/Courtyard.tscn") -> tuple[str, dict]:
    pid = f"dragonreq_20261108_120000_{next(_counter):08x}"
    payload = {"installation_id": INSTALLATION, "proposal_id": pid, "body": body, "body_sha256": ea.body_sha256(body),
               "client_request_id": "c", "dragon_session_id": "s"}
    if mandate_id is not None:
        payload["mandate_id"] = mandate_id
    return pid, auth.register_proposal(PROPOSER, payload)


def _run(auth, pid: str, changed=("scenes/courtyard/Courtyard.tscn",), ok=True) -> dict:
    """Executor side: pick up, consume, report, exactly as the dock does."""
    grants = auth.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"]
    fields = next(json.loads(g["grant_json"]) for g in grants if json.loads(g["grant_json"])["proposal_id"] == pid)
    assert auth.verify_grant(*next((g["grant_json"], g["grant_signature_b64"]) for g in grants
                                   if json.loads(g["grant_json"])["proposal_id"] == pid))
    auth.consume(EXECUTOR, {"installation_id": INSTALLATION, "grant_id": fields["grant_id"], "proposal_id": pid,
                            "body_sha256": fields["body_sha256"], "current_scope_sha256": "f" * 64})
    edit_id = "edit_%s" % pid[-8:] if changed else ""
    auth.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "edit", "proposal_id": pid,
                                   "grant_id": fields["grant_id"], "edit_id": edit_id, "turn_ok": ok,
                                   "receipt_state": "AVAILABLE" if changed else "", "changed_paths": list(changed),
                                   "scope_violations": []})
    return fields


def _code(exc: pytest.ExceptionInfo) -> str:
    return exc.value.code


# ---- creation: explicit human approval, policy-bounded scope -------------------------------------

def test_only_the_approver_creates_a_mandate(authority) -> None:
    for client in (PROPOSER, EXECUTOR, HUMAN):
        with pytest.raises(ea.EditAuthorityError) as exc:
            _create(authority, client=client)
        assert _code(exc) == "CLIENT_ROLE_MISMATCH"
    view = _create(authority)
    assert view["state"] == "ACTIVE" and "approval" not in view
    assert view["goal_sha256"] == ea.body_sha256(GOAL) and view["max_edits"] == 3
    assert view["protected_paths"] == ["project.godot", "scenes/locked/"]   # always the policy's, never the request's


def test_policy_without_mandate_modes_permits_none(tmp_path: Path, clock: Clock) -> None:
    auth = _authority(tmp_path, clock, modes=None)
    try:
        with pytest.raises(ea.EditAuthorityError) as exc:
            _create(auth)
        assert _code(exc) == "MANDATE_MODE_NOT_PERMITTED"
    finally:
        auth.close()


def test_policy_rejects_unknown_mandate_modes(tmp_path: Path) -> None:
    policy = tmp_path / "p.json"
    policy.write_text(json.dumps(_policy(["SINGLE_TASK"])))
    with pytest.raises(ValueError):
        ea.load_edit_policy(policy)


@pytest.mark.parametrize("prefixes,code", [
    (["assets/"], "SCOPE_NOT_PERMITTED"),            # outside the policy's writable prefixes
    (["scenes/locked/"], "SCOPE_NOT_PERMITTED"),     # a protected path
    (["scenes/locked/inner/"], "SCOPE_NOT_PERMITTED"),
    (["scenes/a/", "scenes/b/"], "SCHEMA_INVALID"),  # FULL_SCENE is one folder
    (["../outside/"], "SCHEMA_INVALID"),
    ([""], "SCHEMA_INVALID"),                        # the whole project is never a FULL_SCENE scope
])
def test_full_scene_scope_cannot_exceed_policy(authority, prefixes, code) -> None:
    with pytest.raises(ea.EditAuthorityError) as exc:
        _create(authority, prefixes=prefixes)
    assert _code(exc) == code


@pytest.mark.parametrize("kwargs", [
    {"max_edits": 0}, {"max_edits": ea.MAX_MANDATE_EDITS + 1}, {"max_edits": True},
    {"ttl": 10}, {"ttl": ea.MAX_MANDATE_TTL_S + 1},
    {"mode": "ENTIRE_GAME", "prefixes": ["game/"], "workspace": ""},     # needs a workspace
    {"mode": "ENTIRE_GAME", "prefixes": [""], "workspace": "ws_game"},   # never "the whole tree"
    {"mode": "ENTIRE_GAME", "prefixes": ["../game/"], "workspace": "ws_game"},
    {"mode": "FULL_SCENE", "workspace": "ws_game"},                       # FULL_SCENE is the open project
])
def test_mandate_bounds_are_validated(authority, kwargs) -> None:
    with pytest.raises(ea.EditAuthorityError) as exc:
        _create(authority, **kwargs)
    assert _code(exc) == "SCHEMA_INVALID"


def test_one_active_mandate_and_no_renewal(authority) -> None:
    first = _create(authority)
    with pytest.raises(ea.EditAuthorityError) as exc:
        _create(authority, max_edits=50)
    assert _code(exc) == "MANDATE_ALREADY_ACTIVE"
    # No route can widen or extend a mandate: the route table has create, revoke and complete only.
    mandate_routes = {op for _, op in route_mod._ROUTES.values() if "mandate" in op}
    assert mandate_routes == {"create_mandate", "revoke_mandate", "complete_mandate"}
    authority.revoke_mandate(APPROVER, {"installation_id": INSTALLATION, "mandate_id": first["mandate_id"], "evidence": DOCK})
    assert _create(authority)["mandate_id"] != first["mandate_id"]       # a new approval, a new mandate


# ---- the loop: proposals authorized at registration, budget, expiry, Stop ----------------------

def test_mandate_proposals_are_authorized_without_accept_within_budget(authority) -> None:
    mandate = _create(authority, max_edits=2)
    pid, reply = _propose(authority, mandate["mandate_id"])
    assert reply["state"] == "AUTHORIZED" and reply["edit_index"] == 1 and reply["max_edits"] == 2
    fields = _run(authority, pid)
    assert fields["channel"] == "MANDATE" and fields["mandate_id"] == mandate["mandate_id"]
    assert fields["writable_path_prefixes"] == ["scenes/courtyard/"]      # the mandate's scope, not the policy's
    assert fields["protected_paths"] == ["project.godot", "scenes/locked/"]
    pid2, reply2 = _propose(authority, mandate["mandate_id"])
    assert reply2["edit_index"] == 2
    _run(authority, pid2)
    state = authority.state(PROPOSER, {"installation_id": INSTALLATION})["mandate"]
    assert state["state"] == "EXHAUSTED" and state["edits_recorded"] == 2
    with pytest.raises(ea.EditAuthorityError) as exc:
        _propose(authority, mandate["mandate_id"])
    assert _code(exc) == "MANDATE_NOT_ACTIVE"


def test_one_edit_at_a_time(authority) -> None:
    mandate = _create(authority)
    pid, _ = _propose(authority, mandate["mandate_id"])
    with pytest.raises(ea.EditAuthorityError) as exc:     # authorized, not yet run
        _propose(authority, mandate["mandate_id"])
    assert _code(exc) == "OPERATION_IN_FLIGHT"
    _run(authority, pid)
    _propose(authority, mandate["mandate_id"])            # after its outcome, the next may follow


def test_refused_registration_leaves_no_proposal(authority) -> None:
    with pytest.raises(ea.EditAuthorityError):
        _propose(authority, "mandate_0000000000000000")
    assert authority.state(PROPOSER, {"installation_id": INSTALLATION})["pending"] == []


def test_expiry_ends_the_mandate_and_voids_its_grant(authority, clock: Clock) -> None:
    mandate = _create(authority, ttl=60)
    pid, reply = _propose(authority, mandate["mandate_id"])
    assert reply["expires_at"] == mandate["expires_at"]
    clock.now += 61
    assert authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"] == []
    assert authority.proposal_record(pid)["state"] == "AUTHORIZATION_REVOKED"
    assert authority.state(APPROVER, {"installation_id": INSTALLATION})["mandate"]["state"] == "EXPIRED"
    with pytest.raises(ea.EditAuthorityError) as exc:
        _propose(authority, mandate["mandate_id"])
    assert _code(exc) == "MANDATE_NOT_ACTIVE"


def test_grant_never_outlives_its_mandate(authority, clock: Clock) -> None:
    mandate = _create(authority, ttl=60)
    _, reply = _propose(authority, mandate["mandate_id"])
    assert reply["expires_at"] == mandate["expires_at"] < clock.now + ea.GRANT_TTL_S


def test_stop_revokes_and_an_issued_grant_can_no_longer_be_consumed(authority) -> None:
    mandate = _create(authority)
    pid, _ = _propose(authority, mandate["mandate_id"])
    grant = json.loads(authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"][0]["grant_json"])
    for client in (PROPOSER, EXECUTOR):
        with pytest.raises(ea.EditAuthorityError):
            authority.revoke_mandate(client, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"],
                                              "evidence": DOCK})
    view = authority.revoke_mandate(APPROVER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"],
                                               "evidence": DOCK})
    assert view["state"] == "REVOKED"
    with pytest.raises(ea.EditAuthorityError) as exc:
        authority.consume(EXECUTOR, {"installation_id": INSTALLATION, "grant_id": grant["grant_id"], "proposal_id": pid,
                                     "body_sha256": grant["body_sha256"], "current_scope_sha256": "f" * 64})
    assert _code(exc) == "GRANT_NOT_CONSUMABLE"
    with pytest.raises(ea.EditAuthorityError) as exc:
        authority.revoke_mandate(APPROVER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"],
                                            "evidence": DOCK})
    assert _code(exc) == "MANDATE_NOT_ACTIVE"


def test_dragon_can_complete_but_never_create_or_revoke(authority) -> None:
    mandate = _create(authority)
    with pytest.raises(ea.EditAuthorityError):
        authority.complete_mandate(EXECUTOR, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"],
                                              "summary": "done"})
    view = authority.complete_mandate(PROPOSER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"],
                                                 "summary": "Courtyard built."})
    assert view["state"] == "COMPLETED" and view["summary"] == "Courtyard built."


def test_out_of_scope_outcome_revokes_the_mandate(authority) -> None:
    mandate = _create(authority)
    pid, _ = _propose(authority, mandate["mandate_id"])
    _run(authority, pid, changed=("scenes/courtyard/A.tscn", "scripts/evil.gd"))
    view = authority.state(APPROVER, {"installation_id": INSTALLATION})["mandate"]
    assert view["state"] == "REVOKED" and "scripts/evil.gd" in view["end_reason"]


def test_audit_trail_records_every_step(authority) -> None:
    mandate = _create(authority)
    pid, _ = _propose(authority, mandate["mandate_id"])
    _run(authority, pid)
    authority.complete_mandate(PROPOSER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"], "summary": "ok"})
    kinds = [e["kind"] for e in authority.events()]
    assert kinds == ["mandate_created", "proposal_registered", "proposal_authorized", "grant_consumed", "edit_outcome",
                     "mandate_ended"]
    created = authority.events()[0]
    assert created["max_edits"] == 3 and created["writable_path_prefixes"] == ["scenes/courtyard/"]


def test_mandate_survives_restart_but_its_unconsumed_grant_does_not(tmp_path: Path, clock: Clock) -> None:
    auth = _authority(tmp_path, clock)
    mandate = _create(auth)
    pid, _ = _propose(auth, mandate["mandate_id"])
    auth.close()
    auth = _authority(tmp_path, clock)
    try:
        assert auth.proposal_record(pid)["state"] == "AUTHORIZATION_LOST"
        assert auth.state(APPROVER, {"installation_id": INSTALLATION})["mandate"]["state"] == "ACTIVE"
        assert auth.pickup(EXECUTOR, {"installation_id": INSTALLATION})["grants"] == []
    finally:
        auth.close()


def test_legacy_ledger_without_mandates_still_loads(tmp_path: Path, clock: Clock) -> None:
    legacy = {k: v for k, v in ea._empty_ledger().items() if k not in ("mandates", "promotions")}
    (tmp_path / "ledger.json").write_text(json.dumps(legacy))
    auth = _authority(tmp_path, clock)
    try:
        assert _create(auth)["state"] == "ACTIVE"
    finally:
        auth.close()


# ---- ENTIRE_GAME workspace and promotion --------------------------------------------------------

def _entire_game(auth) -> dict:
    mandate = _create(auth, mode="ENTIRE_GAME", prefixes=["game/"], workspace="ws_my_game", max_edits=5)
    pid, _ = _propose(auth, mandate["mandate_id"], body="Create project.godot and scenes/Main.tscn")
    fields = _run(auth, pid, changed=("game/project.godot", "game/scenes/Main.tscn", "game/scripts/player.gd"))
    assert fields["workspace_id"] == "ws_my_game" and fields["writable_path_prefixes"] == ["game/"]
    assert fields["protected_paths"] == []      # the isolated workspace protects nothing of the open project
    return mandate


def _promote(auth, mandate_id, manifest, allow=False):
    return auth.create_promotion(APPROVER, {"installation_id": INSTALLATION, "mandate_id": mandate_id, "manifest": manifest,
                                            "base_scope_sha256": "b" * 64, "allow_editor_code": allow, "evidence": DOCK})


def _entry(path, editor_code=False):
    return {"path": path, "sha256": "c" * 64, "editor_code": editor_code}


def test_entire_game_workspace_edits_cover_project_files_only_inside_the_workspace(authority) -> None:
    mandate = _entire_game(authority)
    assert authority.state(APPROVER, {"installation_id": INSTALLATION})["mandate"]["state"] == "ACTIVE"
    with pytest.raises(ea.EditAuthorityError) as exc:            # still running: no promotion
        _promote(authority, mandate["mandate_id"], [_entry("scenes/Main.tscn")])
    assert _code(exc) == "MANDATE_STILL_ACTIVE"


def test_promotion_needs_the_approver_and_stays_inside_the_policy(authority) -> None:
    mandate = _entire_game(authority)
    authority.complete_mandate(PROPOSER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"], "summary": "ok"})
    for client in (PROPOSER, EXECUTOR):
        with pytest.raises(ea.EditAuthorityError):
            authority.create_promotion(client, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"],
                                                "manifest": [_entry("scenes/Main.tscn")], "base_scope_sha256": "b" * 64,
                                                "allow_editor_code": False, "evidence": DOCK})
    for path in ("project.godot", "assets/x.png", "scenes/locked/x.tscn", "../x.tscn"):
        with pytest.raises(ea.EditAuthorityError) as exc:
            _promote(authority, mandate["mandate_id"], [_entry(path)], allow=True)
        assert _code(exc) in ("SCOPE_NOT_PERMITTED", "SCHEMA_INVALID"), path


@pytest.mark.parametrize("entry", [_entry("scripts/player.gd"), _entry("scenes/Main.tscn", editor_code=True),
                                   _entry("scenes/level.scn"), _entry("scripts/addon.gdextension")])
def test_editor_executable_files_are_never_promoted_without_explicit_approval(authority, entry) -> None:
    mandate = _entire_game(authority)
    authority.revoke_mandate(APPROVER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"], "evidence": DOCK})
    with pytest.raises(ea.EditAuthorityError) as exc:
        _promote(authority, mandate["mandate_id"], [entry])
    assert _code(exc) == "EDITOR_CODE_NOT_ALLOWED"
    reply = _promote(authority, mandate["mandate_id"], [entry], allow=True)
    assert reply["editor_code_paths"] == [entry["path"]]


def test_promotion_lifecycle_and_revert_slot(authority) -> None:
    mandate = _entire_game(authority)
    authority.complete_mandate(PROPOSER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"], "summary": "ok"})
    manifest = [_entry("scenes/Main.tscn"), _entry("scenes/Level.tscn")]
    reply = _promote(authority, mandate["mandate_id"], manifest)
    signed = authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["promotions"]
    assert len(signed) == 1 and authority.verify_grant(signed[0]["grant_json"], signed[0]["grant_signature_b64"])
    fields = json.loads(signed[0]["grant_json"])
    assert fields["contract"] == ea.PROMOTION_GRANT_CONTRACT and fields["manifest_sha256"] == reply["manifest_sha256"]
    with pytest.raises(ea.EditAuthorityError) as exc:
        authority.consume_promotion(EXECUTOR, {"installation_id": INSTALLATION, "grant_id": fields["grant_id"],
                                               "promotion_id": fields["promotion_id"], "manifest_sha256": "0" * 64,
                                               "current_scope_sha256": "b" * 64})
    assert _code(exc) == "MANIFEST_MISMATCH"
    authority.consume_promotion(EXECUTOR, {"installation_id": INSTALLATION, "grant_id": fields["grant_id"],
                                           "promotion_id": fields["promotion_id"], "manifest_sha256": fields["manifest_sha256"],
                                           "current_scope_sha256": "b" * 64})
    out = authority.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "promotion",
                                              "promotion_id": fields["promotion_id"], "grant_id": fields["grant_id"],
                                              "edit_id": "edit_promo", "ok": True, "receipt_state": "AVAILABLE",
                                              "changed_paths": ["scenes/Level.tscn", "scenes/Main.tscn"]})
    assert out["state"] == "COMPLETED" and out["revert_slot"]["edit_id"] == "edit_promo"
    with pytest.raises(ea.EditAuthorityError) as exc:
        _promote(authority, mandate["mandate_id"], manifest)
    assert _code(exc) == "PROMOTION_DUPLICATE"


def test_promotion_is_stale_if_the_project_changed_after_review(authority) -> None:
    mandate = _entire_game(authority)
    authority.complete_mandate(PROPOSER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"], "summary": "ok"})
    _promote(authority, mandate["mandate_id"], [_entry("scenes/Main.tscn")])
    fields = json.loads(authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["promotions"][0]["grant_json"])
    with pytest.raises(ea.EditAuthorityError) as exc:
        authority.consume_promotion(EXECUTOR, {"installation_id": INSTALLATION, "grant_id": fields["grant_id"],
                                               "promotion_id": fields["promotion_id"],
                                               "manifest_sha256": fields["manifest_sha256"], "current_scope_sha256": "d" * 64})
    assert _code(exc) == "TARGET_STATE_CHANGED"
    assert authority.state(APPROVER, {"installation_id": INSTALLATION})["promotion"]["state"] == "STALE"


def test_promotion_outcome_outside_manifest_is_failed(authority) -> None:
    mandate = _entire_game(authority)
    authority.complete_mandate(PROPOSER, {"installation_id": INSTALLATION, "mandate_id": mandate["mandate_id"], "summary": "ok"})
    _promote(authority, mandate["mandate_id"], [_entry("scenes/Main.tscn")])
    fields = json.loads(authority.pickup(EXECUTOR, {"installation_id": INSTALLATION})["promotions"][0]["grant_json"])
    authority.consume_promotion(EXECUTOR, {"installation_id": INSTALLATION, "grant_id": fields["grant_id"],
                                           "promotion_id": fields["promotion_id"], "manifest_sha256": fields["manifest_sha256"],
                                           "current_scope_sha256": "b" * 64})
    out = authority.record_outcome(EXECUTOR, {"installation_id": INSTALLATION, "kind": "promotion",
                                              "promotion_id": fields["promotion_id"], "grant_id": fields["grant_id"],
                                              "edit_id": "e1", "ok": True, "receipt_state": "AVAILABLE",
                                              "changed_paths": ["scenes/Main.tscn", "scenes/Other.tscn"]})
    assert out["state"] == "FAILED"


def test_single_task_flow_is_unchanged_by_an_active_mandate(authority) -> None:
    _create(authority)
    pid, reply = _propose(authority, None)
    assert reply["state"] == "PENDING" and "mandate_id" not in reply     # still needs a human accept


def test_dragon_receives_test_result_observation_and_mandate_bounds() -> None:
    from tier1.engainos.core.continuity_context_builder import ContinuityContextBuilder
    report = {"status": "applied", "execution_summary": "Created 1 file(s).", "result_text": None,
              "validation_result": {"status": "failed", "checks": [{"path": "scenes/Main.tscn", "status": "failed",
                                                                    "error": "parse error line 3"}]},
              "runtime_result": {"status": "observed",
                                 "observation": {"summary": "scenes/Main.tscn ran 30 frames, 3 nodes",
                                                 "lines": ["Main (Node3D)", "Main/Torch (OmniLight3D) at (1, 2, 0)"]},
                                 "mandate": {"mandate_id": "mandate_1", "mode": "FULL_SCENE", "state": "ACTIVE",
                                             "edits_authorized": 2, "max_edits": 5, "goal": GOAL,
                                             "writable_path_prefixes": ["scenes/courtyard/"]}}}
    text = ContinuityContextBuilder().build([], "", 0, coordination_report=report)
    for expected in ("test: failed", "scenes/Main.tscn: parse error line 3", "observation (observed): scenes/Main.tscn ran",
                     "Main/Torch (OmniLight3D) at (1, 2, 0)", "edit 2 of 5 used", f"goal: {GOAL}",
                     "writable scope: scenes/courtyard/", "do not add other objectives", "[MANDATE_COMPLETE]"):
        assert expected in text, expected
    plain = ContinuityContextBuilder().build([], "", 0, coordination_report={
        "status": "applied", "execution_summary": "x", "validation_result": {"status": "not_checked", "checks": []},
        "runtime_result": {"status": "not_checked"}})
    assert "test:" not in plain and "observation" not in plain and "mandate" not in plain


def test_dragon_can_tell_the_post_edit_world_from_the_one_it_saw_before() -> None:
    from tier1.engainos.core.continuity_context_builder import ContinuityContextBuilder
    observation = {"summary": "res://scenes/Main.tscn ran 30 frames: 3 nodes", "lines": ["Main (Node3D)"],
                   "observation_id": "obs_2_bbbbbbbb", "phase": "post_edit", "previous_observation_id": "obs_1_aaaaaaaa",
                   "world_changed": True,
                   "screenshot": {"observation_id": "obs_2_bbbbbbbb", "path": "/lane/observations/obs_2_bbbbbbbb.png",
                                  "sha256": "ab" * 32}}
    report = {"status": "applied", "execution_summary": "x", "validation_result": {"status": "passed", "checks": []},
              "runtime_result": {"status": "observed", "observation": observation}}
    text = ContinuityContextBuilder().build([], "", 0, coordination_report=report)
    assert "id obs_2_bbbbbbbb (post_edit); previous obs_1_aaaaaaaa, world changed since then" in text
    # Continuity dispatch carries no image, so the screenshot is named, never claimed as seen.
    assert "screenshot: /lane/observations/obs_2_bbbbbbbb.png (sha256 " + "ab" * 32 + "); not attached" in text
    observation.update(previous_observation_id=None, world_changed=None, screenshot={})
    first = ContinuityContextBuilder().build([], "", 0, coordination_report=report)
    assert "no earlier observation of this world" in first and "screenshot:" not in first


# ---- scene_ref: the mandate names the exact EngAIn packet it is built from ---------------------

SCENE_ID = "scene.book001.003_first_contact.scene001"
SHA = "a" * 64


def _scene_authority(tmp_path: Path, clock: Clock, packets: dict[str, str] | None):
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps(_policy(["FULL_SCENE", "ENTIRE_GAME"])))

    def sha_of(scene_id: str) -> str:
        if scene_id not in packets:
            raise FileNotFoundError(scene_id)
        return packets[scene_id]

    return ea.EditorEditAuthority(policy=ea.load_edit_policy(policy), ledger_path=tmp_path / "ledger.json", clock=clock,
                                  scene_packet_sha256=None if packets is None else sha_of)


def _create_for_scene(auth, scene_ref):
    return auth.create_mandate(APPROVER, {"installation_id": INSTALLATION, "mode": "FULL_SCENE", "goal": GOAL,
                                          "writable_path_prefixes": ["scenes/courtyard/"], "workspace_id": "",
                                          "max_edits": 3, "ttl_s": 3600, "evidence": DOCK, "scene_ref": scene_ref})


def test_a_matching_scene_ref_is_recorded_on_the_mandate(tmp_path: Path, clock: Clock) -> None:
    auth = _scene_authority(tmp_path, clock, {SCENE_ID: SHA})
    view = _create_for_scene(auth, {"scene_id": SCENE_ID, "packet_sha256": SHA})
    assert view["scene_ref"] == {"scene_id": SCENE_ID, "packet_sha256": SHA}
    assert auth.state(APPROVER, {"installation_id": INSTALLATION})["mandate"]["scene_ref"]["packet_sha256"] == SHA
    auth.close()


@pytest.mark.parametrize("packets, ref, code", [
    ({SCENE_ID: "b" * 64}, {"scene_id": SCENE_ID, "packet_sha256": SHA}, "SCENE_REF_STALE"),
    ({}, {"scene_id": SCENE_ID, "packet_sha256": SHA}, "SCENE_REF_UNKNOWN"),
    (None, {"scene_id": SCENE_ID, "packet_sha256": SHA}, "SCENE_REF_UNVERIFIABLE"),  # fails closed
    ({SCENE_ID: SHA}, {"scene_id": SCENE_ID, "packet_sha256": SHA.upper()}, "SCHEMA_INVALID"),
    ({SCENE_ID: SHA}, {"scene_id": SCENE_ID, "packet_sha256": SHA, "extra": 1}, "SCHEMA_INVALID"),
    ({SCENE_ID: SHA}, {"scene_id": SCENE_ID}, "SCHEMA_INVALID"),
])
def test_a_scene_ref_that_does_not_verify_creates_no_mandate(tmp_path: Path, clock: Clock, packets, ref, code) -> None:
    auth = _scene_authority(tmp_path, clock, packets)
    with pytest.raises(ea.EditAuthorityError) as exc:
        _create_for_scene(auth, ref)
    assert exc.value.code == code
    assert auth._ledger.data["mandates"] == {}
    auth.close()
