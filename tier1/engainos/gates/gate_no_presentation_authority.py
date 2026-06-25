
# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_no_presentation_authority.py

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

from typing import Any

from engain_control.gate_result import GateResult

PRESENTATION_AUTHORITY_KEYS = {
    "render",
    "display",
    "compose",
    "viewport",
    "camera",
    "shader",
    "material",
    "lighting",
    "post_process",
    "ui_layout",
    "godot_scene",
}

def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)

def gate_no_presentation_authority(packet: dict[str, Any]) -> GateResult:
    """
    EngAInOS does not own presentation.
    Godot owns presentation.
    """
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    presentation_keys = sorted(all_keys.intersection(PRESENTATION_AUTHORITY_KEYS))

    if presentation_keys:
        return GateResult(
            "gate_no_presentation_authority",
            "FALSE",
            f"HARD REJECT: EngAInOS contains presentation authority keys: {presentation_keys}",
        )

    return GateResult(
        "gate_no_presentation_authority",
        "TRUE",
        "No presentation authority found",
    )
