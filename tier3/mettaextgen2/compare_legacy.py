#!/usr/bin/env python3
"""Compare legacy Mettaext (Pass 1–5) entity evidence with Gen2 for one scene.

Read-only. Legacy evidence is the `=entities_observed` list in
stageroom/output/passroom/<scene_id>/<scene_id>.zonj.json, the exact field the
3D Dragon's door v1 returns. Gen2 evidence is a fresh parse_artifact.v2.

Usage (repo root, PYTHONPATH=.):
  python3 -m tier3.mettaextgen2.compare_legacy \\
      --chapter-id chapter.book009.048_the_ledger_born \\
      --scene-id scene.book009.048_the_ledger_born.scene005
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence

from .orchestrator import DEFAULT_CHAPTERROOM_ROOT, run_scene

DEFAULT_PASSROOM_ROOT = DEFAULT_CHAPTERROOM_ROOT.parent / "passroom"


def legacy_entities(passroom_root: Path, scene_id: str) -> List[Dict]:
    data = json.loads((passroom_root / scene_id / f"{scene_id}.zonj.json").read_text(encoding="utf-8"))
    return [{"name": e.get("name"), "presence": e.get("presence"), "spawnable": e.get("spawnable"),
             "classification": e.get("classification")} for e in data.get("=entities_observed") or []]


def compare(chapterroom_root: Path, passroom_root: Path, chapter_id: str, scene_id: str) -> Dict:
    artifact = run_scene(chapterroom_root, chapter_id, scene_id)
    gen2 = {e["surface"]: e for e in artifact["declared_entities"]}
    gen2_locations = {l["surface"] for l in artifact["declared_locations"]}
    rows = []
    for legacy in legacy_entities(passroom_root, scene_id):
        name = legacy["name"]
        match = gen2.get(name) or next((e for s, e in gen2.items() if name in s.split()), None)
        if match is None and any(name in loc.split() for loc in gen2_locations):
            verdict = "absorbed into a declared location"
        elif match is None:
            verdict = "not declared by Gen2"
        else:
            verdict = f"{match['local_ref']} {match['surface']!r} {match['status']} presence={match['presence']}"
        rows.append({"legacy_name": name, "legacy_presence": legacy["presence"], "gen2": verdict})
    return {"scene_id": scene_id, "rows": rows,
            "gen2_entities": [(e["local_ref"], e["surface"], e["status"], e["presence"]) for e in artifact["declared_entities"]],
            "gen2_locations": sorted(gen2_locations)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chapter-id", required=True)
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--chapterroom-root", type=Path, default=DEFAULT_CHAPTERROOM_ROOT)
    parser.add_argument("--passroom-root", type=Path, default=DEFAULT_PASSROOM_ROOT)
    args = parser.parse_args(argv)
    result = compare(args.chapterroom_root, args.passroom_root, args.chapter_id, args.scene_id)
    width = max(len(r["legacy_name"]) for r in result["rows"]) if result["rows"] else 10
    print(f"{'legacy entity':<{width}}  legacy presence  ->  Gen2")
    for r in result["rows"]:
        print(f"{r['legacy_name']:<{width}}  {str(r['legacy_presence']):<15}  ->  {r['gen2']}")
    print("\nGen2 declared entities:")
    for ref, surface, status, presence in result["gen2_entities"]:
        print(f"  {ref}  {status:<9}  {presence:<10}  {surface}")
    print("Gen2 declared locations:", ", ".join(result["gen2_locations"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
