# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_governance_rejection_proof.py

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"


from typing import Any

from engain_control.gate_result import GateResult
from engainos.gates.gate_no_simulation_execution import gate_no_simulation_execution
from engainos.gates.gate_no_asset_production import gate_no_asset_production
from engainos.gates.gate_no_presentation_authority import gate_no_presentation_authority
from engainos.gates.gate_acceptance_rule import gate_acceptance_rule_enforced

VALID_BASE_PACKET: dict[str, Any] = {
    "contract": "engainos.governance_packet.v1",
    "source": "engainos",
    "authority_tier": 1,
    "authority_lane": "governance",
    "scene_id": "scene.030_ummade_army",
    "decision_id": "decision_001",
    "decision_type": "runtime_acceptance",
    "acceptance_decision": "accepted",
    "declared_scene_truth": {
        "scene_id": "scene.030_ummade_army",
        "status": "declared"
    },
    "declared_entity_truth": [
        {
            "entity_id": "mika_01",
            "status": "declared"
        }
    ],
    "validated_packets": [
        {
            "source": "godotsim",
            "contract": "godotsim.spatial_sim_packet.v1",
            "result": "accepted"
        }
    ],
    "ap_validation": {
        "result": "passed",
        "gate_count": 3
    }
}

BAD_SIMULATION_PACKET: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "position": [0.0, 0.0, 0.0],
}

BAD_ASSET_PACKET: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "asset_id": "mesh_001",
}

BAD_PRESENTATION_PACKET: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "render": True,
}

BAD_ACCEPTANCE_PACKET: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "ap_validation": {
        "result": "failed",
        "gate_count": 3
    }
}

def gate_simulation_rejection_path(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet with position key is rejected by no_simulation_execution."""
    result = gate_no_simulation_execution(BAD_SIMULATION_PACKET)

    if result.passed == "FALSE":
        return GateResult(
            "gate_simulation_rejection_path",
            "TRUE",
            "Packet with position was correctly rejected",
        )

    return GateResult(
        "gate_simulation_rejection_path",
        "FALSE",
        f"Packet with position should have been rejected but got {result.passed}: {result.message}",
    )

def gate_asset_rejection_path(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet with asset_id key is rejected by no_asset_production."""
    result = gate_no_asset_production(BAD_ASSET_PACKET)

    if result.passed == "FALSE":
        return GateResult(
            "gate_asset_rejection_path",
            "TRUE",
            "Packet with asset_id was correctly rejected",
        )

    return GateResult(
        "gate_asset_rejection_path",
        "FALSE",
        f"Packet with asset_id should have been rejected but got {result.passed}: {result.message}",
    )

def gate_presentation_rejection_path(packet: dict[str, Any]) -> GateResult:
    """PROOF: Packet with render key is rejected by no_presentation_authority."""
    result = gate_no_presentation_authority(BAD_PRESENTATION_PACKET)

    if result.passed == "FALSE":
        return GateResult(
            "gate_presentation_rejection_path",
            "TRUE",
            "Packet with render was correctly rejected",
        )

    return GateResult(
        "gate_presentation_rejection_path",
        "FALSE",
        f"Packet with render should have been rejected but got {result.passed}: {result.message}",
    )

def gate_acceptance_rejection_path(packet: dict[str, Any]) -> GateResult:
    """PROOF: Accepted packet with ap_validation.result='failed' is rejected."""
    result = gate_acceptance_rule_enforced(BAD_ACCEPTANCE_PACKET)

    if result.passed == "FALSE":
        return GateResult(
            "gate_acceptance_rejection_path",
            "TRUE",
            "Accepted packet with failed AP validation was correctly rejected",
        )

    return GateResult(
        "gate_acceptance_rejection_path",
        "FALSE",
        f"Accepted packet with failed AP validation should have been rejected but got {result.passed}: {result.message}",
    )
