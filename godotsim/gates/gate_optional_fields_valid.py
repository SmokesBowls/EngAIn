# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_optional_fields_valid.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_rotation_valid_if_present(packet: dict[str, Any]) -> GateResult:
    any_present = False

    for idx, entity in enumerate(packet.get("entities", [])):
        rotation = entity.get("rotation")
        if rotation is None:
            continue

        any_present = True

        if not isinstance(rotation, list):
            return GateResult(
                "gate_rotation_valid_if_present",
                "FALSE",
                f"Entity at index {idx} rotation must be a list",
            )

        if len(rotation) != 3:
            return GateResult(
                "gate_rotation_valid_if_present",
                "FALSE",
                f"Entity at index {idx} rotation must have exactly 3 elements",
            )

        for coord_idx, coord in enumerate(rotation):
            if type(coord) not in (int, float):
                return GateResult(
                    "gate_rotation_valid_if_present",
                    "FALSE",
                    f"Entity at index {idx} rotation[{coord_idx}] must be numeric",
                )

    if not any_present:
        return GateResult(
            "gate_rotation_valid_if_present",
            "SKIPPED",
            "rotation inspected: optional field absent, no claim made",
        )

    return GateResult(
        "gate_rotation_valid_if_present",
        "TRUE",
        "All present rotation fields are valid",
    )


def gate_velocity_valid_if_present(packet: dict[str, Any]) -> GateResult:
    any_present = False

    for idx, entity in enumerate(packet.get("entities", [])):
        velocity = entity.get("velocity")
        if velocity is None:
            continue

        any_present = True

        if not isinstance(velocity, list):
            return GateResult(
                "gate_velocity_valid_if_present",
                "FALSE",
                f"Entity at index {idx} velocity must be a list",
            )

        if len(velocity) != 3:
            return GateResult(
                "gate_velocity_valid_if_present",
                "FALSE",
                f"Entity at index {idx} velocity must have exactly 3 elements",
            )

        for coord_idx, coord in enumerate(velocity):
            if type(coord) not in (int, float):
                return GateResult(
                    "gate_velocity_valid_if_present",
                    "FALSE",
                    f"Entity at index {idx} velocity[{coord_idx}] must be numeric",
                )

    if not any_present:
        return GateResult(
            "gate_velocity_valid_if_present",
            "SKIPPED",
            "velocity inspected: optional field absent, no claim made",
        )

    return GateResult(
        "gate_velocity_valid_if_present",
        "TRUE",
        "All present velocity fields are valid",
    )


def gate_grounded_valid_if_present(packet: dict[str, Any]) -> GateResult:
    any_present = False

    for idx, entity in enumerate(packet.get("entities", [])):
        grounded = entity.get("grounded")
        if grounded is None:
            continue

        any_present = True

        if not isinstance(grounded, bool):
            return GateResult(
                "gate_grounded_valid_if_present",
                "FALSE",
                f"Entity at index {idx} grounded must be boolean",
            )

    if not any_present:
        return GateResult(
            "gate_grounded_valid_if_present",
            "SKIPPED",
            "grounded inspected: optional field absent, no claim made",
        )

    return GateResult(
        "gate_grounded_valid_if_present",
        "TRUE",
        "All present grounded fields are valid",
    )