# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mrlore/gates/gate_human_review_enforcement.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_auto_resolve_requires_human_review(packet: dict[str, Any]) -> GateResult:
    """
    If allowed_to_auto_resolve is true, human_review_required must also be true.
    MrLore may not silently resolve contradictions without human review.
    """
    allowed_to_auto_resolve = packet.get("allowed_to_auto_resolve", False)

    if not isinstance(allowed_to_auto_resolve, bool):
        return GateResult(
            "gate_auto_resolve_requires_human_review",
            "FALSE",
            "allowed_to_auto_resolve must be boolean",
        )

    if allowed_to_auto_resolve:
        human_review_required = packet.get("human_review_required", False)
        if not human_review_required:
            return GateResult(
                "gate_auto_resolve_requires_human_review",
                "FALSE",
                "HARD REJECT: auto-resolve attempted without human_review_required=true",
            )

    return GateResult(
        "gate_auto_resolve_requires_human_review",
        "TRUE",
        "Auto-resolve enforcement passed",
    )