"""source_loader (GEN2_MODULES.md §2.1).

Input:   a Chapterroom scene packet reference (chapterroom output root,
         chapter_id, chapterroom scene_id).
Output:  SourceDocument for the raw chapter (sha256 pinned at read time) plus
         SceneInput carrying the inherited identity.
Allowed: reading and hashing the raw file; reading Chapterroom outputs.
Forbidden: altering raw text, repairing typos, minting or deriving scene ids.
Failure: any missing or inconsistent input aborts the run (SourceLoadError).
         Nothing is extracted from a packet that no longer matches its source.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from ..lib.annotations import SceneInput
from ..lib.source import SourceDocument

NAME = "source_loader"
VERSION = "0.1.0"


class SourceLoadError(RuntimeError):
    pass


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceLoadError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SourceLoadError(f"{path} is not a JSON object")
    return data


def _find_passA(chapterroom_root: Path, chapter_id: str) -> dict:
    matches = []
    for path in sorted(chapterroom_root.glob("out_passA_*.json")):
        data = _read_json(path)
        if data.get("chapter_id") == chapter_id:
            matches.append(data)
    if len(matches) != 1:
        raise SourceLoadError(f"expected exactly one Pass A manifest for {chapter_id}, found {len(matches)}")
    return matches[0]


def _packet_body(packet_path: Path) -> str:
    text = packet_path.read_text(encoding="utf-8")
    marker = "\n---\n"
    if marker not in text:
        raise SourceLoadError(f"{packet_path} has no header terminator")
    return text.split(marker, 1)[1]


def load_scene_source(chapterroom_root: Path, chapter_id: str, scene_id: str) -> Tuple[SourceDocument, SceneInput]:
    index_path = chapterroom_root / "scene_packets" / chapter_id / "scene_packets_index.json"
    index = _read_json(index_path)
    entries = [p for p in index.get("packets", []) if p.get("scene_id") == scene_id]
    if len(entries) != 1:
        raise SourceLoadError(f"{scene_id} not found exactly once in {index_path}")
    entry = entries[0]

    pass_b = _read_json(chapterroom_root / f"out_passB_{chapter_id}.json")
    scenes = [s for s in pass_b.get("scenes", []) if s.get("scene_id") == scene_id]
    if len(scenes) != 1:
        raise SourceLoadError(f"{scene_id} not found exactly once in Pass B output")
    first, last = scenes[0]["boundary_start_line"], scenes[0]["boundary_end_line"]

    source_path = Path(_find_passA(chapterroom_root, chapter_id)["source_file"])
    if not source_path.is_file():
        raise SourceLoadError(f"raw source missing: {source_path}")
    doc = SourceDocument.from_file(source_path, first, last)

    packet_path = Path(entry["packet_path"])
    region_text = doc.text[doc.region_start:doc.region_end]
    if _packet_body(packet_path).strip() != region_text.strip():
        raise SourceLoadError(
            f"packet {packet_path.name} no longer matches {source_path.name} lines {first}-{last}; "
            "re-run Chapterroom before extracting"
        )

    scene = SceneInput(
        chapter_id=chapter_id,
        chapterroom_scene_id=scene_id,
        source_scene_label=entry.get("source_scene_label"),
        source_scene_title=entry.get("source_scene_title"),
        boundary_method=entry["boundary_method"],
        authored_scene_boundaries_proven=bool(entry["authored_scene_boundaries_proven"]),
        packet_path=str(packet_path),
    )
    return doc, scene
