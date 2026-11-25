"""Operation F: signed scene activation on 8080 and snapshot consistency."""

from __future__ import annotations

import json
import os
import stat
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tier1.engainos.aproom.reality_mode import RealityMode, reality
from tier1.engainos.authority.local_signed_transport import SignedRequestVerifier, signed_headers
from tier2.godotsim import scene_activation_intake as sai
from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

ACTIVATOR, STRANGER = "test-activator", "test-stranger"
SECRETS = {ACTIVATOR: b"\x05" * 32, STRANGER: b"\x06" * 32}


def doc(scene_id, text="Candidate."):
    return {"scene_id": scene_id, "@id": scene_id, "entities": [],
            "events": [{"type": "narration", "data": {"text": text}}], "segments": [{"text": text}]}


class TestSignedSceneActivation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RuntimeHTTPHandler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        RuntimeHTTPHandler.activation_intake = None

    def setUp(self):
        self.runtime = EngAInRuntime()
        RuntimeHTTPHandler.runtime = self.runtime
        sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, self.runtime)
        self.env = mock.patch.dict(os.environ, {sai.FLAG_ENV: "1"})
        self.env.start()
        # Only ACTIVATOR holds the activate role; STRANGER's secret is unknown here.
        RuntimeHTTPHandler.activation_intake = sai.SceneActivationIntake(
            SignedRequestVerifier({ACTIVATOR: SECRETS[ACTIVATOR]}), frozenset({ACTIVATOR}))

    def tearDown(self):
        self.env.stop()

    def _post(self, raw, headers):
        req = urllib.request.Request(self.base + sai.ACTIVATION_PATH, data=raw, method="POST",
                                     headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")

    def _activate(self, scene, expected="current", client=ACTIVATOR, extra=None, sign=True):
        if expected == "current":
            expected = self.runtime.scene_manager.current_activation()
        body = {"scene": scene, "expected_scene_activation": expected, **(extra or {})}
        raw = json.dumps(body).encode()
        headers = signed_headers(client, SECRETS[client], "POST", sai.ACTIVATION_PATH, raw) if sign else {}
        return self._post(raw, headers)

    def _stamp(self):
        return self.runtime.scene_manager.current_activation()

    # ── gates ──
    def test_flag_off_and_uncomposed(self):
        with mock.patch.dict(os.environ, {sai.FLAG_ENV: "0"}):
            self.assertEqual(self._activate(doc("scene.a"))[0], 404)
        RuntimeHTTPHandler.activation_intake = None
        self.assertEqual(self._activate(doc("scene.a"))[0], 503)
        self.assertIsNone(self._stamp())

    def test_unauthenticated_and_unassigned_refused(self):
        self.assertEqual(self._activate(doc("scene.a"), sign=False)[0], 401)
        self.assertIn(self._activate(doc("scene.a"), client=STRANGER)[0], (401, 403))
        raw = json.dumps({"scene": doc("scene.a"), "expected_scene_activation": None}).encode()
        tampered = signed_headers(ACTIVATOR, SECRETS[ACTIVATOR], "POST", sai.ACTIVATION_PATH, raw + b" ")
        self.assertEqual(self._post(raw, tampered)[0], 401)
        self.assertIsNone(self._stamp())

    def test_signed_activation_succeeds_and_is_observable(self):
        status, body = self._activate(doc("scene.a"))
        self.assertEqual((status, body["status"]), (200, "loaded"), body)
        stamp = body["scene_activation"]
        self.assertEqual(stamp, self._stamp())
        payload = self.runtime.get_snapshot()["payload"]
        self.assertEqual((payload["scene_activation"], payload["scene_id"], payload["scene"]["scene_id"]),
                         (stamp, "scene.a", "scene.a"))

    def test_client_cannot_declare_actor_tier_or_mode(self):
        for extra in ({"actor_authority_tier": 3}, {"reality_mode": "LIVE"}, {"actor_id": "op"}):
            with self.subTest(extra=extra):
                self.assertEqual(self._activate(doc("scene.a"), extra=extra)[0], 400)
        self.assertIsNone(self._stamp())

    def test_runtime_mode_decides_not_the_client(self):
        for mode in (RealityMode.REPLAY, RealityMode.FINALIZED, RealityMode.IMBUED, RealityMode.DREAM):
            with self.subTest(mode=mode), reality(mode):
                self.assertEqual(self._activate(doc("scene.a"))[0], 403)
        self.assertIsNone(self._stamp())
        self.assertEqual(self._activate(doc("scene.a"))[0], 200)  # back in DRAFT

    def test_finalized_scene_refused_without_tier_override(self):
        with mock.patch("tier1.engainos.aproom.canon.can_edit", return_value=False):
            self.assertEqual(self._activate(doc("scene.a"))[0], 403)
        self.assertIsNone(self._stamp())

    def test_stale_and_same_scene_reload_protected(self):
        self.assertEqual(self._activate(doc("scene.a"))[0], 200)
        first = self._stamp()
        self.assertEqual(self._activate(doc("scene.b"))[0], 200)
        status, body = self._activate(doc("scene.c"), expected=first)          # stale
        self.assertEqual((status, body["reason"]), (409, "stale_scene_activation"))
        self.assertEqual(self._activate(doc("scene.c"), expected=None)[0], 409)  # missing precondition
        second = self._stamp()
        # Same-scene reload: refused without the current stamp, a fresh load with it.
        self.assertEqual(self._activate(doc("scene.b", "Rewritten."), expected=None)[0], 409)
        self.assertEqual(self._activate(doc("scene.b", "Rewritten."), expected=first)[0], 409)
        self.assertEqual(self._stamp(), second)
        self.assertEqual(self._activate(doc("scene.b", "Rewritten."))[0], 200)
        self.assertEqual(self._stamp()["load_seq"], second["load_seq"] + 1)

    def test_snapshot_is_consistent_under_concurrent_activation(self):
        self.assertEqual(self._activate(doc("scene.s0"))[0], 200)
        manager, stop, errors = self.runtime.scene_manager, threading.Event(), []
        # Widen the reader's window between its snapshot copy and its hydration: an
        # unlocked reader then reliably pairs a copied stamp with a moved pointer.
        original = sim_runtime._hydrate_snapshot_scene

        def slow_hydrate(*a, **kw):
            time.sleep(0.003)
            return original(*a, **kw)

        patcher = mock.patch.object(sim_runtime, "_hydrate_snapshot_scene", slow_hydrate)
        patcher.start()
        self.addCleanup(patcher.stop)

        def churn():
            i = 0
            while not stop.is_set():
                i += 1
                with manager.activation_lock:
                    manager.load_scene(doc(f"scene.s{i}"), activate=True,
                                       expected_activation=manager.current_activation())

        writer = threading.Thread(target=churn, daemon=True)
        writer.start()
        try:
            for _ in range(200):
                try:
                    payload = self.runtime.get_snapshot()["payload"]
                except RuntimeError as exc:  # dict changed size during copy
                    errors.append(repr(exc))
                    continue
                ids = (payload["scene_activation"]["scene_id"], payload["scene_id"], payload["scene"]["scene_id"])
                if len(set(ids)) != 1:
                    errors.append(ids)
        finally:
            stop.set()
            writer.join(5)
        self.assertEqual(errors, [])


class TestActivationComposition(unittest.TestCase):
    def test_deny_all_policy_composes_nothing_and_writes_no_credentials(self):
        with TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {sai.FLAG_ENV: "1"}):
            intake, reason = sai.compose_from_environment(policy_path=sai.DEFAULT_POLICY_PATH, transport_dir=Path(tmp))
            self.assertIsNone(intake)
            self.assertIn("deny-all", reason)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_activate_role_cannot_carry_actor_or_tier(self):
        with TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {sai.FLAG_ENV: "1"}):
            policy = Path(tmp) / "p.json"
            policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {
                ACTIVATOR: {"routes": ["activate"], "actor_id": "x", "actor_authority_tier": 3}}}))
            intake, reason = sai.compose_from_environment(policy_path=policy, transport_dir=Path(tmp) / "t")
            self.assertIsNone(intake)
            self.assertIn("invalid", reason)
            policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {
                ACTIVATOR: {"routes": ["build"]}}}))
            self.assertIsNone(sai.compose_from_environment(policy_path=policy, transport_dir=Path(tmp) / "t")[0])

    def test_isolated_test_policy_provisions_0600_credentials(self):
        with TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {sai.FLAG_ENV: "1"}):
            policy = Path(tmp) / "p.json"
            policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1",
                                          "clients": {ACTIVATOR: {"routes": ["activate"]}}}))
            intake, reason = sai.compose_from_environment(policy_path=policy, transport_dir=Path(tmp) / "t")
            self.assertEqual(reason, "composed")
            key = Path(tmp) / "t" / sai.SERVER_NAME / f"{ACTIVATOR}.key"
            self.assertEqual(stat.S_IMODE(key.stat().st_mode), 0o600)

    def test_flag_off_composes_nothing(self):
        with mock.patch.dict(os.environ, {sai.FLAG_ENV: "0"}):
            self.assertIsNone(sai.compose_from_environment()[0])


if __name__ == "__main__":
    unittest.main()
