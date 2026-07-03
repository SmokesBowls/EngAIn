from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_contradiction_candidate_grouper import run_contradiction_candidate_grouper


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _claim(
    claim_id: str,
    source_scene: str,
    claim_domain: str,
    subject: str,
    predicate: str,
    obj: str,
    line: int = 1,
) -> dict:
    return {
        "claim_id": claim_id,
        "SOURCE_SCENE": source_scene,
        "claim_domain": claim_domain,
        "claim_type": "environment_state" if claim_domain == "environment" else "entity_presence",
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "status": "PROPOSED",
        "source_line": line,
    }


def _write_high_claim_manifest(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE": True,
                "HIGH_CLAIM_SCENES_SELECTED": 1,
                "review_required_scenes": [
                    {
                        "SOURCE_SCENE": "scene.demo.noisy",
                        "claim_count": 100,
                        "review_status": "CLAIM_DENSITY_REVIEW_REQUIRED",
                    }
                ],
                "CANON_WRITTEN": False,
                "RUNTIME_TOUCHED": False,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_contradiction_candidate_grouper_groups_different_objects_without_resolving(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    high_manifest = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    _write_high_claim_manifest(high_manifest)
    _write_jsonl(
        claims_path,
        [
            _claim("claim.001", "scene.demo.clean1", "environment", "scene.demo.clean1", "terrain_family", "coastal"),
            _claim("claim.002", "scene.demo.clean1", "environment", "scene.demo.clean1", "terrain_family", "desert"),
            _claim("claim.003", "scene.demo.clean2", "entity", "Geralt", "present_in", "scene.demo.clean2"),
            _claim("claim.004", "scene.demo.clean3", "entity", "Geralt", "present_in", "scene.demo.clean3"),
            _claim("claim.005", "scene.demo.noisy", "environment", "scene.demo.noisy", "terrain_family", "coastal"),
        ],
    )
    before_claims = claims_path.read_text(encoding="utf-8")

    manifest = run_contradiction_candidate_grouper(claims_path, high_manifest)

    assert manifest["MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE"] is True
    assert manifest["CLAIMS_READ"] == 5
    assert manifest["HIGH_CLAIM_SCENES_FLAGGED"] == 1
    assert manifest["CLAIMS_IN_HIGH_CLAIM_SCENES"] == 1
    assert manifest["CONTRADICTION_CANDIDATES_WRITTEN"] == 2
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert claims_path.read_text(encoding="utf-8") == before_claims

    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    candidates = [json.loads(line) for line in candidates_path.read_text(encoding="utf-8").splitlines()]
    assert [candidate["candidate_type"] for candidate in candidates] == [
        "same_subject_predicate_different_object",
        "same_subject_predicate_different_object",
    ]
    assert candidates[0]["subject"] == "Geralt"
    assert candidates[0]["predicate"] == "present_in"
    assert candidates[0]["objects"] == ["scene.demo.clean2", "scene.demo.clean3"]
    assert candidates[1]["subject"] == "scene.demo.clean1"
    assert candidates[1]["predicate"] == "terrain_family"
    assert candidates[1]["objects"] == ["coastal", "desert"]
    assert all(candidate["status"] == "CANDIDATE_REVIEW_REQUIRED" for candidate in candidates)
    assert all(candidate["resolved"] is False for candidate in candidates)


def test_contradiction_candidate_grouper_flags_high_density_groups_without_resolving(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    high_manifest = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    _write_high_claim_manifest(high_manifest)
    _write_jsonl(
        claims_path,
        [
            _claim("claim.001", "scene.demo.noisy", "environment", "scene.demo.noisy", "terrain_family", "coastal"),
            _claim("claim.002", "scene.demo.noisy", "environment", "scene.demo.noisy", "terrain_family", "desert"),
        ],
    )

    manifest = run_contradiction_candidate_grouper(claims_path, high_manifest)

    assert manifest["MRLORE_CONTRADICTION_CANDIDATE_GROUPER_COMPLETE"] is True
    assert manifest["CONTRADICTION_CANDIDATES_WRITTEN"] == 1
    assert manifest["CANDIDATES_TOUCHING_HIGH_CLAIM_SCENES"] == 1
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    candidate = json.loads(candidates_path.read_text(encoding="utf-8").strip())
    assert candidate["touches_high_claim_scene"] is True
    assert candidate["review_flags"] == ["CLAIM_DENSITY_REVIEW_REQUIRED"]
    assert candidate["resolved"] is False
