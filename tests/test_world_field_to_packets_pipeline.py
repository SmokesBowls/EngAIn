import hashlib
import json

import pytest

from engain.world.world_field_adapter import normalize_world_field_payload
from engain.world.placement_emitter import emit_placement_packets_from_grid
from engain.render.packet_io import write_packets_json, read_packets_json


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_sample_payload() -> dict:
    with open("tests/fixtures/world_field_sample.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_world_field_pipeline_deterministic_and_hash_stable(tmp_path):
    payload = _load_sample_payload()

    n1 = normalize_world_field_payload(payload)
    n2 = normalize_world_field_payload(payload)

    p1 = emit_placement_packets_from_grid(
        n1["terrain_grid"],
        elevations=n1["elevations"],
        chunk_x=n1["chunk_x"],
        chunk_y=n1["chunk_y"],
        chunk_size=n1["chunk_size"],
    )
    p2 = emit_placement_packets_from_grid(
        n2["terrain_grid"],
        elevations=n2["elevations"],
        chunk_x=n2["chunk_x"],
        chunk_y=n2["chunk_y"],
        chunk_size=n2["chunk_size"],
    )

    d1 = [x.to_dict() for x in p1]
    d2 = [x.to_dict() for x in p2]
    assert d1 == d2

    out1 = tmp_path / "wf_packets_1.json"
    out2 = tmp_path / "wf_packets_2.json"
    write_packets_json(out1, p1)
    write_packets_json(out2, p2)

    b1 = out1.read_bytes()
    b2 = out2.read_bytes()
    assert b1 == b2
    assert _sha256_bytes(b1) == _sha256_bytes(b2)


def test_chunk_offsets_and_elevation_affect_world_coordinates():
    payload = _load_sample_payload()
    n = normalize_world_field_payload(payload)
    packets = emit_placement_packets_from_grid(
        n["terrain_grid"],
        elevations=n["elevations"],
        chunk_x=n["chunk_x"],
        chunk_y=n["chunk_y"],
        chunk_size=n["chunk_size"],
    )

    # grid (2,1): x=2 z=1 elevation=0.0
    t = next(p for p in packets if p.grid["x"] == 2 and p.grid["y"] == 1)
    assert t.world["x"] == float(n["chunk_x"] * n["chunk_size"] + 2)
    assert t.world["z"] == float(n["chunk_y"] * n["chunk_size"] + 1)
    assert t.world["y"] == 0.0

    # grid (1,1): elevation 2.0
    e = next(p for p in packets if p.grid["x"] == 1 and p.grid["y"] == 1)
    assert e.world["y"] == 2.0


def test_expected_fixture_matches_current_output():
    payload = _load_sample_payload()
    n = normalize_world_field_payload(payload)
    packets = emit_placement_packets_from_grid(
        n["terrain_grid"],
        elevations=n["elevations"],
        chunk_x=n["chunk_x"],
        chunk_y=n["chunk_y"],
        chunk_size=n["chunk_size"],
    )
    current = [p.to_dict() for p in packets]
    expected = read_packets_json("tests/fixtures/world_field_packets.json")
    assert current == expected


def test_multi_chunk_payload_rejected():
    bad = {
        "chunks": [
            {
                "chunk_key": [0, 0],
                "chunk_size": 16,
                "terrain_grid": [["grass"]],
                "elevations": [[0.0]],
            },
            {
                "chunk_key": [1, 0],
                "chunk_size": 16,
                "terrain_grid": [["sand"]],
                "elevations": [[0.0]],
            },
        ]
    }
    with pytest.raises(ValueError):
        normalize_world_field_payload(bad)


def test_bad_elevation_shape_rejected():
    bad = {
        "terrain_grid": [["grass", "sand"], ["rock", "cliff"]],
        "elevations": [[0.0], [1.0]],
        "chunk_x": 0,
        "chunk_y": 0,
        "chunk_size": 16,
    }
    with pytest.raises(ValueError):
        normalize_world_field_payload(bad)
