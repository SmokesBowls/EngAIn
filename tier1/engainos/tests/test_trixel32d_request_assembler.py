# First-proof fixture for the trixel32d vertical slice:
# a real 3×2 WorldField patch driven through the full EngAIn-side chain:
#   WorldField sculpt → worldfield_grid_facts.v1 → EngAInOS assembler →
#   trixel32d validator gate.
# Six cells, three distinct elevations, two recipe identities, one authorized
# metric, one declared topology policy. Collision/placement intentionally
# absent (v2 contract fields, downstream of this slice step).

import copy

from tier1.engainos.bridgeroom.trixel32d_request_assembler import (
    ASSEMBLED,
    REJECTED,
    assemble_surface_request,
)
from tier2.worldfield.grid_facts_emitter import emit_grid_facts
from tier2.worldfield.trixel_world_adapter import make_wired_field

# 3×2 patch: elevations chosen so coastal_beach thresholds yield exactly two
# recipe identities — grass→default.generic (0.42–0.62), rock→mountain.rocky_ridge
# (0.78–0.90). Three distinct elevations: 0.45, 0.50, 0.85.
FIXTURE_ELEVATIONS = {
    (0, 0): 0.50, (1, 0): 0.45, (2, 0): 0.85,
    (0, 1): 0.85, (1, 1): 0.50, (2, 1): 0.45,
}

METRIC_GRANT = {
    "granted_by": "cartographer",
    "unit": "meter",
    "cell_width": 0.1,
    "cell_depth": 0.1,
    "vertical_measurement_rule": "ELEVATION_TIMES_MAX_HEIGHT_LAYERS",
    "max_height_layers": 6,
    "source_artifact_id": "metric_layout.proof.001",
}

PROVENANCE = {
    "source_scene_id": "scene.proof.001",
    "topology_artifact_id": "topology.proof.001",
    "metric_layout_artifact_id": "metric_layout.proof.001",
}

CONSTRUCTION_POLICY = {
    "topology_policy": "HEIGHT_FIELD_CELL_EXTRUSION",
    "ordering": "ROW_MAJOR",
    "appearance_policy": "RECIPE_REFERENCE",
    "gap_fill": {
        "enabled": True,
        "mode": "PER_CELL_EXTRUSION",
        "adjacency_policy": "ALL_FACES_INDEPENDENT",
        "resolved_color": [0.35, 0.35, 0.35, 1.0],
        "thickness_local_units": 0.025,
    },
    "recipe_base_colors": {
        "default.generic": [0.29, 0.55, 0.25, 1.0],
        "mountain.rocky_ridge": [0.48, 0.48, 0.48, 1.0],
    },
}


def build_fixture_grid_facts():
    """Sculpt the 3×2 patch on a real WorldField and emit real grid facts."""
    field, bridge, adapter = make_wired_field(3, 2, profile_id="coastal_beach")
    for (x, y), elevation in FIXTURE_ELEVATIONS.items():
        chunk = field.get_or_create_chunk(x, y)
        lx, ly = field.get_local_coords(x, y)
        chunk.set(lx, ly, elevation)
    adapter.apply_dirty_chunks(bridge.get_dirty_data())
    return emit_grid_facts(field, adapter)


def test_first_proof_fixture_assembles():
    grid_facts = build_fixture_grid_facts()

    # WorldField-side acceptance gates
    assert grid_facts["width"] == 3 and grid_facts["height"] == 2
    assert len(grid_facts["cells"]) == 6
    assert grid_facts["fully_mapped"] is True
    assert {c["recipe"] for c in grid_facts["cells"]} == {
        "default.generic", "mountain.rocky_ridge",
    }
    assert len({c["elevation"] for c in grid_facts["cells"]}) == 3

    status, request, reasons = assemble_surface_request(
        grid_facts, METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY
    )
    assert status == ASSEMBLED, f"expected ASSEMBLED, got {status}: {reasons}"

    # Provenance survives the assembly unchanged
    identity = request["identity"]
    assert identity["source_scene_id"] == "scene.proof.001"
    assert identity["provenance"]["topology_artifact_id"] == "topology.proof.001"

    # Cartographer's authorized metric survives unchanged
    vm = request["vertical_metric"]
    assert vm["max_height_layers"] == 6.0
    assert vm["source_artifact_id"] == "metric_layout.proof.001"
    assert request["planar_config"]["cell_width"] == 0.1

    # Elevations pass through untouched, colors come only from the declared table
    for cell, req_cell in zip(grid_facts["cells"], request["pixel_field_data"]):
        assert req_cell["elevation"] == cell["elevation"]
        assert req_cell["base_color"] == CONSTRUCTION_POLICY["recipe_base_colors"][cell["recipe"]]


def test_request_id_is_deterministic():
    grid_facts = build_fixture_grid_facts()
    _, req_a, _ = assemble_surface_request(
        grid_facts, METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY
    )
    _, req_b, _ = assemble_surface_request(
        build_fixture_grid_facts(), METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY
    )
    assert req_a["identity"]["request_id"] == req_b["identity"]["request_id"]


def test_rejects_unmapped_recipe():
    grid_facts = build_fixture_grid_facts()
    grid_facts["cells"][2]["recipe"] = None
    grid_facts["cells"][2]["terrain"] = "pier"
    status, request, reasons = assemble_surface_request(
        grid_facts, METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY
    )
    assert status == REJECTED and request is None
    assert any("pier" in r and "never guessed" in r for r in reasons)


def test_rejects_row_major_violation():
    grid_facts = build_fixture_grid_facts()
    grid_facts["cells"][0], grid_facts["cells"][1] = (
        grid_facts["cells"][1], grid_facts["cells"][0],
    )
    status, _, reasons = assemble_surface_request(
        grid_facts, METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY
    )
    assert status == REJECTED
    assert any("row-major" in r for r in reasons)


def test_rejects_missing_metric_authority():
    grid_facts = build_fixture_grid_facts()
    grant = copy.deepcopy(METRIC_GRANT)
    del grant["max_height_layers"]
    grant["granted_by"] = "worldfield"  # wrong authority
    status, _, reasons = assemble_surface_request(
        grid_facts, grant, PROVENANCE, CONSTRUCTION_POLICY
    )
    assert status == REJECTED
    assert any("granted_by" in r for r in reasons)
    assert any("max_height_layers" in r for r in reasons)


def test_rejects_undeclared_recipe_color():
    grid_facts = build_fixture_grid_facts()
    policy = copy.deepcopy(CONSTRUCTION_POLICY)
    del policy["recipe_base_colors"]["mountain.rocky_ridge"]
    status, _, reasons = assemble_surface_request(
        grid_facts, METRIC_GRANT, PROVENANCE, policy
    )
    assert status == REJECTED
    assert any("never invents colors" in r for r in reasons)


if __name__ == "__main__":
    import json
    grid_facts = build_fixture_grid_facts()
    status, request, reasons = assemble_surface_request(
        grid_facts, METRIC_GRANT, PROVENANCE, CONSTRUCTION_POLICY
    )
    print("status:", status)
    if request:
        print("request_id:", request["identity"]["request_id"])
        print("cells:", len(request["pixel_field_data"]),
              "| recipes:", sorted({c["recipe"] for c in request["pixel_field_data"]}))
        print(json.dumps(request["pixel_field_data"][0], indent=2))
    else:
        print("reasons:", reasons)
