# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/gates/gate_world_field_boundary.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_WORLD_FIELD_KEYS = {
    "canon_truth",
    "acceptance_decision",
    "ap_allowed_true",
    "render",
    "display",
    "final_art",
    "asset_truth",
    "affect_state",
    "claims",
    "contradictions",
    "quest_complete",
    "inventory",
}


def gate_world_field_boundary(packet: dict[str, Any]) -> GateResult:
    """Validate WorldField is raw float substrate with no semantic authority."""
    try:
        from terrain import world_field_nucleus
    except Exception as exc:
        return GateResult(
            "gate_world_field_boundary",
            "FALSE",
            f"Cannot import world_field_nucleus: {exc}",
        )

    # Check module-level attributes for forbidden keys
    module_attrs = set(dir(world_field_nucleus))
    stolen_keys = sorted(module_attrs.intersection(FORBIDDEN_WORLD_FIELD_KEYS))

    if stolen_keys:
        return GateResult(
            "gate_world_field_boundary",
            "FALSE",
            f"WorldField contains forbidden authority keys: {stolen_keys}",
        )

    return GateResult(
        "gate_world_field_boundary",
        "TRUE",
        "WorldField is clean of semantic/canon/render authority",
    )