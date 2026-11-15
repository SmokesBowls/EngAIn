from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_predicate_collision_policy_registry_gate import (
    run_predicate_collision_policy_registry_gate,
)


def _policy() -> dict:
    return {
        "contract": "engain.mrlore_predicate_collision_policy.v1",
        "policy_effect": "REVIEW_CLASSIFICATION_ONLY",
        "runtime_authority": False,
        "canon_authority": False,
        "predicate_classes": {
            "MULTI_VALUED_HINT": ["atmospheric_hints", "boundary_hints", "hazard_hints", "path_hints"],
            "TRANSIENT_STATE": ["present_in", "located_at", "standing_near", "holding", "facing", "traveling_to"],
            "DURABLE_STATE": ["dead", "destroyed", "sealed", "married_to", "crowned_as", "missing_limb", "owner_of", "parent_of"],
            "EXCLUSIVE_STATE": ["active_form"],
            "UNKNOWN_REVIEW": [],
        },
    }


def test_predicate_collision_policy_registry_gate_validates_policy_and_writes_manifest(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "lexicon" / "predicate_collision_policy.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(_policy(), sort_keys=True), encoding="utf-8")
    before_registry = registry_path.read_text(encoding="utf-8")

    manifest = run_predicate_collision_policy_registry_gate(registry_path)

    assert manifest["MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE"] is True
    assert manifest["REGISTRY_FOUND"] is True
    assert manifest["REGISTRY_JSON_VALID"] is True
    assert manifest["REGISTRY_SCHEMA_VALID"] is True
    assert manifest["PREDICATES_LOADED"] == 19
    assert manifest["DUPLICATE_PREDICATES_FOUND"] is False
    assert manifest["POLICY_EFFECT"] == "REVIEW_CLASSIFICATION_ONLY"
    assert manifest["RUNTIME_AUTHORITY"] is False
    assert manifest["CANON_AUTHORITY"] is False
    assert manifest["TEMPORAL_CLASSIFIER_CAN_CONSUME"] is True
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert manifest["errors"] == []
    assert manifest["errors_count"] == 0
    assert registry_path.read_text(encoding="utf-8") == before_registry

    written_manifest = json.loads((engain_dir / "manifests" / "predicate_collision_policy_registry_gate_manifest.json").read_text(encoding="utf-8"))
    assert written_manifest["TEMPORAL_CLASSIFIER_CAN_CONSUME"] is True


def test_predicate_collision_policy_registry_gate_rejects_duplicate_predicate_across_classes(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "lexicon" / "predicate_collision_policy.json"
    policy = _policy()
    policy["predicate_classes"]["DURABLE_STATE"].append("present_in")
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(policy, sort_keys=True), encoding="utf-8")

    manifest = run_predicate_collision_policy_registry_gate(registry_path)

    assert manifest["MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["REGISTRY_FOUND"] is True
    assert manifest["REGISTRY_JSON_VALID"] is True
    assert manifest["DUPLICATE_PREDICATES_FOUND"] is True
    assert manifest["TEMPORAL_CLASSIFIER_CAN_CONSUME"] is False
    assert manifest["errors_count"] > 0


def test_predicate_collision_policy_registry_gate_rejects_authority_or_wrong_effect(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "lexicon" / "predicate_collision_policy.json"
    policy = _policy()
    policy["runtime_authority"] = True
    policy["policy_effect"] = "CANON_WRITE"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(policy, sort_keys=True), encoding="utf-8")

    manifest = run_predicate_collision_policy_registry_gate(registry_path)

    assert manifest["MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["POLICY_EFFECT"] == "CANON_WRITE"
    assert manifest["RUNTIME_AUTHORITY"] is True
    assert manifest["CANON_AUTHORITY"] is False
    assert manifest["TEMPORAL_CLASSIFIER_CAN_CONSUME"] is False
    assert any("policy_effect" in error or "runtime_authority" in error for error in manifest["errors"])
