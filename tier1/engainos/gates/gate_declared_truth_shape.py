
# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_declared_truth_shape.py

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

from typing import Any

from engain_control.gate_result import GateResult

VALID_TRUTH_STATUSES = {"declared", "rejected", "pending"}

def gate_declared_truth_shape(packet: dict[str, Any]) -> GateResult:
    # Validate declared_scene_truth
    declared_scene_truth = packet.get("declared_scene_truth")
    if not isinstance(declared_scene_truth, dict):
        return GateResult(
            "gate_declared_truth_shape",
            "FALSE",
            "declared_scene_truth must be a dict",
        )

    if declared_scene_truth.get("scene_id") != packet.get("scene_id"):
        return GateResult(
            "gate_declared_truth_shape",
            "FALSE",
            "declared_scene_truth.scene_id must equal packet.scene_id",
        )

    scene_status = declared_scene_truth.get("status")
    if scene_status not in VALID_TRUTH_STATUSES:
        return GateResult(
            "gate_declared_truth_shape",
            "FALSE",
            f"declared_scene_truth.status must be one of {VALID_TRUTH_STATUSES}, got: {scene_status}",
        )

    # Validate declared_entity_truth
    declared_entity_truth = packet.get("declared_entity_truth")
    if not isinstance(declared_entity_truth, list):
        return GateResult(
            "gate_declared_truth_shape",
            "FALSE",
            "declared_entity_truth must be a list",
        )

    for idx, entity in enumerate(declared_entity_truth):
        if not isinstance(entity, dict):
            return GateResult(
                "gate_declared_truth_shape",
                "FALSE",
                f"Entity at index {idx} must be a dict",
            )

        entity_id = entity.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id.strip():
            return GateResult(
                "gate_declared_truth_shape",
                "FALSE",
                f"Entity at index {idx} entity_id must be a non-empty string",
            )

        entity_status = entity.get("status")
        if entity_status not in VALID_TRUTH_STATUSES:
            return GateResult(
                "gate_declared_truth_shape",
                "FALSE",
                f"Entity at index {idx} status must be one of {VALID_TRUTH_STATUSES}, got: {entity_status}",
            )

    return GateResult(
        "gate_declared_truth_shape",
        "TRUE",
        "Declared truth shape is valid",
    )
