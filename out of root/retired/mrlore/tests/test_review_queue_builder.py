from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_review_queue_builder import run_review_queue_builder


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _candidate(candidate_id: str, subject: str, predicate: str, claim_domain: str, touches_high: bool) -> dict:
    return {
        "candidate_id": candidate_id,
        "candidate_type": "same_subject_predicate_different_object",
        "claim_domain": claim_domain,
        "subject": subject,
        "predicate": predicate,
        "objects": ["obj.a", "obj.b"],
        "source_scenes": ["scene.high" if touches_high else "scene.clean"],
        "touches_high_claim_scene": touches_high,
        "review_flags": ["CLAIM_DENSITY_REVIEW_REQUIRED"] if touches_high else [],
        "reasons": ["same_subject_same_predicate_different_object"],
        "status": "CANDIDATE_REVIEW_REQUIRED",
        "resolved": False,
        "CANON_WRITTEN": False,
        "CONTRADICTION_RESOLVED": False,
    }


def _write_audit_summary(path: Path, candidates_path: Path, candidates_read: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE": True,
                "CANDIDATES_READ": candidates_read,
                "HIGH_CLAIM_TOUCHING": 3,
                "CLEAN_SCENE_ONLY": candidates_read - 3,
                "REVIEW_BUCKETS_WRITTEN": True,
                "source_candidates_jsonl": str(candidates_path),
                "CONTRADICTIONS_RESOLVED": False,
                "CANON_WRITTEN": False,
                "RUNTIME_TOUCHED": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_review_queue_builder_writes_capped_jsonl_and_markdown_without_authority_side_effects(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    audit_summary = engain_dir / "manifests" / "mrlore_contradiction_candidate_audit_summary.json"
    candidates = [
        _candidate("cand.p0.1", "High One", "present_in", "entity", True),
        _candidate("cand.p0.2", "High Two", "boundary_hints", "environment", True),
        _candidate("cand.p0.3", "High Three", "path_hints", "environment", True),
        _candidate("cand.p2.1", "Entity One", "present_in", "entity", False),
        _candidate("cand.p2.2", "Entity Two", "present_in", "entity", False),
        _candidate("cand.p2.3", "Entity Three", "present_in", "entity", False),
        _candidate("cand.p3.1", "Other One", "boundary_hints", "environment", False),
        _candidate("cand.p3.2", "Other Two", "path_hints", "environment", False),
        _candidate("cand.p3.3", "Other Three", "hazard_hints", "environment", False),
    ]
    _write_jsonl(candidates_path, candidates)
    _write_audit_summary(audit_summary, candidates_path, len(candidates))
    before_candidates = candidates_path.read_text(encoding="utf-8")

    manifest = run_review_queue_builder(audit_summary, candidates_path, max_items_per_bucket=2)

    assert manifest["MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE"] is True
    assert manifest["CANDIDATES_READ"] == 9
    assert manifest["MAX_ITEMS_PER_BUCKET"] == 2
    assert manifest["QUEUE_ITEMS_WRITTEN"] == 6
    assert manifest["P0_ITEMS"] == 2
    assert manifest["P2_ITEMS"] == 2
    assert manifest["P3_ITEMS"] == 2
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert candidates_path.read_text(encoding="utf-8") == before_candidates

    queue_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue.jsonl"
    queue_items = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]
    assert [item["priority_bucket"] for item in queue_items] == ["P0", "P0", "P2", "P2", "P3", "P3"]
    assert [item["candidate_id"] for item in queue_items] == [
        "cand.p0.1",
        "cand.p0.2",
        "cand.p2.1",
        "cand.p2.2",
        "cand.p3.1",
        "cand.p3.2",
    ]
    assert all(item["status"] == "REVIEW_QUEUED" for item in queue_items)
    assert all(item["resolved"] is False for item in queue_items)

    md_path = engain_dir / "mrlore" / "review" / "contradiction_review_queue.md"
    md = md_path.read_text(encoding="utf-8")
    assert "# MrLore Contradiction Review Queue" in md
    assert "## P0" in md
    assert "cand.p0.1" in md


def test_review_queue_builder_refuses_incomplete_audit_summary(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    audit_summary = engain_dir / "manifests" / "mrlore_contradiction_candidate_audit_summary.json"
    _write_jsonl(candidates_path, [_candidate("cand.001", "Entity", "present_in", "entity", False)])
    audit_summary.parent.mkdir(parents=True, exist_ok=True)
    audit_summary.write_text(
        json.dumps({"MRLORE_CONTRADICTION_CANDIDATE_AUDIT_SUMMARY_COMPLETE": False}),
        encoding="utf-8",
    )

    manifest = run_review_queue_builder(audit_summary, candidates_path, max_items_per_bucket=50)

    assert manifest["MRLORE_REVIEW_QUEUE_BUILDER_COMPLETE"] is False
    assert manifest["QUEUE_ITEMS_WRITTEN"] == 0
    assert manifest["errors"] == ["contradiction candidate audit summary is incomplete"]
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
