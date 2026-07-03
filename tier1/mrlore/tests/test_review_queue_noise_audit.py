from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_review_queue_noise_audit import run_review_queue_noise_audit


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _queue_item(queue_id: str, subject: str, claim_domain: str = "entity") -> dict:
    return {
        "queue_id": queue_id,
        "candidate_id": f"candidate.{queue_id}",
        "priority_bucket": "P0",
        "claim_domain": claim_domain,
        "subject": subject,
        "predicate": "present_in" if claim_domain == "entity" else "boundary_hints",
        "objects": ["scene.demo.a", "scene.demo.b"],
        "source_scenes": ["scene.demo.a"],
        "status": "REVIEW_QUEUED",
        "resolved": False,
        "claim_promoted": False,
        "claim_rejected": False,
        "canon_written": False,
    }


def test_review_queue_noise_audit_flags_stopword_and_too_short_subjects_without_altering_queue(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue.jsonl"
    _write_jsonl(
        queue_path,
        [
            _queue_item("q001", "About"),
            _queue_item("q002", "in"),
            _queue_item("q003", "Geralt"),
            _queue_item("q004", "The Last Door"),
            _queue_item("q005", "Acceptance"),
        ],
    )
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_review_queue_noise_audit(queue_path)

    assert manifest["MRLORE_REVIEW_QUEUE_NOISE_AUDIT_COMPLETE"] is True
    assert manifest["QUEUE_ITEMS_READ"] == 5
    assert manifest["NOISE_FLAGS_WRITTEN"] == 4
    assert manifest["QUEUE_ITEMS_ALTERED"] is False
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert queue_path.read_text(encoding="utf-8") == before_queue

    flags_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue_noise_flags.jsonl"
    flags = [json.loads(line) for line in flags_path.read_text(encoding="utf-8").splitlines()]
    assert [flag["queue_id"] for flag in flags] == ["q001", "q002", "q004", "q005"]
    reasons = {flag["queue_id"]: flag["noise_reasons"] for flag in flags}
    assert "common_word_or_sentence_starter" in reasons["q001"]
    assert "too_short_token" in reasons["q002"]
    assert "starts_with_stopword" in reasons["q004"]
    assert "abstract_sentence_starter" in reasons["q005"]
    assert all(flag["status"] == "NOISE_REVIEW_FLAGGED" for flag in flags)
    assert all(flag["claim_rejected"] is False for flag in flags)

    manifest_path = engain_dir / "manifests" / "review_queue_noise_audit_manifest.json"
    assert manifest_path.exists()
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["NOISE_FLAGS_WRITTEN"] == 4


def test_review_queue_noise_audit_records_read_errors_without_rejecting_claims(tmp_path: Path) -> None:
    queue_path = tmp_path / ".engain" / "mrlore" / "review" / "contradiction_review_queue.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(json.dumps(_queue_item("q001", "About")) + "\n{bad json\n", encoding="utf-8")

    manifest = run_review_queue_noise_audit(queue_path)

    assert manifest["MRLORE_REVIEW_QUEUE_NOISE_AUDIT_COMPLETE"] is False
    assert manifest["QUEUE_ITEMS_READ"] == 1
    assert manifest["NOISE_FLAGS_WRITTEN"] == 1
    assert manifest["read_errors_count"] == 1
    assert manifest["QUEUE_ITEMS_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
