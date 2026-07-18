from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

import tier1.engainos.gates.gate_trixel32d_handshake as handshake_gate
from tier1.engainos.gates.gate_trixel32d_handshake import (
    validate_trixel32d_surface_request,
    validate_trixel32d_surface_built,
    gate_trixel32d_handshake,
    GateResult
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
CANONICAL_REQUEST_FIXTURE = FIXTURE_DIR / "trixel32d_request_3x2_first_proof.json"
CANONICAL_BUILT_FIXTURE = FIXTURE_DIR / "trixel32d_surface_built_3x2_first_proof.json"
CANONICAL_BUILT_SHA256 = "bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929"
REQUEST_ID = "t32dreq_8b14a3bac98d1025"
TOPOLOGY_POLICY = "HEIGHT_FIELD_CELL_EXTRUSION"
SURFACE_ID = "t32dsurface_0f5d9d7e96ed734a"


def get_valid_fixture_request() -> dict[str, Any]:
    return {
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": REQUEST_ID,
        },
        "packet_type": "trixel32d_surface_request",
        "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
        "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
        "construction": {
            "topology_policy": TOPOLOGY_POLICY,
        },
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


def get_valid_fixture_built() -> dict[str, Any]:
    return {
        "contract": "trixel32d_surface_built.v1",
        "packet_type": "trixel32d_surface_built",
        "request_id": REQUEST_ID,
        "surface_id": SURFACE_ID,
        "status": "BUILT",
        "local_spatial_metadata": {
            "coordinate_space": "TRIXEL_LOCAL_Y_UP"
        },
        "rejected_cells": [],
        "errors": [],
        "topology_policy": TOPOLOGY_POLICY,
        "appearance": {},
        "geometry": {
            "vertices": [[0,0,0], [1,0,0]],
            "indices": [0, 1]
        },
        "primitive_provenance": [],
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
                "source_cell_ordinal": 2,
                "field_x": 1,
                "field_y": 0,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 4, "vertex_count": 4, "index_start": 6, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 4, "vertex_count": 4, "index_start": 6, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 4, "vertex_count": 4, "index_start": 6, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 4, "vertex_count": 4, "index_start": 6, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 4, "vertex_count": 4, "index_start": 6, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 4, "vertex_count": 4, "index_start": 6, "index_count": 6}
                ]
            },
            {
                "cell_key": "2,0",
                "source_cell_ordinal": 4,
                "field_x": 2,
                "field_y": 0,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 8, "vertex_count": 4, "index_start": 12, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 8, "vertex_count": 4, "index_start": 12, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 8, "vertex_count": 4, "index_start": 12, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 8, "vertex_count": 4, "index_start": 12, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 8, "vertex_count": 4, "index_start": 12, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 8, "vertex_count": 4, "index_start": 12, "index_count": 6}
                ]
            },
            {
                "cell_key": "0,1",
                "source_cell_ordinal": 1,
                "field_x": 0,
                "field_y": 1,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 12, "vertex_count": 4, "index_start": 18, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 12, "vertex_count": 4, "index_start": 18, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 12, "vertex_count": 4, "index_start": 18, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 12, "vertex_count": 4, "index_start": 18, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 12, "vertex_count": 4, "index_start": 18, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 12, "vertex_count": 4, "index_start": 18, "index_count": 6}
                ]
            },
            {
                "cell_key": "1,1",
                "source_cell_ordinal": 3,
                "field_x": 1,
                "field_y": 1,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 16, "vertex_count": 4, "index_start": 24, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 16, "vertex_count": 4, "index_start": 24, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 16, "vertex_count": 4, "index_start": 24, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 16, "vertex_count": 4, "index_start": 24, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 16, "vertex_count": 4, "index_start": 24, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 16, "vertex_count": 4, "index_start": 24, "index_count": 6}
                ]
            },
            {
                "cell_key": "2,1",
                "source_cell_ordinal": 5,
                "field_x": 2,
                "field_y": 1,
                "surfaces": [
                    {"role": "PRIMARY_PIXEL_FACE", "face": "top", "vertex_start": 20, "vertex_count": 4, "index_start": 30, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "bottom", "vertex_start": 20, "vertex_count": 4, "index_start": 30, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_y", "vertex_start": 20, "vertex_count": 4, "index_start": 30, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_x", "vertex_start": 20, "vertex_count": 4, "index_start": 30, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "+field_y", "vertex_start": 20, "vertex_count": 4, "index_start": 30, "index_count": 6},
                    {"role": "NEUTRAL_GAP_FILL", "face": "-field_x", "vertex_start": 20, "vertex_count": 4, "index_start": 30, "index_count": 6}
                ]
            }
        ]
    }


