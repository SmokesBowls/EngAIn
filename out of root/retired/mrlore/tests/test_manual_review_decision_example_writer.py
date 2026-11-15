from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_manual_review_decision_example_writer import (
    run_manual_review_decision_example_writer,
)
from tier1.mrlore.mrlore_manual_review_decision_schema import (
    ALLOWED_DECISION_STATUSES,
    run_manual_review_decision_schema,
    validate_manual_review_decision_record,
)


def test_example_writer_writes_synthetic_examples_and_validates_against_schema(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    run_manual_review_decision_schema(engain_dir=engain_dir)

    manifest = run_manual_review_decision_example_writer(engain_dir=engain_dir)

    assert manifest["MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE"] is True
    assert manifest["EXAMPLE_DECISIONS_WRITTEN"] == len(ALLOWED_DECISION_STATUSES)
    assert manifest["EXAMPLE_DECISIONS_VALIDATED"] is True
    assert manifest["SYNTHETIC_EXAMPLES_ONLY"] is True
    assert manifest["REAL_DECISIONS_CREATED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIM_REJECTION_AUTHORITY_APPLIED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["ACCEPTED_LORE_PACKET_EXISTS"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False

    example_path = engain_dir / "mrlore" / "review" / "manual_review_decisions.example.jsonl"
    manifest_path = engain_dir / "manifests" / "manual_review_decision_example_manifest.json"
    assert example_path.exists()
    assert manifest_path.exists()

    examples = [json.loads(line) for line in example_path.read_text(encoding="utf-8").splitlines()]
    assert [record["decision_status"] for record in examples] == list(ALLOWED_DECISION_STATUSES)
    assert all("synthetic_example" not in record for record in examples)
    assert all(record["review_scope"] == "MANUAL_REVIEW_ONLY" for record in examples)
    assert all(record["authority_effect"] == "NONE" for record in examples)
    assert all(record["promotion_allowed"] is False for record in examples)
    assert all(record["claims_promoted"] is False for record in examples)
    assert all(record["claim_rejection_authority_applied"] is False for record in examples)
    assert all(record["canon_written"] is False for record in examples)
    assert all(record["accepted_lore_packet_exists"] is False for record in examples)
    assert all(record["contradictions_resolved"] is False for record in examples)

    schema = json.loads((engain_dir / "mrlore" / "review" / "manual_review_decisions.schema.json").read_text(encoding="utf-8"))
    for record in examples:
        assert validate_manual_review_decision_record(record, schema) == []


def test_example_writer_refuses_missing_schema_without_creating_examples(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"

    manifest = run_manual_review_decision_example_writer(engain_dir=engain_dir)

    assert manifest["MRLORE_MANUAL_REVIEW_DECISION_EXAMPLE_WRITER_COMPLETE"] is False
    assert manifest["SCHEMA_FOUND"] is False
    assert manifest["EXAMPLE_DECISIONS_WRITTEN"] == 0
    assert manifest["REAL_DECISIONS_CREATED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert not (engain_dir / "mrlore" / "review" / "manual_review_decisions.example.jsonl").exists()
