# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/mrlore/gates/gate_no_auto_resolve_attempt.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_no_auto_resolve_attempt(packet: dict[str, Any]) -> GateResult:
    """
    MrLore may not auto-resolve canon contradictions in this supervisor.
    Human review does not bless auto-resolution. It stops the packet for review.
    
    If allowed_to_auto_resolve is True, return FALSE.
    If False or absent, return TRUE.
    """
    allowed_to_auto_resolve = packet.get("allowed_to_auto_resolve", False)

    if not isinstance(allowed_to_auto_resolve, bool):
        return GateResult(
            "gate_no_auto_resolve_attempt",
            "FALSE",
            "allowed_to_auto_resolve must be boolean",
        )

    if allowed_to_auto_resolve:
        return GateResult(
            "gate_no_auto_resolve_attempt",
            "FALSE",
            "HARD REJECT: MrLore may not auto-resolve canon contradictions",
        )

    return GateResult(
        "gate_no_auto_resolve_attempt",
        "TRUE",
        "No auto-resolve attempt detected",
    )