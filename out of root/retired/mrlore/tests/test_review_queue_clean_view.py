from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_review_queue_clean_view import run_review_queue_clean_view


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _queue_item(queue_id: str, subject: str) -> dict:
    return {
        "queue_id": queue_id,
        "candidate_id": f"candidate.{queue_id}",
        "priority_bucket": "P0",
        "claim_domain": "entity",
        "subject": subject,
        "predicate": "present_in",
        "objects": ["scene.a", "scene.b"],
        "source_scenes": ["scene.a"],
        "status": "REVIEW_QUEUED",
        "resolved": False,
        "claim_promoted": False,
        "claim_rejected": False,
        "canon_written": False,
    }


def _noise_flag(queue_id: str, subject: str) -> dict:
    return {
        "queue_id": queue_id,
        "candidate_id": f"candidate.{queue_id}",
        "subject": subject,
        "noise_reasons": ["common_word_or_sentence_starter"],
        "status": "NOISE_REVIEW_FLAGGED",
        "queue_item_altered": False,
        "candidate_altered": False,
        "claim_rejected": False,
        "canon_written": False,
    }


def test_clean_view_excludes_noise_flags_without_altering_original_queue(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue.jsonl"
    flags_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue_noise_flags.jsonl"
    _write_jsonl(
        queue_path,
        [
            _queue_item("q001", "About"),
            _queue_item("q002", "Geralt"),
            _queue_item("q003", "Above"),
            _queue_item("q004", "Yennefer"),
        ],
    )
    _write_jsonl(flags_path, [_noise_flag("q001", "About"), _noise_flag("q003", "Above")])
    before_queue = queue_path.read_text(encoding="utf-8")
    before_flags = flags_path.read_text(encoding="utf-8")

    manifest = run_review_queue_clean_view(queue_path, flags_path)

    assert manifest["MRLORE_REVIEW_QUEUE_CLEAN_VIEW_COMPLETE"] is True
    assert manifest["QUEUE_ITEMS_READ"] == 4
    assert manifest["NOISE_FLAGS_READ"] == 2
    assert manifest["CLEAN_ITEMS_WRITTEN"] == 2
    assert manifest["NOISY_ITEMS_EXCLUDED_FROM_VIEW"] == 2
    assert manifest["ORIGINAL_QUEUE_ALTERED"] is False
    assert manifest["NOISE_FLAGS_ALTERED"] is False
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert queue_path.read_text(encoding="utf-8") == before_queue
    assert flags_path.read_text(encoding="utf-8") == before_flags

    clean_path = engain_dir / "mrlore" / "review" / "clean_review_queue.jsonl"
    clean_items = [json.loads(line) for line in clean_path.read_text(encoding="utf-8").splitlines()]
    assert [item["queue_id"] for item in clean_items] == ["q002", "q004"]
    assert all(item["clean_view_status"] == "CLEAN_VIEW_INCLUDED" for item in clean_items)
    assert all(item["original_queue_item_altered"] is False for item in clean_items)

    md_path = engain_dir / "mrlore" / "review" / "clean_review_queue.md"
    md = md_path.read_text(encoding="utf-8")
    assert "# MrLore Clean Contradiction Review Queue" in md
    assert "q002" in md
    assert "q001" not in md

    manifest_path = engain_dir / "manifests" / "clean_review_queue_manifest.json"
    assert manifest_path.exists()


def test_clean_view_records_noise_flag_read_errors_without_rejecting_claims(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue.jsonl"
    flags_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue_noise_flags.jsonl"
    _write_jsonl(queue_path, [_queue_item("q001", "Geralt")])
    flags_path.parent.mkdir(parents=True, exist_ok=True)
    flags_path.write_text("{bad json\n", encoding="utf-8")

    manifest = run_review_queue_clean_view(queue_path, flags_path)

    assert manifest["MRLORE_REVIEW_QUEUE_CLEAN_VIEW_COMPLETE"] is False
    assert manifest["QUEUE_ITEMS_READ"] == 1
    assert manifest["NOISE_FLAGS_READ"] == 0
    assert manifest["CLEAN_ITEMS_WRITTEN"] == 1
    assert manifest["noise_flag_read_errors_count"] == 1
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
