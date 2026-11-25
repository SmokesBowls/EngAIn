"""Operation A: restored pass1_spatial consumes real pass1_explicit output."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PASSROOM = Path(__file__).resolve().parents[1] / "passroom"
sys.path.insert(0, str(PASSROOM))
from pass1_spatial import process_file  # noqa: E402

FIXTURE = "The guard stood before the stone gate.\nThe king approached the guard.\n"
EXPECTED = [
    ("spatial_signal", "in_front_of", "guard", "stone gate", "OLINK", 1),
    ("movement_signal", "stand", "guard", "before", "MOVELINK", 1),
    ("movement_signal", "approach", "king", "guard", "MOVELINK", 2),
]


class Pass1SpatialRecovery(unittest.TestCase):
    def test_fixture_through_real_pass1_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "input.txt").write_text(FIXTURE, encoding="utf-8")
            subprocess.run([sys.executable, str(PASSROOM / "pass1_explicit.py"),
                            str(tmp / "input.txt"), str(tmp / "explicit.txt")],
                           check=True, capture_output=True)
            result = process_file(tmp / "explicit.txt", tmp / "spatial.json")
            on_disk = json.loads((tmp / "spatial.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk, result)
        self.assertEqual(set(result), {"source_pass1", "signal_count", "signals"})
        self.assertEqual(result["signal_count"], 3)
        got = [(s["signal_type"], s["relation"], s["subject_hint"], s["object_hint"],
                s["topology_link_hint"], s["line"]) for s in result["signals"]]
        self.assertEqual(got, EXPECTED)


if __name__ == "__main__":
    unittest.main()
