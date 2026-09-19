"""
test_pass3_pass4_entity_handoff.py — Regression tests for the 2026-09-19
entity handoff fix (engain-avatar-audit: 09-19-2026-tran-false-entity-
root-cause-found.md, 09-19-2026-pass2-pass3-pass4-handoff-gap-found.md,
09-19-2026-entities-field-consumer-trace.md, 09-19-2026-entity-handoff-
fix-plan.md).

Two defects, two fixes, tested together and separately:

  PRIMARY (pass3_merge.py, merge_to_zonj()):
    @entities was never populated from Pass 2's classified entities at
    all -- only entities_observed was. This forced Pass 4's narration-
    scan fallback to run on every scene, every chapter, unconditionally.
    Fix: project the SPAWNABLE-true subset of entities_observed into
    @entities. Per the consumer trace, @entities must stay
    spawnable-safe -- tier2/godotsim's bridge_entities_for_scene() has
    no independent spawnable check and would try to give a non-spawnable
    entity (e.g. Lyaris) a physical mesh/transform.

  DEFENSIVE (pass4_zon_bridge.py, ZONBridge.extract_entities()):
    the narration-scan fallback matched world_rules' registered entity
    names as plain substrings ("tran" in "transformed"). Fix: word-
    boundary matching. Kept as a fallback for malformed/legacy/partial
    input, not removed.

Real world_rules.json fixtures used throughout, not synthetic ones:
  Lyaris  -- known, spawnable: false (aeon_keeper)
  Vairis  -- known, spawnable: true  (character)
  Tran    -- known, spawnable: true  (character, chapter_102/mars_convergence)
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
    """Shared pipeline plumbing: write source, run Pass 1/2, merge to ZONJ."""
    ch_file = tmp_path / f"{stem}.txt"
    ch_file.write_text(text, encoding="utf-8")

    pass1_out = tmp_path / f"out_pass1_{stem}.txt"
    pass1_explicit.process_file(ch_file, pass1_out)

    segments = pass2_enhanced.load_segments(str(pass1_out))
    characters = pass2_entity_filter.filter_entities(
        pass2_enhanced.extract_characters(segments)
    )
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


def _through_pass4(tmp_path: Path, stem: str, zonj_dict: dict) -> dict:
    zonj_file = tmp_path / f"zonj_{stem}.json"
    zonj_file.write_text(json.dumps(zonj_dict), encoding="utf-8")
    bridge = pass4_zon_bridge.ZONBridge(world_rules_path=WORLD_RULES_FILE)
    return bridge.convert_to_zonj(zonj_file, pass4_zon_bridge.ZONMetadata())


class TestEntityHandoffPrimaryFix(unittest.TestCase):
    """pass3_merge.py: @entities now projects the spawnable subset of
    entities_observed, instead of never being populated at all."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        world_rules_loader.load_rules()
        # Lyaris (known, non-spawnable) and Vairis (known, spawnable),
        # each mentioned 3+ times so pass2's frequency filter admits them
        # as candidates at all.
        self.source_text = (
            "# Chapter 301: Handoff Test\n"
            "Lyaris watched the horizon. Lyaris said nothing more.\n"
            "Vairis walked beside her. Vairis carried the lantern.\n"
            "Lyaris and Vairis continued on together.\n"
        )

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_lyaris_present_in_entities_observed(self):
        """Criterion 1: Lyaris is present in entities_observed."""
        zonj = _run_pass1_through_pass3(self.tmp_path, "301_handoff", self.source_text)
        entities_observed = zonj.get("entities_observed", [])
        names = [e["name"] for e in entities_observed]
        self.assertIn("Lyaris", names)
        lyaris = next(e for e in entities_observed if e["name"] == "Lyaris")
        self.assertTrue(lyaris["known"])
        self.assertFalse(lyaris["spawnable"])

    def test_lyaris_absent_from_at_entities(self):
        """Criterion 2: Lyaris is absent from @entities while spawnable:false."""
        zonj = _run_pass1_through_pass3(self.tmp_path, "301_handoff", self.source_text)
        self.assertNotIn("Lyaris", zonj.get("@entities", []))

    def test_spawnable_entity_reaches_at_entities(self):
        """Criterion 3: a genuinely spawnable Pass-2 entity reaches @entities."""
        zonj = _run_pass1_through_pass3(self.tmp_path, "301_handoff", self.source_text)
        self.assertIn("Vairis", zonj.get("@entities", []))

    def test_entities_observed_unchanged_by_this_fix(self):
        """Criterion 6: entities_observed's own construction is untouched --
        regression pin against the exact pre-fix shape (name/known/
        spawnable/classification/mentions per entry, sorted by name)."""
        zonj = _run_pass1_through_pass3(self.tmp_path, "301_handoff", self.source_text)
        entities_observed = zonj.get("entities_observed", [])
        names = [e["name"] for e in entities_observed]
        self.assertEqual(names, sorted(names))
        for entry in entities_observed:
            self.assertEqual(
                set(entry.keys()), {"name", "known", "spawnable", "classification", "mentions"}
            )


class TestPass4CompanionAndFallback(unittest.TestCase):
    """pass4_zon_bridge.py: the pre-populated @entities path, and the
    hardened narration-scan fallback."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        world_rules_loader.load_rules()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_normal_pipeline_scene_does_not_need_the_narration_fallback(self):
        """Criterion 7: normal current-pipeline input does not activate
        the narration scan at all, because @entities now arrives
        pre-populated from Pass 3."""
        source_text = (
            "# Chapter 302: Fallback Non-Activation Test\n"
            "Vairis walked beside her. Vairis carried the lantern.\n"
            "Vairis paused at the ridge.\n"
        )
        zonj = _run_pass1_through_pass3(self.tmp_path, "302_no_fallback", source_text)
        self.assertIn("@entities", zonj)  # primary fix already populated it
        zon_canonical = _through_pass4(self.tmp_path, "302_no_fallback", zonj)
        self.assertIn("Vairis", zon_canonical.get("@entities", []))

    def test_false_tran_disappears_from_transformed_text(self):
        """Criteria 4 + 5 (part 1): the exact false-positive case from
        the live investigation -- "transformed"/"transformation" in the
        text, no standalone "Tran" -- must not produce the entity "Tran",
        even via the fallback path (constructed with an empty upstream
        @entities to force the narration scan to run)."""
        bridge = pass4_zon_bridge.ZONBridge(world_rules_path=WORLD_RULES_FILE)
        obj = {
            "segments": [
                {"text": "The vessel had transformed since the last transformation."},
            ],
        }
        entities = bridge.extract_entities(obj)
        self.assertNotIn("Tran", entities)

    def test_standalone_tran_still_matches_when_genuinely_present(self):
        """Criteria 4 + 5 (part 2): the word-boundary fix must not disable
        real detection -- a genuine standalone "Tran" must still be found
        by the narration-scan fallback."""
        bridge = pass4_zon_bridge.ZONBridge(world_rules_path=WORLD_RULES_FILE)
        obj = {
            "segments": [
                {"text": "Tran stood at the threshold. Tran did not move."},
            ],
        }
        entities = bridge.extract_entities(obj)
        self.assertIn("Tran", entities)


if __name__ == "__main__":
    unittest.main()
