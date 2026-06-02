#!/usr/bin/env python3
"""
Trixelmap Build Orchestrator

Sidecar pipeline for EngAIn spatial/map production.

Reads:
  - relationship-only spatial authority YAML
  - ZONJ JSON
  - scene JSON
  - vault markdown

Writes:
  - spatial_authority.json
  - resolved_layout.json
  - terrain_field.json
  - trixelcomposer_recipe.json
  - trixelcomposer_atlas_plan.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from spatial_authority_extractor import (
    extract_from_scene_json,
    extract_from_vault_md,
    extract_from_zonj,
)
from spatial_layout_solver import solve_layout
from terrain_field_builder import build_terrain_field
from trixel_recipe_writer import write_recipe_and_atlas


YAML_EXTENSIONS = {".yaml", ".yml"}
JSON_EXTENSIONS = {".json"}


def normalize_spatial_authority_yaml(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts relationship-only YAML into the internal trixelmap authority shape.

    Input shape:
      world_constraints:
        regions:
          gruulith_mountain:
            preferred_quadrant: northwest
            terrain_class: frozen_volcanic_peak

      spatial_graph:
        edges:
          - {from: a, to: b, relation: borders_east}

    Output shape expected by spatial_layout_solver.py:
      {
        "version": "1.0",
        "source": "spatial_authority_yaml",
        "regions": {
          "gruulith_mountain": {
            "id": "gruulith_mountain",
            "quadrant_hint": "northwest",
            "terrain_class": "frozen_volcanic_peak"
          }
        },
        "edges": [...]
      }
    """
    world_constraints = data.get("world_constraints", {})
    source_regions = world_constraints.get("regions", {})
    source_edges = data.get("spatial_graph", {}).get("edges", [])

    regions: Dict[str, Dict[str, Any]] = {}

    for region_id, region_data in source_regions.items():
        if not isinstance(region_data, dict):
            region_data = {}

        quadrant_hint = (
            region_data.get("quadrant_hint")
            or region_data.get("preferred_quadrant")
            or region_data.get("quadrant")
            or region_data.get("placement")
            or "center"
        )

        regions[region_id] = {
            "id": region_id,
            "quadrant_hint": quadrant_hint,
            "terrain_class": region_data.get("terrain_class", "default"),
            "type": region_data.get("type"),
            "size_hint": region_data.get("size_hint", "medium"),
            "landmarks": region_data.get("landmarks", region_data.get("contains", [])),
            "raw": region_data,
        }

    edges = []
    for edge in source_edges:
        if not isinstance(edge, dict):
            continue

        from_id = edge.get("from")
        to_id = edge.get("to")
        relation = edge.get("relation", "adjacent")

        if not from_id or not to_id:
            continue

        edges.append(
            {
                "from": from_id,
                "to": to_id,
                "relation": relation,
                "weight": edge.get("weight", 1.0),
            }
        )

    return {
        "version": str(data.get("version", "1.0")),
        "source": "spatial_authority_yaml",
        "regions": regions,
        "edges": edges,
        "validation_predicates": data.get("validation_predicates", []),
    }


def load_authority(input_path: Path) -> Dict[str, Any]:
    text = input_path.read_text(encoding="utf-8")
    suffix = input_path.suffix.lower()

    if suffix in YAML_EXTENSIONS:
        data = yaml.safe_load(text) or {}

        if "world_constraints" in data or "spatial_authority" in data:
            if "spatial_authority" in data and "world_constraints" not in data:
                data = {
                    "world_constraints": {
                        "regions": data.get("spatial_authority", {}).get("regions", {})
                    },
                    "spatial_graph": data.get("spatial_authority", {}).get("spatial_graph", {}),
                    "validation_predicates": data.get("spatial_authority", {}).get(
                        "validation_predicates", []
                    ),
                }

            return normalize_spatial_authority_yaml(data)

        raise ValueError(
            f"YAML file does not contain world_constraints or spatial_authority: {input_path}"
        )

    if suffix in JSON_EXTENSIONS:
        data = json.loads(text)

        if "world_constraints" in data or "spatial_authority" in data:
            return normalize_spatial_authority_yaml(data)

        if "=segments" in data:
            return extract_from_zonj(data)

        return extract_from_scene_json(data)

    return extract_from_vault_md(text)


def run_pipeline(input_path: str, output_dir: str) -> bool:
    inp = Path(input_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not inp.exists():
        raise FileNotFoundError(f"Input file does not exist: {inp}")

    print(f"[trixelmap] Extracting spatial authority from: {inp}")
    authority = load_authority(inp)

    authority_path = out / "spatial_authority.json"
    authority_path.write_text(json.dumps(authority, indent=2), encoding="utf-8")

    region_count = len(authority.get("regions", {}))
    edge_count = len(authority.get("edges", []))
    print(f"[trixelmap] Authority regions: {region_count}")
    print(f"[trixelmap] Authority edges: {edge_count}")

    if region_count == 0:
        raise ValueError(
            "Spatial authority extraction produced 0 regions. Refusing to continue."
        )

    print("[trixelmap] Solving spatial layout...")
    layout = solve_layout(authority)
    (out / "resolved_layout.json").write_text(
        json.dumps(layout, indent=2), encoding="utf-8"
    )

    print("[trixelmap] Building terrain field...")
    terrain = build_terrain_field(layout)
    (out / "terrain_field.json").write_text(
        json.dumps(terrain, indent=2), encoding="utf-8"
    )

    print("[trixelmap] Generating Trixelcomposer recipe & atlas plan...")
    contracts = write_recipe_and_atlas(terrain, layout)
    (out / "trixelcomposer_recipe.json").write_text(
        json.dumps(contracts["recipe"], indent=2), encoding="utf-8"
    )
    (out / "trixelcomposer_atlas_plan.json").write_text(
        json.dumps(contracts["atlas_plan"], indent=2), encoding="utf-8"
    )

    print(f"[trixelmap] ✅ Pipeline complete. Outputs in: {out}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Trixelmap: Narrative/Authority → Spatial Intelligence → Trixelcomposer Contracts"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to spatial authority YAML, ZONJ JSON, scene JSON, or vault markdown",
    )
    parser.add_argument(
        "--output-dir",
        default="trixelmap/out",
        help="Output directory",
    )

    args = parser.parse_args()

    try:
        run_pipeline(args.input, args.output_dir)
        return 0
    except Exception as exc:
        print(f"[trixelmap] FATAL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
