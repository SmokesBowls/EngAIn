from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_temporal_aware_review_by_chapter_view import (
    run_temporal_aware_review_by_chapter_view,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _write_intake_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "MRLORE_SCENE_INTAKE_COMPLETE": True,
                "engain_dir": str(path.parents[1]),
                "chapters": [
                    {
                        "chapter_id": "chapter.book001.001_first",
                        "status": "MRLORE_READY",
                        "scene_count": 2,
                        "scenes": [
                            {"scene_id": "scene.book001.001_first.scene001", "scene_index": 1},
                            {"scene_id": "scene.book001.001_first.scene002", "scene_index": 2},
                        ],
                    },
                    {
                        "chapter_id": "chapter.book001.002_second",
                        "status": "MRLORE_READY",
                        "scene_count": 1,
                        "scenes": [
                            {"scene_id": "scene.book001.002_second.scene001", "scene_index": 1},
                        ],
                    },
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _claim(claim_id: str, scene_id: str, chapter_id: str, chapter_seq: int, scene_index: int, global_seq: int) -> dict:
    return {
        "claim_id": claim_id,
        "chapter_id": chapter_id,
        "chapter_sequence_index": chapter_seq,
        "source_scene_id": scene_id,
        "source_scene": scene_id,
        "SOURCE_SCENE": scene_id,
        "scene_index": scene_index,
        "global_scene_sequence_index": global_seq,
        "temporal_index": float(f"{global_seq}.{scene_index:03d}"),
        "temporal_basis": "CHAPTERROOM_SCENE_ORDER",
        "claim_domain": "entity",
        "subject": "subject",
        "predicate": "present_in",
        "object": scene_id,
        "status": "PROPOSED",
    }


def _queue_item(
    queue_id: str,
    candidate_id: str,
    bucket: str,
    scenes: list[str],
    subject: str,
    predicate: str = "present_in",
    domain: str = "entity",
    classification: str = "SEQUENTIAL_STATE_CHANGE",
    quality_flagged: bool = False,
) -> dict:
    return {
        "queue_id": queue_id,
        "candidate_id": candidate_id,
        "priority_bucket": bucket,
        "claim_domain": domain,
        "subject": subject,
        "predicate": predicate,
        "objects": ["object.a"],
        "source_scenes": scenes,
        "temporal_classification": classification,
        "temporal_basis": "CHAPTERROOM_SCENE_ORDER",
        "entity_quality_flagged": quality_flagged,
        "quality_reasons": ["single_common_word"] if quality_flagged else [],
        "status": "TEMPORAL_AWARE_REVIEW_QUEUED",
        "authority_effect": "NONE",
        "candidate_altered": False,
        "classification_altered": False,
        "claim_promoted": False,
        "claim_rejected": False,
        "contradiction_resolved": False,
        "canon_written": False,
    }


def test_temporal_aware_review_by_chapter_groups_chapter_first_scene_second_and_preserves_items(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    temporal_manifest_path = engain_dir / "manifests" / "mrlore_temporal_claim_context_manifest.json"
    intake_manifest_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"

    _write_intake_manifest(intake_manifest_path)
    _write_jsonl(
        claims_path,
        [
            _claim("claim.a", "scene.book001.001_first.scene001", "chapter.book001.001_first", 1, 1, 34),
            _claim("claim.b", "scene.book001.001_first.scene002", "chapter.book001.001_first", 1, 2, 35),
            _claim("claim.c", "scene.book001.002_second.scene001", "chapter.book001.002_second", 2, 1, 36),
        ],
    )
    temporal_manifest_path.write_text(
        json.dumps(
            {
                "MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE": True,
                "TEMPORAL_BASIS": "CHAPTERROOM_SCENE_ORDER",
                "errors": [],
                "errors_count": 0,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    records = [
        _queue_item(
            "q.late",
            "candidate.late",
            "P3_SEQUENTIAL_STATE_CHANGE",
            ["scene.book001.001_first.scene002"],
            "Marduk",
        ),
        _queue_item(
            "q.early",
            "candidate.early",
            "P0_CONCURRENT_CONFLICT",
            ["scene.book001.001_first.scene001"],
            "Keen",
            classification="CONCURRENT_OBJECT_COLLISION",
        ),
        _queue_item(
            "q.noisy",
            "candidate.noisy",
            "P9_ENTITY_QUALITY_FLAGGED",
            ["scene.book001.002_second.scene001"],
            "About",
            quality_flagged=True,
        ),
    ]
    _write_jsonl(queue_path, records)
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_temporal_aware_review_by_chapter_view(
        queue_path,
        claims_path,
        temporal_manifest_path,
        intake_manifest_path,
    )

    assert manifest["MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_COMPLETE"] is True
    assert manifest["QUEUE_ITEMS_READ"] == 3
    assert manifest["QUEUE_ITEMS_WRITTEN_TO_VIEW"] == 3
    assert manifest["CHAPTERS_WRITTEN"] == 2
    assert manifest["SCENES_WRITTEN"] == 3
    assert manifest["TEMPORAL_DISPLAY_IDS_WRITTEN"] is True

    json_path = engain_dir / "mrlore" / "review" / "by_chapter" / "temporal_aware_review_by_chapter.json"
    view = json.loads(json_path.read_text(encoding="utf-8"))
    assert [chapter["chapter_id"] for chapter in view["chapters"]] == [
        "chapter.book001.001_first",
        "chapter.book001.002_second",
    ]
    first_chapter = view["chapters"][0]
    assert [scene["source_scene_id"] for scene in first_chapter["scenes"]] == [
        "scene.book001.001_first.scene001",
        "scene.book001.001_first.scene002",
    ]
    assert first_chapter["scenes"][0]["temporal_display_id"] == "T000034.001-C001-S001"
    assert first_chapter["scenes"][1]["temporal_display_id"] == "T000035.002-C001-S002"
    seen_queue_ids = [
        item["queue_id"]
        for chapter in view["chapters"]
        for scene in chapter["scenes"]
        for item in scene["items"]
    ]
    assert sorted(seen_queue_ids) == ["q.early", "q.late", "q.noisy"]
    assert first_chapter["scenes"][0]["bucket_counts"] == {"P0_CONCURRENT_CONFLICT": 1}
    assert first_chapter["scenes"][1]["bucket_counts"] == {"P3_SEQUENTIAL_STATE_CHANGE": 1}

    md_path = engain_dir / "mrlore" / "review" / "by_chapter" / "temporal_aware_review_by_chapter.md"
    markdown = md_path.read_text(encoding="utf-8")
    assert "## Chapter C001 — book001.001_first" in markdown
    assert "### Scene T000034.001-C001-S001 — scene.book001.001_first.scene001" in markdown
    assert "#### P0_CONCURRENT_CONFLICT" in markdown
    assert "QUALITY_FLAGGED" in markdown
    assert queue_path.read_text(encoding="utf-8") == before_queue


def test_temporal_aware_review_by_chapter_v2_displays_second_pass_p3_flags_in_p8_lane_without_mutation(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    flags_path = engain_dir / "mrlore" / "review" / "temporal_aware_p3_second_pass_quality_flags.jsonl"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    temporal_manifest_path = engain_dir / "manifests" / "mrlore_temporal_claim_context_manifest.json"
    intake_manifest_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"

    _write_intake_manifest(intake_manifest_path)
    _write_jsonl(
        claims_path,
        [
            _claim("claim.a", "scene.book001.001_first.scene001", "chapter.book001.001_first", 1, 1, 34),
            _claim("claim.b", "scene.book001.001_first.scene002", "chapter.book001.001_first", 1, 2, 35),
        ],
    )
    temporal_manifest_path.write_text(json.dumps({"MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE": True}), encoding="utf-8")
    records = [
        _queue_item(
            "q.clean",
            "candidate.clean",
            "P3_SEQUENTIAL_STATE_CHANGE",
            ["scene.book001.001_first.scene001"],
            "Marduk",
        ),
        _queue_item(
            "q.second_pass",
            "candidate.second_pass",
            "P3_SEQUENTIAL_STATE_CHANGE",
            ["scene.book001.001_first.scene001"],
            "Across",
        ),
        _queue_item(
            "q.old_quality",
            "candidate.old_quality",
            "P9_ENTITY_QUALITY_FLAGGED",
            ["scene.book001.001_first.scene002"],
            "About",
            quality_flagged=True,
        ),
        _queue_item(
            "q.environment",
            "candidate.environment",
            "P4_ENVIRONMENT_REVIEW",
            ["scene.book001.001_first.scene002"],
            "scene.env",
            domain="environment",
            classification="ENVIRONMENT_MULTI_HINT_ACCUMULATION",
        ),
    ]
    _write_jsonl(queue_path, records)
    _write_jsonl(
        flags_path,
        [
            {
                "flag_id": "flag.q.second_pass",
                "queue_id": "q.second_pass",
                "candidate_id": "candidate.second_pass",
                "subject": "Across",
                "bucket": "P3_SEQUENTIAL_STATE_CHANGE",
                "domain": "entity",
                "predicate": "present_in",
                "second_pass_quality_flagged": True,
                "second_pass_reasons": ["connector_or_preposition"],
                "authority_effect": "NONE",
            }
        ],
    )
    before_queue = queue_path.read_bytes()
    before_flags = flags_path.read_bytes()

    manifest = run_temporal_aware_review_by_chapter_view(
        queue_path,
        claims_path,
        temporal_manifest_path,
        intake_manifest_path,
        second_pass_flags_path=flags_path,
    )

    assert manifest["MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_COMPLETE"] is True
    assert manifest["MRLORE_TEMPORAL_AWARE_REVIEW_BY_CHAPTER_VIEW_V2"] is True
    assert manifest["SECOND_PASS_FLAGS_READ"] == 1
    assert manifest["SECOND_PASS_P3_ITEMS_DISPLAYED_IN_P8"] == 1
    assert manifest["display_bucket_counts"] == {
        "P3_SEQUENTIAL_STATE_CHANGE": 1,
        "P8_SECOND_PASS_ENTITY_QUALITY_REVIEW": 1,
        "P4_ENVIRONMENT_REVIEW": 1,
        "P9_ENTITY_QUALITY_FLAGGED": 1,
    }
    view = json.loads((engain_dir / "mrlore" / "review" / "by_chapter" / "temporal_aware_review_by_chapter.json").read_text(encoding="utf-8"))
    items = [item for chapter in view["chapters"] for scene in chapter["scenes"] for item in scene["items"]]
    by_queue_id = {item["queue_id"]: item for item in items}
    assert by_queue_id["q.clean"]["priority_bucket"] == "P3_SEQUENTIAL_STATE_CHANGE"
    assert by_queue_id["q.clean"]["source_priority_bucket"] == "P3_SEQUENTIAL_STATE_CHANGE"
    assert by_queue_id["q.second_pass"]["priority_bucket"] == "P8_SECOND_PASS_ENTITY_QUALITY_REVIEW"
    assert by_queue_id["q.second_pass"]["source_priority_bucket"] == "P3_SEQUENTIAL_STATE_CHANGE"
    assert by_queue_id["q.second_pass"]["second_pass_quality_flagged"] is True
    assert by_queue_id["q.second_pass"]["second_pass_reasons"] == ["connector_or_preposition"]
    assert by_queue_id["q.old_quality"]["priority_bucket"] == "P9_ENTITY_QUALITY_FLAGGED"
    assert by_queue_id["q.environment"]["priority_bucket"] == "P4_ENVIRONMENT_REVIEW"
    markdown = (engain_dir / "mrlore" / "review" / "by_chapter" / "temporal_aware_review_by_chapter.md").read_text(encoding="utf-8")
    assert markdown.index("#### P3_SEQUENTIAL_STATE_CHANGE") < markdown.index("#### P8_SECOND_PASS_ENTITY_QUALITY_REVIEW")
    assert "SECOND_PASS_QUALITY" in markdown
    assert queue_path.read_bytes() == before_queue
    assert flags_path.read_bytes() == before_flags


def test_temporal_aware_review_by_chapter_safety_flags_remain_false(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    temporal_manifest_path = engain_dir / "manifests" / "mrlore_temporal_claim_context_manifest.json"
    intake_manifest_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    _write_intake_manifest(intake_manifest_path)
    _write_jsonl(
        claims_path,
        [_claim("claim.a", "scene.book001.001_first.scene001", "chapter.book001.001_first", 1, 1, 34)],
    )
    temporal_manifest_path.write_text(json.dumps({"MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE": True}), encoding="utf-8")
    _write_jsonl(
        queue_path,
        [
            _queue_item(
                "q.early",
                "candidate.early",
                "P0_CONCURRENT_CONFLICT",
                ["scene.book001.001_first.scene001"],
                "Keen",
                classification="CONCURRENT_OBJECT_COLLISION",
            )
        ],
    )
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_temporal_aware_review_by_chapter_view(
        queue_path,
        claims_path,
        temporal_manifest_path,
        intake_manifest_path,
    )

    assert manifest["REVIEW_SCOPE"] == "CHAPTER_FIRST_SCENE_SECOND"
    assert manifest["SOURCE_QUEUE_ALTERED"] is False
    assert manifest["SECOND_PASS_FLAGS_ALTERED"] is False
    assert manifest["CLAIMS_ALTERED"] is False
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
    assert manifest["ENGINE_AGNOSTIC"] is True
    assert manifest["GODOT_USED_AS_TEMPORAL_AUTHORITY"] is False
    assert manifest["errors_count"] == 0
    assert queue_path.read_text(encoding="utf-8") == before_queue
