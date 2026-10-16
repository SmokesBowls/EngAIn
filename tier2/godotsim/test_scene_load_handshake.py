"""
test_scene_load_handshake.py -- Regression tests for the 8080 /scene/load
handshake (stageroom scene -> Godot Boot.gd -> SimClient.load_scene_doc ->
POST /scene/load) after Vault Linker retirement, Part A.

Part A removes the linker's scene generation, boot relink and scene
substitution. The vault routes, the vault context read by /world/*, and the
snapshot fallback stay in place until they are reviewed on their own.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import tempfile
import threading
import types
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

SCENE_ID = "scene.900_handshake_test_scene001"
IDENTITY = {
    "reality_mode": "LIVE",
    "actor_authority_tier": 3,
    "issuer": "godot_semantic_runtime",
    "source": "godot_semantic_runtime",
}


def _stageroom_doc():
    """Shape of a passroom game_scenes artifact after Boot.gd adaptation."""
    return {
        "scene_id": SCENE_ID,
        "@id": SCENE_ID,
        "entities": [
            {"id": "geralt", "name": "Geralt", "type": "character",
             "position": {"x": 0.0, "y": 0.0, "z": 0.0}},
            {"id": "mika", "name": "Mika", "type": "character",
             "position": {"x": 5.0, "y": 0.0, "z": 0.0}},
        ],
        "events": [{"type": "dialogue", "actor": "mika", "action": "speak",
                    "data": {"text": "Again?"}}],
        "segments": [{"text": "Again?"}],
        "layout_proof": {"marker": "stageroom"},
        **IDENTITY,
    }


class TestSceneLoadHandshake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = EngAInRuntime()
        RuntimeHTTPHandler.runtime = cls.runtime
        sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, cls.runtime)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeHTTPHandler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.runtime.vault_scenes.clear()

    def _call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")

    def _snapshot_payload(self):
        status, env = self._call("GET", "/snapshot")
        self.assertEqual(status, 200)
        return env.get("payload", env)

    # -- the live handshake ------------------------------------------------

    def test_stageroom_doc_loads_and_owns_snapshot(self):
        log = io.StringIO()
        with contextlib.redirect_stdout(log):
            status, body = self._call("POST", "/scene/load", _stageroom_doc())
        self.assertEqual((status, body.get("status")), (200, "loaded"))
        loaded_id = body["scene_id"]

        payload = self._snapshot_payload()
        self.assertEqual(payload.get("scene_id"), loaded_id)
        self.assertEqual(self.runtime._active_scene_id, loaded_id)
        self.assertEqual(payload["scene"].get("layout_proof"), {"marker": "stageroom"})
        self.assertEqual(len(payload.get("bridge_entities") or []), 2)
        self.assertNotIn("Failed to persist active scene state", log.getvalue())

    def test_registered_vault_scene_does_not_replace_client_doc(self):
        status, body = self._call("POST", "/scene/load", _stageroom_doc())
        self.assertEqual(status, 200)
        self.runtime.vault_scenes[body["scene_id"]] = {
            "@id": body["scene_id"], "=segments": [{"text": "linker paragraph"}]}
        status, _ = self._call("POST", "/scene/load", _stageroom_doc())
        self.assertEqual(status, 200)
        self.assertEqual(self._snapshot_payload()["scene"].get("layout_proof"),
                         {"marker": "stageroom"})

    def test_replay_request_is_blocked(self):
        doc = dict(_stageroom_doc(), reality_mode="REPLAY")
        status, body = self._call("POST", "/scene/load", doc)
        self.assertEqual((status, body.get("error")), (403, "governance_rejected"))

    def test_missing_identity_is_rejected(self):
        doc = {k: v for k, v in _stageroom_doc().items() if k not in IDENTITY}
        status, body = self._call("POST", "/scene/load", doc)
        self.assertEqual((status, body.get("error")), (400, "governance_rejected"))

    def test_doc_without_segments_is_rejected(self):
        status, body = self._call("POST", "/scene/load", {"scene_id": SCENE_ID, **IDENTITY})
        self.assertEqual((status, body.get("error")), (400, "invalid_zonj"))

    # -- snapshot fallback contract (kept in Part A) ----------------------

    def test_snapshot_fallback_reads_vault_scenes_when_doc_missing(self):
        envelope = {"payload": {}}
        stub = types.SimpleNamespace(_active_scene_id="scene.x", _active_scene_doc=None,
                                     vault_scenes={"scene.x": {"@id": "scene.x"}})
        sim_runtime._hydrate_snapshot_scene(envelope, stub)
        self.assertEqual(envelope["payload"]["scene_id"], "scene.x")
        self.assertEqual(envelope["payload"]["scene"], {"@id": "scene.x"})

    # -- linker processing is gone ------------------------------------------

    def test_linker_module_is_gone(self):
        self.assertIsNone(importlib.util.find_spec("tier2.godotsim.vault_linker"))
        self.assertFalse(hasattr(self.runtime, "vault_linker"))
        self.assertIsInstance(self.runtime.vault_scenes, dict)

    # -- vault API and /world/* dependency are kept -------------------------

    def test_vault_routes_answer_and_world_routes_get_vault_context(self):
        with tempfile.TemporaryDirectory() as vault:
            manifest = {"vault_id": "handshake_test",
                        "build": {"output_dir": os.path.join(vault, "build")}}
            with open(os.path.join(vault, "vault.manifest.json"), "w") as f:
                json.dump(manifest, f)
            with open(os.path.join(vault, "note.md"), "w") as f:
                f.write("# Note\n\nGeralt waits.\n")

            status, body = self._call("POST", "/vault/link",
                                      {"manifest": manifest, "vault_root": vault})
            self.assertEqual((status, body.get("status"), body.get("vault_id")),
                             (200, "ok", "handshake_test"))

            status, body = self._call("GET", "/vault/status")
            self.assertEqual((status, body.get("linked"), body.get("vault_root")),
                             (200, True, vault))

            self.assertEqual(self._call("GET", "/vault/search?q=geralt")[0], 200)

            status, body = self._call("POST", "/world/load_mirror", {})
            self.assertEqual((status, body.get("ok")), (200, True))
            status, body = self._call("POST", "/world/sync", {"dry_run": True})
            self.assertEqual((status, body.get("action")), (200, "world/sync"))

        self.runtime.snapshot.pop("vaults", None)
        self.runtime.snapshot.pop("active_vault_id", None)

    def test_world_routes_without_vault_context(self):
        self.runtime.snapshot.pop("vaults", None)
        self.runtime.snapshot.pop("active_vault_id", None)
        self.assertEqual(self._call("POST", "/world/sync", {"dry_run": True})[0], 400)
        self.assertEqual(self._call("POST", "/world/load_mirror", {})[0], 400)


if __name__ == "__main__":
    unittest.main()
