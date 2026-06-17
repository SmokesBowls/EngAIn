# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/gates/gate_relationship_deltas_valid_if_present.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_relationship_deltas_valid_if_present(packet: dict[str, Any]) -> GateResult:
    any_present = False

    for entity in packet.get("entities", []):
        entity_id = entity.get("entity_id", "UNKNOWN_ENTITY")
        rel_deltas = entity.get("relationship_deltas")

        if rel_deltas is None:
            continue

        any_present = True

        if not isinstance(rel_deltas, list):
            return GateResult(
                "gate_relationship_deltas_valid_if_present",
                "FALSE",
                f"relationship_deltas for {entity_id} must be a list",
            )

        for rel in rel_deltas:
            if not isinstance(rel, dict):
                return GateResult(
                    "gate_relationship_deltas_valid_if_present",
                    "FALSE",
                    f"relationship_delta for {entity_id} must be a dict",
                )

            for required_key in ("target_id", "axis", "delta"):
                if required_key not in rel:
                    return GateResult(
                        "gate_relationship_deltas_valid_if_present",
                        "FALSE",
                        f"relationship_delta for {entity_id} missing {required_key}",
                    )

            if not isinstance(rel["target_id"], str) or not rel["target_id"].strip():
                return GateResult(
                    "gate_relationship_deltas_valid_if_present",
                    "FALSE",
                    f"target_id for {entity_id} must be a non-empty string",
                )

            if not isinstance(rel["axis"], str) or not rel["axis"].strip():
                return GateResult(
                    "gate_relationship_deltas_valid_if_present",
                    "FALSE",
                    f"axis for {entity_id} must be a non-empty string",
                )

            if not isinstance(rel["delta"], (int, float)):
                return GateResult(
                    "gate_relationship_deltas_valid_if_present",
                    "FALSE",
                    f"relationship delta for {entity_id} must be numeric",
                )

            if not -1.0 <= rel["delta"] <= 1.0:
                return GateResult(
                    "gate_relationship_deltas_valid_if_present",
                    "FALSE",
                    f"relationship delta for {entity_id} out of bounds [-1.0, 1.0]: {rel['delta']}",
                )

    if not any_present:
        return GateResult(
            "gate_relationship_deltas_valid_if_present",
            "SKIPPED",
            "relationship_deltas inspected: optional field absent, no claim made",
        )

    return GateResult(
        "gate_relationship_deltas_valid_if_present",
        "TRUE",
        "relationship_deltas validated successfully",
    )