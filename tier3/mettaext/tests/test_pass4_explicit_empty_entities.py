"""
test_pass4_explicit_empty_entities.py — Regression tests for Pass 4's
@entities branch (ZONBridge.extract_entities).

An explicit "@entities": [] is an upstream answer ("no spawnable entities"),
not a missing value, so it must not trigger the narration-scan fallback.
Without this, a compatibility adapter that writes [] after a successful
extraction would have its decision overridden by world_rules name matching.
Pass 3 omits the key when empty, so legacy scenes keep the fallback.

Real world_rules.json fixtures:
  Vairis -- known, spawnable: true
  Lyaris -- known, spawnable: false
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tier3.mettaext.passroom.pass4_zon_bridge import ZONBridge, ZONMetadata

WORLD_RULES_FILE = Path("tier1/engainos/assets/world_rules.json")
NARRATION = [{"line": 1, "type": "narration", "text": "Vairis watched the shore while Lyaris waited."}]


def _scene(**extra) -> dict:
    return {"type": "scene", "id": "scene.t.scene001", "segments": NARRATION, **extra}


class TestPass4EntitiesBranch(unittest.TestCase):
    def setUp(self):
        self.bridge = ZONBridge(world_rules_path=WORLD_RULES_FILE)

    def test_missing_entities_keeps_narration_scan_fallback(self):
        self.assertEqual(self.bridge.extract_entities(_scene()), ["Vairis"])

    def test_explicit_empty_suppresses_narration_scan(self):
        self.assertEqual(self.bridge.extract_entities(_scene(**{"@entities": []})), [])

    def test_populated_list_unchanged(self):
        self.assertEqual(self.bridge.extract_entities(_scene(**{"@entities": ["vairis", "Lyaris"]})), ["Vairis"])

    def test_non_list_value_still_treated_as_missing(self):
        self.assertEqual(self.bridge.extract_entities(_scene(**{"@entities": None})), ["Vairis"])

    def test_explicit_empty_reaches_both_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zonj_scene.t.scene001.json"
            path.write_text(json.dumps(_scene(**{"@entities": []})), encoding="utf-8")
            meta = ZONMetadata()
            self.assertEqual(self.bridge.convert_to_zonj(path, meta)["@entities"], [])
            self.assertNotIn("@entities:", self.bridge.convert_to_zon(path, meta))

    def test_missing_input_fails_without_output(self):
        # A failed upstream extraction leaves no Pass 3 file; Pass 4 must fail, not emit an empty scene.
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            result = subprocess.run(
                [sys.executable, "-m", "tier3.mettaext.passroom.pass4_zon_bridge",
                 str(Path(tmp) / "zonj_missing.json"), "--output-dir", str(out_dir),
                 "--world-rules", str(WORLD_RULES_FILE)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(out_dir.exists() and any(out_dir.iterdir()))


if __name__ == "__main__":
    unittest.main()