def test_01_valid_fixture_request_passes() -> None:
    req = get_valid_fixture_request()
    errors = validate_trixel32d_surface_request(req)
    assert len(errors) == 0, f"Expected no errors, got: {errors}"


def test_02_valid_fixture_built_passes() -> None:
    req = get_valid_fixture_request()
    built = get_valid_fixture_built()
    errors = validate_trixel32d_surface_built(built, req)
    assert len(errors) == 0, f"Expected no errors, got: {errors}"


def test_03_invalid_coordinate_space_fails() -> None:
    req = get_valid_fixture_request()
    req["coordinate_space"] = "WORLDCELL_GRID"
    errors = validate_trixel32d_surface_request(req)
    assert any("coordinate_space" in err for err in errors)


def test_04_invalid_up_axis_policy_fails() -> None:
    req = get_valid_fixture_request()
    req["up_axis_policy"] = "FLEXIBLE"
    errors = validate_trixel32d_surface_request(req)
    assert any("up_axis_policy" in err for err in errors)


def test_05_non_unit_length_vectors_fail_outside_tolerance() -> None:
    req = get_valid_fixture_request()
    # Length of [0.5, 0.0, 0.5] is 0.707 (far outside tolerance)
    req["orientation"]["vectors"]["right"] = [0.5, 0.0, 0.5]
    errors = validate_trixel32d_surface_request(req)
    assert any("unit length" in err for err in errors)


def test_06_non_orthogonal_basis_fails() -> None:
    req = get_valid_fixture_request()
    req["orientation"]["vectors"]["forward"] = [1.0, 0.0, 0.0]
    req["orientation"]["vectors"]["right"] = [1.0, 0.0, 0.0] # Parallel
    errors = validate_trixel32d_surface_request(req)
    assert any("orthogonal" in err for err in errors)


def test_07_invalid_handedness_fails() -> None:
    req = get_valid_fixture_request()
    # Inverting up vector, making right-handed system left-handed
    req["orientation"]["vectors"]["up"] = [0.0, -1.0, 0.0]
    errors = validate_trixel32d_surface_request(req)
    assert any("handedness" in err or "violates Y-up" in err for err in errors)


def test_08_missing_coordinate_dense_fails() -> None:
    req = get_valid_fixture_request()
    req["pixel_field_data"].pop(2)
    errors = validate_trixel32d_surface_request(req)
    assert any("length" in err or "Missing coordinate" in err for err in errors)


def test_09_duplicate_coordinate_fails() -> None:
    req = get_valid_fixture_request()
    # Duplicate coordinate
    req["pixel_field_data"][2] = copy.deepcopy(req["pixel_field_data"][0])
    errors = validate_trixel32d_surface_request(req)
    assert any("Duplicate coordinate" in err for err in errors)


def test_10_invalid_built_status_fails() -> None:
    built = get_valid_fixture_built()
    built["status"] = "PARTIALLY_BUILT"
    errors = validate_trixel32d_surface_built(built)
    assert any("status" in err for err in errors)


def test_11_built_errors_not_empty_fails() -> None:
    built = get_valid_fixture_built()
    built["errors"] = ["Failure in mesh generation"]
    errors = validate_trixel32d_surface_built(built, get_valid_fixture_request())
    assert any("errors" in err for err in errors)


def test_12_rejected_packet_requires_errors() -> None:
    built = get_valid_fixture_built()
    built["status"] = "REJECTED"
    built["surface_id"] = None
    built["geometry"] = None
    built["cell_geometry_ranges"] = []
    built["primitive_provenance"] = []
    built["errors"] = []
    del built["appearance"]
    del built["topology_policy"]
    errors = validate_trixel32d_surface_built(built, get_valid_fixture_request())
    assert any("errors" in err for err in errors)


