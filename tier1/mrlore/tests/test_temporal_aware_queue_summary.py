from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_temporal_aware_queue_summary import run_temporal_aware_queue_summary


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _queue_item(
    queue_id: str,
    bucket: str,
    subject: str,
    predicate: str = "present_in",
    domain: str = "entity",
    scenes: list[str] | None = None,
    temporal_classification: str = "SEQUENTIAL_STATE_CHANGE",
    quality_flagged: bool = False,
    quality_reasons: list[str] | None = None,
    touches_high_claim_scene: bool = False,
) -> dict:
    return {
        "queue_id": queue_id,
        "priority_bucket": bucket,
        "candidate_id": f"candidate.{queue_id}",
        "claim_domain": domain,
        "subject": subject,
        "predicate": predicate,
        "source_scenes": scenes or [f"scene.{queue_id}.a", f"scene.{queue_id}.b"],
        "touches_high_claim_scene": touches_high_claim_scene,
        "temporal_classification": temporal_classification,
        "temporal_basis": "CHAPTERROOM_SCENE_ORDER",
        "temporal_indexes": [1.001, 2.001] if temporal_classification == "SEQUENTIAL_STATE_CHANGE" else [1.001],
        "entity_quality_flagged": quality_flagged,
        "quality_flag_match": "claim_ref" if quality_flagged else "none",
        "quality_reasons": quality_reasons or [],
        "status": "TEMPORAL_AWARE_REVIEW_QUEUED",
        "authority_effect": "NONE",
        "candidate_altered": False,
        "classification_altered": False,
        "claim_rejected": False,
        "claim_promoted": False,
        "contradiction_resolved": False,
        "canon_written": False,
    }


def test_temporal_aware_queue_summary_counts_temporal_pressure_and_overlap_without_mutation(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    records = [
        _queue_item(
            "q1",
            "P3_SEQUENTIAL_STATE_CHANGE",
            "Marduk",
            scenes=["scene.shared", "scene.seq.clean"],
            touches_high_claim_scene=True,
        ),
        _queue_item(
            "q2",
            "P3_SEQUENTIAL_STATE_CHANGE",
            "Marduk",
            predicate="wearing",
            scenes=["scene.seq.clean"],
        ),
        _queue_item(
            "q3",
            "P9_ENTITY_QUALITY_FLAGGED",
            "About",
            scenes=["scene.seq.noisy"],
            quality_flagged=True,
            quality_reasons=["single_common_word"],
        ),
        _queue_item(
            "q4",
            "P0_CONCURRENT_CONFLICT",
            "Keen",
            scenes=["scene.shared", "scene.concurrent"],
            temporal_classification="CONCURRENT_OBJECT_COLLISION",
            touches_high_claim_scene=True,
        ),
        _queue_item(
            "q5",
            "P4_ENVIRONMENT_REVIEW",
            "scene.env",
            predicate="terrain_family",
            domain="environment",
            scenes=["scene.env"],
            temporal_classification="REVIEW_REQUIRED",
        ),
    ]
    _write_jsonl(queue_path, records)
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_temporal_aware_queue_summary(queue_path, top_items_per_bucket=5)

    assert manifest["MRLORE_TEMPORAL_AWARE_QUEUE_SUMMARY_COMPLETE"] is True
    assert manifest["QUEUE_ITEMS_READ"] == 5
    assert manifest["bucket_counts"] == {
        "P0_CONCURRENT_CONFLICT": 1,
        "P3_SEQUENTIAL_STATE_CHANGE": 2,
        "P4_ENVIRONMENT_REVIEW": 1,
        "P9_ENTITY_QUALITY_FLAGGED": 1,
    }
    assert manifest["domain_counts_by_bucket"]["P3_SEQUENTIAL_STATE_CHANGE"] == {"entity": 2}
    assert manifest["top_subjects_by_bucket"]["P3_SEQUENTIAL_STATE_CHANGE"][0] == {"subject": "Marduk", "count": 2}
    assert manifest["top_predicates_by_bucket"]["P3_SEQUENTIAL_STATE_CHANGE"] == [
        {"predicate": "present_in", "count": 1},
        {"predicate": "wearing", "count": 1},
    ]
    assert manifest["scene_counts_by_bucket"]["P3_SEQUENTIAL_STATE_CHANGE"] == {
        "item_count": 2,
        "source_scene_refs": 3,
        "unique_source_scenes": 2,
    }
    assert manifest["high_claim_scene_overlap"] == {
        "items": 2,
        "by_bucket": {"P0_CONCURRENT_CONFLICT": 1, "P3_SEQUENTIAL_STATE_CHANGE": 1},
    }
    assert manifest["quality_flag_overlap"]["items"] == 1
    assert manifest["quality_flag_overlap"]["by_bucket"] == {"P9_ENTITY_QUALITY_FLAGGED": 1}
    assert manifest["quality_reason_counts"] == {"single_common_word": 1}
    assert manifest["sequential_state_change_pressure"] == {
        "temporal_classification_items": 3,
        "bucketed_clean_items": 2,
        "quality_flagged_items": 1,
        "high_claim_scene_items": 1,
        "by_bucket": {"P3_SEQUENTIAL_STATE_CHANGE": 2, "P9_ENTITY_QUALITY_FLAGGED": 1},
    }
    assert manifest["concurrent_conflict_pressure"] == {
        "temporal_classification_items": 1,
        "bucketed_items": 1,
        "quality_flagged_items": 0,
        "high_claim_scene_items": 1,
        "by_bucket": {"P0_CONCURRENT_CONFLICT": 1},
    }
    assert manifest["QUEUE_ALTERED"] is False
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLASSIFICATIONS_ALTERED"] is False
    assert manifest["QUALITY_FLAGS_ALTERED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert queue_path.read_text(encoding="utf-8") == before_queue

    manifest_path = engain_dir / "manifests" / "temporal_aware_review_queue_summary.json"
    assert manifest_path.exists()
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["QUEUE_ITEMS_READ"] == 5


def test_temporal_aware_queue_summary_records_read_errors_without_mutation(tmp_path: Path) -> None:
    queue_path = tmp_path / ".engain" / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(
        json.dumps(_queue_item("q1", "P3_SEQUENTIAL_STATE_CHANGE", "Marduk")) + "\n{bad json\n",
        encoding="utf-8",
    )
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_temporal_aware_queue_summary(queue_path)

    assert manifest["MRLORE_TEMPORAL_AWARE_QUEUE_SUMMARY_COMPLETE"] is False
    assert manifest["QUEUE_ITEMS_READ"] == 1
    assert manifest["read_errors_count"] == 1
    assert manifest["QUEUE_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert queue_path.read_text(encoding="utf-8") == before_queue
