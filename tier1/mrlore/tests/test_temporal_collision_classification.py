from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_predicate_collision_policy_registry_gate import (
    run_predicate_collision_policy_registry_gate,
)
from tier1.mrlore.mrlore_temporal_collision_classification import run_temporal_collision_classification


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _write_policy_and_gate(engain_dir: Path, exclusive_predicates: list[str] | None = None) -> None:
    registry_path = engain_dir / "mrlore" / "lexicon" / "predicate_collision_policy.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "contract": "engain.mrlore_predicate_collision_policy.v1",
                "policy_effect": "REVIEW_CLASSIFICATION_ONLY",
                "runtime_authority": False,
                "canon_authority": False,
                "predicate_classes": {
                    "MULTI_VALUED_HINT": ["atmospheric_hints", "boundary_hints", "hazard_hints", "path_hints"],
                    "TRANSIENT_STATE": ["present_in", "located_at", "standing_near", "holding", "facing", "traveling_to"],
                    "DURABLE_STATE": ["dead", "destroyed", "sealed", "married_to", "crowned_as", "missing_limb", "owner_of", "parent_of"],
                    "EXCLUSIVE_STATE": exclusive_predicates or [],
                    "UNKNOWN_REVIEW": [],
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    manifest = run_predicate_collision_policy_registry_gate(registry_path)
    assert manifest["MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE"] is True


def _enriched_claim(claim_id: str, scene: str, predicate: str, obj: str, temporal_index: float | None, domain: str = "entity") -> dict:
    claim = {
        "claim_id": claim_id,
        "SOURCE_SCENE": scene,
        "source_scene": scene,
        "source_scene_id": scene,
        "claim_domain": domain,
        "claim_type": "entity_presence",
        "subject": "Aldrin",
        "predicate": predicate,
        "object": obj,
        "status": "PROPOSED",
        "temporal_basis": "CHAPTERROOM_SCENE_ORDER" if temporal_index is not None else "UNRESOLVED_SCENE_ORDER",
        "temporal_confidence": 1.0 if temporal_index is not None else 0.0,
        "temporal_scope": "SCENE_SEQUENTIAL",
    }
    if temporal_index is not None:
        claim["temporal_index"] = temporal_index
    return claim


def _candidate(candidate_id: str, predicate: str, objects: list[str], refs_by_object: dict[str, list[dict]], subject: str = "Aldrin", domain: str = "entity") -> dict:
    return {
        "candidate_id": candidate_id,
        "candidate_type": "same_subject_predicate_different_object",
        "claim_domain": domain,
        "subject": subject,
        "predicate": predicate,
        "objects": objects,
        "source_scenes": sorted({ref["SOURCE_SCENE"] for refs in refs_by_object.values() for ref in refs}),
        "object_claim_refs": refs_by_object,
        "reasons": ["same_subject_same_predicate_different_object"],
        "resolved": False,
        "CONTRADICTION_RESOLVED": False,
        "CANON_WRITTEN": False,
    }


def _ref(claim_id: str, scene: str) -> dict:
    return {"claim_id": claim_id, "SOURCE_SCENE": scene, "source_line": 1}


def test_transient_present_in_ordered_different_objects_becomes_sequential_state_change(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir)
    _write_jsonl(
        claims_path,
        [
            _enriched_claim("claim.a", "scene.alpha.001", "present_in", "room.a", 1.001),
            _enriched_claim("claim.b", "scene.alpha.002", "present_in", "room.b", 2.002),
        ],
    )
    _write_jsonl(candidates_path, [_candidate("cand.move", "present_in", ["room.a", "room.b"], {"room.a": [_ref("claim.a", "scene.alpha.001")], "room.b": [_ref("claim.b", "scene.alpha.002")]})])

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert manifest["MRLORE_TEMPORAL_COLLISION_CLASSIFICATION_COMPLETE"] is True
    assert manifest["CANDIDATES_READ"] == 1
    assert manifest["CLASSIFICATIONS_WRITTEN"] == 1
    assert manifest["SEQUENTIAL_STATE_CHANGE_COUNT"] == 1
    sidecar_path = engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl"
    records = [json.loads(line) for line in sidecar_path.read_text(encoding="utf-8").splitlines()]
    assert records[0]["candidate_id"] == "cand.move"
    assert records[0]["classification"] == "SEQUENTIAL_STATE_CHANGE"
    assert records[0]["temporal_basis"] == "CHAPTERROOM_SCENE_ORDER"
    assert records[0]["temporal_indexes"] == [1.001, 2.002]
    assert records[0]["authority_effect"] == "NONE"


def test_transient_present_in_equal_temporal_indexes_becomes_concurrent_collision(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir)
    _write_jsonl(claims_path, [_enriched_claim("claim.a", "scene.same.001", "present_in", "room.a", 1.001), _enriched_claim("claim.b", "scene.same.002", "present_in", "room.b", 1.001)])
    _write_jsonl(candidates_path, [_candidate("cand.concurrent", "present_in", ["room.a", "room.b"], {"room.a": [_ref("claim.a", "scene.same.001")], "room.b": [_ref("claim.b", "scene.same.002")]})])

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert manifest["CONCURRENT_OBJECT_COLLISION_COUNT"] == 1
    record = json.loads((engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["classification"] == "CONCURRENT_OBJECT_COLLISION"
    assert "equal or overlapping temporal indexes" in record["reason"]


def test_durable_state_ordered_different_objects_becomes_durable_continuity_review(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir)
    _write_jsonl(claims_path, [_enriched_claim("claim.dead.yes", "scene.dead.001", "dead", "true", 1.001), _enriched_claim("claim.dead.no", "scene.dead.002", "dead", "false", 2.001)])
    _write_jsonl(candidates_path, [_candidate("cand.dead", "dead", ["false", "true"], {"true": [_ref("claim.dead.yes", "scene.dead.001")], "false": [_ref("claim.dead.no", "scene.dead.002")]})])

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert manifest["DURABLE_STATE_CONTINUITY_REVIEW_COUNT"] == 1
    record = json.loads((engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["classification"] == "DURABLE_STATE_CONTINUITY_REVIEW"


def test_environment_multi_valued_hint_same_scene_becomes_accumulation_not_collision(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir)
    _write_jsonl(
        claims_path,
        [
            _enriched_claim("claim.edge", "scene.env.001", "boundary_hints", "edge", 1.001, domain="environment"),
            _enriched_claim("claim.limit", "scene.env.001", "boundary_hints", "limit", 1.001, domain="environment"),
        ],
    )
    _write_jsonl(
        candidates_path,
        [
            _candidate(
                "cand.env.hints",
                "boundary_hints",
                ["edge", "limit"],
                {"edge": [_ref("claim.edge", "scene.env.001")], "limit": [_ref("claim.limit", "scene.env.001")]},
                subject="scene.env.001",
                domain="environment",
            )
        ],
    )

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert manifest["ENVIRONMENT_MULTI_HINT_ACCUMULATION_COUNT"] == 1
    assert manifest["CONCURRENT_OBJECT_COLLISION_COUNT"] == 0
    record = json.loads((engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["classification"] == "ENVIRONMENT_MULTI_HINT_ACCUMULATION"
    assert record["predicate_class"] == "MULTI_VALUED_HINT"
    assert record["authority_effect"] == "NONE"


def test_exclusive_state_equal_temporal_indexes_becomes_concurrent_collision(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir, exclusive_predicates=["active_form"])
    _write_jsonl(claims_path, [_enriched_claim("claim.a", "scene.form.001", "active_form", "dragon", 1.001), _enriched_claim("claim.b", "scene.form.001", "active_form", "human", 1.001)])
    _write_jsonl(candidates_path, [_candidate("cand.form", "active_form", ["dragon", "human"], {"dragon": [_ref("claim.a", "scene.form.001")], "human": [_ref("claim.b", "scene.form.001")]})])

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert manifest["CONCURRENT_OBJECT_COLLISION_COUNT"] == 1
    record = json.loads((engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["classification"] == "CONCURRENT_OBJECT_COLLISION"
    assert record["predicate_class"] == "EXCLUSIVE_STATE"


def test_missing_temporal_index_becomes_temporal_order_unknown_review(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir)
    _write_jsonl(claims_path, [_enriched_claim("claim.a", "scene.unknown.001", "present_in", "room.a", None), _enriched_claim("claim.b", "scene.unknown.002", "present_in", "room.b", 2.001)])
    _write_jsonl(candidates_path, [_candidate("cand.unknown", "present_in", ["room.a", "room.b"], {"room.a": [_ref("claim.a", "scene.unknown.001")], "room.b": [_ref("claim.b", "scene.unknown.002")]})])

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert manifest["TEMPORAL_ORDER_UNKNOWN_REVIEW_COUNT"] == 1
    record = json.loads((engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["classification"] == "TEMPORAL_ORDER_UNKNOWN_REVIEW"


def test_same_object_becomes_no_conflict_same_object_and_candidates_are_not_mutated(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir)
    _write_jsonl(claims_path, [_enriched_claim("claim.a", "scene.sameobj.001", "located_at", "room.a", 1.001), _enriched_claim("claim.b", "scene.sameobj.002", "located_at", "room.a", 2.001)])
    _write_jsonl(candidates_path, [_candidate("cand.same", "located_at", ["room.a"], {"room.a": [_ref("claim.a", "scene.sameobj.001"), _ref("claim.b", "scene.sameobj.002")]})])
    before_candidates = candidates_path.read_text(encoding="utf-8")
    before_claims = claims_path.read_text(encoding="utf-8")

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert candidates_path.read_text(encoding="utf-8") == before_candidates
    assert claims_path.read_text(encoding="utf-8") == before_claims
    assert manifest["NO_CONFLICT_SAME_OBJECT_COUNT"] == 1
    assert manifest["SIDE_CAR_ONLY"] is True
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLAIMS_ALTERED"] is False
    record = json.loads((engain_dir / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["classification"] == "NO_CONFLICT_SAME_OBJECT"


def test_temporal_collision_classification_authority_flags_remain_false(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    candidates_path = engain_dir / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"
    _write_policy_and_gate(engain_dir)
    _write_jsonl(claims_path, [_enriched_claim("claim.a", "scene.flags.001", "present_in", "room.a", 1.001), _enriched_claim("claim.b", "scene.flags.002", "present_in", "room.b", 2.001)])
    _write_jsonl(candidates_path, [_candidate("cand.flags", "present_in", ["room.a", "room.b"], {"room.a": [_ref("claim.a", "scene.flags.001")], "room.b": [_ref("claim.b", "scene.flags.002")]})])

    manifest = run_temporal_collision_classification(claims_path, candidates_path)

    assert manifest["SIDE_CAR_ONLY"] is True
    assert manifest["CANDIDATES_ALTERED"] is False
    assert manifest["CLAIMS_ALTERED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert manifest["ENGINE_AGNOSTIC"] is True
    assert manifest["GODOT_USED_AS_TEMPORAL_AUTHORITY"] is False
    written_manifest = json.loads((engain_dir / "manifests" / "mrlore_temporal_collision_classification_manifest.json").read_text(encoding="utf-8"))
    assert written_manifest["GODOT_USED_AS_TEMPORAL_AUTHORITY"] is False
