"""T03-R2: catalog extractions are delivered by the existing Stageroom resolver.

A real December Mettaext run (run_chapter_extraction) on a throwaway vault, then
StageroomSceneResolver.load_catalog_scene and 8765 /load_scene?catalog_id=. Each
failure case breaks exactly one link of catalog -> receipt -> Pass 4 -> Pass 5.
The last case reads the two real production extractions (read-only).
"""

import hashlib
import json
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer, ThreadingHTTPServer
from pathlib import Path

from tier1.engainos.bridgeroom.scene_server import SceneRequestHandler
from tier1.engainos.bridgeroom.stageroom_scene_resolver import StageroomSceneResolver
from tier1.engainos.tools.run_chapter_extraction import run_extraction

CID = "book_01_genesis/001_the garden.md"
OTHER = "book_01_genesis/002_the gate.md"
CHAPTER = """Lyaris stood at the edge of the garden. "The light is changing," she said.
Mordain looked up at the sky and nodded. The wind moved through the old trees.
"""
REAL = ("book_01_book_of_genesis/003_first_contact.md", "book_16_fragmented_beginning/086_sanctuary_to_storm.md")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class CatalogSceneDeliveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmpl = tempfile.TemporaryDirectory()
        cls.template = Path(cls._tmpl.name)
        book = cls.template / "vault" / "book_01_genesis"
        book.mkdir(parents=True)
        (cls.template / "vault" / "vault.manifest.json").write_text("{}", encoding="utf-8")
        (book / "001_the garden.md").write_text(CHAPTER, encoding="utf-8")
        (book / "002_the gate.md").write_text(CHAPTER + "The gate stayed shut.\n", encoding="utf-8")
        cls._manifest(cls.template)
        cls.receipt = run_extraction(CID, cls.template / "engain_manifest.json", cls.template / "stageroom")
        assert cls.receipt["status"] == "candidate", cls.receipt

    @classmethod
    def tearDownClass(cls):
        cls._tmpl.cleanup()

    @staticmethod
    def _manifest(root: Path):
        (root / "engain_manifest.json").write_text(json.dumps({
            "active": {"vault": "v"},
            "vaults": {"v": {"root": str(root / "vault"), "manifest": str(root / "vault" / "vault.manifest.json")}},
        }), encoding="utf-8")

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "w"
        shutil.copytree(self.template, self.root)
        self._manifest(self.root)
        self.manifest = self.root / "engain_manifest.json"
        self.resolver = StageroomSceneResolver(self.root / "stageroom")
        self.out = (self.root / "stageroom/output/narrative_to_game/catalog/book_01_genesis/001_the garden.md"
                    / self.receipt["source_sha256"][:12])
        self.pass4 = next(o["path"] for o in self.receipt["outputs"]
                          if o["path"].startswith("pipeline_work/") and o["path"].endswith(".zonj.json"))

    def tearDown(self):
        self._tmp.cleanup()

    def _deliver(self, cid=CID):
        return self.resolver.load_catalog_scene(cid, self.manifest)

    def _edit_json(self, rel, change, rehash=True):
        """Change one artifact; with rehash, also update its receipt hash (so only the change itself is wrong)."""
        path = self.out / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data), encoding="utf-8")
        if rehash:
            receipt_path = self.out / "receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            for o in receipt["outputs"]:
                if o["path"] == rel:
                    o["sha256"] = _sha(path)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    # -- delivery ---------------------------------------------------------

    def test_delivers_pass5_with_its_own_pass4_segments_and_provenance(self):
        packet = self._deliver()
        pass5 = json.loads((self.out / self.receipt["game_scenes"][0]).read_text(encoding="utf-8"))
        pass4 = json.loads((self.out / self.pass4).read_text(encoding="utf-8"))
        self.assertEqual(packet["scene_id"], self.receipt["chapter_id"])
        self.assertEqual(pass4["@id"], "scene." + self.receipt["chapter_id"])
        self.assertTrue(pass4["=segments"])
        self.assertEqual(packet["=segments"], pass4["=segments"])
        for key, value in pass5.items():  # Pass 5 is delivered as written; nothing overwritten
            self.assertEqual(packet[key], value, key)
        self.assertEqual(packet["catalog_extraction"], {
            "source": "tier1_chapter_extraction_receipt", "catalog_id": CID,
            "chapter_id": self.receipt["chapter_id"], "source_sha256": self.receipt["source_sha256"],
            "receipt_status": "candidate", "acceptance": "not accepted",
            "pass4_sha256": _sha(self.out / self.pass4),
            "pass5_sha256": _sha(self.out / self.receipt["game_scenes"][0])})

    # -- fail closed --------------------------------------------------------

    def test_unknown_and_unextracted_chapters_are_refused(self):
        for cid in ("book_01_genesis/../../etc/passwd", "book_01_genesis/009_missing.md", OTHER):
            with self.assertRaises(FileNotFoundError, msg=cid):
                self._deliver(cid)

    def test_stale_extraction_is_refused(self):
        (self.root / "vault/book_01_genesis/001_the garden.md").write_text(CHAPTER + "Later.\n", encoding="utf-8")
        with self.assertRaisesRegex(FileNotFoundError, "stale"):
            self._deliver()

    def test_failed_run_is_refused(self):
        self._edit_json("receipt.json", lambda r: r.update(status="failed", returncode=1), rehash=False)
        with self.assertRaisesRegex(ValueError, "did not finish"):
            self._deliver()

    def test_tampered_pass4_is_refused(self):
        self._edit_json(self.pass4, lambda d: d["=segments"].pop(), rehash=False)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self._deliver()

    def test_missing_segments_are_refused_not_manufactured(self):
        self._edit_json(self.pass4, lambda d: d.pop("=segments"))
        with self.assertRaisesRegex(ValueError, "=segments"):
            self._deliver()

    def test_pass4_of_another_scene_is_refused(self):
        self._edit_json(self.pass4, lambda d: d.update({"@id": "scene.999_other"}))
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self._deliver()

    def test_pass5_of_another_scene_is_refused(self):
        self._edit_json(self.receipt["game_scenes"][0], lambda d: d.update(scene_id="999_other"))
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self._deliver()

    def test_ambiguous_pass4_is_refused(self):
        extra = self.out / "pipeline_work/other.zonj.json"
        shutil.copyfile(self.out / self.pass4, extra)
        receipt_path = self.out / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["outputs"].append({"path": "pipeline_work/other.zonj.json", "sha256": _sha(extra)})
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            self._deliver()

    def test_unresolved_vault_is_refused(self):
        self.manifest.write_text(json.dumps({"active": {"vault": "missing"}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self._deliver()

    # -- consumers ----------------------------------------------------------

    def test_delivered_scene_satisfies_the_godotsim_scene_load_contract(self):
        from tier2.godotsim import sim_runtime
        from tier2.godotsim.http_handlers import RuntimeHTTPHandler
        from tier2.godotsim.runtime_core import EngAInRuntime

        runtime = EngAInRuntime()  # isolated; env_manager unset, so no Blender
        saved = getattr(RuntimeHTTPHandler, "runtime", None)
        RuntimeHTTPHandler.runtime = runtime
        sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, runtime)
        server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeHTTPHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            packet = self._deliver()
            body = json.dumps({"scene": packet, "reality_mode": "DRAFT", "actor_authority_tier": 2,
                               "actor_id": "t03r2-test", "source_system": "t03r2-test"}).encode()
            req = urllib.request.Request(base + "/scene/load", data=body, method="POST",
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                loaded = json.loads(resp.read())
            self.assertEqual(loaded["status"], "loaded")
            with urllib.request.urlopen(base + "/snapshot/peek", timeout=30) as resp:
                payload = json.loads(resp.read()).get("payload")
            self.assertEqual(payload["scene_activation"]["scene_id"], loaded["scene_id"])
            self.assertEqual(len(runtime.snapshot["scene"]["segments"]), len(packet["=segments"]))
        finally:
            server.shutdown()
            server.server_close()
            RuntimeHTTPHandler.runtime = saved

    def test_8765_load_scene_by_catalog_id(self):
        saved = (SceneRequestHandler.vault_manifest_path, SceneRequestHandler.stageroom_path)
        SceneRequestHandler.vault_manifest_path = self.manifest
        SceneRequestHandler.stageroom_path = self.root / "stageroom"
        server = HTTPServer(("127.0.0.1", 0), SceneRequestHandler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_address[1]}"

        def get(query):
            try:
                with urllib.request.urlopen(base + "/load_scene?" + query, timeout=30) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                with e:
                    return e.code, json.loads(e.read())

        try:
            quoted = urllib.request.quote(CID, safe="")
            status, body = get("catalog_id=" + quoted)
            self.assertEqual(status, 200, body)
            self.assertEqual(body["scene_ref"]["catalog_id"], CID)
            self.assertEqual(body["data"]["=segments"], self._deliver()["=segments"])
            self.assertEqual(get(f"catalog_id={quoted}&scene_id=scene.x")[0], 400)
            self.assertEqual(get("catalog_id=" + urllib.request.quote(OTHER, safe=""))[0], 404)
            self._edit_json(self.pass4, lambda d: d.pop("=segments"))
            self.assertEqual(get("catalog_id=" + quoted)[0], 409)
        finally:
            server.shutdown()
            server.server_close()
            SceneRequestHandler.vault_manifest_path, SceneRequestHandler.stageroom_path = saved


class RealCatalogExtractionsTest(unittest.TestCase):
    """The two production extractions, through the production vault and Stageroom (read-only)."""

    def test_real_extractions_deliver_their_own_segments(self):
        resolver = StageroomSceneResolver(None)
        try:
            packets = {cid: resolver.load_catalog_scene(cid) for cid in REAL}
        except (FileNotFoundError, ValueError) as exc:
            self.skipTest(f"production catalog extractions not available: {exc}")
        for cid, packet in packets.items():
            ce = packet["catalog_extraction"]
            out = (resolver.root / "output/narrative_to_game/catalog" / cid / ce["source_sha256"][:12])
            pass4 = json.loads(next((out / "pipeline_work").glob("*.zonj.json")).read_text(encoding="utf-8"))
            self.assertEqual(packet["=segments"], pass4["=segments"], cid)
            self.assertEqual((ce["receipt_status"], ce["acceptance"]), ("candidate", "not accepted"))
        self.assertTrue(resolver.list_available_scenes())  # Chapterroom route still answers


if __name__ == "__main__":
    unittest.main()
