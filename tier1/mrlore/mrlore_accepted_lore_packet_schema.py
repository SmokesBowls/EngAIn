#!/usr/bin/env python3
"""
mrlore_accepted_lore_packet_schema.py — define accepted lore packet shape only.

PURPOSE:
    Build the schema for future accepted-lore packet artifacts and prove
    schema-local example records validate against it.

OUTPUTS:
    vault/.engain/mrlore/accepted/accepted_lore_packet.schema.json
    vault/.engain/manifests/accepted_lore_packet_schema_manifest.json

DOES NOT:
    create real accepted lore packets
    promote claims
    reject claims
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

REQUIRED_FIELDS = (
    "packet_id",
    "packet_type",
    "lore_status",
    "claim_id",
    "claim_domain",
    "claim_type",
    "subject",
    "predicate",
    "object",
    "SOURCE_SCENES",
    "source_claim_refs",
    "review_decision_refs",
    "accepted_by",
    "accepted_at",
    "authority_scope",
    "canon_write_allowed",
    "runtime_mutation_allowed",
    "godot_mutation_allowed",
    "zonj_compile_allowed",
    "promotion_gate_passed",
    "notes",
)

_FALSE_AUTHORITY_FIELDS = (
    "canon_write_allowed",
    "runtime_mutation_allowed",
    "godot_mutation_allowed",
    "zonj_compile_allowed",
    "promotion_gate_passed",
)

_STRING_FIELDS = (
    "packet_id",
    "packet_type",
    "lore_status",
    "claim_id",
    "claim_domain",
    "claim_type",
    "subject",
    "predicate",
    "object",
    "accepted_by",
    "authority_scope",
    "notes",
)

_ISO_8601_OR_NULL_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"

LOCKS = (
    "Accepted Lore Packet schema defines the shape of accepted lore.",
    "Schema creation does not create real accepted lore packets.",
    "accepted lore is not canon file writing.",
    "accepted lore is not Godot/runtime mutation.",
    "accepted lore is not ZONJ compilation.",
    "Real accepted packets require a later promotion gate.",
    "passroom may eventually consume accepted lore packets, but only after that contract is built.",
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


def default_engain_dir(manifest_path: Path | None = None) -> Path:
    return _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())


def build_accepted_lore_packet_schema() -> dict[str, Any]:
    bool_false_property = {"type": "boolean", "const": False}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "engain.mrlore_accepted_lore_packet.schema.v1",
        "title": "MrLore Accepted Lore Packet Schema",
        "description": (
            "accepted lore packets record lore truth inside MrLore only; they do not write canon, compile ZONJ, "
            "mutate Godot, touch runtime, or become passroom input until separate gates/contracts allow it"
        ),
        "type": "object",
        "additionalProperties": False,
        "required": list(REQUIRED_FIELDS),
        "properties": {
            "packet_id": {"type": "string", "pattern": r"^accepted_lore_packet\.[a-z0-9_]+\.\d{4}$"},
            "packet_type": {"type": "string", "const": "ACCEPTED_LORE_PACKET"},
            "lore_status": {"type": "string", "const": "ACCEPTED"},
            "claim_id": {"type": "string", "minLength": 1},
            "claim_domain": {"type": "string", "enum": ["entity", "environment"]},
            "claim_type": {"type": "string", "minLength": 1},
            "subject": {"type": "string", "minLength": 1},
            "predicate": {"type": "string", "minLength": 1},
            "object": {"type": "string", "minLength": 1},
            "SOURCE_SCENES": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
            "source_claim_refs": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
            "review_decision_refs": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "accepted_by": {"type": "string", "const": "MANUAL_OR_GATE_AUTHORITY_REQUIRED"},
            "accepted_at": {
                "anyOf": [
                    {"type": "string", "format": "date-time"},
                    {"type": "null"},
                ],
                "description": "ISO 8601 timestamp or null in schema/example phase.",
            },
            "authority_scope": {"type": "string", "const": "LORE_ONLY"},
            "canon_write_allowed": bool_false_property,
            "runtime_mutation_allowed": bool_false_property,
            "godot_mutation_allowed": bool_false_property,
            "zonj_compile_allowed": bool_false_property,
            "promotion_gate_passed": bool_false_property,
            "notes": {"type": "string"},
        },
        "locks": list(LOCKS),
        "authority_scope_lock": {
            "LORE_ONLY": "Accepted inside MrLore lore review space only. Not canon, runtime, Godot, ZONJ, or passroom authority."
        },
    }


def example_accepted_lore_packets() -> list[dict[str, Any]]:
    claim_id = "claim.scene.book001.001_the_ethereal_vigil.scene001.entity.0001"
    scene_id = "scene.book001.001_the_ethereal_vigil.scene001"
    return [
        {
            "packet_id": "accepted_lore_packet.example.0001",
            "packet_type": "ACCEPTED_LORE_PACKET",
            "lore_status": "ACCEPTED",
            "claim_id": claim_id,
            "claim_domain": "entity",
            "claim_type": "entity_presence",
            "subject": "Aeon Keeper",
            "predicate": "present_in",
            "object": scene_id,
            "SOURCE_SCENES": [scene_id],
            "source_claim_refs": [claim_id],
            "review_decision_refs": [],
            "accepted_by": "MANUAL_OR_GATE_AUTHORITY_REQUIRED",
            "accepted_at": None,
            "authority_scope": "LORE_ONLY",
            "canon_write_allowed": False,
            "runtime_mutation_allowed": False,
            "godot_mutation_allowed": False,
            "zonj_compile_allowed": False,
            "promotion_gate_passed": False,
            "notes": "",
        }
    ]


def validate_accepted_lore_packet_record(record: Any, schema: dict[str, Any] | None = None) -> list[str]:
    _ = schema or build_accepted_lore_packet_schema()
    if not isinstance(record, dict):
        return ["record must be a JSON object"]

    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"missing required field: {field}")

    for field in _STRING_FIELDS:
        if field in record and not isinstance(record[field], str):
            errors.append(f"{field} must be a string")
        elif field in record and field != "notes" and not record[field].strip():
            errors.append(f"{field} must be non-empty")

    if record.get("packet_type") != "ACCEPTED_LORE_PACKET":
        errors.append("packet_type must be ACCEPTED_LORE_PACKET")
    if record.get("lore_status") != "ACCEPTED":
        errors.append("lore_status must be ACCEPTED")
    if record.get("authority_scope") != "LORE_ONLY":
        errors.append("authority_scope must be LORE_ONLY")
    if record.get("accepted_by") != "MANUAL_OR_GATE_AUTHORITY_REQUIRED":
        errors.append("accepted_by must be MANUAL_OR_GATE_AUTHORITY_REQUIRED")

    for field in _FALSE_AUTHORITY_FIELDS:
        if record.get(field) is not False:
            if field == "promotion_gate_passed":
                errors.append("promotion_gate_passed must be false for schema-only phase")
            else:
                errors.append(f"{field} must be false")

    if "SOURCE_SCENES" in record:
        if not isinstance(record["SOURCE_SCENES"], list):
            errors.append("SOURCE_SCENES must be an array")
        elif not record["SOURCE_SCENES"]:
            errors.append("SOURCE_SCENES must contain at least one source scene")
        elif any(not isinstance(item, str) or not item.strip() for item in record["SOURCE_SCENES"]):
            errors.append("SOURCE_SCENES entries must be non-empty strings")

    if "source_claim_refs" in record:
        if not isinstance(record["source_claim_refs"], list):
            errors.append("source_claim_refs must be an array")
        elif not record["source_claim_refs"]:
            errors.append("source_claim_refs must contain at least one claim ref")
        elif any(not isinstance(item, str) or not item.strip() for item in record["source_claim_refs"]):
            errors.append("source_claim_refs entries must be non-empty strings")

    if "review_decision_refs" in record:
        if not isinstance(record["review_decision_refs"], list):
            errors.append("review_decision_refs must be an array")
        elif any(not isinstance(item, str) or not item.strip() for item in record["review_decision_refs"]):
            errors.append("review_decision_refs entries must be non-empty strings")

    accepted_at = record.get("accepted_at")
    if accepted_at is not None:
        if not isinstance(accepted_at, str) or not re.match(_ISO_8601_OR_NULL_PATTERN, accepted_at):
            errors.append("accepted_at must be ISO 8601 timestamp or null")

    claim_id = record.get("claim_id")
    source_claim_refs = record.get("source_claim_refs")
    if isinstance(claim_id, str) and isinstance(source_claim_refs, list) and claim_id not in source_claim_refs:
        errors.append("source_claim_refs must include claim_id")

    return errors


def run_accepted_lore_packet_schema(engain_dir: Path | str | None = None, manifest_path: Path | str | None = None) -> dict[str, Any]:
    resolved_engain_dir = Path(engain_dir).resolve() if engain_dir is not None else default_engain_dir(Path(manifest_path) if manifest_path else None).resolve()
    schema_path = resolved_engain_dir / "mrlore" / "accepted" / "accepted_lore_packet.schema.json"
    out_manifest_path = resolved_engain_dir / "manifests" / "accepted_lore_packet_schema_manifest.json"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    out_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    schema = build_accepted_lore_packet_schema()
    examples = example_accepted_lore_packets()
    validation_failures = [
        {"packet_id": example.get("packet_id"), "errors": errors}
        for example in examples
        if (errors := validate_accepted_lore_packet_record(example, schema))
    ]

    schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    complete = len(validation_failures) == 0
    manifest: dict[str, Any] = {
        "contract": "engain.mrlore_accepted_lore_packet_schema_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_path": str(schema_path),
        "manifest_path": str(out_manifest_path),
        "MRLORE_ACCEPTED_LORE_PACKET_SCHEMA_COMPLETE": complete,
        "SCHEMA_WRITTEN": True,
        "EXAMPLE_PACKETS_VALIDATED": complete,
        "REQUIRED_FIELDS": list(REQUIRED_FIELDS),
        "REAL_ACCEPTED_LORE_PACKETS_CREATED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "PASSROOM_CONSUMPTION_ALLOWED": False,
        "PROMOTION_GATE_EXISTS": False,
        "locks": list(LOCKS),
        "example_validation_failures": validation_failures,
        "errors": ["one or more internal example packets failed schema proof"] if validation_failures else [],
    }
    out_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore accepted lore packet schema proof — no promotion runner.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    args = parser.parse_args()

    try:
        manifest = run_accepted_lore_packet_schema(
            engain_dir=Path(args.engain_dir) if args.engain_dir else None,
            manifest_path=Path(args.manifest) if args.manifest else None,
        )
    except Exception as exc:
        print(f"[ACCEPTED_LORE_PACKET_SCHEMA] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[ACCEPTED_LORE_PACKET_SCHEMA] "
        f"MRLORE_ACCEPTED_LORE_PACKET_SCHEMA_COMPLETE={manifest['MRLORE_ACCEPTED_LORE_PACKET_SCHEMA_COMPLETE']}"
    )
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] SCHEMA_WRITTEN={manifest['SCHEMA_WRITTEN']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] EXAMPLE_PACKETS_VALIDATED={manifest['EXAMPLE_PACKETS_VALIDATED']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] REAL_ACCEPTED_LORE_PACKETS_CREATED={manifest['REAL_ACCEPTED_LORE_PACKETS_CREATED']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] CLAIMS_REJECTED={manifest['CLAIMS_REJECTED']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] SCHEMA={manifest['schema_path']}")
    print(f"[ACCEPTED_LORE_PACKET_SCHEMA] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_ACCEPTED_LORE_PACKET_SCHEMA_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
