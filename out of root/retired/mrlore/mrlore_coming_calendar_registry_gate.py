#!/usr/bin/env python3
"""
mrlore_coming_calendar_registry_gate.py — validate the author-declared Coming calendar registry.

The Coming calendar is temporal-context-only. It gives MrLore an absolute
cosmic-year axis for North/South continuity without writing canon, promoting
claims, resolving contradictions, or touching runtime/Godot/ZONJ systems.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT = "engain.mrlore_coming_calendar_registry.v1"
GATE_CONTRACT = "engain.mrlore_coming_calendar_registry_gate_manifest.v1"
AUTHORITY_OWNER = "AUTHOR_DECLARED"
REQUIRED_POLICY_EFFECT = "TEMPORAL_CONTEXT_ONLY"
ALLOWED_REGIONS = {"NORTH", "SOUTH", "COSMIC"}
REQUIRED_DOCTRINE_LOCKS = (
    "Chapter order is source retrieval order, not absolute story-time order.",
    "Cosmic Year is absolute world-history time.",
    "Coming ID groups regional manifestations.",
    "Regional names are aliases, not separate events.",
    "The Coming and The Shadow can be same event when they share the same shared_event_id.",
    "Branch-local elapsed years must map back to Cosmic Year.",
    "North and South manifestations with the same shared_event_id are concurrent unless explicitly marked otherwise.",
    "This registry does not write canon.",
    "This registry does not promote claims.",
    "This registry does not resolve contradictions.",
    "This registry does not touch runtime, Godot, or ZONJ.",
)

_HERE = Path(__file__).resolve().parent
_SCHEMA_PATH = _HERE / "timeline" / "coming_calendar.schema.json"
_DEFAULT_REGISTRY_PATH = _HERE / "timeline" / "default_coming_calendar.json"


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


def _resolve_engain_dir(manifest_path: Path) -> Path:
    if not manifest_path.exists():
        raise FileNotFoundError(f"engain_manifest.json not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = data.get("output_dir")
    active_vault = data.get("active_vault")
    if output_dir:
        return Path(output_dir)
    if active_vault:
        return Path(active_vault) / ".engain"
    raise ValueError("engain_manifest.json has no output_dir or active_vault")


def _infer_engain_dir_from_registry_path(registry_path: Path) -> Path:
    resolved = registry_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def default_registry_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "timeline" / "coming_calendar.json"


def default_registry_template_path() -> Path:
    return _DEFAULT_REGISTRY_PATH


def _base_manifest(registry_path: Path, manifest_path: Path) -> dict[str, Any]:
    return {
        "contract": GATE_CONTRACT,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(registry_path),
        "schema_path": str(_SCHEMA_PATH),
        "manifest_path": str(manifest_path),
        "MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE": False,
        "REGISTRY_FOUND": registry_path.exists(),
        "REGISTRY_JSON_VALID": False,
        "REGISTRY_SCHEMA_VALID": False,
        "COMINGS_LOADED": 0,
        "MANIFESTATIONS_LOADED": 0,
        "SHARED_EVENTS_LOADED": 0,
        "CHAPTER_RANGES_LOADED": 0,
        "DUPLICATE_COMING_IDS_FOUND": False,
        "CONFLICTING_SHARED_EVENT_IDS_FOUND": False,
        "POLICY_EFFECT": None,
        "TEMPORAL_ENRICHMENT_CAN_CONSUME": False,
        "RUNTIME_AUTHORITY": None,
        "CANON_AUTHORITY": None,
        "CLAIMS_ALTERED": False,
        "CANDIDATES_ALTERED": False,
        "QUEUES_ALTERED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "chapter_ranges_by_coming": {},
        "errors": [],
        "errors_count": 0,
    }


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest["errors_count"] = len(manifest.get("errors", []))
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _schema_validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["registry root must be a JSON object"]

    required_root = {
        "contract",
        "authority_owner",
        "runtime_authority",
        "canon_authority",
        "policy_effect",
        "doctrine_locks",
        "comings",
    }
    missing_root = sorted(required_root - set(data))
    if missing_root:
        errors.append(f"registry missing required keys: {', '.join(missing_root)}")
    if data.get("contract") != CONTRACT:
        errors.append(f"contract must be {CONTRACT}")
    if data.get("authority_owner") != AUTHORITY_OWNER:
        errors.append("authority_owner must be AUTHOR_DECLARED")
    if data.get("runtime_authority") is not False:
        errors.append("runtime_authority must be false")
    if data.get("canon_authority") is not False:
        errors.append("canon_authority must be false")
    if data.get("policy_effect") != REQUIRED_POLICY_EFFECT:
        errors.append("policy_effect must equal TEMPORAL_CONTEXT_ONLY")

    doctrine_locks = data.get("doctrine_locks")
    if not isinstance(doctrine_locks, list) or not all(_is_nonempty_string(item) for item in doctrine_locks):
        errors.append("doctrine_locks must be a non-empty list of strings")
    else:
        missing_locks = [lock for lock in REQUIRED_DOCTRINE_LOCKS if lock not in doctrine_locks]
        if missing_locks:
            errors.append(f"doctrine_locks missing required locks: {'; '.join(missing_locks)}")

    comings = data.get("comings")
    if not isinstance(comings, list) or not comings:
        errors.append("comings must be a non-empty list")
        return errors

    for index, coming in enumerate(comings):
        prefix = f"comings[{index}]"
        if not isinstance(coming, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("coming_id", "coming_number", "shared_event_id", "regional_manifestations", "aliases", "status", "notes"):
            if key not in coming:
                errors.append(f"{prefix} missing required key: {key}")
        if not _is_nonempty_string(coming.get("coming_id")):
            errors.append(f"{prefix}.coming_id must be a non-empty string")
        if not isinstance(coming.get("coming_number"), int):
            errors.append(f"{prefix}.coming_number must be an integer")
        if not isinstance(coming.get("cosmic_year_start"), int):
            errors.append(f"{prefix}.cosmic_year_start must be an integer")
        if "cosmic_year_end" in coming and not isinstance(coming.get("cosmic_year_end"), int):
            errors.append(f"{prefix}.cosmic_year_end must be an integer when present")
        if "cosmic_year_end_approx" in coming and not isinstance(coming.get("cosmic_year_end_approx"), bool):
            errors.append(f"{prefix}.cosmic_year_end_approx must be boolean when present")
        if "cosmic_year_start_approx" in coming and not isinstance(coming.get("cosmic_year_start_approx"), bool):
            errors.append(f"{prefix}.cosmic_year_start_approx must be boolean when present")
        if not _is_nonempty_string(coming.get("shared_event_id")):
            errors.append(f"{prefix}.shared_event_id must be a non-empty string")
        if not isinstance(coming.get("aliases"), list):
            errors.append(f"{prefix}.aliases must be a list")
        if not _is_nonempty_string(coming.get("status")):
            errors.append(f"{prefix}.status must be a non-empty string")
        if not isinstance(coming.get("notes"), str):
            errors.append(f"{prefix}.notes must be a string")

        manifestations = coming.get("regional_manifestations")
        if not isinstance(manifestations, list) or not manifestations:
            errors.append(f"{prefix}.regional_manifestations must be a non-empty list")
            continue
        for manifestation_index, manifestation in enumerate(manifestations):
            mprefix = f"{prefix}.regional_manifestations[{manifestation_index}]"
            if not isinstance(manifestation, dict):
                errors.append(f"{mprefix} must be an object")
                continue
            if manifestation.get("region") not in ALLOWED_REGIONS:
                errors.append(f"{mprefix}.region must be one of NORTH, SOUTH, COSMIC")
            if not _is_nonempty_string(manifestation.get("regional_name")):
                errors.append(f"{mprefix}.regional_name must be a non-empty string")
            chapter_ranges = manifestation.get("manuscript_chapter_ranges")
            if not isinstance(chapter_ranges, list) or not chapter_ranges:
                errors.append(f"{mprefix}.manuscript_chapter_ranges must be a non-empty list")
            elif not all(_is_nonempty_string(item) for item in chapter_ranges):
                errors.append(f"{mprefix}.manuscript_chapter_ranges entries must be non-empty strings")
    return errors


def _duplicate_coming_id_errors(comings: list[Any]) -> tuple[bool, list[str]]:
    counts = Counter(coming.get("coming_id") for coming in comings if isinstance(coming, dict) and _is_nonempty_string(coming.get("coming_id")))
    duplicate_errors = [f"coming_id {coming_id!r} appears {count} times" for coming_id, count in sorted(counts.items()) if count > 1]
    return bool(duplicate_errors), duplicate_errors


def _shared_event_conflict_errors(comings: list[Any]) -> tuple[bool, list[str]]:
    by_event: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    approximate_events: set[str] = set()
    for coming in comings:
        if not isinstance(coming, dict):
            continue
        event_id = coming.get("shared_event_id")
        year = coming.get("cosmic_year_start")
        coming_id = coming.get("coming_id")
        if not _is_nonempty_string(event_id) or not isinstance(year, int) or not _is_nonempty_string(coming_id):
            continue
        event_key = str(event_id)
        coming_key = str(coming_id)
        if coming.get("cosmic_year_start_approx") is True or coming.get("cosmic_year_end_approx") is True:
            approximate_events.add(event_key)
        by_event[event_key][year].append(coming_key)

    errors: list[str] = []
    for event_id, years in sorted(by_event.items()):
        if len(years) <= 1 or event_id in approximate_events:
            continue
        detail = ", ".join(f"{year}: {','.join(sorted(ids))}" for year, ids in sorted(years.items()))
        errors.append(f"shared_event_id {event_id!r} has conflicting cosmic_year_start values: {detail}")
    return bool(errors), errors


def _summarize(data: dict[str, Any], manifest: dict[str, Any]) -> None:
    comings = data.get("comings", []) if isinstance(data.get("comings"), list) else []
    valid_comings = [coming for coming in comings if isinstance(coming, dict)]
    shared_events = {coming.get("shared_event_id") for coming in valid_comings if _is_nonempty_string(coming.get("shared_event_id"))}
    chapter_ranges_by_coming: dict[str, dict[str, list[str]]] = {}
    manifestations_loaded = 0
    chapter_ranges_loaded = 0

    for coming in valid_comings:
        coming_id = coming.get("coming_id")
        if not _is_nonempty_string(coming_id):
            continue
        coming_key = str(coming_id)
        chapter_ranges_by_coming.setdefault(coming_key, {})
        manifestations = coming.get("regional_manifestations", [])
        if not isinstance(manifestations, list):
            continue
        for manifestation in manifestations:
            if not isinstance(manifestation, dict):
                continue
            manifestations_loaded += 1
            region = manifestation.get("region")
            chapter_ranges = manifestation.get("manuscript_chapter_ranges", [])
            if not isinstance(region, str):
                region = "UNKNOWN"
            if isinstance(chapter_ranges, list):
                kept_ranges = [item for item in chapter_ranges if isinstance(item, str)]
                chapter_ranges_by_coming[coming_key].setdefault(region, []).extend(kept_ranges)
                chapter_ranges_loaded += len(kept_ranges)

    manifest["COMINGS_LOADED"] = len(valid_comings)
    manifest["MANIFESTATIONS_LOADED"] = manifestations_loaded
    manifest["SHARED_EVENTS_LOADED"] = len(shared_events)
    manifest["CHAPTER_RANGES_LOADED"] = chapter_ranges_loaded
    manifest["chapter_ranges_by_coming"] = chapter_ranges_by_coming


def run_coming_calendar_registry_gate(
    registry_path: Path | str,
    manifest_path: Path | str | None = None,
    *,
    install_default_if_missing: bool = True,
) -> dict[str, Any]:
    registry_file = Path(registry_path).resolve()
    engain_dir = _infer_engain_dir_from_registry_path(registry_file)
    manifest_file = Path(manifest_path).resolve() if manifest_path else engain_dir / "manifests" / "coming_calendar_registry_gate_manifest.json"

    if install_default_if_missing and not registry_file.exists():
        install_default_coming_calendar_registry(registry_file)

    manifest = _base_manifest(registry_file, manifest_file)
    if not registry_file.exists():
        manifest["errors"].append(f"coming calendar registry not found: {registry_file}")
        _write_manifest(manifest_file, manifest)
        return manifest

    try:
        data = json.loads(registry_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        manifest["errors"].append(f"registry JSON invalid: {exc.msg}")
        _write_manifest(manifest_file, manifest)
        return manifest

    manifest["REGISTRY_JSON_VALID"] = True
    if isinstance(data, dict):
        manifest["POLICY_EFFECT"] = data.get("policy_effect")
        manifest["RUNTIME_AUTHORITY"] = data.get("runtime_authority")
        manifest["CANON_AUTHORITY"] = data.get("canon_authority")
        _summarize(data, manifest)

    schema_errors = _schema_validate(data)
    comings = data.get("comings", []) if isinstance(data, dict) and isinstance(data.get("comings"), list) else []
    duplicate_found, duplicate_errors = _duplicate_coming_id_errors(comings)
    shared_conflict_found, shared_conflict_errors = _shared_event_conflict_errors(comings)
    manifest["DUPLICATE_COMING_IDS_FOUND"] = duplicate_found
    manifest["CONFLICTING_SHARED_EVENT_IDS_FOUND"] = shared_conflict_found
    manifest["errors"].extend(schema_errors)
    manifest["errors"].extend(duplicate_errors)
    manifest["errors"].extend(shared_conflict_errors)
    manifest["REGISTRY_SCHEMA_VALID"] = not schema_errors
    manifest["TEMPORAL_ENRICHMENT_CAN_CONSUME"] = (
        manifest["REGISTRY_FOUND"] is True
        and manifest["REGISTRY_JSON_VALID"] is True
        and manifest["REGISTRY_SCHEMA_VALID"] is True
        and not duplicate_found
        and not shared_conflict_found
        and manifest["POLICY_EFFECT"] == REQUIRED_POLICY_EFFECT
        and manifest["RUNTIME_AUTHORITY"] is False
        and manifest["CANON_AUTHORITY"] is False
    )
    manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] = bool(manifest["TEMPORAL_ENRICHMENT_CAN_CONSUME"])
    _write_manifest(manifest_file, manifest)
    return manifest


def install_default_coming_calendar_registry(registry_path: Path | str) -> Path:
    registry_file = Path(registry_path).resolve()
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_DEFAULT_REGISTRY_PATH, registry_file)
    return registry_file


def load_coming_calendar_registry(registry_path: Path | str) -> dict[str, Any]:
    registry_file = Path(registry_path).resolve()
    engain_dir = _infer_engain_dir_from_registry_path(registry_file)
    gate_manifest_path = engain_dir / "manifests" / "coming_calendar_registry_gate_manifest.json"
    if not gate_manifest_path.exists():
        raise FileNotFoundError(f"Coming calendar gate manifest not found: {gate_manifest_path}")
    gate_manifest = json.loads(gate_manifest_path.read_text(encoding="utf-8"))
    if not gate_manifest.get("MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE", False):
        raise ValueError("Coming calendar gate manifest is not complete")
    if not gate_manifest.get("TEMPORAL_ENRICHMENT_CAN_CONSUME", False):
        raise ValueError("Coming calendar registry is not consumable by temporal enrichment")
    return json.loads(registry_file.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MrLore Coming calendar registry.")
    parser.add_argument("--registry", default=None, help="Path to coming_calendar.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json for active .engain discovery.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--no-install-default", action="store_true", help="Do not install repo default registry if active registry is missing.")
    args = parser.parse_args()

    try:
        engain_dir = Path(args.engain_dir).resolve() if args.engain_dir else None
        manifest_path = Path(args.manifest) if args.manifest else None
        registry_path = Path(args.registry).resolve() if args.registry else default_registry_path(manifest_path, engain_dir)
        manifest = run_coming_calendar_registry_gate(
            registry_path,
            install_default_if_missing=not args.no_install_default,
        )
    except Exception as exc:
        print(f"[COMING_CALENDAR_REGISTRY_GATE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE={manifest['MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE']}")
    print(f"REGISTRY_FOUND={manifest['REGISTRY_FOUND']}")
    print(f"REGISTRY_JSON_VALID={manifest['REGISTRY_JSON_VALID']}")
    print(f"REGISTRY_SCHEMA_VALID={manifest['REGISTRY_SCHEMA_VALID']}")
    print(f"COMINGS_LOADED={manifest['COMINGS_LOADED']}")
    print(f"MANIFESTATIONS_LOADED={manifest['MANIFESTATIONS_LOADED']}")
    print(f"SHARED_EVENTS_LOADED={manifest['SHARED_EVENTS_LOADED']}")
    print(f"CHAPTER_RANGES_LOADED={manifest['CHAPTER_RANGES_LOADED']}")
    print(f"DUPLICATE_COMING_IDS_FOUND={manifest['DUPLICATE_COMING_IDS_FOUND']}")
    print(f"CONFLICTING_SHARED_EVENT_IDS_FOUND={manifest['CONFLICTING_SHARED_EVENT_IDS_FOUND']}")
    print(f"POLICY_EFFECT={manifest['POLICY_EFFECT']}")
    print(f"TEMPORAL_ENRICHMENT_CAN_CONSUME={manifest['TEMPORAL_ENRICHMENT_CAN_CONSUME']}")
    print(f"RUNTIME_AUTHORITY={manifest['RUNTIME_AUTHORITY']}")
    print(f"CANON_AUTHORITY={manifest['CANON_AUTHORITY']}")
    print(f"CLAIMS_ALTERED={manifest['CLAIMS_ALTERED']}")
    print(f"CANDIDATES_ALTERED={manifest['CANDIDATES_ALTERED']}")
    print(f"QUEUES_ALTERED={manifest['QUEUES_ALTERED']}")
    print(f"CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"errors_count={manifest['errors_count']}")
    print(f"MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
