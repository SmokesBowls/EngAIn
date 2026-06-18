# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/gates/gate_no_authority_overreach.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_KEYS = {
    "canon_truth",
    "acceptance_decision",
    "ap_allowed_true",
    "render",
    "display",
    "final_art",
    "asset_truth",
    "authoritative",
    "position",
    "velocity",
    "affect_state",
    "claims",
    "contradictions",
}


def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)


def gate_no_authority_overreach(packet: dict[str, Any]) -> GateResult:
    """Validate terrain packet contains no forbidden authority keys."""
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    stolen_keys = sorted(all_keys.intersection(FORBIDDEN_KEYS))

    if stolen_keys:
        return GateResult(
            "gate_no_authority_overreach",
            "FALSE",
            f"HARD REJECT: terrain packet contains forbidden authority keys: {stolen_keys}",
        )

    return GateResult(
        "gate_no_authority_overreach",
        "TRUE",
        "Terrain packet is clean of forbidden authority keys",
    )