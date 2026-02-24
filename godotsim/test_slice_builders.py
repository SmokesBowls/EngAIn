import pytest
import sys
import os

# Add the current directory to path so we can import from the same directory
sys.path.insert(0, os.path.dirname(__file__))

from slice_builders import build_entity_kview_v1, SliceError
from slice_types import EntityKViewV1

def test_build_entity_kview_v1_valid():
    """Verify successful creation of EntityKViewV1 with valid data."""
    world = {
        "entities": {
            "hero": {
                "pos": (1.0, 2.0, 3.0),
                "vel": (0.0, 1.0, 0.0),
                "health": 80.0
            }
        }
    }
    view = build_entity_kview_v1(world, "hero")
    # Using type() check to avoid issues with multiple imports of the same class
    assert view.__class__.__name__ == "EntityKViewV1"
    assert view.eid == "hero"
    assert view.pos == (1.0, 2.0, 3.0)
    assert view.vel == (0.0, 1.0, 0.0)
    assert view.health == 80.0
    assert view.max_health == 100.0  # default

def test_build_entity_kview_v1_missing_pos():
    """Verify that SliceError is raised when 'pos' and 'position' are missing."""
    world = {
        "entities": {
            "hero": {
                "vel": (0.0, 0.0, 0.0)
            }
        }
    }
    with pytest.raises(SliceError, match="position missing for hero"):
        build_entity_kview_v1(world, "hero")

def test_build_entity_kview_v1_invalid_entities():
    """Verify SliceError when 'entities' is missing or not a dict."""
    with pytest.raises(SliceError, match="world.entities missing or not dict"):
        build_entity_kview_v1({}, "hero")

    with pytest.raises(SliceError, match="world.entities missing or not dict"):
        build_entity_kview_v1({"entities": "not a dict"}, "hero")

def test_build_entity_kview_v1_invalid_eid():
    """Verify SliceError when eid is not found."""
    world = {"entities": {}}
    with pytest.raises(SliceError, match="entity hero not found in snapshot"):
        build_entity_kview_v1(world, "hero")

def test_build_entity_kview_v1_position_alias():
    """Verify that 'position' works as an alias for 'pos'."""
    world = {
        "entities": {
            "hero": {
                "position": (10.0, 20.0, 30.0)
            }
        }
    }
    view = build_entity_kview_v1(world, "hero")
    assert view.pos == (10.0, 20.0, 30.0)
