"""
test_stageroom_scene_delivery.py -- A Stageroom scene delivered by the resolver
satisfies the runtime's scene contract (narrative, where/when, structured
entities with health), and a valid attack passes the AP rules.

Passing the AP rules is not combat execution: the accepted hit is only queued;
no health changes (ticks and registration are separate, unresolved work).
Isolated fixtures, real resolver, real SceneManager, real AP rules, real combat
adapter; stub runtime holding only the snapshot. No servers, no ticks.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tier1.engainos.aproom.ap_complex_rules import check_complex_rules
from tier1.engainos.bridgeroom.stageroom_scene_resolver import StageroomSceneResolver
from tier2.godotsim.adapters.combat3d_adapter import Combat3DAdapter
from tier2.godotsim.command_dispatcher import CommandDispatcher
from tier2.godotsim.runtime_gateway import _ap_rule_view
from tier2.godotsim.scene_manager import SceneManager

SID = "scene.beach.scene001"
ENTITIES = [
    {"id": "pelagor", "name": "Pelagor", "health": 100.0, "max_health": 100.0,
     "position": {"x": 0.0, "y": 0.0, "z": 0.0}, "type": "character"},
    {"id": "korath", "name": "Korath", "health": 100.0, "max_health": 100.0,
     "position": {"x": 2.0, "y": 0.0, "z": 0.0}, "type": "character"},
]


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestStageroomSceneDelivery(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "stageroom"
        _write(root / "output/chapterroom/scene_packets/chapter.beach/scene_packets_index.json",
               {"packets": [{"scene_id": SID, "chapter_id": "chapter.beach"}]})
        scene_dir = root / "output/passroom" / SID
        _write(scene_dir / "game_scenes" / f"{SID}.json",
               {"scene_id": SID, "entities": ENTITIES, "events": [],
                "metadata": {"where": "Realm/Physical/Beach", "when": "t0"}})
        _write(scene_dir / f"{SID}.zonj.json",
               {"@id": SID, "@entities": ["Pelagor", "Korath"],
                "=segments": [{"type": "narration", "text": "The tide turned against the cliffs."}]})

        doc = StageroomSceneResolver(root).load_scene(SID)
        self.runtime = SimpleNamespace(snapshot={
            "scene_id": None, "entities": {}, "spatial": {}, "perception": {},
            "behavior": {}, "world": {"time": 0.0}, "events": [], "scene": None,
            "scene_raw": None,
        })
        self.scenes = SceneManager(self.runtime)
        self.scenes.load_scene(doc, activate=True, override_id=SID)

    def test_narrative_where_when_reach_text_pipeline(self):
        scene = self.runtime.snapshot["scene"]
        self.assertEqual(len(scene["segments"]), 1)
        self.assertEqual((scene["where"], scene["when"]), ("Realm/Physical/Beach", "t0"))
        look = json.dumps(self.scenes.handle_text_command("look"))
        self.assertIn("The tide turned against the cliffs.", look)

    def test_structured_entities_with_health_reach_snapshot(self):
        entities = self.runtime.snapshot["entities"]
        self.assertEqual(entities["pelagor"]["health"], 100.0)
        self.assertEqual(entities["korath"]["max_health"], 100.0)

    def test_valid_attack_passes_ap_but_is_not_executed(self):
        request = {"command": "combat/damage", "source": "pelagor", "target": "korath", "damage": 10}
        self.assertEqual(check_complex_rules(_ap_rule_view(request), self.runtime.snapshot), [])

        self.runtime.combat = Combat3DAdapter()
        result = CommandDispatcher(self.runtime, self.scenes).dispatch(request)
        self.assertEqual(result["status"], "damage_applied")  # the ack only
        self.assertEqual(len(self.runtime.combat.pending_damage), 1)  # queued, not ticked
        self.assertEqual(self.runtime.combat.get_entity_health("korath"), (0.0, 0.0))  # never registered
        self.assertEqual(self.runtime.snapshot["entities"]["korath"]["health"], 100.0)  # unchanged


if __name__ == "__main__":
    unittest.main()
