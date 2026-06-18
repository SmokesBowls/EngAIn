# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mrlore/gates/gate_contradictions_valid_if_present.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_contradictions_valid_if_present(packet: dict[str, Any]) -> GateResult:
    contradictions = packet.get("contradictions")

    # BYPASS: contradictions is optional
    if contradictions is None:
        return GateResult(
            "gate_contradictions_valid_if_present",
            "SKIPPED",
            "contradictions inspected: optional field absent, no claim made",
        )

    if not isinstance(contradictions, list):
        return GateResult(
            "gate_contradictions_valid_if_present",
            "FALSE",
            "contradictions must be a list",
        )

    packet_human_review_required = packet.get("human_review_required", False)
    packet_review_status = packet.get("review_status", "")

    for idx, contra in enumerate(contradictions):
        if not isinstance(contra, dict):
            return GateResult(
                "gate_contradictions_valid_if_present",
                "FALSE",
                f"Contradiction at index {idx} must be a dict",
            )

        for required_key in ("contradiction_id", "severity", "reason", "requires_human_review"):
            if required_key not in contra:
                return GateResult(
                    "gate_contradictions_valid_if_present",
                    "FALSE",
                    f"Contradiction at index {idx} missing {required_key}",
                )

        if not isinstance(contra["contradiction_id"], str) or not contra["contradiction_id"].strip():
            return GateResult(
                "gate_contradictions_valid_if_present",
                "FALSE",
                f"Contradiction at index {idx} contradiction_id must be a non-empty string",
            )

        if not isinstance(contra["severity"], str) or contra["severity"] not in ("low", "medium", "high"):
            return GateResult(
                "gate_contradictions_valid_if_present",
                "FALSE",
                f"Contradiction at index {idx} severity must be low/medium/high",
            )

        if not isinstance(contra["reason"], str) or not contra["reason"].strip():
            return GateResult(
                "gate_contradictions_valid_if_present",
                "FALSE",
                f"Contradiction at index {idx} reason must be a non-empty string",
            )

        if not isinstance(contra["requires_human_review"], bool):
            return GateResult(
                "gate_contradictions_valid_if_present",
                "FALSE",
                f"Contradiction at index {idx} requires_human_review must be boolean",
            )

        # HUMAN REVIEW ENFORCEMENT: medium/high severity must stop for review
        if contra["severity"] in ("medium", "high"):
            if not contra["requires_human_review"]:
                return GateResult(
                    "gate_contradictions_valid_if_present",
                    "FALSE",
                    f"Contradiction at index {idx} severity={contra['severity']} requires requires_human_review=true",
                )

            if not packet_human_review_required:
                return GateResult(
                    "gate_contradictions_valid_if_present",
                    "FALSE",
                    f"Contradiction at index {idx} severity={contra['severity']} requires packet.human_review_required=true",
                )

            if packet_review_status != "human_review_required":
                return GateResult(
                    "gate_contradictions_valid_if_present",
                    "FALSE",
                    f"Contradiction at index {idx} severity={contra['severity']} requires packet.review_status='human_review_required'",
                )

    return GateResult(
        "gate_contradictions_valid_if_present",
        "TRUE",
        "All contradictions have valid structure with proper human-review enforcement",
    )