"""8765 vault routes, exercised over real HTTP against a temporary engain_manifest.json and vault."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path

from tier1.engainos.bridgeroom.scene_server import SceneRequestHandler
from tier1.engainos.tools.run_chapter_extraction import run_extraction


class SceneServerVaultRoutesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.vault = tmp / "vaultA"
        (self.vault / "book_01_genesis").mkdir(parents=True)
        (self.vault / "book_01_genesis" / "001_vigil.md").write_text("one", encoding="utf-8")
        (self.vault / "vault.manifest.json").write_text("{}", encoding="utf-8")
        self.manifest = tmp / "engain_manifest.json"
        self._write_manifest("vaultA")

        self._saved_manifest = SceneRequestHandler.vault_manifest_path
        self._saved_stageroom = SceneRequestHandler.stageroom_path
        SceneRequestHandler.vault_manifest_path = self.manifest
        self.stageroom = tmp / "stageroom"
        SceneRequestHandler.stageroom_path = self.stageroom
        self.server = HTTPServer(("127.0.0.1", 0), SceneRequestHandler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        SceneRequestHandler.vault_manifest_path = self._saved_manifest
        SceneRequestHandler.stageroom_path = self._saved_stageroom
        self._tmp.cleanup()

    def _write_manifest(self, active_id):
        self.manifest.write_text(json.dumps({
            "active": {"vault": active_id},
            "vaults": {"vaultA": {"root": str(self.vault),
                                  "manifest": str(self.vault / "vault.manifest.json")}},
            "active_vault": str(self.vault),
        }), encoding="utf-8")

    def _get(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read())

    def test_vault_active_reports_authority(self):
        status, body = self._get("/vault/active")
        self.assertEqual(status, 200, body)
        v = body["vault"]
        self.assertEqual((v["status"], v["vault_id"], v["root"]), ("ok", "vaultA", str(self.vault)))
        self.assertEqual(v["source"], str(self.manifest))
        self.assertEqual(v["authority_fields"], {"vault_id": "active.vault", "root": "vaults['vaultA'].root"})

    def test_vault_active_failure_is_explicit(self):
        self._write_manifest("missing_id")
        status, body = self._get("/vault/active")
        self.assertEqual(status, 503)
        self.assertEqual(body["status"], "error")
        self.assertIsNone(body["vault"]["root"])
        self.assertTrue(body["vault"]["problems"])

    def test_vault_active_is_read_only(self):
        before = self.manifest.read_bytes()
        self._get("/vault/active")
        self.assertEqual(self.manifest.read_bytes(), before)

    def _catalog_ids(self):
        status, body = self._get("/chapters/catalog")
        self.assertEqual(status, 200, body)
        return {e["catalog_id"]: e for b in body["catalog"]["books"] for e in b["chapters"]}

    def test_catalog_rescans_every_request(self):
        book = self.vault / "book_01_genesis"
        self.assertEqual(set(self._catalog_ids()), {"book_01_genesis/001_vigil.md"})
        (book / "002_new.md").write_text("two", encoding="utf-8")
        (book / "001_vigil.md").rename(book / "001_the_vigil.md")
        self.assertEqual(set(self._catalog_ids()), {"book_01_genesis/001_the_vigil.md", "book_01_genesis/002_new.md"})
        (book / "002_new.md").unlink()
        self.assertEqual(set(self._catalog_ids()), {"book_01_genesis/001_the_vigil.md"})

    def test_catalog_keeps_unusual_files_with_identity_hash_and_anomalies(self):
        (self.vault / "book_01_genesis" / "after 58 to 140 split.txt").write_text("notes", encoding="utf-8")
        e = self._catalog_ids()["book_01_genesis/after 58 to 140 split.txt"]
        self.assertEqual(e["anomalies"], ["unusual_filename"])
        self.assertEqual(len(e["source_sha256"]), 64)
        _, body = self._get("/chapters/catalog")
        self.assertEqual(body["vault"]["vault_id"], "vaultA")
        self.assertEqual(body["catalog"]["manifest_discrepancies"]["vault_manifest"],
                         str(self.vault / "vault.manifest.json"))

    def test_catalog_is_read_only(self):
        (self.vault / ".engain").mkdir()
        (self.vault / ".engain" / "chapter_index.json").write_text("stale", encoding="utf-8")
        snap = lambda: {str(p): (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
                        for p in sorted(self.vault.rglob("*"))}
        before = snap()
        self._catalog_ids()
        self.assertEqual(snap(), before)

    def test_catalog_failure_is_explicit(self):
        self._write_manifest("missing_id")
        status, body = self._get("/chapters/catalog")
        self.assertEqual(status, 503)
        self.assertNotIn("catalog", body)
        self.assertTrue(body["vault"]["problems"])

    def test_legacy_scene_routes_unchanged(self):
        expected = SceneRequestHandler.loader.list_available_scenes()
        for route in ("/list_scenes", "/list_chapters"):
            status, body = self._get(route)
            self.assertEqual(status, 200)
            self.assertEqual(body, {"status": "success", "chapters": expected, "scenes": expected})

    # --- M01b: /chapters/extraction ---

    CID = "book_01_genesis/001_vigil.md"

    def _extraction(self, cid=CID):
        from urllib.parse import quote
        return self._get("/chapters/extraction?catalog_id=" + quote(cid))

    def test_extraction_requires_known_catalog_id(self):
        self.assertEqual(self._get("/chapters/extraction")[0], 400)
        status, body = self._extraction("book_01_genesis/../../etc/passwd")
        self.assertEqual((status, body["extraction"]), (404, "unknown_catalog_id"))

    def test_extraction_not_extracted_then_current_candidate(self):
        status, body = self._extraction()
        self.assertEqual((status, body["extraction"], body["previous"]), (404, "not_extracted", []))
        run_extraction(self.CID, self.manifest, self.stageroom)
        status, body = self._extraction()
        self.assertEqual(status, 200, body)
        self.assertEqual((body["extraction"], body["acceptance"]), ("candidate", "not accepted"))
        self.assertEqual(list(body["game_scenes"]), body["receipt"]["game_scenes"])

    def test_edited_chapter_reports_stale_and_serves_no_old_output(self):
        first = run_extraction(self.CID, self.manifest, self.stageroom)
        (self.vault / "book_01_genesis" / "001_vigil.md").write_text("one, revised", encoding="utf-8")
        status, body = self._extraction()
        self.assertEqual((status, body["extraction"]), (404, "stale"))
        self.assertNotIn("game_scenes", body)
        self.assertEqual(body["previous"][0]["source_sha256"], first["source_sha256"])

    def test_tampered_output_is_refused(self):
        r = run_extraction(self.CID, self.manifest, self.stageroom)
        scene = next(self.stageroom.rglob(r["game_scenes"][0].split("/")[-1]))
        scene.write_text("{}", encoding="utf-8")
        status, body = self._extraction()
        self.assertEqual((status, body["extraction"]), (500, "receipt_mismatch"))


if __name__ == "__main__":
    unittest.main()
