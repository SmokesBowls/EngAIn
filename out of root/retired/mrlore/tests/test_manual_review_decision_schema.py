from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_manual_review_decision_schema import (
    ALLOWED_DECISION_STATUSES,
    build_manual_review_decision_schema,
    run_manual_review_decision_schema,
    validate_manual_review_decision_record,
)


def test_schema_file_contains_allowed_decision_statuses(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"

    manifest = run_manual_review_decision_schema(engain_dir=engain_dir)

    assert manifest["MRLORE_MANUAL_REVIEW_DECISION_SCHEMA_COMPLETE"] is True
    assert manifest["SCHEMA_WRITTEN"] is True
    assert manifest["EXAMPLE_DECISIONS_VALIDATED"] is True
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIM_REJECTION_AUTHORITY_APPLIED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["ACCEPTED_LORE_PACKET_EXISTS"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False

    schema_path = engain_dir / "mrlore" / "review" / "manual_review_decisions.schema.json"
    manifest_path = engain_dir / "manifests" / "manual_review_decision_schema_manifest.json"
    assert schema_path.exists()
    assert manifest_path.exists()

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["properties"]["decision_status"]["enum"] == list(ALLOWED_DECISION_STATUSES)
    assert schema["properties"]["review_scope"]["const"] == "MANUAL_REVIEW_ONLY"
    assert schema["properties"]["authority_effect"]["const"] == "NONE"
    assert "manual review decisions are review artifacts only" in schema["description"]


def test_schema_requires_no_authority_effect() -> None:
    schema = build_manual_review_decision_schema()
    valid_record = {
        "decision_id": "manual_review_decision.review_queue.p0.0006.001",
        "queue_id": "review_queue.p0.0006",
        "candidate_id": "contradiction_candidate.e0610c8ab1793e7835d46ceb",
        "reviewer_id": "human_or_review_agent_id",
        "decision_status": "SUSPEND",
        "decision_reason": "Needs source scene inspection before any authority decision.",
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

    assert validate_manual_review_decision_record(valid_record, schema) == []

    promoted = dict(valid_record)
    promoted["promotion_allowed"] = True
    assert "promotion_allowed must be false" in validate_manual_review_decision_record(promoted, schema)

    authority = dict(valid_record)
    authority["authority_effect"] = "PROMOTE"
    assert "authority_effect must be NONE" in validate_manual_review_decision_record(authority, schema)

    rejected = dict(valid_record)
    rejected["decision_status"] = "REJECT_AND_DELETE"
    assert "decision_status is not allowed: REJECT_AND_DELETE" in validate_manual_review_decision_record(rejected, schema)
