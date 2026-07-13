"""Technical validator for Cartographer metric-layout artifacts."""

from __future__ import annotations

from math import isfinite
from typing import Any


_FORBIDDEN_KEYS = frozenset(
    {
        "image",
        "image_path",
        "png",
        "sprite",
        "texture",
        "material",
        "palette",
        "atlas",
        "mesh",
        "scene_ref",
        "node_path",
        "render_plan",
        "trixel_payload",
        "godot_node",
        "runtime_mutation",
    }
)


def _walk_forbidden(value: Any, path: str = "root") -> list[str]:
    violations: list[str] = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_KEYS:
                violations.append(f"forbidden field present: {child_path}")
            violations.extend(_walk_forbidden(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(_walk_forbidden(child, f"{path}[{index}]"))

    return violations


def validate_metric_layout_artifact(
    artifact: dict[str, Any],
    accepted_spatial_truth: dict[str, Any],
) -> dict[str, Any]:
    violations: list[str] = []
    checks_run = 0

    checks_run += 1
    if artifact.get("contract") != "engain.cartographer_metric_layout.v1":
        violations.append("wrong or missing metric-layout contract")

    checks_run += 1
    if artifact.get("lifecycle") != "DRAFT":
        violations.append("validator input lifecycle must be DRAFT")

    checks_run += 1
    if artifact.get("coordinate_space") != "world_cell_y_up":
        violations.append("coordinate_space must be world_cell_y_up")

    checks_run += 1
    if artifact.get("unit") != "meter":
        violations.append("unit must be meter")

    checks_run += 1
    expected_axis_contract = {
        "x": "east_west",
        "y": "vertical_up",
        "z": "north_south_depth",
    }
    if artifact.get("axis_contract") != expected_axis_contract:
        violations.append("axis_contract does not match world_cell_y_up")

    checks_run += 1
    if accepted_spatial_truth.get("packet_type") != "accepted_spatial_truth":
        violations.append("upstream packet is not accepted_spatial_truth")

    source_entities = accepted_spatial_truth.get("entities", [])
    source_ids = [str(item.get("entity_id", "")) for item in source_entities]
    source_id_set = set(source_ids)

    layout_entities = artifact.get("entities", [])
    layout_ids = [str(item.get("entity_id", "")) for item in layout_entities]
    layout_id_set = set(layout_ids)

    checks_run += 1
    if len(layout_ids) != len(layout_id_set):
        violations.append("metric layout contains duplicate entity IDs")

    checks_run += 1
    if layout_id_set != source_id_set:
        missing = sorted(source_id_set - layout_id_set)
        extra = sorted(layout_id_set - source_id_set)
        violations.append(
            f"entity set mismatch; missing={missing}; extra={extra}"
        )

    checks_run += 1
    anchor_entity_id = str(artifact.get("anchor_entity_id", ""))
    if anchor_entity_id not in layout_id_set:
        violations.append("anchor_entity_id is not present in layout entities")

    anchor_position: dict[str, Any] | None = None

    for entity in layout_entities:
        entity_id = str(entity.get("entity_id", ""))
        position = entity.get("position")

        checks_run += 1
        if not isinstance(position, dict):
            violations.append(f"entity {entity_id} has no position object")
            continue

        for axis in ("x", "y", "z"):
            checks_run += 1
            value = position.get(axis)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                violations.append(
                    f"entity {entity_id} position.{axis} is not numeric"
                )
                continue
            if not isfinite(float(value)):
                violations.append(
                    f"entity {entity_id} position.{axis} is not finite"
                )

        if entity_id == anchor_entity_id:
            anchor_position = position

    checks_run += 1
    if anchor_position != {"x": 0.0, "y": 0.0, "z": 0.0}:
        violations.append("anchor entity must be located at exact origin")

    checks_run += 1
    unresolved = artifact.get("unresolved_constraints", [])
    if unresolved:
        violations.append(
            f"unresolved_constraints is non-empty ({len(unresolved)})"
        )

    forbidden_violations = _walk_forbidden(artifact)
    checks_run += 1
    violations.extend(forbidden_violations)

    return {
        "validator": "cartographer.metric_layout_validator.v1",
        "passed": not violations,
        "checks_run": checks_run,
        "violations": violations,
        "source_entity_count": len(source_id_set),
        "layout_entity_count": len(layout_id_set),
    }
