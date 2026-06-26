"""
gate_accept_proposed_topology_artifact.py — Topologist Gates

The gate that advances a ProseTopologyArtifact from PROPOSED to ACCEPTED.

Boundary:
  Validation (reckoningroom) says: "artifact is structurally sound."
  This gate says:                  "artifact may advance lifecycle."

  These are different authorities. Validation is a technical check.
  The gate is a lifecycle decision. Only the gate may write ACCEPTED.

What the gate checks:
  ✓ artifact.lifecycle == "PROPOSED"
  ✓ validation_report.passed == True
  ✓ validation_report.violations == []
  ✓ artifact has at least two entities
  ✓ artifact has at least one topology link
  ✓ no render / coordinate / Trixel fields present
  ✓ no runtime mutation payload

What the gate does NOT do:
  ✗ re-validate topology structure (that is the reckoningroom's job)
  ✗ parse prose
  ✗ call Godot, Trixel, Blender, or Mechanimation
  ✗ advance lifecycle without a clean validation report
  ✗ invent or modify spatial relations
"""

from __future__ import annotations

from typing import Any


_GATE_ID = "gate_accept_proposed_topology_artifact"

_RENDER_FORBIDDEN = frozenset({
    "trixel_payload", "blender_payload", "mechanimation_payload",
    "render", "renderer", "visual", "sprite", "mesh", "texture",
    "x", "y", "z", "position", "transform", "global_transform",
    "translation", "rotation", "scale", "node_path",
    "width_px", "height_px", "depth_px",
})


def evaluate_topology_artifact_for_acceptance(
    artifact: dict[str, Any],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate a PROPOSED ProseTopologyArtifact for lifecycle advancement.

    Takes raw dicts so the gate operates independently of the artifact
    dataclass — caller may load from JSON without importing topology_artifact.

    Args:
        artifact:          ProseTopologyArtifact.to_dict() output.
        validation_report: ValidationReport.to_dict() output.

    Returns:
        Gate result dict:
        {
            "gate_id":        str,
            "decision":       "ACCEPTED" | "REJECTED",
            "input_lifecycle": str,
            "output_lifecycle": str,
            "accepted_spatial_truth_packet": dict | None,
            "violations":     list[str],
        }
    """
    violations: list[str] = []
    input_lifecycle = artifact.get("lifecycle", "")

    # 1. Lifecycle must be PROPOSED
    if input_lifecycle != "PROPOSED":
        violations.append(
            f"lifecycle must be PROPOSED; got '{input_lifecycle}'. "
            "Advance from DRAFT to PROPOSED before gate submission."
        )

    # 2. Validation must have passed
    if not validation_report.get("passed", False):
        violations.append(
            "validation_report.passed is False — "
            "artifact failed the reckoningroom. Resolve violations first."
        )

    # 3. No open violations in the validation report
    report_violations = validation_report.get("violations", [])
    if report_violations:
        violations.append(
            f"validation_report.violations is non-empty "
            f"({len(report_violations)} violation(s)). "
            "All topology violations must be resolved before gate submission."
        )

    # 4. At least two entities (spatial relation requires figure + ground)
    entities = artifact.get("entities", [])
    if len(entities) < 2:
        violations.append(
            f"artifact declares {len(entities)} entity/entities; "
            "at least two are required. "
            "A spatial relation must have a figure and a ground."
        )

    # 5. At least one topology link
    link_count = (
        len(artifact.get("olinks",    []))
        + len(artifact.get("qslinks",  []))
        + len(artifact.get("movelinks", []))
    )
    if link_count == 0:
        violations.append(
            "artifact has no topology links (olinks + qslinks + movelinks = 0). "
            "An accepted artifact must assert at least one spatial relation."
        )

    # 6. No render / coordinate / Trixel fields
    for key in _RENDER_FORBIDDEN:
        if key in artifact:
            violations.append(
                f"artifact contains forbidden field '{key}'. "
                "Accepted spatial truth must be coordinate-free and render-free."
            )

    decision        = "ACCEPTED" if not violations else "REJECTED"
    output_lifecycle = "ACCEPTED" if decision == "ACCEPTED" else input_lifecycle

    accepted_packet: dict[str, Any] | None = None
    if decision == "ACCEPTED":
        accepted_packet = {
            "packet_type":        "accepted_spatial_truth",
            "source_artifact_id": artifact.get("artifact_id"),
            "entities":           artifact.get("entities",  []),
            "qslinks":            artifact.get("qslinks",   []),
            "olinks":             artifact.get("olinks",    []),
            "movelinks":          artifact.get("movelinks", []),
        }

    return {
        "gate_id":                       _GATE_ID,
        "decision":                      decision,
        "input_lifecycle":               input_lifecycle,
        "output_lifecycle":              output_lifecycle,
        "accepted_spatial_truth_packet": accepted_packet,
        "violations":                    violations,
    }
