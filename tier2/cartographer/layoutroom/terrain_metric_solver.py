"""
Cartographer terrain metric grant.

Turns a declared physical measurement basis plus WorldField's grid dimensions
into the metric grant the EngAInOS request assembler requires
(docs/contracts/TRIXEL32D_REQUEST_ASSEMBLY_AND_CONSUMER_v1.md, "Authorized metrics"):

    cell_width  = physical_width_m / grid width   (field_x -> RIGHT)
    cell_depth  = physical_depth_m / grid height  (field_y -> FORWARD)
    max_height_layers = vertical_extent_m          (Trixel: world_cell_y =
                        round(elevation * layers), one layer = one meter up)

Never infers physical extent from cell count, never assumes square cells,
never fills a missing basis. Anything missing or provisional returns a
BLOCKED receipt naming exactly what is absent. Engine-independent: no
recipes, colors, meshes or Trixel payloads.
"""

from __future__ import annotations

import hashlib
import json
from math import isfinite
from typing import Any

GRANT_CONTRACT = "engain.cartographer_terrain_metric_grant.v1"
VERTICAL_RULE = "ELEVATION_TIMES_MAX_HEIGHT_LAYERS"
GRANTED = "GRANTED"
BLOCKED = "BLOCKED"


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) and value > 0


def solve_terrain_metrics(
    grid_facts: dict[str, Any],
    measurement_basis: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return {"status": GRANTED, "grant": {...}} or {"status": BLOCKED, "missing": [...]}."""
    missing: list[str] = []
    width, height = grid_facts.get("width"), grid_facts.get("height")
    if grid_facts.get("packet_type") != "worldfield_grid_facts":
        missing.append("grid_facts.packet_type worldfield_grid_facts")
    for name, value in (("width", width), ("height", height)):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            missing.append(f"grid_facts.{name} positive integer")

    basis = measurement_basis or {}
    if measurement_basis is None:
        missing.append("measurement_basis (no physical measurement basis declared for this scene)")
    else:
        for key in ("basis_id", "source", "scene_id"):
            if not isinstance(basis.get(key), str) or not basis[key].strip():
                missing.append(f"measurement_basis.{key}")
        for key in ("physical_width_m", "physical_depth_m"):
            if not _positive(basis.get(key)):
                missing.append(f"measurement_basis.{key} positive meters")
        vertical = basis.get("vertical_extent_m")
        if not _positive(vertical):
            missing.append("measurement_basis.vertical_extent_m positive meters (vertical scale)")
        elif float(vertical) != int(vertical):
            missing.append("measurement_basis.vertical_extent_m must be whole meters (Trixel layers are integral)")
        if basis.get("basis_status") != "evidence":
            missing.append("measurement_basis.basis_status == 'evidence' (provisional bases cannot authorize construction metrics)")

    if missing:
        return {"status": BLOCKED, "contract": GRANT_CONTRACT, "missing": missing}

    grid_sha256 = _hash(grid_facts)
    grant = {
        "contract": GRANT_CONTRACT,
        "granted_by": "cartographer",
        "unit": "meter",
        "cell_width": float(basis["physical_width_m"]) / width,
        "cell_depth": float(basis["physical_depth_m"]) / height,
        "max_height_layers": int(basis["vertical_extent_m"]),
        "vertical_measurement_rule": VERTICAL_RULE,
        "grid": {"width": width, "height": height, "profile": grid_facts.get("profile"),
                 "grid_facts_sha256": grid_sha256},
        "measurement_basis": {k: basis[k] for k in (
            "basis_id", "source", "scene_id", "basis_status",
            "physical_width_m", "physical_depth_m", "vertical_extent_m")},
    }
    grant["source_artifact_id"] = "terrain_metric." + _hash(grant)[:16]
    return {"status": GRANTED, "grant": grant}
