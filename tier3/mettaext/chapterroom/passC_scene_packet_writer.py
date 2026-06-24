#!/usr/bin/env python3
"""
Pass C — Scene Packet Writer

Reads a Pass B scene boundary proposal and writes one scene packet text file per scene.
These packets are inputs for passroom Pass 1–5.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict


def safe_filename(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_.-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "scene"


def packet_text(scene: Dict[str, Any], proposal: Dict[str, Any]) -> str:
    header = [
        f"@scene_id: {scene['scene_id']}",
        f"@chapter_id: {scene['chapter_id']}",
        f"@scene_index: {scene['scene_index']}",
        f"@boundary_method: {scene['boundary_method']}",
        f"@authority_state: {scene['authority_state']}",
        f"@authored_scene_boundaries_proven: {str(scene['authored_scene_boundaries_proven']).lower()}",
        f"@boundary_start_line: {scene['boundary_start_line']}",
        f"@boundary_end_line: {scene['boundary_end_line']}",
        "@contract: engain.scene_text_packet.v1",
        "---",
        "",
    ]
    return "\n".join(header) + scene["text"].strip() + "\n"


def write_packets(proposal: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    chapter_id = proposal["chapter_id"]
    packet_dir = output_dir / "scene_packets" / chapter_id
    packet_dir.mkdir(parents=True, exist_ok=True)

    packet_entries = []

    for scene in proposal.get("scenes", []):
        filename = f"{safe_filename(scene['scene_id'])}.txt"
        path = packet_dir / filename
        path.write_text(packet_text(scene, proposal), encoding="utf-8")

        packet_entries.append({
            "scene_id": scene["scene_id"],
            "chapter_id": chapter_id,
            "scene_index": scene["scene_index"],
            "packet_path": str(path),
            "boundary_method": scene["boundary_method"],
            "authority_state": scene["authority_state"],
            "authored_scene_boundaries_proven": scene["authored_scene_boundaries_proven"],
        })

    index = {
        "contract": "engain.scene_provider_packet.v1",
        "authority_state": proposal["authority_state"],
        "chapter_id": chapter_id,
        "scene_count": len(packet_entries),
        "boundary_method": proposal["boundary_method"],
        "authored_scene_boundaries_proven": proposal["authored_scene_boundaries_proven"],
        "packets": packet_entries,
    }

    index_path = packet_dir / "scene_packets_index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    index["index_path"] = str(index_path)
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Pass C: scene packet writer.")
    parser.add_argument("passB_proposal", help="Pass B JSON proposal.")
    parser.add_argument("--output-dir", default=".", help="Directory for scene packet output.")
    args = parser.parse_args()

    proposal_path = Path(args.passB_proposal).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    index = write_packets(proposal, output_dir)

    print("[PASS C] SCENE_PACKET_WRITER_COMPLETE = TRUE")
    print(f"[PASS C] CHAPTER_ID = {index['chapter_id']}")
    print(f"[PASS C] SCENE_COUNT = {index['scene_count']}")
    print(f"[PASS C] INDEX = {index['index_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
