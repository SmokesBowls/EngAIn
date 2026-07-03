from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_quality_aware_review_queue_builder import run_quality_aware_review_queue_builder


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _candidate(candidate_id: str, subject: str, claim_domain: str = "entity", scenes: list[str] | None = None) -> dict:
    source_scenes = scenes or ["scene.demo.clean"]
    predicate = "present_in" if claim_domain == "entity" else "terrain_family"
    return {
        "candidate_id": candidate_id,
        "candidate_type": "same_subject_predicate_different_object",
        "claim_domain": claim_domain,
        "subject": subject,
        "predicate": predicate,
        "objects": source_scenes,
        "source_scenes": source_scenes,
        "touches_high_claim_scene": False,
        "review_flags": [],
        "reasons": ["same_subject_same_predicate_different_object"],
        "object_claim_refs": {
            scene: [
                {
                    "claim_id": f"claim.{candidate_id}.{index}",
                    "SOURCE_SCENE": scene,
                    "source_line": index,
                }
            ]
            for index, scene in enumerate(source_scenes, 1)
        },
        "resolved": False,
        "CONTRADICTION_RESOLVED": False,
        "CANON_WRITTEN": False,
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


def test_quality_aware_review_queue_marks_and_downranks_quality_flagged_entity_candidates(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    quality_flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    high_claim_manifest_path = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"

    candidates = [
        _candidate("c.high", "Clean High", scenes=["scene.high"]),
        _candidate("c.env", "scene.demo", claim_domain="environment", scenes=["scene.env"]),
        _candidate("c.clean", "Marduk", scenes=["scene.clean"]),
        _candidate("c.noisy.subject", "About", scenes=["scene.noisy.a", "scene.noisy.b"]),
        _candidate("c.noisy.claim", "Some Candidate", scenes=["scene.claimflag"]),
    ]
    _write_jsonl(candidates_path, candidates)
    _write_jsonl(
        quality_flags_path,
        [
            _quality_flag("claim.external.noisy.subject", "About"),
            _quality_flag("claim.c.noisy.claim.1", "Different Surface", "possessive_fragment"),
        ],
    )
    high_claim_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    high_claim_manifest_path.write_text(
        json.dumps(
            {
                "MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE": True,
                "review_required_scenes": [{"SOURCE_SCENE": "scene.high", "review_status": "CLAIM_DENSITY_REVIEW_REQUIRED"}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    before_candidates = candidates_path.read_text(encoding="utf-8")

    manifest = run_quality_aware_review_queue_builder(candidates_path, quality_flags_path, high_claim_manifest_path)

    assert manifest["MRLORE_QUALITY_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE"] is True
    assert manifest["CANDIDATES_READ"] == 5
    assert manifest["QUALITY_FLAGS_READ"] == 2
    assert manifest["QUEUE_ITEMS_WRITTEN"] == 5
    assert manifest["QUALITY_FLAGGED_ITEMS_MARKED"] == 2
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["QUALITY_FLAGS_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert candidates_path.read_text(encoding="utf-8") == before_candidates

    queue_path = engain_dir / "mrlore" / "review" / "quality_aware_contradiction_review_queue.jsonl"
    items = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]
    assert [item["candidate_id"] for item in items] == ["c.high", "c.env", "c.clean", "c.noisy.subject", "c.noisy.claim"]
    buckets = {item["candidate_id"]: item["priority_bucket"] for item in items}
    assert buckets["c.high"] == "P0_HIGH_CLAIM"
    assert buckets["c.env"] == "P1_ENVIRONMENT"
    assert buckets["c.clean"] == "P2_CLEAN_ENTITY"
    assert buckets["c.noisy.subject"] == "P9_ENTITY_QUALITY_FLAGGED"
    assert buckets["c.noisy.claim"] == "P9_ENTITY_QUALITY_FLAGGED"
    noisy = {item["candidate_id"]: item for item in items if item["entity_quality_flagged"]}
    assert noisy["c.noisy.subject"]["quality_flag_match"] == "subject"
    assert noisy["c.noisy.claim"]["quality_flag_match"] == "claim_ref"
    assert all(item["claim_rejected"] is False for item in items)
    assert all(item["claim_promoted"] is False for item in items)

    assert (engain_dir / "mrlore" / "review" / "quality_aware_contradiction_review_queue.md").exists()
    assert (engain_dir / "manifests" / "quality_aware_review_queue_manifest.json").exists()


def test_quality_aware_review_queue_records_read_errors_without_authority_effect(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    quality_flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    high_claim_manifest_path = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    candidates_path.write_text(json.dumps(_candidate("c.noisy", "About")) + "\n{bad json\n", encoding="utf-8")
    _write_jsonl(quality_flags_path, [_quality_flag("claim.c.noisy.1", "About")])
    high_claim_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    high_claim_manifest_path.write_text(json.dumps({"MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE": True, "review_required_scenes": []}), encoding="utf-8")

    manifest = run_quality_aware_review_queue_builder(candidates_path, quality_flags_path, high_claim_manifest_path)

    assert manifest["MRLORE_QUALITY_AWARE_REVIEW_QUEUE_BUILDER_COMPLETE"] is False
    assert manifest["CANDIDATES_READ"] == 1
    assert manifest["QUALITY_FLAGS_READ"] == 1
    assert manifest["QUEUE_ITEMS_WRITTEN"] == 1
    assert manifest["read_errors_count"] == 1
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CANON_WRITTEN"] is False
