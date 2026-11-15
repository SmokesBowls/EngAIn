# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/mrlore/gates/gate_contradiction_stop_proof.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult
from tier1.mrlore.gates.gate_contradictions_valid_if_present import gate_contradictions_valid_if_present


VALID_MEDIUM_CONTRADICTION_PACKET: dict[str, Any] = {
    "contract": "mrlore.canon_review_packet.v1",
    "source": "mrlore",
    "authority_lane": "canon_review",
    "authority_tier": 3,
    "scene_id": "scene.030_ummade_army",
    "source_text_id": "chapter_or_pass_id",
    "review_status": "human_review_required",
    "canon_status": "unconfirmed",
    "claims": [],
    "human_review_required": True,
    "contradictions": [
        {
            "contradiction_id": "contra_001",
            "severity": "medium",
            "reason": "Entity name appears under two aliases.",
            "requires_human_review": True,
        }
    ],
}


INVALID_MEDIUM_CONTRADICTION_PACKET: dict[str, Any] = {
    **VALID_MEDIUM_CONTRADICTION_PACKET,
    "contradictions": [
        {
            "contradiction_id": "contra_001",
            "severity": "medium",
            "reason": "Entity name appears under two aliases.",
            "requires_human_review": False,  # VIOLATION: medium severity requires True
        }
    ],
}


INVALID_PACKET_REVIEW_STATUS: dict[str, Any] = {
    **VALID_MEDIUM_CONTRADICTION_PACKET,
    "review_status": "unconfirmed",  # VIOLATION: medium severity requires "human_review_required"
}


def gate_medium_contradiction_positive_path(packet: dict[str, Any]) -> GateResult:
    """
    PROOF: Valid medium contradiction packet should pass.
    Returns TRUE if the underlying gate returns TRUE.
    Returns FALSE if the underlying gate returns FALSE or SKIPPED.
    """
    result = gate_contradictions_valid_if_present(VALID_MEDIUM_CONTRADICTION_PACKET)
    
    if result.passed == "TRUE":
        return GateResult(
            "gate_medium_contradiction_positive_path",
            "TRUE",
            "Valid medium contradiction requires human review and passed",
        )
    
    return GateResult(
        "gate_medium_contradiction_positive_path",
        "FALSE",
        f"Valid medium contradiction should have passed but got {result.passed}: {result.message}",
    )


def gate_medium_contradiction_rejection_path(packet: dict[str, Any]) -> GateResult:
    """
    PROOF: Invalid medium contradiction packet (requires_human_review=false) should be rejected.
    Returns TRUE if the underlying gate returns FALSE (proving rejection works).
    Returns FALSE if the underlying gate returns TRUE or SKIPPED (proving rejection failed).
    """
    result = gate_contradictions_valid_if_present(INVALID_MEDIUM_CONTRADICTION_PACKET)
    
    if result.passed == "FALSE":
        return GateResult(
            "gate_medium_contradiction_rejection_path",
            "TRUE",
            "Invalid medium contradiction was correctly rejected",
        )
    
    return GateResult(
        "gate_medium_contradiction_rejection_path",
        "FALSE",
        f"Invalid medium contradiction should have been rejected but got {result.passed}: {result.message}",
    )


def gate_medium_contradiction_review_status_rejection(packet: dict[str, Any]) -> GateResult:
    """
    PROOF: Medium contradiction with wrong review_status should be rejected.
    Returns TRUE if the underlying gate returns FALSE (proving rejection works).
    Returns FALSE if the underlying gate returns TRUE or SKIPPED (proving rejection failed).
    """
    result = gate_contradictions_valid_if_present(INVALID_PACKET_REVIEW_STATUS)
    
    if result.passed == "FALSE":
        return GateResult(
            "gate_medium_contradiction_review_status_rejection",
            "TRUE",
            "Medium contradiction with wrong review_status was correctly rejected",
        )
    
    return GateResult(
        "gate_medium_contradiction_review_status_rejection",
        "FALSE",
        f"Medium contradiction with wrong review_status should have been rejected but got {result.passed}: {result.message}",
    )