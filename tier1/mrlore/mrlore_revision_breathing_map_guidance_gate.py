#!/usr/bin/env python3
"""
mrlore_revision_breathing_map_guidance_gate.py — validate breathing map guidance quality.

This gate proves that breathing_map.jsonl is an author-facing revision guidance
surface, not a score-only artifact and not a prose rewrite artifact. It reads the
revision layer only and writes a manifest. It does not alter claims, canon,
contradictions, ZONJ, runtime, Godot, or the breathing map itself.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT = "engain.mrlore_revision_breathing_map_guidance_gate_manifest.v1"

REQUIRED_FIELDS = (
    "chapter_id",
    "book_id",
    "chapter_number",
    "pressure_score",
    "pressure_rank_global",
    "pressure_rank_within_book",
    "detected_event_pressure",
    "missing_breath_type",
    "expected_internal_feeling",
    "revision_guidance",
    "do_not_change",
    "author_action_required",
)
RANKING_FIELDS = (
    "pressure_score",
    "pressure_rank_global",
    "pressure_percentile_global",
    "pressure_rank_within_book",
    "pressure_percentile_within_book",
    "pressure_tier_global",
    "pressure_tier_within_book",
)
SAFETY_LOCK_FIELDS = (
    "DIAGNOSTIC_REVISION_GUIDANCE_ONLY",
    "PRESSURE_SCORE_DIAGNOSTIC_NOT_QUALITY_JUDGMENT",
    "HIGH_PRESSURE_NOT_BAD_CHAPTER",
    "HIGH_PRESSURE_STATE_CHANGE_HUMAN_REVIEW",
    "AUTHOR_REVISES_MANUALLY",
    "CANON_WRITTEN",
    "CLAIMS_PROMOTED",
    "CLAIMS_REJECTED",
    "CONTRADICTIONS_RESOLVED",
    "ACCEPTED_LORE_PACKETS_CREATED",
    "ZONJ_COMPILED",
    "GODOT_TOUCHED",
    "RUNTIME_TOUCHED",
)
FALSE_LOCK_FIELDS = (
    "CANON_WRITTEN",
    "CLAIMS_PROMOTED",
    "CLAIMS_REJECTED",
    "CONTRADICTIONS_RESOLVED",
    "ACCEPTED_LORE_PACKETS_CREATED",
    "ZONJ_COMPILED",
    "GODOT_TOUCHED",
    "RUNTIME_TOUCHED",
)
TRUE_LOCK_FIELDS = (
    "DIAGNOSTIC_REVISION_GUIDANCE_ONLY",
    "PRESSURE_SCORE_DIAGNOSTIC_NOT_QUALITY_JUDGMENT",
    "HIGH_PRESSURE_NOT_BAD_CHAPTER",
    "HIGH_PRESSURE_STATE_CHANGE_HUMAN_REVIEW",
    "AUTHOR_REVISES_MANUALLY",
)
FORBIDDEN_REWRITE_FIELDS = (
    "rewritten_scene",
    "replacement_paragraph",
    "replacement_scene",
    "generated_prose",
    "suggested_rewrite",
    "new_chapter_text",
    "canon_patch",
    "accepted_lore_packet",
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
    raise ValueError("engain_manifest.json has no output_dir or active_vault")


def default_paths(manifest_path: Path | None = None, engain_dir: Path | None = None) -> dict[str, Path]:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return {
        "breathing_map": engain_dir / "mrlore" / "revision" / "breathing_map.jsonl",
        "manifest": engain_dir / "manifests" / "mrlore_revision_breathing_map_guidance_gate_manifest.json",
    }


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return records, [{"path": str(path), "line": None, "error": "breathing map not found"}]
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append({"path": str(path), "line": line_number, "error": f"invalid JSON: {exc.msg}"})
                continue
            if not isinstance(record, dict):
                errors.append({"path": str(path), "line": line_number, "error": "record must be a JSON object"})
                continue
            records.append(record)
    return records, errors


def _field_type_ok(record: dict[str, Any], field: str) -> bool:
    value = record.get(field)
    if field in {"detected_event_pressure", "missing_breath_type", "do_not_change"}:
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if field in {"expected_internal_feeling", "revision_guidance", "chapter_id", "book_id"}:
        return isinstance(value, str) and bool(value.strip())
    if field in {"chapter_number", "pressure_rank_global", "pressure_rank_within_book"}:
        return isinstance(value, int) and value >= 0
    if field == "pressure_score":
        return isinstance(value, (int, float))
    if field == "author_action_required":
        return value is True
    return field in record


def _forbidden_paths(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_str = str(key)
            path = f"{prefix}.{key_str}" if prefix else key_str
            if key_str in FORBIDDEN_REWRITE_FIELDS:
                paths.append(path)
            paths.extend(_forbidden_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            paths.extend(_forbidden_paths(item, path))
    return paths


def run_guidance_gate(
    breathing_map_path: Path | str,
    manifest_path: Path | str,
) -> dict[str, Any]:
    breathing_map_file = Path(breathing_map_path).resolve()
    manifest_file = Path(manifest_path).resolve()
    records, read_errors = _read_jsonl(breathing_map_file)

    missing_required: list[dict[str, Any]] = []
    missing_ranking: list[dict[str, Any]] = []
    missing_safety: list[dict[str, Any]] = []
    author_action_failures: list[dict[str, Any]] = []
    forbidden_hits: list[dict[str, Any]] = []

    for index, record in enumerate(records, 1):
        record_id = str(record.get("chapter_id") or f"record.{index}")
        for field in REQUIRED_FIELDS:
            if not _field_type_ok(record, field):
                missing_required.append({"record_index": index, "record_id": record_id, "field": field})
        for field in RANKING_FIELDS:
            if field not in record:
                missing_ranking.append({"record_index": index, "record_id": record_id, "field": field})
        for field in SAFETY_LOCK_FIELDS:
            if field not in record:
                missing_safety.append({"record_index": index, "record_id": record_id, "field": field})
        for field in TRUE_LOCK_FIELDS:
            if record.get(field) is not True:
                missing_safety.append({"record_index": index, "record_id": record_id, "field": field, "expected": True})
        for field in FALSE_LOCK_FIELDS:
            if record.get(field) is not False:
                missing_safety.append({"record_index": index, "record_id": record_id, "field": field, "expected": False})
        if record.get("author_action_required") is not True:
            author_action_failures.append({"record_index": index, "record_id": record_id})
        for path in _forbidden_paths(record):
            forbidden_hits.append({"record_index": index, "record_id": record_id, "field_path": path})

    required_guidance_ok = not missing_required and not missing_ranking and bool(records)
    forbidden_absent = not forbidden_hits
    author_action_ok = not author_action_failures and bool(records)
    safety_locks_ok = not missing_safety and bool(records)

    manifest: dict[str, Any] = {
        "contract": CONTRACT,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_breathing_map": str(breathing_map_file),
        "manifest_path": str(manifest_file),
        "MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE": bool(
            breathing_map_file.exists()
            and not read_errors
            and required_guidance_ok
            and forbidden_absent
            and author_action_ok
            and safety_locks_ok
        ),
        "BREATHING_MAP_FOUND": breathing_map_file.exists(),
        "RECORDS_READ": len(records),
        "REQUIRED_GUIDANCE_FIELDS_PRESENT": required_guidance_ok,
        "PRESSURE_RANKING_FIELDS_PRESENT": not missing_ranking and bool(records),
        "FORBIDDEN_REWRITE_FIELDS_ABSENT": forbidden_absent,
        "AUTHOR_ACTION_REQUIRED_TRUE": author_action_ok,
        "SAFETY_LOCKS_PRESENT": safety_locks_ok,
        "CANON_WRITTEN": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "ACCEPTED_LORE_PACKET_CREATED": False,
        "ZONJ_COMPILED": False,
        "GODOT_TOUCHED": False,
        "RUNTIME_TOUCHED": False,
        "read_errors_count": len(read_errors),
        "read_errors": read_errors[:100],
        "missing_required_fields_count": len(missing_required),
        "missing_required_fields": missing_required[:100],
        "missing_ranking_fields_count": len(missing_ranking),
        "missing_ranking_fields": missing_ranking[:100],
        "missing_safety_locks_count": len(missing_safety),
        "missing_safety_locks": missing_safety[:100],
        "author_action_failures_count": len(author_action_failures),
        "author_action_failures": author_action_failures[:100],
        "forbidden_rewrite_fields_count": len(forbidden_hits),
        "forbidden_rewrite_fields": forbidden_hits[:100],
        "errors": [] if not read_errors else ["breathing map JSONL read errors"],
        "errors_count": 0 if not read_errors else 1,
    }
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def run_revision_breathing_map_guidance_gate(
    engain_dir: Path | str | None = None,
    engain_manifest_path: Path | str | None = None,
    breathing_map_path: Path | str | None = None,
) -> dict[str, Any]:
    paths = default_paths(
        Path(engain_manifest_path) if engain_manifest_path is not None else None,
        Path(engain_dir) if engain_dir is not None else None,
    )
    return run_guidance_gate(breathing_map_path or paths["breathing_map"], paths["manifest"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MrLore revision breathing map guidance records.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--breathing-map", default=None, help="Path to breathing_map.jsonl.")
    parser.add_argument("--output-manifest", default=None, help="Path to output guidance gate manifest.")
    args = parser.parse_args()

    try:
        paths = default_paths(
            Path(args.manifest) if args.manifest else None,
            Path(args.engain_dir) if args.engain_dir else None,
        )
        manifest = run_guidance_gate(
            args.breathing_map or paths["breathing_map"],
            args.output_manifest or paths["manifest"],
        )
    except Exception as exc:  # pragma: no cover - CLI guardrail
        print(f"MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_ERROR: {exc}")
        return 1
    print(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if manifest.get("MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE") else 1


if __name__ == "__main__":
    raise SystemExit(main())
