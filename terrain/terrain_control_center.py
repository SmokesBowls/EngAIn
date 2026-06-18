# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/terrain_control_center.py

from __future__ import annotations

from typing import Any

from engain_control.gate_print import run_script_gates

from terrain.gates import gate_imports
from terrain.gates import gate_thresholds_exist
from terrain.gates import gate_world_field_boundary
from terrain.gates import gate_adapter_boundary
from terrain.gates import gate_dirty_chunk_or_delta_shape
from terrain.gates import gate_no_authority_overreach
from terrain.gates import gate_terrain_adapter_rejection_proof


MINIMAL_TEST_PACKET: dict[str, Any] = {
    "terrain_intent": {
        "profile": "coastal_transition",
        "thresholds": {
            "deep_water": {"min": 0.00, "max": 0.10},
        },
        "region_elevation_targets": {
            "coastal_margin": 0.26,
        },
    }
}


def run(packet: dict[str, Any] | None = None) -> bool:
    packet_to_test = packet if packet is not None else MINIMAL_TEST_PACKET

    script_results: list[bool] = []

    script_results.append(
        run_script_gates(
            script_name="imports.py",
            packet=packet_to_test,
            gates=[
                gate_imports.gate_imports,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="thresholds_exist.py",
            packet=packet_to_test,
            gates=[
                gate_thresholds_exist.gate_thresholds_exist,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="world_field_boundary.py",
            packet=packet_to_test,
            gates=[
                gate_world_field_boundary.gate_world_field_boundary,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="adapter_boundary.py",
            packet=packet_to_test,
            gates=[
                gate_adapter_boundary.gate_adapter_boundary,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="dirty_chunk_or_delta_shape.py",
            packet=packet_to_test,
            gates=[
                gate_dirty_chunk_or_delta_shape.gate_dirty_chunk_or_delta_shape,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_authority_overreach.py",
            packet=packet_to_test,
            gates=[
                gate_no_authority_overreach.gate_no_authority_overreach,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="terrain_adapter_rejection_proof.py",
            packet=packet_to_test,
            gates=[
                gate_terrain_adapter_rejection_proof.gate_rejects_canon_truth,
                gate_terrain_adapter_rejection_proof.gate_rejects_render,
                gate_terrain_adapter_rejection_proof.gate_rejects_authoritative,
            ],
        )
    )

    system_passed = all(script_results)

    print(f"TERRAIN_CONTROL_CENTER RESULT: {'TRUE' if system_passed else 'FALSE'}")

    return system_passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)