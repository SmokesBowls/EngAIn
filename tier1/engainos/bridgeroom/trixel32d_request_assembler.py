# trixel32d_request_assembler.py — EngAInOS request assembly for the trixel3.2d seam.
#
# "EngAInOS needs his crew to tell him these" (TRIXEL_ENGAINOS_FINAL_HANDSHAKE.md).
# This module is where the crew's contributions meet:
#
#   WorldField      → worldfield_grid_facts.v1 (per-cell elevation/terrain/recipe)
#   Cartographer    → authorized metric grant (cell metrics, vertical rule)
#   Topologist/
#   Cartographer/
#   MettaExt        → provenance (source scene id, artifact ids, hashes)
#   EngAInOS        → contract identity, doctrine orientation constants,
#                     construction policy (topology/gap-fill/ordering/appearance)
#
# Output: ONE fail-closed trixel32d_surface_request, self-checked against the
# existing validator gate (gates/gate_trixel32d_handshake.py) before release.
#
# Doctrine:
#   - The assembler JOINS declared inputs; it never invents values. Colors come
#     from the declared construction_policy.recipe_base_colors table, never from
#     the assembler's imagination.
#   - Fail closed: incomplete or contradictory provider data → REJECTED with
#     every reason listed. No silent defaults.
#   - Unmapped terrain (recipe null) → REJECTED, reasons name the terrains.
#     Unmapped names stay visible and are never guessed.
#   - request_id is a deterministic content hash — same inputs, same identity.

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

try:
    from tier1.engainos.gates.gate_trixel32d_handshake import (
        validate_trixel32d_surface_request,
    )
except ImportError:  # script-mode fallback
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gates"))
    from gate_trixel32d_handshake import validate_trixel32d_surface_request


ASSEMBLED = "ASSEMBLED"
REJECTED = "REJECTED"

REQUEST_CONTRACT = "trixel32d_surface_request.v1"

# Doctrine orientation constants — owned by the contract, stamped by EngAInOS.
# cross(right, forward) == up (right-handed, Y-up):
#   cross([1,0,0], [0,0,-1]) == [0,1,0]
DOCTRINE_ORIENTATION: dict[str, Any] = {
    "basis_authority": "VECTORS",
    "field_axis_binding": {
        "field_x_increases_along": "RIGHT",
        "field_y_increases_along": "FORWARD",
    },
    "vectors": {
        "forward": [0.0, 0.0, -1.0],
        "right": [1.0, 0.0, 0.0],
        "up": [0.0, 1.0, 0.0],
    },
    "tolerance": 0.0001,
}

# Trixel-supported policies the assembler will accept. Extending this set is a
# contract change, not a call-site convenience.
SUPPORTED_TOPOLOGY_POLICIES = frozenset({"HEIGHT_FIELD_CELL_EXTRUSION"})
SUPPORTED_ORDERING = "ROW_MAJOR"
SUPPORTED_APPEARANCE_POLICY = "RECIPE_REFERENCE"
SUPPORTED_VERTICAL_RULES = frozenset({"ELEVATION_TIMES_MAX_HEIGHT_LAYERS"})


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_str(node: dict, key: str, where: str, reasons: list[str]) -> str | None:
    value = node.get(key)
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"{where}.{key} missing or empty")
        return None
    return value


def _require_positive_number(node: dict, key: str, where: str, reasons: list[str]):
    value = node.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        reasons.append(f"{where}.{key} must be a positive finite number")
        return None
    return value


