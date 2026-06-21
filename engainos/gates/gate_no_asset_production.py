
# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_no_asset_production.py

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

from typing import Any

from engain_control.gate_result import GateResult

ASSET_PRODUCTION_KEYS = {
    "asset_id",
    "mesh_id",
    "texture_id",
    "atlas",
    "skin",
    "recipe",
    "manifest",
    "provenance",
    "asset_supersession",
    "blend_file",
    "gltf_export",
    "texture_bake",
    "mesh_generation",
}

def _collect_keys(value: Any, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            _collect_keys(child, found)
    elif isinstance(value, list):
        for child in value:
            _collect_keys(child, found)

def gate_no_asset_production(packet: dict[str, Any]) -> GateResult:
    """
    EngAInOS does not own asset production.
    Trixel owns asset truth.
    """
    all_keys: set[str] = set()
    _collect_keys(packet, all_keys)

    asset_keys = sorted(all_keys.intersection(ASSET_PRODUCTION_KEYS))

    if asset_keys:
        return GateResult(
            "gate_no_asset_production",
            "FALSE",
            f"HARD REJECT: EngAInOS contains asset production keys: {asset_keys}",
        )

    return GateResult(
        "gate_no_asset_production",
        "TRUE",
        "No asset production authority found",
    )
