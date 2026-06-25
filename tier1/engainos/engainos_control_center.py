# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/engainos_control_center.py

from __future__ import annotations

from typing import Any

from engain_control.gate_print import run_script_gates

from tier1.engainos.gates import gate_packet_identity
from tier1.engainos.gates import gate_acceptance_rule
from tier1.engainos.gates import gate_declared_truth_shape
from tier1.engainos.gates import gate_validated_packets_shape
from tier1.engainos.gates import gate_no_asset_production
from tier1.engainos.gates import gate_no_simulation_execution
from tier1.engainos.gates import gate_no_presentation_authority
from tier1.engainos.gates import gate_no_lane_theft_in_packet
from tier1.engainos.gates import gate_governance_rejection_proof


MINIMAL_TEST_PACKET: dict[str, Any] = {
    "contract": "tier1.engainos.governance_packet.v1",
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
            "source": "mrlore",
            "contract": "mrlore.canon_review_packet.v1",
            "result": "accepted"
        },
        {
            "source": "godotsim",
            "contract": "godotsim.spatial_sim_packet.v1",
            "result": "accepted"
        },
        {
            "source": "engionality",
            "contract": "engionality.affect_packet.v1",
            "result": "accepted"
        }
    ],
    "ap_validation": {
        "result": "passed",
        "gate_count": 3
    }
}


def run(packet: dict[str, Any] | None = None) -> bool:
    packet_to_test = packet if packet is not None else MINIMAL_TEST_PACKET

    script_results: list[bool] = []

    script_results.append(
        run_script_gates(
            script_name="packet_identity.py",
            packet=packet_to_test,
            gates=[
                gate_packet_identity.gate_packet_identity,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="acceptance_rule.py",
            packet=packet_to_test,
            gates=[
                gate_acceptance_rule.gate_acceptance_rule_enforced,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="declared_truth_shape.py",
            packet=packet_to_test,
            gates=[
                gate_declared_truth_shape.gate_declared_truth_shape,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="validated_packets_shape.py",
            packet=packet_to_test,
            gates=[
                gate_validated_packets_shape.gate_validated_packets_shape,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_asset_production.py",
            packet=packet_to_test,
            gates=[
                gate_no_asset_production.gate_no_asset_production,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_simulation_execution.py",
            packet=packet_to_test,
            gates=[
                gate_no_simulation_execution.gate_no_simulation_execution,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_presentation_authority.py",
            packet=packet_to_test,
            gates=[
                gate_no_presentation_authority.gate_no_presentation_authority,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_lane_theft_in_packet.py",
            packet=packet_to_test,
            gates=[
                gate_no_lane_theft_in_packet.gate_no_lane_theft_in_packet,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="governance_rejection_proof.py",
            packet=packet_to_test,
            gates=[
                gate_governance_rejection_proof.gate_simulation_rejection_path,
                gate_governance_rejection_proof.gate_asset_rejection_path,
                gate_governance_rejection_proof.gate_presentation_rejection_path,
                gate_governance_rejection_proof.gate_acceptance_rejection_path,
            ],
        )
    )

    system_passed = all(script_results)

    print(f"ENGAINOS_CONTROL_CENTER RESULT: {'TRUE' if system_passed else 'FALSE'}")

    return system_passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)