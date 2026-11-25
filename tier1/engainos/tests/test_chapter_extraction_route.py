"""H02: 8765 POST/GET /chapters/extract runs the existing run_chapter_extraction for one catalog_id."""

import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from tier1.engainos.bridgeroom import scene_server
from tier1.engainos.bridgeroom.chapter_extraction_route import ChapterExtractionJobs
from tier1.engainos.tools import run_chapter_extraction as rce

CHAPTER = """Lyaris stood at the edge of the garden. "The light is changing," she said.
Mordain looked up at the sky and nodded. The wind moved through the old trees.
"""
CID = "book_01_genesis/001_the garden.md"


class ChapterExtractionRoute(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.vault = tmp / "vault"
        (self.vault / "book_01_genesis").mkdir(parents=True)
        (self.vault / "vault.manifest.json").write_text("{}", encoding="utf-8")
        (self.vault / "book_01_genesis" / "001_the garden.md").write_text(CHAPTER, encoding="utf-8")
        self.manifest = tmp / "engain_manifest.json"
        self.manifest.write_text(json.dumps({"active": {"vault": "v"}, "vaults": {"v": {
            "root": str(self.vault), "manifest": str(self.vault / "vault.manifest.json")}}}), encoding="utf-8")
        self.stageroom = tmp / "stageroom"
        H = scene_server.SceneRequestHandler
        self._saved = (H.vault_manifest_path, H.stageroom_path, H.extraction_jobs)
        H.vault_manifest_path, H.stageroom_path = self.manifest, self.stageroom
        H.extraction_jobs = ChapterExtractionJobs()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        H = scene_server.SceneRequestHandler
        H.vault_manifest_path, H.stageroom_path, H.extraction_jobs = self._saved
        self._tmp.cleanup()

    def _req(self, path, body=None, content_type="application/json"):
        data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        req = urllib.request.Request(self.base + path, data=data, method="POST" if data is not None else "GET",
                                     headers={"Content-Type": content_type})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def _wait(self, cid=CID):
        for _ in range(600):
            code, job = self._req("/chapters/extract?catalog_id=" + urllib.request.quote(cid))
            if job.get("state") != "running":
                return job
            time.sleep(0.1)
        self.fail("extraction did not finish")

    def _vault_state(self):
        return {str(p): (p.stat().st_mtime_ns, p.read_bytes()) for p in sorted(self.vault.rglob("*")) if p.is_file()}

    def test_extracts_through_existing_operation_and_preview_becomes_candidate(self):
        before = self._vault_state()
        self.assertEqual(self._req("/chapters/extraction?catalog_id=" + urllib.request.quote(CID))[1]["extraction"],
                         "not_extracted")
        code, started = self._req("/chapters/extract", {"catalog_id": CID})
        self.assertEqual((code, started["state"]), (202, "running"))
        job = self._wait()
        self.assertEqual(job["state"], "finished", job)
        receipt = job["receipt"]
        self.assertEqual((receipt["contract"], receipt["status"], receipt["acceptance"]),
                         (rce.RECEIPT_CONTRACT, "candidate", "not accepted"))
        self.assertEqual(receipt["catalog_id"], CID)
        code, preview = self._req("/chapters/extraction?catalog_id=" + urllib.request.quote(CID))
        self.assertEqual((code, preview["extraction"]), (200, "candidate"))
        self.assertEqual(preview["receipt"], receipt)
        self.assertEqual(self._vault_state(), before)  # manuscript untouched

    def test_unknown_or_path_ids_refused_before_anything_runs(self):
        for cid in ("book_01_genesis/../../etc/passwd", "/etc/passwd", "nope/none.md"):
            code, body = self._req("/chapters/extract", {"catalog_id": cid})
            self.assertEqual((code, body["state"]), (404, "refused"), cid)
        self.assertFalse(self.stageroom.exists())

    def test_malformed_requests_refused(self):
        self.assertEqual(self._req("/chapters/extract", {"catalog_id": CID, "path": "/x"})[0], 400)
        self.assertEqual(self._req("/chapters/extract", {"catalog_id": 5})[0], 400)
        self.assertEqual(self._req("/chapters/extract", b"catalog_id=x", "application/x-www-form-urlencoded")[0], 415)
        self.assertEqual(self._req("/chapters/extract", b"not json")[0], 400)
        self.assertFalse(self.stageroom.exists())

    def test_duplicate_request_while_running_is_refused(self):
        gate, calls = threading.Event(), []

        def slow(*args):
            calls.append(args)
            gate.wait(10)
            return {"status": "candidate"}

        scene_server.SceneRequestHandler.extraction_jobs = ChapterExtractionJobs(runner=slow)
        self.assertEqual(self._req("/chapters/extract", {"catalog_id": CID})[0], 202)
        code, body = self._req("/chapters/extract", {"catalog_id": CID})
        self.assertEqual((code, body["state"], body["running_catalog_id"]), (409, "busy", CID))
        self.assertEqual(self._req("/chapters/extract?catalog_id=" + urllib.request.quote(CID))[1]["state"], "running")
        gate.set()
        self.assertEqual(self._wait()["state"], "finished")
        self.assertEqual(len(calls), 1)

    def test_runner_error_is_reported_not_left_running(self):
        def broken(*args):
            raise rce.ExtractionError("unfinished earlier run left /x; inspect it and remove it to retry")
        scene_server.SceneRequestHandler.extraction_jobs = ChapterExtractionJobs(runner=broken)
        self.assertEqual(self._req("/chapters/extract", {"catalog_id": CID})[0], 202)
        job = self._wait()
        self.assertEqual(job["state"], "error")
        self.assertIn("unfinished earlier run", job["message"])
        self.assertIsNone(job["running_catalog_id"])


if __name__ == "__main__":
    unittest.main()
