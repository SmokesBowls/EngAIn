"""8765 /trixel32d/build + /trixel32d/consume: authentication, policy identity,
runtime reality mode, Godot testimony, scene-bound lifecycle, ledger/receipt,
one-time grants, and fail-closed composition.

The end-to-end cases invoke the real trixel3.2d consumer subprocess; every
runtime path (drops, receipts, ledger, credentials) is redirected into tmp_path.

The client policy here is a disposable test fixture. Production policy is
deny-all (tier1/engainos/authority/TRIXEL32D_LIVE_CLIENT_POLICY_V1.json) until
a human assigns clients.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import pytest

import tier1.engainos.bridgeroom.trixel32d_live_route as route
from tier1.engainos.authority.local_signed_transport import (
    ClientAssignment,
    SignedRequestVerifier,
    load_client_policy,
    signed_headers,
)
from tier1.engainos.authority.trixel32d_application_grant import GRANT_FIELDS, GrantSigner
from tier1.engainos.authority.trixel32d_live_authority_state import (
    AuthorityStateError, LiveAuthorityState, scene_revision_of,
)
from tier1.engainos.bridgeroom import scene_server
from tier1.engainos.tests.test_trixel32d_bound_assembly import TEST_BASIS, contributions

SCENE = {"scene_id": "scene-live-route", "segments": [{"text": "live"}], "entities": []}
LOAD_1 = ("runtime-instance-a", 1, SCENE["scene_id"])
SLOT = ("RUNTIME_CONTAINER", "container-terrain-live", "slot-live-terrain")
IDENTITY_BASIS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
OBSERVATION = {"main_instance_id": 7, "local_generation": 0}
BUILD, CONSUME = "/trixel32d/build", "/trixel32d/consume"

BUILDER, PRESENTER = "test-builder", "test-presenter"
POLICY = {
    BUILDER: ClientAssignment("disposable-test-builder", 2, frozenset({"build"})),
    PRESENTER: ClientAssignment(None, None, frozenset({"consume"})),
}
SECRETS = {BUILDER: b"\x01" * 32, PRESENTER: b"\x02" * 32}
SIGNER = GrantSigner()  # RSA key generation is slow; one per test module


class Env:
    def __init__(self, tmp_path, monkeypatch):
        self.tmp = tmp_path
        self.runtime = tmp_path / "runtime"
        self.ledger = self.runtime / "ledger.jsonl"
        self.load = LOAD_1
        self.scene = dict(SCENE)
        self.observation = dict(OBSERVATION)
        self.godot_load = None  # None: Godot has rendered the current load
        self.reality = {"mode": "DRAFT", "scene_id": None}
        self.truth_dir = tmp_path / "scene_truth"
        self.truth = self.declare(SCENE)
        monkeypatch.setattr(route, "RUNTIME_DIR", self.runtime)
        monkeypatch.setattr(route, "LEDGER_PATH", self.ledger)
        monkeypatch.setattr(route, "SCENE_TRUTH_DIR", self.truth_dir)
        monkeypatch.setattr(route, "_fetch_runtime_scene", lambda: (dict(self.scene), self.load, self.reality))
        self.authority = self.compose()

    def declare(self, scene, **changes):
        """Authority-owned target declarations for exactly this scene revision."""
        self.truth_dir.mkdir(exist_ok=True)
        path = self.truth_dir / f"{scene['scene_id']}.json"
        path.write_text(json.dumps({
            "contract": route.SCENE_TRUTH_CONTRACT,
            "scene_id": scene["scene_id"],
            "scene_revision": scene_revision_of(scene),
            "declared_targets": [
                list(SLOT),
                ["RUNTIME_CONTAINER", "container-terrain-live", "slot-taken"],
                ["RUNTIME_CONTAINER", "container-terrain-live", "slot-second"],
            ],
            "slot_occupancy": {"slot-taken": "t32dapply_feedfacefeedface"},
            **changes,
        }))
        return path

    def compose(self):
        return route.LiveRouteAuthority(
            self.ledger,
            verifier=SignedRequestVerifier(SECRETS),
            client_policy=POLICY,
            observation_source=lambda: self.testimony(),
            grant_signer=SIGNER,
        )

    def testimony(self):
        runtime_instance_id, load_seq, scene_id = self.godot_load or self.load
        return {
            "observed_load": {"runtime_instance_id": runtime_instance_id, "load_seq": load_seq, "scene_id": scene_id},
            "presentation_active": True,
            **self.observation,
        }

    def post(self, path, body, client=BUILDER, headers=None):
        raw = json.dumps(body).encode("utf-8")
        headers = headers if headers is not None else signed_headers(client, SECRETS[client], "POST", path, raw)
        return route.handle_http("POST", path, headers, raw, self.authority)

    def build(self, body, client=BUILDER):
        return self.post(BUILD, body, client)

    def consume(self, authorized, *, testimony=None, client=PRESENTER, artifact_sha256=None):
        entry = authorized["ledger_entry"]
        return self.post(CONSUME, {
            "decision_id": entry["decision_id"],
            "apply_id": entry["apply_id"],
            "artifact_sha256": artifact_sha256 or entry["artifact_sha256"],
            **(testimony if testimony is not None else self.testimony()),
        }, client)

    def ledger_events(self):
        if not self.ledger.exists():
            return []
        return [json.loads(line)["event"] for line in self.ledger.read_text().splitlines()]

    def side_effects(self):
        return list(self.runtime.glob("trixel32d_*"))


@pytest.fixture
def live_env(tmp_path, monkeypatch):
    env = Env(tmp_path, monkeypatch)
    yield env
    env.authority.close()


def _body(**overrides):
    body = {
        "placement": {
            "mode": "scene_bound",
            "parent_kind": SLOT[0],
            "parent_id": SLOT[1],
            "application_slot_id": SLOT[2],
            "origin": [0.0, 0.0, 0.0],
            "basis_columns": IDENTITY_BASIS,
            "visibility": "VISIBLE",
        },
        "collision": {"mode": "denied"},
        "surface": dict(zip(
            ("grid_facts", "metric_grant", "provenance", "construction_policy"),
            contributions(basis=dict(TEST_BASIS, scene_id=SCENE["scene_id"])),
        )),
    }
    body.update(overrides)
    return body


def _surface(topology_artifact_id):
    # A different provenance yields a different request.
    surface = _body()["surface"]
    return dict(surface, provenance=dict(surface["provenance"], topology_artifact_id=topology_artifact_id))


def _second_slot(topology_artifact_id):
    return _body(placement=dict(_body()["placement"], application_slot_id="slot-second"),
                 surface=_surface(topology_artifact_id))


# ── Boundary rejections ──────────────────────────────────────────────

@pytest.mark.parametrize("field,value", [
    ("placement", {"mode": "canonical_persistent"}),
    ("placement", {}),
    ("collision", {"mode": "granted"}),
    ("collision", {}),
])
def test_placement_and_collision_modes_hard_reject(live_env, field, value):
    status, body = live_env.build(_body(**{field: value}))
    assert status == 403 and body["status"] == "REJECTED"
    assert not live_env.side_effects()


def test_route_without_composed_authority_fails_closed():
    status, body = route.handle_http("POST", BUILD, {}, b"{}", None)
    assert status == 503 and "not composed" in body["errors"][0]


def test_unknown_trixel_route_is_404(live_env):
    assert live_env.post("/trixel32d/other", {})[0] == 404


# ── Authentication (B4) ──────────────────────────────────────────────

def _assert_unauthenticated(env, status, body, reason):
    assert status == 401 and reason in body["errors"][0], body
    assert not env.side_effects() and env.ledger_events() == []


def test_unsigned_request_is_refused_before_any_side_effect(live_env):
    status, body = live_env.post(BUILD, _body(), headers={})
    _assert_unauthenticated(live_env, status, body, "not signed")


def test_signature_over_a_different_body_is_refused(live_env):
    headers = signed_headers(BUILDER, SECRETS[BUILDER], "POST", BUILD, b"{}")
    status, body = live_env.post(BUILD, _body(), headers=headers)
    _assert_unauthenticated(live_env, status, body, "does not verify")


def test_signature_for_another_route_is_refused(live_env):
    raw = json.dumps(_body()).encode()
    headers = signed_headers(BUILDER, SECRETS[BUILDER], "POST", CONSUME, raw)
    status, body = route.handle_http("POST", BUILD, headers, raw, live_env.authority)
    _assert_unauthenticated(live_env, status, body, "does not verify")


def test_unknown_client_is_refused(live_env):
    raw = json.dumps(_body()).encode()
    headers = signed_headers("test-stranger", b"\x09" * 32, "POST", BUILD, raw)
    status, body = route.handle_http("POST", BUILD, headers, raw, live_env.authority)
    _assert_unauthenticated(live_env, status, body, "not a provisioned")


def test_stale_timestamp_is_refused(live_env):
    raw = json.dumps(_body()).encode()
    headers = signed_headers(BUILDER, SECRETS[BUILDER], "POST", BUILD, raw, now=1_000_000)
    status, body = route.handle_http("POST", BUILD, headers, raw, live_env.authority)
    _assert_unauthenticated(live_env, status, body, "freshness")


def test_replayed_request_is_refused(live_env):
    raw = json.dumps(_body(collision={"mode": "granted"})).encode()
    headers = signed_headers(BUILDER, SECRETS[BUILDER], "POST", BUILD, raw)
    assert route.handle_http("POST", BUILD, headers, raw, live_env.authority)[0] == 403
    status, body = route.handle_http("POST", BUILD, headers, raw, live_env.authority)
    _assert_unauthenticated(live_env, status, body, "already used")


def test_client_without_the_route_assignment_is_refused(live_env):
    status, body = live_env.build(_body(), client=PRESENTER)
    assert status == 403 and "not assigned the 'build' route" in body["errors"][0]
    assert not live_env.side_effects()


def test_identity_comes_from_policy_and_never_from_the_body(live_env):
    status, body = live_env.build(_body(
        principal={"actor_id": "stranger", "actor_authority_tier": 3, "reality_mode": "FINALIZED"},
        actor_id="stranger", actor_authority_tier=3, reality_mode="FINALIZED",
        semantic={"main_instance_id": 999, "local_generation": 42},
    ))
    assert status == 200, body
    evidence = body["authorization"]["authority_evidence"]
    assigned = POLICY[BUILDER]
    assert (evidence["actor_id"], evidence["actor_authority_tier"], evidence["reality_mode"]) == (
        assigned.actor_id, assigned.actor_authority_tier, "DRAFT")
    semantic = body["authorization"]["semantic_activation"]
    assert semantic["semantic_main_instance_id"] == OBSERVATION["main_instance_id"]
    assert semantic["semantic_local_generation"] == OBSERVATION["local_generation"]


# ── Runtime reality mode ─────────────────────────────────────────────

@pytest.mark.parametrize("reality,reason", [
    ({"mode": "IMBUED", "scene_id": None}, "'IMBUED' has no defined handling"),
    ({"mode": "DREAM", "scene_id": None}, "'DREAM' has no defined handling"),
    ({"mode": "TEST", "scene_id": None}, "'TEST' has no defined handling"),
    (None, "not published"),
    ({"mode": "DRAFT", "scene_id": "scene-other"}, "scoped to 'scene-other'"),
])
def test_runtime_reality_modes_without_defined_handling_are_refused(live_env, reality, reason):
    live_env.reality = reality
    status, body = live_env.build(_body())
    assert status == 409 and reason in body["errors"][0], body
    assert not live_env.side_effects() and live_env.ledger_events() == []


def test_runtime_replay_mode_refuses_issuance(live_env):
    live_env.reality = {"mode": "REPLAY", "scene_id": None}
    status, body = live_env.build(_body())
    assert status == 403 and "REPLAY" in body["errors"][0]
    assert live_env.ledger_events() == []


def test_runtime_finalized_mode_requires_tier_3(live_env):
    live_env.reality = {"mode": "FINALIZED", "scene_id": None}
    status, body = live_env.build(_body())
    assert status == 403 and "Tier 3" in body["errors"][0]
    assert live_env.ledger_events() == []


# ── Godot testimony (B3) ─────────────────────────────────────────────

@pytest.mark.parametrize("godot_load", [
    ("runtime-instance-a", 1, SCENE["scene_id"]),           # an older load of the same scene
    ("runtime-instance-a", 3, SCENE["scene_id"]),           # a load the runtime has not made
    ("runtime-instance-b", 2, SCENE["scene_id"]),           # another runtime process
    ("runtime-instance-a", 2, "scene-other"),               # another scene
])
def test_godot_testimony_for_another_load_is_refused(live_env, godot_load):
    live_env.load = ("runtime-instance-a", 2, SCENE["scene_id"])
    live_env.godot_load = godot_load
    status, body = live_env.build(_body())
    assert status == 409 and "different runtime scene load" in body["errors"][0]
    assert live_env.ledger_events() == []


@pytest.mark.parametrize("testimony", [
    None,
    {"main_instance_id": 7, "local_generation": 0},  # no observed_load: nothing to bind to
    {"observed_load": {"runtime_instance_id": "runtime-instance-a", "load_seq": True,
                       "scene_id": SCENE["scene_id"]}, "main_instance_id": 7, "local_generation": 0},
])
def test_malformed_godot_testimony_is_refused(live_env, testimony):
    live_env.testimony = lambda: testimony
    status, body = live_env.build(_body())
    assert status == 409 and "Godot observation" in body["errors"][0]
    assert live_env.ledger_events() == []


def test_inactive_presentation_testimony_is_refused(live_env):
    live_env.observation = dict(OBSERVATION, presentation_active=False)
    status, body = live_env.build(_body())
    assert status == 409 and "active presentation" in body["errors"][0]
    assert live_env.ledger_events() == []


def test_replayed_older_godot_generation_is_refused(live_env):
    live_env.observation = {"main_instance_id": 7, "local_generation": 5}
    assert live_env.build(_body())[0] == 200
    live_env.observation = {"main_instance_id": 7, "local_generation": 4}
    status, body = live_env.build(_second_slot("topology.proof.005"))
    assert status == 403 and "stale" in body["errors"][0]
    assert live_env.ledger_events() == ["authorization_issued"]


def test_declared_occupied_slot_rejects(live_env):
    placement = dict(_body()["placement"], application_slot_id="slot-taken")
    status, body = live_env.build(_body(placement=placement))
    assert status == 409 and "occupied" in body["errors"][0]


def test_rejected_issuance_writes_neither_ledger_record_nor_evidence(live_env):
    live_env.observation = {"main_instance_id": 0, "local_generation": 0}
    status, body = live_env.build(_body())
    assert status == 403 and body["status"] == "REJECTED"
    assert live_env.ledger_events() == []
    assert not list(live_env.runtime.glob("trixel32d_reports/*/*"))


# ── Live build ───────────────────────────────────────────────────────

def test_live_build_authorizes_once_then_slot_refuses(live_env):
    status, body = live_env.build(_body())
    assert status == 200, body
    packet = body["authorization"]["apply_packet"]
    assert packet["lifetime"]["mode"] == "SCENE_BOUND"
    assert packet["collision"]["decision"] == "DENIED"
    assert packet["target"]["application_slot_id"] == SLOT[2]
    assert packet["surface_binding"]["built_response_sha256"] == body["built_response_sha256"]
    assert live_env.ledger_events() == ["authorization_issued"]
    status, body = live_env.build(_body())
    assert status == 409 and "already exists" in body["errors"][0]


def test_authorization_file_is_the_exact_ledger_artifact(live_env):
    status, body = live_env.build(_body())
    assert status == 200, body
    data = (live_env.tmp / body["authorization_file"]).read_bytes()
    ledger_event = json.loads(live_env.ledger.read_text().splitlines()[0])
    assert hashlib.sha256(data).hexdigest() == body["authorization_sha256"] == ledger_event["artifact_sha256"]
    assert json.loads(data) == ledger_event["artifact"]


def test_built_drop_ref_is_runtime_relative_when_runtime_is_outside_repo(live_env):
    assert not str(route.RUNTIME_DIR).startswith(str(route.REPO_ROOT))
    status, body = live_env.build(_body())
    assert status == 200, body
    ref = body["built_drop_dir"]
    slot = ref.rsplit("/", 1)[1]
    assert ref == f"runtime/trixel32d_built_drops/{slot}" and slot.startswith("t32ddrop_")
    assert (live_env.tmp / ref).is_dir()
    assert (live_env.runtime / "trixel32d_reports" / slot / route.RECEIPT_FILENAME).is_file()


# ── Consumption and one-time grants ──────────────────────────────────

def test_consume_returns_a_bound_signed_grant_once(live_env):
    status, authorized = live_env.build(_body())
    assert status == 200, authorized
    status, granted = live_env.consume(authorized)
    assert status == 200 and granted["status"] == "GRANTED", granted
    assert SIGNER.verify(granted["grant_json"], granted["grant_signature_b64"])
    grant = json.loads(granted["grant_json"])
    assert set(grant) == GRANT_FIELDS
    activation = authorized["authorization"]["scene_activation"]
    assert grant["client_id"] == PRESENTER
    assert grant["decision_id"] == authorized["ledger_entry"]["decision_id"]
    assert grant["artifact_sha256"] == authorized["authorization_sha256"]
    assert grant["runtime_session_id"] == live_env.authority.runtime_session_id
    assert (grant["activation_id"], grant["scene_revision"]) == (activation["activation_id"], activation["scene_revision"])
    assert grant["observed_load"] == live_env.testimony()["observed_load"]
    assert grant["expires_at"] - grant["issued_at"] == 30
    assert live_env.ledger_events() == ["authorization_issued", "authorization_consumed"]
    status, body = live_env.consume(authorized)
    assert status == 403 and "already consumed" in body["errors"][0]


def test_tampered_grant_does_not_verify(live_env):
    status, authorized = live_env.build(_body())
    status, granted = live_env.consume(authorized)
    assert status == 200
    forged = granted["grant_json"].replace('"load_seq":1', '"load_seq":2')
    assert forged != granted["grant_json"]
    assert not SIGNER.verify(forged, granted["grant_signature_b64"])
    assert not GrantSigner().verify(granted["grant_json"], granted["grant_signature_b64"])


def test_consume_with_a_forged_artifact_hash_is_refused(live_env):
    status, authorized = live_env.build(_body())
    status, body = live_env.consume(authorized, artifact_sha256="0" * 64)
    assert status == 403 and "hash does not match" in body["errors"][0]
    assert live_env.ledger_events() == ["authorization_issued"]


def test_builder_cannot_consume(live_env):
    status, authorized = live_env.build(_body())
    status, body = live_env.consume(authorized, client=BUILDER)
    assert status == 403 and "not assigned the 'consume' route" in body["errors"][0]


def test_consumer_testimony_must_match_the_reported_observation(live_env):
    status, authorized = live_env.build(_body())
    claimed = dict(live_env.testimony(), local_generation=9)
    status, body = live_env.consume(authorized, testimony=claimed)
    assert status == 409 and "disagrees" in body["errors"][0]
    assert live_env.ledger_events() == ["authorization_issued"]


def test_newer_godot_generation_makes_the_authorization_unusable(live_env):
    status, authorized = live_env.build(_body())
    live_env.observation = dict(OBSERVATION, local_generation=1)  # presentation changed after issuance
    status, body = live_env.consume(authorized)
    assert status == 403 and "different Semantic observation" in body["errors"][0]


def test_stale_consumer_testimony_is_refused(live_env):
    status, authorized = live_env.build(_body())
    live_env.load = ("runtime-instance-a", 2, SCENE["scene_id"])
    live_env.godot_load = LOAD_1  # Godot still reports the load it saw before the reload
    status, body = live_env.consume(authorized)
    assert status == 409 and "different runtime scene load" in body["errors"][0]


def test_reality_mode_change_after_issuance_refuses_consumption(live_env):
    status, authorized = live_env.build(_body())
    live_env.reality = {"mode": "REPLAY", "scene_id": None}
    status, body = live_env.consume(authorized)
    assert status == 409 and "reality mode changed" in body["errors"][0]
    assert live_env.ledger_events() == ["authorization_issued"]


# ── Scene-bound lifecycle ────────────────────────────────────────────

def test_different_request_to_same_slot_is_refused_within_one_load(live_env):
    assert live_env.build(_body())[0] == 200
    status, body = live_env.build(_body(surface=_surface("topology.proof.002")))
    assert status == 403 and "CREATE_ONLY application slot is occupied" in body["errors"][0]


def test_unchanged_load_keeps_one_activation_across_requests(live_env):
    status, first = live_env.build(_body())
    status, other = live_env.build(_second_slot("topology.proof.004"))
    assert status == 200, other
    assert (other["authorization"]["scene_activation"]["activation_id"]
            == first["authorization"]["scene_activation"]["activation_id"])


def test_same_scene_reload_invalidates_the_old_slot_and_its_authorization(live_env):
    status, first = live_env.build(_body())
    assert status == 200, first
    live_env.load = ("runtime-instance-a", 2, SCENE["scene_id"])  # same scene, reloaded
    status, second = live_env.build(_body())
    assert status == 200, second
    assert second["built_drop_dir"] != first["built_drop_dir"]
    assert (second["authorization"]["scene_activation"]["activation_id"]
            != first["authorization"]["scene_activation"]["activation_id"])
    status, body = live_env.consume(first)
    assert status == 403 and "different scene activation" in body["errors"][0]
    assert live_env.consume(second)[0] == 200


def test_different_scene_refuses_the_authorization(live_env):
    status, first = live_env.build(_body())
    assert status == 200, first
    other = "scene-other-live"
    live_env.scene = dict(SCENE, scene_id=other)
    live_env.declare(live_env.scene)
    live_env.load = ("runtime-instance-a", 2, other)
    status, body = live_env.consume(first)
    assert status == 403 and "different scene activation" in body["errors"][0]


def test_runtime_restart_is_a_new_load_identity(live_env):
    status, first = live_env.build(_body())
    live_env.load = ("runtime-instance-b", 1, SCENE["scene_id"])  # 8080 restarted: seq starts over
    assert live_env.build(_body())[0] == 200
    status, body = live_env.consume(first)
    assert status == 403 and "different scene activation" in body["errors"][0]


def test_process_restart_invalidates_authorizations_and_pending_work(live_env):
    status, first = live_env.build(_body())
    live_env.authority.close()
    live_env.authority = live_env.compose()  # 8765 restarted on the same ledger
    status, second = live_env.build(_body())
    assert status == 200, second
    assert second["built_drop_dir"] != first["built_drop_dir"]
    status, body = live_env.consume(first)
    assert status == 403 and "different runtime session" in body["errors"][0]


def test_load_change_during_a_build_is_refused(live_env, monkeypatch):
    holder = live_env.authority
    original = holder.authorize

    def authorize(**kwargs):
        # Another request observes a newer runtime load after this one took its activation.
        holder.sync_activation(dict(SCENE), ("runtime-instance-a", 9, SCENE["scene_id"]), {"declared_targets": []})
        return original(**kwargs)

    monkeypatch.setattr(holder, "authorize", authorize)
    status, body = live_env.build(_body())
    assert status == 409 and "changed during the request" in body["errors"][0]
    assert live_env.ledger_events() == []


def test_second_authority_cannot_open_a_held_ledger(live_env):
    with pytest.raises(AuthorityStateError, match="already owned"):
        live_env.compose()


# ── Ledger and receipt ───────────────────────────────────────────────

def test_receipt_references_its_ledger_entry(live_env):
    status, body = live_env.build(_body())
    slot = body["built_drop_dir"].rsplit("/", 1)[1]
    receipt = json.loads((live_env.runtime / "trixel32d_reports" / slot / route.RECEIPT_FILENAME).read_text())
    ledger_event = json.loads(live_env.ledger.read_text().splitlines()[0])
    assert receipt["authority_ledger_entry"] == body["ledger_entry"] == {
        "decision_id": ledger_event["decision_id"],
        "apply_id": ledger_event["apply_id"],
        "artifact_sha256": ledger_event["artifact_sha256"],
        "runtime_session_id": ledger_event["runtime_session_id"],
    }


def test_receipt_failure_is_explicit_and_never_yields_a_second_authorization(live_env, monkeypatch):
    def fail(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(route, "write_intake_receipt", fail)
    status, body = live_env.build(_body())
    assert status == 500
    decision_id = json.loads(live_env.ledger.read_text().splitlines()[0])["decision_id"]
    assert decision_id in body["errors"][0] and "recorded in the authority ledger" in body["errors"][0]
    # Retrying, identically or with another request for the slot, issues nothing new.
    assert live_env.build(_body())[0] == 409
    status, body = live_env.build(_body(surface=_surface("topology.proof.005")))
    assert status == 403 and "occupied" in body["errors"][0]
    assert live_env.ledger_events() == ["authorization_issued"]


# ── Composition root: fail closed without locking ────────────────────

def _ledger_is_free(path):
    state = LiveAuthorityState(path, "probe", principal_registration_capability=object(),
                               trusted_state_mutation_capability=object(),
                               authorization_commit_capability=object(),
                               decision_consumption_capability=object())
    state.close()
    return True


def _write_policy(path, clients):
    path.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": clients}))
    return path


@pytest.mark.parametrize("flag,policy,observed,reason", [
    (None, "valid", True, "is not '1'"),
    ("1", "missing", True, "deny-all"),
    ("1", "empty", True, "deny-all"),
    ("1", "tier0", True, "invalid"),
    ("1", "valid", False, "exactly one presentation observer (found 0)"),
    ("1", "two_observers", False, "exactly one presentation observer (found 2)"),
    ("1", "observer_only", False, "deny-all"),
])
def test_unconfigured_route_composes_nothing_and_locks_nothing(tmp_path, monkeypatch, flag, policy, observed, reason):
    if flag:
        monkeypatch.setenv(route.FLAG_ENV, flag)
    else:
        monkeypatch.delenv(route.FLAG_ENV, raising=False)
    policy_path = tmp_path / "policy.json"
    entry = {"actor_id": "disposable-test-builder", "actor_authority_tier": 2, "routes": ["build"]}
    if policy == "valid":
        _write_policy(policy_path, {BUILDER: entry})
    elif policy == "empty":
        _write_policy(policy_path, {})
    elif policy == "tier0":
        _write_policy(policy_path, {BUILDER: dict(entry, actor_authority_tier=0)})
    elif policy == "two_observers":
        _write_policy(policy_path, {BUILDER: entry, "obs-one": {"routes": ["observe"]}, "obs-two": {"routes": ["observe"]}})
    elif policy == "observer_only":
        _write_policy(policy_path, {"obs-one": {"routes": ["observe"]}})
    ledger, transport = tmp_path / "ledger" / "l.jsonl", tmp_path / "transport"
    authority, why = route.compose_from_environment(
        observation_source=(lambda: {}) if observed else None,
        ledger_path=ledger, policy_path=policy_path, transport_dir=transport,
    )
    assert authority is None and reason in why
    assert not ledger.exists() and not transport.exists()
    assert _ledger_is_free(ledger)


def test_configured_route_provisions_private_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv(route.FLAG_ENV, "1")
    policy_path = _write_policy(tmp_path / "policy.json", {
        BUILDER: {"actor_id": "disposable-test-builder", "actor_authority_tier": 2, "routes": ["build"]},
        "obs-one": {"routes": ["observe"]},
    })
    transport = tmp_path / "transport"
    authority, why = route.compose_from_environment(
        ledger_path=tmp_path / "l.jsonl", policy_path=policy_path, transport_dir=transport,
    )
    try:
        assert why == "composed"
        server_dir = transport / route.SERVER_NAME
        assert stat.S_IMODE(os.stat(server_dir).st_mode) == 0o700
        key = server_dir / f"{BUILDER}.key"
        assert stat.S_IMODE(os.stat(key).st_mode) == 0o600 and len(key.read_text()) == 64
        assert not (server_dir / "obs-one.key").exists()  # observers get 8080 credentials, not 8765's
        assert (server_dir / route.GRANT_PUBLIC_KEY_FILENAME).read_text() == authority.grant_public_key_pem
        with pytest.raises(AuthorityStateError, match="already owned"):
            _ledger_is_free(tmp_path / "l.jsonl")
    finally:
        authority.close()


def test_committed_production_policy_is_deny_all():
    assert load_client_policy(route.POLICY_PATH, route.KNOWN_ROUTES) == {}


def test_observation_source_reads_only_the_configured_observer_from_peek(monkeypatch):
    record = {"client_id": "obs-one", "observed_load": dict(STAMP), "presentation_active": True,
              "main_instance_id": 7, "local_generation": 0}
    envelope = {"presentation_observations": {"obs-one": record, "obs-two": dict(record, client_id="obs-two")}}
    seen = []

    def fake_urlopen(url, timeout):
        seen.append(url)
        return _Resp(json.dumps(envelope).encode())

    monkeypatch.setattr(route.urllib.request, "urlopen", fake_urlopen)
    assert route.runtime_observation_source("obs-one")() == record
    assert seen[0].endswith("/snapshot/peek")
    with pytest.raises(route.RouteError, match="no presentation observation"):
        route.runtime_observation_source("obs-three")()


def test_grant_signer_fails_closed_on_an_unpinned_cryptography(monkeypatch):
    import cryptography
    monkeypatch.setattr(cryptography, "__version__", "99.0.0")
    with pytest.raises(AuthorityStateError, match="re-verify and update the pin"):
        GrantSigner()


# ── Runtime read ─────────────────────────────────────────────────────

class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _peek(monkeypatch, payload, reality=None):
    seen = []

    def fake_urlopen(url, timeout):
        seen.append(url)
        envelope = {"payload": payload}
        if reality is not None:
            envelope["reality_context"] = reality
        return _Resp(json.dumps(envelope).encode())

    monkeypatch.setattr(route.urllib.request, "urlopen", fake_urlopen)
    return seen


STAMP = {"runtime_instance_id": "runtime-instance-a", "load_seq": 3, "scene_id": SCENE["scene_id"]}


def test_runtime_scene_is_read_from_the_non_consuming_peek(monkeypatch):
    reality = {"mode": "DRAFT", "scene_id": None}
    seen = _peek(monkeypatch, {"scene_id": SCENE["scene_id"], "scene": SCENE, "scene_activation": STAMP}, reality)
    scene, identity, context = route._fetch_runtime_scene()
    assert seen[0].endswith("/snapshot/peek")
    assert scene == SCENE and identity == ("runtime-instance-a", 3, SCENE["scene_id"]) and context == reality


@pytest.mark.parametrize("payload,reason", [
    ({"scene_id": SCENE["scene_id"], "scene": SCENE}, "no scene load identity"),
    ({"scene_id": SCENE["scene_id"], "scene": SCENE, "scene_activation": dict(STAMP, load_seq=0)}, "malformed"),
    ({"scene_id": SCENE["scene_id"], "scene": SCENE, "scene_activation": dict(STAMP, load_seq=True)}, "malformed"),
    ({"scene_id": SCENE["scene_id"], "scene": SCENE, "scene_activation": dict(STAMP, scene_id="other")}, "disagree"),
    ({"scene_id": SCENE["scene_id"], "scene": SCENE, "scene_activation": dict(STAMP, scene_id=None)}, "malformed"),
    ({"scene_id": "other", "scene": SCENE, "scene_activation": STAMP}, "disagree"),
])
def test_runtime_scene_without_a_consistent_load_identity_is_refused(monkeypatch, payload, reason):
    _peek(monkeypatch, payload)
    with pytest.raises(route.RouteError) as err:
        route._fetch_runtime_scene()
    assert err.value.status == 409 and reason in err.value.message


# ── 8765 wiring ──────────────────────────────────────────────────────

def _post_8765(monkeypatch, flag, authority, path):
    seen = []

    def fake_handle(method, req_path, headers, body, auth):
        seen.append((method, req_path, headers.get("X-EngAIn-Client"), body, auth))
        return 200, {"ok": True}

    monkeypatch.setattr(route, "handle_http", fake_handle)
    if flag:
        monkeypatch.setenv(route.FLAG_ENV, "1")
    else:
        monkeypatch.delenv(route.FLAG_ENV, raising=False)
    monkeypatch.setattr(scene_server.SceneRequestHandler, "trixel32d_authority", authority)
    server = HTTPServer(("127.0.0.1", 0), scene_server.SceneRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{server.server_address[1]}{path}",
            data=b'{"raw": 1}', method="POST",
            headers={"Content-Type": "application/json", "X-EngAIn-Client": "test-builder"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, seen
        except urllib.error.HTTPError as err:
            return err.code, seen
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize("path", [BUILD, CONSUME])
def test_scene_server_routes_are_404_while_flag_is_off(monkeypatch, path):
    status, seen = _post_8765(monkeypatch, flag=False, authority=object(), path=path)
    assert status == 404 and seen == []


@pytest.mark.parametrize("path", [BUILD, CONSUME])
def test_scene_server_hands_raw_bytes_and_headers_to_the_route(monkeypatch, path):
    composed = object()
    status, seen = _post_8765(monkeypatch, flag=True, authority=composed, path=path)
    assert status == 200 and seen == [("POST", path, "test-builder", b'{"raw": 1}', composed)]


# ── OP_G: scene-specific declarations and bound provider contributions ──

def test_no_declaration_for_the_active_scene_refuses(live_env):
    live_env.truth.unlink()
    status, body = live_env.build(_body())
    assert status == 409 and "no authority-owned target declarations" in body["errors"][0]
    assert live_env.side_effects() == []


def test_declaration_for_another_revision_refuses(live_env):
    live_env.declare(SCENE, scene_revision=scene_revision_of(dict(SCENE, segments=[{"text": "older"}])))
    status, body = live_env.build(_body())
    assert status == 409 and "another scene revision" in body["errors"][0]
    assert live_env.side_effects() == []


def test_proof_scene_truth_is_not_consulted(live_env):
    # The fixed proof artifact names scene-first-proof; activating that id finds no declaration here.
    live_env.scene = dict(SCENE, scene_id="scene-first-proof")
    live_env.load = ("runtime-instance-a", 2, "scene-first-proof")
    status, body = live_env.build(_body())
    assert status == 409 and "no authority-owned target declarations" in body["errors"][0]
    assert not hasattr(route, "SCENE_TRUTH_PATH")


@pytest.mark.parametrize("scene_id", ["../escape", "scene/../../x", ".hidden", "a" * 200])
def test_scene_ids_cannot_address_other_files(live_env, scene_id):
    live_env.scene = dict(SCENE, scene_id=scene_id)
    live_env.load = ("runtime-instance-a", 2, scene_id)
    assert live_env.build(_body())[0] == 409


def test_provenance_must_name_the_active_scene(live_env):
    other = contributions(basis=dict(TEST_BASIS, scene_id="scene-other-live"))
    body = _body(surface=dict(zip(("grid_facts", "metric_grant", "provenance", "construction_policy"), other)))
    status, resp = live_env.build(body)
    assert status == 409 and "does not name the active scene" in resp["errors"][0]
    assert live_env.side_effects() == []


def test_proof_metric_grant_is_refused_in_production(live_env):
    from tier1.engainos.tests.test_trixel32d_request_assembler import (
        CONSTRUCTION_POLICY, METRIC_GRANT, build_fixture_grid_facts)
    body = _body(surface={"grid_facts": build_fixture_grid_facts(), "metric_grant": METRIC_GRANT,
                          "provenance": {"source_scene_id": SCENE["scene_id"], "topology_artifact_id": "t",
                                         "metric_layout_artifact_id": "metric_layout.proof.001"},
                          "construction_policy": CONSTRUCTION_POLICY})
    status, resp = live_env.build(body)
    assert status == 400 and "request assembly rejected" in resp["errors"][0]
    assert live_env.side_effects() == []
