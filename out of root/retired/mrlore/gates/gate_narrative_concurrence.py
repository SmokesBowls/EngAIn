"""Lifecycle gate for MrLore narrative concurrence over proposed layouts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


_GATE_ID = "gate_narrative_concurrence"


def evaluate_metric_layout_for_concurrence(
    proposed_metric_layout: dict[str, Any],
    concurrence_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Gate to transition a proposed metric layout to the CONCURRED state.
    
    Checks that validation did not result in contradictions or unresolved findings.
    """
    violations: list[str] = []

    if proposed_metric_layout.get("lifecycle") != "PROPOSED":
        violations.append("metric-layout lifecycle must be PROPOSED")

    decision = concurrence_report.get("concurrence_decision", "REJECTED")
    if decision != "CONCURRED":
        violations.append(
            f"concurrence checker decision was {decision}, expected CONCURRED"
        )

    concurred_packet: dict[str, Any] | None = None

    if decision == "CONCURRED" and not violations:
        concurred_packet = {
            "packet_type": "narratively_concurred_metric_layout",
            "lifecycle": "CONCURRED",
            "source_topology_artifact_id": proposed_metric_layout.get("source_artifact_id"),
            "source_metric_layout_artifact_id": proposed_metric_layout.get("artifact_id"),
            "concurrence_decision": "CONCURRED",
            "contradictions": list(concurrence_report.get("contradictions", [])),
            "unresolved_findings": list(concurrence_report.get("unresolved_findings", [])),
            "metric_layout": deepcopy(proposed_metric_layout),
        }

    return {
        "gate_id": _GATE_ID,
        "decision": "CONCURRED" if (decision == "CONCURRED" and not violations) else "REJECTED",
        "input_lifecycle": proposed_metric_layout.get("lifecycle"),
        "output_lifecycle": "CONCURRED" if (decision == "CONCURRED" and not violations) else proposed_metric_layout.get("lifecycle"),
        "concurred_metric_layout_packet": concurred_packet,
        "violations": violations,
    }