def test_13_row_major_mismatch_fails() -> None:
    req = get_valid_fixture_request()
    built = get_valid_fixture_built()
    # Swap element 1 and 2 in ranges, breaking row-major order
    built["cell_geometry_ranges"][1], built["cell_geometry_ranges"][2] = (
        built["cell_geometry_ranges"][2],
        built["cell_geometry_ranges"][1]
    )
    errors = validate_trixel32d_surface_built(built, req)
    assert any("coordinate mismatch" in err for err in errors)


def test_14_gate_result_integration() -> None:
    req = get_valid_fixture_request()
    r_res = gate_trixel32d_handshake(req)
    assert r_res.is_true(), f"Expected TRUE, got {r_res.passed}: {r_res.message}"

    built = get_valid_fixture_built()
    b_res = gate_trixel32d_handshake(built, request=req)
    assert b_res.is_true(), f"Expected TRUE, got {b_res.passed}: {b_res.message}"

    # Verify skipped gate on other packets
    other_packet = {"packet_type": "some_other_packet"}
    o_res = gate_trixel32d_handshake(other_packet)
    assert o_res.is_skipped()


# =============================================================================
# NEW TESTS FOR SPECIFIC CONTRACT v1.1 MANDATES
# =============================================================================

def test_15_corrected_face_ordering() -> None:
    # Verify that a response fails if it deviates from the corrected ordering:
    # 1. top, 2. bottom, 3. -field_y, 4. +field_x, 5. +field_y, 6. -field_x
    req = get_valid_fixture_request()
    built = get_valid_fixture_built()
    
    # Swapping -field_y and +field_x on cell 0
    surfaces = built["cell_geometry_ranges"][0]["surfaces"]
    surfaces[2], surfaces[3] = surfaces[3], surfaces[2]
    
    errors = validate_trixel32d_surface_built(built, req)
    assert any("face must be '-field_y'" in err for err in errors)


def test_16_normalized_non_exact_unit_vectors() -> None:
    # If a vector is slightly off but within tolerance, raw validation passes
    # and normalization ensures it is fully unit length (1.0 exactly).
    req = get_valid_fixture_request()
    # 0.7072^2 * 2 = 1.00025 -> length is ~1.00012, within tolerance of 0.0001 (relative to 1.0)
    # Wait, tolerance is 0.0001, so diff is 0.00012 which is slightly larger than 0.0001. Let's make it closer:
    # Let's use 0.70714 * 0.70714 * 2 = 1.00008, length is ~1.00004 -> within tolerance!
    req["orientation"]["vectors"]["forward"] = [0.70714, 0.0, -0.70714]
    
    errors = validate_trixel32d_surface_request(req)
    assert len(errors) == 0, f"Expected validation to pass and normalize, got: {errors}"


def test_17_scrambled_input_sorted_into_row_major_output() -> None:
    # If the request's pixel_field_data is scrambled, the validator should still pass.
    # The response's cell_geometry_ranges MUST still be in row-major order.
    req = get_valid_fixture_request()
    # Scramble the request pixel_field_data array
    req["pixel_field_data"] = [
        req["pixel_field_data"][5],
        req["pixel_field_data"][0],
        req["pixel_field_data"][4],
        req["pixel_field_data"][1],
        req["pixel_field_data"][3],
        req["pixel_field_data"][2],
    ]
    
    errors_req = validate_trixel32d_surface_request(req)
    assert len(errors_req) == 0, "Scrambled DENSE request should pass validation"
    
    built = get_valid_fixture_built()
    errors_built = validate_trixel32d_surface_built(built, req)
    assert len(errors_built) == 0, "Response in correct row-major order should pass even if request was scrambled"


