"""
test_scene_local_manifestation.py -- Regression tests for the 2026-09-19
scene-local manifestation feature (engain-avatar-audit:
09-19-2026-pelagor-vaelith-global-vs-scene-local-spawnable-gap.md,
09-19-2026-scene-local-manifestation-design.md,
09-19-2026-scene-local-manifestation-design-corrected.md).

Two independent axes on entities_observed -- presence and physicality --
plus a new derived @entities_manifested field on the ZONJ scene dict.

Fixtures below are synthetic but modeled directly on the real, currently
generated Book 1 artifacts (chapter 1 scene 1 and chapter 2 scenes 1-2),
using the same real world_rules.json identities (Vaelith, Pelagor,
Senareth, Giants, Vairis) and the same textual evidence patterns actually
found in those artifacts:

  Vaelith (ch1): listed in the scene's own "participants:" line;
    "projected her awareness through the Veil" describes her ACTION, not
    her location -- she is local, and nonphysical (no body established).

  Pelagor (ch1): absent from the participants line; only ever described
    via "resonance of Pelagor essence" / "energy signature" -- detected
    at a distance, never placed in the room. Remote.

  Senareth (ch2): listed in participants; real-time body-formation
    narration ("body began forming, muscles and organs") and physical
    interaction with the beach ("tried to stand", "palms" against sand).
    Local and physical -- the positive control this feature needed.

  Giants (ch2): listed in participants; direct local physical action
    ("emerged from the forest", "stood watching"). Local and physical,
    but known_non_spawnable in world_rules.json (collective/species,
    spawnable: false) -- proves manifestation and spawnable are
    orthogonal gates, excluded from @entities_manifested for a different
    reason than Vaelith/Pelagor.

  Vairis (ch2, in this fixture only): mentioned in prose, not listed in
    participants, no remote-sensing or physical/nonphysical evidence
    either -- must fail closed to presence=unknown, not be guessed as
    local, per the "fail closed rather than inventing locality" rule.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext import world_rules_loader
from tier3.mettaext.passroom import (
    pass1_explicit,
    pass2_enhanced,
    pass2_entity_filter,
    pass3_merge,
    pass4_zon_bridge,
)

WORLD_RULES_FILE = Path("tier1/engainos/assets/world_rules.json")


def _run_pass1_through_pass3(tmp_path: Path, stem: str, text: str) -> dict:
    ch_file = tmp_path / f"{stem}.txt"
    ch_file.write_text(text, encoding="utf-8")

    pass1_out = tmp_path / f"out_pass1_{stem}.txt"
    pass1_explicit.process_file(ch_file, pass1_out)

    segments = pass2_enhanced.load_segments(str(pass1_out))
    characters = pass2_entity_filter.filter_entities(
        pass2_enhanced.extract_characters(segments)
    )
    pass2_enhanced.infer_presence_enhanced(segments, characters)
    pass2_enhanced.infer_physicality_enhanced(segments, characters)

    pass2_out = tmp_path / f"out_pass2_{stem}.metta"
    pass2_enhanced.write_metta(
        str(pass2_out),
        pass2_enhanced.infer_speakers_enhanced(segments, characters),
        pass2_enhanced.infer_emotions_enhanced(segments, characters),
        pass2_enhanced.infer_actions_enhanced(segments),
        pass2_enhanced.infer_thoughts_enhanced(segments, characters),
        characters,
        pass2_enhanced.infer_relationships(segments, characters),
    )

    p1_segs = pass3_merge.parse_pass1(str(pass1_out))
    p2_data = pass3_merge.parse_pass2(str(pass2_out))
    return pass3_merge.merge_to_zonj(p1_segs, p2_data, str(pass1_out), str(pass2_out))


class TestPresenceAndPhysicalityNegativeControls(unittest.TestCase):
    """Chapter 1 evidence: Vaelith (local/nonphysical) and Pelagor (remote)."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        world_rules_loader.load_rules()
        self.source_text = (
            "# Chapter 401: Ethereal Vigil Test\n"
            "participants: Vaelith, Mordain, Korath\n"
            "Vaelith projected her awareness through the Veil, sensing distant shifts.\n"
            "Vaelith and Mordain watched together in silence, their consciousness calm.\n"
            "Vaelith's awareness lingered on the world below.\n"
            "The others studied the unmistakable resonance of Pelagor essence within the forms.\n"
            "They analyzed the ancient energy signature of Pelagor again and again.\n"
            "Pelagor remained far below, unreachable and unseen.\n"
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _entities_observed(self):
        zonj = _run_pass1_through_pass3(self.tmp_path, "401_vigil", self.source_text)
        return {e["name"]: e for e in zonj.get("entities_observed", [])}, zonj

    def test_vaelith_is_local_not_remote(self):
        """The core correction: an entity whose ACTION reaches somewhere
        remote is not itself remote, when the scene's own participants
        line places them locally."""
        observed, _ = self._entities_observed()
        self.assertEqual(observed["Vaelith"]["presence"], "local")
        self.assertGreaterEqual(observed["Vaelith"]["presence_confidence"], 0.9)

    def test_vaelith_is_nonphysical(self):
        observed, _ = self._entities_observed()
        self.assertEqual(observed["Vaelith"]["physicality"], "nonphysical")

    def test_pelagor_is_remote(self):
        observed, _ = self._entities_observed()
        self.assertEqual(observed["Pelagor"]["presence"], "remote")

    def test_pelagor_physicality_is_unknown_not_guessed(self):
        """physicality is only meaningful for presence == local; a remote
        entity must never be assigned a physicality value."""
        observed, _ = self._entities_observed()
        self.assertEqual(observed["Pelagor"]["physicality"], "unknown")

    def test_at_entities_unchanged_both_still_spawnable(self):
        """world_rules.spawnable must stay untouched by this feature --
        both remain in the existing @entities projection.

        2026-09-20 Pattern 4 fix: Mordain is now also correctly seeded
        (he's listed in participants: and is known/spawnable in
        world_rules.json), so he correctly joins @entities too -- this
        is the fix working as intended, not a regression. He was
        previously silently dropped here for the same reason Mika/
        Zephyr/Saresh/Torhh were in the real corpus: too few prose
        mentions to pass the old frequency-only gate."""
        _, zonj = self._entities_observed()
        self.assertEqual(sorted(zonj.get("@entities", [])), ["Mordain", "Pelagor", "Vaelith"])

    def test_mordain_seeded_as_participant_despite_low_mentions(self):
        """Direct Pattern 4 regression case: Mordain has only 2 prose
        mentions in this fixture (would fail the old count>=3 gate) but
        is explicitly listed in participants: -- must still appear in
        entities_observed, with presence local."""
        observed, _ = self._entities_observed()
        self.assertIn("Mordain", observed)
        self.assertEqual(observed["Mordain"]["presence"], "local")

    def test_neither_reaches_entities_manifested(self):
        """The acceptance case: @entities_manifested must be present
        (manifestation was computed) but empty (neither qualifies) --
        not absent, and not silently falling back to @entities."""
        _, zonj = self._entities_observed()
        self.assertIn("@entities_manifested", zonj)
        self.assertEqual(zonj["@entities_manifested"], [])


class TestPhysicalPositiveControlsAndOrthogonality(unittest.TestCase):
    """Chapter 2 evidence: Senareth (local/physical, positive control),
    Giants (local/physical but non-spawnable -- orthogonality proof),
    and Vairis (fail-closed to unknown when no placement evidence)."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        world_rules_loader.load_rules()
        self.source_text = (
            "# Chapter 402: Molten Descent Test\n"
            "participants: Senareth, Giants\n"
            "Senareth's body began forming, muscles and organs taking shape at last.\n"
            "Senareth tried to stand and immediately fell onto the sand.\n"
            "Senareth forced themselves to stand again, palms pressed into the ground.\n"
            "The Giants emerged from the forest, massive and slow.\n"
            "The Giants stood watching, their steps heavy on the earth.\n"
            "Around Senareth, more Giants approached, drawn by the disturbance.\n"
            "Vairis had spoken of the descent long before it began.\n"
            "Vairis's words echoed among them all that day.\n"
            "They remembered what Vairis had said afterward.\n"
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _entities_observed(self):
        zonj = _run_pass1_through_pass3(self.tmp_path, "402_descent", self.source_text)
        return {e["name"]: e for e in zonj.get("entities_observed", [])}, zonj

    def test_senareth_is_local_and_physical(self):
        observed, _ = self._entities_observed()
        self.assertEqual(observed["Senareth"]["presence"], "local")
        self.assertEqual(observed["Senareth"]["physicality"], "physical")

    def test_senareth_reaches_entities_manifested(self):
        _, zonj = self._entities_observed()
        self.assertIn("Senareth", zonj.get("@entities_manifested", []))

    def test_giants_are_local_and_physical_but_not_spawnable(self):
        """world_rules.json: Giants is a known collective/species entity
        with spawnable: false -- manifestation must classify it as truly
        local and physical anyway; only the separate spawnable gate
        excludes it, proving the two checks are independent."""
        observed, _ = self._entities_observed()
        self.assertEqual(observed["Giants"]["presence"], "local")
        self.assertEqual(observed["Giants"]["physicality"], "physical")
        self.assertFalse(observed["Giants"]["spawnable"])

    def test_giants_excluded_from_entities_manifested(self):
        _, zonj = self._entities_observed()
        self.assertNotIn("Giants", zonj.get("@entities_manifested", []))
        # And confirm it was never in @entities either -- pre-existing,
        # unrelated-to-this-feature spawnable filtering.
        self.assertNotIn("Giants", zonj.get("@entities", []))

    def test_vairis_fails_closed_to_unknown_presence(self):
        """No participants listing, no remote-sensing phrase, no
        physical/nonphysical keyword evidence for Vairis in this scene --
        must default to unknown, never be guessed as local or remote."""
        observed, _ = self._entities_observed()
        self.assertEqual(observed["Vairis"]["presence"], "unknown")
        self.assertEqual(observed["Vairis"]["presence_confidence"], 0.0)

    def test_vairis_stays_in_entities_but_not_manifested(self):
        """Still globally spawnable (world_rules), so still in @entities --
        but excluded from @entities_manifested since presence was never
        established as local."""
        _, zonj = self._entities_observed()
        self.assertIn("Vairis", zonj.get("@entities", []))
        self.assertNotIn("Vairis", zonj.get("@entities_manifested", []))


class TestPass4ManifestationPassthrough(unittest.TestCase):
    """pass4_zon_bridge.py must transport @entities_manifested unchanged,
    using key presence (not truthiness) so an empty-but-computed list
    survives -- never re-deriving it."""

    def test_present_empty_list_survives_passthrough(self):
        bridge = pass4_zon_bridge.ZONBridge(world_rules_path=WORLD_RULES_FILE)
        scene = {
            "id": "test_scene",
            "segments": [{"line": 1, "type": "narration", "text": "Nothing physical here."}],
            "@entities": ["Pelagor", "Vaelith"],
            "@entities_manifested": [],
        }
        with tempfile.TemporaryDirectory() as td:
            zonj_path = Path(td) / "zonj_test_scene.json"
            zonj_path.write_text(json.dumps(scene), encoding="utf-8")
            out = bridge.convert_to_zonj(zonj_path, pass4_zon_bridge.ZONMetadata())
        self.assertIn("@entities_manifested", out)
        self.assertEqual(out["@entities_manifested"], [])

    def test_absent_key_stays_absent(self):
        """An artifact that never computed manifestation must not have
        the key invented for it."""
        bridge = pass4_zon_bridge.ZONBridge(world_rules_path=WORLD_RULES_FILE)
        scene = {
            "id": "test_scene_legacy",
            "segments": [{"line": 1, "type": "narration", "text": "Legacy scene, no manifestation data."}],
            "@entities": ["Pelagor"],
        }
        with tempfile.TemporaryDirectory() as td:
            zonj_path = Path(td) / "zonj_test_scene_legacy.json"
            zonj_path.write_text(json.dumps(scene), encoding="utf-8")
            out = bridge.convert_to_zonj(zonj_path, pass4_zon_bridge.ZONMetadata())
        self.assertNotIn("@entities_manifested", out)

    def test_nonempty_manifested_list_survives_passthrough(self):
        bridge = pass4_zon_bridge.ZONBridge(world_rules_path=WORLD_RULES_FILE)
        scene = {
            "id": "test_scene2",
            "segments": [{"line": 1, "type": "narration", "text": "Senareth stood on the sand."}],
            "@entities": ["Senareth"],
            "@entities_manifested": ["Senareth"],
        }
        with tempfile.TemporaryDirectory() as td:
            zonj_path = Path(td) / "zonj_test_scene2.json"
            zonj_path.write_text(json.dumps(scene), encoding="utf-8")
            out = bridge.convert_to_zonj(zonj_path, pass4_zon_bridge.ZONMetadata())
        self.assertEqual(out["@entities_manifested"], ["Senareth"])


if __name__ == "__main__":
    unittest.main()
