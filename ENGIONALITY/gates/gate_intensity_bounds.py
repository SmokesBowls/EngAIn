# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/gates/gate_intensity_bounds.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_entity_intensity_bounds(packet: dict[str, Any]) -> GateResult:
    entities = packet.get("entities", [])

    for entity in entities:
        entity_id = entity.get("entity_id", "UNKNOWN_ENTITY")
        intensity = entity.get("intensity")

        if intensity is None:
            return GateResult(
                "gate_entity_intensity_bounds",
                "FALSE",
                f"Missing intensity for {entity_id}",
            )

        if not isinstance(intensity, (int, float)):
            return GateResult(
                "gate_entity_intensity_bounds",
                "FALSE",
                f"Intensity for {entity_id} must be numeric",
            )

        if not 0.0 <= intensity <= 1.0:
            return GateResult(
                "gate_entity_intensity_bounds",
                "FALSE",
                f"Intensity {intensity} for {entity_id} out of bounds [0.0, 1.0]",
            )

        stability = entity.get("stability")

        if stability is not None:
            if not isinstance(stability, (int, float)):
                return GateResult(
                    "gate_entity_intensity_bounds",
                    "FALSE",
                    f"Stability for {entity_id} must be numeric when present",
                )

            if not 0.0 <= stability <= 1.0:
                return GateResult(
                    "gate_entity_intensity_bounds",
                    "FALSE",
                    f"Stability {stability} for {entity_id} out of bounds [0.0, 1.0]",
                )

    return GateResult(
        "gate_entity_intensity_bounds",
        "TRUE",
        "All intensity and stability values are within [0.0, 1.0]",
    )