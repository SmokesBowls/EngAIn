"""Operation E: provider outputs -> bound request; C3 asymmetric coordinate check via real Trixel."""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from tier1.engainos.bridgeroom.trixel32d_request_assembler import (
    ASSEMBLED, REJECTED, assemble_bound_surface_request,
)
from tier1.engainos.bridgeroom.trixel32d_request_dispatch import dispatch_request_drop
from tier1.engainos.gates.gate_trixel32d_handshake import validate_trixel32d_surface_request
from tier2.cartographer.layoutroom.terrain_metric_solver import solve_terrain_metrics
from tier2.worldfield.grid_facts_emitter import emit_grid_facts
from tier2.worldfield.trixel_world_adapter import field_from_elevation_grid

TRIXEL_TOOL = Path(__file__).resolve().parents[3].parent / "trixel3.2d" / "tools" / "consume_trixel32d_request_drop.py"

SCENE = "scene.isolated_test.terrain"
# Asymmetric 3x2: the only 0.85 cell is the east end of row 0; 0.45 only at (1,1).
ELEV = [[0.50, 0.50, 0.85],
        [0.50, 0.45, 0.50]]
TEST_BASIS = {  # isolated declared test policy, not production evidence
    "basis_id": "TEST_ONLY_isolated_terrain_basis", "source": "test_trixel32d_bound_assembly.py",
    "scene_id": SCENE, "basis_status": "evidence",
    "physical_width_m": 6.0, "physical_depth_m": 2.0, "vertical_extent_m": 4,
}
POLICY = {
    "topology_policy": "HEIGHT_FIELD_CELL_EXTRUSION", "ordering": "ROW_MAJOR",
    "appearance_policy": "RECIPE_REFERENCE",
    "gap_fill": {"enabled": True, "mode": "PER_CELL_EXTRUSION", "adjacency_policy": "ALL_FACES_INDEPENDENT",
                 "resolved_color": [0.35, 0.35, 0.35, 1.0], "thickness_local_units": 0.025},
    "recipe_base_colors": {"default.generic": [0.29, 0.55, 0.25, 1.0],
                           "mountain.rocky_ridge": [0.48, 0.48, 0.48, 1.0]},
}


def contributions(elev=ELEV, basis=TEST_BASIS):
    field, _, adapter = field_from_elevation_grid(elev, "coastal_beach")
    grid = emit_grid_facts(field, adapter)
    grant = solve_terrain_metrics(grid, basis)["grant"]
    provenance = {"source_scene_id": basis["scene_id"], "topology_artifact_id": "topology.isolated_test",
                  "metric_layout_artifact_id": grant["source_artifact_id"]}
    return grid, grant, provenance, copy.deepcopy(POLICY)


def test_provider_outputs_assemble_and_pass_gate():
    status, request, reasons = assemble_bound_surface_request(*contributions())
    assert status == ASSEMBLED, reasons
    assert validate_trixel32d_surface_request(request) == []
    assert request["planar_config"]["cell_width"] == 2.0 and request["planar_config"]["cell_depth"] == 1.0
    assert request["vertical_metric"]["max_height_layers"] == 4.0
    assert request["identity"]["source_scene_id"] == SCENE
    # deterministic
    assert assemble_bound_surface_request(*contributions())[1]["identity"]["request_id"] == request["identity"]["request_id"]


@pytest.mark.parametrize("mutate,needle", [
    (lambda g, m, p, c: p.update(source_scene_id="scene.other"), "measures scene"),
    (lambda g, m, p, c: g["cells"][0].update(elevation=0.9), "different grid facts"),
    (lambda g, m, p, c: m.update(cell_width=0.1), "altered after Cartographer"),
    (lambda g, m, p, c: p.update(metric_layout_artifact_id="metric_layout.proof.001"), "does not name this metric grant"),
    (lambda g, m, p, c: m.pop("contract"), "metric_grant.contract"),
])
def test_mismatched_chain_rejected(mutate, needle):
    g, m, p, c = contributions()
    mutate(g, m, p, c)
    status, request, reasons = assemble_bound_surface_request(g, m, p, c)
    assert (status, request) == (REJECTED, None)
    assert any(needle in r for r in reasons), reasons


