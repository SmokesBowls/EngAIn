from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

"""Pure fail-closed validator for `trixel32d_surface_apply.v1`.

Contract authority: docs/contracts/TRIXEL32D_SURFACE_APPLY_CONTRACT_v1.md.

This gate validates an application-authorization packet against the trusted
EngAInOS authority envelope, trusted scene truth, and the identity-complete
byte-level built-response validation result. It performs no transport, starts
no runtime, attaches no node, allocates no collision, and mutates no scene or
canonical state. Acceptance returns a deeply immutable packet; rejection
returns errors and nothing else.
"""

import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tier1.engainos.gates.gate_trixel32d_handshake import (
    BuiltSurfaceValidation,
    GateResult,
)

APPLY_CONTRACT = "trixel32d_surface_apply.v1"
APPLY_PACKET_TYPE = "trixel32d_surface_apply"
BUILT_CONTRACT = "trixel32d_surface_built.v1"

_ID_PATTERNS = {
    "apply_id": re.compile(r"^t32dapply_[0-9a-f]{16}$"),
    "request_id": re.compile(r"^t32dreq_[0-9a-f]{16}$"),
    "surface_id": re.compile(r"^t32dsurface_[0-9a-f]{16}$"),
}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_ROOT_FIELDS = frozenset({
    "contract",
    "packet_type",
    "apply_id",
    "surface_binding",
    "authorization",
    "target",
    "local_to_scene",
    "visibility",
    "replacement",
    "lifetime",
    "classification",
    "collision",
})
_SURFACE_BINDING_FIELDS = frozenset({
    "built_contract",
    "request_id",
    "surface_id",
    "built_response_sha256",
})
_AUTHORIZATION_FIELDS = frozenset({
    "decision",
    "decision_id",
    "issued_by",
    "actor_id",
    "actor_authority_tier",
    "reality_mode",
    "authority_revision",
    "runtime_session_id",
    "ap_rule_ids",
})
_TARGET_FIELDS = frozenset({
    "scene_id",
    "scene_revision",
    "parent_kind",
    "parent_id",
    "application_slot_id",
})
_LOCAL_TO_SCENE_FIELDS = frozenset({"space", "basis_columns", "origin"})
_VISIBILITY_FIELDS = frozenset({"intent"})
_REPLACEMENT_FIELDS = frozenset({"mode", "replaces_apply_id"})
_LIFETIME_FIELDS = frozenset({"mode"})
_COLLISION_FIELDS = frozenset({
    "decision",
    "authorized_by_decision_id",
    "shape_policy",
    "layer",
    "mask",
})

_INTENT_FIELDS = (
    "apply_id",
    "surface_binding",
    "target",
    "local_to_scene",
    "visibility",
    "replacement",
    "lifetime",
    "classification",
    "collision",
)

_PARENT_KINDS = frozenset({"SCENE_ROOT", "RUNTIME_CONTAINER", "ENTITY_MOUNT"})
_REALITY_MODES = frozenset({"DRAFT", "FINALIZED", "REPLAY"})
_VISIBILITY_INTENTS = frozenset({"VISIBLE", "HIDDEN"})
_REPLACEMENT_MODES = frozenset({"CREATE_ONLY", "REPLACE_EXACT"})
_LIFETIME_MODES = frozenset({"SCENE_BOUND", "RUNTIME_SESSION", "CANONICAL_PERSISTENT"})
_CLASSIFICATIONS = frozenset({"PRESENTATION_ONLY", "STATIC_SPATIAL", "DYNAMIC_SPATIAL"})
_SPATIAL_CLASSIFICATIONS = frozenset({"STATIC_SPATIAL", "DYNAMIC_SPATIAL"})
_COLLISION_DECISIONS = frozenset({"DENIED", "GRANTED"})
_COLLISION_LAYER_MASK_MAX = 4294967295
_ACTOR_TIERS = frozenset({0, 1, 2, 3})
_TIER_HUMAN_AUTHORITY_ROOT = 3


@dataclass(frozen=True)
class CollisionGrantEvidence:
    """Trusted EngAInOS evidence explicitly authorizing collision (section 14.2)."""

    scene_revision: str
    request_id: str
    surface_id: str
    built_response_sha256: str
    basis_columns: tuple[tuple[float, float, float], ...]
    origin: tuple[float, float, float]
    classification: str
    shape_policy: str
    layer: int
    mask: int


