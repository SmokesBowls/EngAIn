
# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_validated_packets_shape.py

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

from typing import Any

from engain_control.gate_result import GateResult

VALID_PACKET_RESULTS = {"accepted", "rejected", "pending"}
ALLOWED_VALIDATED_PACKET_KEYS = {"source", "contract", "result"}

def gate_validated_packets_shape(packet: dict[str, Any]) -> GateResult:
    validated_packets = packet.get("validated_packets")

    if not isinstance(validated_packets, list):
        return GateResult(
            "gate_validated_packets_shape",
            "FALSE",
            "validated_packets must be a list",
        )

    for idx, vp in enumerate(validated_packets):
        if not isinstance(vp, dict):
            return GateResult(
                "gate_validated_packets_shape",
                "FALSE",
                f"Validated packet at index {idx} must be a dict",
            )

        # Check for forbidden keys (prevent full packet embedding)
        forbidden_keys = set(vp.keys()) - ALLOWED_VALIDATED_PACKET_KEYS
        if forbidden_keys:
            return GateResult(
                "gate_validated_packets_shape",
                "FALSE",
                f"Validated packet at index {idx} contains forbidden keys: {forbidden_keys}",
            )

        source = vp.get("source")
        if not isinstance(source, str) or not source.strip():
            return GateResult(
                "gate_validated_packets_shape",
                "FALSE",
                f"Validated packet at index {idx} source must be a non-empty string",
            )

        contract = vp.get("contract")
        if not isinstance(contract, str) or not contract.strip():
            return GateResult(
                "gate_validated_packets_shape",
                "FALSE",
                f"Validated packet at index {idx} contract must be a non-empty string",
            )

        result = vp.get("result")
        if result not in VALID_PACKET_RESULTS:
            return GateResult(
                "gate_validated_packets_shape",
                "FALSE",
                f"Validated packet at index {idx} result must be one of {VALID_PACKET_RESULTS}, got: {result}",
            )

    return GateResult(
        "gate_validated_packets_shape",
        "TRUE",
        "Validated packets shape is valid",
    )
