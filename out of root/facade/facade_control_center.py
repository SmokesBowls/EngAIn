# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/facade_control_center.py

from __future__ import annotations

from typing import Any

from engain_control.gate_print import run_script_gates

from facade.gates import gate_packet_identity
from facade.gates import gate_safe_import_contract
from facade.gates import gate_no_runtime_entrypoint_import
from facade.gates import gate_no_side_effect_imports
from facade.gates import gate_packet_shape_boundary
from facade.gates import gate_no_render_truth_mixed
from facade.gates import gate_legacy_wrapped_not_replaced
from facade.gates import gate_migration_status_honest
from facade.gates import gate_facade_rejection_proof


MINIMAL_TEST_PACKET: dict[str, Any] = {
    "contract": "facade.witness_packet.v1",
    "source": "facade_witness",
    "authority_tier": "TIER_0_5",
    "authority_lane": "boundary_guard",
    "import_attempts": [
        {
            "module": "engainos.core.ap_core",
            "side_effects_checked": True,
            "passed": True,
        }
    ],
    "packet_validations": [
        {
            "packet_type": "godotsim.spatial_sim_packet.v1",
            "shape_valid": True,
        }
    ],
    "migration_status": {
        "status": "in_progress",
        "legacy_source_active": True,
        "full_migration_complete": False,
    },
    "legacy_wrapped": [
        {
            "module": "godotengain.engainos.core.ap_core",
            "wrapped": True,
            "replaced": False,
        }
    ],
    "runtime_entrypoints_guarded": [
        {
            "entrypoint": "launch_engine",
            "not_imported_by_design": True,
        }
    ],
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
            script_name="safe_import_contract.py",
            packet=packet_to_test,
            gates=[
                gate_safe_import_contract.gate_safe_import_contract,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_runtime_entrypoint_import.py",
            packet=packet_to_test,
            gates=[
                gate_no_runtime_entrypoint_import.gate_no_runtime_entrypoint_import,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_side_effect_imports.py",
            packet=packet_to_test,
            gates=[
                gate_no_side_effect_imports.gate_no_side_effect_imports,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="packet_shape_boundary.py",
            packet=packet_to_test,
            gates=[
                gate_packet_shape_boundary.gate_packet_shape_boundary,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="no_render_truth_mixed.py",
            packet=packet_to_test,
            gates=[
                gate_no_render_truth_mixed.gate_no_render_truth_mixed,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="legacy_wrapped_not_replaced.py",
            packet=packet_to_test,
            gates=[
                gate_legacy_wrapped_not_replaced.gate_legacy_wrapped_not_replaced,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="migration_status_honest.py",
            packet=packet_to_test,
            gates=[
                gate_migration_status_honest.gate_migration_status_honest,
            ],
        )
    )

    script_results.append(
        run_script_gates(
            script_name="facade_rejection_proof.py",
            packet=packet_to_test,
            gates=[
                gate_facade_rejection_proof.gate_rejects_side_effect,
                gate_facade_rejection_proof.gate_rejects_render_truth,
                gate_facade_rejection_proof.gate_rejects_migration_lie,
                gate_facade_rejection_proof.gate_rejects_legacy_replacement,
                gate_facade_rejection_proof.gate_rejects_runtime_entrypoint_import,
            ],
        )
    )

    system_passed = all(script_results)

    print(f"FACADE_CONTROL_CENTER RESULT: {'TRUE' if system_passed else 'FALSE'}")

    return system_passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)