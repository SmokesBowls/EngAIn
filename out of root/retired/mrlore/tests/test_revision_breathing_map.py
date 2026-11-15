from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_revision_breathing_map import run_revision_breathing_map


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _claim(claim_id: str, chapter_id: str, scene_id: str, seq: int, predicate: str = "present_in") -> dict:
    return {
        "claim_id": claim_id,
        "chapter_id": chapter_id,
        "chapter_sequence_index": seq,
        "source_scene_id": scene_id,
        "source_scene": scene_id,
        "SOURCE_SCENE": scene_id,
        "scene_index": 1,
        "global_scene_sequence_index": seq,
        "temporal_index": float(f"{seq}.001"),
        "claim_domain": "entity",
        "subject": "Marduk",
        "predicate": predicate,
        "object": scene_id,
        "status": "PROPOSED",
    }


def test_revision_breathing_map_reads_live_body_and_writes_revision_lane_without_authoring(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    mrlore_dir = engain_dir / "mrlore"
    proposed_path = mrlore_dir / "claims" / "proposed_claims.jsonl"
    temporal_path = mrlore_dir / "claims" / "proposed_claims.temporal_enriched.jsonl"
    cosmic_path = mrlore_dir / "claims" / "proposed_claims.cosmic_enriched.jsonl"
    candidates_path = mrlore_dir / "contradictions" / "contradiction_candidates.jsonl"
    classifications_path = mrlore_dir / "contradictions" / "temporal_collision_classifications.jsonl"
    queue_path = mrlore_dir / "review" / "temporal_aware_quality_review_queue.jsonl"
    by_chapter_path = mrlore_dir / "review" / "by_chapter" / "temporal_aware_review_by_chapter.json"
    coming_path = mrlore_dir / "timeline" / "coming_calendar.json"
    predicate_policy_path = mrlore_dir / "lexicon" / "predicate_collision_policy.json"
    preserve_path = mrlore_dir / "lexicon" / "preserve_entity_allowlist.json"
    output_jsonl = mrlore_dir / "revision" / "breathing_map.jsonl"
    output_md = mrlore_dir / "revision" / "breathing_map.md"
    output_manifest = engain_dir / "manifests" / "mrlore_revision_breathing_map_manifest.json"

    chapter_a = "chapter.book006.030_ummade_army"
    scene_a = "scene.book006.030_ummade_army.scene001"
    chapter_b = "chapter.book006.031_second"
    scene_b = "scene.book006.031_second.scene001"

    proposed = [_claim("claim.a1", chapter_a, scene_a, 29), _claim("claim.b1", chapter_b, scene_b, 30)]
    temporal = proposed + [_claim("claim.a2", chapter_a, scene_a, 29, "holding")]
    cosmic = [dict(record, coming_id="FIRST_COMING", region="NORTH") if record["chapter_id"] == chapter_a else record for record in temporal]
    _write_jsonl(proposed_path, proposed)
    _write_jsonl(temporal_path, temporal)
    _write_jsonl(cosmic_path, cosmic)
    _write_jsonl(
        candidates_path,
        [
            {
                "candidate_id": "candidate.a",
                "predicate": "present_in",
                "source_scenes": [scene_a],
                "resolved": False,
            }
        ],
    )
    _write_jsonl(
        classifications_path,
        [
            {
                "candidate_id": "candidate.a",
                "classification": "CONCURRENT_OBJECT_COLLISION",
                "source_scenes": [scene_a],
                "authority_effect": "NONE",
            },
            {
                "candidate_id": "candidate.b",
                "classification": "SEQUENTIAL_STATE_CHANGE",
                "source_scenes": [scene_b],
                "authority_effect": "NONE",
            },
        ],
    )
    _write_jsonl(
        queue_path,
        [
            {
                "queue_id": "queue.a",
                "candidate_id": "candidate.a",
                "priority_bucket": "P0_CONCURRENT_CONFLICT",
                "source_scenes": [scene_a],
                "authority_effect": "NONE",
            },
            {
                "queue_id": "queue.b",
                "candidate_id": "candidate.b",
                "priority_bucket": "P3_SEQUENTIAL_STATE_CHANGE",
                "source_scenes": [scene_b],
                "authority_effect": "NONE",
            },
        ],
    )
    _write_json(
        by_chapter_path,
        {
            "authority_effect": "NONE",
            "chapters": [
                {
                    "chapter_id": chapter_a,
                    "chapter_sequence_index": 29,
                    "scenes": [
                        {
                            "source_scene_id": scene_a,
                            "scene_index": 1,
                            "global_scene_sequence_index": 1,
                            "bucket_counts": {"P0_CONCURRENT_CONFLICT": 1},
                            "items": [],
                        }
                    ],
                },
                {
                    "chapter_id": chapter_b,
                    "chapter_sequence_index": 2,
                    "scenes": [
                        {
                            "source_scene_id": scene_b,
                            "scene_index": 1,
                            "global_scene_sequence_index": 2,
                            "bucket_counts": {"P3_SEQUENTIAL_STATE_CHANGE": 1},
                            "items": [],
                        }
                    ],
                },
            ],
        },
    )
    _write_json(coming_path, {"comings": [{"coming_id": "FIRST_COMING", "coming_number": 1}]})
    _write_json(predicate_policy_path, {"predicate_classes": {"TRANSIENT_STATE": ["present_in"], "DURABLE_STATE": ["dead"]}})
    _write_json(preserve_path, {"terms": [{"term": "Marduk", "status": "ACTIVE"}]})

    before = {
        path: path.read_text(encoding="utf-8")
        for path in [
            proposed_path,
            temporal_path,
            cosmic_path,
            candidates_path,
            classifications_path,
            queue_path,
            by_chapter_path,
            coming_path,
            predicate_policy_path,
            preserve_path,
        ]
    }

    manifest = run_revision_breathing_map(
        proposed_path,
        temporal_path,
        cosmic_path,
        candidates_path,
        classifications_path,
        queue_path,
        by_chapter_path,
        coming_path,
        predicate_policy_path,
        preserve_path,
        output_jsonl,
        output_md,
        output_manifest,
        mrlore_dir / "revision" / "focus",
        30,
        30,
        "book006",
    )

    assert manifest["MRLORE_REVISION_BREATHING_MAP_COMPLETE"] is True
    assert manifest["MRLORE_REVISION_BREATHING_MAP_READS_FULL_MRLORE_BODY"] is True
    assert manifest["PROPOSED_CLAIMS_READ"] == 2
    assert manifest["TEMPORAL_ENRICHED_CLAIMS_READ"] == 3
    assert manifest["COSMIC_ENRICHED_CLAIMS_READ"] == 3
    assert manifest["CONTRADICTION_CANDIDATES_READ"] == 1
    assert manifest["TEMPORAL_COLLISION_CLASSIFICATIONS_READ"] == 2
    assert manifest["TEMPORAL_AWARE_REVIEW_QUEUE_ITEMS_READ"] == 2
    assert manifest["BY_CHAPTER_REVIEW_CHAPTERS_READ"] == 2
    assert manifest["COMING_CONTEXTS_LOADED"] == 1
    assert manifest["PREDICATE_CLASSES_LOADED"] == 2
    assert manifest["PRESERVE_ALLOWLIST_TERMS_LOADED"] == 1
    assert manifest["CHAPTERS_WRITTEN"] == 2
    assert manifest["MRLORE_REVISION_BREATHING_MAP_CALIBRATION_V2"] is True
    assert manifest["PRESSURE_RANKINGS_WRITTEN"] is True
    assert manifest["WITHIN_BOOK_RANKINGS_WRITTEN"] is True
    assert manifest["FOCUS_FILTER_CHAPTER_START"] == 30
    assert manifest["FOCUS_FILTER_CHAPTER_END"] == 30
    assert manifest["FOCUS_FILTER_BOOK_ID"] == "book006"
    assert manifest["MRLORE_REVISION_BREATHING_MAP_AUTHOR_USEFULNESS_V3"] is True
    assert manifest["MARKDOWN_GUIDANCE_FIELDS_WRITTEN"] is True
    assert manifest["CHAPTER_HEADING_DISPLAY_FIXED"] is True
    assert manifest["TITLE_BASED_GUIDANCE_HINTS_WRITTEN"] is True
    assert manifest["GENERATED_PROSE_CREATED"] is False
    assert manifest["REPLACEMENT_PROSE_CREATED"] is False
    assert manifest["FOCUS_RECORDS_WRITTEN"] == 1
    assert manifest["CHAPTERS_REWRITTEN"] is False
    assert manifest["REPLACEMENT_PROSE_GENERATED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["ACCEPTED_LORE_PACKETS_CREATED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["AUTHOR_REVISES_MANUALLY"] is True

    records = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [record["chapter_id"] for record in records] == [chapter_a, chapter_b]
    first = records[0]
    assert first["revision_scope"] == "AUTHOR_FACING_BREATHING_GUIDANCE_ONLY"
    assert first["pressure_score"] == first["event_pressure_score"]
    assert first["pressure_rank_global"] == 1
    assert first["pressure_percentile_global"] == 50.0
    assert first["pressure_rank_within_book"] == 1
    assert first["pressure_percentile_within_book"] == 100.0
    assert first["pressure_tier_global"] == first["event_pressure_tier"]
    assert first["pressure_tier_within_book"] == "BOOK_EXTREME_PRESSURE"
    assert first["diagnostic_confidence"] == "HIGH"
    assert first["primary_pressure_source"] in {
        "CLAIM_DENSITY_AND_TEMPORAL_COLLISION_LOAD",
        "TEMPORAL_COLLISION_LOAD",
        "REVIEW_QUEUE_PRESSURE",
        "CLAIM_DENSITY",
        "LOW_PRESSURE_BASELINE",
    }
    assert first["PRESSURE_SCORE_DIAGNOSTIC_NOT_QUALITY_JUDGMENT"] is True
    assert first["HIGH_PRESSURE_NOT_BAD_CHAPTER"] is True
    assert first["HIGH_PRESSURE_STATE_CHANGE_HUMAN_REVIEW"] is True
    assert "unmaking / erased army aftermath" in first["detected_event_pressure"]
    assert "GRIEF_WITHOUT_EVIDENCE" in first["missing_breath_type"]
    assert first["expected_internal_feeling"] == (
        "The witness should feel the horror of remembering what the world no longer confirms."
    )
    assert first["CANON_WRITTEN"] is False
    assert first["CLAIMS_PROMOTED"] is False
    assert first["CLAIMS_REJECTED"] is False
    assert first["CONTRADICTIONS_RESOLVED"] is False
    assert first["ZONJ_COMPILED"] is False
    assert first["GODOT_TOUCHED"] is False
    assert first["RUNTIME_TOUCHED"] is False
    assert "rewritten_scene" not in json.dumps(first)
    assert "replacement_paragraph" not in json.dumps(first)
    assert "generated_prose" not in json.dumps(first)
    assert first["temporal_cosmic_context"]["coming_ids"] == {"FIRST_COMING": 2}
    assert first["review_pressure"]["review_bucket_counts"]["P0_CONCURRENT_CONFLICT"] >= 1
    assert first["contradiction_pressure"]["classification_counts"]["CONCURRENT_OBJECT_COLLISION"] == 1
    assert any("manual" in guidance.lower() for guidance in first["breathing_guidance"])

    markdown = output_md.read_text(encoding="utf-8")
    assert "# MrLore Revision Breathing Map" in markdown
    assert "# Top Revision Breathing Targets" in markdown
    assert "## Global Top 20" in markdown
    assert "## Top 5 Per Book" in markdown
    assert "## CH30–CH38 Arc Focus" in markdown
    assert "Does not rewrite chapters" in markdown
    assert "Pressure score is diagnostic, not a quality judgment" in markdown
    assert "Author revises manually" in markdown
    focus_path = mrlore_dir / "revision" / "focus" / "book006_ch30_ch30_breathing_map.md"
    assert focus_path.exists()
    focus_markdown = focus_path.read_text(encoding="utf-8")
    assert "Focus records: 1" in focus_markdown
    assert "Detected event pressure:" in focus_markdown
    assert "Missing breath type:" in focus_markdown
    assert "Expected internal feeling:" in focus_markdown
    assert "Do not change:" in focus_markdown
    assert "CH030 — book006.030_ummade_army" in focus_markdown
    assert "C029 — book006.030_ummade_army" not in focus_markdown
    assert "Author action required:" in focus_markdown
    assert "true" in focus_markdown
    assert "Safety:" in focus_markdown
    assert str(output_jsonl).endswith(".engain/mrlore/revision/breathing_map.jsonl")
    assert str(output_manifest).endswith(".engain/manifests/mrlore_revision_breathing_map_manifest.json")

    for path, content in before.items():
        assert path.read_text(encoding="utf-8") == content
