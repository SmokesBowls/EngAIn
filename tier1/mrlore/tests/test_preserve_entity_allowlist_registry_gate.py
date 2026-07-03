from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate import (
    load_consumable_preserve_terms,
    run_preserve_entity_allowlist_registry_gate,
)


def _registry(terms: list[dict], **overrides: object) -> dict:
    data = {
        "contract": "engain.mrlore_preserve_entity_allowlist.v1",
        "registry_type": "PRESERVE_ENTITY_ALLOWLIST",
        "authority_owner": "NARRATIVE_TEAM",
        "runtime_authority": False,
        "canon_authority": False,
        "description": "Known valid lore terms that should not be treated as extraction noise.",
        "terms": terms,
    }
    data.update(overrides)
    return data


def _term(term: str, term_type: str = "title", status: str = "ACTIVE") -> dict:
    return {
        "term": term,
        "term_type": term_type,
        "status": status,
        "notes": "test term",
    }


def test_registry_gate_accepts_valid_active_and_proposed_terms_without_authority(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            _registry([
                _term("Aeon Keeper", "title", "ACTIVE"),
                _term("The Ashen Choir", "faction", "PROPOSED"),
                _term("Old Noise", "concept", "DEPRECATED"),
            ])
        ),
        encoding="utf-8",
    )

    manifest = run_preserve_entity_allowlist_registry_gate(registry_path)

    assert manifest["MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE"] is True
    assert manifest["REGISTRY_FOUND"] is True
    assert manifest["REGISTRY_JSON_VALID"] is True
    assert manifest["REGISTRY_SCHEMA_VALID"] is True
    assert manifest["TERMS_LOADED"] == 3
    assert manifest["CONSUMABLE_TERMS_LOADED"] == 2
    assert manifest["DUPLICATE_TERMS_FOUND"] is False
    assert manifest["RUNTIME_AUTHORITY"] is False
    assert manifest["CANON_AUTHORITY"] is False
    assert manifest["QUALITY_GATE_CAN_CONSUME"] is True
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False

    manifest_path = engain_dir / "manifests" / "preserve_entity_allowlist_registry_gate_manifest.json"
    assert manifest_path.exists()
    terms = load_consumable_preserve_terms(registry_path, manifest_path)
    assert terms == {"Aeon Keeper", "The Ashen Choir"}


def test_registry_gate_fails_clearly_for_invalid_json(tmp_path: Path) -> None:
    registry_path = tmp_path / ".engain" / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text('{"contract": "engain.mrlore_preserve_entity_allowlist.v1" "terms": []}', encoding="utf-8")

    manifest = run_preserve_entity_allowlist_registry_gate(registry_path)

    assert manifest["MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["REGISTRY_FOUND"] is True
    assert manifest["REGISTRY_JSON_VALID"] is False
    assert manifest["REGISTRY_SCHEMA_VALID"] is False
    assert manifest["QUALITY_GATE_CAN_CONSUME"] is False
    assert any("invalid JSON" in error for error in manifest["errors"])


def test_registry_gate_rejects_duplicate_terms_blank_terms_bad_enums_and_authority_claims(tmp_path: Path) -> None:
    registry_path = tmp_path / ".engain" / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        json.dumps(
            _registry(
                [
                    _term("Aeon Keeper", "title", "ACTIVE"),
                    _term(" aeon keeper ", "title", "PROPOSED"),
                    _term("", "artifact", "ACTIVE"),
                    _term("Bad Type", "weapon", "ACTIVE"),
                    _term("Bad Status", "concept", "CANON"),
                ],
                runtime_authority=True,
                canon_authority=True,
            )
        ),
        encoding="utf-8",
    )

    manifest = run_preserve_entity_allowlist_registry_gate(registry_path)

    assert manifest["MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["REGISTRY_JSON_VALID"] is True
    assert manifest["REGISTRY_SCHEMA_VALID"] is False
    assert manifest["DUPLICATE_TERMS_FOUND"] is True
    assert manifest["RUNTIME_AUTHORITY"] is True
    assert manifest["CANON_AUTHORITY"] is True
    assert manifest["QUALITY_GATE_CAN_CONSUME"] is False
    joined_errors = "\n".join(manifest["errors"])
    assert "duplicate term" in joined_errors
    assert "blank term" in joined_errors
    assert "invalid term_type" in joined_errors
    assert "invalid status" in joined_errors
    assert "runtime_authority must be false" in joined_errors
    assert "canon_authority must be false" in joined_errors
