import json

import pytest

from engain.render.packet_io import read_packets_json, write_packets_json
from engain.render.transforms import build_placement_packet
from engain.world.chunks import make_chunk_coordinate
from engain.world.coordinates import make_coordinate_abi


def _make_packet(tile_id, grid_x, grid_y, elevation, chunk_x, chunk_y, chunk_size, rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0), visible_face="top"):
    coordinate = make_coordinate_abi(
        grid_x=grid_x,
        grid_y=grid_y,
        elevation=elevation,
        tile_address=f"d{grid_x}.u{elevation}.f{grid_y}",
    )
    chunk = make_chunk_coordinate(
        local_x=grid_x,
        local_z=grid_y,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
        chunk_size=chunk_size,
    )
    return build_placement_packet(
        tile_id=tile_id,
        coordinate_abi=coordinate,
        chunk_coordinate=chunk,
        visible_face=visible_face,
        rotation=rotation,
        scale=scale,
    )


def test_write_then_read_round_trip(tmp_path):
    p1 = _make_packet("shoreline", 10, 16, 0, 0, 1, 48)
    p2 = _make_packet("cliff", -7, 12, 3, -250, 4096, 32, rotation=(0.0, 90.0, 0.0), scale=(1.0, 2.0, 0.5), visible_face="wall")

    out = tmp_path / "packets.json"
    write_packets_json(out, [p1, p2])

    loaded = read_packets_json(out)
    assert loaded == [p1.to_dict(), p2.to_dict()]

    raw = out.read_text(encoding="utf-8")
    assert raw.endswith("\n")


def test_fixture_loads_successfully():
    fixture = "tests/fixtures/placement_packets_sample.json"
    loaded = read_packets_json(fixture)

    assert isinstance(loaded, list)
    assert len(loaded) >= 2
    for packet in loaded:
        assert set(["tile_id", "grid", "chunk", "world", "render"]).issubset(packet.keys())


def test_malformed_root_object_raises_value_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not": "a-list"}), encoding="utf-8")

    with pytest.raises(ValueError):
        read_packets_json(bad)
