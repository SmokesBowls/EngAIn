#!/usr/bin/env python3
"""Export the checksum-locked apply-authorization artifact (TRIXEL32D_APPLY_AUTHORIZATION_EXPORT_V1).

Parametrized production exporter (roadmap Ticket A). Runs the unchanged
trixel32d_surface_apply.v1 gate live against a caller-declared payload and,
only on gate TRUE, exports one canonical artifact carrying the accepted
apply packet, the gate result, the authorized intent digest, the trusted
authority evidence, and the declared scene truth read from the
authority-owned TRIXEL32D_SCENE_TRUTH_V1.json artifact. The artifact is the
sole application authority for the isolated Godot apply executor — never a
renderer-side consume report. Collision in the authorized packet is
DENIED/NONE. Passive: writes the artifact and nothing else.

Payload path, expected SHA-256, trusted request path, declared target, and
transform origin are validated inputs, not hardcoded fixture imports — this
module has no dependency on the test suite. build_artifact() called with no
arguments reproduces the original accepted grass complete-edge export byte
for byte (SHA-256 5467c9c6d9e05aca564a9dbd042af62eb4893b87234c91f1d5f32b44b5fd039f).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tier1.engainos.gates.gate_trixel32d_handshake import (
    validate_trixel32d_surface_built_bytes,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    TrustedApplicationAuthority,
    TrustedSceneTruth,
    canonical_application_intent_digest,
    gate_trixel32d_surface_apply,
)

ARTIFACT_CONTRACT = "engainos.trixel32d_apply_authorization.v1"
FIXTURES_DIR = ROOT / "tier1" / "engainos" / "tests" / "fixtures"
SCENE_TRUTH_PATH = ROOT / "tier1" / "engainos" / "authority" / "TRIXEL32D_SCENE_TRUTH_V1.json"
AUTHORITY_DECISIONS_PATH = (
    ROOT
    / "tier1"
    / "engainos"
    / "authority"
    / "TRIXEL32D_TICKET_A_APPLICATION_DECISIONS_V1.json"
)
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Declared authority identity: the same actor/decision evidence proven for
# the first accepted authorization. Not test-only data — this is the
# production authority envelope for every export until a real EngAInOS
# authority-issuance path exists.
DECISION_ID = "engainos-decision-3x2-first-proof"
ACTOR_ID = "actor-human-root-001"
AUTHORITY_REVISION = "authority-rev-7"
SESSION_ID = "session-2026-07-18-proof"
AP_RULE_IDS = ("ap-rule-apply-001",)
IDENTITY_BASIS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

SCENE_ID = "scene-first-proof"
SCENE_REVISION = "scene-rev-12"
PARENT_KIND = "RUNTIME_CONTAINER"
PARENT_ID = "container-terrain-proof"

# Defaults reproduce the original accepted grass complete-edge export
# exactly: build_artifact() with no arguments must be byte-identical to the
# committed artifact.
GRASS_PAYLOAD_PATH = FIXTURES_DIR / "trixel32d_surface_built_texel_complete_edge.json"
GRASS_REQUEST_PATH = FIXTURES_DIR / "trixel32d_request_texel_complete_edge.json"
GRASS_EXPECTED_SHA256 = "49396807a2d119328608b44203c0a8aae20cfe5ac0028e880676ac538bb7745b"
GRASS_REQUEST_ID = "t32dreq_001241884d12dff0"
GRASS_SURFACE_ID = "t32dsurface_cd7eee9d7877c948"
GRASS_APPLY_ID = "t32dapply_00c0ffee00c0ffee"
GRASS_TICKET_A_DECISION_ID = "engainos-ticket-a-grass-application-v1"
GRASS_SLOT_ID = "slot-surface-3x2"
GRASS_ORIGIN = [2.0, 0.5, -1.0]

# Second declared tile (roadmap Ticket A). Origin offset well clear of the
# grass slab's ~16-unit footprint so both apply visibly apart.
STONE_PAYLOAD_PATH = FIXTURES_DIR / "trixel32d_surface_built_texel_stone_complete_edge.json"
STONE_REQUEST_PATH = FIXTURES_DIR / "trixel32d_request_texel_stone_complete_edge.json"
STONE_EXPECTED_SHA256 = "939c10c2a2de957b49c9a042b74c6e2aeac75ff03bbe037200cd35794962c7ce"
STONE_REQUEST_ID = "t32dreq_47840250a37b492f"
STONE_SURFACE_ID = "t32dsurface_e33b7a00b15a4b68"
STONE_APPLY_ID = "t32dapply_939c10c2a2de957b"
STONE_TICKET_A_DECISION_ID = "engainos-ticket-a-stone-application-v1"
STONE_SLOT_ID = "slot-surface-stone-16x16"
STONE_ORIGIN = [22.0, 0.5, -1.0]

EXPORT_ROOT = ROOT / "runtime" / "trixel32d_apply_authorizations"


# The exact scene truth the original grass export was authorized under —
# preserved inline so build_artifact() with no arguments keeps reproducing
# the frozen historical byte lock even though the authority-owned scene
# truth artifact below has since grown a second declared slot. The already
# accepted artifact on disk stays byte-untouched either way; this is what
# keeps a *rebuild* of it byte-identical too.
_HISTORICAL_GRASS_SCENE_TRUTH = TrustedSceneTruth(
    scene_id=SCENE_ID,
    active_scene_revision=SCENE_REVISION,
    declared_targets=frozenset({
        (PARENT_KIND, PARENT_ID, GRASS_SLOT_ID),
        (PARENT_KIND, PARENT_ID, "slot-occupied"),
        ("SCENE_ROOT", "scene-first-proof-root", "slot-root-decor"),
    }),
    slot_occupancy={"slot-occupied": "t32dapply_feedfacefeedface"},
)


def _strict_json_object_bytes(payload_bytes: bytes, label: str) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"nonstandard JSON constant {value!r}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        data = json.loads(
            payload_bytes.decode("utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{label} root must be an object")
    return data


def _scene_truth_from_bytes(payload_bytes: bytes) -> TrustedSceneTruth:
    data = _strict_json_object_bytes(payload_bytes, "scene truth artifact")
    if data.get("contract") != "engainos.trixel32d_scene_truth.v1":
        raise SystemExit("scene truth artifact does not carry the expected contract")
    try:
        return TrustedSceneTruth(
            scene_id=data["scene_id"],
            active_scene_revision=data["active_scene_revision"],
            declared_targets=frozenset(tuple(target) for target in data["declared_targets"]),
            slot_occupancy=dict(data["slot_occupancy"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"scene truth artifact has invalid structure: {exc}") from exc


def _read_scene_truth(scene_truth_path: Path) -> TrustedSceneTruth:
    return _scene_truth_from_bytes(scene_truth_path.read_bytes())


def _read_ticket_a_decision(
    decision_id: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    authority_path = AUTHORITY_DECISIONS_PATH.resolve(strict=True)
    authority_bytes = authority_path.read_bytes()
    data = _strict_json_object_bytes(authority_bytes, "authority decision artifact")
    if data.get("contract") != "engainos.trixel32d_application_decisions.v1":
        raise SystemExit("authority decision artifact does not carry the expected contract")
    if data.get("issued_by") != "engainos":
        raise SystemExit("authority decision artifact was not issued by EngAInOS")
    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise SystemExit("authority decision artifact decisions must be an array")
    matches = [decision for decision in decisions if isinstance(decision, dict) and decision.get("decision_id") == decision_id]
    if len(matches) != 1:
        raise SystemExit("authority decision_id must resolve exactly once")
    decision = matches[0]
    if decision.get("decision") != "AUTHORIZED":
        raise SystemExit("authority decision is not AUTHORIZED")
    binding = {
        "contract": data["contract"],
        "repository_path": authority_path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(authority_bytes).hexdigest(),
    }
    return decision, binding


def _authority_from_decision(decision: dict[str, Any]) -> TrustedApplicationAuthority:
    if decision.get("collision_grant") is not None:
        raise SystemExit("Ticket A authority decision must not grant collision")
    try:
        return TrustedApplicationAuthority(
            decision_id=decision["decision_id"],
            actor_id=decision["actor_id"],
            actor_authority_tier=decision["actor_authority_tier"],
            reality_mode=decision["reality_mode"],
            authority_revision=decision["authority_revision"],
            runtime_session_id=decision["runtime_session_id"],
            authorized_intent_sha256=decision["authorized_intent_sha256"],
            ap_rule_ids=tuple(decision["ap_rule_ids"]),
            ap_rule_required=decision["ap_rule_required"],
            canonical_persistence_authorized=decision["canonical_persistence_authorized"],
            collision_grant=None,
        )
    except (KeyError, TypeError) as exc:
        raise SystemExit(f"authority decision has invalid structure: {exc}") from exc


def _authority_for(packet: dict[str, Any]) -> TrustedApplicationAuthority:
    return TrustedApplicationAuthority(
        decision_id=DECISION_ID,
        actor_id=ACTOR_ID,
        actor_authority_tier=3,
        reality_mode="DRAFT",
        authority_revision=AUTHORITY_REVISION,
        runtime_session_id=SESSION_ID,
        authorized_intent_sha256=canonical_application_intent_digest(packet),
        ap_rule_ids=AP_RULE_IDS,
        ap_rule_required=True,
        canonical_persistence_authorized=False,
        collision_grant=None,
    )


def _build_apply_packet(
    *,
    apply_id: str,
    request_id: str,
    surface_id: str,
    built_response_sha256: str,
    application_slot_id: str,
    origin: list[float],
    authority_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision_id = (
        authority_decision["decision_id"] if authority_decision is not None else DECISION_ID
    )
    actor_id = authority_decision["actor_id"] if authority_decision is not None else ACTOR_ID
    actor_authority_tier = (
        authority_decision["actor_authority_tier"] if authority_decision is not None else 3
    )
    reality_mode = (
        authority_decision["reality_mode"] if authority_decision is not None else "DRAFT"
    )
    authority_revision = (
        authority_decision["authority_revision"]
        if authority_decision is not None
        else AUTHORITY_REVISION
    )
    runtime_session_id = (
        authority_decision["runtime_session_id"]
        if authority_decision is not None
        else SESSION_ID
    )
    ap_rule_ids = (
        list(authority_decision["ap_rule_ids"])
        if authority_decision is not None
        else list(AP_RULE_IDS)
    )
    return {
        "contract": "trixel32d_surface_apply.v1",
        "packet_type": "trixel32d_surface_apply",
        "apply_id": apply_id,
        "surface_binding": {
            "built_contract": "trixel32d_surface_built.v1",
            "request_id": request_id,
            "surface_id": surface_id,
            "built_response_sha256": built_response_sha256,
        },
        "authorization": {
            "decision": "AUTHORIZED",
            "decision_id": decision_id,
            "issued_by": "engainos",
            "actor_id": actor_id,
            "actor_authority_tier": actor_authority_tier,
            "reality_mode": reality_mode,
            "authority_revision": authority_revision,
            "runtime_session_id": runtime_session_id,
            "ap_rule_ids": ap_rule_ids,
        },
        "target": {
            "scene_id": SCENE_ID,
            "scene_revision": SCENE_REVISION,
            "parent_kind": PARENT_KIND,
            "parent_id": PARENT_ID,
            "application_slot_id": application_slot_id,
        },
        "local_to_scene": {
            "space": "SCENE_LOCAL_Y_UP",
            "basis_columns": copy.deepcopy(IDENTITY_BASIS),
            "origin": list(origin),
        },
        "visibility": {"intent": "VISIBLE"},
        "replacement": {"mode": "CREATE_ONLY", "replaces_apply_id": None},
        "lifetime": {"mode": "SCENE_BOUND"},
        "classification": "PRESENTATION_ONLY",
        "collision": {
            "decision": "DENIED",
            "authorized_by_decision_id": decision_id,
            "shape_policy": "NONE",
            "layer": 0,
            "mask": 0,
        },
    }


def build_artifact(
    *,
    payload_path: Path | str | None = None,
    request_path: Path | str | None = None,
    expected_payload_sha256: str | None = None,
    apply_id: str | None = None,
    request_id: str | None = None,
    surface_id: str | None = None,
    application_slot_id: str | None = None,
    origin: list[float] | None = None,
    scene_truth_path: Path | str | None = None,
    authority_decision_id: str | None = None,
) -> tuple[dict, bytes]:
    payload_path = Path(payload_path) if payload_path is not None else GRASS_PAYLOAD_PATH
    request_path = Path(request_path) if request_path is not None else GRASS_REQUEST_PATH
    expected_payload_sha256 = expected_payload_sha256 or GRASS_EXPECTED_SHA256
    apply_id = apply_id or GRASS_APPLY_ID
    request_id = request_id or GRASS_REQUEST_ID
    surface_id = surface_id or GRASS_SURFACE_ID
    application_slot_id = application_slot_id or GRASS_SLOT_ID
    origin = list(origin) if origin is not None else list(GRASS_ORIGIN)

    if authority_decision_id is None:
        historical_inputs_match = (
            payload_path.resolve() == GRASS_PAYLOAD_PATH.resolve()
            and request_path.resolve() == GRASS_REQUEST_PATH.resolve()
            and expected_payload_sha256 == GRASS_EXPECTED_SHA256
            and apply_id == GRASS_APPLY_ID
            and request_id == GRASS_REQUEST_ID
            and surface_id == GRASS_SURFACE_ID
            and application_slot_id == GRASS_SLOT_ID
            and origin == GRASS_ORIGIN
            and scene_truth_path is None
        )
        if not historical_inputs_match:
            raise SystemExit(
                "historical rebuild path may reproduce only the exact frozen grass authorization"
            )

    if not _SHA256_PATTERN.fullmatch(expected_payload_sha256):
        raise SystemExit("expected_payload_sha256 must be 64 lowercase hexadecimal characters")

    payload_bytes = payload_path.read_bytes()
    trusted_request = json.loads(request_path.read_text(encoding="utf-8"))

    authority_decision: dict[str, Any] | None = None
    authority_decision_binding: dict[str, str] | None = None
    if authority_decision_id is not None:
        authority_decision, authority_decision_binding = _read_ticket_a_decision(
            authority_decision_id
        )

    packet = _build_apply_packet(
        apply_id=apply_id,
        request_id=request_id,
        surface_id=surface_id,
        built_response_sha256=expected_payload_sha256,
        application_slot_id=application_slot_id,
        origin=origin,
        authority_decision=authority_decision,
    )
    intent_digest = canonical_application_intent_digest(packet)
    if (
        authority_decision is not None
        and authority_decision.get("authorized_intent_sha256") != intent_digest
    ):
        raise SystemExit(
            "preissued authority decision does not cover the exact application intent"
        )

    validation = validate_trixel32d_surface_built_bytes(
        payload_bytes,
        trusted_request,
        expected_response_sha256=expected_payload_sha256,
    )
    assert validation.accepted, validation.errors

    authority = (
        _authority_from_decision(authority_decision)
        if authority_decision is not None
        else _authority_for(packet)
    )
    scene_truth_binding: dict[str, str] | None = None
    if scene_truth_path is not None:
        if authority_decision is None:
            raise SystemExit(
                "Ticket A authorization requires independently preissued authority evidence"
            )
        requested_scene_truth_path = Path(scene_truth_path).resolve(strict=True)
        authority_scene_truth_path = SCENE_TRUTH_PATH.resolve(strict=True)
        if requested_scene_truth_path != authority_scene_truth_path:
            raise SystemExit(
                "Ticket A authorization must use the authority-owned scene truth artifact"
            )
        scene_truth_bytes = requested_scene_truth_path.read_bytes()
        scene_truth = _scene_truth_from_bytes(scene_truth_bytes)
        scene_truth_binding = {
            "contract": "engainos.trixel32d_scene_truth.v1",
            "repository_path": requested_scene_truth_path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(scene_truth_bytes).hexdigest(),
        }
    else:
        scene_truth = _HISTORICAL_GRASS_SCENE_TRUTH

    outcome = gate_trixel32d_surface_apply(
        packet,
        built_validation=validation,
        authority=authority,
        scene_truth=scene_truth,
    )
    if not outcome.is_true():
        raise SystemExit(f"apply gate refused: {outcome.message}")

    artifact = {
        "contract": ARTIFACT_CONTRACT,
        "packet_type": "trixel32d_apply_authorization",
        "apply_packet": packet,
        "gate_result": {
            "gate_name": outcome.gate_name,
            "passed": outcome.passed,
            "message": outcome.message,
        },
        "authorized_intent_sha256": intent_digest,
        "authority": {
            "decision_id": authority.decision_id,
            "actor_id": authority.actor_id,
            "actor_authority_tier": authority.actor_authority_tier,
            "reality_mode": authority.reality_mode,
            "authority_revision": authority.authority_revision,
            "runtime_session_id": authority.runtime_session_id,
            "ap_rule_ids": list(authority.ap_rule_ids),
        },
        "scene_truth": {
            "scene_id": scene_truth.scene_id,
            "active_scene_revision": scene_truth.active_scene_revision,
            "declared_targets": sorted(list(t) for t in scene_truth.declared_targets),
            "slot_occupancy": dict(scene_truth.slot_occupancy),
        },
        "payload_binding": dict(packet["surface_binding"]),
        "collision_authorized": False,
        "godot_runtime_scope": "ISOLATED_APPLY_EXECUTOR_PROOF_ONLY",
    }
    if scene_truth_binding is not None:
        artifact["scene_truth_binding"] = scene_truth_binding
    if authority_decision_binding is not None:
        artifact["authority_decision_binding"] = authority_decision_binding
    artifact_bytes = json.dumps(artifact, indent=1, sort_keys=True).encode("utf-8")
    return artifact, artifact_bytes


def build_ticket_a_artifact(tile: str) -> tuple[dict, bytes]:
    """Build one Ticket A authorization through the common authority path."""
    configs = {
        "grass": {
            "payload_path": GRASS_PAYLOAD_PATH,
            "request_path": GRASS_REQUEST_PATH,
            "expected_payload_sha256": GRASS_EXPECTED_SHA256,
            "apply_id": GRASS_APPLY_ID,
            "request_id": GRASS_REQUEST_ID,
            "surface_id": GRASS_SURFACE_ID,
            "application_slot_id": GRASS_SLOT_ID,
            "origin": GRASS_ORIGIN,
            "authority_decision_id": GRASS_TICKET_A_DECISION_ID,
        },
        "stone": {
            "payload_path": STONE_PAYLOAD_PATH,
            "request_path": STONE_REQUEST_PATH,
            "expected_payload_sha256": STONE_EXPECTED_SHA256,
            "apply_id": STONE_APPLY_ID,
            "request_id": STONE_REQUEST_ID,
            "surface_id": STONE_SURFACE_ID,
            "application_slot_id": STONE_SLOT_ID,
            "origin": STONE_ORIGIN,
            "authority_decision_id": STONE_TICKET_A_DECISION_ID,
        },
    }
    if tile not in configs:
        raise SystemExit(f"unknown Ticket A tile: {tile!r}; expected 'grass' or 'stone'")
    return build_artifact(**configs[tile], scene_truth_path=SCENE_TRUTH_PATH)


# Module-level defaults for the occupied-slot check on the original
# (grass) export path — unchanged from the pre-parametrization version so
# every existing monkeypatch-based test keeps working exactly as before.
EXPORT_DIR = EXPORT_ROOT / ("t32ddrop_" + GRASS_EXPECTED_SHA256[:16])
ARTIFACT_PATH = EXPORT_DIR / "TRIXEL32D_SURFACE_APPLY_AUTHORIZATION_V1.json"


def main() -> int:
    tag = "[trixel32d_apply_authorization_export]"
    if ARTIFACT_PATH.exists():
        print(f"{tag}[SLOT_OCCUPIED] {ARTIFACT_PATH}")
        return 1
    _, artifact_bytes = build_artifact()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_bytes(artifact_bytes)
    print(f"{tag}[ARTIFACT_WRITTEN] {ARTIFACT_PATH}")
    print(f"{tag}[ARTIFACT_SHA256] {hashlib.sha256(artifact_bytes).hexdigest()}")
    print(f"{tag}[GATE] TRUE | collision DENIED/NONE | scope ISOLATED_APPLY_EXECUTOR_PROOF_ONLY")
    return 0


TICKET_A_ARTIFACT_FILENAME = (
    "TRIXEL32D_SURFACE_APPLY_AUTHORIZATION_TICKET_A_AUTHORITY_BOUND_V1.json"
)


def ticket_a_artifact_path(tile: str) -> Path:
    payload_sha256 = {
        "grass": GRASS_EXPECTED_SHA256,
        "stone": STONE_EXPECTED_SHA256,
    }.get(tile)
    if payload_sha256 is None:
        raise SystemExit(f"unknown Ticket A tile: {tile!r}; expected 'grass' or 'stone'")
    return EXPORT_ROOT / ("t32ddrop_" + payload_sha256[:16]) / TICKET_A_ARTIFACT_FILENAME


def export_ticket_a(tile: str) -> int:
    """Write one occupied-once Ticket A authorization from the common exporter."""
    tag = f"[trixel32d_apply_authorization_export_ticket_a_{tile}]"
    artifact_path = ticket_a_artifact_path(tile)
    if artifact_path.exists():
        print(f"{tag}[SLOT_OCCUPIED] {artifact_path}")
        return 1
    _, artifact_bytes = build_ticket_a_artifact(tile)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(artifact_bytes)
    print(f"{tag}[ARTIFACT_WRITTEN] {artifact_path}")
    print(f"{tag}[ARTIFACT_SHA256] {hashlib.sha256(artifact_bytes).hexdigest()}")
    print(f"{tag}[GATE] TRUE | collision DENIED/NONE | scope ISOLATED_APPLY_EXECUTOR_PROOF_ONLY")
    return 0


def main_stone() -> int:
    """Backward-compatible alias for the Ticket A stone export."""
    return export_ticket_a("stone")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "ticket-a":
        raise SystemExit(export_ticket_a(sys.argv[2]))
    if len(sys.argv) > 1 and sys.argv[1] == "stone":
        raise SystemExit(main_stone())
    raise SystemExit(main())
