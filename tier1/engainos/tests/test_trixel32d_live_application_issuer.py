from __future__ import annotations

import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import tier1.engainos.authority.trixel32d_live_application_issuer as issuer_module
from tier1.engainos.authority.trixel32d_live_authority_state import (
    AuthorityStateError,
    LiveAuthorityState,
    SemanticActivationObservation,
    TargetDeclaration,
    UntrustedPrincipal,
)
from tier1.engainos.authority.trixel32d_live_application_issuer import (
    LiveApplicationIssuer,
    ProposedApplication,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    canonical_application_intent_digest,
)


def _fresh_contract_payloads() -> tuple[dict, bytes]:
    """Create current-contract test payloads without historical proof artifacts."""
    request_id = "t32dreq_0123456789abcdef"
    topology_policy = "HEIGHT_FIELD_CELL_EXTRUSION"
    request = {
        "packet_type": "trixel32d_surface_request",
        "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
        "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": request_id,
        },
        "orientation": {
            "basis_authority": "VECTORS",
            "field_axis_binding": {
                "field_x_increases_along": "RIGHT",
                "field_y_increases_along": "FORWARD",
            },
            "vectors": {
                "forward": [0.0, 0.0, -1.0],
                "right": [1.0, 0.0, 0.0],
                "up": [0.0, 1.0, 0.0],
            },
            "tolerance": 0.0001,
        },
        "planar_config": {
            "field_width_columns": 1,
            "field_height_rows": 1,
            "field_coverage": "DENSE",
            "cell_width": 1.0,
            "cell_depth": 1.0,
            "center_column": 0.0,
            "center_row": 0.0,
        },
        "construction": {"topology_policy": topology_policy},
        "gap_fill": {
            "enabled": True,
            "mode": "PER_CELL_EXTRUSION",
            "adjacency_policy": "ALL_FACES_INDEPENDENT",
            "resolved_color": [0.1, 0.1, 0.1, 1.0],
            "thickness_local_units": 0.1,
        },
        "pixel_field_data": [
            {
                "field_x": 0,
                "field_y": 0,
                "elevation": 1.0,
                "base_color": [0.2, 0.3, 0.4, 1.0],
            }
        ],
    }
    faces = ("top", "bottom", "-field_y", "+field_x", "+field_y", "-field_x")
    surfaces = [
        {
            "role": "PRIMARY_PIXEL_FACE" if index == 0 else "NEUTRAL_GAP_FILL",
            "face": face,
            "vertex_start": index * 4,
            "vertex_count": 4,
            "index_start": index * 6,
            "index_count": 6,
        }
        for index, face in enumerate(faces)
    ]
    surface_digest = hashlib.sha256(f"{request_id}:{topology_policy}".encode()).hexdigest()[:16]
    built = {
        "appearance": {},
        "cell_geometry_ranges": [
            {
                "cell_key": "0,0",
                "field_x": 0,
                "field_y": 0,
                "source_cell_ordinal": 0,
                "surfaces": surfaces,
            }
        ],
        "contract": "trixel32d_surface_built.v1",
        "errors": [],
        "geometry": {"vertices": [[0.0, 0.0, 0.0]], "indices": [0]},
        "local_spatial_metadata": {"coordinate_space": "TRIXEL_LOCAL_Y_UP"},
        "packet_type": "trixel32d_surface_built",
        "primitive_provenance": [],
        "rejected_cells": [],
        "request_id": request_id,
        "status": "BUILT",
        "surface_id": f"t32dsurface_{surface_digest}",
        "topology_policy": topology_policy,
    }
    return request, json.dumps(built, sort_keys=True, separators=(",", ":")).encode()


TRUSTED_REQUEST, BUILT_BYTES = _fresh_contract_payloads()
BUILT_SHA256 = hashlib.sha256(BUILT_BYTES).hexdigest()
SCENE = {"scene_id": "scene.live.001", "segments": [{"text": "live"}], "entities": []}
TARGET = TargetDeclaration("RUNTIME_CONTAINER", "semantic-terrain", "slot-live-terrain")
IDENTITY_BASIS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
_REGISTRATION_CAPABILITIES: dict[int, object] = {}
_STATE_MUTATION_CAPABILITIES: dict[int, object] = {}
_COMMIT_CAPABILITIES: dict[int, object] = {}
_CONSUMPTION_CAPABILITIES: dict[int, object] = {}