def canonical_application_intent_digest(intent: Mapping[str, Any]) -> str:
    """Deterministic digest of one exact application intent.

    Trusted EngAInOS issuance and this gate derive the digest from the same
    canonical serialization of the intent-defining fields, so an authority
    envelope covers exactly one apply_id, surface binding, target, transform,
    visibility, replacement, lifetime, classification, and collision
    declaration.
    """
    payload = {field: intent[field] for field in _INTENT_FIELDS}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class TrustedApplicationAuthority:
    """Trusted EngAInOS authority envelope for one application decision.

    Values must come from accepted EngAInOS authority evidence, never from an
    untrusted request or a renderer/client (contract sections 3.1 and 7).
    authorized_intent_sha256 binds the decision to exactly one application
    intent via canonical_application_intent_digest.
    """

    decision_id: str
    actor_id: str
    actor_authority_tier: int
    reality_mode: str
    authority_revision: str
    runtime_session_id: str
    authorized_intent_sha256: str
    ap_rule_ids: tuple[str, ...]
    ap_rule_required: bool
    canonical_persistence_authorized: bool
    collision_grant: CollisionGrantEvidence | None


@dataclass(frozen=True)
class TrustedSceneTruth:
    """Declared scene truth the target block is validated against (section 8).

    declared_targets holds complete (parent_kind, parent_id, application_slot_id)
    tuples; a slot exists only as part of the parent that declares it.
    """

    scene_id: str
    active_scene_revision: str
    declared_targets: frozenset[tuple[str, str, str]]
    slot_occupancy: Mapping[str, str]


@dataclass(frozen=True)
class ApplySurfaceValidation:
    """Result bound to one immutable accepted application packet."""

    packet: Mapping[str, Any] | None
    errors: tuple[str, ...]

    @property
    def accepted(self) -> bool:
        return not self.errors and self.packet is not None


def _canonical_identity(value: Any, field: str) -> bool:
    return isinstance(value, str) and _ID_PATTERNS[field].fullmatch(value) is not None


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def _strict_integer(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int)


def _finite_triple(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(_finite_number(component) for component in value)
    )


