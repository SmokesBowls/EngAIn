#!/usr/bin/env python3
"""
chapter_to_stage_packets.py

Purpose:
  Convert one compiled chapter packet into multiple runtime/display stage packets.

This script DOES:
  - Read one compiled chapter JSON packet.
  - Preserve chapter_id, entities, locations, metadata.
  - Split events into smaller stage packets.
  - Assign each stage packet:
      chapter_id
      stage_id
      scene_id
      source_packet_id
      stage_index
      stage_event_start
      stage_event_end
  - Write each stage as its own JSON file.

This script DOES NOT:
  - Decide canon.
  - Run AP.
  - Spawn anything.
  - Modify the original chapter packet.
  - Delete files.
  - Guess artistic scene names beyond a safe generated fallback.

Usage:
  python3 engainos/tools/chapter_splitter/chapter_to_stage_packets.py \
    --input mettaext/compiled/pipeline_work/compiled_chapters/scene.058_paradox_engine.json \
    --output mettaext/compiled/pipeline_work/runtime_stages \
    --book 010 \
    --chapter 058 \
    --events-per-stage 10
"""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List


def safe_slug(value: str) -> str:
    """
    Convert a title/name/id fragment into a safe lowercase slug.
    """
    value = str(value).strip().lower()
    value = re.sub(r"^scene\.", "", value)
    value = re.sub(r"^ch\.", "", value)
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unknown"


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into fixed-size chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    return [
        items[index:index + chunk_size]
        for index in range(0, len(items), chunk_size)
    ]


def load_json(path: Path) -> Dict[str, Any]:
    """
    Load a JSON object from disk.
    """
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}, got {type(data).__name__}")

    return data


def infer_chapter_id(packet: Dict[str, Any], input_path: Path, chapter: str) -> str:
    """
    Determine the chapter identity.

    Preference:
      1. packet.chapter_id
      2. packet.scene_id, because old packets used scene_id for chapter identity
      3. input filename stem
      4. ch.<chapter>
    """
    return (
        packet.get("chapter_id")
        or packet.get("scene_id")
        or input_path.stem
        or f"ch.{chapter}"
    )


def infer_chapter_slug(chapter_id: str) -> str:
    """
    Convert a chapter id like scene.058_paradox_engine into paradox_engine.
    """
    slug = safe_slug(chapter_id)
    slug = re.sub(r"^\d{3}_", "", slug)
    return slug or "chapter"


def build_stage_packet(
    source_packet: Dict[str, Any],
    chapter_id: str,
    chapter_slug: str,
    book: str,
    chapter: str,
    stage_number: int,
    events: List[Dict[str, Any]],
    stage_name: str | None = None,
) -> Dict[str, Any]:
    """
    Build one runtime/display stage packet from a source chapter packet.
    """
    stage_index = f"{stage_number:03d}"

    if stage_name:
        stage_slug = safe_slug(stage_name)
    else:
        stage_slug = f"{chapter_slug}_scn_{stage_index}"

    # Runtime/display scene id. This is the thing Godot should treat as the scene.
    scene_id = f"scene.{stage_index}_{stage_slug}"

    # Human/authoring stage id. This binds book/chapter/stage position.
    stage_id = f"stage.book{book}.chapter{chapter}.slice{stage_index}"

    # Trace/provenance id. This tells where the stage came from.
    source_packet_id = f"source.book{book}.chapter{chapter}.slice{stage_index}"

    event_start = None
    event_end = None
    if events:
        event_start = events[0].get("timestamp")
        event_end = events[-1].get("timestamp")

    stage_packet = {
        "contract": "engain.runtime_stage_packet.v1",
        "authority_state": "GENERATED_DRAFT",
        "accepted_runtime_truth": False,
        "promotion_required": True,
        "chapter_id": chapter_id,
        "stage_id": stage_id,
        "scene_id": scene_id,
        "source_packet_id": source_packet_id,
        "stage_index": stage_number,
        "stage_event_start": event_start,
        "stage_event_end": event_end,
        "description": f"book {int(book)}, chapter {int(chapter)}, scene {stage_number}",
        "source_description": source_packet.get("description", ""),
        "entities": deepcopy(source_packet.get("entities", [])),
        "locations": deepcopy(source_packet.get("locations", [])),
        "events": deepcopy(events),
        "metadata": {
            **deepcopy(source_packet.get("metadata", {})),
            "book": book,
            "chapter": chapter,
            "stage": stage_index,
            "chapter_slug": chapter_slug,
            "source_chapter_id": chapter_id,
        },
    }

    return stage_packet


