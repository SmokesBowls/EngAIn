from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_high_claim_scene_review_manifest import run_high_claim_scene_review_manifest


def _write_summary(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "contract": "engain.mrlore_proposed_claim_audit_summary.v1",
                "MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE": True,
                "source_claims_jsonl": str(path.parents[1] / "mrlore" / "claims" / "proposed_claims.jsonl"),
                "high_claim_scene_threshold": {
                    "mean": 2.0,
                    "standard_deviation": 0.75,
                    "threshold": 3.5,
                },
                "source_scene_counts": {
                    "scene.demo.low": 3,
                    "scene.demo.equal_floor": 3.5,
                    "scene.demo.high_b": 7,
                    "scene.demo.high_a": 4,
                },
                "CANON_WRITTEN": False,
                "RUNTIME_TOUCHED": False,
                "GODOT_TOUCHED": False,
                "ZONJ_COMPILED": False,
                "CONTRADICTIONS_RESOLVED": False,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_high_claim_scene_review_manifest_flags_only_scenes_above_threshold(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    summary_path = engain_dir / "manifests" / "proposed_claim_audit_summary.json"
    proposed_claims = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    proposed_claims.parent.mkdir(parents=True, exist_ok=True)
    proposed_claims.write_text('{"claim_id":"claim.demo"}\n', encoding="utf-8")
    before_claims = proposed_claims.read_text(encoding="utf-8")
    _write_summary(summary_path)

    manifest = run_high_claim_scene_review_manifest(summary_path)

    assert manifest["MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE"] is True
    assert manifest["CLAIM_DENSITY_REVIEW_REQUIRED"] is True
    assert manifest["HIGH_CLAIM_SCENES_SELECTED"] == 2
    assert manifest["CLAIMS_REMOVED"] is False
    assert manifest["PROPOSED_CLAIMS_ALTERED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert [scene["SOURCE_SCENE"] for scene in manifest["review_required_scenes"]] == [
        "scene.demo.high_b",
        "scene.demo.high_a",
    ]
    assert {scene["review_status"] for scene in manifest["review_required_scenes"]} == {
        "CLAIM_DENSITY_REVIEW_REQUIRED"
    }
    assert proposed_claims.read_text(encoding="utf-8") == before_claims

    out_path = engain_dir / "manifests" / "high_claim_scene_review_manifest.json"
    assert out_path.exists()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["HIGH_CLAIM_SCENES_SELECTED"] == 2


def test_high_claim_scene_review_manifest_refuses_incomplete_audit_summary(tmp_path: Path) -> None:
    summary_path = tmp_path / ".engain" / "manifests" / "proposed_claim_audit_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE": False,
                "high_claim_scene_threshold": {"threshold": 1},
                "source_scene_counts": {"scene.demo.high": 2},
            }
        ),
        encoding="utf-8",
    )

    manifest = run_high_claim_scene_review_manifest(summary_path)

    assert manifest["MRLORE_HIGH_CLAIM_SCENE_REVIEW_MANIFEST_COMPLETE"] is False
    assert manifest["HIGH_CLAIM_SCENES_SELECTED"] == 0
    assert manifest["errors"] == ["proposed claim audit summary is incomplete"]
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
