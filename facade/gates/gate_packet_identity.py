# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_packet_identity.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


VALID_AUTHORITY_TIERS = {"TIER_0_5", "0.5", 0.5}


def gate_packet_identity(packet: dict[str, Any]) -> GateResult:
    """Validate Facade Witness packet identity."""
    if packet.get("contract") != "facade.witness_packet.v1":
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "Invalid contract version",
        )

    if packet.get("source") != "facade_witness":
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "Invalid source",
        )

    authority_tier = packet.get("authority_tier")
    if authority_tier not in VALID_AUTHORITY_TIERS:
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            f"Invalid authority_tier: {authority_tier}",
        )

    if packet.get("authority_lane") != "boundary_guard":
        return GateResult(
            "gate_packet_identity",
            "FALSE",
            "Invalid authority_lane",
        )

    return GateResult(
        "gate_packet_identity",
        "TRUE",
        "Facade Witness packet identity is valid",
    )