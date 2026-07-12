from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"

import sys
import math
import json
from pathlib import Path
from typing import Any

# Configure paths to ensure imports resolve correctly
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
from dataclasses import dataclass

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: str
    message: str
    def is_true(self) -> bool: return self.passed == "TRUE"
    def is_false(self) -> bool: return self.passed == "FALSE"
    def is_skipped(self) -> bool: return self.passed == "SKIPPED"


def validate_trixel32d_surface_request(packet: dict[str, Any]) -> list[str]:
    """Validate trixel32d_surface_request payload format and values (fail-fast order)."""
    errors = []

    # 1. Contract identifier
    if packet.get("packet_type") != "trixel32d_surface_request":
        errors.append("Invalid packet_type: expected 'trixel32d_surface_request'")
        return errors

    # 2. Coordinate space policy
    if packet.get("coordinate_space") != "WORLD_FIELD_GRID_TO_LOCAL_Y_UP":
        errors.append("Invalid coordinate_space: must be 'WORLD_FIELD_GRID_TO_LOCAL_Y_UP'")
    if packet.get("up_axis_policy") != "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION":
        errors.append("Invalid up_axis_policy: must be 'MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION'")

    # 3. Finiteness of all values
    # Check orientation
    orientation = packet.get("orientation")
    if not isinstance(orientation, dict):
        errors.append("Missing or invalid 'orientation' node")
        return errors

    if orientation.get("basis_authority") != "VECTORS":
        errors.append("Invalid basis_authority: expected 'VECTORS'")

    binding = orientation.get("field_axis_binding")
    if not isinstance(binding, dict):
        errors.append("Missing or invalid 'field_axis_binding'")
    else:
        if binding.get("field_x_increases_along") != "RIGHT":
            errors.append("field_x_increases_along must be 'RIGHT'")
        if binding.get("field_y_increases_along") != "FORWARD":
            errors.append("field_y_increases_along must be 'FORWARD'")

    vectors = orientation.get("vectors")
    if not isinstance(vectors, dict):
        errors.append("Missing or invalid 'vectors' in orientation")
        return errors

    forward = vectors.get("forward")
    right = vectors.get("right")
    up = vectors.get("up")
    tolerance = float(orientation.get("tolerance", 0.0001))

    for name, vec in [("forward", forward), ("right", right), ("up", up)]:
        if not isinstance(vec, list) or len(vec) != 3:
            errors.append(f"Vector '{name}' must be a list of 3 coordinates")
            continue
        for val in vec:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                errors.append(f"Vector '{name}' contains non-numeric component: {val}")
            elif not math.isfinite(val):
                errors.append(f"Vector '{name}' contains non-finite component")

    if errors:
        return errors

    # Vector geometry mathematical validations
    def length(v: list[float]) -> float:
        return math.sqrt(sum(x*x for x in v))

    def dot(v1: list[float], v2: list[float]) -> float:
        return sum(x*y for x, y in zip(v1, v2))

    def cross(v1: list[float], v2: list[float]) -> list[float]:
        return [
            v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]
        ]

    # Raw vector unit length check within tolerance
    for name, vec in [("forward", forward), ("right", right), ("up", up)]:
        l = length(vec)
        if abs(l - 1.0) > tolerance:
            errors.append(f"Vector '{name}' is not unit length within tolerance (length={l:.6f})")

    if errors:
        return errors

    # Normalized Working-Vector Rule: normalize immediately after raw validation
    l_f = length(forward)
    l_r = length(right)
    l_u = length(up)
    
    norm_forward = [f / l_f for f in forward]
    norm_right = [r / l_r for r in right]
    norm_up = [u / l_u for u in up]

    # Orthogonality checks using normalized vectors
    d_rf = dot(norm_right, norm_forward)
    d_ru = dot(norm_right, norm_up)
    d_fu = dot(norm_forward, norm_up)
    if abs(d_rf) > tolerance:
        errors.append(f"Vectors 'right' and 'forward' are not orthogonal (dot={d_rf:.6f})")
    if abs(d_ru) > tolerance:
        errors.append(f"Vectors 'right' and 'up' are not orthogonal (dot={d_ru:.6f})")
    if abs(d_fu) > tolerance:
        errors.append(f"Vectors 'forward' and 'up' are not orthogonal (dot={d_fu:.6f})")

    # Handedness check using normalized vectors
    cr = cross(norm_right, norm_forward)
    diff = length([c - u for c, u in zip(cr, norm_up)])
    if diff > tolerance:
        errors.append(f"Invalid handedness: cross(right, forward) differs from up (diff={diff:.6f})")

    # up axis policy standard check using normalized vectors
    up_diff = length([u - expected for u, expected in zip(norm_up, [0.0, 1.0, 0.0])])
    if up_diff > tolerance:
        errors.append(f"up vector violates Y-up policy (diff={up_diff:.6f})")

    if errors:
        return errors

    # 4. Planar dimensions & cell sizes
    planar = packet.get("planar_config")
    if not isinstance(planar, dict):
        errors.append("Missing or invalid 'planar_config' node")
        return errors

    width = planar.get("field_width_columns")
    height = planar.get("field_height_rows")
    coverage = planar.get("field_coverage")
    cell_w = planar.get("cell_width")
    cell_d = planar.get("cell_depth")
    center_c = planar.get("center_column")
    center_r = planar.get("center_row")

    if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
        errors.append("field_width_columns must be a positive integer")
    if not isinstance(height, int) or isinstance(height, bool) or height <= 0:
        errors.append("field_height_rows must be a positive integer")
    if coverage != "DENSE":
        errors.append("field_coverage must be 'DENSE'")
    if not isinstance(cell_w, (int, float)) or isinstance(cell_w, bool) or cell_w <= 0:
        errors.append("cell_width must be a positive number")
    if not isinstance(cell_d, (int, float)) or isinstance(cell_d, bool) or cell_d <= 0:
        errors.append("cell_depth must be a positive number")
    if not isinstance(center_c, (int, float)) or isinstance(center_c, bool):
        errors.append("center_column must be a number")
    if not isinstance(center_r, (int, float)) or isinstance(center_r, bool):
        errors.append("center_row must be a number")

    if errors:
        return errors

    # 5. Visual policies (gap fill)
    gap_fill = packet.get("gap_fill")
    if not isinstance(gap_fill, dict):
        errors.append("Missing or invalid 'gap_fill' node")
        return errors

    enabled = gap_fill.get("enabled")
    mode = gap_fill.get("mode")
    adjacency = gap_fill.get("adjacency_policy")
    color = gap_fill.get("resolved_color")
    thickness = gap_fill.get("thickness_local_units")

    if not isinstance(enabled, bool):
        errors.append("gap_fill.enabled must be a boolean")
    if mode != "PER_CELL_EXTRUSION":
        errors.append("gap_fill.mode must be 'PER_CELL_EXTRUSION'")
    if adjacency != "ALL_FACES_INDEPENDENT":
        errors.append("gap_fill.adjacency_policy must be 'ALL_FACES_INDEPENDENT'")
    if not isinstance(color, list) or len(color) != 4 or not all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in color):
        errors.append("gap_fill.resolved_color must be a list of 4 float RGBA values")
    if not isinstance(thickness, (int, float)) or isinstance(thickness, bool) or thickness <= 0:
        errors.append("gap_fill.thickness_local_units must be a positive float")

    if errors:
        return errors

    # 6. Planar coverage DENSE checks
    field_data = packet.get("pixel_field_data")
    if not isinstance(field_data, list):
        errors.append("Missing or invalid 'pixel_field_data' list")
        return errors

    expected_len = width * height
    if len(field_data) != expected_len:
        errors.append(f"pixel_field_data length ({len(field_data)}) does not match planar dimensions ({expected_len})")
        return errors

    visited = set()
    for idx, cell in enumerate(field_data):
        if not isinstance(cell, dict):
            errors.append(f"pixel_field_data[{idx}] must be a dict")
            return errors

        fx = cell.get("field_x")
        fy = cell.get("field_y")
        elev = cell.get("elevation")
        base_color = cell.get("base_color")

        # Zero-inclusive, dimension-exclusive checks
        if not isinstance(fx, int) or isinstance(fx, bool) or fx < 0 or fx >= width:
            errors.append(f"pixel_field_data[{idx}].field_x must be from 0 inclusive to {width} exclusive")
        if not isinstance(fy, int) or isinstance(fy, bool) or fy < 0 or fy >= height:
            errors.append(f"pixel_field_data[{idx}].field_y must be from 0 inclusive to {height} exclusive")
        if not isinstance(elev, (int, float)) or isinstance(elev, bool) or not math.isfinite(elev):
            errors.append(f"pixel_field_data[{idx}].elevation must be a finite number")
        if not isinstance(base_color, list) or len(base_color) != 4 or not all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in base_color):
            errors.append(f"pixel_field_data[{idx}].base_color must be a list of 4 float RGBA values")

        if errors:
            return errors

        coord = (fx, fy)
        if coord in visited:
            errors.append(f"Duplicate coordinate detected at index {idx}: {coord}")
            return errors
        visited.add(coord)

    # Coverage completeness
    for x in range(width):
        for y in range(height):
            if (x, y) not in visited:
                errors.append(f"Missing coordinate in DENSE field coverage: ({x}, {y})")
                return errors

    return []


