"""
test_authored_scene_boundary_splitter.py -- Regression tests for the
2026-09-19 authored-scene-marker splitter (engain-avatar-audit:
09-19-2026-scene-boundary-splitter-traced.md,
09-19-2026-scene-boundary-splitter-design-corrected-no-day-rule.md).

Covers, in order:
  1. split_by_authored_scene_markers() unit behavior in isolation.
  2. choose_boundaries() end-to-end with synthetic text (authored path
     and the unchanged fallback path).
  3. passC_scene_packet_writer.py carrying scene_meta into the actual
     packet file and index entry.
  4. Book 1 acceptance: real vault chapters 1-4 produce exactly the
     authored scene counts (1, 1, 7, 1), skipped gracefully if the
     real vault isn't present in this environment.
  5. End-to-end confirmation that Pass 2's manifestation inference
     (fc3e3d1) still finds "participants:" and classifies Vaelith/
     Pelagor correctly after this segmentation change.

No day N special-casing is tested for *correctness* here, only for
*harmlessness* -- per the corrected design, day N lines get no
recognition at all and are expected to fall wherever plain marker-to-
marker chunking puts them.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tier3.mettaext.chapterroom import (
    passA_chapter_intake,
    passB_scene_boundary_provider,
    passC_scene_packet_writer,
)
from tier3.mettaext.passroom import pass1_explicit, pass2_enhanced, pass2_entity_filter
from tier3.mettaext import world_rules_loader

VAULT_BOOK1_DIR = Path(
    "/home/mytruelove/Downloads/obsidianburdenNov25/book_01_book_of_genesis"
)
WORLD_RULES_FILE = Path("tier1/engainos/assets/world_rules.json")


class TestSplitByAuthoredSceneMarkers(unittest.TestCase):
    def test_single_marker_with_scene_meta(self):
        text = (
            "book 1\n"
            "chapter 002-molten descent\n"
            "\n"
            "day 0\n"
            "\n"
            "scene 002.1 — molten descent\n"
            "\n"
            "scene meta:\n"
            "location: Akashic threshold / Earth coastline landing beach\n"
            "time: day 0, landing through sunset\n"
            "participants: Senareth, Elyraen, Vairis\n"
            "focus: The Nephoretti descend and land.\n"
            "continuity: Immediately follows chapter 001\n"
            "\n"
            "Prose begins here. Senareth stood.\n"
            "\n"
            "end of chapter 002-molten descent\n"
        )
        lines = text.splitlines()
        chunks = passB_scene_boundary_provider.split_by_authored_scene_markers(lines)
        self.assertEqual(len(chunks), 1)
        start, end, chunk_text, meta = chunks[0]
        self.assertEqual(
            meta,
            {
                "location": "Akashic threshold / Earth coastline landing beach",
                "time": "day 0, landing through sunset",
                "participants": "Senareth, Elyraen, Vairis",
                "focus": "The Nephoretti descend and land.",
                "continuity": "Immediately follows chapter 001",
            },
        )
        # Raw scene meta: lines must still be present verbatim in the text --
        # Pass 2 depends on scanning for "participants:" directly.
        self.assertIn("participants: Senareth, Elyraen, Vairis", chunk_text)
        # Chapter-level header lines (book/chapter/day) must NOT be in this
        # scene's text -- they precede the marker.
        self.assertNotIn("chapter 002-molten descent\n\nday 0", chunk_text)
        self.assertIn("Prose begins here. Senareth stood.", chunk_text)
        self.assertIn("end of chapter 002-molten descent", chunk_text)

    def test_multiple_markers_produce_multiple_chunks(self):
        text = (
            "book 1\nchapter 003-first contact\n\n"
            "day 1\n\nscene 003.1 — first night on the beach\n\n"
            "scene meta:\nlocation: Beach\nparticipants: Zephyr\n\n"
            "First scene prose.\n\n"
            "day 2\n\nscene 003.2 — failed approach\n\n"
            "scene meta:\nlocation: Beach\nparticipants: Zephyr, Torrhen\n\n"
            "Second scene prose.\n"
        )
        lines = text.splitlines()
        chunks = passB_scene_boundary_provider.split_by_authored_scene_markers(lines)
        self.assertEqual(len(chunks), 2)
        self.assertIn("First scene prose.", chunks[0][2])
        self.assertIn("participants: Zephyr\n", chunks[0][2])
        self.assertIn("Second scene prose.", chunks[1][2])
        self.assertEqual(chunks[1][3]["participants"], "Zephyr, Torrhen")

    def test_no_markers_returns_empty(self):
        text = "Just plain prose.\n\nNo scene markers anywhere in this text.\n"
        chunks = passB_scene_boundary_provider.split_by_authored_scene_markers(
            text.splitlines()
        )
        self.assertEqual(chunks, [])

    def test_generic_keys_not_hardcoded(self):
        """Chapter 18's scene meta introduces presentation/cutscene purpose --
        keys absent from Book 1 -- and they must be captured without any
        splitter change, proving the parser is genuinely generic."""
        text = (
            "scene 018.2 — the lessons begin: silence and touch\n\n"
            "scene meta:\n"
            "location: Sol-3 Surface (Torrhen's Ice Cave)\n"
            "time: year 14,014\n"
            "participants: Zephyr, Torrhen\n"
            "focus: Torrhen teaches Zephyr mental silence.\n"
            "continuity: Days after arrival in scene 018.1\n"
            "presentation: playable-cutscene\n"
            "cutscene purpose: Zephyr's first hybrid ice-shaping.\n"
            "\n"
            "Prose.\n"
        )
        chunks = passB_scene_boundary_provider.split_by_authored_scene_markers(
            text.splitlines()
        )
        self.assertEqual(len(chunks), 1)
        meta = chunks[0][3]
        self.assertEqual(meta["presentation"], "playable-cutscene")
        self.assertEqual(meta["cutscene purpose"], "Zephyr's first hybrid ice-shaping.")

    def test_time_value_preserved_opaque(self):
        """time: must never be parsed -- preserved exactly as authored,
        including compound/relative annotations."""
        text = (
            "scene 020.1 — the discovery: the avalanche rescue\n\n"
            "scene meta:\n"
            "location: Sol-3 Surface\n"
            "time: year 14,032 (fifteen years after the Great Flood in scene 019.2)\n"
            "participants: The Sage, Torrhen\n"
            "\n"
            "Prose.\n"
        )
        chunks = passB_scene_boundary_provider.split_by_authored_scene_markers(
            text.splitlines()
        )
        meta = chunks[0][3]
        self.assertEqual(
            meta["time"],
            "year 14,032 (fifteen years after the Great Flood in scene 019.2)",
        )

    def test_legacy_day_line_is_not_specially_recognized(self):
        """A 'day N' line before a scene marker is ordinary chapter-level
        text, excluded from the following scene's chunk -- not folded in,
        not treated as an error. Confirms the corrected (no special rule)
        design is actually what's implemented."""
        text = (
            "book 1\nchapter 001-the ethereal vigil\n\n"
            "day 0\n\n"
            "scene 001.1 — the ethereal vigil\n\n"
            "scene meta:\nparticipants: Lyaris\n\n"
            "Prose.\n"
        )
        chunks = passB_scene_boundary_provider.split_by_authored_scene_markers(
            text.splitlines()
        )
        self.assertEqual(len(chunks), 1)
        self.assertNotIn("day 0", chunks[0][2])

    def test_marker_regex_does_not_confuse_chapter_title_hyphen(self):
        """'chapter 002-molten descent' (no surrounding spaces around the
        hyphen) must never be mistaken for a 'scene NNN.x — title' marker
        (space-dash-space)."""
        text = "chapter 002-molten descent\n\nscene 002.1 — molten descent\n\nProse.\n"
        chunks = passB_scene_boundary_provider.split_by_authored_scene_markers(
            text.splitlines()
        )
        self.assertEqual(len(chunks), 1)
        self.assertNotIn("chapter 002-molten descent", chunks[0][2])


