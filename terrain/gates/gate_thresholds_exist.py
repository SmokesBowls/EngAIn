from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_thresholds_exist(packet: dict[str, Any]) -> GateResult:
    """Validate terrain_thresholds exposes terrain profile mapping and conversion."""
    try:
        from terrain import terrain_thresholds
    except Exception as exc:
        return GateResult(
            "gate_thresholds_exist",
            "FALSE",
            f"Cannot import terrain_thresholds: {type(exc).__name__}: {exc}",
        )

    if not hasattr(terrain_thresholds, "TERRAIN_PROFILES"):
        return GateResult(
            "gate_thresholds_exist",
            "FALSE",
            "terrain_thresholds missing TERRAIN_PROFILES",
        )

    if not hasattr(terrain_thresholds, "value_to_terrain"):
        return GateResult(
            "gate_thresholds_exist",
            "FALSE",
            "terrain_thresholds missing value_to_terrain()",
        )

    profiles = terrain_thresholds.TERRAIN_PROFILES

    if not isinstance(profiles, dict) or not profiles:
        return GateResult(
            "gate_thresholds_exist",
            "FALSE",
            "TERRAIN_PROFILES must be a non-empty dict",
        )

    sample = terrain_thresholds.value_to_terrain(0.05)

    if not isinstance(sample, str) or not sample.strip():
        return GateResult(
            "gate_thresholds_exist",
            "FALSE",
            "value_to_terrain() must return a non-empty terrain string",
        )

    return GateResult(
        "gate_thresholds_exist",
        "TRUE",
        f"terrain_thresholds exposes TERRAIN_PROFILES and value_to_terrain(); sample=0.05 -> {sample}",
    )
