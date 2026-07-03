from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_proposed_claim_shape_gate import run_claim_shape_gate


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def test_claim_shape_gate_accepts_only_structurally_safe_proposed_claims(tmp_path: Path) -> None:
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
        ],
    )

    manifest = run_claim_shape_gate(claims_path)

    assert manifest["MRLORE_CLAIM_SHAPE_GATE_COMPLETE"] is True
    assert manifest["CLAIMS_CHECKED"] == 2
    assert manifest["CLAIMS_PASSED"] == 2
    assert manifest["CLAIMS_FAILED"] == 0
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert manifest["raw_chapter_primary_authority_used"] is False
    assert manifest["legal_claim_domains"] == ["entity", "environment"]
    assert manifest["failures"] == []

    manifest_path = engain_dir / "manifests" / "claim_shape_gate_manifest.json"
    assert manifest_path.exists()
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["CLAIMS_PASSED"] == 2


def test_claim_shape_gate_rejects_missing_source_scene_non_proposed_illegal_domain_and_raw_chapter_authority(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    _write_jsonl(
        claims_path,
        [
            {
                "claim_id": "claim.no-source-scene",
                "claim_domain": "entity",
                "claim_type": "entity_presence",
                "subject": "Geralt",
                "predicate": "present_in",
                "object": "scene.demo.scene001",
                "status": "PROPOSED",
            },
            {
                "claim_id": "claim.canon",
                "SOURCE_SCENE": "scene.demo.scene001",
                "claim_domain": "entity",
                "claim_type": "entity_presence",
                "subject": "Geralt",
                "predicate": "present_in",
                "object": "scene.demo.scene001",
                "status": "CANON",
            },
            {
                "claim_id": "claim.bad-domain",
                "SOURCE_SCENE": "scene.demo.scene001",
                "claim_domain": "timeline",
                "claim_type": "timeline_state",
                "subject": "scene.demo.scene001",
                "predicate": "year",
                "object": "3100",
                "status": "PROPOSED",
            },
            {
                "claim_id": "claim.raw-authority",
                "SOURCE_SCENE": "scene.demo.scene001",
                "claim_domain": "environment",
                "claim_type": "environment_state",
                "subject": "scene.demo.scene001",
                "predicate": "terrain_family",
                "object": "coastal",
                "status": "PROPOSED",
                "primary_authority": "/vault/raw/chapters/chapter001.txt",
            },
        ],
    )

    manifest = run_claim_shape_gate(claims_path)

    assert manifest["MRLORE_CLAIM_SHAPE_GATE_COMPLETE"] is False
    assert manifest["CLAIMS_CHECKED"] == 4
    assert manifest["CLAIMS_PASSED"] == 0
    assert manifest["CLAIMS_FAILED"] == 4
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["raw_chapter_primary_authority_used"] is True
    failure_text = json.dumps(manifest["failures"], sort_keys=True)
    assert "missing required field: SOURCE_SCENE" in failure_text
    assert "status must be PROPOSED" in failure_text
    assert "illegal claim_domain" in failure_text
    assert "raw chapter primary authority" in failure_text
