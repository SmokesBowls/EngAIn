"""Operation C: unit conversion (C1) and terrain metric grant (C2)."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tier2.topologist.tests.test_spatial_handoff import fixture_artifact, submit_and_gate, GUARD, GATE, KING  # noqa: E402
from tier2.topologist.artifactroom.occupancy_evidence import apply_occupancy_evidence  # noqa: E402
from tier2.cartographer.layoutroom.topology_metric_layout_solver import build_metric_layout  # noqa: E402
from tier2.cartographer.reckoningroom.metric_layout_validator import validate_metric_layout_artifact  # noqa: E402
from tier2.cartographer.gates.gate_propose_metric_layout import evaluate_metric_layout_for_proposal  # noqa: E402
from tier2.cartographer.layoutroom.terrain_metric_solver import solve_terrain_metrics, BLOCKED, GRANTED  # noqa: E402
from tier2.cartographer.reckoningroom.terrain_metric_validator import validate_terrain_metric_grant  # noqa: E402

TEST_BASIS = {"basis_id": "TEST_ONLY_basis", "source": "unit test fixture", "meters_per_pgt": 0.25}


def packet(records=None):
    art = fixture_artifact()
    if records:
        art = apply_occupancy_evidence(art, records)
    return submit_and_gate(art)[1]["accepted_spatial_truth_packet"]


def positions(layout):
    return {e["entity_id"]: tuple(e["position"].values()) for e in layout.to_dict()["entities"]}


PROVISIONAL_GUARD = {GUARD: {"semantic_type": "person", "semantic_evidence": "The guard stood",
                             "occupancy_class": "human_standard", "occupancy_basis": "provisional",
                             "provisional_reason": "build not stated"}}


class EntityLayoutUnits(unittest.TestCase):
    def test_recovery_fixture_unchanged_and_provisional(self):
        pkt = packet()
        layout = build_metric_layout(pkt).to_dict()
        report = validate_metric_layout_artifact(layout, pkt)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["checks_run"], 24)
        self.assertEqual(positions(build_metric_layout(pkt)),
                         {GUARD: (0.0, 0.0, 0.0), KING: (1.0, 0.0, 0.0), GATE: (0.0, 0.0, -2.0)})
        self.assertEqual((layout["metric_status"], layout["measurement_basis"]), ("provisional", None))
        self.assertEqual(evaluate_metric_layout_for_proposal(layout, report)["decision"], "PROPOSED")

    def test_pgt_never_read_as_meters_without_basis(self):
        self.assertEqual(positions(build_metric_layout(packet(PROVISIONAL_GUARD))),
                         positions(build_metric_layout(packet())))

    def test_declared_basis_converts_and_stays_provisional(self):
        layout = build_metric_layout(packet(PROVISIONAL_GUARD), TEST_BASIS)
        d = layout.to_dict()
        by_id = {e["entity_id"]: e for e in d["entities"]}
        self.assertEqual(by_id[GUARD]["extent_source"], "pgt_provisional")
        self.assertEqual(by_id[GATE]["extent_source"], "fallback")
        # guard half-depth = 3 PGT * 0.25 m / 2; gate fallback 0.5; clearance 1.0
        self.assertAlmostEqual(positions(layout)[GATE][2], -(0.375 + 0.5 + 1.0))
        self.assertEqual(d["metric_status"], "provisional")
        self.assertEqual(d["measurement_basis"]["basis_id"], "TEST_ONLY_basis")
        self.assertTrue(validate_metric_layout_artifact(d, packet(PROVISIONAL_GUARD))["passed"])

    def test_bad_basis_refused(self):
        for bad in ({"basis_id": "x", "source": "y"}, {"basis_id": "x", "source": "", "meters_per_pgt": 1},
                    {"basis_id": "x", "source": "y", "meters_per_pgt": 0}, {"pgt_unit_px": 10}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                build_metric_layout(packet(), bad)


GRID = {"packet_type": "worldfield_grid_facts", "version": "worldfield_grid_facts.v1",
        "width": 4, "height": 2, "field_coverage": "DENSE", "profile": "test", "cells": []}
BASIS = {"basis_id": "TEST_ONLY_terrain", "source": "unit test fixture", "scene_id": "scene.test",
         "basis_status": "evidence", "physical_width_m": 8.0, "physical_depth_m": 6.0,
         "vertical_extent_m": 5}


class TerrainMetricGrant(unittest.TestCase):
    def test_non_square_grant_from_declared_extent(self):
        out = solve_terrain_metrics(GRID, BASIS)
        self.assertEqual(out["status"], GRANTED)
        g = out["grant"]
        self.assertEqual((g["cell_width"], g["cell_depth"], g["max_height_layers"]), (2.0, 3.0, 5))
        self.assertEqual((g["granted_by"], g["unit"]), ("cartographer", "meter"))
        self.assertEqual(g["vertical_measurement_rule"], "ELEVATION_TIMES_MAX_HEIGHT_LAYERS")
        self.assertTrue(validate_terrain_metric_grant(g, GRID)["passed"])
        other = dict(GRID, width=8)
        self.assertIn("grid_bound", validate_terrain_metric_grant(g, other)["violations"])

    def test_blocked_receipts_name_what_is_missing(self):
        self.assertEqual(solve_terrain_metrics(GRID, None)["status"], BLOCKED)
        cases = {
            "vertical_extent_m": dict(BASIS, vertical_extent_m=None),
            "whole meters": dict(BASIS, vertical_extent_m=2.5),
            "physical_width_m": {k: v for k, v in BASIS.items() if k != "physical_width_m"},
            "basis_status": dict(BASIS, basis_status="provisional"),
            "scene_id": dict(BASIS, scene_id=""),
        }
        for needle, basis in cases.items():
            out = solve_terrain_metrics(GRID, basis)
            self.assertEqual(out["status"], BLOCKED)
            self.assertTrue(any(needle in m for m in out["missing"]), (needle, out))
            self.assertNotIn("grant", out)

    def test_extent_not_inferred_from_cell_count(self):
        out = solve_terrain_metrics(dict(GRID, width=40), BASIS)
        self.assertEqual(out["grant"]["cell_width"], 0.2)  # same 8 m field, finer grid

    def test_tampered_grant_fails_validation(self):
        g = copy.deepcopy(solve_terrain_metrics(GRID, BASIS)["grant"])
        g["cell_width"] = 0.1
        self.assertIn("cell_width_from_extent", validate_terrain_metric_grant(g, GRID)["violations"])


if __name__ == "__main__":
    unittest.main()