def test_18_source_cell_ordinal_preserves_original_request_order() -> None:
    # Request order: [cell_5, cell_0, cell_4, cell_1, cell_3, cell_2]
    # Ordinals:     [0=cell_5, 1=cell_0, 2=cell_4, 3=cell_1, 4=cell_3, 5=cell_2]
    # Row major coordinates in response:
    # 0,0 is cell_0 (ordinal 1)
    # 1,0 is cell_2 (ordinal 5)
    # 2,0 is cell_4 (ordinal 2)
    # 0,1 is cell_1 (ordinal 3)
    # 1,1 is cell_3 (ordinal 4)
    # 2,1 is cell_5 (ordinal 0)
    req = get_valid_fixture_request()
    orig_cells = req["pixel_field_data"]
    scrambled = [
        orig_cells[5], # index 0 in scrambled -> ordinal 0
        orig_cells[0], # index 1 in scrambled -> ordinal 1
        orig_cells[4], # index 2 in scrambled -> ordinal 2
        orig_cells[1], # index 3 in scrambled -> ordinal 3
        orig_cells[3], # index 4 in scrambled -> ordinal 4
        orig_cells[2], # index 5 in scrambled -> ordinal 5
    ]
    req["pixel_field_data"] = scrambled
    
    built = get_valid_fixture_built()
    # Map the ranges source_cell_ordinals to match the scrambled request indices:
    # 0,0 -> request[1] -> ordinal 1
    # 1,0 -> request[5] -> ordinal 5
    # 2,0 -> request[2] -> ordinal 2
    # 0,1 -> request[3] -> ordinal 3
    # 1,1 -> request[4] -> ordinal 4
    # 2,1 -> request[0] -> ordinal 0
    built["cell_geometry_ranges"][0]["source_cell_ordinal"] = 1
    built["cell_geometry_ranges"][1]["source_cell_ordinal"] = 5
    built["cell_geometry_ranges"][2]["source_cell_ordinal"] = 2
    built["cell_geometry_ranges"][3]["source_cell_ordinal"] = 3
    built["cell_geometry_ranges"][4]["source_cell_ordinal"] = 4
    built["cell_geometry_ranges"][5]["source_cell_ordinal"] = 0
    
    errors = validate_trixel32d_surface_built(built, req)
    assert len(errors) == 0, f"Expected ordinals to align with scrambled request indices, got: {errors}"


def test_19_request_and_response_coordinate_spaces_differ() -> None:
    # Request is WORLD_FIELD_GRID_TO_LOCAL_Y_UP
    # Response is TRIXEL_LOCAL_Y_UP
    # If response tries to use request coordinate space, it fails validation.
    req = get_valid_fixture_request()
    built = get_valid_fixture_built()

    built["local_spatial_metadata"]["coordinate_space"] = "WORLD_FIELD_GRID_TO_LOCAL_Y_UP"
    errors = validate_trixel32d_surface_built(built, req)
    assert any("local_spatial_metadata.coordinate_space" in err for err in errors)


# =============================================================================
# IDENTITY-COMPLETE BUILT-RESPONSE BOUNDARY
# =============================================================================


def _canonical_request() -> dict[str, Any]:
    return json.loads(CANONICAL_REQUEST_FIXTURE.read_bytes())


def _canonical_built_bytes() -> bytes:
    return CANONICAL_BUILT_FIXTURE.read_bytes()


def _canonical_built() -> dict[str, Any]:
    return json.loads(_canonical_built_bytes())


def test_20_canonical_built_fixture_bytes_are_independently_locked() -> None:
    assert hashlib.sha256(_canonical_built_bytes()).hexdigest() == CANONICAL_BUILT_SHA256


def test_21_exact_built_bytes_validate_and_return_their_binding_digest() -> None:
    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        _canonical_built_bytes(),
        _canonical_request(),
        expected_response_sha256=CANONICAL_BUILT_SHA256,
    )

    assert result.accepted
    assert result.errors == ()
    assert result.response_sha256 == CANONICAL_BUILT_SHA256
    assert result.packet is not None
    assert result.packet["request_id"] == REQUEST_ID
    assert result.packet["surface_id"] == SURFACE_ID


def test_22_built_contract_is_required_and_exact() -> None:
    request = _canonical_request()
    for invalid_contract in (None, "trixel32d_surface_built.v2"):
        built = _canonical_built()
        if invalid_contract is None:
            del built["contract"]
        else:
            built["contract"] = invalid_contract

        errors = validate_trixel32d_surface_built(built, request)

        assert any("contract" in error for error in errors)


def test_23_built_request_id_must_match_the_trusted_request() -> None:
    built = _canonical_built()
    built["request_id"] = "t32dreq_0000000000000000"

    errors = validate_trixel32d_surface_built(built, _canonical_request())

    assert any("request_id" in error and "match" in error for error in errors)


def test_24_built_surface_id_is_required_and_deterministic() -> None:
    request = _canonical_request()
    for invalid_surface_id in (None, "t32dsurface_ffffffffffffffff"):
        built = _canonical_built()
        if invalid_surface_id is None:
            del built["surface_id"]
        else:
            built["surface_id"] = invalid_surface_id

        errors = validate_trixel32d_surface_built(built, request)

        assert any("surface_id" in error for error in errors)


