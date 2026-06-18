# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mrlore/mrlore_control_center.py

from __future__ import annotations

from typing import Any

from engain_control.gate_print import run_script_gates

from mrlore.gates import gate_required_fields
from mrlore.gates import gate_enum_values_valid
from mrlore.gates import gate_claims_structure
from mrlore.gates import gate_contradictions_valid_if_present
from mrlore.gates import gate_no_lane_theft_in_packet
from mrlore.gates import gate_no_auto_resolve_attempt
from mrlore.gates import gate_no_vault_path_dependency
from mrlore.gates import gate_contradiction_stop_proof


MINIMAL_TEST_PACKET: dict[str, Any] = {
    "contract": "mrlore.canon_review_packet.v1",
    "source": "mrlore",
    "authority_lane": "canon_review",
    "authority_tier": 3,
    "scene_id": "scene.030_ummade_army",
    "source_text_id": "chapter_or_pass_id",
    "review_status": "human_review_required",
    "canon_status": "unconfirmed",
    "claims": [
        {
            "claim_id": "claim_001",
            "subject": "mika",
            "predicate": "appears_in_scene",
            "object": "scene.030_ummade_army",
            "source_span": {
                "start": 1204,
                "end": 1218,
            },
            "canon_risk": "low",
        }
    ],
    "allowed_to_auto_resolve": False,
    "human_review_required": True,
}


def run(packet: dict[str, Any] | None = None) -> bool:
    packet_to_test = packet if packet is not None else MINIMAL_TEST_PACKET

    script_results: list[bool] = []

    script_results.append(
        run_script_gates(
            script_name="required_fields.py",
            packet=packet_to_test,
            gates=[
                gate_required_fields.gate_contract_and_source_valid,
                gate_required_fields.gate_scene_and_source_present,
                gate_required_fields.gate_claims_array_present,
                gate_required_fields.gate_human_review_required_present,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="enum_values_valid.py",
            packet=packet_to_test,
            gates=[
                gate_enum_values_valid.gate_review_status_valid,
                gate_enum_values_valid.gate_canon_status_valid,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="claims_structure.py",
            packet=packet_to_test,
            gates=[
                gate_claims_structure.gate_claims_structure_valid,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="contradictions_valid_if_present.py",
            packet=packet_to_test,
            gates=[
                gate_contradictions_valid_if_present.gate_contradictions_valid_if_present,
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
            script_name="no_auto_resolve_attempt.py",
            packet=packet_to_test,
            gates=[
                gate_no_auto_resolve_attempt.gate_no_auto_resolve_attempt,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_vault_path_dependency.py",
            packet=packet_to_test,
            gates=[
                gate_no_vault_path_dependency.gate_no_vault_path_dependency,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="contradiction_stop_proof.py",
            packet=packet_to_test,
            gates=[
                gate_contradiction_stop_proof.gate_medium_contradiction_positive_path,
                gate_contradiction_stop_proof.gate_medium_contradiction_rejection_path,
                gate_contradiction_stop_proof.gate_medium_contradiction_review_status_rejection,
            ],
        )
    )

    system_passed = all(script_results)

    print(f"MRLORE_CONTROL_CENTER RESULT: {'TRUE' if system_passed else 'FALSE'}")

    return system_passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)