"""Technical validator for Cartographer terrain metric grants against their grid facts."""

from __future__ import annotations

from math import isclose
from typing import Any

from tier2.cartographer.layoutroom.terrain_metric_solver import GRANT_CONTRACT, VERTICAL_RULE, _hash


def validate_terrain_metric_grant(grant: dict[str, Any], grid_facts: dict[str, Any]) -> dict[str, Any]:
    v: list[str] = []
    basis = grant.get("measurement_basis") or {}
    grid = grant.get("grid") or {}
    checks = {
        "contract": grant.get("contract") == GRANT_CONTRACT,
        "granted_by_cartographer": grant.get("granted_by") == "cartographer",
        "unit_meter": grant.get("unit") == "meter",
        "vertical_rule": grant.get("vertical_measurement_rule") == VERTICAL_RULE,
        "basis_is_evidence": basis.get("basis_status") == "evidence",
        "grid_bound": grid.get("grid_facts_sha256") == _hash(grid_facts)
        and (grid.get("width"), grid.get("height")) == (grid_facts.get("width"), grid_facts.get("height")),
        "cell_width_from_extent": isinstance(grid_facts.get("width"), int) and grid_facts["width"] > 0
        and isclose(grant.get("cell_width", 0.0), basis.get("physical_width_m", -1) / grid_facts["width"]),
        "cell_depth_from_extent": isinstance(grid_facts.get("height"), int) and grid_facts["height"] > 0
        and isclose(grant.get("cell_depth", 0.0), basis.get("physical_depth_m", -1) / grid_facts["height"]),
        "layers_from_vertical_extent": grant.get("max_height_layers") == basis.get("vertical_extent_m"),
        "source_artifact_id": isinstance(grant.get("source_artifact_id"), str)
        and grant["source_artifact_id"].startswith("terrain_metric."),
    }
    v = [name for name, ok in checks.items() if not ok]
    return {"validator": "cartographer.terrain_metric_validator.v1", "passed": not v,
            "checks_run": len(checks), "violations": v}
