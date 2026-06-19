# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixel/trixel_parser_control_center.py

from __future__ import annotations

from typing import Any

from engain_control.gate_print import run_script_gates

from trixel.gates import gate_gimp_palette_file
from trixel.gates import gate_gimp_palette_rejection_proof
from trixel.gates import gate_manifest_shape
from trixel.gates import gate_adapter_output_shape
from trixel.gates import gate_adapter_rejection_proof


MINIMAL_TEST_PACKET: dict[str, Any] = {}


def run(packet: dict[str, Any] | None = None) -> bool:
    packet_to_test = packet if packet is not None else MINIMAL_TEST_PACKET

    script_results: list[bool] = []

    # Parser gates
    script_results.append(
        run_script_gates(
            script_name="gimp_palette_file.py",
            packet=packet_to_test,
            gates=[
                gate_gimp_palette_file.gate_imports,
                gate_gimp_palette_file.gate_class_exists,
                gate_gimp_palette_file.gate_valid_input,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="gimp_palette_rejection_proof.py",
            packet=packet_to_test,
            gates=[
                gate_gimp_palette_rejection_proof.gate_rejects_missing_header,
                gate_gimp_palette_rejection_proof.gate_rejects_bad_color_values,
                gate_gimp_palette_rejection_proof.gate_rejects_empty_input,
            ],
        )
    )

    # Manifest gates
    script_results.append(
        run_script_gates(
            script_name="manifest_shape.py",
            packet=packet_to_test,
            gates=[
                gate_manifest_shape.gate_manifest_identity,
                gate_manifest_shape.gate_manifest_assets_shape,
                gate_manifest_shape.gate_no_lane_theft_in_manifest,
            ],
        )
    )

    # Adapter output gates
    script_results.append(
        run_script_gates(
            script_name="adapter_output_shape.py",
            packet=packet_to_test,
            gates=[
                gate_adapter_output_shape.gate_spatial_authority_shape,
                gate_adapter_output_shape.gate_resolved_layout_shape,
                gate_adapter_output_shape.gate_terrain_field_shape,
                gate_adapter_output_shape.gate_recipe_shape,
                gate_adapter_output_shape.gate_atlas_plan_shape,
            ],
        )
    )

    # Adapter rejection proof
    script_results.append(
        run_script_gates(
            script_name="adapter_rejection_proof.py",
            packet=packet_to_test,
            gates=[
                gate_adapter_rejection_proof.gate_rejects_authoritative_recipe,
            ],
        )
    )

    system_passed = all(script_results)

    print(f"TRIXEL_PARSER_CONTROL_CENTER RESULT: {'TRUE' if system_passed else 'FALSE'}")

    return system_passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)