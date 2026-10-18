"""
test_combat_commit.py -- Combat registration, queueing, execution and commit
against snapshot-owned health.

EngAInRuntime.snapshot owns health/alive; Combat3DAdapter is working state.
Outcomes are distinguished:
  queued    -- gateway accepted, dispatcher appended to runtime.command_queue
  executed  -- drain_commands() ran the queued command into the adapter
  committed -- tick() ran the kernel and wrote health/alive into the snapshot

Real runtime (simulation thread patched out; ticks driven by hand), real
gateway/AP rules, dispatcher, adapter and kernel. No servers.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from tier1.engainos.aproom.reality_mode import RealityMode, reality
from tier2.godotsim import runtime_core
from tier2.godotsim.runtime_gateway import RuntimeGateway

SID = "scene.beach.scene001"


def _scene(sid=SID, pelagor_health=100.0):
    return {
        "scene_id": sid,
        "entities": [
            {"id": "pelagor", "name": "Pelagor", "health": pelagor_health, "max_health": 100.0},
            {"id": "korath", "name": "Korath", "health": 100.0, "max_health": 100.0},
        ],
        "=segments": [{"type": "narration", "text": "The tide turned."}],
    }


class CombatRuntimeCase(unittest.TestCase):
    def setUp(self):
        with patch.object(runtime_core.EngAInRuntime, "_simulation_loop", lambda self: None):
            self.rt = runtime_core.EngAInRuntime()
        self.rt.scene_manager.load_scene(_scene(), activate=True, override_id=SID)

    def attack(self, source="pelagor", target="korath", damage=10):
        return RuntimeGateway(self.rt, self.rt.command_dispatcher).submit({
            "command": "combat/damage", "source": source, "target": target, "damage": damage,
            "reality_mode": "DRAFT", "actor_authority_tier": 1, "actor_id": "test",
        })

    def health(self, eid="korath"):
        return self.rt.snapshot["entities"][eid]["health"]


class TestQueued(CombatRuntimeCase):
    def test_scene_load_registers_working_state_from_snapshot(self):
        self.assertEqual(self.rt.combat.get_entity_health("korath"), (100.0, 100.0))
        self.assertTrue(self.rt.combat.is_alive("pelagor"))

    def test_accepted_hit_is_only_queued(self):
        decision = self.attack()
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.result, {"type": "ack", "status": "queued", "command": "combat/damage"})
        self.assertEqual(len(self.rt.command_queue), 1)
        self.assertEqual(len(self.rt.combat.damage_queue), 0)
        self.assertEqual(self.health(), 100.0)

    def test_ap_rejection_queues_nothing(self):
        self.rt.scene_manager.load_scene(_scene(pelagor_health=5.0), activate=True, override_id=SID)
        decision = self.attack()
        self.assertFalse(decision.accepted)
        self.assertIn("health", decision.reason)
        self.assertEqual(self.rt.command_queue, [])


class TestExecuted(CombatRuntimeCase):
    def test_drain_executes_hit_into_adapter_once(self):
        self.attack()
        self.rt.drain_commands()
        self.assertEqual(len(self.rt.combat.damage_queue), 1)
        self.assertEqual(self.rt.command_queue, [])
        self.assertEqual(self.health(), 100.0)  # executed, not committed

    def test_replay_blocks_execution(self):
        self.attack()
        with reality(RealityMode.REPLAY):
            self.rt.drain_commands()
        self.assertEqual(len(self.rt.combat.damage_queue), 0)
        self.rt.tick()
        self.assertEqual(self.health(), 100.0)

    def test_inventory_and_dialogue_ticks_stay_off(self):
        self.attack()
        with patch.object(self.rt.inventory, "tick") as inv, patch.object(self.rt.dialogue, "tick") as dlg:
            self.rt.drain_commands()
            self.rt.tick()
        inv.assert_not_called()
        dlg.assert_not_called()


class TestCommitted(CombatRuntimeCase):
    def test_tick_commits_exactly_once(self):
        self.attack()
        self.rt.drain_commands()
        self.rt.tick()
        self.assertEqual(self.health(), 90.0)
        self.rt.drain_commands()
        self.rt.tick()
        self.rt.tick()
        self.assertEqual(self.health(), 90.0)
        self.assertNotIn("alive", self.rt.snapshot["entities"]["korath"])  # unchanged, not written

    def test_lethal_hit_commits_dead_state(self):
        self.attack(damage=150)
        self.rt.drain_commands()
        self.rt.tick()
        self.assertEqual(self.health(), 0.0)
        self.assertIs(self.rt.snapshot["entities"]["korath"]["alive"], False)

    def test_commit_builds_on_newer_snapshot_state(self):
        self.attack()
        self.rt.drain_commands()
        self.rt.snapshot["entities"]["korath"]["health"] = 50.0  # newer authoritative value
        self.rt.tick()
        self.assertEqual(self.health(), 40.0)

    def test_entity_that_left_snapshot_is_not_recreated(self):
        self.attack()
        self.rt.drain_commands()
        del self.rt.snapshot["entities"]["korath"]
        self.rt.tick()
        self.assertNotIn("korath", self.rt.snapshot["entities"])

    def test_scene_switch_drops_pending_hits(self):
        self.attack()
        self.rt.drain_commands()
        self.rt.scene_manager.load_scene(_scene("scene.beach.scene002"), activate=True,
                                         override_id="scene.beach.scene002")
        self.rt.tick()
        self.assertEqual(self.health(), 100.0)

    def test_committed_health_feeds_next_ap_check(self):
        self.attack(source="korath", target="pelagor", damage=95)
        self.rt.drain_commands()
        self.rt.tick()
        self.assertEqual(self.health("pelagor"), 5.0)
        decision = self.attack(source="pelagor", target="korath")
        self.assertFalse(decision.accepted)
        self.assertIn("health", decision.reason)


if __name__ == "__main__":
    unittest.main()
