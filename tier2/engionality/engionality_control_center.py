# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/engionality_control_center.py

from __future__ import annotations

from typing import Any

from engain_control.gate_print import run_script_gates

from tier2.engionality.gates import gate_affect_state_valid
from tier2.engionality.gates import gate_intensity_bounds
from tier2.engionality.gates import gate_no_lane_theft_in_packet
from tier2.engionality.gates import gate_relationship_deltas_valid_if_present
from tier2.engionality.gates import gate_required_fields
from tier2.engionality.gates import gate_scene_mood_valid_if_present


MINIMAL_TEST_PACKET: dict[str, Any] = {
    "contract": "engionality.affect_packet.v1",
    "source": "engionality",
    "authority_tier": 2,
    "scene_id": "scene_001",
    "tick": 1042,
    "entities": [
        {
            "entity_id": "mika_01",
            "affect_state": "fear",
            "intensity": 0.72,
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
                gate_required_fields.gate_scene_and_time_present,
                gate_required_fields.gate_entities_array_present,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="intensity_bounds.py",
            packet=packet_to_test,
            gates=[
                gate_intensity_bounds.gate_entity_intensity_bounds,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="affect_state_valid.py",
            packet=packet_to_test,
            gates=[
                gate_affect_state_valid.gate_affect_state_present_and_valid,
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
            script_name="relationship_deltas_valid_if_present.py",
            packet=packet_to_test,
            gates=[
                gate_relationship_deltas_valid_if_present.gate_relationship_deltas_valid_if_present,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="scene_mood_valid_if_present.py",
            packet=packet_to_test,
            gates=[
                gate_scene_mood_valid_if_present.gate_scene_mood_valid_if_present,
            ],
        )
    )

    system_passed = all(script_results)

    print(f"ENGIONALITY_CONTROL_CENTER RESULT: {'TRUE' if system_passed else 'FALSE'}")

    return system_passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)