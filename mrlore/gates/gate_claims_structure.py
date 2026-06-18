# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/mrlore/gates/gate_claims_structure.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_claims_structure_valid(packet: dict[str, Any]) -> GateResult:
    claims = packet.get("claims", [])

    if not isinstance(claims, list):
        return GateResult(
            "gate_claims_structure_valid",
            "FALSE",
            "claims must be a list",
        )

    for idx, claim in enumerate(claims):
        if not isinstance(claim, dict):
            return GateResult(
                "gate_claims_structure_valid",
                "FALSE",
                f"Claim at index {idx} must be a dict",
            )

        # Required fields
        for required_key in ("claim_id", "subject", "predicate", "object"):
            if required_key not in claim:
                return GateResult(
                    "gate_claims_structure_valid",
                    "FALSE",
                    f"Claim at index {idx} missing {required_key}",
                )

            if not isinstance(claim[required_key], str) or not claim[required_key].strip():
                return GateResult(
                    "gate_claims_structure_valid",
                    "FALSE",
                    f"Claim at index {idx} {required_key} must be a non-empty string",
                )

        # source_span is REQUIRED for MrLore (canon review with source anchors)
        source_span = claim.get("source_span")
        if source_span is None:
            return GateResult(
                "gate_claims_structure_valid",
                "FALSE",
                f"Claim at index {idx} missing required source_span",
            )

        if not isinstance(source_span, dict):
            return GateResult(
                "gate_claims_structure_valid",
                "FALSE",
                f"Claim at index {idx} source_span must be a dict",
            )

        if "start" not in source_span or "end" not in source_span:
            return GateResult(
                "gate_claims_structure_valid",
                "FALSE",
                f"Claim at index {idx} source_span missing start or end",
            )

        # STRICT INTEGER CHECK: type(value) is int, not isinstance(value, int)
        # This prevents bool values from passing as integers
        if type(source_span["start"]) is not int:
            return GateResult(
                "gate_claims_structure_valid",
                "FALSE",
                f"Claim at index {idx} source_span start must be an integer",
            )

        if type(source_span["end"]) is not int:
            return GateResult(
                "gate_claims_structure_valid",
                "FALSE",
                f"Claim at index {idx} source_span end must be an integer",
            )

        if source_span["end"] < source_span["start"]:
            return GateResult(
                "gate_claims_structure_valid",
                "FALSE",
                f"Claim at index {idx} source_span end < start",
            )

        # canon_risk is optional but if present must be valid
        canon_risk = claim.get("canon_risk")
        if canon_risk is not None:
            if not isinstance(canon_risk, str) or canon_risk not in ("low", "medium", "high"):
                return GateResult(
                    "gate_claims_structure_valid",
                    "FALSE",
                    f"Claim at index {idx} canon_risk must be low/medium/high",
                )

    return GateResult(
        "gate_claims_structure_valid",
        "TRUE",
        "All claims have valid structure with required source_span",
    )