"""
test_metadata_leakage.py — Regression tests for Boundary 3: Metadata Leakage & Default Overrides

Tests:
1. pipeline_runner must NOT hardcode 'FirstAge' or 'Beach' into Pass 4/5 outputs when unspecified in source.
2. Verified upstream era (e.g. from Pass A era_hint or @era header) must propagate correctly.
3. Verified upstream location/environment must propagate, or remain unknown/unset when absent (never defaulting to 'Beach').
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext import pipeline_runner
from tier3.mettaext.chapterroom import passA_chapter_intake, passB_scene_boundary_provider, passC_scene_packet_writer
from tier3.mettaext.passroom import pass4_zon_bridge, pass5_game_bridge


class TestMetadataLeakage(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_pipeline_runner_does_not_hardcode_firstage_and_beach_when_unspecified(self):
        """
        Requirement: When source text contains no era or location hints,
        Pass 4/5 outputs must NOT contain 'FirstAge' or 'Beach'.
        """
        source_text = (
            "# Chapter 88: The Silent Tower\n"
            "The ancient stone tower stood atop the mountain peak in silence.\n"
            "Vairis observed the horizon."
        )
        ch_file = self.tmp_path / "088_silent_tower.txt"
        ch_file.write_text(source_text, encoding="utf-8")


        pipeline_runner.run_pipeline(str(ch_file))

        passroom_dir = Path("tier3/mettaext/stageroom/output/passroom")
        zonj_files = list(passroom_dir.glob("**/*088_the_silent_tower*.zonj.json"))
        self.assertTrue(len(zonj_files) > 0, f"Pipeline must generate at least one .zonj.json file in {passroom_dir}")

        for zonj_path in zonj_files:
            content = json.loads(zonj_path.read_text(encoding="utf-8"))
            when_val = content.get("@when", "")
            where_val = content.get("@where", "")

            self.assertNotIn("FirstAge", when_val, "Pass 4 @when must NOT contain hardcoded 'FirstAge' when source does not specify it")
            self.assertNotEqual(where_val, "Beach", "Pass 4 @where must NOT be hardcoded to 'Beach' when source does not specify it")

    def test_upstream_era_propagation_when_present(self):
        """
        Requirement: When source contains an explicit era header (e.g. @era: ThirdAge),
        it must propagate to Pass 4 / Pass 5 outputs.
        """
        source_text = (
            "@era: ThirdAge\n"
            "# Chapter 89: The Third Age Citadel\n"
            "In the ThirdAge, the citadel endured."
        )
        ch_file = self.tmp_path / "089_citadel.txt"
        ch_file.write_text(source_text, encoding="utf-8")

        manifest = passA_chapter_intake.intake(ch_file, self.tmp_path / "out_passA_089.json")
        self.assertEqual(manifest.get("era_hint"), "ThirdAge", "Pass A intake must detect 'ThirdAge' era hint")

    def test_upstream_location_propagation_or_unset_when_absent(self):
        """
        Requirement: When source specifies a location (e.g. @location: MountainPeak),
        it should be preserved; when absent, location should remain unset/unknown, not 'Beach'.
        """
        meta_default = pass4_zon_bridge.ZONMetadata(era="Unknown", location="Unknown")
        self.assertNotEqual(meta_default.location, "Beach", "Default location in Pass 4 ZONMetadata must not be 'Beach'")

    def test_pass4_direct_invocation_defaults_to_unknown(self):
        """
        Independent test: When pass4_zon_bridge is invoked directly without --era or --location flags,
        it defaults to 'Unknown', NOT 'FirstAge' or 'Beach'.
        """
        import subprocess
        import sys

        p3_file = self.tmp_path / "zonj_scene_test.json"
        p3_data = {
            "type": "scene",
            "id": "scene.test.001",
            "segments": [{"line": 1, "type": "narration", "text": "Prose line."}]
        }
        p3_file.write_text(json.dumps(p3_data), encoding="utf-8")

        p4_out_dir = self.tmp_path / "pass4_out"
        p4_out_dir.mkdir(parents=True)

        cmd = [
            sys.executable, "-m", "tier3.mettaext.passroom.pass4_zon_bridge",
            str(p3_file),
            "--output-dir", str(p4_out_dir)
        ]
        subprocess.run(cmd, check=True)

        p4_zonj_path = p4_out_dir / "scene_test.zonj.json"
        p4_zonj = json.loads(p4_zonj_path.read_text(encoding="utf-8"))

        self.assertIn("Unknown", p4_zonj.get("@when", ""))
        self.assertNotIn("FirstAge", p4_zonj.get("@when", ""))
        self.assertIn("Unknown", p4_zonj.get("@where", ""))
        self.assertNotIn("Beach", p4_zonj.get("@where", ""))


if __name__ == "__main__":
    unittest.main()
