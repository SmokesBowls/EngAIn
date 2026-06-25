#!/usr/bin/env python3
"""
runtime_stage_identity.py

Purpose:
  Validate accepted runtime stage packets before EngAInOS treats them as
  runtime-loadable truth.

Core law:
  File exists on disk does not mean accepted.
  Trae/writer output does not mean accepted.
  EngAInOS validates accepted runtime stage identity before load/approval.

Expected accepted packet shape:

{
  "contract": "engain.runtime_stage_packet.v1",
  "authority_state": "ACCEPTED_RUNTIME_STAGE",
  "accepted_runtime_truth": true,
  "promotion_required": false,

  "book_id": "book.010",
  "chapter_id": "chapter.058_paradox_engine",
  "stage_id": "stage.book010.chapter058.slice001",
  "scene_id": "scene.book010.chapter058.stage001",
  "source_packet_id": "source.book010.chapter058.slice001",

  "entities": [],
  "locations": [],
  "events": []
}

Naming law:
  book_id          = book.010
  chapter_id       = chapter.058_paradox_engine
  stage_id         = stage.book010.chapter058.slice001
  scene_id         = scene.book010.chapter058.stage001
  source_packet_id = source.book010.chapter058.slice001
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


BOOK_RE = re.compile(r"^book\.(?P<book>\d{3})$")
CHAPTER_RE = re.compile(r"^chapter\.(?P<chapter>\d{3})_(?P<slug>[a-z0-9_]+)$")
STAGE_RE = re.compile(r"^stage\.book(?P<book>\d{3})\.chapter(?P<chapter>\d{3})\.slice(?P<slice>\d{3})$")
SCENE_RE = re.compile(r"^scene\.book(?P<book>\d{3})\.chapter(?P<chapter>\d{3})\.stage(?P<stage>\d{3})$")
SOURCE_RE = re.compile(r"^source\.book(?P<book>\d{3})\.chapter(?P<chapter>\d{3})\.slice(?P<slice>\d{3})$")


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    code: str
    message: str
    errors: List[str]
    details: Dict[str, Any]


def load_json_object(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}, got {type(data).__name__}")

    return data


def _match(pattern: re.Pattern[str], value: Any, field_name: str) -> tuple[Optional[Dict[str, str]], Optional[str]]:
    if not isinstance(value, str) or not value.strip():
        return None, f"{field_name} missing or not a non-empty string"

    match = pattern.match(value)
    if not match:
        return None, f"{field_name} does not match required format: {value}"

    return match.groupdict(), None


def validate_runtime_stage_identity(
    packet: Dict[str, Any],
    file_path: Optional[Path] = None,
) -> ValidationResult:
    errors: List[str] = []

    if packet.get("contract") != "engain.runtime_stage_packet.v1":
        errors.append("contract must be engain.runtime_stage_packet.v1")

    if packet.get("authority_state") != "ACCEPTED_RUNTIME_STAGE":
        errors.append("authority_state must be ACCEPTED_RUNTIME_STAGE")

    if packet.get("accepted_runtime_truth") is not True:
        errors.append("accepted_runtime_truth must be true")

    if packet.get("promotion_required") is not False:
        errors.append("promotion_required must be false")

    book_parts, err = _match(BOOK_RE, packet.get("book_id"), "book_id")
    if err:
        errors.append(err)

    chapter_parts, err = _match(CHAPTER_RE, packet.get("chapter_id"), "chapter_id")
    if err:
        errors.append(err)

    stage_parts, err = _match(STAGE_RE, packet.get("stage_id"), "stage_id")
    if err:
        errors.append(err)

    scene_parts, err = _match(SCENE_RE, packet.get("scene_id"), "scene_id")
    if err:
        errors.append(err)

    source_parts, err = _match(SOURCE_RE, packet.get("source_packet_id"), "source_packet_id")
    if err:
        errors.append(err)

    if book_parts and stage_parts and book_parts["book"] != stage_parts["book"]:
        errors.append("book_id and stage_id book number mismatch")

    if book_parts and scene_parts and book_parts["book"] != scene_parts["book"]:
        errors.append("book_id and scene_id book number mismatch")

    if book_parts and source_parts and book_parts["book"] != source_parts["book"]:
        errors.append("book_id and source_packet_id book number mismatch")

    if chapter_parts and stage_parts and chapter_parts["chapter"] != stage_parts["chapter"]:
        errors.append("chapter_id and stage_id chapter number mismatch")

    if chapter_parts and scene_parts and chapter_parts["chapter"] != scene_parts["chapter"]:
        errors.append("chapter_id and scene_id chapter number mismatch")

    if chapter_parts and source_parts and chapter_parts["chapter"] != source_parts["chapter"]:
        errors.append("chapter_id and source_packet_id chapter number mismatch")

    if stage_parts and scene_parts and stage_parts["slice"] != scene_parts["stage"]:
        errors.append("stage_id slice number and scene_id stage number mismatch")

    if stage_parts and source_parts and stage_parts["slice"] != source_parts["slice"]:
        errors.append("stage_id slice number and source_packet_id slice number mismatch")

    if file_path is not None and scene_parts:
        expected_name = f"{packet.get('scene_id')}.json"
        if file_path.name != expected_name:
            errors.append(f"filename must match scene_id: expected {expected_name}, got {file_path.name}")

    if not isinstance(packet.get("entities", []), list):
        errors.append("entities must be a list")

    if not isinstance(packet.get("locations", []), list):
        errors.append("locations must be a list")

    if not isinstance(packet.get("events", []), list):
        errors.append("events must be a list")

    if errors:
        return ValidationResult(
            passed=False,
            code="FALSE",
            message="runtime stage identity rejected",
            errors=errors,
            details={},
        )

    return ValidationResult(
        passed=True,
        code="TRUE",
        message="runtime stage identity accepted",
        errors=[],
        details={
            "book": book_parts["book"] if book_parts else None,
            "chapter": chapter_parts["chapter"] if chapter_parts else None,
            "stage": scene_parts["stage"] if scene_parts else None,
            "scene_id": packet.get("scene_id"),
        },
    )


def validate_file(path: Path) -> ValidationResult:
    packet = load_json_object(path)
    return validate_runtime_stage_identity(packet, file_path=path)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate accepted runtime stage packet identity.")
    parser.add_argument("paths", nargs="+", help="Runtime stage JSON files to validate.")
    args = parser.parse_args()

    all_passed = True

    for raw in args.paths:
        path = Path(raw)
        result = validate_file(path)
        print(f"[runtime_stage_identity][{path}] {result.code}: {result.message}")

        for error in result.errors:
            print(f"  - {error}")

        if not result.passed:
            all_passed = False

    print(f"[runtime_stage_identity][ALL] {'TRUE' if all_passed else 'FALSE'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
