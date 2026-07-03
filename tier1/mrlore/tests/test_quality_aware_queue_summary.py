from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_quality_aware_queue_summary import run_quality_aware_queue_summary


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _queue_item(
    queue_id: str,
    bucket: str,
    subject: str,
    domain: str = "entity",
    reasons: list[str] | None = None,
    quality_flagged: bool = False,
) -> dict:
    return {
        "queue_id": queue_id,
        "priority_bucket": bucket,
        "candidate_id": f"candidate.{queue_id}",
        "claim_domain": domain,
        "subject": subject,
        "predicate": "present_in" if domain == "entity" else "terrain_family",
        "quality_reasons": reasons or [],
        "entity_quality_flagged": quality_flagged,
        "status": "QUALITY_AWARE_REVIEW_QUEUED",
        "candidate_altered": False,
        "claim_rejected": False,
        "claim_promoted": False,
        "contradiction_resolved": False,
        "canon_written": False,
    }


def test_quality_aware_queue_summary_counts_buckets_domains_reasons_and_top_subjects_without_mutation(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "quality_aware_contradiction_review_queue.jsonl"
    records = [
        _queue_item("q1", "P0_HIGH_CLAIM", "Marduk"),
        _queue_item("q2", "P0_HIGH_CLAIM", "Marduk"),
        _queue_item("q3", "P1_ENVIRONMENT", "scene.demo", "environment"),
        _queue_item("q4", "P9_ENTITY_QUALITY_FLAGGED", "About", reasons=["single_common_word"], quality_flagged=True),
        _queue_item("q5", "P9_ENTITY_QUALITY_FLAGGED", "About", reasons=["single_common_word", "too_short_token"], quality_flagged=True),
        _queue_item("q6", "P2_CLEAN_ENTITY", "Aldrin"),
    ]
    _write_jsonl(queue_path, records)
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_quality_aware_queue_summary(queue_path)

    assert manifest["MRLORE_QUALITY_AWARE_QUEUE_SUMMARY_COMPLETE"] is True
    assert manifest["QUEUE_ITEMS_READ"] == 6
    assert manifest["bucket_counts"] == {
        "P0_HIGH_CLAIM": 2,
        "P1_ENVIRONMENT": 1,
        "P2_CLEAN_ENTITY": 1,
        "P9_ENTITY_QUALITY_FLAGGED": 2,
    }
    assert manifest["domain_counts_by_bucket"]["P0_HIGH_CLAIM"] == {"entity": 2}
    assert manifest["domain_counts_by_bucket"]["P1_ENVIRONMENT"] == {"environment": 1}
    assert manifest["quality_reason_counts"] == {"single_common_word": 2, "too_short_token": 1}
    assert manifest["quality_flagged_items"] == 2
    assert manifest["top_subjects_by_bucket"]["P0_HIGH_CLAIM"][0] == {"subject": "Marduk", "count": 2}
    assert manifest["top_subjects_by_bucket"]["P9_ENTITY_QUALITY_FLAGGED"][0] == {"subject": "About", "count": 2}
    assert manifest["QUEUE_ALTERED"] is False
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert queue_path.read_text(encoding="utf-8") == before_queue

    manifest_path = engain_dir / "manifests" / "quality_aware_review_queue_summary.json"
    assert manifest_path.exists()
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["QUEUE_ITEMS_READ"] == 6


def test_quality_aware_queue_summary_records_read_errors_without_mutation(tmp_path: Path) -> None:
    queue_path = tmp_path / ".engain" / "mrlore" / "review" / "quality_aware_contradiction_review_queue.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        json.dumps(
            _queue_item(
                "q1",
                "P9_ENTITY_QUALITY_FLAGGED",
                "About",
                reasons=["single_common_word"],
                quality_flagged=True,
            )
        )
        + "\n{bad json\n",
        encoding="utf-8",
    )
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_quality_aware_queue_summary(queue_path)

    assert manifest["MRLORE_QUALITY_AWARE_QUEUE_SUMMARY_COMPLETE"] is False
    assert manifest["QUEUE_ITEMS_READ"] == 1
    assert manifest["read_errors_count"] == 1
    assert manifest["QUEUE_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert queue_path.read_text(encoding="utf-8") == before_queue
