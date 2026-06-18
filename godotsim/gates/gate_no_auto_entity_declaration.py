# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_no_auto_entity_declaration.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


ENTITY_DECLARATION_KEYS = {
    "spawn",
    "despawn",
    "create_entity",
    "destroy_entity",
    "new_entity",
    "entity_declaration",
    "declare_entity",
}


def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)


def gate_no_auto_entity_declaration(packet: dict[str, Any]) -> GateResult:
    """
    GodotSim may not declare new entities.
    Entity declaration authority belongs to EngAInOS.
    """
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    declaration_keys = sorted(all_keys.intersection(ENTITY_DECLARATION_KEYS))

    if declaration_keys:
        return GateResult(
            "gate_no_auto_entity_declaration",
            "FALSE",
            f"HARD REJECT: entity declaration keys found: {declaration_keys}",
        )

    return GateResult(
        "gate_no_auto_entity_declaration",
        "TRUE",
        "Packet contains no entity declaration authority",
    )