class TestChooseBoundariesIntegration(unittest.TestCase):
    def _manifest(self, chapter_id: str, raw_text: str) -> dict:
        return {"contract": "engain.chapter_intake_manifest.v1", "chapter_id": chapter_id, "raw_text": raw_text}

    def test_authored_markers_set_authority_state_and_proven(self):
        raw_text = (
            "book 1\nchapter 001-test\n\nday 0\n\n"
            "scene 001.1 — only scene\n\nscene meta:\nparticipants: Vaelith\n\n"
            "Prose.\n"
        )
        proposal = passB_scene_boundary_provider.choose_boundaries(
            self._manifest("chapter.001_test", raw_text), target_words=900
        )
        self.assertEqual(proposal["boundary_method"], "authored_scene_marker")
        self.assertEqual(proposal["authority_state"], "SCENE_BOUNDARY_AUTHORED")
        self.assertTrue(proposal["authored_scene_boundaries_proven"])
        self.assertEqual(proposal["scene_count"], 1)
        scene = proposal["scenes"][0]
        self.assertEqual(scene["authority_state"], "SCENE_BOUNDARY_AUTHORED")
        self.assertTrue(scene["authored_scene_boundaries_proven"])
        self.assertEqual(scene["scene_meta"], {"participants": "Vaelith"})

    def test_no_markers_falls_back_unchanged(self):
        """Regression pin: chapters with no authored markers must produce
        exactly the same fallback behavior as before this change."""
        raw_text = "# Chapter 15: The Choice\nLine 1 narration.\n\n\nLine 2 narration."
        proposal = passB_scene_boundary_provider.choose_boundaries(
            self._manifest("chapter.015_the_choice", raw_text), target_words=900
        )
        self.assertNotEqual(proposal["boundary_method"], "authored_scene_marker")
        self.assertFalse(proposal["authored_scene_boundaries_proven"])
        for scene in proposal["scenes"]:
            self.assertNotIn("scene_meta", scene)


