
# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_no_simulation_execution.py

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

from typing import Any

from engain_control.gate_result import GateResult

SIMULATION_EXECUTION_KEYS = {
    "position",
    "velocity",
    "collision",
    "physics_step",
    "sim_tick",
    "spatial_update",
    "movement",
    "reachability",
    "blocked_paths",
    "navigation_state",
}

def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)

def gate_no_simulation_execution(packet: dict[str, Any]) -> GateResult:
    """
    EngAInOS does not execute simulation.
    GodotSim owns simulation execution.
    """
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    sim_keys = sorted(all_keys.intersection(SIMULATION_EXECUTION_KEYS))

    if sim_keys:
        return GateResult(
            "gate_no_simulation_execution",
            "FALSE",
            f"HARD REJECT: EngAInOS contains simulation execution keys: {sim_keys}",
        )

    return GateResult(
        "gate_no_simulation_execution",
        "TRUE",
        "No simulation execution authority found",
    )