class HexFactory:
    def __init__(self, start: int = 1):
        self.value = start

    def __call__(self) -> str:
        value = f"{self.value:032x}"
        self.value += 1
        return value


def make_state(tmp_path: Path, *, state_cls=LiveAuthorityState) -> LiveAuthorityState:
    registration_capability = object()
    state_mutation_capability = object()
    commit_capability = object()
    consumption_capability = object()
    state = state_cls(
        ledger_path=tmp_path / "live_authority.jsonl",
        authority_revision="authority-live-test-1",
        principal_registration_capability=registration_capability,
        trusted_state_mutation_capability=state_mutation_capability,
        authorization_commit_capability=commit_capability,
        decision_consumption_capability=consumption_capability,
        id_factory=HexFactory(),
    )
    _REGISTRATION_CAPABILITIES[id(state)] = registration_capability
    _STATE_MUTATION_CAPABILITIES[id(state)] = state_mutation_capability
    _COMMIT_CAPABILITIES[id(state)] = commit_capability
    _CONSUMPTION_CAPABILITIES[id(state)] = consumption_capability
    return state


def activate_scene(state: LiveAuthorityState, scene):
    return state.activate_scene(
        scene,
        capability=_STATE_MUTATION_CAPABILITIES[id(state)],
    )


def declare_target(state: LiveAuthorityState, activation, target=TARGET):
    state.declare_target(
        activation.scene_id,
        activation.scene_revision,
        target,
        capability=_STATE_MUTATION_CAPABILITIES[id(state)],
    )


def observe_activation(state: LiveAuthorityState, observation):
    state.observe_semantic_activation(
        observation,
        capability=_STATE_MUTATION_CAPABILITIES[id(state)],
    )


def prepare_current_state(tmp_path: Path, *, state_cls=LiveAuthorityState):
    state = make_state(tmp_path, state_cls=state_cls)
    principal = state.register_trusted_principal(
        actor_id="human-root-live-test",
        actor_authority_tier=3,
        reality_mode="DRAFT",
        capability=_REGISTRATION_CAPABILITIES[id(state)],
    )
    activation = activate_scene(state, SCENE)
    declare_target(state, activation)
    observation = SemanticActivationObservation(
        runtime_session_id=state.runtime_session_id,
        activation_id=activation.activation_id,
        scene_id=activation.scene_id,
        scene_revision=activation.scene_revision,
        semantic_main_instance_id=9001,
        semantic_local_generation=4,
    )
    observe_activation(state, observation)
    return state, principal, activation, observation


def proposal(**overrides) -> ProposedApplication:
    values = {
        "request_id": TRUSTED_REQUEST["identity"]["request_id"],
        "surface_id": json.loads(BUILT_BYTES)["surface_id"],
        "built_response_sha256": BUILT_SHA256,
        "parent_kind": TARGET.parent_kind,
        "parent_id": TARGET.parent_id,
        "application_slot_id": TARGET.application_slot_id,
        "basis_columns": copy.deepcopy(IDENTITY_BASIS),
        "origin": [0.0, 0.0, 0.0],
        "visibility_intent": "VISIBLE",
        "replacement_mode": "CREATE_ONLY",
        "replaces_apply_id": None,
        "lifetime_mode": "SCENE_BOUND",
        "classification": "PRESENTATION_ONLY",
        "collision_decision": "DENIED",
        "observed_activation_id": None,
        "semantic_main_instance_id": None,
        "semantic_local_generation": None,
    }
    values.update(overrides)
    return ProposedApplication(**values)


def issue(state, principal, proposed=None):
    intended = proposed or proposal()
    observation = state.current_observation
    if observation is not None and intended.observed_activation_id is None:
        intended = replace(
            intended,
            observed_activation_id=observation.activation_id,
            semantic_main_instance_id=observation.semantic_main_instance_id,
            semantic_local_generation=observation.semantic_local_generation,
        )
    return LiveApplicationIssuer(
        state,
        commit_capability=_COMMIT_CAPABILITIES[id(state)],
    ).issue(
        intended,
        built_response_bytes=BUILT_BYTES,
        trusted_request=TRUSTED_REQUEST,
        principal=principal,
    )


