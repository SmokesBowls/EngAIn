#!/usr/bin/env python3
"""Export the checksum-locked apply-authorization artifact (TRIXEL32D_APPLY_AUTHORIZATION_EXPORT_V1).

Runs the unchanged trixel32d_surface_apply.v1 gate live against the
intake-validated complete-edge payload and, only on gate TRUE, exports one
canonical artifact carrying the accepted apply packet, the gate result, the
authorized intent digest, the trusted authority evidence, and the declared
scene truth. The artifact is the sole application authority for the isolated
Godot apply executor — never a renderer-side consume report. Collision in
the authorized packet is DENIED/NONE. Passive: writes the artifact and
nothing else.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tier1.engainos.gates.gate_trixel32d_handshake import (
    validate_trixel32d_surface_built_bytes,
)
from tier1.engainos.gates.gate_trixel32d_surface_apply import (
    canonical_application_intent_digest,
    gate_trixel32d_surface_apply,
)
from tier1.engainos.tests.test_trixel32d_complete_edge_transport import (
    COMPLETE_EDGE_PAYLOAD,
    COMPLETE_EDGE_REQUEST,
    COMPLETE_EDGE_SHA256,
    complete_edge_apply_packet,
)
from tier1.engainos.tests.test_trixel32d_surface_apply import (
    authority_for,
    canonical_scene_truth,
)

ARTIFACT_CONTRACT = "engainos.trixel32d_apply_authorization.v1"
AUTHORIZED_ORIGIN = [2.0, 0.5, -1.0]
EXPORT_DIR = ROOT / "runtime" / "trixel32d_apply_authorizations" / ("t32ddrop_" + COMPLETE_EDGE_SHA256[:16])
ARTIFACT_PATH = EXPORT_DIR / "TRIXEL32D_SURFACE_APPLY_AUTHORIZATION_V1.json"


def build_artifact() -> tuple[dict, bytes]:
    packet = complete_edge_apply_packet()
    packet["local_to_scene"]["origin"] = list(AUTHORIZED_ORIGIN)

    validation = validate_trixel32d_surface_built_bytes(
        COMPLETE_EDGE_PAYLOAD,
        COMPLETE_EDGE_REQUEST,
        expected_response_sha256=COMPLETE_EDGE_SHA256,
    )
    assert validation.accepted, validation.errors

    authority = authority_for(packet)
    scene_truth = canonical_scene_truth()
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
        "authorized_intent_sha256": canonical_application_intent_digest(packet),
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
    artifact_bytes = json.dumps(artifact, indent=1, sort_keys=True).encode("utf-8")
    return artifact, artifact_bytes


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


if __name__ == "__main__":
    raise SystemExit(main())
