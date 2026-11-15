"""The runtime keeps a scene's provenance: authored anchors, the packet's own id, and honest placement labels.

Pass 5 marks its index-based layout `layout_source: fallback_linear`; SceneManager used to relabel it
`authored_pos`. The runtime's prose extractor also re-added names Passroom had judged not to be
entities ("Tomorrow"). And /scene/load canonicalizes ids (dots -> underscores) with no record of the
original.
"""

from __future__ import annotations

import contextlib
import io
import unittest

from tier2.godotsim.runtime_core import EngAInRuntime

SOURCE_ID = "scene.book001.903_provenance.scene001"
SCENE = {
    "scene_id": SOURCE_ID,
    "source_scene_id": SOURCE_ID,
    "where": "Realm/Physical/Earth coastline landing beach",
    "when": "day 1, first night",
    "metadata": {"anchor_provenance": {"where": "authored:@scene_meta_location",
                                       "when": "authored:@scene_meta_time"}},
    "terrain_metadata": {"region": "Earth coastline landing beach", "terrain_family": "coastal"},
    "entities": [{"id": "senareth", "name": "Senareth", "type": "character",
                  "position": {"x": 0.0, "y": 0.0, "z": 0.0}, "layout_source": "fallback_linear"}],
    "entities_observed": [{"name": "Tomorrow", "known": False, "classification": "unknown"}],
    # The reference scene's own lines that made the extractor promote "Tomorrow".
    "segments": [
        {"type": "dialogue", "speaker": "Senareth", "text": '"Tomorrow we try again," Senareth said. "Tomorrow we send individuals."'},
        {"type": "narration", "text": "Tomorrow, Senareth thought. Tomorrow we bridge this gap."},
    ],
}


class TestSceneProvenance(unittest.TestCase):
    def setUp(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.runtime = EngAInRuntime()
            self.runtime.scene_manager.load_scene(dict(SCENE), activate=True)

    def tearDown(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.runtime.shutdown()

    def test_authored_anchors_and_source_id_survive(self) -> None:
        scene = self.runtime.snapshot["scene"]
        self.assertEqual(scene["where"], SCENE["where"])
        self.assertEqual(scene["when"], SCENE["when"])
        self.assertEqual(scene["anchor_provenance"]["where"], "authored:@scene_meta_location")
        self.assertEqual(scene["terrain"]["region"], "Earth coastline landing beach")
        self.assertEqual(scene["source_scene_id"], SOURCE_ID)
        self.assertNotEqual(scene["scene_id"], SOURCE_ID, "the canonical rewrite is visible, not silent")

    def test_fallback_layout_is_never_labelled_authored(self) -> None:
        bridge = {e.get("name"): e for e in self.runtime.snapshot.get("bridge_entities") or []}
        self.assertEqual(bridge["Senareth"].get("placement_source"), "fallback_linear")

    def test_names_passroom_rejected_are_not_readded_from_prose(self) -> None:
        names = {str(e.get("name")) for e in self.runtime.snapshot.get("entities", {}).values()}
        self.assertNotIn("Tomorrow", names)


if __name__ == "__main__":
    unittest.main()
