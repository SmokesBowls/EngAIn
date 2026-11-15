from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_contradiction_candidate_audit_summary import run_contradiction_candidate_audit_summary


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _candidate(
    candidate_id: str,
    claim_domain: str,
    subject: str,
    predicate: str,
    touches_high_claim_scene: bool,
    reasons: list[str] | None = None,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "candidate_type": "same_subject_predicate_different_object",
        "claim_domain": claim_domain,
        "subject": subject,
        "predicate": predicate,
        "objects": ["a", "b"],
        "source_scenes": ["scene.demo.high" if touches_high_claim_scene else "scene.demo.clean"],
        "touches_high_claim_scene": touches_high_claim_scene,
        "review_flags": ["CLAIM_DENSITY_REVIEW_REQUIRED"] if touches_high_claim_scene else [],
        "reasons": reasons or ["same_subject_same_predicate_different_object"],
        "status": "CANDIDATE_REVIEW_REQUIRED",
        "resolved": False,
        "CANON_WRITTEN": False,
        "CONTRADICTION_RESOLVED": False,
    }


def _write_grouper_manifest(path: Path, candidates_path: Path, count: int, high_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE": True,
                "CONTRADICTION_CANDIDATES_WRITTEN": count,
                "CANDIDATES_TOUCHING_HIGH_CLAIM_SCENES": high_count,
                "candidate_jsonl_path": str(candidates_path),
                "CONTRADICTIONS_RESOLVED": False,
                "CANON_WRITTEN": False,
                "RUNTIME_TOUCHED": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_contradiction_candidate_audit_summary_counts_pressure_without_resolving(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    manifest_path = engain_dir / "manifests" / "mrlore_contradiction_candidate_manifest.json"
    _write_jsonl(
        candidates_path,
        [
            _candidate("cand.001", "entity", "Geralt", "present_in", True),
            _candidate("cand.002", "entity", "Geralt", "present_in", False),
            _candidate(
                "cand.003",
                "environment",
                "scene.demo.clean",
                "terrain_family",
                False,
                ["same_subject_same_predicate_different_object", "incompatible_state_predicate"],
            ),
            _candidate("cand.004", "environment", "scene.demo.high", "region", True, ["incompatible_state_predicate"]),
        ],
    )
    _write_grouper_manifest(manifest_path, candidates_path, count=4, high_count=2)
    before_candidates = candidates_path.read_text(encoding="utf-8")

    summary = run_contradiction_candidate_audit_summary(candidates_path, manifest_path)

    assert summary["MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE"] is True
    assert summary["CANDIDATES_READ"] == 4
    assert summary["HIGH_CLAIM_TOUCHING"] == 2
    assert summary["CLEAN_SCENE_ONLY"] == 2
    assert summary["DOMAIN_COUNTS_WRITTEN"] is True
    assert summary["PREDICATE_COUNTS_WRITTEN"] is True
    assert summary["SUBJECT_COUNTS_WRITTEN"] is True
    assert summary["REVIEW_BUCKETS_WRITTEN"] is True
    assert summary["CONTRADICTIONS_RESOLVED"] is False
    assert summary["CLAIMS_PROMOTED"] is False
    assert summary["CLAIMS_REJECTED"] is False
    assert summary["CANON_WRITTEN"] is False
    assert summary["RUNTIME_TOUCHED"] is False
    assert summary["domain_counts"] == {"entity": 2, "environment": 2}
    assert summary["predicate_counts"] == {"present_in": 2, "region": 1, "terrain_family": 1}
    assert summary["subject_counts"]["Geralt"] == 2
    assert summary["top_contradiction_heavy_subjects"][0] == {"subject": "Geralt", "count": 2}
    assert summary["top_contradiction_heavy_predicates"][0] == {"predicate": "present_in", "count": 2}
    assert summary["review_priority_buckets"]["P0_HIGH_CLAIM_REVIEW_REQUIRED"] == 2
    assert summary["review_priority_buckets"]["P1_INCOMPATIBLE_STATE_PREDICATE"] == 1
    assert summary["review_priority_buckets"]["P2_CLEAN_ENTITY_PRESENCE"] == 1
    assert candidates_path.read_text(encoding="utf-8") == before_candidates

    out_path = engain_dir / "manifests" / "mrlore_contradiction_candidate_audit_summary.json"
    assert out_path.exists()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["CANDIDATES_READ"] == 4


def test_contradiction_candidate_audit_summary_refuses_incomplete_grouper_manifest(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    manifest_path = engain_dir / "manifests" / "mrlore_contradiction_candidate_manifest.json"
    _write_jsonl(candidates_path, [_candidate("cand.001", "entity", "Geralt", "present_in", False)])
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE": False}),
        encoding="utf-8",
    )

    summary = run_contradiction_candidate_audit_summary(candidates_path, manifest_path)

    assert summary["MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE"] is False
    assert summary["CANDIDATES_READ"] == 0
    assert summary["errors"] == ["contradiction candidate grouper manifest is incomplete"]
    assert summary["CONTRADICTIONS_RESOLVED"] is False
    assert summary["CANON_WRITTEN"] is False
