#!/usr/bin/env python3
"""
mrlore_manual_review_decision_example_writer.py — write synthetic manual review examples.

PURPOSE:
    Write manual_review_decisions.example.jsonl as a safe template only, validate
    every example against manual_review_decisions.schema.json, and prove decision
    files can exist without authority effect.

INPUT:
    vault/.engain/mrlore/review/manual_review_decisions.schema.json

OUTPUTS:
    vault/.engain/mrlore/review/manual_review_decisions.example.jsonl
    vault/.engain/manifests/manual_review_decision_example_manifest.json

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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tier1.mrlore.mrlore_manual_review_decision_schema import (
    ALLOWED_DECISION_STATUSES,
    default_engain_dir,
    validate_manual_review_decision_record,
)

_STATUS_REASONS = {
    "CONFIRM": "Synthetic example: reviewer thinks this queued item is valid enough for later promotion review; no promotion is applied.",
    "REJECT_AS_NOISE": "Synthetic example: reviewer thinks this queued item is extraction noise; no claim rejection authority is applied.",
    "SUSPEND": "Synthetic example: reviewer cannot decide yet; no contradiction is resolved.",
    "NEEDS_SOURCE_REVIEW": "Synthetic example: reviewer needs source scene inspection; no source packet or claim status is changed.",
}


def _example_record(decision_status: str, sequence: int) -> dict[str, Any]:
    queue_id = f"review_queue.p0.{sequence:04d}"
    candidate_id = "contradiction_candidate.e0610c8ab1793e7835d46ceb"
    return {
        "decision_id": f"manual_review_decision.{queue_id}.001",
        "queue_id": queue_id,
        "candidate_id": candidate_id,
        "reviewer_id": "synthetic_example_reviewer",
        "decision_status": decision_status,
        "decision_reason": _STATUS_REASONS[decision_status],
        "source_review_notes": "Synthetic template only; not a real review decision.",
        "reviewed_at": None,
        "SOURCE_SCENES": [f"synthetic.scene.{sequence:04d}"],
        "claim_refs": [
            {
                "claim_id": f"claim.synthetic.{sequence:04d}",
                "SOURCE_SCENE": f"synthetic.scene.{sequence:04d}",
                "source_line": None,
            }
        ],
        "candidate_ref": candidate_id,
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


def build_example_manual_review_decisions() -> list[dict[str, Any]]:
    return [_example_record(status, index) for index, status in enumerate(ALLOWED_DECISION_STATUSES, 1)]


def _empty_manifest(engain_dir: Path, schema_path: Path, example_path: Path, manifest_path: Path) -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_manual_review_decision_example_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "engain_dir": str(engain_dir),
        "source_schema_path": str(schema_path),
        "example_decisions_jsonl_path": str(example_path),
        "manifest_path": str(manifest_path),
        "MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE": False,
        "SCHEMA_FOUND": False,
        "EXAMPLE_DECISIONS_WRITTEN": 0,
        "EXAMPLE_DECISIONS_VALIDATED": False,
        "SYNTHETIC_EXAMPLES_ONLY": True,
        "REAL_DECISIONS_CREATED": False,
        "CLAIMS_PROMOTED": False,
        "CLAIM_REJECTION_AUTHORITY_APPLIED": False,
        "CANON_WRITTEN": False,
        "ACCEPTED_LORE_PACKET_EXISTS": False,
        "CONTRADICTIONS_RESOLVED": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "validation_failures": [],
        "errors": [],
    }


def run_manual_review_decision_example_writer(
    engain_dir: Path | str | None = None,
    manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    resolved_engain_dir = (
        Path(engain_dir).resolve()
        if engain_dir is not None
        else default_engain_dir(Path(manifest_path) if manifest_path else None).resolve()
    )
    review_dir = resolved_engain_dir / "mrlore" / "review"
    manifests_dir = resolved_engain_dir / "manifests"
    schema_path = review_dir / "manual_review_decisions.schema.json"
    example_path = review_dir / "manual_review_decisions.example.jsonl"
    out_manifest_path = manifests_dir / "manual_review_decision_example_manifest.json"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    manifest = _empty_manifest(resolved_engain_dir, schema_path, example_path, out_manifest_path)
    if not schema_path.exists():
        manifest["errors"] = [f"manual review decision schema not found: {schema_path}"]
        out_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    manifest["SCHEMA_FOUND"] = True
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    examples = build_example_manual_review_decisions()
    validation_failures = [
        {
            "decision_id": example.get("decision_id"),
            "decision_status": example.get("decision_status"),
            "errors": errors,
        }
        for example in examples
        if (errors := validate_manual_review_decision_record(example, schema))
    ]

    if validation_failures:
        manifest["validation_failures"] = validation_failures
        manifest["errors"] = ["one or more synthetic example decisions failed schema validation"]
        out_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    review_dir.mkdir(parents=True, exist_ok=True)
    example_path.write_text(
        "".join(json.dumps(example, ensure_ascii=False, sort_keys=True) + "\n" for example in examples),
        encoding="utf-8",
    )

    manifest.update(
        {
            "MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE": True,
            "EXAMPLE_DECISIONS_WRITTEN": len(examples),
            "EXAMPLE_DECISIONS_VALIDATED": True,
            "allowed_decision_statuses": list(ALLOWED_DECISION_STATUSES),
            "example_policy": "synthetic template records only; not real review decisions and no authority effect",
        }
    )
    out_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Write synthetic MrLore manual review decision examples only.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    args = parser.parse_args()

    try:
        manifest = run_manual_review_decision_example_writer(
            engain_dir=Path(args.engain_dir) if args.engain_dir else None,
            manifest_path=Path(args.manifest) if args.manifest else None,
        )
    except Exception as exc:
        print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[MANUAL_REVIEW_DECISION_EXAMPLE] "
        f"MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE={manifest['MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE']}"
    )
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] SCHEMA_FOUND={manifest['SCHEMA_FOUND']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] EXAMPLE_DECISIONS_WRITTEN={manifest['EXAMPLE_DECISIONS_WRITTEN']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] EXAMPLE_DECISIONS_VALIDATED={manifest['EXAMPLE_DECISIONS_VALIDATED']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] SYNTHETIC_EXAMPLES_ONLY={manifest['SYNTHETIC_EXAMPLES_ONLY']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] REAL_DECISIONS_CREATED={manifest['REAL_DECISIONS_CREATED']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] CLAIMS_PROMOTED={manifest['CLAIMS_PROMOTED']}")
    print(
        "[MANUAL_REVIEW_DECISION_EXAMPLE] "
        f"CLAIM_REJECTION_AUTHORITY_APPLIED={manifest['CLAIM_REJECTION_AUTHORITY_APPLIED']}"
    )
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(
        "[MANUAL_REVIEW_DECISION_EXAMPLE] "
        f"ACCEPTED_LORE_PACKET_EXISTS={manifest['ACCEPTED_LORE_PACKET_EXISTS']}"
    )
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] CONTRADICTIONS_RESOLVED={manifest['CONTRADICTIONS_RESOLVED']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] EXAMPLES={manifest['example_decisions_jsonl_path']}")
    print(f"[MANUAL_REVIEW_DECISION_EXAMPLE] MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
