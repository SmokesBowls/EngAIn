# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_required_fields.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_contract_and_source_valid(packet: dict[str, Any]) -> GateResult:
    if packet.get("contract") != "godotsim.spatial_sim_packet.v1":
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid contract version",
        )

    if packet.get("source") != "godotsim":
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid source",
        )

    if packet.get("authority_tier") != 2:
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid authority tier",
        )

    return GateResult(
        "gate_contract_and_source_valid",
        "TRUE",
        "Contract, source, and tier are valid",
    )


def gate_scene_and_tick_present(packet: dict[str, Any]) -> GateResult:
    if "scene_id" not in packet:
        return GateResult(
            "gate_scene_and_tick_present",
            "FALSE",
            "Missing scene_id",
        )

    if not isinstance(packet["scene_id"], str) or not packet["scene_id"].strip():
        return GateResult(
            "gate_scene_and_tick_present",
            "FALSE",
            "scene_id must be a non-empty string",
        )

    if "sim_tick" not in packet and "time" not in packet:
        return GateResult(
            "gate_scene_and_tick_present",
            "FALSE",
            "Missing sim_tick or time",
        )

    # STRICT TYPE CHECK: type(...) is int, not isinstance(..., int)
    # bool is a subclass of int in Python, so True/False can accidentally pass isinstance checks.
    if "sim_tick" in packet and type(packet["sim_tick"]) is not int:
        return GateResult(
            "gate_scene_and_tick_present",
            "FALSE",
            "sim_tick must be an integer",
        )

    if "time" in packet and type(packet["time"]) not in (int, float):
        return GateResult(
            "gate_scene_and_tick_present",
            "FALSE",
            "time must be numeric",
        )

    return GateResult(
        "gate_scene_and_tick_present",
        "TRUE",
        "scene_id and sim_tick/time are present and correctly typed",
    )


def gate_entities_array_present(packet: dict[str, Any]) -> GateResult:
    if "entities" not in packet:
        return GateResult(
            "gate_entities_array_present",
            "FALSE",
            "Missing entities array",
        )

    if not isinstance(packet["entities"], list):
        return GateResult(
            "gate_entities_array_present",
            "FALSE",
            "entities must be a list",
        )

    return GateResult(
        "gate_entities_array_present",
        "TRUE",
        "entities array is present and valid",
    )