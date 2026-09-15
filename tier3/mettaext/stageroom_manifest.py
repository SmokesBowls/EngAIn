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

    chapterroom_artifacts_set: set[str] = set()
    passroom_artifacts_set: set[str] = set()
    game_scene_candidates_set: set[str] = set()

    # 1. Collect Chapterroom JSON artifacts that explicitly state chapter_id == source_text_id
    if chapterroom_root.exists():
        for json_file in chapterroom_root.glob("*.json"):
            if not json_file.is_file():
                continue
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if data.get("chapter_id") == source_text_id:
                    chapterroom_artifacts_set.add(rel_to_stageroom(json_file, stageroom_root))
            except Exception:
                pass

    # 2. Resolve canonical scene packet index and exact scene_ids for source_text_id
    scene_ids: set[str] = set()
    canonical_packets_dir = chapterroom_root / "scene_packets" / source_text_id
    index_path = canonical_packets_dir / "scene_packets_index.json"

    if index_path.exists():
        chapterroom_artifacts_set.add(rel_to_stageroom(index_path, stageroom_root))
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            for pkt in index_data.get("packets", []):
                if isinstance(pkt, dict) and "scene_id" in pkt:
                    scene_ids.add(pkt["scene_id"])
        except Exception:
            pass

        for pkt_file in canonical_packets_dir.glob("*.txt"):
            if pkt_file.is_file():
                chapterroom_artifacts_set.add(rel_to_stageroom(pkt_file, stageroom_root))

    # Search any scene_packets_index.json under scene_packets whose JSON content proves chapter_id
    scene_packets_root = chapterroom_root / "scene_packets"
    if scene_packets_root.exists():
        for idx_file in scene_packets_root.rglob("scene_packets_index.json"):
            if idx_file.is_file() and idx_file != index_path:
                try:
                    idx_data = json.loads(idx_file.read_text(encoding="utf-8"))
                    if idx_data.get("chapter_id") == source_text_id:
                        chapterroom_artifacts_set.add(rel_to_stageroom(idx_file, stageroom_root))
                        for pkt in idx_data.get("packets", []):
                            if isinstance(pkt, dict) and "scene_id" in pkt:
                                scene_ids.add(pkt["scene_id"])
                        for pkt_file in idx_file.parent.glob("*.txt"):
                            if pkt_file.is_file():
                                chapterroom_artifacts_set.add(rel_to_stageroom(pkt_file, stageroom_root))
                except Exception:
                    pass

    # 3. Collect Passroom artifacts belonging to exact scene_ids
    if passroom_root.exists():
        for scene_id in scene_ids:
            scene_dir = passroom_root / scene_id
            if scene_dir.exists() and scene_dir.is_dir():
                for artifact_file in scene_dir.rglob("*"):
                    if artifact_file.is_file():
                        rel_path = rel_to_stageroom(artifact_file, stageroom_root)
                        passroom_artifacts_set.add(rel_path)
                        if artifact_file.name.endswith(".json") and "game_scenes" in artifact_file.parts:
                            game_scene_candidates_set.add(rel_path)

        # Content/JSON payload check for any passroom artifacts directly under passroom_root or unnested dirs
        for pfile in passroom_root.rglob("*.json"):
            if pfile.is_file() and rel_to_stageroom(pfile, stageroom_root) not in passroom_artifacts_set:
                try:
                    pdata = json.loads(pfile.read_text(encoding="utf-8"))
                    sid = pdata.get("scene_id") or pdata.get("id") or pdata.get("@id")
                    ch_id = pdata.get("chapter_id") or pdata.get("@chapter_id")
                    if (sid in scene_ids) or (ch_id == source_text_id):
                        rel_path = rel_to_stageroom(pfile, stageroom_root)
                        passroom_artifacts_set.add(rel_path)
                        if pfile.name.endswith(".json") and "game_scenes" in pfile.parts:
                            game_scene_candidates_set.add(rel_path)
                except Exception:
                    pass

    return {
        "contract": "mettaext.stageroom_run_manifest.v1",
        "source": "mettaext",
        "authority": "structured_witness",
        "run_state": "METTAEXT_DONE",
        "source_text_id": source_text_id,
        "stageroom_root": "tier3/mettaext/stageroom",
        "artifacts": {
            "chapterroom": sorted(chapterroom_artifacts_set),
            "passroom": sorted(passroom_artifacts_set),
            "game_scene_candidates": sorted(game_scene_candidates_set),
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