def validate_trixel32d_surface_built(packet: dict[str, Any], request: dict[str, Any] | None = None) -> list[str]:
    """Validate trixel32d_surface_built handshake response."""
    errors = []

    if packet.get("packet_type") != "trixel32d_surface_built":
        errors.append("Invalid packet_type: expected 'trixel32d_surface_built'")
        return errors

    status = packet.get("status")
    if status not in {"BUILT", "REJECTED"}:
        errors.append("status must be 'BUILT' or 'REJECTED'")
        return errors

    # Response local spatial metadata coordinate space check
    meta = packet.get("local_spatial_metadata")
    if not isinstance(meta, dict) or meta.get("coordinate_space") != "TRIXEL_LOCAL_Y_UP":
        errors.append("local_spatial_metadata.coordinate_space must be 'TRIXEL_LOCAL_Y_UP'")

    if status == "REJECTED":
        if packet.get("geometry") is not None:
            errors.append("geometry must be null when status is REJECTED")
        errs = packet.get("errors")
        if not isinstance(errs, list) or len(errs) == 0 or not all(isinstance(e, str) for e in errs):
            errors.append("errors must be a non-empty list of strings when status is REJECTED")
        return errors

    # status == BUILT
    errs = packet.get("errors")
    if errs is not None and (not isinstance(errs, list) or len(errs) > 0):
        errors.append("errors must be empty or null when status is BUILT")

    rejected_cells = packet.get("rejected_cells")
    if not isinstance(rejected_cells, list) or len(rejected_cells) > 0:
        errors.append("rejected_cells must be an empty list when status is BUILT")

    geometry = packet.get("geometry")
    if not isinstance(geometry, dict):
        errors.append("geometry must be a dict when status is BUILT")
        return errors

    cell_ranges = packet.get("cell_geometry_ranges")
    if not isinstance(cell_ranges, list):
        errors.append("cell_geometry_ranges must be a list when status is BUILT")
        return errors

    if request:
        width = request["planar_config"]["field_width_columns"]
        height = request["planar_config"]["field_height_rows"]
        expected_cells = width * height

        if len(cell_ranges) != expected_cells:
            errors.append(f"cell_geometry_ranges length ({len(cell_ranges)}) does not match request ({expected_cells})")
            return errors

        # Verify row-major ordering and cell geometry range details
        idx = 0
        for y in range(height):
            for x in range(width):
                cell = cell_ranges[idx]
                if not isinstance(cell, dict):
                    errors.append(f"cell_geometry_ranges[{idx}] must be a dict")
                    return errors

                # Zero-inclusive, dimension-exclusive boundary assertions
                cx = cell.get("field_x")
                cy = cell.get("field_y")
                if not isinstance(cx, int) or cx < 0 or cx >= width:
                    errors.append(f"cell_geometry_ranges[{idx}].field_x must be from 0 inclusive to {width} exclusive")
                if not isinstance(cy, int) or cy < 0 or cy >= height:
                    errors.append(f"cell_geometry_ranges[{idx}].field_y must be from 0 inclusive to {height} exclusive")

                if cx != x or cy != y:
                    errors.append(f"cell_geometry_ranges[{idx}] coordinate mismatch: expected ({x},{y}), got ({cx},{cy})")

                expected_key = f"{x},{y}"
                if cell.get("cell_key") != expected_key:
                    errors.append(f"cell_geometry_ranges[{idx}].cell_key must be '{expected_key}', got '{cell.get('cell_key')}'")

                # Note: source_cell_ordinal maps to the ordinal of the requested pixel_field_data,
                # which might be scrambled in the input. Let's make sure it is present and numeric.
                if not isinstance(cell.get("source_cell_ordinal"), int):
                    errors.append(f"cell_geometry_ranges[{idx}].source_cell_ordinal must be an integer")

                surfaces = cell.get("surfaces")
                if not isinstance(surfaces, list) or len(surfaces) != 6:
                    errors.append(f"cell_geometry_ranges[{idx}].surfaces must have exactly 6 surfaces")
                    return errors

                # Exact Corrected normative face ordering:
                # 1. PRIMARY_PIXEL_FACE (top)
                # 2. NEUTRAL_GAP_FILL bottom
                # 3. NEUTRAL_GAP_FILL -field_y
                # 4. NEUTRAL_GAP_FILL +field_x
                # 5. NEUTRAL_GAP_FILL +field_y
                # 6. NEUTRAL_GAP_FILL -field_x
                expected_surfaces = [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top"},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom"},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y"},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x"},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y"},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x"}
                ]

                for s_idx, (s, expected) in enumerate(zip(surfaces, expected_surfaces)):
                    if s.get("role") != expected["role"]:
                        errors.append(f"cell_geometry_ranges[{idx}].surfaces[{s_idx}].role must be '{expected['role']}'")
                    if s.get("face") != expected["face"]:
                        errors.append(f"cell_geometry_ranges[{idx}].surfaces[{s_idx}].face must be '{expected['face']}'")

                    v_start = s.get("vertex_start")
                    v_count = s.get("vertex_count")
                    i_start = s.get("index_start")
                    i_count = s.get("index_count")

                    if not isinstance(v_start, int) or v_start < 0:
                        errors.append(f"cell_geometry_ranges[{idx}].surfaces[{s_idx}].vertex_start must be a non-negative integer")
                    if not isinstance(v_count, int) or v_count <= 0:
                        errors.append(f"cell_geometry_ranges[{idx}].surfaces[{s_idx}].vertex_count must be a positive integer")
                    if not isinstance(i_start, int) or i_start < 0:
                        errors.append(f"cell_geometry_ranges[{idx}].surfaces[{s_idx}].index_start must be a non-negative integer")
                    if not isinstance(i_count, int) or i_count <= 0:
                        errors.append(f"cell_geometry_ranges[{idx}].surfaces[{s_idx}].index_count must be a positive integer")
                idx += 1

    return errors


