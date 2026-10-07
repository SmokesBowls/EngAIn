"""
test_authored_scene_markers_fenced_yaml.py -- Regression tests for the
2026-10-06 Chapterroom compatibility update to Pass B: current manuscripts
(Book 09) write authored scene markers as markdown headings
("### scene 048.5 — title") and put scene metadata in fenced ```yaml blocks,
in two layouts (a nested 'scene meta:' mapping, or top-level keys). Before
this update Pass B did not recognise that format and fell back to
mechanical_word_chunk for every Book 09 chapter.

The 09-19 rules are unchanged and still pinned by
test_authored_scene_boundary_splitter.py; these tests only cover the new
format and the additive source_scene_label field. Nothing here writes into
the vault: real-chapter checks use in-memory functions only.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext.chapterroom import passB_scene_boundary_provider as passB
from tier3.mettaext.chapterroom import passC_scene_packet_writer as passC

BOOK09_DIR = Path("/mnt/data-drive/obsidianburdenNov25not vault/book_09_bureaucratic_debt")

NESTED_LAYOUT = (
    "book 9\n"
    "### scene 048.5 — Three days later / Zephyr at Mika's grave\n"
    "```yaml\n"
    "scene meta:\n"
    "  location: Mika's grave / Falcon Ridge / departure path\n"
    "  time: Y17,511 M6 D22, daytime–sunset\n"
    "  participants: Geralt; Zephyr; Mika Covenant (grave and memory only)\n"
    "  terminal state: >-\n"
    "    The peace era has ended;\n"
    "    Karvex is defeated.\n"
    "```\n"
    "\n"
    "Three days later, at Mika’s grave, Zephyr appeared.\n"
)

TOP_LEVEL_LAYOUT = (
    "### scene 050.4 — Umbra arrival\n"
    "```yaml\n"
    "scene: \"050.4\"\n"
    "title: Umbra arrival\n"
    "date_like: 2026-09-19\n"
    "state ledger:\n"
    "  Geralt: Approximately 80% remains.\n"
    "  Vek'tar: Recruited and temporally unstable.\n"
    "```\n"
    "They didn't so much land as congeal into existence.\n"
)


class TestHeadingPrefixedMarkers(unittest.TestCase):
    def test_heading_marker_recognised_with_label_and_title(self):
        chunks = passB.authored_scene_chunks(NESTED_LAYOUT.splitlines())
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].source_scene_label, "048.5")
        self.assertEqual(chunks[0].source_scene_title, "Three days later / Zephyr at Mika's grave")
        self.assertEqual(chunks[0].start_line, 2)

    def test_bare_marker_still_recognised(self):
        text = "scene 003.1 — first night on the beach\n\nscene meta:\nparticipants: Senareth\n\nProse.\n"
        chunks = passB.authored_scene_chunks(text.splitlines())
        self.assertEqual(chunks[0].source_scene_label, "003.1")
        self.assertEqual(chunks[0].scene_meta_format, "plain")
        self.assertEqual(chunks[0].scene_meta, {"participants": "Senareth"})

    def test_other_headings_are_not_markers(self):
        text = "### Chapter notes — draft\n## scene list\n### scene notes — none\nProse.\n"
        self.assertEqual(passB.authored_scene_chunks(text.splitlines()), [])

    def test_legacy_tuple_api_unchanged(self):
        tuples = passB.split_by_authored_scene_markers(NESTED_LAYOUT.splitlines())
        self.assertEqual(len(tuples), 1)
        start, end, text, meta = tuples[0]
        self.assertEqual((start, end), (2, len(NESTED_LAYOUT.splitlines())))
        self.assertIn("participants", meta)


class TestFencedYamlMetadata(unittest.TestCase):
    def test_nested_scene_meta_layout_is_unwrapped(self):
        chunk = passB.authored_scene_chunks(NESTED_LAYOUT.splitlines())[0]
        self.assertEqual(chunk.scene_meta_format, "fenced_yaml")
        self.assertIsNone(chunk.scene_meta_error)
        self.assertEqual(
            list(chunk.scene_meta),
            ["location", "time", "participants", "terminal state"],
        )
        self.assertEqual(chunk.scene_meta["participants"],
                         "Geralt; Zephyr; Mika Covenant (grave and memory only)")

    def test_values_are_opaque_strings_as_written(self):
        nested = passB.authored_scene_chunks(NESTED_LAYOUT.splitlines())[0].scene_meta
        self.assertEqual(nested["time"], "Y17,511 M6 D22, daytime–sunset")
        top = passB.authored_scene_chunks(TOP_LEVEL_LAYOUT.splitlines())[0].scene_meta
        # No type coercion: a date-like value stays the string that was written.
        self.assertEqual(top["date_like"], "2026-09-19")
        self.assertIsInstance(top["date_like"], str)
        self.assertEqual(top["scene"], "050.4")

    def test_block_scalar_folded_to_one_header_line(self):
        meta = passB.authored_scene_chunks(NESTED_LAYOUT.splitlines())[0].scene_meta
        self.assertEqual(meta["terminal state"], "The peace era has ended; Karvex is defeated.")
        self.assertNotIn("\n", meta["terminal state"])

    def test_top_level_layout_nested_mapping_becomes_dotted_keys(self):
        meta = passB.authored_scene_chunks(TOP_LEVEL_LAYOUT.splitlines())[0].scene_meta
        self.assertEqual(meta["state ledger.Geralt"], "Approximately 80% remains.")
        self.assertEqual(meta["state ledger.Vek'tar"], "Recruited and temporally unstable.")
        self.assertNotIn("state ledger", meta)

    def test_raw_yaml_lines_stay_in_scene_text(self):
        """Pass 2 scans segment text for 'participants:' directly."""
        chunk = passB.authored_scene_chunks(NESTED_LAYOUT.splitlines())[0]
        self.assertIn("  participants: Geralt; Zephyr;", chunk.text)
        self.assertIn("```yaml", chunk.text)

    def test_unterminated_fence_keeps_boundary_and_reports_error(self):
        text = "### scene 001.1 — open fence\n```yaml\nlocation: Beach\nProse with no close.\n"
        chunk = passB.authored_scene_chunks(text.splitlines())[0]
        self.assertEqual(chunk.scene_meta, {})
        self.assertEqual(chunk.scene_meta_error, "unterminated yaml fence")
        self.assertEqual(chunk.source_scene_label, "001.1")

    def test_fence_closing_in_next_scene_is_not_borrowed(self):
        text = (
            "### scene 001.1 — a\n```yaml\nlocation: A\n"
            "### scene 001.2 — b\n```yaml\nlocation: B\n```\nProse.\n"
        )
        chunks = passB.authored_scene_chunks(text.splitlines())
        self.assertEqual(chunks[0].scene_meta_error, "unterminated yaml fence")
        self.assertEqual(chunks[1].scene_meta, {"location": "B"})

    def test_invalid_yaml_reports_error(self):
        text = "### scene 001.1 — bad\n```yaml\nlocation: [unclosed\n```\nProse.\n"
        chunk = passB.authored_scene_chunks(text.splitlines())[0]
        self.assertEqual(chunk.scene_meta, {})
        self.assertTrue(chunk.scene_meta_error.startswith("yaml parse error"))

    def test_non_mapping_yaml_reports_error(self):
        text = "### scene 001.1 — list\n```yaml\n- a\n- b\n```\nProse.\n"
        chunk = passB.authored_scene_chunks(text.splitlines())[0]
        self.assertEqual(chunk.scene_meta_error, "yaml metadata is a list, not a mapping")


class TestChooseBoundariesCarriesLabel(unittest.TestCase):
    def _proposal(self, raw_text: str) -> dict:
        manifest = {"contract": "engain.chapter_intake_manifest.v1",
                    "chapter_id": "chapter.book009.048_the_ledger_born", "raw_text": raw_text}
        return passB.choose_boundaries(manifest, target_words=900)

    def test_label_is_carried_and_independent_of_index(self):
        raw = ("### scene 048.4 — four\n```yaml\nlocation: X\n```\nP4.\n"
               "### scene 048.5 — five\n```yaml\nlocation: Y\n```\nP5.\n")
        proposal = self._proposal(raw)
        self.assertEqual(proposal["boundary_method"], "authored_scene_marker")
        first, second = proposal["scenes"]
        # scene_index stays sequential; the label is what the author wrote.
        self.assertEqual((first["scene_index"], first["source_scene_label"]), (1, "048.4"))
        self.assertEqual(first["scene_id"], "scene.book009.048_the_ledger_born.scene001")
        self.assertEqual((second["scene_index"], second["source_scene_label"]), (2, "048.5"))
        self.assertEqual(second["scene_meta"], {"location": "Y"})
        self.assertEqual(second["scene_meta_format"], "fenced_yaml")

    def test_mechanical_fallback_has_no_label(self):
        proposal = self._proposal("No markers.\n\n\nStill none.\n")
        for scene in proposal["scenes"]:
            self.assertNotIn("source_scene_label", scene)

    def test_pass_c_index_carries_label(self):
        proposal = self._proposal(NESTED_LAYOUT)
        with tempfile.TemporaryDirectory() as tmp:
            index = passC.write_packets(proposal, Path(tmp))
            entry = index["packets"][0]
            self.assertEqual(entry["source_scene_label"], "048.5")
            self.assertEqual(entry["scene_meta_format"], "fenced_yaml")
            on_disk = json.loads(Path(index["index_path"]).read_text(encoding="utf-8"))
            self.assertEqual(on_disk["packets"][0]["source_scene_label"], "048.5")
            packet = Path(entry["packet_path"]).read_text(encoding="utf-8")
            self.assertIn("@scene_meta_participants: Geralt; Zephyr;", packet)


@unittest.skipUnless(BOOK09_DIR.is_dir(), "Book 09 vault not present")
class TestBook09RealChapters(unittest.TestCase):
    """Read-only: raw text is read and split in memory; nothing is written."""

    def _proposal(self, filename: str, chapter_id: str) -> dict:
        raw = (BOOK09_DIR / filename).read_text(encoding="utf-8")
        return passB.choose_boundaries(
            {"contract": "engain.chapter_intake_manifest.v1", "chapter_id": chapter_id, "raw_text": raw},
            target_words=1200,
        )

    def test_chapter_048_authored_scenes(self):
        proposal = self._proposal("048_the_ledger_born.md", "chapter.book009.048_the_ledger_born")
        self.assertEqual(proposal["boundary_method"], "authored_scene_marker")
        self.assertEqual([s["source_scene_label"] for s in proposal["scenes"]],
                         ["048.1", "048.2", "048.3", "048.4", "048.5"])
        last = proposal["scenes"][-1]
        self.assertEqual(last["boundary_start_line"], 467)
        self.assertIn("Mika Covenant (grave and memory only)", last["scene_meta"]["participants"])
        self.assertTrue(all("scene_meta_error" not in s for s in proposal["scenes"]))

    def test_chapter_050_top_level_layout(self):
        proposal = self._proposal("050_the_scout.md", "chapter.book009.050_the_scout")
        self.assertEqual(proposal["boundary_method"], "authored_scene_marker")
        labels = [s["source_scene_label"] for s in proposal["scenes"]]
        self.assertEqual(labels[:4], ["050.1", "050.2", "050.3", "050.4"])
        arrival = proposal["scenes"][3]
        self.assertEqual(arrival["boundary_start_line"], 289)
        self.assertEqual(arrival["scene_meta"]["scene"], "050.4")
        self.assertIn("state ledger.Geralt", arrival["scene_meta"])
        self.assertTrue(all("scene_meta_error" not in s for s in proposal["scenes"]))


if __name__ == "__main__":
    unittest.main()
