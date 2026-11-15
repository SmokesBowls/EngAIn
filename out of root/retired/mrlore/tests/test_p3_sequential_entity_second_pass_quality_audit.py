from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_p3_sequential_entity_second_pass_quality_audit import (
    run_p3_sequential_entity_second_pass_quality_audit,
)


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _queue_item(
    queue_id: str,
    subject: str,
    bucket: str = "P3_SEQUENTIAL_STATE_CHANGE",
    domain: str = "entity",
    predicate: str = "present_in",
) -> dict:
    return {
        "queue_id": queue_id,
        "candidate_id": f"candidate.{queue_id}",
        "priority_bucket": bucket,
        "bucket": bucket,
        "claim_domain": domain,
        "domain": domain,
        "subject": subject,
        "predicate": predicate,
        "authority_effect": "NONE",
    }


def _write_preserve_registry(engain_dir: Path) -> tuple[Path, Path]:
    registry_path = engain_dir / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    manifest_path = engain_dir / "manifests" / "preserve_entity_allowlist_registry_gate_manifest.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "contract": "engain.mrlore_preserve_entity_allowlist.v1",
                "registry_type": "PRESERVE_ENTITY_ALLOWLIST",
                "authority_owner": "NARRATIVE_TEAM",
                "runtime_authority": False,
                "canon_authority": False,
                "terms": [
                    {"term": "I", "term_type": "character", "status": "ACTIVE"},
                    {"term": "Before", "term_type": "event", "status": "PROPOSED"},
                    {"term": "Deprecated Noise", "term_type": "concept", "status": "DEPRECATED"},
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "registry_path": str(registry_path.resolve()),
                "MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE": True,
                "QUALITY_GATE_CAN_CONSUME": True,
                "CANON_WRITTEN": False,
                "RUNTIME_TOUCHED": False,
                "GODOT_TOUCHED": False,
                "ZONJ_COMPILED": False,
                "errors": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return registry_path, manifest_path


def test_p3_second_pass_flags_pronouns_determiners_connectors_and_verbs_without_mutating_queue(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    registry_path, gate_manifest_path = _write_preserve_registry(engain_dir)
    records = [
        _queue_item("q1", "I'm"),
        _queue_item("q2", "All"),
        _queue_item("q3", "Across"),
        _queue_item("q4", "Could"),
        _queue_item("q5", "Ancient"),
        _queue_item("q6", "Within", bucket="P4_ENVIRONMENT_REVIEW"),
        _queue_item("q7", "Yes", predicate="located_at"),
        _queue_item("q8", "No", domain="environment"),
    ]
    _write_jsonl(queue_path, records)
    before_queue = queue_path.read_bytes()

    manifest = run_p3_sequential_entity_second_pass_quality_audit(
        queue_path=queue_path,
        preserve_registry_path=registry_path,
        preserve_gate_manifest_path=gate_manifest_path,
    )

    assert manifest["MRLORE_P3_SEQUENTIAL_ENTITY_SECOND_PASS_QUALITY_AUDIT_COMPLETE"] is True
    assert manifest["QUEUE_ITEMS_READ"] == 8
    assert manifest["P3_ENTITY_ITEMS_CHECKED"] == 5
    assert manifest["SECOND_PASS_FLAGS_WRITTEN"] == 4
    assert manifest["PRESERVE_REGISTRY_USED"] is True
    assert manifest["PRESERVED_TERMS_SKIPPED"] == 0
    assert queue_path.read_bytes() == before_queue

    flag_path = engain_dir / "mrlore" / "review" / "temporal_aware_p3_second_pass_quality_flags.jsonl"
    flags = [json.loads(line) for line in flag_path.read_text(encoding="utf-8").splitlines()]
    by_subject = {flag["subject"]: flag for flag in flags}
    assert by_subject["I'm"]["second_pass_reasons"] == ["pronoun_or_contraction"]
    assert by_subject["All"]["second_pass_reasons"] == ["determiner_or_quantifier"]
    assert by_subject["Across"]["second_pass_reasons"] == ["connector_or_preposition"]
    assert by_subject["Could"]["second_pass_reasons"] == ["modal_or_common_verb"]
    assert "Ancient" not in by_subject
    for flag in flags:
        assert flag["authority_effect"] == "NONE"
        assert flag["bucket"] == "P3_SEQUENTIAL_STATE_CHANGE"
        assert flag["domain"] == "entity"
        assert flag["predicate"] == "present_in"


def test_p3_second_pass_preserve_registry_terms_are_not_flagged_and_other_filter_hits_are_flagged(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    registry_path, gate_manifest_path = _write_preserve_registry(engain_dir)
    _write_jsonl(
        queue_path,
        [
            _queue_item("q1", "I"),
            _queue_item("q2", "Before"),
            _queue_item("q3", "No"),
            _queue_item("q4", "Someone"),
            _queue_item("q5", "Ten"),
            _queue_item("q6", "CHAPTER SUMMARY: residual header"),
            _queue_item("q7", "This is a leftover sentence fragment"),
        ],
    )
    before_queue = queue_path.read_text(encoding="utf-8")

    manifest = run_p3_sequential_entity_second_pass_quality_audit(
        queue_path=queue_path,
        preserve_registry_path=registry_path,
        preserve_gate_manifest_path=gate_manifest_path,
    )

    assert manifest["P3_ENTITY_ITEMS_CHECKED"] == 7
    assert manifest["SECOND_PASS_FLAGS_WRITTEN"] == 5
    assert manifest["PRESERVED_TERMS_SKIPPED"] == 2
    assert queue_path.read_text(encoding="utf-8") == before_queue
    flag_path = engain_dir / "mrlore" / "review" / "temporal_aware_p3_second_pass_quality_flags.jsonl"
    flags = [json.loads(line) for line in flag_path.read_text(encoding="utf-8").splitlines()]
    by_subject = {flag["subject"]: flag for flag in flags}
    assert "I" not in by_subject
    assert "Before" not in by_subject
    assert by_subject["Someone"]["second_pass_reasons"] == ["vague_reference_word"]
    assert by_subject["Ten"]["second_pass_reasons"] == ["numeric_word"]
    assert by_subject["CHAPTER SUMMARY: residual header"]["second_pass_reasons"] == ["source_markup_fragment"]
    assert by_subject["This is a leftover sentence fragment"]["second_pass_reasons"] == ["likely_sentence_fragment"]


def test_p3_second_pass_manifest_keeps_all_safety_flags_false(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    queue_path = engain_dir / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"
    registry_path, gate_manifest_path = _write_preserve_registry(engain_dir)
    _write_jsonl(queue_path, [_queue_item("q1", "You’re")])

    manifest = run_p3_sequential_entity_second_pass_quality_audit(
        queue_path=queue_path,
        preserve_registry_path=registry_path,
        preserve_gate_manifest_path=gate_manifest_path,
    )

    assert manifest["SOURCE_QUEUE_ALTERED"] is False
    assert manifest["CLAIMS_ALTERED"] is False
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert manifest["errors"] == []
    assert manifest["errors_count"] == 0

    manifest_path = engain_dir / "manifests" / "temporal_aware_p3_second_pass_quality_manifest.json"
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["SECOND_PASS_FLAGS_WRITTEN"] == 1
