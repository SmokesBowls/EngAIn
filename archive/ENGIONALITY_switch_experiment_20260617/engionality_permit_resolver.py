from __future__ import annotations

from engain_control.control_report import ControlCenterReport
from engain_control.permit_decision import PermitDecision


REQUIRED_GATES = {
    "gate_contract_and_source_valid",
    "gate_scene_and_time_present",
    "gate_entities_array_present",
    "gate_entity_intensity_bounds",
    "gate_affect_state_present_and_valid",
    "gate_no_lane_theft_in_packet",
}


OPTIONAL_GATES = {
    "gate_relationship_deltas_valid_if_present",
    "gate_scene_mood_valid_if_present",
}


def resolve_engionality_permit(report: ControlCenterReport) -> PermitDecision:
    all_gates = report.all_gates()

    false_gates = [
        gate for gate in all_gates
        if gate.passed == "FALSE"
    ]

    if false_gates:
        failed_names = [gate.gate_name for gate in false_gates]
        return PermitDecision(
            permit="DENY",
            message=f"Engionality packet denied. Failed gates: {failed_names}",
        )

    gate_by_name = {
        gate.gate_name: gate
        for gate in all_gates
    }

    missing_required = [
        gate_name for gate_name in REQUIRED_GATES
        if gate_name not in gate_by_name
    ]

    if missing_required:
        return PermitDecision(
            permit="DENY",
            message=f"Engionality packet denied. Required gates did not run: {missing_required}",
        )

    required_not_true = [
        gate_name for gate_name in REQUIRED_GATES
        if gate_by_name[gate_name].passed != "TRUE"
    ]

    if required_not_true:
        return PermitDecision(
            permit="DENY",
            message=f"Engionality packet denied. Required gates were not TRUE: {required_not_true}",
        )

    true_gates = [
        gate for gate in all_gates
        if gate.passed == "TRUE"
    ]

    if not true_gates:
        return PermitDecision(
            permit="NO_CLAIM",
            message="No Engionality claims were made. No worker should run.",
        )

    skipped_optional = [
        gate.gate_name for gate in all_gates
        if gate.gate_name in OPTIONAL_GATES and gate.passed == "SKIPPED"
    ]

    return PermitDecision(
        permit="ALLOW",
        message=(
            "Engionality packet allowed. Required gates passed. "
            f"Optional gates stepped aside cleanly: {skipped_optional}"
        ),
    )