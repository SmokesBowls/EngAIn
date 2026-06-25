# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/gates/gate_scene_mood_valid_if_present.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_scene_mood_valid_if_present(packet: dict[str, Any]) -> GateResult:
    scene_mood = packet.get("scene_mood")

    if scene_mood is None:
        return GateResult(
            "gate_scene_mood_valid_if_present",
            "SKIPPED",
            "scene_mood inspected: optional field absent, no claim made",
        )

    if not isinstance(scene_mood, dict):
        return GateResult(
            "gate_scene_mood_valid_if_present",
            "FALSE",
            "scene_mood must be a dict",
        )

    dominant = scene_mood.get("dominant")
    intensity = scene_mood.get("intensity")

    if not isinstance(dominant, str) or not dominant.strip():
        return GateResult(
            "gate_scene_mood_valid_if_present",
            "FALSE",
            "scene_mood.dominant must be a non-empty string",
        )

    if not isinstance(intensity, (int, float)):
        return GateResult(
            "gate_scene_mood_valid_if_present",
            "FALSE",
            "scene_mood.intensity must be numeric",
        )

    if not 0.0 <= intensity <= 1.0:
        return GateResult(
            "gate_scene_mood_valid_if_present",
            "FALSE",
            f"scene_mood.intensity out of bounds [0.0, 1.0]: {intensity}",
        )

    return GateResult(
        "gate_scene_mood_valid_if_present",
        "TRUE",
        "scene_mood validated successfully",
    )