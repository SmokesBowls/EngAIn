# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/godotsim_control_center.py

from __future__ import annotations

from typing import Any

from engain_control.gate_print import run_script_gates

from godotsim.gates import gate_required_fields
from godotsim.gates import gate_entity_structure
from godotsim.gates import gate_optional_fields_valid
from godotsim.gates import gate_no_lane_theft_in_packet
from godotsim.gates import gate_no_narrative_meaning
from godotsim.gates import gate_no_auto_entity_declaration


MINIMAL_TEST_PACKET: dict[str, Any] = {
    "contract": "godotsim.spatial_sim_packet.v1",
    "source": "godotsim",
    "authority_tier": 2,
    "scene_id": "scene.030_ummade_army",
    "sim_tick": 1042,
    "entities": [
        {
            "entity_id": "mika_01",
            "position": [12.5, 0.0, 8.3],
            "collision_role": "kinematic",
        }
    ],
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
                gate_required_fields.gate_scene_and_tick_present,
                gate_required_fields.gate_entities_array_present,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="entity_structure.py",
            packet=packet_to_test,
            gates=[
                gate_entity_structure.gate_entity_id_present,
                gate_entity_structure.gate_position_present_and_valid,
                gate_entity_structure.gate_collision_role_valid,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="optional_fields_valid.py",
            packet=packet_to_test,
            gates=[
                gate_optional_fields_valid.gate_rotation_valid_if_present,
                gate_optional_fields_valid.gate_velocity_valid_if_present,
                gate_optional_fields_valid.gate_grounded_valid_if_present,
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
            script_name="no_narrative_meaning.py",
            packet=packet_to_test,
            gates=[
                gate_no_narrative_meaning.gate_no_narrative_meaning_in_packet,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_auto_entity_declaration.py",
            packet=packet_to_test,
            gates=[
                gate_no_auto_entity_declaration.gate_no_auto_entity_declaration,
            ],
        )
    )

    system_passed = all(script_results)

    print(f"GODOTSIM_CONTROL_CENTER RESULT: {'TRUE' if system_passed else 'FALSE'}")

    return system_passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)