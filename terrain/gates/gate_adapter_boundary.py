# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/gates/gate_adapter_boundary.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_ADAPTER_KEYS = {
    "canon_truth",
    "acceptance_decision",
    "ap_allowed_true",
    "render",
    "display",
    "final_art",
    "asset_truth",
    "position",
    "velocity",
    "affect_state",
    "claims",
    "contradictions",
    "authoritative",
    "godot_render_authority",
}


def gate_adapter_boundary(packet: dict[str, Any]) -> GateResult:
    """Validate adapter translates, not owns state."""
    try:
        from terrain import trixel_world_adapter
    except Exception as exc:
        return GateResult(
            "gate_adapter_boundary",
            "FALSE",
            f"Cannot import trixel_world_adapter: {exc}",
        )

    # Check module-level attributes for forbidden keys
    module_attrs = set(dir(trixel_world_adapter))
    stolen_keys = sorted(module_attrs.intersection(FORBIDDEN_ADAPTER_KEYS))

    if stolen_keys:
        return GateResult(
            "gate_adapter_boundary",
            "FALSE",
            f"Adapter contains forbidden authority keys: {stolen_keys}",
        )

    return GateResult(
        "gate_adapter_boundary",
        "TRUE",
        "Adapter boundary is clean of canon/runtime/render authority",
    )