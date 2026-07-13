"""Lifecycle gate for Cartographer metric-layout proposals."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_GATE_ID = "gate_propose_metric_layout"


def evaluate_metric_layout_for_proposal(
    artifact: dict[str, Any],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    violations: list[str] = []

    if artifact.get("lifecycle") != "DRAFT":
        violations.append("metric-layout lifecycle must be DRAFT")

    if not validation_report.get("passed", False):
        violations.append("metric-layout validation did not pass")

    report_violations = validation_report.get("violations", [])
    if report_violations:
        violations.append(
            f"validation report contains {len(report_violations)} violation(s)"
        )

    decision = "PROPOSED" if not violations else "REJECTED"
    proposed_packet: dict[str, Any] | None = None

    if decision == "PROPOSED":
        proposed_packet = deepcopy(artifact)
        proposed_packet["packet_type"] = "proposed_metric_layout"
        proposed_packet["lifecycle"] = "PROPOSED"
        proposed_packet["authority_note"] = (
            "Cartographer metric proposal only. Requires MrLore narrative "
            "concurrence and EngAInOS contract/authority verification before use."
        )

    return {
        "gate_id": _GATE_ID,
        "decision": decision,
        "input_lifecycle": artifact.get("lifecycle"),
        "output_lifecycle": "PROPOSED" if decision == "PROPOSED" else artifact.get("lifecycle"),
        "proposed_metric_layout_packet": proposed_packet,
        "violations": violations,
    }
