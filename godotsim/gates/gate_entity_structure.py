# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_entity_structure.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


VALID_COLLISION_ROLES = {"solid", "trigger", "kinematic", "sensor", "static", "dynamic"}


def gate_entity_id_present(packet: dict[str, Any]) -> GateResult:
    for idx, entity in enumerate(packet.get("entities", [])):
        entity_id = entity.get("entity_id")
        if entity_id is None:
            return GateResult(
                "gate_entity_id_present",
                "FALSE",
                f"Entity at index {idx} missing entity_id",
            )
        if not isinstance(entity_id, str) or not entity_id.strip():
            return GateResult(
                "gate_entity_id_present",
                "FALSE",
                f"Entity at index {idx} entity_id must be a non-empty string",
            )

    return GateResult(
        "gate_entity_id_present",
        "TRUE",
        "All entities have valid entity_id",
    )


def gate_position_present_and_valid(packet: dict[str, Any]) -> GateResult:
    for idx, entity in enumerate(packet.get("entities", [])):
        position = entity.get("position")
        if position is None:
            return GateResult(
                "gate_position_present_and_valid",
                "FALSE",
                f"Entity at index {idx} missing required position",
            )

        if not isinstance(position, list):
            return GateResult(
                "gate_position_present_and_valid",
                "FALSE",
                f"Entity at index {idx} position must be a list",
            )

        if len(position) != 3:
            return GateResult(
                "gate_position_present_and_valid",
                "FALSE",
                f"Entity at index {idx} position must have exactly 3 elements [x, y, z]",
            )

        for coord_idx, coord in enumerate(position):
            if type(coord) not in (int, float):
                return GateResult(
                    "gate_position_present_and_valid",
                    "FALSE",
                    f"Entity at index {idx} position[{coord_idx}] must be numeric",
                )

    return GateResult(
        "gate_position_present_and_valid",
        "TRUE",
        "All entities have valid position [x, y, z]",
    )


def gate_collision_role_valid(packet: dict[str, Any]) -> GateResult:
    for idx, entity in enumerate(packet.get("entities", [])):
        collision_role = entity.get("collision_role")
        if collision_role is None:
            return GateResult(
                "gate_collision_role_valid",
                "FALSE",
                f"Entity at index {idx} missing required collision_role",
            )

        if not isinstance(collision_role, str):
            return GateResult(
                "gate_collision_role_valid",
                "FALSE",
                f"Entity at index {idx} collision_role must be a string",
            )

        if collision_role not in VALID_COLLISION_ROLES:
            return GateResult(
                "gate_collision_role_valid",
                "FALSE",
                f"Entity at index {idx} collision_role '{collision_role}' not in {VALID_COLLISION_ROLES}",
            )

    return GateResult(
        "gate_collision_role_valid",
        "TRUE",
        "All entities have valid collision_role",
    )