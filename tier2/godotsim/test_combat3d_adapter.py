"""
test_combat3d_adapter.py -- Regression tests: Combat3DAdapter.tick() must work
with the canonical kernels/combat3d_mr.py.

The 2026-06-21 kernel relocation made the dict-alert kernel canonical, but the
adapter still unpacked alerts as (entity_id, alert_type) tuples and raised
ValueError on the first processed damage. Real adapter, real kernel, no mocks;
the runtime tick is not involved.
"""

from __future__ import annotations

import unittest

from tier2.godotsim.adapters.combat3d_adapter import Combat3DAdapter


class TestCombat3DAdapterTick(unittest.TestCase):
    def setUp(self):
        self.combat = Combat3DAdapter()
        self.combat.register_entity("guard", health=50.0, max_health=50.0)
        self.combat.register_entity("scout", health=20.0, max_health=50.0)

    def _hit(self, target, amount, source="guard"):
        self.combat.handle_delta("combat3d/apply_damage",
                                 {"source": source, "target": target, "amount": amount})
        return self.combat.tick(1.0 / 60.0)

    def test_damage_lowers_health_without_alert_deltas(self):
        deltas = self._hit("guard", 7.0, source="scout")
        self.assertEqual(deltas, [])
        self.assertEqual(self.combat.get_entity_health("guard"), (43.0, 50.0))
        state = self.combat.get_all_state()
        self.assertEqual(state["entity_hp"]["guard"], 43.0)
        self.assertEqual(state["pending_damage"], [])

    def test_low_health_sets_flag(self):
        deltas = self._hit("scout", 8.0)  # 12 <= 25% of 50
        self.assertEqual(deltas, [("behavior3d/set_flag", {"entity": "scout", "flag": "low_health"})])

    def test_death_sets_dead_and_disables_navigation(self):
        deltas = self._hit("scout", 25.0)
        self.assertEqual(deltas, [
            ("behavior3d/set_flag", {"entity": "scout", "flag": "dead"}),
            ("navigation3d/disable", {"entity": "scout"}),
        ])
        self.assertFalse(self.combat.is_alive("scout"))

    def test_unknown_target_is_ignored(self):
        self.assertEqual(self._hit("nobody", 10.0), [])
        self.assertNotIn("nobody", self.combat.get_all_state()["entity_hp"])


if __name__ == "__main__":
    unittest.main()
