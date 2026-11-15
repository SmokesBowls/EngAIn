"""Signed Godot presentation testimony on the real 8080 handler (POST /presentation/observation)."""

from __future__ import annotations

import http.client
import json
import os
import stat
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tier1.engainos.authority.local_signed_transport import SignedRequestVerifier, signed_headers
from tier2.godotsim import presentation_observation as po
from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

OBSERVER, OTHER = "test-observer", "test-builder"
SECRETS = {OBSERVER: b"\x03" * 32, OTHER: b"\x04" * 32}
SCENE_ID = "scene.906_presentation_observation"
# Same scene-load shape the existing peek test uses against the real gateway.
DOC = {
    "scene_id": SCENE_ID, "@id": SCENE_ID, "entities": [],
    "events": [{"type": "narration", "data": {"text": "Observed."}}],
    "segments": [{"text": "Observed."}],
    "reality_mode": "LIVE", "actor_authority_tier": 3,
    "issuer": "godot_semantic_runtime", "source": "godot_semantic_runtime",
}


class TestPresentationObservation(unittest.TestCase):
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
        RuntimeHTTPHandler.presentation_intake = None

    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"TRIXEL32D_LIVE_ROUTE": "1"})
        self.env.start()
        # Only OBSERVER holds the observe role; OTHER's secret is unknown to this server.
        RuntimeHTTPHandler.presentation_intake = po.PresentationObservationIntake(
            SignedRequestVerifier({OBSERVER: SECRETS[OBSERVER]}), frozenset({OBSERVER}))
        RuntimeHTTPHandler.runtime = self.runtime
        self.seq = 0

    def tearDown(self):
        self.env.stop()

    # ── helpers ──
    def _request(self, method, path, raw=None, headers=None):
        req = urllib.request.Request(self.base + path, data=raw, method=method,
                                     headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")

    def _load(self):
        status, body = self._request("POST", "/scene/load", json.dumps(DOC).encode())
        self.assertEqual(body.get("status"), "loaded")
        return dict(self._peek()["payload"]["scene_activation"])

    def _peek(self):
        return self._request("GET", "/snapshot/peek")[1]

    def _report(self, load, *, client=OBSERVER, seq=None, gen=0, main=7, active=True, headers=None, raw=None):
        if seq is None:
            self.seq += 1
            seq = self.seq
        raw = raw if raw is not None else json.dumps({
            "observed_load": load, "main_instance_id": main, "local_generation": gen,
            "presentation_active": active, "report_seq": seq,
        }).encode()
        headers = headers if headers is not None else signed_headers(client, SECRETS[client], "POST", po.OBSERVATION_PATH, raw)
        return self._request("POST", po.OBSERVATION_PATH, raw, headers)

    # ── tests ──
    def test_flag_off_keeps_the_endpoint_absent(self):
        load = self._load()
        with mock.patch.dict(os.environ, {"TRIXEL32D_LIVE_ROUTE": "0"}):
            self.assertEqual(self._report(load)[0], 404)
        self.assertEqual(self._peek()["presentation_observations"], {})

    def test_uncomposed_intake_is_503(self):
        RuntimeHTTPHandler.presentation_intake = None
        self.assertEqual(self._report(self._load())[0], 503)
        self.assertNotIn("presentation_observations", self._peek())

    def test_valid_report_is_retained_as_testimony_and_published_without_consumption(self):
        load = self._load()
        status, body = self._report(load, gen=2)
        self.assertEqual(status, 200, body)
        first, second = self._peek(), self._peek()
        record = first["presentation_observations"][OBSERVER]
        self.assertEqual(first["presentation_observations"], second["presentation_observations"])
        self.assertEqual(record["testimony"], "AUTHENTICATED_CLIENT_TESTIMONY")
        self.assertEqual((record["client_id"], record["observed_load"], record["local_generation"]), (OBSERVER, load, 2))
        self.assertEqual(len(record["transport_nonce"]), 32)
        self.assertNotIn("presentation_observations", self.runtime.snapshot)
        self.assertNotIn("presentation_observations", self._request("GET", "/snapshot")[1])

    def test_unsigned_or_foreign_reports_are_refused_and_not_retained(self):
        load = self._load()
        raw = json.dumps({"observed_load": load}).encode()
        self.assertEqual(self._request("POST", po.OBSERVATION_PATH, raw)[0], 401)
        status, body = self._report(load, client=OTHER)
        self.assertEqual(status, 401, body)
        self.assertIn("not a provisioned", body["errors"][0])
        self.assertEqual(self._peek()["presentation_observations"], {})

    def test_replayed_request_is_refused(self):
        load = self._load()
        raw = json.dumps({"observed_load": load, "main_instance_id": 7, "local_generation": 0,
                          "presentation_active": True, "report_seq": 1}).encode()
        headers = signed_headers(OBSERVER, SECRETS[OBSERVER], "POST", po.OBSERVATION_PATH, raw)
        self.assertEqual(self._report(load, raw=raw, headers=headers)[0], 200)
        status, body = self._report(load, raw=raw, headers=headers)
        self.assertEqual(status, 401)
        self.assertIn("already used", body["errors"][0])

    def test_reports_for_other_loads_are_refused(self):
        load = self._load()
        for wrong in (dict(load, load_seq=load["load_seq"] - 1), dict(load, load_seq=load["load_seq"] + 1),
                      dict(load, runtime_instance_id="another-runtime"), dict(load, scene_id="scene.other")):
            status, body = self._report(wrong)
            self.assertEqual(status, 409, wrong)
            self.assertIn("not the runtime's current load", body["errors"][0])

    def test_reload_supersedes_the_old_load(self):
        old = self._load()
        self.assertEqual(self._report(old)[0], 200)
        new = self._load()
        status, body = self._report(old)
        self.assertEqual(status, 409)
        # The retained record still names the old load, so 8765 refuses it as stale.
        self.assertEqual(self._peek()["presentation_observations"][OBSERVER]["observed_load"], old)
        self.assertEqual(self._report(new)[0], 200)

    def test_delayed_and_regressing_reports_are_refused(self):
        load = self._load()
        self.assertEqual(self._report(load, seq=5, gen=3)[0], 200)
        status, body = self._report(load, seq=4, gen=3)   # delayed: arrives after seq 5
        self.assertEqual(status, 409)
        self.assertIn("out of order", body["errors"][0])
        status, body = self._report(load, seq=6, gen=2)   # generation went backwards
        self.assertEqual(status, 409)
        self.assertIn("regresses", body["errors"][0])
        self.assertEqual(self._report(load, seq=7, gen=3, active=False)[0], 200)

    def test_godot_process_restart_starts_a_new_sequence(self):
        load = self._load()
        self.assertEqual(self._report(load, seq=9, main=7)[0], 200)
        self.assertEqual(self._report(load, seq=1, main=8)[0], 200)
        self.assertEqual(self._peek()["presentation_observations"][OBSERVER]["main_instance_id"], 8)

    def test_runtime_restart_refuses_reports_for_the_old_runtime(self):
        load = self._load()
        restarted = EngAInRuntime()
        self.assertNotEqual(restarted.runtime_instance_id, self.runtime.runtime_instance_id)
        RuntimeHTTPHandler.runtime = restarted
        sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, restarted)
        try:
            status, body = self._report(load)
            self.assertEqual(status, 409)
            self.assertIn("no current scene load", body["errors"][0])
        finally:
            RuntimeHTTPHandler.runtime = self.runtime
            sim_runtime._install_live_edit_shims(RuntimeHTTPHandler, self.runtime)

    def test_malformed_and_oversized_reports_are_refused(self):
        load = self._load()
        for raw in (b"not json", json.dumps({"observed_load": load}).encode(),
                    json.dumps({"observed_load": load, "main_instance_id": True, "local_generation": 0,
                                "presentation_active": True, "report_seq": 1}).encode(),
                    json.dumps({"observed_load": load, "main_instance_id": 7, "local_generation": 0,
                                "presentation_active": True, "report_seq": 1, "tier": 3}).encode()):
            self.assertEqual(self._report(load, raw=raw)[0], 400, raw)
        # Declared oversize: refused from the header, before the body is read.
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=30)
        try:
            conn.putrequest("POST", po.OBSERVATION_PATH)
            conn.putheader("Content-Length", str(17 * 1024 * 1024))
            conn.endheaders()
            self.assertEqual(conn.getresponse().status, 413)
        finally:
            conn.close()
        self.assertEqual(self._peek()["presentation_observations"], {})


