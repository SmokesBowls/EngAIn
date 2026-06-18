# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_packet_shape_boundary.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_packet_shape_boundary(packet: dict[str, Any]) -> GateResult:
    """Validate packet shape boundary exists and is enforced."""
    packet_validations = packet.get("packet_validations")

    if not isinstance(packet_validations, list):
        return GateResult(
            "gate_packet_shape_boundary",
            "FALSE",
            "packet_validations must be a list",
        )

    for idx, validation in enumerate(packet_validations):
        if not isinstance(validation, dict):
            return GateResult(
                "gate_packet_shape_boundary",
                "FALSE",
                f"Packet validation at index {idx} must be a dict",
            )

        for required_key in ("packet_type", "shape_valid"):
            if required_key not in validation:
                return GateResult(
                    "gate_packet_shape_boundary",
                    "FALSE",
                    f"Packet validation at index {idx} missing {required_key}",
                )

        if not isinstance(validation["packet_type"], str) or not validation["packet_type"].strip():
            return GateResult(
                "gate_packet_shape_boundary",
                "FALSE",
                f"Packet validation at index {idx} packet_type must be a non-empty string",
            )

        if not isinstance(validation["shape_valid"], bool):
            return GateResult(
                "gate_packet_shape_boundary",
                "FALSE",
                f"Packet validation at index {idx} shape_valid must be boolean",
            )

        # STRICT: A packet validation that reports invalid shape must fail the board.
        if validation["shape_valid"] is not True:
            return GateResult(
                "gate_packet_shape_boundary",
                "FALSE",
                f"Packet validation at index {idx} reports shape_valid=false - facade cannot bless an invalid shape",
            )

    return GateResult(
        "gate_packet_shape_boundary",
        "TRUE",
        "Packet shape boundary is enforced and all shapes are valid",
    )