def test_25_modified_response_bytes_fail_the_independent_checksum_lock() -> None:
    built = _canonical_built()
    built["surface_id"] = "t32dsurface_ffffffffffffffff"
    modified_bytes = json.dumps(built, sort_keys=True).encode("utf-8")

    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        modified_bytes,
        _canonical_request(),
        expected_response_sha256=CANONICAL_BUILT_SHA256,
    )

    assert not result.accepted
    assert result.packet is None
    assert result.response_sha256 != CANONICAL_BUILT_SHA256
    assert any("SHA-256" in error for error in result.errors)


def test_26_built_response_requires_a_trusted_request_context() -> None:
    errors = validate_trixel32d_surface_built(_canonical_built(), None)

    assert any("trusted request" in error for error in errors)


def test_27_unknown_built_response_identity_field_rejects() -> None:
    built = _canonical_built()
    built["response_id"] = "uncontracted-identity"

    errors = validate_trixel32d_surface_built(built, _canonical_request())

    assert any("unknown root fields" in error and "response_id" in error for error in errors)


def test_28_identity_rejection_does_not_mutate_response_or_request() -> None:
    built = _canonical_built()
    built["request_id"] = "t32dreq_0000000000000000"
    request = _canonical_request()
    before_built = copy.deepcopy(built)
    before_request = copy.deepcopy(request)

    errors = validate_trixel32d_surface_built(built, request)

    assert errors
    assert built == before_built
    assert request == before_request


def test_29_rejected_response_preserves_request_identity_without_surface_identity() -> None:
    rejected = {
        "contract": "trixel32d_surface_built.v1",
        "packet_type": "trixel32d_surface_built",
        "request_id": REQUEST_ID,
        "surface_id": None,
        "status": "REJECTED",
        "local_spatial_metadata": {
            "coordinate_space": "TRIXEL_LOCAL_Y_UP",
            "winding_policy": "CLOCKWISE_FRONT_FACE_GODOT",
            "normals_policy": "CANONICAL_FACE_NORMALS_INCLUDED",
            "tangents_policy": "OMITTED_NO_TANGENT_BASIS",
        },
        "geometry": None,
        "cell_geometry_ranges": [],
        "primitive_provenance": [],
        "rejected_cells": [],
        "errors": ["deterministic rejection"],
    }

    errors = validate_trixel32d_surface_built(rejected, _canonical_request())

    assert errors == []


def test_30_duplicate_json_identity_key_rejects_before_semantic_validation() -> None:
    response_text = _canonical_built_bytes().decode("utf-8")
    duplicate = f'"request_id": "{REQUEST_ID}",\n  "request_id": "{REQUEST_ID}",'
    response_text = response_text.replace(
        f'"request_id": "{REQUEST_ID}",',
        duplicate,
        1,
    )

    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        response_text.encode("utf-8"),
        _canonical_request(),
    )

    assert not result.accepted
    assert result.packet is None
    assert any("duplicate JSON key" in error and "request_id" in error for error in result.errors)


def test_31_response_topology_must_match_trusted_request_even_with_matching_surface_id() -> None:
    built = _canonical_built()
    attacker_policy = "ATTACKER_SELECTED_POLICY"
    built["topology_policy"] = attacker_policy
    attacker_digest = hashlib.sha256(
        f"{REQUEST_ID}:{attacker_policy}".encode("utf-8")
    ).hexdigest()[:16]
    built["surface_id"] = f"t32dsurface_{attacker_digest}"

    errors = validate_trixel32d_surface_built(built, _canonical_request())

    assert any("topology_policy" in error and "trusted request" in error for error in errors)


def test_32_accepted_packet_is_deeply_immutable() -> None:
    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        _canonical_built_bytes(),
        _canonical_request(),
    )

    assert result.accepted
    assert result.packet is not None
    with pytest.raises(TypeError):
        result.packet["request_id"] = "t32dreq_0000000000000000"
    with pytest.raises(TypeError):
        result.packet["geometry"]["positions"][0][0] = 999.0


def test_33_malformed_trusted_request_fails_closed_without_exception() -> None:
    request = _canonical_request()
    del request["planar_config"]

    errors = validate_trixel32d_surface_built(_canonical_built(), request)

    assert any(
        "trusted request failed request validation" in error
        and "planar_config" in error
        for error in errors
    )


