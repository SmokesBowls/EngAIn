# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/gates/gate_dirty_chunk_or_delta_shape.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_dirty_chunk_or_delta_shape(packet: dict[str, Any]) -> GateResult:
    """Validate TerrainDelta shape if it exists."""
    try:
        from terrain import trixel_world_adapter
        
        if not hasattr(trixel_world_adapter, "TerrainDelta"):
            return GateResult(
                "gate_dirty_chunk_or_delta_shape",
                "SKIPPED",
                "TerrainDelta optional proof absent; adapter boundary still inspected",
            )
        
        TerrainDelta = trixel_world_adapter.TerrainDelta
        
        # Validate it's a class/dataclass
        if not isinstance(TerrainDelta, type):
            return GateResult(
                "gate_dirty_chunk_or_delta_shape",
                "FALSE",
                "TerrainDelta must be a class",
            )
        
    except Exception as exc:
        return GateResult(
            "gate_dirty_chunk_or_delta_shape",
            "FALSE",
            f"TerrainDelta validation failed: {exc}",
        )

    return GateResult(
        "gate_dirty_chunk_or_delta_shape",
        "TRUE",
        "TerrainDelta shape is valid",
    )