"""M01a: Tier 1 picks the chapter by catalog_id; December Mettaext runs on a copy; receipt records provenance."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tier1.engainos.tools.run_chapter_extraction import ExtractionError, run_extraction

# Dec-2025 anchor input (outside the repo: manuscript text is not copied into fixtures).
ANCHOR_INPUT = Path("/mnt/data-drive/devvm-projects/mettaext-recovery/historical/EngAIn/mettaext/book/"
                    "act_01ch_08_the_shattered_mind.txt")
ANCHOR_SHA = "8bd05dbfe79f1b2c8dabf1512679f47e326c110bbbb5f577541d62932ba3061f"

CHAPTER = """Lyaris stood at the edge of the garden. "The light is changing," she said.
Mordain looked up at the sky and nodded. The wind moved through the old trees.
"""


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class RunChapterExtractionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.vault = tmp / "vault"
        self.book = self.vault / "book_01_genesis"
        self.book.mkdir(parents=True)
        (self.vault / "vault.manifest.json").write_text("{}", encoding="utf-8")
        self.chapter = self.book / "001_the garden.md"   # space in name on purpose
        self.chapter.write_text(CHAPTER, encoding="utf-8")
        self.manifest = tmp / "engain_manifest.json"
        self.manifest.write_text(json.dumps({
            "active": {"vault": "v"},
            "vaults": {"v": {"root": str(self.vault), "manifest": str(self.vault / "vault.manifest.json")}},
        }), encoding="utf-8")
        self.stageroom = tmp / "stageroom"

    def tearDown(self):
        self._tmp.cleanup()

    def _snapshot(self):
        return {str(p): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
                for p in sorted(self.vault.rglob("*"))}

    def test_unknown_catalog_id_refused_and_nothing_written(self):
        with self.assertRaises(ExtractionError):
            run_extraction("book_01_genesis/../../etc/passwd", self.manifest, self.stageroom)
        self.assertFalse(self.stageroom.exists())

    def test_unresolved_vault_refused(self):
        self.manifest.write_text(json.dumps({"active": {"vault": "missing"}}), encoding="utf-8")
        with self.assertRaises(ExtractionError):
            run_extraction("book_01_genesis/001_the garden.md", self.manifest, self.stageroom)

    def test_run_writes_candidate_with_provenance_and_leaves_vault_untouched(self):
        before = self._snapshot()
        r = run_extraction("book_01_genesis/001_the garden.md", self.manifest, self.stageroom)
        self.assertEqual(self._snapshot(), before)
        self.assertEqual((r["status"], r["acceptance"], r["returncode"]), ("candidate", "not accepted", 0))
        self.assertEqual(r["source_sha256"], _sha(self.chapter))
        out = (self.stageroom / "output/narrative_to_game/catalog/book_01_genesis/001_the garden.md"
               / r["source_sha256"][:12])
        self.assertEqual((out / "source" / "001_the garden.md").read_bytes(), self.chapter.read_bytes())
        self.assertTrue(r["game_scenes"])
        for o in r["outputs"]:
            self.assertEqual(_sha(out / o["path"]), o["sha256"], o["path"])
        self.assertEqual(json.loads((out / "receipt.json").read_text(encoding="utf-8")), r)

    def test_finished_run_is_not_repeated_and_edit_gets_new_dir(self):
        cid = "book_01_genesis/001_the garden.md"
        first = run_extraction(cid, self.manifest, self.stageroom)
        self.assertEqual(run_extraction(cid, self.manifest, self.stageroom)["finished_at"], first["finished_at"])
        self.chapter.write_text(CHAPTER + "The garden fell silent.\n", encoding="utf-8")
        second = run_extraction(cid, self.manifest, self.stageroom)
        self.assertNotEqual(second["source_sha256"], first["source_sha256"])

    def test_unfinished_run_is_not_overwritten(self):
        cid = "book_01_genesis/001_the garden.md"
        r = run_extraction(cid, self.manifest, self.stageroom)
        receipt = next(self.stageroom.rglob("receipt.json"))
        receipt.unlink()
        with self.assertRaises(ExtractionError):
            run_extraction(cid, self.manifest, self.stageroom)
        self.assertTrue(r)

    @unittest.skipUnless(ANCHOR_INPUT.is_file(), "Dec-2025 anchor input not available")
    def test_december_anchor_reproduces_through_catalog(self):
        shutil.copyfile(ANCHOR_INPUT, self.book / ANCHOR_INPUT.name)
        r = run_extraction(f"book_01_genesis/{ANCHOR_INPUT.name}", self.manifest, self.stageroom)
        scene = next(o for o in r["outputs"] if o["path"] == "game_scenes/act_01ch_08_the_shattered_mind.json")
        self.assertEqual(scene["sha256"], ANCHOR_SHA)


if __name__ == "__main__":
    unittest.main()