def write_stage_packets(
    source_packet: Dict[str, Any],
    input_path: Path,
    output_dir: Path,
    book: str,
    chapter: str,
    events_per_stage: int,
) -> List[Path]:
    """
    Split a chapter packet into runtime stage packets and write them to output_dir.
    """
    chapter_id = infer_chapter_id(source_packet, input_path, chapter)
    chapter_slug = infer_chapter_slug(chapter_id)

    events = source_packet.get("events", [])
    if not isinstance(events, list):
        raise ValueError("source packet field 'events' must be a list")

    event_chunks = chunk_list(events, events_per_stage)

    output_dir.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []

    for index, event_chunk in enumerate(event_chunks, start=1):
        stage_packet = build_stage_packet(
            source_packet=source_packet,
            chapter_id=chapter_id,
            chapter_slug=chapter_slug,
            book=book,
            chapter=chapter,
            stage_number=index,
            events=event_chunk,
        )

        scene_id = stage_packet["scene_id"]
        output_path = output_dir / f"{scene_id}.json"
        if output_path.exists() and not getattr(write_stage_packets, "_overwrite_drafts", False):
            raise FileExistsError(
                f"Refusing to overwrite existing generated stage draft: {output_path}\n"
                f"Pass --overwrite-drafts only if you are intentionally regenerating draft files.\n"
                f"Do not use --overwrite-drafts against accepted runtime_stages."
            )

        if output_path.exists() and not getattr(write_stage_packets, "_overwrite_drafts", False):
            raise FileExistsError(
                f"Refusing to overwrite existing generated stage draft: {output_path}\n"
                f"Pass --overwrite-drafts only if you are intentionally regenerating draft files.\n"
                f"Do not use --overwrite-drafts against accepted runtime_stages."
            )

        output_path.write_text(
            json.dumps(stage_packet, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        written.append(output_path)

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split one compiled chapter packet into multiple runtime stage packets."
    )
    parser.add_argument("--input", required=True, help="Input compiled chapter JSON path.")
    parser.add_argument("--output", required=True, help="Output directory for runtime stage packets.")
    parser.add_argument("--book", required=True, help="Book number, e.g. 010.")
    parser.add_argument("--chapter", required=True, help="Chapter number, e.g. 058.")
    parser.add_argument(
        "--events-per-stage",
        type=int,
        default=10,
        help="Number of events per generated stage packet. Default: 10.",
    )
    parser.add_argument(
        "--overwrite-drafts",
        action="store_true",
        help="Allow replacing existing generated draft files. Never use for accepted runtime_stages.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    source_packet = load_json(input_path)

    write_stage_packets._overwrite_drafts = bool(args.overwrite_drafts)

    write_stage_packets._overwrite_drafts = bool(args.overwrite_drafts)

    written = write_stage_packets(
        source_packet=source_packet,
        input_path=input_path,
        output_dir=output_dir,
        book=str(args.book).zfill(3),
        chapter=str(args.chapter).zfill(3),
        events_per_stage=args.events_per_stage,
    )

    print("CHAPTER_SPLIT_COMPLETE = TRUE")
    print(f"INPUT = {input_path}")
    print(f"OUTPUT_DIR = {output_dir}")
    print(f"STAGE_COUNT = {len(written)}")
    for path in written:
        print(f"WROTE = {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
