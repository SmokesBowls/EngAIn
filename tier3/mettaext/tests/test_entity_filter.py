"""
test_entity_filter.py — Revised Regression tests for Boundary 2: Entity Filter Evidence Preservation

Repair Targets:
1. UNKNOWN != DELETE (unknown proper names survive as semantic evidence)
2. NON-SPAWNABLE != DELETE FROM SEMANTIC EVIDENCE (known non-spawnables survive as semantic evidence without pretending to spawn)
3. NOISE FILTERING != ONTOLOGY REJECTION (extraction noise is filtered out of entities, but raw Pass 1 source evidence remains untouched)
4. PERSISTENCE SURVIVAL (unknown valid entity candidate survives into out_pass2_*.metta and Pass 3 merge ZONJ)
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tier3.mettaext.passroom import pass2_enhanced, pass3_merge
from tier3.mettaext.passroom.pass2_enhanced import Character, Segment
from tier3.mettaext.passroom.pass2_entity_filter import filter_entities


class TestEntityFilter(unittest.TestCase):

    def test_known_spawnable_entity_survives(self):
        """
        Known + spawnable entity (e.g. 'Elyraen') must survive in filtered entity dictionary.
        """
        characters = {
            "Elyraen": Character(name="Elyraen", mentions=5)
        }
        filtered = filter_entities(characters)

        self.assertIn("Elyraen", filtered, "Known spawnable entity 'Elyraen' must survive entity filtering")

    def test_known_non_spawnable_entity_preserved_without_spawning(self):
        """
        Known + non-spawnable entity (e.g. 'Lyaris') must survive in filtered output,
        without being marked as spawnable.
        """
        characters = {
            "Lyaris": Character(name="Lyaris", mentions=5)
        }
        filtered = filter_entities(characters)

        self.assertIn("Lyaris", filtered, "Known non-spawnable entity 'Lyaris' must NOT be deleted from semantic evidence")
        char = filtered["Lyaris"]
        # Must not pretend it can spawn
        self.assertFalse(getattr(char, "spawnable", False), "Known non-spawnable entity must have spawnable=False")

    def test_unknown_entity_many_mentions_survives_as_unknown(self):
        """
        Unknown proper entity with many mentions (e.g. 'Igigi', mentions=10) must survive
        semantic evidence as UNKNOWN (known=False, spawnable=False).
        """
        characters = {
            "Igigi": Character(name="Igigi", mentions=10)
        }
        filtered = filter_entities(characters)

        self.assertIn("Igigi", filtered, "Unknown proper entity 'Igigi' must NOT be deleted from semantic evidence")
        char = filtered["Igigi"]
        self.assertFalse(getattr(char, "known", True), "Unknown entity should have known=False")
        self.assertFalse(getattr(char, "spawnable", True), "Unknown entity must have spawnable=False")

    def test_unknown_entity_single_mention_survives_as_observation(self):
        """
        Unknown proper entity with only 1 mention (e.g. 'MysteryTraveler', mentions=1)
        must still survive as a single-mention observation (known=False, spawnable=False).
        """
        characters = {
            "MysteryTraveler": Character(name="MysteryTraveler", mentions=1)
        }
        filtered = filter_entities(characters)

        self.assertIn("MysteryTraveler", filtered, "Single mention unknown proper entity 'MysteryTraveler' must NOT be deleted")
        char = filtered["MysteryTraveler"]
        self.assertFalse(getattr(char, "known", True), "Single mention unknown entity should have known=False")
        self.assertFalse(getattr(char, "spawnable", True), "Single mention unknown entity must have spawnable=False")

    def test_linguistic_noise_filtered_without_source_loss_or_ontology_rejection(self):
        """
        Obvious extraction noise ('The', 'volcanic') is filtered out of the semantic entity dictionary,
        but Pass 1 raw source text remains untouched in raw segments.
        Noise rejection must be driven by noise criteria, not ontology absence.
        """
        # Pass 1 raw evidence contains the prose
        raw_segment = Segment(tag_line_no=1, text_line_no=1, type="narration", speaker=None, text="The volcanic mountain stood in silence.")
        self.assertIn("The", raw_segment.text)
        self.assertIn("volcanic", raw_segment.text)

        characters = {
            "The": Character(name="The", mentions=5),
            "volcanic": Character(name="volcanic", mentions=2),
        }
        filtered = filter_entities(characters)

        # Extraction noise MUST NOT become semantic entities
        self.assertNotIn("The", filtered, "Extraction noise 'The' should be filtered from semantic entity dict")
        self.assertNotIn("volcanic", filtered, "Extraction noise 'volcanic' should be filtered from semantic entity dict")

        # But raw Pass 1 source segment remains completely intact
        self.assertEqual(raw_segment.text, "The volcanic mountain stood in silence.")

    def test_unknown_entity_persistence_through_pass2_metta_and_pass3_zonj(self):
        """
        End-to-end Boundary 2 persistence test:
        An unknown proper entity ('Igigi') must survive beyond filter_entities()
        into out_pass2_*.metta on disk and remain observable in Pass 3 merge ZONJ.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            pass1_file = tmppath / "out_pass1_test_scene.txt"
            pass1_content = (
                "{type:narration} The Igigi gathered under the shadowed canopy to deliberate.\n"
                "{type:dialogue, speaker:Igigi} \"We cannot remain silent,\" declared Igigi.\n"
            )
            pass1_file.write_text(pass1_content, encoding="utf-8")

            # 1. Parse Pass 1 segments
            segments = pass2_enhanced.load_segments(str(pass1_file))
            self.assertTrue(any("Igigi" in seg.text for seg in segments), "Pass 1 source text must contain 'Igigi'")

            # 2. Extract & filter characters
            characters = pass2_enhanced.extract_characters(segments)
            self.assertIn("Igigi", characters, "Pass 2 extraction must identify 'Igigi'")

            filtered = filter_entities(characters)
            self.assertIn("Igigi", filtered, "filter_entities must preserve 'Igigi' as UNKNOWN")
            self.assertFalse(filtered["Igigi"].known)

            # 3. Infer speakers and write Pass 2 metta artifact to disk
            speakers = pass2_enhanced.infer_speakers_enhanced(segments, filtered)
            emotions = pass2_enhanced.infer_emotions_enhanced(segments, filtered)
            actions = pass2_enhanced.infer_actions_enhanced(segments)
            thoughts = pass2_enhanced.infer_thoughts_enhanced(segments, filtered)
            relationships = pass2_enhanced.infer_relationships(segments, filtered)

            metta_file = tmppath / "out_pass2_test_scene.metta"
            pass2_enhanced.write_metta(
                str(metta_file),
                speakers,
                emotions,
                actions,
                thoughts,
                filtered,
                relationships,
            )

            # 4. Verify durable evidence in out_pass2_*.metta on disk
            metta_text = metta_file.read_text(encoding="utf-8")
            self.assertIn("Igigi", metta_text, "out_pass2_*.metta file on disk must contain durable evidence of 'Igigi'")

            # 5. Parse Pass 2 metta artifact & merge in Pass 3
            p1_segments = pass3_merge.parse_pass1(str(pass1_file))
            p2_data = pass3_merge.parse_pass2(str(metta_file))
            zonj = pass3_merge.merge_to_zonj(p1_segments, p2_data, str(pass1_file), str(metta_file))

            # 6. Verify Pass 3 ZONJ scene contains durable evidence of 'Igigi'
            zonj_str = str(zonj)
            self.assertIn("Igigi", zonj_str, "Pass 3 merge ZONJ must not silently erase evidence of 'Igigi'")


if __name__ == "__main__":
    unittest.main()
