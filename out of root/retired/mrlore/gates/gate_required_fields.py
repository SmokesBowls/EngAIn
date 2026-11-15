# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/mrlore/gates/gate_required_fields.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_contract_and_source_valid(packet: dict[str, Any]) -> GateResult:
    if packet.get("contract") != "mrlore.canon_review_packet.v1":
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid contract version",
        )

    if packet.get("source") != "mrlore":
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid source",
        )

    if packet.get("authority_tier") != 3:
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid authority tier",
        )

    if packet.get("authority_lane") != "canon_review":
        return GateResult(
            "gate_contract_and_source_valid",
            "FALSE",
            "Invalid authority lane",
        )

    return GateResult(
        "gate_contract_and_source_valid",
        "TRUE",
        "Contract, source, tier, and lane are valid",
    )


def gate_scene_and_source_present(packet: dict[str, Any]) -> GateResult:
    if "scene_id" not in packet:
        return GateResult(
            "gate_scene_and_source_present",
            "FALSE",
            "Missing scene_id",
        )

    if not isinstance(packet["scene_id"], str) or not packet["scene_id"].strip():
        return GateResult(
            "gate_scene_and_source_present",
            "FALSE",
            "scene_id must be a non-empty string",
        )

    if "source_text_id" not in packet:
        return GateResult(
            "gate_scene_and_source_present",
            "FALSE",
            "Missing source_text_id",
        )

    if not isinstance(packet["source_text_id"], str) or not packet["source_text_id"].strip():
        return GateResult(
            "gate_scene_and_source_present",
            "FALSE",
            "source_text_id must be a non-empty string",
        )

    return GateResult(
        "gate_scene_and_source_present",
        "TRUE",
        "scene_id and source_text_id are present and valid",
    )


def gate_claims_array_present(packet: dict[str, Any]) -> GateResult:
    if "claims" not in packet:
        return GateResult(
            "gate_claims_array_present",
            "FALSE",
            "Missing claims array",
        )

    if not isinstance(packet["claims"], list):
        return GateResult(
            "gate_claims_array_present",
            "FALSE",
            "claims must be a list",
        )

    return GateResult(
        "gate_claims_array_present",
        "TRUE",
        "claims array is present and valid",
    )


def gate_human_review_required_present(packet: dict[str, Any]) -> GateResult:
    if "human_review_required" not in packet:
        return GateResult(
            "gate_human_review_required_present",
            "FALSE",
            "Missing human_review_required",
        )

    if not isinstance(packet["human_review_required"], bool):
        return GateResult(
            "gate_human_review_required_present",
            "FALSE",
            "human_review_required must be a boolean",
        )

    return GateResult(
        "gate_human_review_required_present",
        "TRUE",
        "human_review_required is present and boolean",
    )