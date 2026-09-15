"""
test_identity_hierarchy.py — Regression tests for Repair Boundary 1: Identity Hierarchy & Propagation

Tests:
1. Distinct canonical chapter_ids for chapters with identical filename stems under different books.
2. Explicit parent chapter_id traceability in scene packets and downstream scene artifacts (Passes 3-5).
3. Propagation of Pass A chapter_id by pipeline_runner without filename stem re-derivation.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext.chapterroom import passA_chapter_intake
from tier3.mettaext.chapterroom import passB_scene_boundary_provider
from tier3.mettaext.chapterroom import passC_scene_packet_writer
from tier3.mettaext.passroom import pass1_explicit
from tier3.mettaext.passroom import pass2_enhanced
from tier3.mettaext.passroom import pass3_merge
from tier3.mettaext.passroom import pass4_zon_bridge
from tier3.mettaext.passroom import pass5_game_bridge


class TestIdentityHierarchy(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_same_stem_different_books_distinct_chapter_ids(self):
        """
        Requirement 1: Two chapters with the same filename stem ('015_the_choice.txt')
        under different books must retain distinct canonical chapter_ids.
        """
        ch1_text = "@book: book001\n@title: The Choice\n# Chapter 15: The Choice\nThe Igigi weighed their options."
        ch2_text = "@book: book002\n@title: The Choice\n# Chapter 15: The Choice\nIn another era, the choice remained."

        dir1 = self.tmp_path / "book001"
        dir2 = self.tmp_path / "book002"
        dir1.mkdir(parents=True)
        dir2.mkdir(parents=True)

        file1 = dir1 / "015_the_choice.txt"
        file2 = dir2 / "015_the_choice.txt"
        file1.write_text(ch1_text, encoding="utf-8")
        file2.write_text(ch2_text, encoding="utf-8")

        manifest1 = passA_chapter_intake.intake(file1, dir1 / "out_passA_015_the_choice.json")
        manifest2 = passA_chapter_intake.intake(file2, dir2 / "out_passA_015_the_choice.json")

        id1 = manifest1["chapter_id"]
        id2 = manifest2["chapter_id"]

        # Assert Pass A establishes distinct chapter IDs
        self.assertNotEqual(id1, id2, "Chapters from different books with the same filename stem must have distinct chapter_ids")
        self.assertIn("book001", id1)
        self.assertIn("book002", id2)

    def test_pipeline_runner_propagates_passA_chapter_id(self):
        """
        Test that pipeline_runner passes Pass A's chapter_id to stageroom_manifest
        rather than re-deriving source_text_id from chapter_path.stem.
        """
        import inspect
        from tier3.mettaext import pipeline_runner

        source = inspect.getsource(pipeline_runner.run_pipeline)
        self.assertNotIn(
            "source_text_id = chapter_path.stem",
            source,
            "FAIL: pipeline_runner.py re-derives source_text_id from chapter_path.stem instead of propagating Pass A chapter_id"
        )
        self.assertIn(
            '"--source-text-id", chapter_id',
            source,
            "FAIL: pipeline_runner.py must pass Pass A chapter_id directly to stageroom_manifest"
        )

    def test_scene_id_traceable_parent_chapter_id(self):
        """
        Requirement 2: Every scene_id must retain an explicit traceable parent chapter_id;
        downstream consumers must not infer the parent from filenames.
        """
        ch_text = "@book: book001\n# Chapter 15: The Choice\nLine 1 narration.\n\n\nLine 2 narration."
        file_path = self.tmp_path / "015_the_choice.txt"
        file_path.write_text(ch_text, encoding="utf-8")

        # Pass A
        manifestA = passA_chapter_intake.intake(file_path, self.tmp_path / "out_passA_015_the_choice.json")
        canonical_chapter_id = manifestA["chapter_id"]

        # Pass B
        proposalB = passB_scene_boundary_provider.choose_boundaries(manifestA, target_words=900)
        self.assertEqual(proposalB["chapter_id"], canonical_chapter_id)
        for scene in proposalB["scenes"]:
            self.assertEqual(scene["chapter_id"], canonical_chapter_id)

        # Pass C
        indexC = passC_scene_packet_writer.write_packets(proposalB, self.tmp_path)
        self.assertEqual(indexC["chapter_id"], canonical_chapter_id)

        # Inspect packet header
        packet_info = indexC["packets"][0]
        packet_path = Path(packet_info["packet_path"])
        packet_content = packet_path.read_text(encoding="utf-8")
        self.assertIn(f"@chapter_id: {canonical_chapter_id}", packet_content)
        self.assertIn(f"@scene_id: {packet_info['scene_id']}", packet_content)

        # Pass 1
        p1_out = self.tmp_path / "out_pass1_test.txt"
        pass1_explicit.process_file(packet_path, p1_out)

        # Pass 2
        p2_segments = pass2_enhanced.load_segments(str(p1_out))
        p2_chars = pass2_enhanced.extract_characters(p2_segments)
        p2_speakers = pass2_enhanced.infer_speakers_enhanced(p2_segments, p2_chars)
        p2_emotions = pass2_enhanced.infer_emotions_enhanced(p2_segments, p2_chars)
        p2_actions = pass2_enhanced.infer_actions_enhanced(p2_segments)
        p2_thoughts = pass2_enhanced.infer_thoughts_enhanced(p2_segments, p2_chars)
        p2_rels = pass2_enhanced.infer_relationships(p2_segments, p2_chars)
        p2_out = self.tmp_path / "out_pass2_test.metta"
        pass2_enhanced.write_metta(str(p2_out), p2_speakers, p2_emotions, p2_actions, p2_thoughts, p2_chars, p2_rels)

        # Pass 3
        p3_segments = pass3_merge.parse_pass1(str(p1_out))
        p3_p2data = pass3_merge.parse_pass2(str(p2_out))
        p3_zonj = pass3_merge.merge_to_zonj(
            p3_segments,
            p3_p2data,
            str(p1_out),
            str(p2_out),
            scene_id=packet_info['scene_id'],
            chapter_id=canonical_chapter_id,
        )

        # Pass 3 output check: chapter_id and scene id must be present
        self.assertIn("chapter_id", p3_zonj, "Pass 3 ZONJ must preserve explicit chapter_id")
        self.assertEqual(p3_zonj["chapter_id"], canonical_chapter_id, "Pass 3 ZONJ chapter_id must match Pass A canonical chapter_id")
        self.assertEqual(p3_zonj["id"], packet_info['scene_id'], "Pass 3 ZONJ id must match scene_id from packet index")

    def test_pass4_pass5_identity_propagation_misleading_filename(self):
        """
        Test identity propagation through Pass 4 and Pass 5 with a deliberately misleading filename.
        Ensures downstream passes read scene_id and chapter_id from payload rather than inferring from filename.
        """
        canonical_chapter_id = "chapter.book001.015_the_choice"
        canonical_scene_id = "scene.book001.015_the_choice.scene001"

        zonj_data = {
            "type": "scene",
            "id": canonical_scene_id,
            "chapter_id": canonical_chapter_id,
            "segments": [
                {
                    "line": 1,
                    "type": "narration",
                    "text": "The Igigi weighed their choices."
                }
            ]
        }

        # Save with a deliberately misleading filename
        misleading_file = self.tmp_path / "zonj_totally_wrong_name.json"
        misleading_file.write_text(json.dumps(zonj_data), encoding="utf-8")

        # --- Pass 4 ---
        bridge4 = pass4_zon_bridge.ZONBridge()
        p4_meta = pass4_zon_bridge.ZONMetadata(era="FirstAge", location="Beach")
        p4_zonj = bridge4.convert_to_zonj(misleading_file, p4_meta)

        # Assert Pass 4 preserves canonical scene_id (ignoring misleading filename)
        self.assertEqual(
            p4_zonj.get("@id"),
            canonical_scene_id,
            f"FAIL: Pass 4 converted @id to '{p4_zonj.get('@id')}' instead of preserving canonical scene_id '{canonical_scene_id}'"
        )

        # Assert Pass 4 preserves explicit @chapter_id from payload
        self.assertIn(
            "@chapter_id",
            p4_zonj,
            "FAIL: Pass 4 ZONJ output drops explicit @chapter_id from payload"
        )
        self.assertEqual(
            p4_zonj.get("@chapter_id"),
            canonical_chapter_id,
            f"FAIL: Pass 4 @chapter_id is '{p4_zonj.get('@chapter_id')}' instead of '{canonical_chapter_id}'"
        )

        # --- Pass 5 ---
        bridge5 = pass5_game_bridge.GameBridge()
        p5_game = bridge5.convert_zon_to_game(p4_zonj)

        # Assert Pass 5 preserves canonical scene_id
        self.assertEqual(
            p5_game.get("scene_id"),
            canonical_scene_id,
            f"FAIL: Pass 5 scene_id is '{p5_game.get('scene_id')}' instead of '{canonical_scene_id}'"
        )

        # Assert Pass 5 metadata preserves explicit chapter_id
        self.assertIn(
            "chapter_id",
            p5_game.get("metadata", {}),
            "FAIL: Pass 5 game scene metadata drops explicit chapter_id"
        )
        self.assertEqual(
            p5_game.get("metadata", {}).get("chapter_id"),
            canonical_chapter_id,
            f"FAIL: Pass 5 metadata chapter_id is '{p5_game.get('metadata', {}).get('chapter_id')}' instead of '{canonical_chapter_id}'"
        )


if __name__ == "__main__":
    unittest.main()


