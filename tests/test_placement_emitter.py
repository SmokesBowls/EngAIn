import json

import pytest

from engain.world.placement_emitter import emit_placement_packets_from_grid
from engain.render.packet_io import write_packets_json


def _load_fixture():
    with open("tests/fixtures/terrain_grid_sample.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_packet_count_and_determinism():
    fx = _load_fixture()
    p1 = emit_placement_packets_from_grid(
        fx["terrain_grid"],
        elevations=fx["elevations"],
        chunk_x=fx["chunk_x"],
        chunk_y=fx["chunk_y"],
        chunk_size=fx["chunk_size"],
    )
    p2 = emit_placement_packets_from_grid(
        fx["terrain_grid"],
        elevations=fx["elevations"],
        chunk_x=fx["chunk_x"],
        chunk_y=fx["chunk_y"],
        chunk_size=fx["chunk_size"],
    )

    expected_count = len(fx["terrain_grid"]) * len(fx["terrain_grid"][0])
    assert len(p1) == expected_count
    assert [x.to_dict() for x in p1] == [x.to_dict() for x in p2]


def test_repeated_json_write_is_byte_identical(tmp_path):
    fx = _load_fixture()
    packets = emit_placement_packets_from_grid(
        fx["terrain_grid"],
        elevations=fx["elevations"],
        chunk_x=fx["chunk_x"],
        chunk_y=fx["chunk_y"],
        chunk_size=fx["chunk_size"],
    )

    p1 = tmp_path / "packets_1.json"
    p2 = tmp_path / "packets_2.json"
    write_packets_json(p1, packets)
    write_packets_json(p2, packets)

    b1 = p1.read_bytes()
    b2 = p2.read_bytes()
    assert b1 == b2


def test_world_position_formulas_and_nonzero_elevation():
    fx = _load_fixture()
    packets = emit_placement_packets_from_grid(
        fx["terrain_grid"],
        elevations=fx["elevations"],
        chunk_x=fx["chunk_x"],
        chunk_y=fx["chunk_y"],
        chunk_size=fx["chunk_size"],
    )

    # pick grid(1,1) where elevation is 2.0
    target = next(p for p in packets if p.grid["x"] == 1 and p.grid["y"] == 1)

    expected_x = fx["chunk_x"] * fx["chunk_size"] + 1
    expected_z = fx["chunk_y"] * fx["chunk_size"] + 1
    assert target.world["x"] == float(expected_x)
    assert target.world["z"] == float(expected_z)
    assert target.world["y"] == 2.0


def test_invalid_non_rectangular_grid_raises():
    bad_grid = [
        ["grass", "sand"],
        ["rock"],
    ]
    with pytest.raises(ValueError):
        emit_placement_packets_from_grid(bad_grid)


def test_invalid_elevation_shape_raises():
    grid = [
        ["grass", "sand", "rock"],
        ["cliff", "shoreline", "deep_water"],
    ]
    bad_elev = [
        [0.0, 1.0],
        [0.0, 0.0],
    ]
    with pytest.raises(ValueError):
        emit_placement_packets_from_grid(grid, elevations=bad_elev)
