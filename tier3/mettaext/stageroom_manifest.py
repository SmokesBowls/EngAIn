#!/usr/bin/env python3
"""
Mettaext Stageroom Done Manifest

Writes tier3/mettaext/stageroom/mettaext_done_manifest.json.

Authority:
- Evidence only.
- Consumers pull from stageroom.
- Mettaext does not dispatch.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def rel_to_stageroom(path: Path, stageroom_root: Path) -> str:
    return str(path.resolve().relative_to(stageroom_root.resolve()))


def collect_files(root: Path, pattern: str, stageroom_root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        rel_to_stageroom(path, stageroom_root)
        for path in root.rglob(pattern)
        if path.is_file()
    )


def build_manifest(source_text_id: str, stageroom_root: Path) -> dict[str, Any]:
    chapterroom_root = stageroom_root / "output" / "chapterroom"
    passroom_root = stageroom_root / "output" / "passroom"

    chapterroom_artifacts: list[str] = []
    chapterroom_artifacts += collect_files(chapterroom_root, "out_passA_*.json", stageroom_root)
    chapterroom_artifacts += collect_files(chapterroom_root, "out_passB_*.json", stageroom_root)
    chapterroom_artifacts += collect_files(chapterroom_root / "scene_packets", "scene_packets_index.json", stageroom_root)
    chapterroom_artifacts += collect_files(chapterroom_root / "scene_packets", "scene.*.txt", stageroom_root)

    passroom_artifacts: list[str] = []
    passroom_artifacts += collect_files(passroom_root, "out_pass1_*.txt", stageroom_root)
    passroom_artifacts += collect_files(passroom_root, "out_pass2_*.metta", stageroom_root)
    passroom_artifacts += collect_files(passroom_root, "zonj_*.json", stageroom_root)
    passroom_artifacts += collect_files(passroom_root, "*.zon", stageroom_root)
    passroom_artifacts += collect_files(passroom_root, "*.zonj.json", stageroom_root)
    passroom_artifacts += collect_files(passroom_root, "scene.*.json", stageroom_root)
    passroom_artifacts += collect_files(passroom_root, "scene_index.json", stageroom_root)

    game_scene_candidates = collect_files(passroom_root, "scene.*.json", stageroom_root)

    return {
        "contract": "mettaext.stageroom_run_manifest.v1",
        "source": "mettaext",
        "authority": "structured_witness",
        "run_state": "METTAEXT_DONE",
        "source_text_id": source_text_id,
        "stageroom_root": "tier3/mettaext/stageroom",
        "artifacts": {
            "chapterroom": chapterroom_artifacts,
            "passroom": passroom_artifacts,
            "game_scene_candidates": game_scene_candidates,
        },
        "authority_note": "Evidence only. Consumers pull from stageroom. Mettaext does not dispatch.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write Mettaext stageroom done manifest.")
    parser.add_argument("--source-text-id", required=True)
    parser.add_argument("--stageroom-root", default="tier3/mettaext/stageroom")
    parser.add_argument("--output", default="tier3/mettaext/stageroom/mettaext_done_manifest.json")
    args = parser.parse_args()

    stageroom_root = Path(args.stageroom_root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(args.source_text_id, stageroom_root)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("METTAEXT_DONE_MANIFEST_WRITTEN=TRUE")
    print(f"MANIFEST={output_path}")
    print(f"SOURCE_TEXT_ID={args.source_text_id}")
    print(f"CHAPTERROOM_ARTIFACTS={len(manifest['artifacts']['chapterroom'])}")
    print(f"PASSROOM_ARTIFACTS={len(manifest['artifacts']['passroom'])}")
    print(f"GAME_SCENE_CANDIDATES={len(manifest['artifacts']['game_scene_candidates'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
