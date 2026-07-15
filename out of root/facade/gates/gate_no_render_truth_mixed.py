# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_no_render_truth_mixed.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_RENDER_KEYS = {
    "render",
    "display",
    "viewport",
    "shader",
    "material",
    "lighting",
    "post_process",
    "ui_layout",
    "godot_scene",
    "final_art",
    "render_asset",
    "rendered_assets",
}


def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)


def gate_no_render_truth_mixed(packet: dict[str, Any]) -> GateResult:
    """Validate no render truth is mixed into world-state packets."""
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    render_keys = sorted(all_keys.intersection(FORBIDDEN_RENDER_KEYS))

    if render_keys:
        return GateResult(
            "gate_no_render_truth_mixed",
            "FALSE",
            f"HARD REJECT: render truth keys found in Facade Witness packet: {render_keys}",
        )

    return GateResult(
        "gate_no_render_truth_mixed",
        "TRUE",
        "No render truth mixed into Facade Witness packet",
    )