def _basis_determinant(columns: list[list[float]]) -> float:
    (a, d, g), (b, e, h), (c, f, i) = columns
    return (
        float(a) * (float(e) * float(i) - float(f) * float(h))
        - float(b) * (float(d) * float(i) - float(f) * float(g))
        + float(c) * (float(d) * float(h) - float(e) * float(g))
    )


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _closed_object(value: Any, name: str, fields: frozenset[str], errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return False
    unknown = sorted(set(value.keys()) - fields)
    if unknown:
        errors.append(f"{name} contains undeclared keys: {', '.join(unknown)}")
        return False
    missing = sorted(fields - set(value.keys()))
    if missing:
        errors.append(f"{name} is missing required keys: {', '.join(missing)}")
        return False
    return True


def _validate_trusted_authority(authority: Any, errors: list[str]) -> bool:
    if not isinstance(authority, TrustedApplicationAuthority):
        errors.append("trusted authority evidence must be a TrustedApplicationAuthority")
        return False
    if not _nonempty_string(authority.decision_id):
        errors.append("trusted authority decision_id must be a non-empty string")
        return False
    if not _nonempty_string(authority.actor_id):
        errors.append("trusted authority actor_id must be a non-empty string")
        return False
    if not _strict_integer(authority.actor_authority_tier) or authority.actor_authority_tier not in _ACTOR_TIERS:
        errors.append("trusted authority actor_authority_tier must be an integer tier 0 through 3")
        return False
    if authority.reality_mode not in _REALITY_MODES:
        errors.append("trusted authority reality_mode is unknown; rejecting fail-closed")
        return False
    if not _nonempty_string(authority.authority_revision):
        errors.append("trusted authority authority_revision must be a non-empty string")
        return False
    if not _nonempty_string(authority.runtime_session_id):
        errors.append("trusted authority runtime_session_id must be a non-empty string")
        return False
    if not isinstance(authority.authorized_intent_sha256, str) or _SHA256_PATTERN.fullmatch(
        authority.authorized_intent_sha256
    ) is None:
        errors.append(
            "trusted authority authorized_intent_sha256 must be a 64-character"
            " lowercase hexadecimal intent digest"
        )
        return False
    if not isinstance(authority.ap_rule_ids, tuple) or not all(
        _nonempty_string(rule_id) for rule_id in authority.ap_rule_ids
    ):
        errors.append("trusted authority ap_rule_ids must be a tuple of non-empty strings")
        return False
    if len(set(authority.ap_rule_ids)) != len(authority.ap_rule_ids):
        errors.append("trusted authority ap_rule_ids must be unique")
        return False
    if not isinstance(authority.ap_rule_required, bool):
        errors.append("trusted authority ap_rule_required must be a bool")
        return False
    if not isinstance(authority.canonical_persistence_authorized, bool):
        errors.append("trusted authority canonical_persistence_authorized must be a bool")
        return False
    if authority.collision_grant is not None and not isinstance(
        authority.collision_grant, CollisionGrantEvidence
    ):
        errors.append("trusted authority collision_grant must be CollisionGrantEvidence or None")
        return False
    return True


def _validate_trusted_scene_truth(scene_truth: Any, errors: list[str]) -> bool:
    if not isinstance(scene_truth, TrustedSceneTruth):
        errors.append("trusted scene truth must be a TrustedSceneTruth")
        return False
    if not _nonempty_string(scene_truth.scene_id):
        errors.append("trusted scene truth scene_id must be a non-empty string")
        return False
    if not _nonempty_string(scene_truth.active_scene_revision):
        errors.append("trusted scene truth active_scene_revision must be a non-empty string")
        return False
    if not isinstance(scene_truth.declared_targets, frozenset) or not all(
        isinstance(target, tuple)
        and len(target) == 3
        and all(_nonempty_string(part) for part in target)
        for target in scene_truth.declared_targets
    ):
        errors.append(
            "trusted scene truth declared_targets must be a frozenset of"
            " (parent_kind, parent_id, application_slot_id) tuples"
        )
        return False
    if not isinstance(scene_truth.slot_occupancy, Mapping):
        errors.append("trusted scene truth slot_occupancy must be a mapping")
        return False
    return True


def _validate_built_binding(
    binding: dict[str, Any],
    built_validation: Any,
    errors: list[str],
) -> None:
    if not isinstance(built_validation, BuiltSurfaceValidation):
        errors.append(
            "built-response evidence must be the byte-level BuiltSurfaceValidation result;"
            " dict-only semantic validation is insufficient application evidence"
        )
        return
    if not built_validation.accepted:
        errors.append("built-response validation was not accepted; application cannot bind to it")
        return
    if not isinstance(built_validation.response_sha256, str) or _SHA256_PATTERN.fullmatch(
        built_validation.response_sha256
    ) is None:
        errors.append("built-response validation does not carry an exact-byte SHA-256")
        return

    built_packet = built_validation.packet
    if not isinstance(built_packet, Mapping):
        errors.append("built-response validation does not carry an accepted packet")
        return
    if built_packet.get("contract") != BUILT_CONTRACT:
        errors.append("accepted built response contract is not trixel32d_surface_built.v1")
        return
    if built_packet.get("status") != "BUILT":
        errors.append("accepted built response status must be BUILT")
        return

    if binding.get("built_contract") != BUILT_CONTRACT:
        errors.append("surface_binding.built_contract must be 'trixel32d_surface_built.v1'")
    request_id = binding.get("request_id")
    if not _canonical_identity(request_id, "request_id"):
        errors.append("surface_binding.request_id must be a canonical t32dreq identity")
    elif request_id != built_packet.get("request_id"):
        errors.append("surface_binding.request_id does not match the validated built response")
    surface_id = binding.get("surface_id")
    if not _canonical_identity(surface_id, "surface_id"):
        errors.append("surface_binding.surface_id must be a canonical t32dsurface identity")
    elif surface_id != built_packet.get("surface_id"):
        errors.append("surface_binding.surface_id does not match the validated built response")
    bound_sha256 = binding.get("built_response_sha256")
    if not isinstance(bound_sha256, str) or _SHA256_PATTERN.fullmatch(bound_sha256) is None:
        errors.append("surface_binding.built_response_sha256 must be 64 lowercase hexadecimal characters")
    elif bound_sha256 != built_validation.response_sha256:
        errors.append("surface_binding.built_response_sha256 does not match the exact validated bytes")


def _validate_authorization(
    authorization: dict[str, Any],
    authority: TrustedApplicationAuthority,
    errors: list[str],
) -> None:
    if authorization.get("decision") != "AUTHORIZED":
        errors.append("authorization.decision must be 'AUTHORIZED'")
    if authorization.get("issued_by") != "engainos":
        errors.append("authorization.issued_by must be 'engainos'")
    if not _nonempty_string(authorization.get("decision_id")):
        errors.append("authorization.decision_id must be a non-empty string")
    elif authorization["decision_id"] != authority.decision_id:
        errors.append("authorization.decision_id does not resolve to the trusted EngAInOS decision")
    if not _nonempty_string(authorization.get("actor_id")):
        errors.append("authorization.actor_id must be a non-empty string")
    elif authorization["actor_id"] != authority.actor_id:
        errors.append("authorization.actor_id does not match the trusted authority evidence")
    tier = authorization.get("actor_authority_tier")
    if not _strict_integer(tier) or tier not in _ACTOR_TIERS:
        errors.append("authorization.actor_authority_tier must be an integer tier 0 through 3")
    elif tier != authority.actor_authority_tier:
        errors.append("authorization.actor_authority_tier does not match the trusted authority evidence")
    reality_mode = authorization.get("reality_mode")
    if reality_mode not in _REALITY_MODES:
        errors.append("authorization.reality_mode is unknown; rejecting fail-closed")
    else:
        if reality_mode != authority.reality_mode:
            errors.append("authorization.reality_mode does not match the trusted authority evidence")
        if reality_mode == "REPLAY":
            errors.append("REPLAY reality mode rejects every application packet")
        if (
            reality_mode == "FINALIZED"
            and authority.actor_authority_tier != _TIER_HUMAN_AUTHORITY_ROOT
        ):
            errors.append("FINALIZED reality mode requires the Tier 3 human authority root")
    if not _nonempty_string(authorization.get("authority_revision")):
        errors.append("authorization.authority_revision must be a non-empty string")
    elif authorization["authority_revision"] != authority.authority_revision:
        errors.append("authorization.authority_revision does not match the trusted authority evidence")
    if not _nonempty_string(authorization.get("runtime_session_id")):
        errors.append("authorization.runtime_session_id must be a non-empty string")
    elif authorization["runtime_session_id"] != authority.runtime_session_id:
        errors.append("authorization.runtime_session_id does not match the trusted runtime session")
    ap_rule_ids = authorization.get("ap_rule_ids")
    if not isinstance(ap_rule_ids, list) or not all(
        _nonempty_string(rule_id) for rule_id in ap_rule_ids
    ):
        errors.append("authorization.ap_rule_ids must be an array of non-empty strings")
    else:
        if tuple(ap_rule_ids) != authority.ap_rule_ids:
            errors.append("authorization.ap_rule_ids do not match the accepted AP evidence")
        if not ap_rule_ids and authority.ap_rule_required:
            errors.append(
                "authorization.ap_rule_ids may be empty only when the governing decision"
                " proves no AP rule was required"
            )


def _validate_target(
    target: dict[str, Any],
    scene_truth: TrustedSceneTruth,
    errors: list[str],
) -> None:
    if not _nonempty_string(target.get("scene_id")):
        errors.append("target.scene_id must be a non-empty string")
    elif target["scene_id"] != scene_truth.scene_id:
        errors.append("target.scene_id is not the accepted EngAInOS scene identity")
    if not _nonempty_string(target.get("scene_revision")):
        errors.append("target.scene_revision must be a non-empty string")
    elif target["scene_revision"] != scene_truth.active_scene_revision:
        errors.append("target.scene_revision is stale; application rejects rather than retargeting")
    declared_parents = {(kind, parent) for kind, parent, _ in scene_truth.declared_targets}
    declared_slots = {slot for _, _, slot in scene_truth.declared_targets}
    parent_kind = target.get("parent_kind")
    if parent_kind not in _PARENT_KINDS:
        errors.append("target.parent_kind must be SCENE_ROOT, RUNTIME_CONTAINER, or ENTITY_MOUNT")
    parent_id = target.get("parent_id")
    parent_declared = False
    if not _nonempty_string(parent_id):
        errors.append("target.parent_id must be a non-empty string")
    elif parent_kind in _PARENT_KINDS:
        if (parent_kind, parent_id) not in declared_parents:
            errors.append("target parent is outside declared scene truth")
        else:
            parent_declared = True
    slot_id = target.get("application_slot_id")
    if not _nonempty_string(slot_id):
        errors.append("target.application_slot_id must be a non-empty string")
    elif slot_id not in declared_slots:
        errors.append("target.application_slot_id is outside declared scene truth")
    elif parent_declared and (parent_kind, parent_id, slot_id) not in scene_truth.declared_targets:
        errors.append("target.application_slot_id does not belong to the declared parent")


def _validate_local_to_scene(local_to_scene: dict[str, Any], errors: list[str]) -> None:
    if local_to_scene.get("space") != "SCENE_LOCAL_Y_UP":
        errors.append("local_to_scene.space must be 'SCENE_LOCAL_Y_UP'")
    basis_columns = local_to_scene.get("basis_columns")
    if (
        not isinstance(basis_columns, list)
        or len(basis_columns) != 3
        or not all(_finite_triple(column) for column in basis_columns)
    ):
        errors.append("local_to_scene.basis_columns must be exactly three columns of three finite numbers")
        basis_columns = None
    if not _finite_triple(local_to_scene.get("origin")):
        errors.append("local_to_scene.origin must contain exactly three finite numbers")
    if basis_columns is not None:
        determinant = _basis_determinant(basis_columns)
        if not math.isfinite(determinant) or determinant <= 0.0:
            errors.append(
                "local_to_scene basis determinant must be strictly positive;"
                " singular, zero-scale, and reflected transforms reject"
            )


def _validate_replacement(
    replacement: dict[str, Any],
    apply_id: Any,
    target: Any,
    scene_truth: TrustedSceneTruth,
    errors: list[str],
) -> None:
    mode = replacement.get("mode")
    if mode not in _REPLACEMENT_MODES:
        errors.append("replacement.mode must be CREATE_ONLY or REPLACE_EXACT")
        return
    slot_id = target.get("application_slot_id") if isinstance(target, dict) else None
    occupant = (
        scene_truth.slot_occupancy.get(slot_id)
        if isinstance(slot_id, str)
        else None
    )
    replaces_apply_id = replacement.get("replaces_apply_id")
    if mode == "CREATE_ONLY":
        if replaces_apply_id is not None:
            errors.append("CREATE_ONLY requires replaces_apply_id to be null")
        if occupant is not None:
            errors.append("CREATE_ONLY requires an empty application slot")
        return
    if not _canonical_identity(replaces_apply_id, "apply_id"):
        errors.append("REPLACE_EXACT requires a canonical prior apply_id in replaces_apply_id")
        return
    if replaces_apply_id == apply_id:
        errors.append("an apply_id identifies one immutable decision and cannot replace itself")
    if occupant != replaces_apply_id:
        errors.append("REPLACE_EXACT occupant does not match exactly; wildcard replacement is forbidden")


def _validate_lifetime(
    lifetime: dict[str, Any],
    authority: TrustedApplicationAuthority,
    errors: list[str],
) -> None:
    mode = lifetime.get("mode")
    if mode not in _LIFETIME_MODES:
        errors.append("lifetime.mode must be SCENE_BOUND, RUNTIME_SESSION, or CANONICAL_PERSISTENT")
        return
    if mode == "CANONICAL_PERSISTENT":
        if not authority.canonical_persistence_authorized:
            errors.append(
                "CANONICAL_PERSISTENT is a canonical mutation and requires explicit"
                " trusted EngAInOS persistence authorization"
            )
        if (
            authority.reality_mode == "FINALIZED"
            and authority.actor_authority_tier != _TIER_HUMAN_AUTHORITY_ROOT
        ):
            errors.append("CANONICAL_PERSISTENT into FINALIZED state requires Tier 3")


def _validate_collision(
    collision: dict[str, Any],
    packet: dict[str, Any],
    authority: TrustedApplicationAuthority,
    errors: list[str],
) -> None:
    decision = collision.get("decision")
    if decision not in _COLLISION_DECISIONS:
        errors.append("collision.decision must be exactly DENIED or GRANTED; there is no default")
        return
    authorization = packet.get("authorization")
    declared_decision_id = (
        authorization.get("decision_id") if isinstance(authorization, dict) else None
    )
    if collision.get("authorized_by_decision_id") != declared_decision_id or not _nonempty_string(
        collision.get("authorized_by_decision_id")
    ):
        errors.append("collision.authorized_by_decision_id must exactly equal authorization.decision_id")

    classification = packet.get("classification")
    layer = collision.get("layer")
    mask = collision.get("mask")

    if decision == "DENIED":
        if collision.get("shape_policy") != "NONE":
            errors.append("explicit collision denial requires shape_policy NONE")
        if layer != 0 or isinstance(layer, bool) or not isinstance(layer, int):
            errors.append("explicit collision denial requires layer 0")
        if mask != 0 or isinstance(mask, bool) or not isinstance(mask, int):
            errors.append("explicit collision denial requires mask 0")
        return

    if classification not in _SPATIAL_CLASSIFICATIONS:
        errors.append("collision GRANTED requires STATIC_SPATIAL or DYNAMIC_SPATIAL classification")
    if collision.get("shape_policy") != "CANONICAL_MESH_EXACT":
        errors.append("collision GRANTED requires shape_policy CANONICAL_MESH_EXACT in v1")
    if not _strict_integer(layer) or not 1 <= layer <= _COLLISION_LAYER_MASK_MAX:
        errors.append("collision GRANTED requires an integer layer from 1 through 4294967295")
    if not _strict_integer(mask) or not 0 <= mask <= _COLLISION_LAYER_MASK_MAX:
        errors.append("collision GRANTED requires an integer mask from 0 through 4294967295")

    grant = authority.collision_grant
    if grant is None:
        errors.append("collision GRANTED without exact trusted EngAInOS collision authorization")
        return

    binding = packet.get("surface_binding")
    target = packet.get("target")
    local_to_scene = packet.get("local_to_scene")
    binding_matches = (
        isinstance(binding, dict)
        and binding.get("request_id") == grant.request_id
        and binding.get("surface_id") == grant.surface_id
        and binding.get("built_response_sha256") == grant.built_response_sha256
    )
    scene_matches = (
        isinstance(target, dict) and target.get("scene_revision") == grant.scene_revision
    )
    transform_matches = False
    if isinstance(local_to_scene, dict):
        basis_columns = local_to_scene.get("basis_columns")
        origin = local_to_scene.get("origin")
        if (
            isinstance(basis_columns, list)
            and len(basis_columns) == 3
            and all(_finite_triple(column) for column in basis_columns)
            and _finite_triple(origin)
        ):
            transform_matches = (
                tuple(tuple(float(value) for value in column) for column in basis_columns)
                == grant.basis_columns
                and tuple(float(value) for value in origin) == grant.origin
            )
    declaration_matches = (
        classification == grant.classification
        and collision.get("shape_policy") == grant.shape_policy
        and layer == grant.layer
        and mask == grant.mask
    )
    if not (binding_matches and scene_matches and transform_matches and declaration_matches):
        errors.append(
            "trusted collision authorization does not cover this exact scene revision,"
            " surface binding, transform, classification, shape policy, layer, and mask"
        )


def _validate_trixel32d_surface_apply(
    packet: dict[str, Any],
    built_validation: Any,
    authority: TrustedApplicationAuthority,
    scene_truth: TrustedSceneTruth,
) -> list[str]:
    errors: list[str] = []

    unknown = sorted(set(packet.keys()) - _ROOT_FIELDS)
    if unknown:
        return [f"application packet contains undeclared keys: {', '.join(unknown)}"]
    missing = sorted(_ROOT_FIELDS - set(packet.keys()))
    if missing:
        return [f"application packet is missing required keys: {', '.join(missing)}"]

    if packet.get("contract") != APPLY_CONTRACT:
        errors.append("contract must be 'trixel32d_surface_apply.v1'")
    if packet.get("packet_type") != APPLY_PACKET_TYPE:
        errors.append("packet_type must be 'trixel32d_surface_apply'")
    if not _canonical_identity(packet.get("apply_id"), "apply_id"):
        errors.append("apply_id must be a canonical t32dapply identity")

    try:
        intent_sha256 = canonical_application_intent_digest(packet)
    except Exception:
        errors.append(
            "application intent could not be canonically serialized; rejecting fail-closed"
        )
    else:
        if intent_sha256 != authority.authorized_intent_sha256:
            errors.append(
                "trusted authority evidence does not cover this exact application intent"
            )

    if _closed_object(packet.get("surface_binding"), "surface_binding", _SURFACE_BINDING_FIELDS, errors):
        _validate_built_binding(packet["surface_binding"], built_validation, errors)
    if _closed_object(packet.get("authorization"), "authorization", _AUTHORIZATION_FIELDS, errors):
        _validate_authorization(packet["authorization"], authority, errors)
    if _closed_object(packet.get("target"), "target", _TARGET_FIELDS, errors):
        _validate_target(packet["target"], scene_truth, errors)
    if _closed_object(packet.get("local_to_scene"), "local_to_scene", _LOCAL_TO_SCENE_FIELDS, errors):
        _validate_local_to_scene(packet["local_to_scene"], errors)
    if _closed_object(packet.get("visibility"), "visibility", _VISIBILITY_FIELDS, errors):
        if packet["visibility"].get("intent") not in _VISIBILITY_INTENTS:
            errors.append("visibility.intent must be exactly VISIBLE or HIDDEN; implicit visibility rejects")
    if _closed_object(packet.get("replacement"), "replacement", _REPLACEMENT_FIELDS, errors):
        _validate_replacement(
            packet["replacement"], packet.get("apply_id"), packet.get("target"), scene_truth, errors
        )
    if _closed_object(packet.get("lifetime"), "lifetime", _LIFETIME_FIELDS, errors):
        _validate_lifetime(packet["lifetime"], authority, errors)

    classification = packet.get("classification")
    if classification not in _CLASSIFICATIONS:
        errors.append(
            "classification must be PRESENTATION_ONLY, STATIC_SPATIAL, or DYNAMIC_SPATIAL"
        )
    if _closed_object(packet.get("collision"), "collision", _COLLISION_FIELDS, errors):
        collision_decision = packet["collision"].get("decision")
        if classification == "PRESENTATION_ONLY" and collision_decision == "GRANTED":
            errors.append("PRESENTATION_ONLY requires collision DENIED")
        _validate_collision(packet["collision"], packet, authority, errors)

    return errors


def validate_trixel32d_surface_apply(
    packet: Any,
    *,
    built_validation: Any,
    authority: Any,
    scene_truth: Any,
) -> ApplySurfaceValidation:
    """Validate one application packet fail-closed with no side effects.

    Acceptance returns a deeply immutable copy of the packet. Rejection returns
    every detected error, first blocking error first, and no packet.
    """
    context_errors: list[str] = []
    if not _validate_trusted_authority(authority, context_errors) or not _validate_trusted_scene_truth(
        scene_truth, context_errors
    ):
        return ApplySurfaceValidation(packet=None, errors=tuple(context_errors))

    if not isinstance(packet, dict):
        return ApplySurfaceValidation(
            packet=None, errors=("application packet must be a dict",)
        )
    try:
        errors = _validate_trixel32d_surface_apply(packet, built_validation, authority, scene_truth)
    except Exception as exc:
        return ApplySurfaceValidation(
            packet=None,
            errors=(f"application validation failed closed: {type(exc).__name__}",),
        )
    if errors:
        return ApplySurfaceValidation(packet=None, errors=tuple(errors))
    return ApplySurfaceValidation(packet=_freeze_json(packet), errors=())


def gate_trixel32d_surface_apply(
    packet: Any,
    *,
    built_validation: Any,
    authority: Any,
    scene_truth: Any,
) -> GateResult:
    """Active EngAInOS gate wrapper."""
    if not isinstance(packet, dict):
        return GateResult(
            "gate_trixel32d_surface_apply",
            "FALSE",
            "Application packet must be a dict",
        )
    claims_contract = packet.get("contract") == APPLY_CONTRACT
    claims_packet_type = packet.get("packet_type") == APPLY_PACKET_TYPE
    if not claims_contract and not claims_packet_type:
        return GateResult(
            "gate_trixel32d_surface_apply",
            "SKIPPED",
            "Packet claims neither the trixel32d surface apply contract nor its packet type",
        )
    validation = validate_trixel32d_surface_apply(
        packet,
        built_validation=built_validation,
        authority=authority,
        scene_truth=scene_truth,
    )
    if not validation.accepted:
        first = validation.errors[0] if validation.errors else "unknown rejection"
        return GateResult(
            "gate_trixel32d_surface_apply",
            "FALSE",
            f"Application validation failed: {first} (total errors: {len(validation.errors)})",
        )
    return GateResult(
        "gate_trixel32d_surface_apply",
        "TRUE",
        "Trixel 3.2D surface application authorization is valid and exactly bound",
    )
