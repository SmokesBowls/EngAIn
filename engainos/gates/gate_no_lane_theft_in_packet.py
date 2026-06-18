# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_no_lane_theft_in_packet.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_LANE_KEYS = {
    # GodotSim (simulation)
    "position",
    "velocity",
    "collision",
    "sim_tick",
    # Engionality (affect)
    "affect_state",
    "intensity",
    "persona_state",
    "relationship_deltas",
    # MrLore (canon) - but not inside validated_packets references
    "review_status",
    "canon_status",
    "claims",
    "contradictions",
    # Trixel (assets)
    "asset_id",
    "mesh_id",
    "texture_id",
    "atlas",
    # Godot (presentation)
    "render",
    "display",
    "viewport",
}


def _collect_keys(value: Any, found: set[str], skip_keys: set[str] | None = None) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if skip_keys and key in skip_keys:
                continue
            found.add(str(key))
            _collect_keys(child, found, skip_keys)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found, skip_keys)


def gate_no_lane_theft_in_packet(packet: dict[str, Any]) -> GateResult:
    all_keys: set[str] = set()
    # Skip validated_packets because it only contains references (source, contract, result)
    _collect_keys(packet, all_keys, skip_keys={"validated_packets"})

    stolen_keys = sorted(all_keys.intersection(FORBIDDEN_LANE_KEYS))

    if stolen_keys:
        return GateResult(
            "gate_no_lane_theft_in_packet",
            "FALSE",
            f"HARD REJECT: EngAInOS contains forbidden lane keys: {stolen_keys}",
        )

    return GateResult(
        "gate_no_lane_theft_in_packet",
        "TRUE",
        "No lane theft detected",
    )