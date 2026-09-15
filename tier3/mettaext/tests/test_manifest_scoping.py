"""
test_manifest_scoping.py — Regression tests for Boundary 4: Manifest Artifact Scoping

Tests:
1. build_manifest(source_text_id, stageroom_root) must only include artifacts belonging to source_text_id (and its child scene packets).
2. Coexisting chapters: manifest(A) contains only A artifacts, manifest(B) contains only B artifacts.
3. Deliberately misleading filenames: resolved strictly by JSON payload content provenance, not filename substrings.
4. Multiple scene IDs under one chapter: manifest includes all and only that chapter's children.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext import stageroom_manifest


class TestManifestScoping(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_manifest_scoped_to_source_text_id_without_cross_chapter_leakage(self):
        """
        Requirement: Building a stageroom manifest for Chapter A (chapter.book001.001_first)
        must list ONLY Chapter A artifacts and its child scene packets,
        excluding Chapter B (chapter.book002.002_second) artifacts present in stageroom.
        """
        ch_root = self.tmp_path / "output" / "chapterroom"
        pass_root = self.tmp_path / "output" / "passroom"

        # Chapter A setup
        chA_id = "chapter.book001.001_first"
        chA_packets_dir = ch_root / "scene_packets" / chA_id
        chA_packets_dir.mkdir(parents=True)
        (ch_root / "out_passA_001_first.json").write_text(
            json.dumps({"contract": "engain.chapter_intake_manifest.v1", "chapter_id": chA_id}), encoding="utf-8"
        )
        (chA_packets_dir / "scene_packets_index.json").write_text(
            json.dumps({"chapter_id": chA_id, "packets": [{"scene_id": "scene.book001.001_first.scene001"}]}), encoding="utf-8"
        )
        (chA_packets_dir / "scene.book001.001_first.scene001.txt").write_text("Chapter A text", encoding="utf-8")

        chA_scene_dir = pass_root / "scene.book001.001_first.scene001"
        (chA_scene_dir / "game_scenes").mkdir(parents=True)
        (chA_scene_dir / "out_pass1_scene.book001.001_first.scene001.txt").write_text("Pass 1 text", encoding="utf-8")
        (chA_scene_dir / "game_scenes" / "scene.book001.001_first.scene001.json").write_text(
            json.dumps({"scene_id": "scene.book001.001_first.scene001"}), encoding="utf-8"
        )

        # Chapter B setup
        chB_id = "chapter.book002.002_second"
        chB_packets_dir = ch_root / "scene_packets" / chB_id
        chB_packets_dir.mkdir(parents=True)
        (ch_root / "out_passA_002_second.json").write_text(
            json.dumps({"contract": "engain.chapter_intake_manifest.v1", "chapter_id": chB_id}), encoding="utf-8"
        )
        (chB_packets_dir / "scene_packets_index.json").write_text(
            json.dumps({"chapter_id": chB_id, "packets": [{"scene_id": "scene.book002.002_second.scene001"}]}), encoding="utf-8"
        )
        (chB_packets_dir / "scene.book002.002_second.scene001.txt").write_text("Chapter B text", encoding="utf-8")

        chB_scene_dir = pass_root / "scene.book002.002_second.scene001"
        (chB_scene_dir / "game_scenes").mkdir(parents=True)
        (chB_scene_dir / "out_pass1_scene.book002.002_second.scene001.txt").write_text("Pass 1 text", encoding="utf-8")
        (chB_scene_dir / "game_scenes" / "scene.book002.002_second.scene001.json").write_text(
            json.dumps({"scene_id": "scene.book002.002_second.scene001"}), encoding="utf-8"
        )

        # Generate manifest for Chapter A
        manifestA = stageroom_manifest.build_manifest(source_text_id=chA_id, stageroom_root=self.tmp_path)
        chA_artifacts = manifestA["artifacts"]["chapterroom"]
        passA_artifacts = manifestA["artifacts"]["passroom"]
        gameA_candidates = manifestA["artifacts"]["game_scene_candidates"]

        self.assertTrue(any("001_first" in art for art in chA_artifacts), "Chapter A artifacts must be included")
        for art in chA_artifacts + passA_artifacts + gameA_candidates:
            self.assertNotIn("002_second", art, "Chapter B artifacts must NOT bleed into Chapter A manifest")

        # Generate manifest for Chapter B
        manifestB = stageroom_manifest.build_manifest(source_text_id=chB_id, stageroom_root=self.tmp_path)
        chB_artifacts = manifestB["artifacts"]["chapterroom"]
        passB_artifacts = manifestB["artifacts"]["passroom"]
        gameB_candidates = manifestB["artifacts"]["game_scene_candidates"]

        self.assertTrue(any("002_second" in art for art in chB_artifacts), "Chapter B artifacts must be included")
        for art in chB_artifacts + passB_artifacts + gameB_candidates:
            self.assertNotIn("001_first", art, "Chapter A artifacts must NOT bleed into Chapter B manifest")

    def test_misleading_filename_resolved_by_content_provenance(self):
        """
        Requirement: Ownership must be proven by JSON payload content, not filename stems.
        A file named 'out_passA_chapterB_totally_fake.json' whose JSON payload says
        'chapter_id': 'chapter.book001.001_first' belongs to Chapter A, NOT Chapter B.
        """
        ch_root = self.tmp_path / "output" / "chapterroom"

        chA_id = "chapter.book001.001_first"
        chB_id = "chapter.book002.002_second"

        # Create Pass A manifest with misleading filename 'out_passA_chapterB_fake.json'
        misleading_file = ch_root / "out_passA_chapterB_fake.json"
        misleading_file.parent.mkdir(parents=True, exist_ok=True)
        misleading_file.write_text(
            json.dumps({"contract": "engain.chapter_intake_manifest.v1", "chapter_id": chA_id}), encoding="utf-8"
        )

        manifestA = stageroom_manifest.build_manifest(source_text_id=chA_id, stageroom_root=self.tmp_path)
        manifestB = stageroom_manifest.build_manifest(source_text_id=chB_id, stageroom_root=self.tmp_path)

        # Must belong to Chapter A manifest because payload says chapter_id = chA_id
        self.assertTrue(
            any("out_passA_chapterB_fake.json" in art for art in manifestA["artifacts"]["chapterroom"]),
            "Misleading file with Chapter A payload must be included in Chapter A manifest"
        )

        # Must NOT belong to Chapter B manifest despite the 'chapterB' substring in filename
        self.assertFalse(
            any("out_passA_chapterB_fake.json" in art for art in manifestB["artifacts"]["chapterroom"]),
            "Misleading file with Chapter A payload must NOT be included in Chapter B manifest"
        )

    def test_multiple_scene_ids_under_one_chapter(self):
        """
        Requirement: Multiple scene IDs under one chapter must all be collected,
        and only child scenes belonging to that chapter's scene packet index are included.
        """
        ch_root = self.tmp_path / "output" / "chapterroom"
        pass_root = self.tmp_path / "output" / "passroom"

        ch_id = "chapter.book001.005_multi"
        ch_packets_dir = ch_root / "scene_packets" / ch_id
        ch_packets_dir.mkdir(parents=True)

        scene1 = "scene.book001.005_multi.scene001"
        scene2 = "scene.book001.005_multi.scene002"

        (ch_root / "out_passA_005_multi.json").write_text(
            json.dumps({"chapter_id": ch_id}), encoding="utf-8"
        )
        (ch_packets_dir / "scene_packets_index.json").write_text(
            json.dumps({"chapter_id": ch_id, "packets": [{"scene_id": scene1}, {"scene_id": scene2}]}), encoding="utf-8"
        )
        (ch_packets_dir / f"{scene1}.txt").write_text("s1 text", encoding="utf-8")
        (ch_packets_dir / f"{scene2}.txt").write_text("s2 text", encoding="utf-8")

        # Passroom outputs for both scenes
        for sid in [scene1, scene2]:
            sdir = pass_root / sid
            (sdir / "game_scenes").mkdir(parents=True)
            (sdir / f"out_pass1_{sid}.txt").write_text("p1", encoding="utf-8")
            (sdir / "game_scenes" / f"{sid}.json").write_text(json.dumps({"scene_id": sid}), encoding="utf-8")

        manifest = stageroom_manifest.build_manifest(source_text_id=ch_id, stageroom_root=self.tmp_path)
        passroom_arts = manifest["artifacts"]["passroom"]
        game_cands = manifest["artifacts"]["game_scene_candidates"]

        self.assertTrue(any("scene001" in art for art in passroom_arts), "scene001 artifacts must be included")
        self.assertTrue(any("scene002" in art for art in passroom_arts), "scene002 artifacts must be included")
        self.assertTrue(any("scene001" in art for art in game_cands), "scene001 game candidate must be included")
        self.assertTrue(any("scene002" in art for art in game_cands), "scene002 game candidate must be included")


if __name__ == "__main__":
    unittest.main()
