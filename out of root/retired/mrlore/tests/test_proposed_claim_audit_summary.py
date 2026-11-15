from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_proposed_claim_audit_summary import run_claim_audit_summary


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def test_claim_audit_summary_counts_domains_types_predicates_and_source_scenes(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    _write_jsonl(
        claims_path,
        [
            {
                "claim_id": "claim.001",
                "SOURCE_SCENE": "scene.demo.scene001",
                "claim_domain": "entity",
                "claim_type": "entity_presence",
                "subject": "Geralt",
                "predicate": "present_in",
                "object": "scene.demo.scene001",
                "status": "PROPOSED",
            },
            {
                "claim_id": "claim.002",
                "SOURCE_SCENE": "scene.demo.scene001",
                "claim_domain": "environment",
                "claim_type": "environment_state",
                "subject": "scene.demo.scene001",
                "predicate": "terrain_family",
                "object": "coastal",
                "status": "PROPOSED",
            },
            {
                "claim_id": "claim.003",
                "SOURCE_SCENE": "scene.demo.scene002",
                "claim_domain": "environment",
                "claim_type": "environment_state",
                "subject": "scene.demo.scene002",
                "predicate": "terrain_family",
                "object": "urban",
                "status": "PROPOSED",
            },
        ],
    )

    summary = run_claim_audit_summary(claims_path)

    assert summary["MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE"] is True
    assert summary["CLAIMS_READ"] == 3
    assert summary["DOMAINS_COUNTED"] is True
    assert summary["PREDICATES_COUNTED"] is True
    assert summary["SOURCE_SCENES_COUNTED"] is True
    assert summary["CANON_WRITTEN"] is False
    assert summary["RUNTIME_TOUCHED"] is False
    assert summary["domain_counts"] == {"environment": 2, "entity": 1}
    assert summary["claim_type_counts"] == {"environment_state": 2, "entity_presence": 1}
    assert summary["predicate_counts"] == {"terrain_family": 2, "present_in": 1}
    assert summary["source_scene_counts"] == {
        "scene.demo.scene001": 2,
        "scene.demo.scene002": 1,
    }
    assert summary["top_noisy_predicates"][0] == {"predicate": "terrain_family", "count": 2}
    assert summary["high_claim_scenes"][0] == {"SOURCE_SCENE": "scene.demo.scene001", "count": 2}

    out_path = engain_dir / "manifests" / "proposed_claim_audit_summary.json"
    assert out_path.exists()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["CLAIMS_READ"] == 3


def test_claim_audit_summary_keeps_invalid_json_as_read_error_without_canon_side_effects(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    claims_path.parent.mkdir(parents=True, exist_ok=True)
    claims_path.write_text(
        json.dumps(
            {
                "claim_id": "claim.001",
                "SOURCE_SCENE": "scene.demo.scene001",
                "claim_domain": "entity",
                "claim_type": "entity_presence",
                "subject": "Geralt",
                "predicate": "present_in",
                "object": "scene.demo.scene001",
                "status": "PROPOSED",
            }
        )
        + "\n{bad json\n",
        encoding="utf-8",
    )

    summary = run_claim_audit_summary(claims_path)

    assert summary["MRLORE_PROPOSED_CLAIM_AUDIT_SUMMARY_COMPLETE"] is False
    assert summary["CLAIMS_READ"] == 1
    assert summary["read_errors_count"] == 1
    assert summary["CANON_WRITTEN"] is False
    assert summary["RUNTIME_TOUCHED"] is False
