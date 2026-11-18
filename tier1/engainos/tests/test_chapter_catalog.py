"""V03 chapter catalog: live, read-only rescan of book folders with identity, hashes and anomaly flags."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tier1.engainos.tools.chapter_discovery import build_chapter_catalog, discover_chapters


def _entries(cat):
    return {e["catalog_id"]: e for b in cat["books"] for e in b["chapters"]}


def _snapshot(root: Path):
    return {str(p.relative_to(root)): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
            for p in sorted(root.rglob("*"))}


class ChapterCatalogTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "vault"
        b1 = self.root / "book_01_genesis"
        b2 = self.root / "Book_02_Servitude"   # case-insensitive "book"
        for d in (b1, b2, self.root / "notes", b1 / "nested"):
            d.mkdir(parents=True)
        files = {
            b1 / "001_vigil.md": "one",
            b1 / "2_second.md": "two",             # numeric order: before 010
            b1 / "010_tenth.txt": "ten",
            b1 / "22 and 23.md": "combined",
            b1 / "after 58 to 140 split.txt": "notes",
            b1 / "058_paradocs_engine.md": "a",
            b1 / "058_paradox_engine.md": "b",
            b1 / "readme.json": "{}",               # not .md/.txt
            b1 / "nested" / "005_hidden.md": "x",   # subfolder: not scanned
            b2 / "005_garden.md": "garden",
            self.root / "notes" / "001_not_a_chapter.md": "n",
            self.root / "book_loose.md": "file named book, not a folder",
        }
        for p, text in files.items():
            p.write_text(text, encoding="utf-8")
        (self.root / ".engain").mkdir()
        self.stale = self.root / ".engain" / "chapter_index.json"
        self.stale.write_text("{ not json — stale index must be ignored", encoding="utf-8")
        (self.root / "vault.manifest.json").write_text(json.dumps({"source_files": [
            "book_01_genesis/001_vigil.md", "book_01_genesis/gone.md", "book_01_genesis/nested/005_hidden.md",
        ]}), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_discovery_scope(self):
        cat = build_chapter_catalog(self.root)
        self.assertEqual([b["book_id"] for b in cat["books"]], ["book_01_genesis", "Book_02_Servitude"])
        ids = set(_entries(cat))
        self.assertEqual(cat["chapter_count"], 8)
        self.assertIn("Book_02_Servitude/005_garden.md", ids)
        self.assertFalse(any("nested" in i or "notes" in i or i.endswith(".json") for i in ids))

    def test_catalog_ids_unique_and_legacy_fields_preserved(self):
        cat = build_chapter_catalog(self.root)
        flat = [e for b in cat["books"] for e in b["chapters"]]
        self.assertEqual(len({e["catalog_id"] for e in flat}), len(flat))
        e = _entries(cat)["book_01_genesis/22 and 23.md"]
        self.assertEqual((e["chapter_id"], e["file_name"], e["extension"]), ("22 and 23", "22 and 23.md", ".md"))
        legacy = {c["path"]: c for b in discover_chapters(self.root)["books"] for c in b["chapters"]}
        for entry in flat:
            for k, v in legacy[entry["path"]].items():
                self.assertEqual(entry[k], v, k)

    def test_hash_is_of_source_bytes(self):
        e = _entries(build_chapter_catalog(self.root))["book_01_genesis/001_vigil.md"]
        self.assertEqual(e["source_sha256"], hashlib.sha256(b"one").hexdigest())

    def test_anomalies_flagged_not_excluded(self):
        ent = _entries(build_chapter_catalog(self.root))
        self.assertEqual(ent["book_01_genesis/after 58 to 140 split.txt"]["anomalies"], ["unusual_filename"])
        self.assertIsNone(ent["book_01_genesis/after 58 to 140 split.txt"]["leading_number"])
        self.assertEqual(ent["book_01_genesis/22 and 23.md"]["anomalies"], ["ambiguous_chapter_number"])
        for name in ("058_paradocs_engine.md", "058_paradox_engine.md"):
            self.assertEqual(ent[f"book_01_genesis/{name}"]["anomalies"], ["duplicate_chapter_number"])
        self.assertEqual(ent["book_01_genesis/001_vigil.md"]["anomalies"], [])

    def test_duplicates_are_per_book(self):
        ent = _entries(build_chapter_catalog(self.root))
        self.assertEqual(ent["Book_02_Servitude/005_garden.md"]["anomalies"], [])

    def test_numeric_then_unnumbered_order(self):
        cat = build_chapter_catalog(self.root)
        names = [e["file_name"] for e in cat["books"][0]["chapters"]]
        self.assertEqual(names, ["001_vigil.md", "2_second.md", "010_tenth.txt", "22 and 23.md",
                                 "058_paradocs_engine.md", "058_paradox_engine.md", "after 58 to 140 split.txt"])

    def test_chapter_id_collision_reported(self):
        (self.root / "book_01_genesis" / "001_vigil.txt").write_text("same stem", encoding="utf-8")
        cat = build_chapter_catalog(self.root)
        self.assertEqual(cat["chapter_id_collisions"]["001_vigil"],
                         ["book_01_genesis/001_vigil.md", "book_01_genesis/001_vigil.txt"])

    def test_manifest_discrepancies(self):
        md = build_chapter_catalog(self.root)["manifest_discrepancies"]
        self.assertEqual(md["status"], "ok")
        self.assertEqual(md["listed_but_missing"], ["book_01_genesis/gone.md"])
        self.assertIn("Book_02_Servitude/005_garden.md", md["on_disk_but_unlisted"])
        self.assertNotIn("book_01_genesis/001_vigil.md", md["on_disk_but_unlisted"])
        (self.root / "vault.manifest.json").write_text("{", encoding="utf-8")
        self.assertTrue(build_chapter_catalog(self.root)["manifest_discrepancies"]["status"].startswith("unreadable"))

    def test_refresh_after_add_remove_rename(self):
        b1 = self.root / "book_01_genesis"
        build_chapter_catalog(self.root)
        (b1 / "011_new.md").write_text("new", encoding="utf-8")
        (b1 / "010_tenth.txt").unlink()
        (b1 / "001_vigil.md").rename(b1 / "001_the_vigil.md")
        ids = set(_entries(build_chapter_catalog(self.root)))
        self.assertIn("book_01_genesis/011_new.md", ids)
        self.assertNotIn("book_01_genesis/010_tenth.txt", ids)
        self.assertNotIn("book_01_genesis/001_vigil.md", ids)
        self.assertIn("book_01_genesis/001_the_vigil.md", ids)

    def test_edit_changes_hash_not_identity(self):
        p = self.root / "book_01_genesis" / "001_vigil.md"
        before = _entries(build_chapter_catalog(self.root))["book_01_genesis/001_vigil.md"]["source_sha256"]
        p.write_text("one, revised", encoding="utf-8")
        after = _entries(build_chapter_catalog(self.root))["book_01_genesis/001_vigil.md"]["source_sha256"]
        self.assertNotEqual(before, after)

    def test_read_only_and_ignores_stale_index(self):
        before = _snapshot(self.root)
        build_chapter_catalog(self.root)
        self.assertEqual(_snapshot(self.root), before)

    def test_deterministic(self):
        self.assertEqual(json.dumps(build_chapter_catalog(self.root)), json.dumps(build_chapter_catalog(self.root)))


if __name__ == "__main__":
    unittest.main()
