"""
test_environment_generation_gate.py -- T03-R1: Blender environment generation is opt-in.

Scene loading must succeed and be stamped without inferring terrain from scene text
or contacting Blender MCP, unless ENGAIN_BLENDER_ENVIRONMENT=1. Uses an isolated
8080 handler and a real Chapterroom-indexed scene served by the existing Tier 1
resolver (read-only).
"""

from __future__ import annotations

import json
import os
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

from tier2.godotsim import environment_manager as em
from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

IDENTITY = {"reality_mode": "DRAFT", "actor_authority_tier": 2,
            "actor_id": "t03r1-test", "source_system": "t03r1-test"}


def _existing_scene():
    """First Chapterroom scene the existing resolver delivers with its Pass 4 segments."""
    try:
        from tier1.engainos.bridgeroom.stageroom_scene_resolver import StageroomSceneResolver
        resolver = StageroomSceneResolver(None)
        for scene_id in sorted(resolver.list_available_scenes()):
            scene = resolver.load_scene(scene_id)
            if "=segments" in scene or "segments" in scene:
                return scene
    except Exception:
        return None
    return None


class TestEnvironmentGenerationGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = _existing_scene()
        if cls.scene is None:
            raise unittest.SkipTest("no Chapterroom scene with segments available")
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
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")

    def _peek_payload(self):
        status, env = self._call("GET", "/snapshot/peek")
        self.assertEqual(status, 200)
        return env.get("payload", env)

    def _load(self):
        return self._call("POST", "/scene/load", {"scene": json.loads(json.dumps(self.scene)), **IDENTITY})

    def test_factory_is_off_unless_explicitly_opted_in(self):
        for value in (None, "", "0", "true", "yes"):
            env = {k: v for k, v in os.environ.items() if k != em.BLENDER_ENVIRONMENT_OPT_IN}
            if value is not None:
                env[em.BLENDER_ENVIRONMENT_OPT_IN] = value
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertIsNone(em.environment_manager_from_env(), value)
        with mock.patch.dict(os.environ, {em.BLENDER_ENVIRONMENT_OPT_IN: "1"}):
            self.assertIsInstance(em.environment_manager_from_env(), em.EnvironmentManager)

    def test_default_load_is_stamped_without_inference_or_blender(self):
        env = {k: v for k, v in os.environ.items() if k != em.BLENDER_ENVIRONMENT_OPT_IN}
        with mock.patch.dict(os.environ, env, clear=True):
            self.runtime.env_manager = em.environment_manager_from_env()
        self.assertIsNone(self.runtime.env_manager)
        before = self._peek_payload().get("scene_activation") or {}

        infer = mock.Mock(side_effect=AssertionError("terrain inferred"))
        http = mock.Mock(side_effect=AssertionError("Blender MCP contacted"))
        with mock.patch.object(em.EnvironmentManager, "_infer_terrain_profile", infer), \
                mock.patch.object(em.httpx, "AsyncClient", http):
            status, body = self._load()
            time.sleep(0.5)  # generation would run in a daemon thread
        self.assertEqual((status, body.get("status")), (200, "loaded"))
        infer.assert_not_called()
        http.assert_not_called()

        payload = self._peek_payload()
        stamp = payload["scene_activation"]
        self.assertEqual(stamp["scene_id"], body["scene_id"])
        self.assertEqual(payload["scene_id"], body["scene_id"])
        self.assertEqual(stamp["runtime_instance_id"], self.runtime.runtime_instance_id)
        self.assertEqual(stamp["load_seq"], before.get("load_seq", 0) + 1)

        # Terrain is only what the scene brought; nothing generated or inferred is added.
        meta = self.scene.get("metadata") if isinstance(self.scene.get("metadata"), dict) else {}
        expected = dict(self.scene.get("terrain_metadata") or {})
        if meta.get("environment_inference"):
            expected["environment_inference"] = meta["environment_inference"]
        self.assertEqual(self.runtime.snapshot["scene"]["terrain"], expected)
        self.assertEqual(self._call("GET", f"/environment/terrain/{body['scene_id']}"),
                         (200, {"status": "not_found"}))

    def test_opt_in_still_reaches_the_preserved_blender_path(self):
        with mock.patch.dict(os.environ, {em.BLENDER_ENVIRONMENT_OPT_IN: "1"}):
            self.runtime.env_manager = em.environment_manager_from_env()
        reached = threading.Event()
        real_infer = em.EnvironmentManager._infer_terrain_profile

        def infer(manager, scene_data):
            reached.set()
            return real_infer(manager, scene_data)

        async def no_mcp(*_args, **_kwargs):
            return None  # never touch a real Blender server from a test

        async def session_ok(_manager):
            return True

        http = mock.Mock(side_effect=AssertionError("Blender MCP contacted"))
        try:
            with mock.patch.object(em.EnvironmentManager, "_infer_terrain_profile", infer), \
                    mock.patch.object(em.EnvironmentManager, "initialize_session", session_ok), \
                    mock.patch.object(em.EnvironmentManager, "_mcp_call", no_mcp), \
                    mock.patch.object(em.httpx, "AsyncClient", http):
                status, body = self._load()
                self.assertEqual((status, body.get("status")), (200, "loaded"))
                self.assertTrue(reached.wait(5), "opted-in load did not reach terrain inference")
        finally:
            self.runtime.env_manager = None


if __name__ == "__main__":
    unittest.main()
