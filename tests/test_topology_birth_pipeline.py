import hashlib
import json

from engain.world.topology_stub import build_topology_stub
from engain.world.placement_emitter import emit_placement_packets_from_grid
from engain.render.packet_io import write_packets_json, read_packets_json


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def test_topology_birth_pipeline_deterministic(tmp_path):
    topo1 = build_topology_stub(width=6, height=6, profile="coastal")
    topo2 = build_topology_stub(width=6, height=6, profile="coastal")

    packets1 = emit_placement_packets_from_grid(
        topo1["terrain_grid"],
        elevations=topo1["elevations"],
        chunk_x=topo1["chunk_x"],
        chunk_y=topo1["chunk_y"],
        chunk_size=topo1["chunk_size"],
    )
    packets2 = emit_placement_packets_from_grid(
        topo2["terrain_grid"],
        elevations=topo2["elevations"],
        chunk_x=topo2["chunk_x"],
        chunk_y=topo2["chunk_y"],
        chunk_size=topo2["chunk_size"],
    )

    d1 = [p.to_dict() for p in packets1]
    d2 = [p.to_dict() for p in packets2]
    assert d1 == d2

    out1 = tmp_path / "topology_birth_1.json"
    out2 = tmp_path / "topology_birth_2.json"
    write_packets_json(out1, packets1)
    write_packets_json(out2, packets2)

    b1 = out1.read_bytes()
    b2 = out2.read_bytes()
    assert b1 == b2
    assert _sha256_bytes(b1) == _sha256_bytes(b2)

    assert len(packets1) == 6 * 6

    # elevations influence world_y: ensure at least one positive and one low value survived
    ys = [p.world["y"] for p in packets1]
    assert any(y > 0.0 for y in ys)
    assert any(y <= 0.0 for y in ys)

    # all packets have render.position arrays
    for packet in packets1:
        pd = packet.to_dict()
        assert "render" in pd and "position" in pd["render"]
        assert isinstance(pd["render"]["position"], list)
        assert len(pd["render"]["position"]) == 3


def test_expected_fixture_matches_current_output():
    topo = build_topology_stub(width=6, height=6, profile="coastal")
    packets = emit_placement_packets_from_grid(
        topo["terrain_grid"],
        elevations=topo["elevations"],
        chunk_x=topo["chunk_x"],
        chunk_y=topo["chunk_y"],
        chunk_size=topo["chunk_size"],
    )
    current = [p.to_dict() for p in packets]

    fixture_path = "tests/fixtures/topology_birth_packets.json"
    expected = read_packets_json(fixture_path)

    assert current == expected


def test_unknown_profile_raises_value_error():
    try:
        build_topology_stub(profile="unknown")
        raised = False
    except ValueError:
        raised = True
    assert raised