def test_missing_metrics_appearance_and_recipe_rejected():
    g, m, p, c = contributions()
    assert assemble_bound_surface_request(g, {}, p, c)[0] == REJECTED
    c.pop("recipe_base_colors")
    assert assemble_bound_surface_request(g, m, p, c)[0] == REJECTED
    g, m, p, c = contributions(elev=[[0.0, 0.5, 0.85], [0.5, 0.45, 0.5]])  # 0.0 -> deep_water/ocean (mapped)
    c["recipe_base_colors"].pop("default.generic")
    assert assemble_bound_surface_request(g, m, p, c)[0] == REJECTED


def test_proof_grant_is_not_a_production_grant():
    from tier1.engainos.tests.test_trixel32d_request_assembler import METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY, build_fixture_grid_facts
    status, _, reasons = assemble_bound_surface_request(build_fixture_grid_facts(), METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY)
    assert status == REJECTED and any("contract" in r for r in reasons)


@pytest.mark.skipif(not TRIXEL_TOOL.exists(), reason="sibling trixel3.2d not present")
def test_asymmetric_landmarks_through_trixel_are_not_mirrored():
    status, request, reasons = assemble_bound_surface_request(*contributions())
    assert status == ASSEMBLED, reasons
    body = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        assert dispatch_request_drop(tmp / "req", body, generated_by="engainos").dispatched
        run = subprocess.run([sys.executable, str(TRIXEL_TOOL), str(tmp / "req"), str(tmp / "resp"),
                              request["identity"]["request_id"]], capture_output=True, text=True)
        assert run.returncode == 0, run.stdout
        built = json.loads((tmp / "resp" / "TRIXEL32D_SURFACE_BUILT_PAYLOAD_V1.json").read_text())
    pos, idx = built["geometry"]["positions"], built["geometry"]["indices"]
    tops = {}
    for prim in built["primitive_provenance"]:
        if prim["face"] != "top":
            continue
        vs = {i for t in range(prim["primitive_start"], prim["primitive_start"] + prim["primitive_count"])
              for i in idx[3 * t:3 * t + 3]}
        tops[prim["cell_key"]] = [sum(pos[i][k] for i in vs) / len(vs) for k in range(3)]
    cw, cd, layers, cx, cy = 2.0, 1.0, 4, 1.0, 0.5
    for y, row in enumerate(ELEV):
        for x, e in enumerate(row):
            # right=+X, forward=-Z, up=+Y (DOCTRINE_ORIENTATION); one layer = one meter
            assert tops[f"{x},{y}"] == pytest.approx([(x - cx) * cw, round(e * layers), -(y - cy) * cd])
    # East landmark is at +X and highest; the second row lies forward (-Z): no mirror, no rotation.
    assert tops["2,0"][0] > tops["0,0"][0] and tops["2,0"][1] == max(t[1] for t in tops.values())
    assert tops["0,1"][2] < tops["0,0"][2]


def test_provisional_grant_needs_explicit_allowance():
    field, _, adapter = field_from_elevation_grid(ELEV, "coastal_beach")
    grid = emit_grid_facts(field, adapter)
    basis = dict(TEST_BASIS, basis_status="provisional")
    grant = solve_terrain_metrics(grid, basis, allow_provisional=True)["grant"]
    prov = {"source_scene_id": SCENE, "topology_artifact_id": "t", "metric_layout_artifact_id": grant["source_artifact_id"]}
    status, _, reasons = assemble_bound_surface_request(grid, grant, prov, copy.deepcopy(POLICY))
    assert status == REJECTED and any("not evidence-backed" in r for r in reasons)
    status, request, reasons = assemble_bound_surface_request(grid, grant, prov, copy.deepcopy(POLICY), allow_provisional=True)
    assert status == ASSEMBLED, reasons
    # A grant relabelled "evidence" after the fact no longer matches its content address.
    forged = dict(grant, metric_status="evidence")
    assert assemble_bound_surface_request(grid, forged, prov, copy.deepcopy(POLICY), allow_provisional=True)[0] == REJECTED
