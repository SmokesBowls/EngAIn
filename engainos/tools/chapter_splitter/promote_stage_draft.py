#!/usr/bin/env python3
"""
promote_stage_draft.py

Purpose:
  Promote a generated stage draft into an accepted runtime stage packet.

Authority rule:
  The writer may create the file.
  EngAInOS validates whether the accepted file is loadable truth.

This script writes accepted packets with:
  authority_state = ACCEPTED_RUNTIME_STAGE
  accepted_runtime_truth = true
  promotion_required = false

It refuses to overwrite accepted runtime stages unless --overwrite-accepted
is explicitly passed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict


def safe_json_filename(scene_id: str) -> str:
    scene_id = str(scene_id).strip()
    if not scene_id:
        raise ValueError("scene_id cannot be empty")

    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", scene_id)
    return f"{safe}.json"


def load_json_object(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}")

    return data


def promote_stage_draft(
    draft_path: Path,
    output_dir: Path,
    book: str,
    chapter: str,
    chapter_slug: str,
    stage: str,
    accepted_by: str,
    reason: str,
    overwrite_accepted: bool,
) -> Path:
    packet = load_json_object(draft_path)

    if packet.get("authority_state") != "GENERATED_DRAFT":
        raise ValueError(
            f"Refusing to promote packet that is not GENERATED_DRAFT. "
            f"Found authority_state={packet.get('authority_state')!r}"
        )

    if packet.get("accepted_runtime_truth") is True:
        raise ValueError("Draft already claims accepted_runtime_truth=true. Refusing ambiguous promotion.")

    book = str(book).zfill(3)
    chapter = str(chapter).zfill(3)
    stage = str(stage).zfill(3)
    chapter_slug = str(chapter_slug).strip().lower().replace(" ", "_")

    scene_id = f"scene.book{book}.chapter{chapter}.stage{stage}"

    accepted = dict(packet)
    accepted["contract"] = "engain.runtime_stage_packet.v1"
    accepted["authority_state"] = "ACCEPTED_RUNTIME_STAGE"
    accepted["accepted_runtime_truth"] = True
    accepted["promotion_required"] = False

    accepted["book_id"] = f"book.{book}"
    accepted["chapter_id"] = f"chapter.{chapter}_{chapter_slug}"
    accepted["stage_id"] = f"stage.book{book}.chapter{chapter}.slice{stage}"
    accepted["scene_id"] = scene_id
    accepted["source_packet_id"] = f"source.book{book}.chapter{chapter}.slice{stage}"

    accepted["accepted_by"] = accepted_by
    accepted["acceptance_reason"] = reason
    accepted["draft_source_path"] = str(draft_path)
    accepted["promoted_from_scene_id"] = packet.get("scene_id")
    accepted["promoted_from_source_packet_id"] = packet.get("source_packet_id")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / safe_json_filename(scene_id)

    if output_path.exists() and not overwrite_accepted:
        raise FileExistsError(
            f"Refusing to overwrite accepted runtime stage: {output_path}\n"
            f"Pass --overwrite-accepted only if you intentionally replace accepted runtime truth."
        )

    output_path.write_text(
        json.dumps(accepted, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote generated stage draft into accepted runtime stage.")
    parser.add_argument("--draft", required=True, help="Path to GENERATED_DRAFT stage JSON.")
    parser.add_argument("--output-dir", required=True, help="Accepted runtime stage output directory.")
    parser.add_argument("--book", required=True, help="Book number, e.g. 010.")
    parser.add_argument("--chapter", required=True, help="Chapter number, e.g. 058.")
    parser.add_argument("--chapter-slug", required=True, help="Chapter slug, e.g. paradox_engine.")
    parser.add_argument("--stage", required=True, help="Stage/slice number, e.g. 001.")
    parser.add_argument("--accepted-by", required=True, help="Human/operator/authority actor.")
    parser.add_argument("--reason", required=True, help="Why this stage is accepted.")
    parser.add_argument("--overwrite-accepted", action="store_true", help="Replace existing accepted runtime stage.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    output_path = promote_stage_draft(
        draft_path=Path(args.draft),
        output_dir=Path(args.output_dir),
        book=args.book,
        chapter=args.chapter,
        chapter_slug=args.chapter_slug,
        stage=args.stage,
        accepted_by=args.accepted_by,
        reason=args.reason,
        overwrite_accepted=args.overwrite_accepted,
    )

    print("STAGE_PROMOTION_COMPLETE = TRUE")
    print(f"ACCEPTED_RUNTIME_STAGE = {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
