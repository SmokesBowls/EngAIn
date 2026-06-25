
# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_packet_identity.py

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

from typing import Any

from engain_control.gate_result import GateResult

VALID_DECISION_TYPES = {
    "runtime_acceptance",
    "declared_truth_update",
    "bridge_contract_validation",
    "project_state_update",
}

def gate_packet_identity(packet: dict[str, Any]) -> GateResult:
    if packet.get("contract") != "tier1.engainos.governance_packet.v1":
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "Invalid contract version",
        )

    if packet.get("source") != "engainos":
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "Invalid source",
        )

    if packet.get("authority_tier") != 1:
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "Invalid authority tier",
        )

    if packet.get("authority_lane") != "governance":
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "Invalid authority lane",
        )

    scene_id = packet.get("scene_id")
    if not isinstance(scene_id, str) or not scene_id.strip():
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "scene_id must be a non-empty string",
        )

    decision_id = packet.get("decision_id")
    if not isinstance(decision_id, str) or not decision_id.strip():
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "decision_id must be a non-empty string",
        )

    decision_type = packet.get("decision_type")
    if decision_type not in VALID_DECISION_TYPES:
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            f"Invalid decision_type: {decision_type}",
        )

    return GateResult(
        "gate_packet_identity",
        "TRUE",
        "Packet identity is valid",
    )
