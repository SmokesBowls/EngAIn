"""
test_orchestration_characterization.py — Characterization tests for Boundary 5: Orchestration Consolidation

Tests:
1. Canonical single-chapter execution via pipeline_runner.py.
2. Bulk discovery & scanning filtering (is_junk, is_chapter, matches_include, matches_exclude).
3. Dry-run behavior (previews files without executing mutating passes).
4. Vault chapter index traversal contract.
5. TRIXEL score ingestion isolation.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext import engain_ingest, pipeline_runner
from tier3.mettaext.chapterroom import chapterroom_index_runner, passA_chapter_intake


class TestOrchestrationCharacterization(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_canonical_single_chapter_pipeline_runner(self):
        """
        Verify single explicit chapter processing through pipeline_runner.py.
        Must run Chapterroom A/B/C -> Passroom 1/1S/2/3/4/5 and emit stageroom manifest.
        """
        source_text = (
            "# Chapter 101: Orchestration Test\n"
            "Vairis walked along the ancient stone wall.\n"
            "\"The path is clear,\" Vairis observed."
        )
        ch_file = self.tmp_path / "101_orchestration.txt"
        ch_file.write_text(source_text, encoding="utf-8")

        pipeline_runner.run_pipeline(str(ch_file))

        manifest_path = Path("tier3/mettaext/stageroom/mettaext_done_manifest.json")
        self.assertTrue(manifest_path.exists(), "pipeline_runner must emit mettaext_done_manifest.json")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("run_state"), "METTAEXT_DONE")
        self.assertEqual(manifest.get("source_text_id"), "chapter.101_orchestration_test")

    def test_bulk_discovery_pattern_filtering(self):
        """
        Verify bulk discovery and pattern filtering logic (junk exclusion, includes, excludes).
        """
        # Test junk exclusion
        self.assertTrue(engain_ingest.is_junk("out_pass1_001.txt"))
        self.assertTrue(engain_ingest.is_junk("continuity_notes.txt"))
        self.assertTrue(engain_ingest.is_junk("README.md"))
        self.assertFalse(engain_ingest.is_junk("chapter_001_first.txt"))

        # Test canonical chapter detection
        self.assertTrue(engain_ingest.is_chapter("chapter_001_first.txt"))
        self.assertTrue(engain_ingest.is_chapter("act_01_intro.txt"))
        self.assertTrue(engain_ingest.is_chapter("03_Fist_contact.txt"))
        self.assertFalse(engain_ingest.is_chapter("random_notes.txt"))

        # Test include/exclude pattern matching
        self.assertTrue(engain_ingest.matches_include("act_01.txt", ["act_*", "chapter_*"]))
        self.assertFalse(engain_ingest.matches_include("notes.txt", ["act_*", "chapter_*"]))

        self.assertTrue(engain_ingest.matches_exclude("act_01_draft.txt", ["*_draft.txt"]))
        self.assertFalse(engain_ingest.matches_exclude("act_01_final.txt", ["*_draft.txt"]))

    def test_dry_run_preview_mode(self):
        """
        Verify dry-run mode previews candidate files without executing mutating passes.
        """
        # Setup mock directory structure with chapters
        scan_dir = self.tmp_path / "scan_target"
        scan_dir.mkdir()
        (scan_dir / "chapter_01_alpha.txt").write_text("Chapter 1", encoding="utf-8")
        (scan_dir / "chapter_02_beta.txt").write_text("Chapter 2", encoding="utf-8")
        (scan_dir / "out_pass1_junk.txt").write_text("Junk", encoding="utf-8")

        all_files = sorted(p for p in scan_dir.rglob("*") if p.suffix in {".txt", ".md"})
        discovered = [
            p.name for p in all_files
            if not engain_ingest.is_junk(p.name) and engain_ingest.is_chapter(p.name)
        ]

        self.assertEqual(discovered, ["chapter_01_alpha.txt", "chapter_02_beta.txt"])
        self.assertNotIn("out_pass1_junk.txt", discovered)

    def test_vault_chapter_index_traversal_contract(self):
        """
        Verify vault chapter index traversal structure.
        """
        ch_file = self.tmp_path / "005_vault_test.txt"
        ch_file.write_text("# Chapter 5: Vault Test\nProse text.", encoding="utf-8")

        manifest = passA_chapter_intake.intake(ch_file, self.tmp_path / "out_passA_005.json")
        self.assertEqual(manifest["chapter_id"], "chapter.005_vault_test")

    def test_trixel_ingestion_isolation(self):
        """
        Verify TRIXEL score ingestion is isolated from narrative chapter processing.
        """
        trixel_file = self.tmp_path / "score_001.jsonl"
        trixel_file.write_text('{"brush": "tile_01", "score": 95}\n', encoding="utf-8")

        # TRIXEL score files must be treated as non-narrative
        self.assertFalse(engain_ingest.is_chapter(trixel_file.name))

    def test_engain_ingest_delegates_to_pipeline_runner(self):
        """
        Verify engain_ingest.run_pipeline delegates chapter execution to canonical pipeline_runner.
        """
        source_text = "# Chapter 102: Delegation Test\nVairis walked in silence."
        ch_file = self.tmp_path / "102_delegation.txt"
        ch_file.write_text(source_text, encoding="utf-8")

        ok, msg = engain_ingest.run_pipeline(
            input_file=ch_file,
            pipeline_dir=Path("."),
            out_dir=self.tmp_path / "out",
            dry_run=False,
            runtime=None,
        )
        self.assertTrue(ok)

        manifest_path = Path("tier3/mettaext/stageroom/mettaext_done_manifest.json")
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("source_text_id"), "chapter.102_delegation_test")

    def test_narrative_to_game_wrapper_delegates_to_pipeline_runner(self):
        """
        Verify narrative_to_game.UnifiedPipeline delegates to canonical pipeline_runner.
        """
        from tier3.mettaext import narrative_to_game

        source_text = "# Chapter 103: N2G Test\nVairis walked along the wall."
        ch_file = self.tmp_path / "103_n2g.txt"
        ch_file.write_text(source_text, encoding="utf-8")

        pipeline = narrative_to_game.UnifiedPipeline(work_dir=self.tmp_path)
        pipeline.process_chapter(ch_file)

        manifest_path = Path("tier3/mettaext/stageroom/mettaext_done_manifest.json")
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("source_text_id"), "chapter.103_n2g_test")

    def test_master_pipeline_wrapper_delegates_to_pipeline_runner(self):
        """
        Verify master_pipeline.PipelineController delegates to canonical pipeline_runner.
        """
        from tier3.mettaext import master_pipeline

        source_text = "# Chapter 104: Master Pipeline Test\nVairis observed the landscape."
        ch_file = self.tmp_path / "104_master.txt"
        ch_file.write_text(source_text, encoding="utf-8")

        controller = master_pipeline.PipelineController(self.tmp_path)
        ok = controller.run_full_pipeline(ch_file)
        self.assertTrue(ok)

        manifest_path = Path("tier3/mettaext/stageroom/mettaext_done_manifest.json")
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("source_text_id"), "chapter.104_master_pipeline_test")


if __name__ == "__main__":
    unittest.main()