def gate_trixel32d_handshake(packet: dict[str, Any]) -> GateResult:
    """Active EngAInOS gate wrapper."""
    packet_type = packet.get("packet_type")

    if packet_type == "trixel32d_surface_request":
        errors = validate_trixel32d_surface_request(packet)
        if errors:
            return GateResult(
                "gate_trixel32d_handshake",
                "FALSE",
                f"Request validation failed: {errors[0]} (total errors: {len(errors)})",
            )
        return GateResult(
            "gate_trixel32d_handshake",
            "TRUE",
            "Trixel 3.2D surface request is valid and orthoseamed",
        )

    elif packet_type == "trixel32d_surface_built":
        request = packet.get("request_context")
        errors = validate_trixel32d_surface_built(packet, request)
        if errors:
            return GateResult(
                "gate_trixel32d_handshake",
                "FALSE",
                f"Response/built validation failed: {errors[0]} (total errors: {len(errors)})",
            )
        return GateResult(
            "gate_trixel32d_handshake",
            "TRUE",
            "Trixel 3.2D surface built response is valid and orthoseamed",
        )

    return GateResult(
        "gate_trixel32d_handshake",
        "SKIPPED",
        f"Packet type '{packet_type}' is not a trixel32d surface handshake packet",
    )


def main() -> int:
    # 3x2 Proof Fixture Request
    fixture_request = {
        "packet_type": "trixel32d_surface_request",
        "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
        "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
        "orientation": {
            "basis_authority": "VECTORS",
            "field_axis_binding": {
                "field_x_increases_along": "RIGHT",
                "field_y_increases_along": "FORWARD"
            },
            "vectors": {
                "forward": [0.70710678, 0.0, -0.70710678],
                "right": [0.70710678, 0.0, 0.70710678],
                "up": [0.0, 1.0, 0.0]
            },
            "tolerance": 0.0001
        },
        "planar_config": {
            "field_width_columns": 3,
            "field_height_rows": 2,
            "field_coverage": "DENSE",
            "cell_width": 0.1,
            "cell_depth": 0.1,
            "center_column": 1.0,
            "center_row": 0.5
        },
        "gap_fill": {
            "enabled": True,
            "mode": "PER_CELL_EXTRUSION",
            "adjacency_policy": "ALL_FACES_INDEPENDENT",
            "resolved_color": [0.35, 0.35, 0.35, 1.0],
            "thickness_local_units": 0.025
        },
        "pixel_field_data": [
            {"field_x": 0, "field_y": 0, "elevation": 1.0, "base_color": [1.0, 0.0, 0.0, 1.0]},
            {"field_x": 0, "field_y": 1, "elevation": 4.0, "base_color": [0.0, 0.0, 1.0, 1.0]},
            {"field_x": 1, "field_y": 0, "elevation": 2.0, "base_color": [0.0, 1.0, 0.0, 1.0]},
            {"field_x": 1, "field_y": 1, "elevation": 5.0, "base_color": [1.0, 1.0, 0.0, 1.0]},
            {"field_x": 2, "field_y": 0, "elevation": 3.0, "base_color": [1.0, 0.0, 1.0, 1.0]},
            {"field_x": 2, "field_y": 1, "elevation": 6.0, "base_color": [0.0, 1.0, 1.0, 1.0]}
        ]
    }

    # Built Mock Response
    fixture_built = {
        "packet_type": "trixel32d_surface_built",
        "status": "BUILT",
        "local_spatial_metadata": {
            "coordinate_space": "TRIXEL_LOCAL_Y_UP"
        },
        "rejected_cells": [],
        "errors": [],
        "geometry": {
            "vertices": [[0,0,0], [1,0,0]],
            "indices": [0, 1]
        },
        "cell_geometry_ranges": [
            {
                "cell_key": "0,0",
                "source_cell_ordinal": 0,
                "field_x": 0,
                "field_y": 0,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6}
                ]
            },
            {
                "cell_key": "1,0",
                "source_cell_ordinal": 2, # Note: ordinal matches the original request array index, which matches 1,0
                "field_x": 1,
                "field_y": 0,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6}
                ]
            },
            {
                "cell_key": "2,0",
                "source_cell_ordinal": 4,
                "field_x": 2,
                "field_y": 0,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6}
                ]
            },
            {
                "cell_key": "0,1",
                "source_cell_ordinal": 1,
                "field_x": 0,
                "field_y": 1,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6}
                ]
            },
            {
                "cell_key": "1,1",
                "source_cell_ordinal": 3,
                "field_x": 1,
                "field_y": 1,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6}
                ]
            },
            {
                "cell_key": "2,1",
                "source_cell_ordinal": 5,
                "field_x": 2,
                "field_y": 1,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 0, "vertex_count": 4, "index_start": 0, "index_count": 6}
                ]
            }
        ]
    }

    # Run validations
    r_res = gate_trixel32d_handshake(fixture_request)
    
    # embed request context inside the built packet
    fixture_built["request_context"] = fixture_request
    b_res = gate_trixel32d_handshake(fixture_built)

    passed = r_res.is_true() and b_res.is_true()

    report = {
        "gate_id": "TRIXEL32D_HANDSHAKE_SPINE_002",
        "lifecycle": GATE_LIFECYCLE,
        "board": GATE_BOARD,
        "request_validation": r_res.passed,
        "request_message": r_res.message,
        "built_validation": b_res.passed,
        "built_message": b_res.message,
        "passed": passed
    }

    report_dir = REPO_ROOT / "scratch"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "trixel32d_handshake_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[gate_trixel32d_handshake][REQUEST] {'PASS' if r_res.is_true() else 'FAIL'}: {r_res.message}")
    print(f"[gate_trixel32d_handshake][RESPONSE] {'PASS' if b_res.is_true() else 'FAIL'}: {b_res.message}")
    print(f"[gate_trixel32d_handshake][ALL_GATES] {'true' if passed else 'false'}")

    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
