from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tier1.engainos.gates.gate_trixel32d_handshake import (
    BuiltSurfaceValidation,
    validate_trixel32d_surface_built_bytes,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    CollisionGrantEvidence,
    TrustedApplicationAuthority,
    TrustedSceneTruth,
    canonical_application_intent_digest,
    gate_trixel32d_surface_apply,
    validate_trixel32d_surface_apply,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
CANONICAL_REQUEST_FIXTURE = FIXTURE_DIR / "trixel32d_request_3x2_first_proof.json"
CANONICAL_BUILT_FIXTURE = FIXTURE_DIR / "trixel32d_surface_built_3x2_first_proof.json"
CANONICAL_BUILT_SHA256 = "bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929"
REQUEST_ID = "t32dreq_8b14a3bac98d1025"
SURFACE_ID = "t32dsurface_0f5d9d7e96ed734a"

APPLY_ID = "t32dapply_00c0ffee00c0ffee"
PRIOR_APPLY_ID = "t32dapply_feedfacefeedface"
DECISION_ID = "engainos-decision-3x2-first-proof"
ACTOR_ID = "actor-human-root-001"
AUTHORITY_REVISION = "authority-rev-7"
SESSION_ID = "session-2026-07-18-proof"
SCENE_ID = "scene-first-proof"
SCENE_REVISION = "scene-rev-12"
PARENT_KIND = "RUNTIME_CONTAINER"
PARENT_ID = "container-terrain-proof"
SLOT_ID = "slot-surface-3x2"
OCCUPIED_SLOT_ID = "slot-occupied"
ROOT_PARENT_KIND = "SCENE_ROOT"
ROOT_PARENT_ID = "scene-first-proof-root"
ROOT_SLOT_ID = "slot-root-decor"
OTHER_APPLY_ID = "t32dapply_1111111111111111"
AP_RULE_IDS = ("ap-rule-apply-001",)

_TRUSTED_REQUEST = json.loads(CANONICAL_REQUEST_FIXTURE.read_text(encoding="utf-8"))
ACCEPTED_BUILT = validate_trixel32d_surface_built_bytes(
    CANONICAL_BUILT_FIXTURE.read_bytes(),
    _TRUSTED_REQUEST,
    expected_response_sha256=CANONICAL_BUILT_SHA256,
)
assert ACCEPTED_BUILT.accepted, ACCEPTED_BUILT.errors

IDENTITY_BASIS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
IDENTITY_BASIS_TUPLES = tuple(tuple(column) for column in IDENTITY_BASIS)


def canonical_apply_packet() -> dict[str, Any]:
    return {
        "contract": "trixel32d_surface_apply.v1",
        "packet_type": "trixel32d_surface_apply",
        "apply_id": APPLY_ID,
        "surface_binding": {
            "built_contract": "trixel32d_surface_built.v1",
            "request_id": REQUEST_ID,
            "surface_id": SURFACE_ID,
            "built_response_sha256": CANONICAL_BUILT_SHA256,
        },
        "authorization": {
            "decision": "AUTHORIZED",
            "decision_id": DECISION_ID,
            "issued_by": "engainos",
            "actor_id": ACTOR_ID,
            "actor_authority_tier": 3,
            "reality_mode": "DRAFT",
            "authority_revision": AUTHORITY_REVISION,
            "runtime_session_id": SESSION_ID,
            "ap_rule_ids": list(AP_RULE_IDS),
        },
        "target": {
            "scene_id": SCENE_ID,
            "scene_revision": SCENE_REVISION,
            "parent_kind": PARENT_KIND,
            "parent_id": PARENT_ID,
            "application_slot_id": SLOT_ID,
        },
        "local_to_scene": {
            "space": "SCENE_LOCAL_Y_UP",
            "basis_columns": copy.deepcopy(IDENTITY_BASIS),
            "origin": [0.0, 0.0, 0.0],
        },
        "visibility": {"intent": "VISIBLE"},
        "replacement": {"mode": "CREATE_ONLY", "replaces_apply_id": None},
        "lifetime": {"mode": "SCENE_BOUND"},
        "classification": "PRESENTATION_ONLY",
        "collision": {
            "decision": "DENIED",
            "authorized_by_decision_id": DECISION_ID,
            "shape_policy": "NONE",
            "layer": 0,
            "mask": 0,
        },
    }


CANONICAL_INTENT_SHA256 = canonical_application_intent_digest(canonical_apply_packet())


def canonical_authority(**overrides: Any) -> TrustedApplicationAuthority:
    values: dict[str, Any] = {
        "decision_id": DECISION_ID,
        "actor_id": ACTOR_ID,
        "actor_authority_tier": 3,
        "reality_mode": "DRAFT",
        "authority_revision": AUTHORITY_REVISION,
        "runtime_session_id": SESSION_ID,
        "authorized_intent_sha256": CANONICAL_INTENT_SHA256,
        "ap_rule_ids": AP_RULE_IDS,
        "ap_rule_required": True,
        "canonical_persistence_authorized": False,
        "collision_grant": None,
    }
    values.update(overrides)
    return TrustedApplicationAuthority(**values)


def canonical_collision_grant(**overrides: Any) -> CollisionGrantEvidence:
    values: dict[str, Any] = {
        "scene_revision": SCENE_REVISION,
        "request_id": REQUEST_ID,
        "surface_id": SURFACE_ID,
        "built_response_sha256": CANONICAL_BUILT_SHA256,
        "basis_columns": IDENTITY_BASIS_TUPLES,
        "origin": (0.0, 0.0, 0.0),
        "classification": "STATIC_SPATIAL",
        "shape_policy": "CANONICAL_MESH_EXACT",
        "layer": 1,
        "mask": 0,
    }
    values.update(overrides)
    return CollisionGrantEvidence(**values)


def canonical_scene_truth(**overrides: Any) -> TrustedSceneTruth:
    values: dict[str, Any] = {
        "scene_id": SCENE_ID,
        "active_scene_revision": SCENE_REVISION,
        "declared_targets": frozenset({
            (PARENT_KIND, PARENT_ID, SLOT_ID),
            (PARENT_KIND, PARENT_ID, OCCUPIED_SLOT_ID),
            (ROOT_PARENT_KIND, ROOT_PARENT_ID, ROOT_SLOT_ID),
        }),
        "slot_occupancy": {OCCUPIED_SLOT_ID: PRIOR_APPLY_ID},
    }
    values.update(overrides)
    return TrustedSceneTruth(**values)


def authority_for(packet: dict[str, Any], **overrides: Any) -> TrustedApplicationAuthority:
    """Trusted authority issued for exactly this packet's application intent."""
    overrides.setdefault(
        "authorized_intent_sha256", canonical_application_intent_digest(packet)
    )
    return canonical_authority(**overrides)


_DEFAULT = object()


def run(
    packet: Any,
    *,
    built: Any = _DEFAULT,
    authority: Any = _DEFAULT,
    scene: Any = _DEFAULT,
):
    return validate_trixel32d_surface_apply(
        packet,
        built_validation=ACCEPTED_BUILT if built is _DEFAULT else built,
        authority=canonical_authority() if authority is _DEFAULT else authority,
        scene_truth=canonical_scene_truth() if scene is _DEFAULT else scene,
    )


def assert_toxic(packet: Any, needle: str, **kwargs: Any) -> None:
    """One toxic proof: rejection, no accepted packet, and no input mutation."""
    before = copy.deepcopy(packet)
    result = run(packet, **kwargs)
    assert not result.accepted
    assert result.packet is None
    assert any(needle in error for error in result.errors), (needle, result.errors)
    assert packet == before, "rejection must not mutate the submitted packet"


def test_canonical_application_accepted():
    packet = canonical_apply_packet()
    result = run(packet)
    assert result.accepted, result.errors
    assert result.errors == ()
    assert isinstance(result.packet, MappingProxyType)


def test_acceptance_is_deterministic_and_immutable():
    first = run(canonical_apply_packet())
    second = run(canonical_apply_packet())
    assert first.accepted and second.accepted
    assert first.errors == second.errors == ()
    assert json.dumps(first.packet, default=dict, sort_keys=True) == json.dumps(
        second.packet, default=dict, sort_keys=True
    )
    with pytest.raises(TypeError):
        first.packet["classification"] = "DYNAMIC_SPATIAL"  # type: ignore[index]
    with pytest.raises(TypeError):
        first.packet["collision"]["decision"] = "GRANTED"  # type: ignore[index]


def test_acceptance_does_not_mutate_inputs():
    packet = canonical_apply_packet()
    before = copy.deepcopy(packet)
    result = run(packet)
    assert result.accepted
    assert packet == before


def test_wrong_contract_or_packet_type_rejects():
    packet = canonical_apply_packet()
    packet["contract"] = "trixel32d_surface_apply.v2"
    assert_toxic(packet, "contract must be 'trixel32d_surface_apply.v1'")
    packet = canonical_apply_packet()
    packet["packet_type"] = "trixel32d_surface_built"
    assert_toxic(packet, "packet_type must be 'trixel32d_surface_apply'")


@pytest.mark.parametrize(
    "bad_apply_id",
    ["t32dapply_00C0FFEE00C0FFEE", "t32dapply_00c0ffee", "t32dsurface_00c0ffee00c0ffee", 7, None],
)
def test_malformed_apply_id_rejects(bad_apply_id):
    packet = canonical_apply_packet()
    packet["apply_id"] = bad_apply_id
    assert_toxic(packet, "apply_id must be a canonical t32dapply identity")


@pytest.mark.parametrize("missing_key", sorted([
    "contract", "packet_type", "apply_id", "surface_binding", "authorization",
    "target", "local_to_scene", "visibility", "replacement", "lifetime",
    "classification", "collision",
]))
def test_missing_each_root_key_rejects(missing_key):
    packet = canonical_apply_packet()
    del packet[missing_key]
    assert_toxic(packet, "missing required keys")


def test_undeclared_keys_reject_closed_world():
    packet = canonical_apply_packet()
    packet["renderer_path"] = "/root/Terrain"
    assert_toxic(packet, "undeclared keys")

    packet = canonical_apply_packet()
    packet["target"]["node_path"] = "/root/Terrain"
    assert_toxic(packet, "target contains undeclared keys")

    packet = canonical_apply_packet()
    packet["local_to_scene"]["scale"] = 2.0
    assert_toxic(packet, "local_to_scene contains undeclared keys")

    packet = canonical_apply_packet()
    packet["lifetime"]["persistence_hint"] = "KEEP"
    assert_toxic(packet, "lifetime contains undeclared keys")

    packet = canonical_apply_packet()
    packet["collision"]["one_way"] = True
    assert_toxic(packet, "collision contains undeclared keys")

    packet = canonical_apply_packet()
    packet["visibility"]["fallback"] = "AUTO"
    assert_toxic(packet, "visibility contains undeclared keys")


def test_surface_binding_mismatches_reject():
    packet = canonical_apply_packet()
    packet["surface_binding"]["built_contract"] = "trixel32d_surface_built.v2"
    assert_toxic(packet, "surface_binding.built_contract")

    packet = canonical_apply_packet()
    packet["surface_binding"]["request_id"] = "t32dreq_0000000000000000"
    assert_toxic(packet, "surface_binding.request_id does not match")

    packet = canonical_apply_packet()
    packet["surface_binding"]["surface_id"] = "t32dsurface_0000000000000000"
    assert_toxic(packet, "surface_binding.surface_id does not match")

    packet = canonical_apply_packet()
    packet["surface_binding"]["built_response_sha256"] = "0" * 64
    assert_toxic(packet, "does not match the exact validated bytes")

    packet = canonical_apply_packet()
    packet["surface_binding"]["built_response_sha256"] = CANONICAL_BUILT_SHA256.upper()
    assert_toxic(packet, "64 lowercase hexadecimal")


def test_unaccepted_or_dict_only_built_evidence_rejects():
    rejected = BuiltSurfaceValidation(
        response_sha256=CANONICAL_BUILT_SHA256,
        packet=None,
        errors=("upstream rejection",),
    )
    assert_toxic(canonical_apply_packet(), "was not accepted", built=rejected)

    raw_dict = json.loads(CANONICAL_BUILT_FIXTURE.read_text(encoding="utf-8"))
    assert_toxic(
        canonical_apply_packet(),
        "dict-only semantic validation is insufficient",
        built=raw_dict,
    )
    assert_toxic(
        canonical_apply_packet(),
        "dict-only semantic validation is insufficient",
        built=None,
    )


def test_authorization_toxics():
    packet = canonical_apply_packet()
    packet["authorization"]["decision"] = "REJECTED"
    assert_toxic(packet, "authorization.decision must be 'AUTHORIZED'")

    packet = canonical_apply_packet()
    packet["authorization"]["issued_by"] = "godotsim"
    assert_toxic(packet, "authorization.issued_by must be 'engainos'")

    packet = canonical_apply_packet()
    packet["authorization"]["decision_id"] = "some-other-decision"
    assert_toxic(packet, "does not resolve to the trusted EngAInOS decision")

    packet = canonical_apply_packet()
    packet["authorization"]["actor_id"] = "actor-imposter"
    assert_toxic(packet, "actor_id does not match")

    packet = canonical_apply_packet()
    packet["authorization"]["actor_authority_tier"] = True
    assert_toxic(packet, "actor_authority_tier must be an integer tier")

    packet = canonical_apply_packet()
    packet["authorization"]["actor_authority_tier"] = 4
    assert_toxic(packet, "actor_authority_tier must be an integer tier")

    packet = canonical_apply_packet()
    packet["authorization"]["actor_authority_tier"] = 2
    assert_toxic(packet, "actor_authority_tier does not match")

    packet = canonical_apply_packet()
    packet["authorization"]["authority_revision"] = "authority-rev-8"
    assert_toxic(packet, "authority_revision does not match")

    packet = canonical_apply_packet()
    packet["authorization"]["runtime_session_id"] = "session-copied-from-yesterday"
    assert_toxic(packet, "runtime_session_id does not match the trusted runtime session")


def test_replay_reality_mode_rejects_every_packet():
    packet = canonical_apply_packet()
    packet["authorization"]["reality_mode"] = "REPLAY"
    assert_toxic(
        packet,
        "REPLAY reality mode rejects",
        authority=canonical_authority(reality_mode="REPLAY"),
    )


def test_finalized_requires_tier3():
    packet = canonical_apply_packet()
    packet["authorization"]["reality_mode"] = "FINALIZED"
    packet["authorization"]["actor_authority_tier"] = 2
    assert_toxic(
        packet,
        "FINALIZED reality mode requires the Tier 3",
        authority=canonical_authority(reality_mode="FINALIZED", actor_authority_tier=2),
    )

    packet = canonical_apply_packet()
    packet["authorization"]["reality_mode"] = "FINALIZED"
    result = run(packet, authority=canonical_authority(reality_mode="FINALIZED"))
    assert result.accepted, result.errors


def test_unknown_reality_mode_rejects_failclosed():
    packet = canonical_apply_packet()
    packet["authorization"]["reality_mode"] = "DREAM"
    assert_toxic(packet, "reality_mode is unknown")


def test_ap_rule_evidence_rules():
    packet = canonical_apply_packet()
    packet["authorization"]["ap_rule_ids"] = ["ap-rule-invented-999"]
    assert_toxic(packet, "do not match the accepted AP evidence")

    packet = canonical_apply_packet()
    packet["authorization"]["ap_rule_ids"] = []
    assert_toxic(packet, "no AP rule was required")

    packet = canonical_apply_packet()
    packet["authorization"]["ap_rule_ids"] = []
    result = run(
        packet,
        authority=canonical_authority(ap_rule_ids=(), ap_rule_required=False),
    )
    assert result.accepted, result.errors


def test_target_toxics():
    packet = canonical_apply_packet()
    packet["target"]["scene_id"] = "scene-other"
    assert_toxic(packet, "not the accepted EngAInOS scene identity")

    packet = canonical_apply_packet()
    packet["target"]["scene_revision"] = "scene-rev-11"
    assert_toxic(packet, "scene_revision is stale")

    packet = canonical_apply_packet()
    packet["target"]["parent_kind"] = "NODE_PATH"
    assert_toxic(packet, "parent_kind must be SCENE_ROOT, RUNTIME_CONTAINER, or ENTITY_MOUNT")

    packet = canonical_apply_packet()
    packet["target"]["parent_id"] = "container-undeclared"
    assert_toxic(packet, "parent is outside declared scene truth")

    packet = canonical_apply_packet()
    packet["target"]["parent_kind"] = "SCENE_ROOT"
    assert_toxic(packet, "parent is outside declared scene truth")

    packet = canonical_apply_packet()
    packet["target"]["application_slot_id"] = "slot-undeclared"
    assert_toxic(packet, "application_slot_id is outside declared scene truth")


def test_transform_toxics():
    packet = canonical_apply_packet()
    packet["local_to_scene"]["space"] = "GODOT_GLOBAL"
    assert_toxic(packet, "local_to_scene.space must be 'SCENE_LOCAL_Y_UP'")

    packet = canonical_apply_packet()
    packet["local_to_scene"]["basis_columns"] = IDENTITY_BASIS[:2]
    assert_toxic(packet, "exactly three columns")

    packet = canonical_apply_packet()
    packet["local_to_scene"]["basis_columns"] = [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]
    assert_toxic(packet, "exactly three columns of three finite numbers")

    packet = canonical_apply_packet()
    packet["local_to_scene"]["basis_columns"][1][1] = float("nan")
    assert_toxic(packet, "finite numbers")

    packet = canonical_apply_packet()
    packet["local_to_scene"]["origin"] = [0.0, float("inf"), 0.0]
    assert_toxic(packet, "origin must contain exactly three finite numbers")

    packet = canonical_apply_packet()
    packet["local_to_scene"]["basis_columns"][2][2] = "1.0"
    assert_toxic(packet, "finite numbers")

    singular = canonical_apply_packet()
    singular["local_to_scene"]["basis_columns"] = [
        [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0],
    ]
    assert_toxic(singular, "determinant must be strictly positive")

    zero_scale = canonical_apply_packet()
    zero_scale["local_to_scene"]["basis_columns"] = [
        [0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
    ]
    assert_toxic(zero_scale, "determinant must be strictly positive")

    reflected = canonical_apply_packet()
    reflected["local_to_scene"]["basis_columns"] = [
        [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0],
    ]
    assert_toxic(reflected, "determinant must be strictly positive")

    scaled = canonical_apply_packet()
    scaled["local_to_scene"]["basis_columns"] = [
        [2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0],
    ]
    scaled["local_to_scene"]["origin"] = [10.0, 0.5, -3.0]
    result = run(scaled, authority=authority_for(scaled))
    assert result.accepted, result.errors


@pytest.mark.parametrize("bad_intent", ["INHERIT", "AUTO", "", 1, None])
def test_implicit_visibility_rejects(bad_intent):
    packet = canonical_apply_packet()
    packet["visibility"]["intent"] = bad_intent
    assert_toxic(packet, "visibility.intent must be exactly VISIBLE or HIDDEN")


def test_hidden_visibility_accepts():
    packet = canonical_apply_packet()
    packet["visibility"]["intent"] = "HIDDEN"
    result = run(packet, authority=authority_for(packet))
    assert result.accepted, result.errors


def test_replacement_toxics():
    packet = canonical_apply_packet()
    packet["replacement"]["replaces_apply_id"] = PRIOR_APPLY_ID
    assert_toxic(packet, "CREATE_ONLY requires replaces_apply_id to be null")

    packet = canonical_apply_packet()
    packet["target"]["application_slot_id"] = OCCUPIED_SLOT_ID
    assert_toxic(packet, "CREATE_ONLY requires an empty application slot")

    packet = canonical_apply_packet()
    packet["replacement"] = {"mode": "REPLACE_EXACT", "replaces_apply_id": None}
    packet["target"]["application_slot_id"] = OCCUPIED_SLOT_ID
    assert_toxic(packet, "REPLACE_EXACT requires a canonical prior apply_id")

    packet = canonical_apply_packet()
    packet["replacement"] = {"mode": "REPLACE_EXACT", "replaces_apply_id": APPLY_ID}
    packet["target"]["application_slot_id"] = OCCUPIED_SLOT_ID
    assert_toxic(packet, "cannot replace itself")

    packet = canonical_apply_packet()
    packet["replacement"] = {
        "mode": "REPLACE_EXACT",
        "replaces_apply_id": "t32dapply_0123456789abcdef",
    }
    packet["target"]["application_slot_id"] = OCCUPIED_SLOT_ID
    assert_toxic(packet, "occupant does not match exactly")

    packet = canonical_apply_packet()
    packet["replacement"]["mode"] = "REPLACE_CURRENT"
    assert_toxic(packet, "replacement.mode must be CREATE_ONLY or REPLACE_EXACT")


def test_replace_exact_matching_occupant_accepts():
    packet = canonical_apply_packet()
    packet["replacement"] = {"mode": "REPLACE_EXACT", "replaces_apply_id": PRIOR_APPLY_ID}
    packet["target"]["application_slot_id"] = OCCUPIED_SLOT_ID
    result = run(packet, authority=authority_for(packet))
    assert result.accepted, result.errors


def test_lifetime_toxics():
    packet = canonical_apply_packet()
    packet["lifetime"]["mode"] = "FOREVER"
    assert_toxic(packet, "lifetime.mode must be SCENE_BOUND, RUNTIME_SESSION, or CANONICAL_PERSISTENT")

    packet = canonical_apply_packet()
    packet["lifetime"]["mode"] = "CANONICAL_PERSISTENT"
    assert_toxic(packet, "requires explicit trusted EngAInOS persistence authorization")

    packet = canonical_apply_packet()
    packet["lifetime"]["mode"] = "CANONICAL_PERSISTENT"
    result = run(packet, authority=authority_for(packet, canonical_persistence_authorized=True))
    assert result.accepted, result.errors

    packet = canonical_apply_packet()
    packet["lifetime"]["mode"] = "RUNTIME_SESSION"
    result = run(packet, authority=authority_for(packet))
    assert result.accepted, result.errors


def test_classification_collision_contradictions():
    packet = canonical_apply_packet()
    packet["classification"] = "TERRAIN"
    assert_toxic(packet, "classification must be PRESENTATION_ONLY, STATIC_SPATIAL, or DYNAMIC_SPATIAL")

    packet = canonical_apply_packet()
    packet["collision"] = {
        "decision": "GRANTED",
        "authorized_by_decision_id": DECISION_ID,
        "shape_policy": "CANONICAL_MESH_EXACT",
        "layer": 1,
        "mask": 0,
    }
    assert_toxic(
        packet,
        "PRESENTATION_ONLY requires collision DENIED",
        authority=canonical_authority(
            collision_grant=canonical_collision_grant(classification="PRESENTATION_ONLY")
        ),
    )

    packet = canonical_apply_packet()
    packet["collision"]["layer"] = 1
    assert_toxic(packet, "explicit collision denial requires layer 0")

    packet = canonical_apply_packet()
    packet["collision"]["mask"] = 5
    assert_toxic(packet, "explicit collision denial requires mask 0")

    packet = canonical_apply_packet()
    packet["collision"]["shape_policy"] = "CANONICAL_MESH_EXACT"
    assert_toxic(packet, "explicit collision denial requires shape_policy NONE")

    packet = canonical_apply_packet()
    packet["collision"]["authorized_by_decision_id"] = "some-other-decision"
    assert_toxic(packet, "must exactly equal authorization.decision_id")

    packet = canonical_apply_packet()
    packet["collision"]["decision"] = "MAYBE"
    assert_toxic(packet, "collision.decision must be exactly DENIED or GRANTED")


def granted_packet() -> dict[str, Any]:
    packet = canonical_apply_packet()
    packet["classification"] = "STATIC_SPATIAL"
    packet["collision"] = {
        "decision": "GRANTED",
        "authorized_by_decision_id": DECISION_ID,
        "shape_policy": "CANONICAL_MESH_EXACT",
        "layer": 1,
        "mask": 0,
    }
    return packet


def test_collision_grant_requirements():
    assert_toxic(
        granted_packet(),
        "GRANTED without exact trusted EngAInOS collision authorization",
        authority=canonical_authority(collision_grant=None),
    )

    packet = granted_packet()
    packet["collision"]["layer"] = 0
    assert_toxic(
        packet,
        "integer layer from 1 through 4294967295",
        authority=canonical_authority(collision_grant=canonical_collision_grant()),
    )

    packet = granted_packet()
    packet["collision"]["layer"] = 4294967296
    assert_toxic(
        packet,
        "integer layer from 1 through 4294967295",
        authority=canonical_authority(collision_grant=canonical_collision_grant()),
    )

    packet = granted_packet()
    packet["collision"]["mask"] = -1
    assert_toxic(
        packet,
        "integer mask from 0 through 4294967295",
        authority=canonical_authority(collision_grant=canonical_collision_grant()),
    )

    packet = granted_packet()
    packet["collision"]["shape_policy"] = "CONVEX_HULL"
    assert_toxic(
        packet,
        "requires shape_policy CANONICAL_MESH_EXACT",
        authority=canonical_authority(collision_grant=canonical_collision_grant()),
    )

    packet = granted_packet()
    packet["collision"]["layer"] = 2
    assert_toxic(
        packet,
        "does not cover this exact scene revision",
        authority=canonical_authority(collision_grant=canonical_collision_grant(layer=1)),
    )

    packet = granted_packet()
    packet["local_to_scene"]["origin"] = [0.0, 1.0, 0.0]
    assert_toxic(
        packet,
        "does not cover this exact scene revision",
        authority=canonical_authority(collision_grant=canonical_collision_grant()),
    )

    assert_toxic(
        granted_packet(),
        "does not cover this exact scene revision",
        authority=canonical_authority(
            collision_grant=canonical_collision_grant(scene_revision="scene-rev-11")
        ),
    )

    assert_toxic(
        granted_packet(),
        "does not cover this exact scene revision",
        authority=canonical_authority(
            collision_grant=canonical_collision_grant(built_response_sha256="1" * 64)
        ),
    )

    result = run(
        granted_packet(),
        authority=authority_for(granted_packet(), collision_grant=canonical_collision_grant()),
    )
    assert result.accepted, result.errors


def test_dynamic_spatial_with_denied_collision_accepts():
    packet = canonical_apply_packet()
    packet["classification"] = "DYNAMIC_SPATIAL"
    result = run(packet, authority=authority_for(packet))
    assert result.accepted, result.errors


def test_untrusted_context_rejects_failclosed():
    result = run(canonical_apply_packet(), authority="not-an-authority")
    assert not result.accepted
    assert any("TrustedApplicationAuthority" in error for error in result.errors)

    result = run(canonical_apply_packet(), scene="not-scene-truth")
    assert not result.accepted
    assert any("TrustedSceneTruth" in error for error in result.errors)

    result = run(canonical_apply_packet(), authority=canonical_authority(actor_authority_tier=5))
    assert not result.accepted
    assert any("tier 0 through 3" in error for error in result.errors)

    result = run(canonical_apply_packet(), authority=canonical_authority(reality_mode="DREAM"))
    assert not result.accepted
    assert any("reality_mode is unknown" in error for error in result.errors)

    result = run(canonical_apply_packet(), authority=canonical_authority(runtime_session_id=""))
    assert not result.accepted
    assert any("runtime_session_id must be a non-empty string" in error for error in result.errors)


def test_non_dict_packet_rejects():
    result = run(["not", "a", "packet"])
    assert not result.accepted
    assert result.errors == ("application packet must be a dict",)


def test_authority_reuse_with_different_apply_intent_rejects():
    """One trusted authority covers exactly one application intent (review finding 1)."""
    variant = canonical_apply_packet()
    variant["apply_id"] = OTHER_APPLY_ID
    assert_toxic(variant, "exact application intent")

    variant = canonical_apply_packet()
    variant["target"]["parent_kind"] = ROOT_PARENT_KIND
    variant["target"]["parent_id"] = ROOT_PARENT_ID
    variant["target"]["application_slot_id"] = ROOT_SLOT_ID
    assert_toxic(variant, "exact application intent")

    variant = canonical_apply_packet()
    variant["local_to_scene"]["origin"] = [4.0, 0.0, -2.0]
    assert_toxic(variant, "exact application intent")

    variant = canonical_apply_packet()
    variant["visibility"]["intent"] = "HIDDEN"
    assert_toxic(variant, "exact application intent")

    variant = canonical_apply_packet()
    variant["replacement"] = {"mode": "REPLACE_EXACT", "replaces_apply_id": PRIOR_APPLY_ID}
    variant["target"]["application_slot_id"] = OCCUPIED_SLOT_ID
    assert_toxic(variant, "exact application intent")

    variant = canonical_apply_packet()
    variant["lifetime"]["mode"] = "RUNTIME_SESSION"
    assert_toxic(variant, "exact application intent")

    variant = canonical_apply_packet()
    variant["classification"] = "DYNAMIC_SPATIAL"
    assert_toxic(variant, "exact application intent")

    foreign_surface_intent = canonical_apply_packet()
    foreign_surface_intent["surface_binding"]["request_id"] = "t32dreq_0000000000000000"
    assert_toxic(
        canonical_apply_packet(),
        "exact application intent",
        authority=canonical_authority(
            authorized_intent_sha256=canonical_application_intent_digest(foreign_surface_intent)
        ),
    )

    authorized = canonical_apply_packet()
    authorized["visibility"]["intent"] = "HIDDEN"
    result = run(authorized, authority=authority_for(authorized))
    assert result.accepted, result.errors

    result = run(
        canonical_apply_packet(),
        authority=canonical_authority(authorized_intent_sha256="not-a-digest"),
    )
    assert not result.accepted
    assert any("authorized_intent_sha256" in error for error in result.errors)


def test_collision_flip_under_denied_intent_rejects():
    """An authority that authorized a DENIED collision declaration does not cover GRANTED."""
    denied = canonical_apply_packet()
    denied["classification"] = "STATIC_SPATIAL"
    authority = authority_for(denied, collision_grant=canonical_collision_grant())
    result = run(denied, authority=authority)
    assert result.accepted, result.errors

    granted = copy.deepcopy(denied)
    granted["collision"] = {
        "decision": "GRANTED",
        "authorized_by_decision_id": DECISION_ID,
        "shape_policy": "CANONICAL_MESH_EXACT",
        "layer": 1,
        "mask": 0,
    }
    assert_toxic(granted, "exact application intent", authority=authority)


def test_slot_of_foreign_declared_parent_rejects():
    """A declared slot must belong to the declared parent (review finding 2)."""
    packet = canonical_apply_packet()
    packet["target"]["application_slot_id"] = ROOT_SLOT_ID
    assert_toxic(packet, "does not belong to the declared parent")

    packet = canonical_apply_packet()
    packet["target"]["parent_kind"] = ROOT_PARENT_KIND
    packet["target"]["parent_id"] = ROOT_PARENT_ID
    assert_toxic(packet, "does not belong to the declared parent")


def test_gate_wrapper_discriminator_claims_are_false_not_skipped():
    """A packet claiming the apply contract by either discriminator is FALSE, never SKIPPED (review finding 3)."""
    def gate(packet: Any):
        return gate_trixel32d_surface_apply(
            packet,
            built_validation=ACCEPTED_BUILT,
            authority=canonical_authority(),
            scene_truth=canonical_scene_truth(),
        )

    missing_type = canonical_apply_packet()
    del missing_type["packet_type"]
    assert gate(missing_type).is_false()

    wrong_type = canonical_apply_packet()
    wrong_type["packet_type"] = "trixel32d_surface_built"
    assert gate(wrong_type).is_false()

    missing_contract = canonical_apply_packet()
    del missing_contract["contract"]
    assert gate(missing_contract).is_false()

    wrong_contract = canonical_apply_packet()
    wrong_contract["contract"] = "trixel32d_surface_built.v1"
    assert gate(wrong_contract).is_false()

    assert gate({"contract": "trixel32d_surface_apply.v1"}).is_false()
    assert gate({"packet_type": "trixel32d_surface_apply"}).is_false()

    neither = {"contract": "trixel32d_surface_built.v1", "packet_type": "trixel32d_surface_built"}
    assert gate(neither).is_skipped()
    assert gate({}).is_skipped()


def test_gate_wrapper():
    accepted = gate_trixel32d_surface_apply(
        canonical_apply_packet(),
        built_validation=ACCEPTED_BUILT,
        authority=canonical_authority(),
        scene_truth=canonical_scene_truth(),
    )
    assert accepted.is_true()

    toxic = canonical_apply_packet()
    toxic["authorization"]["issued_by"] = "godot"
    rejected = gate_trixel32d_surface_apply(
        toxic,
        built_validation=ACCEPTED_BUILT,
        authority=canonical_authority(),
        scene_truth=canonical_scene_truth(),
    )
    assert rejected.is_false()
    assert "issued_by" in rejected.message

    skipped = gate_trixel32d_surface_apply(
        {"packet_type": "trixel32d_surface_built"},
        built_validation=ACCEPTED_BUILT,
        authority=canonical_authority(),
        scene_truth=canonical_scene_truth(),
    )
    assert skipped.is_skipped()

    not_dict = gate_trixel32d_surface_apply(
        "packet",
        built_validation=ACCEPTED_BUILT,
        authority=canonical_authority(),
        scene_truth=canonical_scene_truth(),
    )
    assert not_dict.is_false()
