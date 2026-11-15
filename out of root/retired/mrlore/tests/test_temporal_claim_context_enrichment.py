from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_temporal_claim_context_enrichment import run_temporal_claim_context_enrichment


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _claim(claim_id: str, source_scene: str | None = "scene.book001.001_alpha.scene001") -> dict:
    claim = {
        "claim_id": claim_id,
        "claim_domain": "entity",
        "claim_type": "entity_presence",
        "subject": "Marduk",
        "predicate": "present_in",
        "object": source_scene or "unknown",
        "status": "PROPOSED",
        "source_line": 7,
    }
    if source_scene is not None:
        claim["SOURCE_SCENE"] = source_scene
        claim["source_scene"] = source_scene
    return claim


def _scene_intake_manifest() -> dict:
    return {
        "contract": "engain.mrlore_scene_intake_manifest.v1",
        "chapters": [
            {
                "chapter_id": "chapter.book001.001_alpha",
                "scene_count": 2,
                "status": "MRLORE_READY",
                "scenes": [
                    {"scene_id": "scene.book001.001_alpha.scene001", "scene_index": 1, "mr_lore_ready": True},
                    {"scene_id": "scene.book001.001_alpha.scene002", "scene_index": 2, "mr_lore_ready": True},
                ],
            },
            {
                "chapter_id": "chapter.book001.002_beta",
                "scene_count": 1,
                "status": "MRLORE_READY",
                "scenes": [
                    {"scene_id": "scene.book001.002_beta.scene001", "scene_index": 1, "mr_lore_ready": True},
                ],
            },
        ],
    }


def test_temporal_claim_context_enrichment_writes_enriched_jsonl_with_scene_order_metadata(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    scene_manifest_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    claims = [
        _claim("claim.alpha.1", "scene.book001.001_alpha.scene001"),
        _claim("claim.alpha.2", "scene.book001.001_alpha.scene002"),
        _claim("claim.beta.1", "scene.book001.002_beta.scene001"),
    ]
    _write_jsonl(claims_path, claims)
    _write_json(scene_manifest_path, _scene_intake_manifest())

    manifest = run_temporal_claim_context_enrichment(claims_path, scene_manifest_path)

    assert manifest["MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE"] is True
    assert manifest["CLAIMS_READ"] == 3
    assert manifest["CLAIMS_WRITTEN"] == 3
    assert manifest["CLAIMS_TEMPORAL_ENRICHED"] == 3
    assert manifest["CLAIMS_TEMPORAL_UNRESOLVED"] == 0
    assert manifest["TEMPORAL_BASIS"] == "CHAPTERROOM_SCENE_ORDER"
    assert manifest["ENGINE_AGNOSTIC"] is True
    assert manifest["GODOT_USED_AS_TEMPORAL_AUTHORITY"] is False

    enriched_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    enriched = [json.loads(line) for line in enriched_path.read_text(encoding="utf-8").splitlines()]
    assert [claim["claim_id"] for claim in enriched] == ["claim.alpha.1", "claim.alpha.2", "claim.beta.1"]
    assert enriched[0]["source_scene_id"] == "scene.book001.001_alpha.scene001"
    assert enriched[0]["chapter_id"] == "chapter.book001.001_alpha"
    assert enriched[0]["scene_index"] == 1
    assert enriched[0]["chapter_sequence_index"] == 1
    assert enriched[0]["global_scene_sequence_index"] == 1
    assert enriched[0]["temporal_index"] == 1.001
    assert enriched[0]["temporal_basis"] == "CHAPTERROOM_SCENE_ORDER"
    assert enriched[0]["temporal_confidence"] == 1.0
    assert enriched[0]["temporal_scope"] == "SCENE_SEQUENTIAL"
    assert enriched[1]["global_scene_sequence_index"] == 2
    assert enriched[1]["temporal_index"] == 2.002
    assert enriched[2]["chapter_sequence_index"] == 2
    assert enriched[2]["global_scene_sequence_index"] == 3
    assert enriched[2]["temporal_index"] == 3.001


def test_temporal_claim_context_enrichment_does_not_alter_original_proposed_claims(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    scene_manifest_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    _write_jsonl(claims_path, [_claim("claim.alpha.1")])
    _write_json(scene_manifest_path, _scene_intake_manifest())
    before_claims = claims_path.read_text(encoding="utf-8")

    manifest = run_temporal_claim_context_enrichment(claims_path, scene_manifest_path)

    assert claims_path.read_text(encoding="utf-8") == before_claims
    assert manifest["PROPOSED_CLAIMS_ALTERED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False


def test_temporal_claim_context_enrichment_records_unresolved_scenes_without_mutating_source_claims(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    scene_manifest_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    unresolved_claim = _claim("claim.unknown", "scene.book999.unknown.scene001")
    _write_jsonl(claims_path, [unresolved_claim])
    _write_json(scene_manifest_path, _scene_intake_manifest())
    before_claims = claims_path.read_text(encoding="utf-8")

    manifest = run_temporal_claim_context_enrichment(claims_path, scene_manifest_path)

    assert claims_path.read_text(encoding="utf-8") == before_claims
    assert manifest["MRLORE_TEMPORAL_CLAIM_CONTEXT_ENRICHMENT_COMPLETE"] is True
    assert manifest["CLAIMS_READ"] == 1
    assert manifest["CLAIMS_WRITTEN"] == 1
    assert manifest["CLAIMS_TEMPORAL_ENRICHED"] == 0
    assert manifest["CLAIMS_TEMPORAL_UNRESOLVED"] == 1
    assert manifest["errors_count"] == 1
    assert "claim.unknown" in manifest["errors"][0]
    assert "scene.book999.unknown.scene001" in manifest["errors"][0]

    enriched_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    enriched = [json.loads(line) for line in enriched_path.read_text(encoding="utf-8").splitlines()]
    assert enriched[0]["claim_id"] == "claim.unknown"
    assert enriched[0]["source_scene_id"] == "scene.book999.unknown.scene001"
    assert enriched[0]["temporal_confidence"] == 0.0
    assert enriched[0]["temporal_basis"] == "UNRESOLVED_SCENE_ORDER"
    assert enriched[0]["temporal_scope"] == "SCENE_SEQUENTIAL"
    assert "chapter_id" not in enriched[0]
    assert "global_scene_sequence_index" not in enriched[0]


def test_temporal_claim_context_enrichment_keeps_godot_runtime_canon_zonj_flags_false(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    scene_manifest_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    _write_jsonl(claims_path, [_claim("claim.alpha.1")])
    _write_json(scene_manifest_path, _scene_intake_manifest())

    manifest = run_temporal_claim_context_enrichment(claims_path, scene_manifest_path)

    assert manifest["ENGINE_AGNOSTIC"] is True
    assert manifest["GODOT_USED_AS_TEMPORAL_AUTHORITY"] is False
    assert manifest["PROPOSED_CLAIMS_ALTERED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False

    manifest_path = engain_dir / "manifests" / "mrlore_temporal_claim_context_manifest.json"
    written_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written_manifest["GODOT_TOUCHED"] is False
    assert written_manifest["RUNTIME_TOUCHED"] is False
