# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_no_lane_theft_in_packet.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_KEYS = {
    # Engionality (affect)
    "affect_state",
    "intensity",
    "stability",
    "persona_state",
    "relationship_deltas",
    "scene_mood",
    # MrLore (canon)
    "canon",
    "canon_truth",
    "canon_approved",
    "review_status",
    "canon_status",
    "claims",
    "contradictions",
    # EngAInOS (authority)
    "ap_allowed",
    "ap_allowed_true",
    "allowed",
    "allowed_true",
    "quest_complete",
    "quest_completion",
    "inventory",
    "health",
    # Trixel/Godot (render)
    "render_asset",
    "rendered_assets",
    "asset_id",
    "mesh_id",
    "texture_id",
}


def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)


def gate_no_lane_theft_in_packet(packet: dict[str, Any]) -> GateResult:
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    stolen_keys = sorted(all_keys.intersection(FORBIDDEN_KEYS))

    if stolen_keys:
        return GateResult(
            "gate_no_lane_theft_in_packet",
            "FALSE",
            f"HARD REJECT: forbidden authority keys found: {stolen_keys}",
        )

    return GateResult(
        "gate_no_lane_theft_in_packet",
        "TRUE",
        "Packet is clean of affect, canon, AP, quest, inventory, health, and render authority keys",
    )