def test_34_nonstandard_json_numeric_constant_rejects() -> None:
    built = _canonical_built()
    built["appearance"]["nonstandard_number"] = float("nan")
    response_bytes = json.dumps(built, sort_keys=True).encode("utf-8")

    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        response_bytes,
        _canonical_request(),
    )

    assert not result.accepted
    assert result.packet is None
    assert any("nonstandard JSON numeric constant" in error for error in result.errors)


def test_35_non_string_expected_checksum_fails_closed() -> None:
    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        _canonical_built_bytes(),
        _canonical_request(),
        expected_response_sha256=123,  # type: ignore[arg-type]
    )

    assert not result.accepted
    assert result.packet is None
    assert any("expected response SHA-256" in error for error in result.errors)


def test_36_byte_level_validation_does_not_mutate_bytes_or_request() -> None:
    response_bytes = _canonical_built_bytes()
    request = _canonical_request()
    before_bytes = response_bytes[:]
    before_request = copy.deepcopy(request)

    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        response_bytes,
        request,
    )

    assert result.accepted
    assert response_bytes == before_bytes
    assert request == before_request


def test_37_request_rejected_by_request_gate_cannot_authorize_response() -> None:
    request = _canonical_request()
    del request["pixel_field_data"]
    assert validate_trixel32d_surface_request(request)

    errors = validate_trixel32d_surface_built(_canonical_built(), request)

    assert any("trusted request failed request validation" in error for error in errors)


def test_38_array_status_in_response_bytes_fails_closed() -> None:
    built = _canonical_built()
    built["status"] = ["BUILT"]

    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        json.dumps(built).encode("utf-8"),
        _canonical_request(),
    )

    assert not result.accepted
    assert result.packet is None
    assert any("status" in error for error in result.errors)


def test_39_scalar_surface_entry_in_response_bytes_fails_closed() -> None:
    built = _canonical_built()
    built["cell_geometry_ranges"][0]["surfaces"][0] = "not-an-object"

    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        json.dumps(built).encode("utf-8"),
        _canonical_request(),
    )

    assert not result.accepted
    assert result.packet is None
    assert any("must be a dict" in error for error in result.errors)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("cell_geometry_ranges", 0, "field_x"), False),
        (("cell_geometry_ranges", 0, "source_cell_ordinal"), True),
        (("cell_geometry_ranges", 0, "surfaces", 0, "vertex_start"), False),
    ],
)
def test_40_boolean_integer_fields_reject(path: tuple[Any, ...], value: bool) -> None:
    built = _canonical_built()
    target: Any = built
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    errors = validate_trixel32d_surface_built(built, _canonical_request())

    assert errors


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("appearance", "not-an-object"),
        ("primitive_provenance", "not-an-array"),
        ("geometry", {}),
    ],
)
def test_41_wrong_built_node_types_reject(field: str, value: Any) -> None:
    built = _canonical_built()
    built[field] = value

    errors = validate_trixel32d_surface_built(built, _canonical_request())

    assert any(field in error or "geometry" in error for error in errors)


def test_42_public_request_validator_and_gate_fail_closed_on_malformed_inputs() -> None:
    request = _canonical_request()
    request["orientation"]["tolerance"] = "not-numeric"

    errors = validate_trixel32d_surface_request(request)
    gate_result = gate_trixel32d_handshake(["not-an-object"])  # type: ignore[arg-type]

    assert errors
    assert gate_result.is_false()


def test_43_public_built_validator_fails_closed_on_non_object() -> None:
    errors = validate_trixel32d_surface_built(["not-an-object"], _canonical_request())  # type: ignore[arg-type]

    assert errors


@pytest.mark.parametrize("depth", [900, 2000])
def test_44_deeply_nested_response_json_fails_closed(depth: int) -> None:
    built = _canonical_built()
    built["appearance"] = "DEPTH_MARKER"
    response_text = json.dumps(built)
    nested_object = '{"nested":' * depth + "null" + "}" * depth
    response_bytes = response_text.replace('"DEPTH_MARKER"', nested_object).encode("utf-8")

    result = handshake_gate.validate_trixel32d_surface_built_bytes(
        response_bytes,
        _canonical_request(),
    )

    assert not result.accepted
    assert result.packet is None
    assert any(
        "depth limit" in error or "failed closed" in error
        for error in result.errors
    )
