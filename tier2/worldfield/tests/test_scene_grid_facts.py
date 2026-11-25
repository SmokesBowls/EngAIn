"""Operation D: one WorldField instance feeds grid facts; recipes exist in Trixel."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TRIXEL_RECIPES = ROOT.parent / "trixel3.2d" / "recipes" / "terrain"
sys.path.insert(0, str(ROOT))

from tier2.worldfield.grid_facts_emitter import TERRAIN_TO_RECIPE, emit_grid_facts  # noqa: E402
from tier2.worldfield.terrain_thresholds import value_to_terrain  # noqa: E402
from tier2.worldfield.trixel_world_adapter import field_from_elevation_grid, make_wired_field  # noqa: E402

# 5 wide x 3 deep, asymmetric, crosses a chunk boundary with chunk_size=4
ELEV = [
    [0.00, 0.10, 0.30, 0.55, 0.90],
    [0.05, 0.20, 0.45, 0.70, 1.00],
    [0.00, 0.00, 0.35, 0.60, 0.80],
]


class SceneGridFacts(unittest.TestCase):
    def test_emitter_reads_the_populated_field(self):
        field, _, adapter = field_from_elevation_grid(ELEV, "coastal_beach", chunk_size=4)
        pkt = emit_grid_facts(field, adapter)
        self.assertEqual((pkt["width"], pkt["height"], len(pkt["cells"])), (5, 3, 15))
        for i, c in enumerate(pkt["cells"]):
            self.assertEqual((c["field_x"], c["field_y"]), (i % 5, i // 5))       # dense row-major
            self.assertEqual(c["elevation"], ELEV[c["field_y"]][c["field_x"]])    # numerical substrate
            self.assertEqual(c["terrain"], value_to_terrain(c["elevation"], "coastal_beach"))  # agreement
            self.assertEqual(c["recipe"], TERRAIN_TO_RECIPE.get(c["terrain"]))
        self.assertEqual(pkt["unmapped_terrains"],
                         sorted({c["terrain"] for c in pkt["cells"] if c["recipe"] is None}))

    def test_legacy_split_is_detectable(self):
        # Classifying a side matrix without touching the nucleus (load_region_contract
        # pattern) leaves the field at 0.0 while terrain says otherwise.
        field, _, adapter = make_wired_field(5, 3, 4, "coastal_beach")
        adapter._grid[1][4] = value_to_terrain(1.0, "coastal_beach")
        cell = emit_grid_facts(field, adapter)["cells"][1 * 5 + 4]
        self.assertNotEqual(cell["terrain"], value_to_terrain(cell["elevation"], "coastal_beach"))

    def test_bad_input_refused_not_clamped(self):
        for bad in ([[0.1, 1.2]], [[0.1], [0.1, 0.2]], [], [[float("nan")]], [[True]]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                field_from_elevation_grid(bad, "coastal_beach")
        with self.assertRaises(ValueError):
            field_from_elevation_grid([[0.1]], "no_such_profile")

    def test_every_mapped_recipe_exists_in_trixel_registry(self):
        if not TRIXEL_RECIPES.is_dir():
            self.skipTest("sibling trixel3.2d not present")
        registry = {p.stem for p in TRIXEL_RECIPES.glob("*.json")}
        self.assertEqual(set(TERRAIN_TO_RECIPE.values()) - registry, set())

    def test_existing_emitter_smoke_still_passes(self):
        out = subprocess.run([sys.executable, "-m", "tier2.worldfield.grid_facts_emitter"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertIn("grid_facts_emitter: TRUE", out)


if __name__ == "__main__":
    unittest.main()