class TestComposition(unittest.TestCase):
    def test_composition_is_deny_all_without_an_observer(self):
        with TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"TRIXEL32D_LIVE_ROUTE": "1"}):
            policy = Path(tmp) / "policy.json"
            policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {}}))
            intake, why = po.compose_from_environment(policy_path=policy, transport_dir=Path(tmp) / "t")
            self.assertIsNone(intake)
            self.assertIn("deny-all", why)
            self.assertFalse((Path(tmp) / "t").exists())
        with mock.patch.dict(os.environ, {"TRIXEL32D_LIVE_ROUTE": "0"}):
            self.assertIsNone(po.compose_from_environment()[0])

    def test_observer_gets_a_private_8080_credential(self):
        with TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"TRIXEL32D_LIVE_ROUTE": "1"}):
            policy = Path(tmp) / "policy.json"
            policy.write_text(json.dumps({"contract": "engainos.local_client_policy.v1", "clients": {
                OBSERVER: {"routes": ["observe"]},
                OTHER: {"actor_id": "disposable-builder", "actor_authority_tier": 2, "routes": ["build"]},
            }}))
            intake, why = po.compose_from_environment(policy_path=policy, transport_dir=Path(tmp) / "t")
            self.assertEqual(why, "composed")
            keys = sorted(p.name for p in (Path(tmp) / "t" / "8080").iterdir())
            self.assertEqual(keys, [f"{OBSERVER}.key"])
            self.assertEqual(stat.S_IMODE(os.stat(Path(tmp) / "t" / "8080" / keys[0]).st_mode), 0o600)

    def test_production_policy_composes_no_intake(self):
        with mock.patch.dict(os.environ, {"TRIXEL32D_LIVE_ROUTE": "1"}):
            intake, why = po.compose_from_environment(transport_dir=Path("/nonexistent-should-not-be-created"))
            self.assertIsNone(intake)
            self.assertIn("deny-all", why)


if __name__ == "__main__":
    unittest.main()
