# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/gates/gate_required_fields.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_contract_and_source_valid(packet: dict[str, Any]) -> GateResult:
    if packet.get("contract") != "engionality.affect_packet.v1":
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid contract version",
        )

    if packet.get("source") != "engionality":
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


def gate_scene_and_time_present(packet: dict[str, Any]) -> GateResult:
    if "scene_id" not in packet:
        return GateResult(
            "gate_scene_and_time_present",
            "FALSE",
            "Missing scene_id",
        )

    if "tick" not in packet and "time" not in packet:
        return GateResult(
            "gate_scene_and_time_present",
            "FALSE",
            "Missing tick or time",
        )

    return GateResult(
        "gate_scene_and_time_present",
        "TRUE",
        "Scene and time identifiers present",
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