class TestPassCCarriesSceneMeta(unittest.TestCase):
    def test_packet_text_includes_scene_meta_header_lines(self):
        proposal = passB_scene_boundary_provider.choose_boundaries(
            {
                "contract": "engain.chapter_intake_manifest.v1",
                "chapter_id": "chapter.002_test",
                "raw_text": (
                    "book 1\nchapter 002-test\n\nday 0\n\n"
                    "scene 002.1 — only scene\n\n"
                    "scene meta:\nparticipants: Senareth\ncutscene purpose: Landing.\n\n"
                    "Prose.\n"
                ),
            },
            target_words=900,
        )
        with tempfile.TemporaryDirectory() as td:
            index = passC_scene_packet_writer.write_packets(proposal, Path(td))
            packet_path = Path(index["packets"][0]["packet_path"])
            packet_text = packet_path.read_text(encoding="utf-8")
        self.assertIn("@scene_meta_participants: Senareth", packet_text)
        self.assertIn("@scene_meta_cutscene_purpose: Landing.", packet_text)
        self.assertEqual(
            index["packets"][0]["scene_meta"],
            {"participants": "Senareth", "cutscene purpose": "Landing."},
        )


@unittest.skipUnless(VAULT_BOOK1_DIR.is_dir(), "real Book 1 vault not present in this environment")
class TestBook1AcceptanceRealVault(unittest.TestCase):
    """The exact acceptance case from the implementation instruction:
    Ch1->1, Ch2->1, Ch3->7, Ch4->1, run against the real vault text."""

    EXPECTED = {
        "001_the_ethereal_vigil.md": 1,
        "002_molten_descent.md": 1,
        "003_first_contact.md": 7,
        "004_the_convergence.md": 1,
    }

    def test_book1_scene_counts(self):
        for filename, expected_count in self.EXPECTED.items():
            path = VAULT_BOOK1_DIR / filename
            manifest = passA_chapter_intake.intake(path, None)
            proposal = passB_scene_boundary_provider.choose_boundaries(manifest, target_words=900)
            self.assertEqual(
                proposal["scene_count"], expected_count,
                f"{filename}: expected {expected_count} authored scenes, got {proposal['scene_count']}",
            )
            self.assertEqual(proposal["boundary_method"], "authored_scene_marker")
            self.assertTrue(proposal["authored_scene_boundaries_proven"])

    def test_chapter2_scene_meta_matches_known_real_text(self):
        path = VAULT_BOOK1_DIR / "002_molten_descent.md"
        manifest = passA_chapter_intake.intake(path, None)
        proposal = passB_scene_boundary_provider.choose_boundaries(manifest, target_words=900)
        meta = proposal["scenes"][0]["scene_meta"]
        self.assertEqual(
            meta["participants"],
            "Senareth, Elyraen, Vairis, Olythae, Nephoretti assembly, Mordain, transformed Pelagor (Giants)",
        )


@unittest.skipUnless(VAULT_BOOK1_DIR.is_dir(), "real Book 1 vault not present in this environment")
class TestManifestationStillWorksAfterSegmentationChange(unittest.TestCase):
    """End-to-end confirmation: after the authored splitter change, Pass 2's
    infer_presence_enhanced() must still find 'participants:' inside the
    real, newly-produced scene packet, and classify Vaelith/Pelagor exactly
    as before (fc3e3d1's regression cases)."""

    def test_chapter1_participants_line_reaches_pass2_and_classifies_correctly(self):
        world_rules_loader.load_rules()
        manifest = passA_chapter_intake.intake(
            VAULT_BOOK1_DIR / "001_the_ethereal_vigil.md", None
        )
        proposal = passB_scene_boundary_provider.choose_boundaries(manifest, target_words=900)
        self.assertEqual(proposal["scene_count"], 1)

        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            index = passC_scene_packet_writer.write_packets(proposal, tmp_path)
            packet_path = Path(index["packets"][0]["packet_path"])

            pass1_out = tmp_path / "out_pass1_ch1.txt"
            pass1_explicit.process_file(packet_path, pass1_out)

            segments = pass2_enhanced.load_segments(str(pass1_out))
            characters = pass2_entity_filter.filter_entities(
                pass2_enhanced.extract_characters(segments)
            )
            pass2_enhanced.infer_presence_enhanced(segments, characters)
            pass2_enhanced.infer_physicality_enhanced(segments, characters)

        self.assertIn("Vaelith", characters)
        self.assertEqual(characters["Vaelith"].presence, "local")
        self.assertEqual(characters["Vaelith"].physicality, "nonphysical")
        self.assertIn("Pelagor", characters)
        self.assertEqual(characters["Pelagor"].presence, "remote")
        self.assertEqual(characters["Pelagor"].physicality, "unknown")


if __name__ == "__main__":
    unittest.main()
