from engain.world.coordinates import make_coordinate_abi
from engain.world.chunks import make_chunk_coordinate
from engain.render.transforms import build_placement_packet


def _make_packet(
    *,
    tile_id: str,
    grid_x: int,
    grid_y: int,
    elevation: int,
    chunk_x: int,
    chunk_y: int,
    chunk_size: int,
    visible_face: str = "top",
    rotation=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
):
    coordinate_abi = make_coordinate_abi(
        grid_x=grid_x,
        grid_y=grid_y,
        elevation=elevation,
        tile_address=f"d{grid_x}.u{elevation}.f{grid_y}",
    )
    chunk_coordinate = make_chunk_coordinate(
        local_x=grid_x,
        local_z=grid_y,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
        chunk_size=chunk_size,
    )
    packet = build_placement_packet(
        tile_id=tile_id,
        coordinate_abi=coordinate_abi,
        chunk_coordinate=chunk_coordinate,
        visible_face=visible_face,
        rotation=rotation,
        scale=scale,
    )
    return packet


def test_same_input_same_packet_deterministic_identity():
    p1 = _make_packet(
        tile_id="shoreline",
        grid_x=10,
        grid_y=16,
        elevation=0,
        chunk_x=0,
        chunk_y=1,
        chunk_size=48,
    )
    p2 = _make_packet(
        tile_id="shoreline",
        grid_x=10,
        grid_y=16,
        elevation=0,
        chunk_x=0,
        chunk_y=1,
        chunk_size=48,
    )

    assert p1 == p2
    assert p1.world == p2.world
    assert p1.chunk == p2.chunk
    assert p1.to_dict()["render"]["position"] == p2.to_dict()["render"]["position"]
    assert p1.to_dict()["render"]["rotation"] == p2.to_dict()["render"]["rotation"]
    assert p1.to_dict()["render"]["scale"] == p2.to_dict()["render"]["scale"]


def test_tile_origin_alignment_world_position_formula():
    # world_x = chunk_x * chunk_size + local_x
    # world_z = chunk_y * chunk_size + local_z
    p = _make_packet(
        tile_id="shoreline",
        grid_x=10,
        grid_y=16,
        elevation=0,
        chunk_x=0,
        chunk_y=1,
        chunk_size=48,
    )

    assert p.world["x"] == 10.0
    assert p.world["y"] == 0.0
    assert p.world["z"] == 64.0
    assert p.to_dict()["render"]["position"] == [10.0, 0.0, 64.0]


def test_negative_coordinates_chunk_and_world_placement():
    p = _make_packet(
        tile_id="ash_plain",
        grid_x=-3,
        grid_y=-5,
        elevation=-2,
        chunk_x=-2,
        chunk_y=-1,
        chunk_size=32,
    )

    assert p.chunk == {"x": -2, "y": -1}
    assert p.world == {"x": -67.0, "y": -2.0, "z": -37.0}
    assert p.to_dict()["render"]["position"] == [-67.0, -2.0, -37.0]


def test_large_chunk_offsets_are_stable():
    p = _make_packet(
        tile_id="deep_water",
        grid_x=31,
        grid_y=31,
        elevation=7,
        chunk_x=1000,
        chunk_y=2000,
        chunk_size=32,
    )

    assert p.chunk == {"x": 1000, "y": 2000}
    assert p.world == {"x": 32031.0, "y": 7.0, "z": 64031.0}


def test_non_default_scale_and_rotation_preservation():
    p = _make_packet(
        tile_id="cliff",
        grid_x=1,
        grid_y=2,
        elevation=3,
        chunk_x=4,
        chunk_y=5,
        chunk_size=16,
        visible_face="wall",
        rotation=(0.0, 90.0, 0.0),
        scale=(1.0, 2.0, 0.5),
    )

    d = p.to_dict()
    assert d["render"]["position"] == [65.0, 3.0, 82.0]
    assert d["render"]["rotation"] == [0.0, 90.0, 0.0]
    assert d["render"]["scale"] == [1.0, 2.0, 0.5]
    assert d["render"]["visible_face"] == "wall"