def assemble_surface_request(
    grid_facts: dict[str, Any],
    metric_grant: dict[str, Any],
    provenance: dict[str, Any],
    construction_policy: dict[str, Any],
) -> tuple[str, dict[str, Any] | None, list[str]]:
    """
    Combine crew contributions into one validated trixel32d_surface_request.

    Returns (status, request_or_none, reasons).
    status == ASSEMBLED: request passed the trixel32d validator gate.
    status == REJECTED:  request is None; reasons list every failure found.
    """
    reasons: list[str] = []

    # ── 1. WorldField grid facts ────────────────────────────────────────────
    if not isinstance(grid_facts, dict) or grid_facts.get("packet_type") != "worldfield_grid_facts":
        return REJECTED, None, ["grid_facts.packet_type must be 'worldfield_grid_facts'"]
    if grid_facts.get("version") != "worldfield_grid_facts.v1":
        reasons.append("grid_facts.version must be 'worldfield_grid_facts.v1'")
    if grid_facts.get("field_coverage") != "DENSE":
        reasons.append("grid_facts.field_coverage must be 'DENSE'")

    width = grid_facts.get("width")
    height = grid_facts.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        reasons.append("grid_facts.width must be a positive integer")
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        reasons.append("grid_facts.height must be a positive integer")

    cells = grid_facts.get("cells")
    if not isinstance(cells, list):
        reasons.append("grid_facts.cells must be a list")
    if reasons:
        return REJECTED, None, reasons

    if len(cells) != width * height:
        reasons.append(
            f"grid_facts.cells length ({len(cells)}) != width*height ({width * height})"
        )

    unmapped: set[str] = set()
    used_recipes: set[str] = set()
    for idx, cell in enumerate(cells):
        expected_x = idx % width
        expected_y = idx // width
        if cell.get("field_x") != expected_x or cell.get("field_y") != expected_y:
            reasons.append(
                f"grid_facts.cells[{idx}] violates row-major order: "
                f"got ({cell.get('field_x')},{cell.get('field_y')}), "
                f"expected ({expected_x},{expected_y})"
            )
            break
        elev = cell.get("elevation")
        if not isinstance(elev, (int, float)) or isinstance(elev, bool) or not math.isfinite(elev) or not (0.0 <= elev <= 1.0):
            reasons.append(f"grid_facts.cells[{idx}].elevation must be finite in [0.0, 1.0]")
        terrain = cell.get("terrain")
        if not isinstance(terrain, str) or not terrain:
            reasons.append(f"grid_facts.cells[{idx}].terrain missing")
        recipe = cell.get("recipe")
        if recipe is None:
            unmapped.add(str(terrain))
        elif isinstance(recipe, str) and recipe:
            used_recipes.add(recipe)
        else:
            reasons.append(f"grid_facts.cells[{idx}].recipe must be a non-empty string or null")

    if unmapped:
        reasons.append(
            "unmapped terrain names (recipe=null) — never guessed, request refused: "
            + ", ".join(sorted(unmapped))
        )

    # ── 2. Cartographer metric grant ────────────────────────────────────────
    if not isinstance(metric_grant, dict):
        reasons.append("metric_grant must be a dict")
        metric_grant = {}
    if metric_grant.get("granted_by") != "cartographer":
        reasons.append("metric_grant.granted_by must be 'cartographer' (metric authority)")
    if metric_grant.get("unit") != "meter":
        reasons.append("metric_grant.unit must be 'meter'")
    cell_width = _require_positive_number(metric_grant, "cell_width", "metric_grant", reasons)
    cell_depth = _require_positive_number(metric_grant, "cell_depth", "metric_grant", reasons)
    max_layers = _require_positive_number(metric_grant, "max_height_layers", "metric_grant", reasons)
    vertical_rule = metric_grant.get("vertical_measurement_rule")
    if vertical_rule not in SUPPORTED_VERTICAL_RULES:
        reasons.append(
            f"metric_grant.vertical_measurement_rule must be one of {sorted(SUPPORTED_VERTICAL_RULES)}"
        )
    _require_str(metric_grant, "source_artifact_id", "metric_grant", reasons)

    # ── 3. Provenance ───────────────────────────────────────────────────────
    if not isinstance(provenance, dict):
        reasons.append("provenance must be a dict")
        provenance = {}
    _require_str(provenance, "source_scene_id", "provenance", reasons)          # MettaExt identity
    _require_str(provenance, "topology_artifact_id", "provenance", reasons)     # Topologist origin
    _require_str(provenance, "metric_layout_artifact_id", "provenance", reasons)  # Cartographer artifact

    # ── 4. Construction policy ──────────────────────────────────────────────
    if not isinstance(construction_policy, dict):
        reasons.append("construction_policy must be a dict")
        construction_policy = {}
    topology_policy = construction_policy.get("topology_policy")
    if topology_policy not in SUPPORTED_TOPOLOGY_POLICIES:
        reasons.append(
            f"construction_policy.topology_policy must be one of {sorted(SUPPORTED_TOPOLOGY_POLICIES)}"
        )
    if construction_policy.get("ordering") != SUPPORTED_ORDERING:
        reasons.append(f"construction_policy.ordering must be '{SUPPORTED_ORDERING}'")
    if construction_policy.get("appearance_policy") != SUPPORTED_APPEARANCE_POLICY:
        reasons.append(
            f"construction_policy.appearance_policy must be '{SUPPORTED_APPEARANCE_POLICY}'"
        )
    gap_fill = construction_policy.get("gap_fill")
    if not isinstance(gap_fill, dict):
        reasons.append("construction_policy.gap_fill must be a dict (validated by the gate)")

    recipe_colors = construction_policy.get("recipe_base_colors")
    if not isinstance(recipe_colors, dict):
        reasons.append("construction_policy.recipe_base_colors must be a dict of recipe → RGBA")
        recipe_colors = {}
    else:
        for recipe_id in sorted(used_recipes):
            color = recipe_colors.get(recipe_id)
            if not (
                isinstance(color, list) and len(color) == 4
                and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in color)
            ):
                reasons.append(
                    f"construction_policy.recipe_base_colors['{recipe_id}'] missing or not RGBA "
                    "— the assembler never invents colors"
                )

    if reasons:
        return REJECTED, None, reasons

    # ── 5. Build the request (join only — no invention) ─────────────────────
    pixel_field_data = [
        {
            "field_x": cell["field_x"],
            "field_y": cell["field_y"],
            "elevation": float(cell["elevation"]),
            "base_color": list(recipe_colors[cell["recipe"]]),
            "recipe": cell["recipe"],
            "terrain": cell["terrain"],
        }
        for cell in cells
    ]

    request: dict[str, Any] = {
        "packet_type": "trixel32d_surface_request",
        "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
        "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
        "orientation": json.loads(json.dumps(DOCTRINE_ORIENTATION)),
        "planar_config": {
            "field_width_columns": width,
            "field_height_rows": height,
            "field_coverage": "DENSE",
            "cell_width": float(cell_width),
            "cell_depth": float(cell_depth),
            # Deterministic geometric center (matches the contract's 3×2 fixture:
            # center_column=(w-1)/2, center_row=(h-1)/2).
            "center_column": (width - 1) / 2.0,
            "center_row": (height - 1) / 2.0,
        },
        "vertical_metric": {
            "vertical_measurement_rule": vertical_rule,
            "max_height_layers": float(max_layers),
            "unit": "meter",
            "granted_by": "cartographer",
            "source_artifact_id": metric_grant["source_artifact_id"],
        },
        "construction": {
            "topology_policy": topology_policy,
            "ordering": SUPPORTED_ORDERING,
            "appearance_policy": SUPPORTED_APPEARANCE_POLICY,
        },
        "gap_fill": json.loads(json.dumps(gap_fill)),
        "pixel_field_data": pixel_field_data,
    }

    # Deterministic identity: content hash over the assembled body + provenance.
    request_id = "t32dreq_" + _canonical_hash({"body": request, "provenance": provenance})[:16]
    request["identity"] = {
        "contract": REQUEST_CONTRACT,
        "packet_type": "trixel32d_surface_request",
        "request_id": request_id,
        "source_scene_id": provenance["source_scene_id"],
        "provenance": json.loads(json.dumps(provenance)),
        "grid_facts_profile": grid_facts.get("profile"),
    }

    # ── 6. Final self-check against the existing validator gate ─────────────
    gate_errors = validate_trixel32d_surface_request(request)
    if gate_errors:
        return REJECTED, None, [f"final_gate: {e}" for e in gate_errors]

    return ASSEMBLED, request, []
