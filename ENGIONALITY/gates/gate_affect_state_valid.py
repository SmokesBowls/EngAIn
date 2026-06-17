# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/gates/gate_affect_state_valid.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


VALID_AFFECT_STATES = {
    "fear",
    "anger",
    "sadness",
    "joy",
    "surprise",
    "disgust",
    "trust",
    "anticipation",
    "guarded",
    "open",
    "strained",
    "loyal",
    "grief",
    "dread",
    "hope",
    "despair",
    "ambiguous",
}


def gate_affect_state_present_and_valid(packet: dict[str, Any]) -> GateResult:
    for entity in packet.get("entities", []):
        entity_id = entity.get("entity_id", "UNKNOWN_ENTITY")
        affect_state = entity.get("affect_state")

        if affect_state is None:
            return GateResult(
                "gate_affect_state_present_and_valid",
                "FALSE",
                f"Missing affect_state for {entity_id}",
            )

        if not isinstance(affect_state, str) or not affect_state.strip():
            return GateResult(
                "gate_affect_state_present_and_valid",
                "FALSE",
                f"affect_state for {entity_id} must be a non-empty string",
            )

        if affect_state not in VALID_AFFECT_STATES:
            return GateResult(
                "gate_affect_state_present_and_valid",
                "FALSE",
                f"Unknown affect_state for {entity_id}: {affect_state}",
            )

    return GateResult(
        "gate_affect_state_present_and_valid",
        "TRUE",
        "All entities have valid affect_state values",
    )