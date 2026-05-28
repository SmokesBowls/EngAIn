import pytest
from engain.world.coordinates import make_coordinate_abi, validate_coordinate_record, CoordinateABI
from trixelcomposer.tile_address import TileAddress, CameraRelative, build

def test_make_coordinate_abi_renamed_fields():
    # Test constructing with positional / keyword compatibility
    coord = make_coordinate_abi(
        grid_x=10,
        grid_y=16,
        elevation=5,
        tile_address="d10.u5.f16"
    )
    assert coord.grid_xy == (10, 16)
    assert coord.elevation == 5
    assert coord.view_address_hint == "d10.u5.f16"
    assert coord.tile_address == "d10.u5.f16" # deprecated alias
    assert coord.world_cell_3d == (10, 5, 16)

def test_validate_coordinate_record_compliant():
    compliant = {
        "schema_version": "trixel_coordinate_abi.v1",
        "authority_level": "coordinate_truth",
        "authoritative": True,
        "artifact_kind": "coordinate_record",
        "position": {
            "world_x": 10.0,
            "world_y": 5.0,
            "world_z": 16.0
        },
        "chunk": {
            "chunk_x": 0,
            "chunk_y": 1,
            "chunk_z": 0,
            "chunk_size": 48,
            "local_x": 10,
            "local_y": 5,
            "local_z": 16
        }
    }
    errors = validate_coordinate_record(compliant)
    assert errors == []

def test_validate_coordinate_record_non_compliant():
    # Missing top-level key
    non_compliant = {
        "schema_version": "trixel_coordinate_abi.v1",
        # Missing authority_level
        "authoritative": True,
        "artifact_kind": "coordinate_record",
    }
    errors = validate_coordinate_record(non_compliant)
    assert len(errors) > 0
    assert any("Missing required top-level key" in err for err in errors)

    # Invalid authoritative value
    bad_val = {
        "schema_version": "trixel_coordinate_abi.v1",
        "authority_level": "coordinate_truth",
        "authoritative": False, # should be True
        "artifact_kind": "coordinate_record",
    }
    errors = validate_coordinate_record(bad_val)
    assert any("Invalid value for 'authoritative'" in err for err in errors)

def test_tile_address_to_view_address_record():
    cam = CameraRelative(horizontal="left", vertical="up", depth="forward")
    ta = build(
        world_cell=(49, 19, 57),
        camera_relative=cam,
        visible_face="top",
        surface_normal=(0.0, 1.0, 0.0),
        view_vector=(0.0, -1.0, 0.0),
        recipe="volcano.branching_lava"
    )
    record = ta.to_view_address_record()
    
    assert record["schema_version"] == "trixel_view_address_abi.v1"
    assert record["authority_level"] == "observer_relative"
    assert record["authoritative"] is False
    assert record["artifact_kind"] == "view_address_record"
    assert record["source"] == "view_address_generator"
    assert record["visible_face"] == "top"
    assert record["normals"] == [0.0, 1.0, 0.0]
    assert record["view_address_string"] == "l49.u19.f57"
