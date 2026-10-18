"""
test_gateway_combat_rules.py -- Regression tests: the 8080 gateway must apply
the gameplay AP rules to the live /combat/damage request.

The live route sends source/target/damage (tier1/engainos/runtime_client.py);
the AP complex rules read attacker/target/amount. Before the fix the gateway
handed the raw request to the rules, no rule matched, and every attack was
dispatched. Only damage the rules allowed may be queued for combat.
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
from tier2.godotsim.command_dispatcher import combat_damage_payload
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
        self.combat = mock.Mock(damage_queue=[])
        # Accepted damage is queued for the simulation thread; capture it here
        # so the live sim loop cannot race the assertions.
        self.add_command = mock.Mock()
        self._patches = [
            mock.patch.object(self.runtime, "combat", self.combat),
            mock.patch.object(self.runtime, "add_command", self.add_command),
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
        self.add_command.assert_not_called()

    def test_self_attack_is_rejected_before_dispatch(self):
        status, body = self._damage("guard", "guard")
        self.assertEqual(status, 403)
        self.assertIn("Cannot attack yourself", body.get("reason", ""))
        self.add_command.assert_not_called()

    def test_valid_attack_is_queued_unchanged(self):
        status, _ = self._damage("guard", "weak", damage=7)
        self.assertEqual(status, 200)
        self.add_command.assert_called_once()
        queued = self.add_command.call_args.args[0]
        self.assertEqual(queued["command"], "combat/damage")
        self.assertEqual(combat_damage_payload(queued),
                         {"source": "guard", "target": "weak", "amount": 7})


if __name__ == "__main__":
    unittest.main()
