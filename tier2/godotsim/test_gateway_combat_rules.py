"""
test_gateway_combat_rules.py -- Regression tests: the 8080 gateway must apply
the gameplay AP rules to the live /combat/damage request.

The live route sends source/target/damage (tier1/engainos/runtime_client.py);
the AP complex rules read attacker/target/amount. Before the fix the gateway
handed the raw request to the rules, no rule matched, and every attack was
dispatched. The combat adapter must only see damage the rules allowed.
"""

from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

from tier2.godotsim import sim_runtime
from tier2.godotsim.http_handlers import RuntimeHTTPHandler
from tier2.godotsim.runtime_core import EngAInRuntime

IDENTITY = {"actor_id": "test", "actor_authority_tier": 1, "reality_mode": "DRAFT"}


class TestGatewayCombatRules(unittest.TestCase):
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
        self.combat = mock.Mock()
        self._patches = [
            mock.patch.object(self.runtime, "combat", self.combat),
            mock.patch.dict(self.runtime.snapshot, {
                "entities": {"weak": {"health": 5.0}, "guard": {"health": 50.0}},
            }),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in reversed(self._patches):
            p.stop()

    def _damage(self, source, target, damage=5):
        body = {"source": source, "target": target, "damage": damage, **IDENTITY}
        req = urllib.request.Request(self.base + "/combat/damage", data=json.dumps(body).encode(),
                                     method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read() or b"{}")

    def test_weak_attacker_is_rejected_before_dispatch(self):
        status, body = self._damage("weak", "guard")
        self.assertEqual(status, 403)
        self.assertEqual(body.get("error"), "governance_rejected")
        self.assertIn("health >= 10", body.get("reason", ""))
        self.combat.handle_delta.assert_not_called()

    def test_self_attack_is_rejected_before_dispatch(self):
        status, body = self._damage("guard", "guard")
        self.assertEqual(status, 403)
        self.assertIn("Cannot attack yourself", body.get("reason", ""))
        self.combat.handle_delta.assert_not_called()

    def test_valid_attack_is_dispatched_unchanged(self):
        status, _ = self._damage("guard", "weak", damage=7)
        self.assertEqual(status, 200)
        self.combat.handle_delta.assert_called_once_with(
            "combat3d/apply_damage", {"source": "guard", "target": "weak", "amount": 7})


if __name__ == "__main__":
    unittest.main()
