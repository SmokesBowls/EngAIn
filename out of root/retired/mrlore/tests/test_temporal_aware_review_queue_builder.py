from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_temporal_aware_review_queue_builder import run_temporal_aware_review_queue_builder


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _write_high_claim_manifest(path: Path, scenes: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE": True,
                "review_required_scenes": [
                    {"SOURCE_SCENE": scene, "review_status": "CLAIM_DENSITY_REVIEW_REQUIRED"}
                    for scene in (scenes or [])
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _candidate(
    candidate_id: str,
    subject: str,
    predicate: str = "present_in",
    claim_domain: str = "entity",
    scenes: list[str] | None = None,
) -> dict:
    source_scenes = scenes or [f"scene.{candidate_id}.a", f"scene.{candidate_id}.b"]
    objects = [f"object.{index}" for index, _scene in enumerate(source_scenes, 1)]
    return {
        "candidate_id": candidate_id,
        "candidate_type": "same_subject_predicate_different_object",
        "claim_domain": claim_domain,
        "subject": subject,
        "predicate": predicate,
        "objects": objects,
        "source_scenes": source_scenes,
        "touches_high_claim_scene": False,
        "review_flags": [],
        "reasons": ["same_subject_same_predicate_different_object"],
        "object_claim_refs": {
            obj: [{"claim_id": f"claim.{candidate_id}.{index}", "SOURCE_SCENE": source_scenes[index - 1]}]
            for index, obj in enumerate(objects, 1)
        },
        "resolved": False,
        "CONTRADICTION_RESOLVED": False,
        "CANON_WRITTEN": False,
    }


def _classification(candidate_id: str, classification: str, indexes: list[float] | None = None) -> dict:
    return {
        "classification_id": f"temporal.{candidate_id}",
        "candidate_id": candidate_id,
        "subject": "subject",
        "predicate": "present_in",
        "domain": "entity",
        "classification": classification,
        "temporal_basis": "CHAPTERROOM_SCENE_ORDER" if indexes is not None else "UNRESOLVED_SCENE_ORDER",
        "temporal_indexes": indexes or [],
        "source_claim_refs": [],
        "source_scenes": [],
        "reason": classification.lower(),
        "authority_effect": "NONE",
    }


def _quality_flag(claim_id: str, subject: str, reason: str = "single_common_word") -> dict:
    return {
        "claim_id": claim_id,
        "subject": subject,
        "quality_reasons": [reason],
        "status": "QUALITY_REVIEW_FLAGGED",
        "sidecar_only": True,
        "claim_rejected": False,
        "claim_promoted": False,
        "canon_written": False,
    }


def test_temporal_aware_review_queue_uses_temporal_classification_buckets_and_downranks_sequential_change(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    classifications_path = engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl"
    quality_flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    high_claim_manifest_path = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    candidates = [
        _candidate("cand.concurrent", "Marduk"),
        _candidate("cand.durable", "Aldrin", predicate="dead"),
        _candidate("cand.unknown", "Keen"),
        _candidate("cand.sequential", "Luminaire"),
        _candidate("cand.env", "scene.demo", predicate="terrain_family", claim_domain="environment"),
        _candidate("cand.clean", "Annunaki"),
        _candidate("cand.noisy", "About"),
    ]
    _write_jsonl(candidates_path, candidates)
    _write_jsonl(
        classifications_path,
        [
            _classification("cand.concurrent", "CONCURRENT_OBJECT_COLLISION", [1.001]),
            _classification("cand.durable", "DURABLE_STATE_CONTINUITY_REVIEW", [1.001, 2.001]),
            _classification("cand.unknown", "TEMPORAL_ORDER_UNKNOWN_REVIEW", None),
            _classification("cand.sequential", "SEQUENTIAL_STATE_CHANGE", [1.001, 2.001]),
        ],
    )
    _write_jsonl(quality_flags_path, [_quality_flag("claim.cand.noisy.1", "About")])
    _write_high_claim_manifest(high_claim_manifest_path, ["scene.cand.concurrent.a"])

    manifest = run_temporal_aware_review_queue_builder(
        candidates_path,
        classifications_path,
        quality_flags_path,
        high_claim_manifest_path,
    )

    assert manifest["MRLORE_TEMPORAL_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE"] is True
    assert manifest["CANDIDATES_READ"] == 7
    assert manifest["TEMPORAL_CLASSIFICATIONS_READ"] == 4
    assert manifest["QUALITY_FLAGS_READ"] == 1
    assert manifest["QUEUE_ITEMS_WRITTEN"] == 7
    assert manifest["P0_CONCURRENT_CONFLICT_ITEMS"] == 1
    assert manifest["P1_DURABLE_STATE_CONTINUITY_REVIEW_ITEMS"] == 1
    assert manifest["P2_TEMPORAL_ORDER_UNKNOWN_ITEMS"] == 1
    assert manifest["P3_SEQUENTIAL_STATE_CHANGE_ITEMS"] == 1
    assert manifest["P4_ENVIRONMENT_REVIEW_ITEMS"] == 1
    assert manifest["P5_CLEAN_ENTITY_REVIEW_ITEMS"] == 1
    assert manifest["P9_ENTITY_QUALITY_FLAGGED_ITEMS"] == 1

    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    items = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]
    assert [item["candidate_id"] for item in items] == [
        "cand.concurrent",
        "cand.durable",
        "cand.unknown",
        "cand.sequential",
        "cand.env",
        "cand.clean",
        "cand.noisy",
    ]
    buckets = {item["candidate_id"]: item["priority_bucket"] for item in items}
    assert buckets["cand.concurrent"] == "P0_CONCURRENT_CONFLICT"
    assert buckets["cand.durable"] == "P1_DURABLE_STATE_CONTINUITY_REVIEW"
    assert buckets["cand.unknown"] == "P2_TEMPORAL_ORDER_UNKNOWN"
    assert buckets["cand.sequential"] == "P3_SEQUENTIAL_STATE_CHANGE"
    assert buckets["cand.env"] == "P4_ENVIRONMENT_REVIEW"
    assert buckets["cand.clean"] == "P5_CLEAN_ENTITY_REVIEW"
    assert buckets["cand.noisy"] == "P9_ENTITY_QUALITY_FLAGGED"
    sequential = next(item for item in items if item["candidate_id"] == "cand.sequential")
    assert sequential["temporal_classification"] == "SEQUENTIAL_STATE_CHANGE"
    assert sequential["temporal_indexes"] == [1.001, 2.001]
    assert sequential["authority_effect"] == "NONE"


def test_temporal_aware_review_queue_writes_sidecar_without_mutating_inputs(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    classifications_path = engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl"
    quality_flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    high_claim_manifest_path = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    _write_jsonl(candidates_path, [_candidate("cand.clean", "Marduk")])
    _write_jsonl(classifications_path, [_classification("cand.clean", "SEQUENTIAL_STATE_CHANGE", [1.001, 2.001])])
    _write_jsonl(quality_flags_path, [])
    _write_high_claim_manifest(high_claim_manifest_path)
    before_candidates = candidates_path.read_text(encoding="utf-8")
    before_classifications = classifications_path.read_text(encoding="utf-8")
    before_quality_flags = quality_flags_path.read_text(encoding="utf-8")

    manifest = run_temporal_aware_review_queue_builder(
        candidates_path,
        classifications_path,
        quality_flags_path,
        high_claim_manifest_path,
    )

    assert candidates_path.read_text(encoding="utf-8") == before_candidates
    assert classifications_path.read_text(encoding="utf-8") == before_classifications
    assert quality_flags_path.read_text(encoding="utf-8") == before_quality_flags
    assert manifest["SIDE_CAR_ONLY"] is True
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLASSIFICATIONS_ALTERED"] is False
    assert manifest["QUALITY_FLAGS_ALTERED"] is False
    assert manifest["CLAIMS_ALTERED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False


def test_temporal_aware_review_queue_records_read_errors_without_authority_effect(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    classifications_path = engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl"
    quality_flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    high_claim_manifest_path = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    candidates_path.write_text(json.dumps(_candidate("cand.clean", "Marduk")) + "\n{bad json\n", encoding="utf-8")
    _write_jsonl(classifications_path, [_classification("cand.clean", "SEQUENTIAL_STATE_CHANGE", [1.001, 2.001])])
    _write_jsonl(quality_flags_path, [])
    _write_high_claim_manifest(high_claim_manifest_path)

    manifest = run_temporal_aware_review_queue_builder(
        candidates_path,
        classifications_path,
        quality_flags_path,
        high_claim_manifest_path,
    )

    assert manifest["MRLORE_TEMPORAL_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE"] is False
    assert manifest["CANDIDATES_READ"] == 1
    assert manifest["QUEUE_ITEMS_WRITTEN"] == 1
    assert manifest["read_errors_count"] == 1
    assert manifest["SIDE_CAR_ONLY"] is True
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
