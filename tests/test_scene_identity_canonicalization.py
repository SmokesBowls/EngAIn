from mettaext.scene_identity import canonical_scene_id
from godotsim.scene_manager import SceneManager


class _DummyRuntime:
    def __init__(self):
        self.snapshot = {
            "scene_id": None,
            "scene": None,
            "scene_raw": None,
            "entities": {},
            "spatial": {},
            "perception": {},
            "behavior": {},
            "events": [],
        }


def _minimal_scene(scene_id: str):
    return {
        "scene_id": scene_id,
        "segments": [{"text": "hello"}],
        "entities": [],
    }


def test_canonical_scene_id_examples():
    assert canonical_scene_id("001_the_ethereal_vigil") == "scene.001_the_ethereal_vigil"
    assert canonical_scene_id("01_the_ethereal_vigil") == "scene.001_the_ethereal_vigil"
    assert canonical_scene_id("scene.001_the_ethereal_vigil") == "scene.001_the_ethereal_vigil"
    assert canonical_scene_id("scene.01_the_ethereal_vigil") == "scene.001_the_ethereal_vigil"

    assert canonical_scene_id("02__molten_descent") == "scene.002_molten_descent"
    assert canonical_scene_id("02_ molten_descent") == "scene.002_molten_descent"
    assert canonical_scene_id("scene.02_ molten_descent") == "scene.002_molten_descent"
    assert canonical_scene_id("scene.002_molten_descent") == "scene.002_molten_descent"

    assert canonical_scene_id("04_the convergence") == "scene.004_the_convergence"


def test_scene_manager_stores_and_activates_canonical_id_from_aliases():
    rt = _DummyRuntime()
    sm = SceneManager(rt)  # type: ignore[arg-type]

    sm.load_scene(_minimal_scene("01_the_ethereal_vigil"), activate=False)

    # Canonical key is authoritative in registry.
    assert "scene.001_the_ethereal_vigil" in sm.scenes

    # Alias lookup should still work for activation.
    assert sm.select_active_scene("scene.01_the_ethereal_vigil") is True
    assert rt.snapshot["scene_id"] == "scene.001_the_ethereal_vigil"


def test_scene_manager_normalizes_molten_descent_alias_to_canonical():
    rt = _DummyRuntime()
    sm = SceneManager(rt)  # type: ignore[arg-type]

    sm.load_scene(_minimal_scene("scene.02_ molten_descent"), activate=True)

    assert rt.snapshot["scene_id"] == "scene.002_molten_descent"
    assert "scene.002_molten_descent" in sm.scenes