def consume(state: LiveAuthorityState, result) -> None:
    assert result.artifact is not None
    assert result.artifact_sha256 is not None
    packet = result.artifact["apply_packet"]
    state.consume_authorization(
        packet["authorization"]["decision_id"],
        packet["apply_id"],
        applied_artifact_sha256=result.artifact_sha256,
        capability=_CONSUMPTION_CAPABILITIES[id(state)],
    )


def assert_rejected_without_commit(state: LiveAuthorityState, result, expected: str):
    assert not result.authorized
    assert result.artifact is None
    assert any(expected in error for error in result.errors), result.errors
    assert state.decision_count == 0
    assert state.slot_occupancy == {}


def test_state_generates_new_runtime_session_each_restart_and_keeps_durable_ledger(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized, result.errors
    first_session = state.runtime_session_id
    ledger_bytes = state.ledger_path.read_bytes()
    assert ledger_bytes.endswith(b"\n")
    assert b'"event":"authorization_issued"' in ledger_bytes

    state.close()
    restarted = make_state(tmp_path)
    assert restarted.runtime_session_id != first_session
    assert restarted.decision_count == 1
    assert restarted.slot_occupancy == {}


def test_active_application_gate_rejection_blocks_commit(tmp_path: Path, monkeypatch):
    state, principal, _, _ = prepare_current_state(tmp_path)
    calls = []

    def reject_gate(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(accepted=False, errors=("toxic active-gate rejection",))

    monkeypatch.setattr(issuer_module, "validate_trixel32d_surface_apply", reject_gate)
    result = issue(state, principal)
    assert len(calls) == 1
    assert_rejected_without_commit(state, result, "toxic active-gate rejection")


def test_commit_boundary_reinvokes_active_gate_instead_of_trusting_passed_marker(
    tmp_path: Path, monkeypatch
):
    state, principal, _, _ = prepare_current_state(tmp_path)

    monkeypatch.setattr(LiveApplicationIssuer, "_evaluate_policy", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        issuer_module,
        "validate_trixel32d_surface_apply",
        lambda *args, **kwargs: SimpleNamespace(accepted=True, errors=()),
    )
    result = issue(state, principal, proposal(collision_decision="GRANTED"))

    assert_rejected_without_commit(state, result, "fails active application gate")


def test_scene_revision_is_deterministic_and_activation_identity_is_fresh(tmp_path: Path):
    state = make_state(tmp_path)
    first = activate_scene(state, SCENE)
    second = activate_scene(state, copy.deepcopy(SCENE))
    assert first.scene_revision == second.scene_revision
    assert first.activation_id != second.activation_id


def test_identity_factory_requires_128_bits_of_lowercase_hex(tmp_path: Path):
    state_capability = object()
    state = LiveAuthorityState(
        tmp_path / "short-id-ledger.jsonl",
        "authority-live-test-1",
        principal_registration_capability=object(),
        trusted_state_mutation_capability=state_capability,
        authorization_commit_capability=object(),
        decision_consumption_capability=object(),
        id_factory=lambda: "abcd",
    )
    with pytest.raises(AuthorityStateError, match="32 lowercase hexadecimal"):
        state.activate_scene(SCENE, capability=state_capability)


def test_server_owned_state_mutations_require_trusted_capability(tmp_path: Path):
    state = make_state(tmp_path)
    with pytest.raises(AuthorityStateError, match="state mutation capability"):
        state.activate_scene(SCENE, capability=object())
    assert state.decision_count == 0


def test_direct_commit_without_issuer_capability_rejects(tmp_path: Path):
    state = make_state(tmp_path)
    with pytest.raises(AuthorityStateError, match="commit capability"):
        state.commit_authorization(
            expected_generation=0,
            decision_id="fabricated-decision",
            apply_id="t32dapply_0000000000000001",
            target=TARGET,
            replacement_mode="CREATE_ONLY",
            replaces_apply_id=None,
            artifact={},
            built_response_bytes=BUILT_BYTES,
            trusted_request=TRUSTED_REQUEST,
            capability=object(),
        )
    assert state.decision_count == 0


def test_direct_commit_with_capability_still_requires_valid_gate_artifact(tmp_path: Path):
    state, _, _, _ = prepare_current_state(tmp_path)
    snapshot = state.snapshot_for_issuance()
    with pytest.raises(AuthorityStateError, match="authorization artifact"):
        state.commit_authorization(
            expected_generation=snapshot.generation,
            decision_id="fabricated-decision",
            apply_id="t32dapply_0000000000000001",
            target=TARGET,
            replacement_mode="CREATE_ONLY",
            replaces_apply_id=None,
            artifact={"gate_result": {"gate_name": "fabricated", "passed": "TRUE"}},
            built_response_bytes=BUILT_BYTES,
            trusted_request=TRUSTED_REQUEST,
            capability=_COMMIT_CAPABILITIES[id(state)],
        )
    assert state.decision_count == 0
    assert state.slot_occupancy == {}


def test_missing_semantic_observation_rejects(tmp_path: Path):
    state = make_state(tmp_path)
    principal = state.register_trusted_principal(
        "human",
        3,
        "DRAFT",
        capability=_REGISTRATION_CAPABILITIES[id(state)],
    )
    activation = activate_scene(state, SCENE)
    declare_target(state, activation)
    assert_rejected_without_commit(state, issue(state, principal), "Semantic activation observation is missing")


@pytest.mark.parametrize(
    ("field", "bad_value", "expected"),
    [
        ("runtime_session_id", "session-from-yesterday", "runtime session"),
        ("activation_id", "activation-fabricated", "activation identity"),
        ("scene_revision", "scene-sha256:stale", "scene revision"),
    ],
)
def test_stale_or_mismatched_semantic_observation_rejects(
    tmp_path: Path, field: str, bad_value, expected: str
):
    state = make_state(tmp_path)
    principal = state.register_trusted_principal(
        "human",
        3,
        "DRAFT",
        capability=_REGISTRATION_CAPABILITIES[id(state)],
    )
    activation = activate_scene(state, SCENE)
    declare_target(state, activation)
    values = {
        "runtime_session_id": state.runtime_session_id,
        "activation_id": activation.activation_id,
        "scene_id": activation.scene_id,
        "scene_revision": activation.scene_revision,
        "semantic_main_instance_id": 42,
        "semantic_local_generation": 4,
    }
    values[field] = bad_value
    with pytest.raises(AuthorityStateError, match=expected):
        state.observe_semantic_activation(
            SemanticActivationObservation(**values),
            capability=_STATE_MUTATION_CAPABILITIES[id(state)],
        )
    assert_rejected_without_commit(state, issue(state, principal), "Semantic activation observation is missing")


def test_application_request_with_stale_semantic_generation_rejects(tmp_path: Path):
    state, principal, _, observation = prepare_current_state(tmp_path)
    stale = proposal(
        observed_activation_id=observation.activation_id,
        semantic_main_instance_id=observation.semantic_main_instance_id,
        semantic_local_generation=observation.semantic_local_generation - 1,
    )
    assert_rejected_without_commit(state, issue(state, principal, stale), "local generation")


def test_fabricated_principal_rejects(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    fabricated = UntrustedPrincipal(
        actor_id=principal.actor_id,
        actor_authority_tier=principal.actor_authority_tier,
        reality_mode=principal.reality_mode,
        authority_revision=principal.authority_revision,
        trust_token="fabricated",
    )
    assert_rejected_without_commit(state, issue(state, fabricated), "trusted principal")


def test_principal_token_is_not_exposed_by_repr(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    assert principal.trust_token not in repr(principal)
    state.close()


def test_principal_registration_requires_server_capability(tmp_path: Path):
    state = make_state(tmp_path)
    with pytest.raises(AuthorityStateError, match="registration capability"):
        state.register_trusted_principal(
            "fabricated-root",
            3,
            "FINALIZED",
            capability=object(),
        )


def test_replay_principal_rejects(tmp_path: Path):
    state, _, _, _ = prepare_current_state(tmp_path)
    replay = state.register_trusted_principal(
        "replay-validator",
        0,
        "REPLAY",
        capability=_REGISTRATION_CAPABILITIES[id(state)],
    )
    assert_rejected_without_commit(state, issue(state, replay), "REPLAY")


def test_undeclared_target_rejects(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal, proposal(application_slot_id="slot-invented-by-client"))
    assert_rejected_without_commit(state, result, "undeclared target")


def test_mismatched_payload_hash_rejects(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal, proposal(built_response_sha256="0" * 64))
    assert_rejected_without_commit(state, result, "built response")


def test_presentation_issuance_is_collision_denied_and_creates_no_geometry(tmp_path: Path):
    state, principal, activation, observation = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized, result.errors
    artifact = result.artifact
    packet = artifact["apply_packet"]
    assert packet["target"]["scene_id"] == activation.scene_id
    assert packet["target"]["scene_revision"] == activation.scene_revision
    assert packet["authorization"]["runtime_session_id"] == state.runtime_session_id
    assert artifact["semantic_activation"] == {
        "activation_id": observation.activation_id,
        "semantic_main_instance_id": 9001,
        "semantic_local_generation": 4,
    }
    assert packet["classification"] == "PRESENTATION_ONLY"
    assert packet["collision"] == {
        "decision": "DENIED",
        "authorized_by_decision_id": packet["authorization"]["decision_id"],
        "shape_policy": "NONE",
        "layer": 0,
        "mask": 0,
    }
    serialized = json.dumps(artifact, default=dict)
    for forbidden in ("vertices", "indices", "ArrayMesh", "MeshInstance3D", "geometry"):
        assert forbidden not in serialized


def test_competing_create_only_requests_yield_exactly_one_authorization(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _index: issue(state, principal), range(16)))
    accepted = [result for result in results if result.authorized]
    rejected = [result for result in results if not result.authorized]
    assert len(accepted) == 1
    assert len(rejected) == 15
    assert all(
        any("occupied" in error or "changed before authorization commitment" in error for error in result.errors)
        for result in rejected
    )
    assert state.decision_count == 1
    assert len(state.slot_occupancy) == 1


class ActivateDuringCommitState(LiveAuthorityState):
    def commit_authorization(self, *args, **kwargs):
        self.activate_scene(
            {"scene_id": "scene.changed", "segments": [], "entities": []},
            capability=_STATE_MUTATION_CAPABILITIES[id(self)],
        )
        return super().commit_authorization(*args, **kwargs)


def test_activation_change_between_validation_and_commit_rejects(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path, state_cls=ActivateDuringCommitState)
    result = issue(state, principal)
    assert_rejected_without_commit(state, result, "changed before authorization commitment")


def test_consumption_requires_trusted_capability_and_exact_artifact_hash(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized and result.artifact is not None
    assert result.artifact_sha256 is not None
    packet = result.artifact["apply_packet"]
    decision_id = packet["authorization"]["decision_id"]
    apply_id = packet["apply_id"]

    with pytest.raises(AuthorityStateError, match="consumption capability"):
        state.consume_authorization(
            decision_id,
            apply_id,
            applied_artifact_sha256=result.artifact_sha256,
            capability=object(),
        )
    with pytest.raises(AuthorityStateError, match="artifact hash"):
        state.consume_authorization(
            decision_id,
            apply_id,
            applied_artifact_sha256="0" * 64,
            capability=_CONSUMPTION_CAPABILITIES[id(state)],
        )
    consume(state, result)


def test_authorization_consumption_is_durable_and_single_use(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    packet = result.artifact["apply_packet"]
    decision_id = packet["authorization"]["decision_id"]
    apply_id = packet["apply_id"]

    consume(state, result)
    with pytest.raises(AuthorityStateError, match="already consumed"):
        consume(state, result)

    state.close()
    restarted = make_state(tmp_path)
    with pytest.raises(AuthorityStateError, match="already consumed"):
        consume(restarted, result)


def test_newer_semantic_generation_invalidates_unconsumed_authorization(tmp_path: Path):
    state, principal, activation, observation = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    assert result.artifact is not None
    packet = result.artifact["apply_packet"]

    observe_activation(
        state,
        replace(observation, semantic_local_generation=observation.semantic_local_generation + 1),
    )
    with pytest.raises(AuthorityStateError, match="different Semantic observation"):
        consume(state, result)


def test_scene_replacement_invalidates_unconsumed_authorization(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    assert result.artifact is not None
    packet = result.artifact["apply_packet"]

    activate_scene(state, {"scene_id": "scene.changed", "segments": [], "entities": []})
    with pytest.raises(AuthorityStateError, match="different scene activation"):
        consume(state, result)


def test_same_scene_reactivation_does_not_reuse_target_declaration(tmp_path: Path):
    state, principal, _, observation = prepare_current_state(tmp_path)
    activation = activate_scene(state, copy.deepcopy(SCENE))
    current_observation = replace(
        observation,
        activation_id=activation.activation_id,
        semantic_local_generation=observation.semantic_local_generation + 1,
    )
    observe_activation(state, current_observation)
    result = issue(state, principal)
    assert_rejected_without_commit(state, result, "undeclared target")

    declare_target(state, activation)
    assert issue(state, principal).authorized


def test_same_scene_reactivation_invalidates_old_authorization(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    assert result.artifact is not None
    packet = result.artifact["apply_packet"]

    activate_scene(state, copy.deepcopy(SCENE))
    with pytest.raises(AuthorityStateError, match="different scene activation"):
        consume(state, result)


def test_runtime_restart_invalidates_unconsumed_authorization(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    packet = result.artifact["apply_packet"]

    state.close()
    restarted = make_state(tmp_path)
    with pytest.raises(AuthorityStateError, match="different runtime session"):
        consume(restarted, result)


def test_replacement_invalidates_earlier_unconsumed_authorization(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    first = issue(state, principal)
    assert first.authorized
    assert first.artifact is not None
    first_packet = first.artifact["apply_packet"]

    replacement = issue(
        state,
        principal,
        proposal(
            replacement_mode="REPLACE_EXACT",
            replaces_apply_id=first_packet["apply_id"],
        ),
    )
    assert replacement.authorized, replacement.errors
    with pytest.raises(AuthorityStateError, match="no longer occupies"):
        consume(state, first)


@pytest.mark.parametrize(
    ("artifact_path", "replacement"),
    [
        (("apply_packet", "authorization", "decision_id"), "tampered-decision"),
        (("authority_evidence", "actor_id"), "tampered-actor"),
        (("authority_evidence", "actor_authority_tier"), 0),
        (("authority_evidence", "authority_revision"), "tampered-authority"),
        (("authority_evidence", "ap_rule_ids"), ["tampered-rule"]),
        (("authorized_intent_sha256",), "0" * 64),
        (("gate_result", "gate_name"), "fabricated-gate"),
    ],
)
def test_durable_artifact_cross_binding_tamper_fails_closed(
    tmp_path: Path, artifact_path: tuple[str, ...], replacement
):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    ledger = state.ledger_path
    state.close()

    event = json.loads(ledger.read_text(encoding="utf-8"))
    node = event["artifact"]
    for key in artifact_path[:-1]:
        node = node[key]
    node[artifact_path[-1]] = replacement
    artifact_bytes = json.dumps(
        event["artifact"], sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    event["artifact_sha256"] = hashlib.sha256(artifact_bytes).hexdigest()
    ledger.write_text(
        json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AuthorityStateError, match="artifact bindings"):
        make_state(tmp_path)


@pytest.mark.parametrize(
    "semantic_case",
    [
        "authority_tier",
        "reality_mode",
        "transform",
        "visibility",
        "replacement",
        "lifetime",
        "classification",
        "collision",
        "surface_binding",
    ],
)
def test_durable_reload_reinvokes_gate_for_all_gate_semantics(
    tmp_path: Path, semantic_case: str
):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    ledger = state.ledger_path
    state.close()

    event = json.loads(ledger.read_text(encoding="utf-8"))
    artifact = event["artifact"]
    packet = artifact["apply_packet"]
    if semantic_case == "authority_tier":
        event["actor_authority_tier"] = 99
        artifact["authority_evidence"]["actor_authority_tier"] = 99
        packet["authorization"]["actor_authority_tier"] = 99
    elif semantic_case == "reality_mode":
        event["reality_mode"] = "UNDECLARED"
        artifact["authority_evidence"]["reality_mode"] = "UNDECLARED"
        packet["authorization"]["reality_mode"] = "UNDECLARED"
    elif semantic_case == "transform":
        packet["local_to_scene"]["basis_columns"] = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    elif semantic_case == "visibility":
        packet["visibility"]["intent"] = "UNDECLARED"
    elif semantic_case == "replacement":
        event["replacement_mode"] = "UNDECLARED"
        packet["replacement"]["mode"] = "UNDECLARED"
    elif semantic_case == "lifetime":
        packet["lifetime"]["mode"] = "UNDECLARED"
    elif semantic_case == "classification":
        packet["classification"] = "UNDECLARED"
    elif semantic_case == "collision":
        packet["collision"]["decision"] = "UNDECLARED"
    elif semantic_case == "surface_binding":
        packet["surface_binding"]["request_id"] = "not-canonical"

    artifact["authorized_intent_sha256"] = canonical_application_intent_digest(packet)
    artifact_bytes = json.dumps(
        artifact, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    event["artifact_sha256"] = hashlib.sha256(artifact_bytes).hexdigest()
    ledger.write_text(
        json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AuthorityStateError, match="active application gate"):
        make_state(tmp_path)


def test_durable_reload_rejects_canonical_surface_binding_substitution(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    ledger = state.ledger_path
    state.close()

    event = json.loads(ledger.read_text(encoding="utf-8"))
    artifact = event["artifact"]
    binding = artifact["apply_packet"]["surface_binding"]
    binding["request_id"] = "t32dreq_ffffffffffffffff"
    binding["surface_id"] = "t32dsurface_ffffffffffffffff"
    binding["built_response_sha256"] = "f" * 64
    artifact["authorized_intent_sha256"] = canonical_application_intent_digest(
        artifact["apply_packet"]
    )
    artifact_bytes = json.dumps(
        artifact, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    event["artifact_sha256"] = hashlib.sha256(artifact_bytes).hexdigest()
    ledger.write_text(
        json.dumps(event, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AuthorityStateError, match="durable built response"):
        make_state(tmp_path)


def test_durable_reload_rejects_nonexistent_replace_exact_occupant(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    first = issue(state, principal)
    assert first.authorized
    assert first.artifact is not None
    replacement = issue(
        state,
        principal,
        proposal(
            replacement_mode="REPLACE_EXACT",
            replaces_apply_id=first.artifact["apply_packet"]["apply_id"],
        ),
    )
    assert replacement.authorized
    ledger = state.ledger_path
    state.close()

    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    replacement_event = events[1]
    nonexistent = "t32dapply_ffffffffffffffff"
    replacement_event["replaces_apply_id"] = nonexistent
    artifact = replacement_event["artifact"]
    artifact["apply_packet"]["replacement"]["replaces_apply_id"] = nonexistent
    artifact["authorized_intent_sha256"] = canonical_application_intent_digest(
        artifact["apply_packet"]
    )
    artifact_bytes = json.dumps(
        artifact, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    replacement_event["artifact_sha256"] = hashlib.sha256(artifact_bytes).hexdigest()
    ledger.write_text(
        "".join(
            json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
            for item in events
        ),
        encoding="utf-8",
    )

    with pytest.raises(AuthorityStateError, match="active application gate"):
        make_state(tmp_path)


def test_durable_reload_accepts_valid_replace_exact_history(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    first = issue(state, principal)
    assert first.authorized
    assert first.artifact is not None
    first_apply_id = first.artifact["apply_packet"]["apply_id"]
    replacement = issue(
        state,
        principal,
        proposal(replacement_mode="REPLACE_EXACT", replaces_apply_id=first_apply_id),
    )
    assert replacement.authorized, replacement.errors
    state.close()

    restarted = make_state(tmp_path)
    assert restarted.decision_count == 2


def test_durable_consumption_session_mismatch_fails_closed(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    consume(state, result)
    ledger = state.ledger_path
    state.close()

    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
    events[1]["runtime_session_id"] = "engain-session-tampered"
    ledger.write_text(
        "".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
    )
    with pytest.raises(AuthorityStateError, match="session binding"):
        make_state(tmp_path)


def test_constructor_rejects_aliased_privileged_capabilities(tmp_path: Path):
    shared = object()
    with pytest.raises(AuthorityStateError, match="separate objects"):
        LiveAuthorityState(
            tmp_path / "aliased-capabilities.jsonl",
            "authority-live-test-1",
            principal_registration_capability=shared,
            trusted_state_mutation_capability=object(),
            authorization_commit_capability=object(),
            decision_consumption_capability=shared,
            id_factory=HexFactory(),
        )


@pytest.mark.parametrize(
    "nested_path",
    [
        ("apply_packet",),
        ("apply_packet", "surface_binding"),
        ("apply_packet", "authorization"),
        ("apply_packet", "target"),
        ("apply_packet", "local_to_scene"),
        ("apply_packet", "visibility"),
        ("apply_packet", "replacement"),
        ("apply_packet", "lifetime"),
        ("apply_packet", "collision"),
        ("scene_activation",),
        ("semantic_activation",),
        ("gate_result",),
    ],
)
def test_unknown_nested_durable_field_fails_closed(tmp_path: Path, nested_path: tuple[str, ...]):
    state, principal, _, _ = prepare_current_state(tmp_path)
    result = issue(state, principal)
    assert result.authorized
    ledger = state.ledger_path
    state.close()

    event = json.loads(ledger.read_text(encoding="utf-8"))
    node = event["artifact"]
    for key in nested_path:
        node = node[key]
    node["unexpected_field"] = "forbidden"
    event["artifact_sha256"] = hashlib.sha256(
        json.dumps(event["artifact"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    ledger.write_text(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
    with pytest.raises(AuthorityStateError, match="noncanonical"):
        make_state(tmp_path)


def test_durable_authority_revision_drift_fails_closed(tmp_path: Path):
    state, principal, _, _ = prepare_current_state(tmp_path)
    assert issue(state, principal).authorized
    ledger = state.ledger_path
    state.close()

    with pytest.raises(AuthorityStateError, match="different authority revision"):
        LiveAuthorityState(
            ledger,
            "authority-live-test-2",
            principal_registration_capability=object(),
            trusted_state_mutation_capability=object(),
            authorization_commit_capability=object(),
            decision_consumption_capability=object(),
            id_factory=HexFactory(),
        )


def test_hard_link_ledger_alias_cannot_acquire_second_owner(tmp_path: Path):
    state = make_state(tmp_path)
    alias = tmp_path / "hard-link-ledger-alias.jsonl"
    alias.hardlink_to(state.ledger_path)
    with pytest.raises(AuthorityStateError, match="already owned"):
        LiveAuthorityState(
            alias,
            "authority-live-test-1",
            principal_registration_capability=object(),
            trusted_state_mutation_capability=object(),
            authorization_commit_capability=object(),
            decision_consumption_capability=object(),
            id_factory=HexFactory(),
        )
    state.close()


def test_durable_ledger_has_exactly_one_live_owner(tmp_path: Path):
    state = make_state(tmp_path)
    with pytest.raises(AuthorityStateError, match="already owned"):
        make_state(tmp_path)
    state.close()
    restarted = make_state(tmp_path)
    restarted.close()


@pytest.mark.parametrize(
    "ledger_text",
    [
        '{"event":"authorization_issued","runtime_session_id":"s","decision_id":"d1","decision_id":"d2","apply_id":"a","artifact":{}}\n',
        '{"event":"authorization_issued","runtime_session_id":"s","decision_id":"d","apply_id":"a","artifact":{},"value":NaN}\n',
    ],
)
def test_noncanonical_durable_ledger_fails_closed(tmp_path: Path, ledger_text: str):
    ledger = tmp_path / "live_authority.jsonl"
    ledger.write_text(ledger_text, encoding="utf-8")
    with pytest.raises(AuthorityStateError, match="durable authority ledger"):
        LiveAuthorityState(
            ledger,
            "authority-live-test-1",
            principal_registration_capability=object(),
            trusted_state_mutation_capability=object(),
            authorization_commit_capability=object(),
            decision_consumption_capability=object(),
            id_factory=HexFactory(),
        )


def test_malformed_durable_ledger_fails_closed(tmp_path: Path):
    ledger = tmp_path / "live_authority.jsonl"
    ledger.write_text('{"event":"authorization_issued"}\nnot-json\n', encoding="utf-8")
    with pytest.raises(AuthorityStateError, match="durable authority ledger"):
        LiveAuthorityState(
            ledger,
            "authority-live-test-1",
            principal_registration_capability=object(),
            trusted_state_mutation_capability=object(),
            authorization_commit_capability=object(),
            decision_consumption_capability=object(),
            id_factory=HexFactory(),
        )


def test_existing_application_gate_file_is_not_modified_by_issuer(tmp_path: Path):
    gate_path = Path(__file__).resolve().parents[1] / "gates" / "gate_trixel32d_surface_apply.py"
    before = hashlib.sha256(gate_path.read_bytes()).hexdigest()
    state, principal, _, _ = prepare_current_state(tmp_path)
    assert issue(state, principal).authorized
    assert hashlib.sha256(gate_path.read_bytes()).hexdigest() == before
