# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/gates/gate_imports.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_imports(packet: dict[str, Any]) -> GateResult:
    """Validate all terrain modules can be imported."""
    try:
        import terrain.world_field_nucleus
        import terrain.terrain_thresholds
        import terrain.trixel_world_adapter
    except Exception as exc:
        return GateResult(
            "gate_imports",
            "FALSE",
            f"Import failed: {type(exc).__name__}: {exc}",
        )

    return GateResult(
        "gate_imports",
        "TRUE",
        "All terrain modules imported successfully",
    )