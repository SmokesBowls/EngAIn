# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_acceptance_rule.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


VALID_ACCEPTANCE_DECISIONS = {"accepted", "rejected", "pending"}


def gate_acceptance_rule_enforced(packet: dict[str, Any]) -> GateResult:
    acceptance_decision = packet.get("acceptance_decision")

    if acceptance_decision is None:
        return GateResult(
            "gate_acceptance_rule_enforced",
            "FALSE",
            "Missing acceptance_decision",
        )

    if acceptance_decision not in VALID_ACCEPTANCE_DECISIONS:
        return GateResult(
            "gate_acceptance_rule_enforced",
            "FALSE",
            f"Invalid acceptance_decision: {acceptance_decision}",
        )

    # If accepted, must have validated packets and passed AP validation
    if acceptance_decision == "accepted":
        validated_packets = packet.get("validated_packets")
        if not isinstance(validated_packets, list) or len(validated_packets) == 0:
            return GateResult(
                "gate_acceptance_rule_enforced",
                "FALSE",
                "Accepted packet must have non-empty validated_packets list",
            )

        ap_validation = packet.get("ap_validation")
        if not isinstance(ap_validation, dict):
            return GateResult(
                "gate_acceptance_rule_enforced",
                "FALSE",
                "Accepted packet must have ap_validation dict",
            )

        if ap_validation.get("result") != "passed":
            return GateResult(
                "gate_acceptance_rule_enforced",
                "FALSE",
                f"Accepted packet must have ap_validation.result='passed', got: {ap_validation.get('result')}",
            )

    return GateResult(
        "gate_acceptance_rule_enforced",
        "TRUE",
        f"Acceptance rule enforced: {acceptance_decision}",
    )