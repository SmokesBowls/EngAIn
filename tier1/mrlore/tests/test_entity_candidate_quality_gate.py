from __future__ import annotations

import json
from pathlib import Path

import pytest

from tier1.mrlore.mrlore_entity_candidate_quality_gate import run_entity_candidate_quality_gate
from tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate import run_preserve_entity_allowlist_registry_gate


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _claim(claim_id: str, subject: str, claim_domain: str = "entity", claim_type: str = "entity_presence") -> dict:
    return {
        "claim_id": claim_id,
        "claim_domain": claim_domain,
        "claim_type": claim_type,
        "subject": subject,
        "predicate": "present_in" if claim_type == "entity_presence" else "terrain_family",
        "object": "scene.demo.001" if claim_type == "entity_presence" else "coastal",
        "SOURCE_SCENE": "scene.demo.001",
        "source_scene": "scene.demo.001",
        "source_line": 12,
        "status": "PROPOSED",
    }


def _write_preserve_registry(engain_dir: Path, terms: list[str] | None = None) -> Path:
    registry_path = engain_dir / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_terms = terms or ["Aeon Keeper", "Akashic Library", "Annunaki", "Marduk", "Luminaire"]
    registry_path.write_text(
        json.dumps(
            {
                "contract": "engain.mrlore_preserve_entity_allowlist.v1",
                "registry_type": "PRESERVE_ENTITY_ALLOWLIST",
                "authority_owner": "NARRATIVE_TEAM",
                "runtime_authority": False,
                "canon_authority": False,
                "terms": [
                    {"term": term, "term_type": "unknown_lore_entity", "status": "ACTIVE"}
                    for term in registry_terms
                ],
            }
        ),
        encoding="utf-8",
    )
    run_preserve_entity_allowlist_registry_gate(registry_path)
    return registry_path


def test_entity_candidate_quality_gate_flags_bad_entity_subjects_sidecar_only(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    records = [
        _claim("claim.bad.common", "About"),
        _claim("claim.bad.verb", "Accessing"),
        _claim("claim.bad.possessive", "Aelxion’s"),
        _claim("claim.bad.newline", "AFTERMATH\n\nThe"),
        _claim("claim.bad.question", "Am I"),
        _claim("claim.bad.generic", "Anger"),
        _claim("claim.good.aeon", "Aeon Keeper"),
        _claim("claim.good.library", "Akashic Library"),
        _claim("claim.good.annunaki", "Annunaki"),
        _claim("claim.good.marduk", "Marduk"),
        _claim("claim.good.luminaire_possessive", "Luminaire’s"),
        _claim("claim.env", "scene.demo.001", claim_domain="environment", claim_type="environment_state"),
    ]
    _write_jsonl(claims_path, records)
    _write_preserve_registry(engain_dir)
    before_claims = claims_path.read_text(encoding="utf-8")

    manifest = run_entity_candidate_quality_gate(claims_path)

    assert manifest["MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE"] is True
    assert manifest["PROPOSED_CLAIMS_READ"] == len(records)
    assert manifest["ENTITY_PRESENCE_CLAIMS_CHECKED"] == 11
    assert manifest["QUALITY_FLAGS_WRITTEN"] == 6
    assert manifest["QUALITY_GATE_CAN_CONSUME"] is True
    assert manifest["PROPOSED_CLAIMS_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert claims_path.read_text(encoding="utf-8") == before_claims

    flags_path = engain_dir / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"
    flags = [json.loads(line) for line in flags_path.read_text(encoding="utf-8").splitlines()]
    assert [flag["claim_id"] for flag in flags] == [
        "claim.bad.common",
        "claim.bad.verb",
        "claim.bad.possessive",
        "claim.bad.newline",
        "claim.bad.question",
        "claim.bad.generic",
    ]
    reasons = {flag["claim_id"]: flag["quality_reasons"] for flag in flags}
    assert "single_common_word" in reasons["claim.bad.common"]
    assert "verb_or_adjective_candidate" in reasons["claim.bad.verb"]
    assert "possessive_fragment" in reasons["claim.bad.possessive"]
    assert "contains_newline_fragment" in reasons["claim.bad.newline"]
    assert "question_fragment" in reasons["claim.bad.question"]
    assert "generic_abstract_noun" in reasons["claim.bad.generic"]
    assert all(flag["status"] == "QUALITY_REVIEW_FLAGGED" for flag in flags)
    assert all(flag["claim_rejected"] is False for flag in flags)
    assert all(flag["claim_promoted"] is False for flag in flags)

    manifest_path = engain_dir / "manifests" / "mrlore_entity_candidate_quality_gate_manifest.json"
    assert manifest_path.exists()


def test_entity_candidate_quality_gate_fails_closed_without_valid_preserve_registry_gate(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    _write_jsonl(claims_path, [_claim("claim.good.aeon", "Aeon Keeper")])
    before_claims = claims_path.read_text(encoding="utf-8")

    with pytest.raises(RuntimeError, match="Preserve entity allowlist registry is invalid"):
        run_entity_candidate_quality_gate(claims_path)

    assert claims_path.read_text(encoding="utf-8") == before_claims
    manifest_path = engain_dir / "manifests" / "mrlore_entity_candidate_quality_gate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE"] is False
    assert manifest["QUALITY_GATE_CAN_CONSUME"] is False
    assert manifest["PROPOSED_CLAIMS_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CANON_WRITTEN"] is False


def test_entity_candidate_quality_gate_records_read_errors_without_mutating_claims(tmp_path: Path) -> None:
    claims_path = tmp_path / ".engain" / "mrlore" / "claims" / "proposed_claims.jsonl"
    claims_path.parent.mkdir(parents=True, exist_ok=True)
    claims_path.write_text(json.dumps(_claim("claim.bad.common", "About")) + "\n{bad json\n", encoding="utf-8")
    _write_preserve_registry(tmp_path / ".engain")
    before_claims = claims_path.read_text(encoding="utf-8")

    manifest = run_entity_candidate_quality_gate(claims_path)

    assert manifest["MRLORE_ENTITY_CANDIDATE_QUALITY_GATE_COMPLETE"] is False
    assert manifest["PROPOSED_CLAIMS_READ"] == 1
    assert manifest["ENTITY_PRESENCE_CLAIMS_CHECKED"] == 1
    assert manifest["QUALITY_FLAGS_WRITTEN"] == 1
    assert manifest["read_errors_count"] == 1
    assert manifest["PROPOSED_CLAIMS_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert claims_path.read_text(encoding="utf-8") == before_claims
