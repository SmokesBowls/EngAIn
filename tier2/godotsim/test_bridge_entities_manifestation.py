"""
test_bridge_entities_manifestation.py -- Regression tests for the
2026-09-19 scene-local manifestation fallback in bridge_entities_for_scene()
(engain-avatar-audit: 09-19-2026-scene-local-manifestation-design-
corrected.md).

bridge_entities_for_scene() must prefer @entities_manifested when the
key is present -- even if the list is empty, which is a real "nothing
here qualifies" answer, not missing data -- and fall back to today's
@entities/entities behavior only when the key is entirely absent
(an artifact generated before this feature existed).
"""

from __future__ import annotations

import unittest

from tier2.godotsim.bridge_integration import bridge_entities_for_scene


class TestManifestationPreferredOverEntities(unittest.TestCase):
    def test_present_empty_manifested_list_yields_zero_entities(self):
        """The exact chapter-1 acceptance case: @entities has two
        globally-spawnable names, but @entities_manifested is present
        and empty -- must produce zero Entity3D results, not fall back
        to spawning Pelagor/Vaelith."""
        scene_doc = {
            "@id": "scene.test.manifestation_empty",
            "@entities": ["Pelagor", "Vaelith"],
            "@entities_manifested": [],
        }
        results = bridge_entities_for_scene(scene_doc)
        self.assertEqual(results, [])

    def test_present_nonempty_manifested_list_is_used_instead_of_entities(self):
        """@entities_manifested is a narrower subset of @entities and
        must be the one actually instantiated."""
        scene_doc = {
            "@id": "scene.test.manifestation_subset",
            "@entities": ["Senareth", "Vairis"],
            "@entities_manifested": ["Senareth"],
        }
        results = bridge_entities_for_scene(scene_doc)
        ids = {r.get("entity_id") for r in results}
        self.assertEqual(ids, {"Senareth"})

    def test_absent_manifested_key_falls_back_to_entities(self):
        """An artifact predating this feature has no @entities_manifested
        key at all -- must fall back to today's @entities behavior
        unchanged, so old artifacts don't stop spawning entities they
        used to spawn until they're regenerated."""
        scene_doc = {
            "@id": "scene.test.legacy_no_manifestation",
            "@entities": ["Pelagor", "Vaelith"],
        }
        results = bridge_entities_for_scene(scene_doc)
        ids = {r.get("entity_id") for r in results}
        self.assertEqual(ids, {"Pelagor", "Vaelith"})

    def test_entities_key_untouched_in_meaning(self):
        """@entities by itself, with no manifestation data at all, must
        keep behaving exactly as before this feature -- this is not a
        redefinition of @entities."""
        scene_doc = {
            "@id": "scene.test.entities_only",
            "entities": ["Senareth"],
        }
        results = bridge_entities_for_scene(scene_doc)
        ids = {r.get("entity_id") for r in results}
        self.assertEqual(ids, {"Senareth"})


if __name__ == "__main__":
    unittest.main()
