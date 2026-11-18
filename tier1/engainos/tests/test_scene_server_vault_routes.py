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
        SceneRequestHandler.vault_manifest_path = self.manifest
        self.server = HTTPServer(("127.0.0.1", 0), SceneRequestHandler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        SceneRequestHandler.vault_manifest_path = self._saved_manifest
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


if __name__ == "__main__":
    unittest.main()
