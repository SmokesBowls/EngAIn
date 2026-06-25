#!/usr/bin/env python3
"""
runtime_stage_manifest.py

Purpose:
  Validate an accepted runtime stage-set manifest.

This proves:
  - The manifest is explicit.
  - The listed runtime stage files exist.
  - Each listed stage passes EngAInOS runtime_stage_identity validation.
  - Mechanical slices are not mistaken for authored narrative scene boundaries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from tier1.engainos.validators.runtime_stage_identity import validate_file


@dataclass(frozen=True)
class ManifestValidationResult:
    passed: bool
    code: str
    message: str
    errors: List[str]


def load_json_object(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}, got {type(data).__name__}")

    return data


def validate_runtime_stage_manifest(
    manifest_path: Path,
    stage_dir: Optional[Path] = None,
) -> ManifestValidationResult:
    errors: List[str] = []
    manifest = load_json_object(manifest_path)

    if stage_dir is None:
        stage_dir = manifest_path.parent

    if manifest.get("contract") != "engain.runtime_stage_manifest.v1":
        errors.append("contract must be engain.runtime_stage_manifest.v1")

    if manifest.get("authority_state") != "ACCEPTED_RUNTIME_STAGE_SET":
        errors.append("authority_state must be ACCEPTED_RUNTIME_STAGE_SET")

    if manifest.get("accepted_runtime_truth") is not True:
        errors.append("accepted_runtime_truth must be true")

    chapter_id = manifest.get("chapter_id")
    if not isinstance(chapter_id, str) or not chapter_id:
        errors.append("chapter_id must be a non-empty string")

    if "boundary_method" not in manifest:
        errors.append("boundary_method must be explicitly present")

    if "authored_scene_boundaries_proven" not in manifest:
        errors.append("authored_scene_boundaries_proven must be explicitly present")

    if manifest.get("boundary_method") == "mechanical_event_chunk":
        if manifest.get("authored_scene_boundaries_proven") is not False:
            errors.append(
                "mechanical_event_chunk manifests must set authored_scene_boundaries_proven=false"
            )

    stages = manifest.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append("stages must be a non-empty list")
        stages = []

    stage_count = manifest.get("stage_count")
    if stage_count != len(stages):
        errors.append(
            f"stage_count must equal len(stages): stage_count={stage_count}, len(stages)={len(stages)}"
        )

    seen = set()
    for stage_id in stages:
        if not isinstance(stage_id, str) or not stage_id:
            errors.append(f"stage entry must be a non-empty string: {stage_id!r}")
            continue

        if stage_id in seen:
            errors.append(f"duplicate stage id in manifest: {stage_id}")
            continue
        seen.add(stage_id)

        stage_path = stage_dir / f"{stage_id}.json"
        if not stage_path.exists():
            errors.append(f"listed stage file missing: {stage_path}")
            continue

        identity_result = validate_file(stage_path)
        if not identity_result.passed:
            errors.append(f"stage identity rejected: {stage_path}")
            for err in identity_result.errors:
                errors.append(f"  {err}")
            continue

        stage_packet = load_json_object(stage_path)
        if chapter_id and stage_packet.get("chapter_id") != chapter_id:
            errors.append(
                f"stage chapter_id mismatch for {stage_path.name}: "
                f"{stage_packet.get('chapter_id')} != {chapter_id}"
            )

    if errors:
        return ManifestValidationResult(
            passed=False,
            code="FALSE",
            message="runtime stage manifest rejected",
            errors=errors,
        )

    return ManifestValidationResult(
        passed=True,
        code="TRUE",
        message="runtime stage manifest accepted",
        errors=[],
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate accepted runtime stage manifest.")
    parser.add_argument("manifest", help="Path to runtime stage manifest JSON.")
    parser.add_argument(
        "--stage-dir",
        default=None,
        help="Directory containing accepted runtime stage JSON files. Defaults to manifest parent.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    stage_dir = Path(args.stage_dir) if args.stage_dir else None

    result = validate_runtime_stage_manifest(manifest_path, stage_dir=stage_dir)

    print(f"[runtime_stage_manifest][{manifest_path}] {result.code}: {result.message}")
    for error in result.errors:
        print(f"  - {error}")
    print(f"[runtime_stage_manifest][ALL] {result.code}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
