# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/mrlore/gates/gate_enum_values_valid.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


VALID_REVIEW_STATUSES = {
    "unconfirmed",
    "canon_approved",
    "human_review_required",
    "rejected",
}

VALID_CANON_STATUSES = {
    "unconfirmed",
    "confirmed",
    "contradicts_established",
    "needs_source",
}


def gate_review_status_valid(packet: dict[str, Any]) -> GateResult:
    review_status = packet.get("review_status")

    if review_status is None:
        return GateResult(
            "gate_review_status_valid",
            "FALSE",
            "Missing review_status",
        )

    if not isinstance(review_status, str):
        return GateResult(
            "gate_review_status_valid",
            "FALSE",
            "review_status must be a string",
        )

    if review_status not in VALID_REVIEW_STATUSES:
        return GateResult(
            "gate_review_status_valid",
            "FALSE",
            f"Invalid review_status: {review_status}",
        )

    return GateResult(
        "gate_review_status_valid",
        "TRUE",
        "review_status is valid",
    )


def gate_canon_status_valid(packet: dict[str, Any]) -> GateResult:
    canon_status = packet.get("canon_status")

    if canon_status is None:
        return GateResult(
            "gate_canon_status_valid",
            "FALSE",
            "Missing canon_status",
        )

    if not isinstance(canon_status, str):
        return GateResult(
            "gate_canon_status_valid",
            "FALSE",
            "canon_status must be a string",
        )

    if canon_status not in VALID_CANON_STATUSES:
        return GateResult(
            "gate_canon_status_valid",
            "FALSE",
            f"Invalid canon_status: {canon_status}",
        )

    return GateResult(
        "gate_canon_status_valid",
        "TRUE",
        "canon_status is valid",
    )