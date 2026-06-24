import pytest
from .slice_builders import build_entity_kview_v1, SliceError
from .slice_types import EntityKViewV1

def test_build_entity_kview_v1_success():
    world = {
        "entities": {
            "e1": {
                "pos": (1, 2, 3),
                "vel": (0, 1, 0),
                "health": 80.0
            }
        }
    }
    view = build_entity_kview_v1(world, "e1")
    assert isinstance(view, EntityKViewV1)
    assert view.eid == "e1"
    assert view.pos == (1.0, 2.0, 3.0)
    assert view.vel == (0.0, 1.0, 0.0)
    assert view.health == 80.0

def test_build_entity_kview_v1_missing_pos():
    world = {
        "entities": {
            "e1": {
                "vel": (0, 1, 0),
                "health": 80.0
            }
        }
    }
    with pytest.raises(SliceError, match="position missing for e1"):
        build_entity_kview_v1(world, "e1")

def test_build_entity_kview_v1_alternative_position():
    world = {
        "entities": {
            "e1": {
                "position": (10, 20, 30),
                "vel": (0, 0, 0)
            }
        }
    }
    view = build_entity_kview_v1(world, "e1")
    assert view.pos == (10.0, 20.0, 30.0)

def test_build_entity_kview_v1_missing_vel_default():
    world = {
        "entities": {
            "e1": {
                "pos": (1, 2, 3)
            }
        }
    }
    # Should normalize missing vel to (0,0,0) by default
    view = build_entity_kview_v1(world, "e1")
    assert view.vel == (0.0, 0.0, 0.0)

def test_build_entity_kview_v1_missing_vel_error():
    world = {
        "entities": {
            "e1": {
                "pos": (1, 2, 3)
            }
        }
    }
    with pytest.raises(SliceError, match="velocity missing for e1"):
        build_entity_kview_v1(world, "e1", normalize_missing_vel=False)
