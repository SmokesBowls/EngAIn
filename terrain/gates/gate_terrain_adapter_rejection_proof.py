# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/gates/gate_terrain_adapter_rejection_proof.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult
from terrain.gates.gate_no_authority_overreach import gate_no_authority_overreach


VALID_BASE_PACKET: dict[str, Any] = {
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


BAD_PACKET_WITH_CANON: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "canon_truth": True,
}


BAD_PACKET_WITH_RENDER: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "render": True,
}


BAD_PACKET_WITH_AUTHORITATIVE: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "authoritative": True,
}


def gate_rejects_canon_truth(packet: dict[str, Any]) -> GateResult:
    """PROOF: Terrain packet with canon_truth is rejected."""
    result = gate_no_authority_overreach(BAD_PACKET_WITH_CANON)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_canon_truth",
            "TRUE",
            "Packet with canon_truth was correctly rejected",
        )

    return GateResult(
        "gate_rejects_canon_truth",
        "FALSE",
        f"Packet with canon_truth should have been rejected but got {result.passed}: {result.message}",
    )


def gate_rejects_render(packet: dict[str, Any]) -> GateResult:
    """PROOF: Terrain packet with render is rejected."""
    result = gate_no_authority_overreach(BAD_PACKET_WITH_RENDER)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_render",
            "TRUE",
            "Packet with render was correctly rejected",
        )

    return GateResult(
        "gate_rejects_render",
        "FALSE",
        f"Packet with render should have been rejected but got {result.passed}: {result.message}",
    )


def gate_rejects_authoritative(packet: dict[str, Any]) -> GateResult:
    """PROOF: Terrain packet with authoritative=true is rejected."""
    result = gate_no_authority_overreach(BAD_PACKET_WITH_AUTHORITATIVE)

    if result.passed == "FALSE":
        return GateResult(
            "gate_rejects_authoritative",
            "TRUE",
            "Packet with authoritative was correctly rejected",
        )

    return GateResult(
        "gate_rejects_authoritative",
        "FALSE",
        f"Packet with authoritative should have been rejected but got {result.passed}: {result.message}",
    )