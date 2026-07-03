#!/usr/bin/env python3
"""
mrlore_claim_extraction_runner.py — EngAIn MrLore Claim Extraction MVP

PURPOSE:
    Read mrlore_scene_intake_manifest.json.
    Loop loaded scene packet JSON paths.
    Extract deterministic proposal-only claims.
    Emit proposed_claims.jsonl and mrlore_claim_extraction_manifest.json.

INPUT:
    vault/.engain/manifests/mrlore_scene_intake_manifest.json

OUTPUT:
    vault/.engain/mrlore/claims/proposed_claims.jsonl
    vault/.engain/manifests/mrlore_claim_extraction_manifest.json

DOES NOT:
    read raw chapters
    decide canon
    resolve contradictions
    compile ZONJ
    touch Godot
    touch runtime
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ENTITY_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z'’-]*(?:\s+[A-Z][A-Za-z'’-]*){0,3}\b"
)

# Deterministic guardrail only. This is not canon judgment.
_ENTITY_STOPWORDS = {
    "A",
    "An",
    "And",
    "As",
    "At",
    "But",
    "By",
    "For",
    "From",
    "He",
    "Her",
    "His",
    "I",
    "If",
    "In",
    "It",
    "Not",
    "No",
    "Now",
    "Never",
    "Neither",
    "Of",
    "On",
    "Once",
    "Only",
    "Or",
    "Perhaps",
    "Outside",
    "She",
    "So",
    "Some",
    "Still",
    "That",
    "The",
    "Their",
    "Then",
    "They",
    "This",
    "Those",
    "Thread",
    "To",
    "We",
    "When",
    "Where",
    "While",
    "With",
    "Without",
    "Yet",
    "You",
    "Book",
    "Chapter",
    "Part",
}

_ENVIRONMENT_KEYS = (
    "terrain_family",
    "region",
    "biome",
    "location",
    "weather",
    "lighting",
    "time_of_day",
    "temperature",
    "boundary_hints",
    "hazard_hints",
    "path_hints",
    "atmospheric_hints",
)


def _find_engain_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(8):
        if (cur / "tier1").exists() and (cur / "tier2").exists() and (cur / "tier3").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return start.resolve()


_HERE = Path(__file__).resolve().parent
_ENGAIN_ROOT = _find_engain_root(_HERE)


def _default_manifest_path() -> Path:
    candidates = [
        _ENGAIN_ROOT / "tier1" / "engainos" / "assets" / "engain_manifest.json",
        _HERE.parent / "engainos" / "assets" / "engain_manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _resolve_engain_dir_from_manifest(manifest_path: Path) -> Path:
    if not manifest_path.exists():
        raise FileNotFoundError(f"engain_manifest.json not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = data.get("output_dir")
    active_vault = data.get("active_vault")
    if output_dir:
        return Path(output_dir)
    if active_vault:
        return Path(active_vault) / ".engain"
    raise ValueError(
        "engain_manifest.json has no output_dir or active_vault. "
        "Run vault_discovery.py first."
    )


def default_intake_manifest_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"


def _line_for_text(text: str, needle: str, scene_start_line: int) -> int:
    for offset, line in enumerate(text.splitlines() or [text]):
        if needle in line:
            return scene_start_line + offset
    return scene_start_line


def _claim_id(parts: Iterable[Any]) -> str:
    raw = "|".join(str(part) for part in parts)
    return "claim." + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _claim(
    *,
    scene_id: str,
    domain: str,
    claim_type: str,
    subject: str,
    predicate: str,
    object_value: str,
    source_line: int,
) -> dict[str, Any]:
    claim = {
        "claim_id": _claim_id((scene_id, domain, claim_type, subject, predicate, object_value, source_line)),
        "SOURCE_SCENE": scene_id,
        "source_scene": scene_id,
        "source_line": source_line,
        "source_span": {"start": source_line, "end": source_line},
        "claim_domain": domain,
        "claim_type": claim_type,
        "subject": subject,
        "predicate": predicate,
        "object": object_value,
        "status": "PROPOSED",
    }
    return claim


def _is_probable_entity(candidate: str) -> bool:
    if candidate in _ENTITY_STOPWORDS:
        return False
    first = candidate.split()[0]
    if first in _ENTITY_STOPWORDS:
        return False
    if candidate.isupper():
        return False
    if any(ch.isdigit() for ch in candidate):
        return False
    return True


def extract_entity_presence_claims(scene_packet: dict[str, Any]) -> list[dict[str, Any]]:
    scene_id = str(scene_packet.get("scene_id") or "")
    text = str(scene_packet.get("text") or "")
    start_line = int(scene_packet.get("start_line") or 1)
    claims: list[dict[str, Any]] = []
    seen: set[str] = set()

    for match in ENTITY_PATTERN.finditer(text):
        candidate = match.group(0).strip()
        if not _is_probable_entity(candidate):
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        source_line = _line_for_text(text, candidate, start_line)
        claims.append(
            _claim(
                scene_id=scene_id,
                domain="entity",
                claim_type="entity_presence",
                subject=candidate,
                predicate="present_in",
                object_value=scene_id,
                source_line=source_line,
            )
        )

    return claims


def extract_environment_state_claims(scene_packet: dict[str, Any]) -> list[dict[str, Any]]:
    scene_id = str(scene_packet.get("scene_id") or "")
    start_line = int(scene_packet.get("start_line") or 1)
    environment = scene_packet.get("environment") or {}
    if not isinstance(environment, dict):
        return []

    claims: list[dict[str, Any]] = []
    for key in _ENVIRONMENT_KEYS:
        if key not in environment:
            continue
        value = environment[key]
        if value in (None, "", []):
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            object_value = str(item).strip()
            if not object_value:
                continue
            claims.append(
                _claim(
                    scene_id=scene_id,
                    domain="environment",
                    claim_type="environment_state",
                    subject=scene_id,
                    predicate=key,
                    object_value=object_value,
                    source_line=start_line,
                )
            )
    return claims


def extract_claims_from_scene_packet(scene_packet: dict[str, Any]) -> list[dict[str, Any]]:
    claims = []
    claims.extend(extract_environment_state_claims(scene_packet))
    claims.extend(extract_entity_presence_claims(scene_packet))
    return sorted(claims, key=lambda c: c["claim_id"])


def _iter_intake_scenes(intake_manifest: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for chapter in intake_manifest.get("chapters", []):
        if chapter.get("status") != "MRLORE_READY":
            continue
        for scene in chapter.get("scenes", []):
            if scene.get("mr_lore_ready") is False:
                continue
            packet_json = scene.get("packet_json")
            if packet_json:
                yield scene


def run_claim_extraction(intake_manifest_path: Path | str) -> dict[str, Any]:
    intake_path = Path(intake_manifest_path).resolve()
    intake = json.loads(intake_path.read_text(encoding="utf-8"))

    engain_dir = Path(intake.get("engain_dir") or intake_path.parents[1]).resolve()
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    extraction_manifest_path = engain_dir / "manifests" / "mrlore_claim_extraction_manifest.json"
    claims_path.parent.mkdir(parents=True, exist_ok=True)
    extraction_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    claims: list[dict[str, Any]] = []
    errors: list[str] = []
    scenes_processed = 0

    for scene_entry in _iter_intake_scenes(intake):
        packet_path = Path(str(scene_entry["packet_json"])).resolve()
        try:
            scene_packet = json.loads(packet_path.read_text(encoding="utf-8"))
        except Exception as exc:  # deterministic report, no fallback to raw chapters
            errors.append(f"Failed to load scene packet {packet_path}: {exc}")
            continue
        scenes_processed += 1
        claims.extend(extract_claims_from_scene_packet(scene_packet))

    claims = sorted(claims, key=lambda c: c["claim_id"])
    claims_path.write_text(
        "".join(json.dumps(claim, ensure_ascii=False, sort_keys=True) + "\n" for claim in claims),
        encoding="utf-8",
    )

    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_claim_extraction_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_intake_manifest": str(intake_path),
        "engain_dir": str(engain_dir),
        "proposed_claims_jsonl": str(claims_path),
        "scenes_expected": intake.get("total_scenes_loaded"),
        "scenes_processed": scenes_processed,
        "claims_written": len(claims),
        "errors": errors,
        "CLAIMS_EXTRACTED": True,
        "CLAIMS_STATUS": "PROPOSED",
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "GODOT_TOUCHED": False,
        "raw_chapters_read": False,
    }
    extraction_manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="EngAIn MrLore Claim Extraction — proposal-only claims from scene intake manifest."
    )
    parser.add_argument(
        "--intake-manifest",
        default=None,
        help="Path to mrlore_scene_intake_manifest.json.",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to engain_manifest.json for resolving vault/.engain if --intake-manifest is omitted.",
    )
    parser.add_argument(
        "--engain-dir",
        default=None,
        help="Direct path to vault/.engain for resolving intake manifest if --intake-manifest is omitted.",
    )
    args = parser.parse_args()

    try:
        if args.intake_manifest:
            intake_path = Path(args.intake_manifest)
        else:
            manifest_path = Path(args.manifest) if args.manifest else None
            engain_dir = Path(args.engain_dir) if args.engain_dir else None
            intake_path = default_intake_manifest_path(manifest_path, engain_dir)
        if not intake_path.exists():
            print(f"[CLAIMS] ERROR: Intake manifest not found: {intake_path}", file=sys.stderr)
            return 1
        manifest = run_claim_extraction(intake_path)
    except Exception as exc:
        print(f"[CLAIMS] ERROR: {exc}", file=sys.stderr)
        return 1

    print("\n[CLAIMS] MRLORE_CLAIM_EXTRACTION_COMPLETE = TRUE")
    print(f"[CLAIMS] SOURCE_INTAKE_MANIFEST = {manifest['source_intake_manifest']}")
    print(f"[CLAIMS] SCENES_PROCESSED       = {manifest['scenes_processed']}")
    print(f"[CLAIMS] CLAIMS_WRITTEN         = {manifest['claims_written']}")
    print(f"[CLAIMS] CLAIMS_STATUS          = {manifest['CLAIMS_STATUS']}")
    print(f"[CLAIMS] CANON_WRITTEN          = {manifest['CANON_WRITTEN']}")
    print(f"[CLAIMS] RUNTIME_TOUCHED        = {manifest['RUNTIME_TOUCHED']}")
    print(f"[CLAIMS] PROPOSED_CLAIMS_JSONL  = {manifest['proposed_claims_jsonl']}")
    if manifest["errors"]:
        print(f"[CLAIMS] ERRORS                 = {len(manifest['errors'])}")
        return 1
    print("[CLAIMS] ERRORS                 = 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
