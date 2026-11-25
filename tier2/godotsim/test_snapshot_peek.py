"""
test_snapshot_peek.py -- B1 (TRIXEL32D_LIVE_ROUTE_BLOCKERS_2026-11-05):
observing the runtime scene must not consume client events, and every scene
activation carries a load identity distinct from earlier activations.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

SCENE_ID = "scene.905_snapshot_peek"
DOC = {
    "scene_id": SCENE_ID,
    "@id": SCENE_ID,
    "entities": [],
    "events": [{"type": "narration", "data": {"text": "Still water."}}],
    "segments": [{"text": "Still water."}],
    "reality_mode": "LIVE",
    "actor_authority_tier": 3,
    "issuer": "godot_semantic_runtime",
    "source": "godot_semantic_runtime",
}
EVENT = {"type": "alert", "tick": 0, "message": "peek-probe"}


class TestSnapshotPeek(unittest.TestCase):
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

    def _call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read() or b"{}")

    def _payload(self, path):
        env = self._call("GET", path)
        return env.get("payload", env)

    def _load(self):
        body = self._call("POST", "/scene/load", dict(DOC, expected_scene_activation=self.runtime.scene_manager.current_activation()))
        self.assertEqual(body.get("status"), "loaded")
        return self._payload("/snapshot/peek")["scene_activation"]

    def test_peek_does_not_consume_events_and_snapshot_still_delivers_them(self):
        self._load()
        self.runtime.snapshot["events"].append(dict(EVENT))
        first = self._payload("/snapshot/peek")
        second = self._payload("/snapshot/peek")
        self.assertIn(EVENT, first["events"])
        self.assertEqual(first["events"], second["events"])
        self.assertEqual(first["scene_id"], SCENE_ID)
        # The render client's poll still receives the event, then drains it.
        self.assertIn(EVENT, self._payload("/snapshot")["events"])
        self.assertNotIn(EVENT, self._payload("/snapshot")["events"])

    def test_peek_publishes_the_runtime_reality_context_outside_the_payload(self):
        self._load()
        from tier1.engainos.aproom.reality_mode import get_context
        envelope = self._call("GET", "/snapshot/peek")
        ctx = get_context()
        self.assertEqual(envelope["reality_context"], {"mode": ctx.mode.value, "scene_id": ctx.scene_id})
        self.assertNotIn("reality_context", envelope["payload"])
        self.assertNotIn("reality_context", self.runtime.snapshot)
        self.assertNotIn("reality_context", self._call("GET", "/snapshot"))

    def test_transforms_poll_keeps_its_existing_draining_behaviour(self):
        self._load()
        self.runtime.snapshot["events"].append(dict(EVENT))
        self._call("GET", "/transforms")
        self.assertNotIn(EVENT, self._payload("/snapshot/peek")["events"])

    def test_each_activation_gets_a_new_load_identity_even_for_the_same_scene(self):
        first = self._load()
        second = self._load()
        self.assertEqual(first["scene_id"], SCENE_ID)
        self.assertEqual(first["runtime_instance_id"], self.runtime.runtime_instance_id)
        self.assertEqual(second["load_seq"], first["load_seq"] + 1)
        # Observing does not advance it.
        self.assertEqual(self._payload("/snapshot/peek")["scene_activation"], second)


if __name__ == "__main__":
    unittest.main()
