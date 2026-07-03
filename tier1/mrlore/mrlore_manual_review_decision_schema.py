#!/usr/bin/env python3
"""
mrlore_manual_review_decision_schema.py — define manual review decision vocabulary.

PURPOSE:
    Build the schema for future manual/review-agent decision artifacts and prove
    example records validate against it.

OUTPUTS:
    vault/.engain/mrlore/review/manual_review_decisions.schema.json
    vault/.engain/manifests/manual_review_decision_schema_manifest.json

DOES NOT:
    create real decisions
    apply review decisions
    promote claims
    reject claims with authority
    create accepted lore packets
    resolve contradictions
    write canon
    compile ZONJ
    touch Godot/runtime
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_DECISION_STATUSES = (
    "CONFIRM",
    "REJECT_AS_NOISE",
    "SUSPEND",
    "NEEDS_SOURCE_REVIEW",
)

REQUIRED_FIELDS = (
    "decision_id",
    "queue_id",
    "candidate_id",
    "reviewer_id",
    "decision_status",
    "decision_reason",
    "source_review_notes",
    "reviewed_at",
    "SOURCE_SCENES",
    "claim_refs",
    "candidate_ref",
    "review_scope",
    "authority_effect",
    "promotion_allowed",
    "claims_promoted",
    "claim_rejection_authority_applied",
    "canon_written",
    "accepted_lore_packet_exists",
    "contradictions_resolved",
    "runtime_touched",
    "godot_touched",
    "zonj_compiled",
)

_FALSE_AUTHORITY_FIELDS = (
    "promotion_allowed",
    "claims_promoted",
    "claim_rejection_authority_applied",
    "canon_written",
    "accepted_lore_packet_exists",
    "contradictions_resolved",
    "runtime_touched",
    "godot_touched",
    "zonj_compiled",
)

_STATUS_MEANINGS = {
    "CONFIRM": "Reviewer thinks the queued item is valid enough for later promotion review. It does not promote.",
    "REJECT_AS_NOISE": "Reviewer thinks the queued item is extraction/review noise. It does not reject the underlying claim with authority.",
    "SUSPEND": "Reviewer cannot decide yet. It does not resolve contradiction.",
    "NEEDS_SOURCE_REVIEW": "Reviewer needs to inspect source scenes. It does not change claim status.",
}

_ISO_8601_OR_NULL_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"


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


def default_engain_dir(manifest_path: Path | None = None) -> Path:
    return _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())


def build_manual_review_decision_schema() -> dict[str, Any]:
    bool_false_property = {"type": "boolean", "const": False}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "engain.mrlore_manual_review_decision.schema.v1",
        "title": "MrLore Manual Review Decision Schema",
        "description": (
            "manual review decisions are review artifacts only; they do not promote claims, reject claims "
            "with authority, create accepted lore, resolve contradictions, write canon, compile ZONJ, touch "
            "Godot, or touch runtime"
        ),
        "type": "object",
        "additionalProperties": False,
        "required": list(REQUIRED_FIELDS),
        "properties": {
            "decision_id": {"type": "string", "pattern": r"^manual_review_decision\.review_queue\.[a-z0-9]+\.\d{4}\.\d{3}$"},
            "queue_id": {"type": "string", "pattern": r"^review_queue\.[a-z0-9]+\.\d{4}$"},
            "candidate_id": {"type": "string", "pattern": r"^contradiction_candidate\.[a-f0-9]{24}$"},
            "reviewer_id": {"type": "string", "minLength": 1},
            "decision_status": {
                "type": "string",
                "enum": list(ALLOWED_DECISION_STATUSES),
                "description": "Allowed manual-review vocabulary only. No status applies authority by itself.",
                "status_meanings": _STATUS_MEANINGS,
            },
            "decision_reason": {"type": "string", "minLength": 1},
            "source_review_notes": {"type": "string"},
            "reviewed_at": {
                "anyOf": [
                    {"type": "string", "format": "date-time"},
                    {"type": "null"},
                ],
                "description": "ISO 8601 timestamp or null while drafting/reviewing.",
            },
            "SOURCE_SCENES": {"type": "array", "items": {"type": "string"}},
            "claim_refs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "claim_id": {"type": "string"},
                        "SOURCE_SCENE": {"type": "string"},
                        "source_line": {"type": ["integer", "null"]},
                    },
                },
            },
            "candidate_ref": {"type": "string", "pattern": r"^contradiction_candidate\.[a-f0-9]{24}$"},
            "review_scope": {"type": "string", "const": "MANUAL_REVIEW_ONLY"},
            "authority_effect": {"type": "string", "const": "NONE"},
            "promotion_allowed": bool_false_property,
            "claims_promoted": bool_false_property,
            "claim_rejection_authority_applied": bool_false_property,
            "canon_written": bool_false_property,
            "accepted_lore_packet_exists": bool_false_property,
            "contradictions_resolved": bool_false_property,
            "runtime_touched": bool_false_property,
            "godot_touched": bool_false_property,
            "zonj_compiled": bool_false_property,
        },
        "decision_status_lock": _STATUS_MEANINGS,
        "locks": [
            "Manual review decisions are review artifacts only.",
            "Manual review decisions do not promote claims.",
            "REJECT_AS_NOISE does not apply claim rejection authority.",
            "CONFIRM does not create accepted lore.",
            "SUSPEND does not resolve contradiction.",
            "NEEDS_SOURCE_REVIEW does not mutate source packets.",
            "Accepted lore packets remain impossible until a separate promotion gate exists and passes.",
        ],
    }


def _example_record(decision_status: str, sequence: int) -> dict[str, Any]:
    return {
        "decision_id": f"manual_review_decision.review_queue.p0.0006.{sequence:03d}",
        "queue_id": "review_queue.p0.0006",
        "candidate_id": "contradiction_candidate.e0610c8ab1793e7835d46ceb",
        "reviewer_id": "human_or_review_agent_id",
        "decision_status": decision_status,
        "decision_reason": _STATUS_MEANINGS[decision_status],
        "source_review_notes": "",
        "reviewed_at": None,
        "SOURCE_SCENES": [],
        "claim_refs": [],
        "candidate_ref": "contradiction_candidate.e0610c8ab1793e7835d46ceb",
        "review_scope": "MANUAL_REVIEW_ONLY",
        "authority_effect": "NONE",
        "promotion_allowed": False,
        "claims_promoted": False,
        "claim_rejection_authority_applied": False,
        "canon_written": False,
        "accepted_lore_packet_exists": False,
        "contradictions_resolved": False,
        "runtime_touched": False,
        "godot_touched": False,
        "zonj_compiled": False,
    }


def example_manual_review_decisions() -> list[dict[str, Any]]:
    return [_example_record(status, index) for index, status in enumerate(ALLOWED_DECISION_STATUSES, 1)]


def validate_manual_review_decision_record(record: Any, schema: dict[str, Any] | None = None) -> list[str]:
    _ = schema or build_manual_review_decision_schema()
    if not isinstance(record, dict):
        return ["record must be a JSON object"]

    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"missing required field: {field}")

    status = record.get("decision_status")
    if status not in ALLOWED_DECISION_STATUSES:
        errors.append(f"decision_status is not allowed: {status}")

    if record.get("review_scope") != "MANUAL_REVIEW_ONLY":
        errors.append("review_scope must be MANUAL_REVIEW_ONLY")
    if record.get("authority_effect") != "NONE":
        errors.append("authority_effect must be NONE")

    for field in _FALSE_AUTHORITY_FIELDS:
        if record.get(field) is not False:
            errors.append(f"{field} must be false")

    for field in ("decision_id", "queue_id", "candidate_id", "reviewer_id", "decision_reason", "candidate_ref"):
        if field in record and not isinstance(record[field], str):
            errors.append(f"{field} must be a string")
        elif field in record and not record[field].strip():
            errors.append(f"{field} must be non-empty")

    if record.get("reviewed_at") is not None:
        reviewed_at = record.get("reviewed_at")
        if not isinstance(reviewed_at, str) or not re.match(_ISO_8601_OR_NULL_PATTERN, reviewed_at):
            errors.append("reviewed_at must be ISO 8601 timestamp or null")

    if "SOURCE_SCENES" in record and not isinstance(record["SOURCE_SCENES"], list):
        errors.append("SOURCE_SCENES must be an array")
    if "claim_refs" in record and not isinstance(record["claim_refs"], list):
        errors.append("claim_refs must be an array")

    if record.get("candidate_ref") != record.get("candidate_id"):
        errors.append("candidate_ref must match candidate_id")

    return errors


def run_manual_review_decision_schema(engain_dir: Path | str | None = None, manifest_path: Path | str | None = None) -> dict[str, Any]:
    resolved_engain_dir = Path(engain_dir).resolve() if engain_dir is not None else default_engain_dir(Path(manifest_path) if manifest_path else None).resolve()
    schema_path = resolved_engain_dir / "mrlore" / "review" / "manual_review_decisions.schema.json"
    out_manifest_path = resolved_engain_dir / "manifests" / "manual_review_decision_schema_manifest.json"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    out_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    schema = build_manual_review_decision_schema()
    examples = example_manual_review_decisions()
    validation_failures = [
        {"decision_status": example.get("decision_status"), "errors": errors}
        for example in examples
        if (errors := validate_manual_review_decision_record(example, schema))
    ]

    schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    complete = len(validation_failures) == 0
    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_manual_review_decision_schema_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_path": str(schema_path),
        "manifest_path": str(out_manifest_path),
        "MRLORE_MANUAL_REVIEW_DECISION_SCHEMA_COMPLETE": complete,
        "SCHEMA_WRITTEN": True,
        "EXAMPLE_DECISIONS_VALIDATED": complete,
        "ALLOWED_DECISION_STATUSES": list(ALLOWED_DECISION_STATUSES),
        "REQUIRED_FIELDS": list(REQUIRED_FIELDS),
        "REAL_DECISIONS_CREATED": False,
        "CLAIMS_READ_AS_AUTHORITY": False,
        "CLAIMS_PROMOTED": False,
        "CLAIM_REJECTION_AUTHORITY_APPLIED": False,
        "CANON_WRITTEN": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "CONTRADICTIONS_RESOLVED": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "locks": schema["locks"],
        "example_validation_failures": validation_failures,
        "errors": ["one or more internal example records failed schema proof"] if validation_failures else [],
    }
    out_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore manual review decision schema proof — no decision writer.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    args = parser.parse_args()

    try:
        manifest = run_manual_review_decision_schema(
            engain_dir=Path(args.engain_dir) if args.engain_dir else None,
            manifest_path=Path(args.manifest) if args.manifest else None,
        )
    except Exception as exc:
        print(f"[MANUAL_REVIEW_DECISION_SCHEMA] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[MANUAL_REVIEW_DECISION_SCHEMA] "
        f"MRLORE_MANUAL_REVIEW_DECISION_SCHEMA_COMPLETE={manifest['MRLORE_MANUAL_REVIEW_DECISION_SCHEMA_COMPLETE']}"
    )
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] SCHEMA_WRITTEN={manifest['SCHEMA_WRITTEN']}")
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] EXAMPLE_DECISIONS_VALIDATED={manifest['EXAMPLE_DECISIONS_VALIDATED']}")
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(
        "[MANUAL_REVIEW_DECISION_SCHEMA] "
        f"CLAIM_REJECTION_AUTHORITY_APPLIED={manifest['CLAIM_REJECTION_AUTHORITY_APPLIED']}"
    )
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(
        "[MANUAL_REVIEW_DECISION_SCHEMA] "
        f"ACCEPTED_LORE_PACKET_EXISTS={manifest['ACCEPTED_LORE_PACKET_EXISTS']}"
    )
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] SCHEMA={manifest['schema_path']}")
    print(f"[MANUAL_REVIEW_DECISION_SCHEMA] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_MANUAL_REVIEW_DECISION_SCHEMA_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
