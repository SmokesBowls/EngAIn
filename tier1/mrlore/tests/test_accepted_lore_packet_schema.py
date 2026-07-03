from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_accepted_lore_packet_schema import (
    REQUIRED_FIELDS,
    build_accepted_lore_packet_schema,
    example_accepted_lore_packets,
    run_accepted_lore_packet_schema,
    validate_accepted_lore_packet_record,
)


def test_schema_file_defines_accepted_lore_packet_without_creating_real_packets(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"

    manifest = run_accepted_lore_packet_schema(engain_dir=engain_dir)

    assert manifest["MRLORE_ACCEPTED_LORE_PACKET_SCHEMA_COMPLETE"] is True
    assert manifest["SCHEMA_WRITTEN"] is True
    assert manifest["EXAMPLE_PACKETS_VALIDATED"] is True
    assert manifest["REAL_ACCEPTED_LORE_PACKETS_CREATED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False

    schema_path = engain_dir / "mrlore" / "accepted" / "accepted_lore_packet.schema.json"
    manifest_path = engain_dir / "manifests" / "accepted_lore_packet_schema_manifest.json"
    assert schema_path.exists()
    assert manifest_path.exists()

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["properties"]["packet_type"]["const"] == "ACCEPTED_LORE_PACKET"
    assert schema["properties"]["lore_status"]["const"] == "ACCEPTED"
    assert schema["properties"]["authority_scope"]["const"] == "LORE_ONLY"
    assert schema["properties"]["canon_write_allowed"]["const"] is False
    assert schema["properties"]["runtime_mutation_allowed"]["const"] is False
    assert schema["properties"]["godot_mutation_allowed"]["const"] is False
    assert schema["properties"]["zonj_compile_allowed"]["const"] is False
    assert schema["properties"]["promotion_gate_passed"]["const"] is False
    assert schema["required"] == list(REQUIRED_FIELDS)
    assert "accepted lore is not canon file writing" in "\n".join(schema["locks"])


def test_example_packet_shape_answers_source_review_and_authority_questions() -> None:
    schema = build_accepted_lore_packet_schema()
    examples = example_accepted_lore_packets()

    assert len(examples) == 1
    packet = examples[0]
    assert validate_accepted_lore_packet_record(packet, schema) == []
    assert packet["packet_id"] == "accepted_lore_packet.example.0001"
    assert packet["packet_type"] == "ACCEPTED_LORE_PACKET"
    assert packet["lore_status"] == "ACCEPTED"
    assert packet["claim_id"] == "claim.scene.book001.001_the_ethereal_vigil.scene001.entity.0001"
    assert packet["claim_domain"] == "entity"
    assert packet["claim_type"] == "entity_presence"
    assert packet["subject"] == "Aeon Keeper"
    assert packet["predicate"] == "present_in"
    assert packet["object"] == "scene.book001.001_the_ethereal_vigil.scene001"
    assert packet["SOURCE_SCENES"] == ["scene.book001.001_the_ethereal_vigil.scene001"]
    assert packet["source_claim_refs"] == ["claim.scene.book001.001_the_ethereal_vigil.scene001.entity.0001"]
    assert packet["review_decision_refs"] == []
    assert packet["accepted_by"] == "MANUAL_OR_GATE_AUTHORITY_REQUIRED"
    assert packet["accepted_at"] is None
    assert packet["authority_scope"] == "LORE_ONLY"
    assert packet["canon_write_allowed"] is False
    assert packet["runtime_mutation_allowed"] is False
    assert packet["godot_mutation_allowed"] is False
    assert packet["zonj_compile_allowed"] is False
    assert packet["promotion_gate_passed"] is False


def test_validator_rejects_packets_that_skip_promotion_gate_or_expand_authority() -> None:
    valid_packet = example_accepted_lore_packets()[0]
    schema = build_accepted_lore_packet_schema()

    promoted = dict(valid_packet)
    promoted["promotion_gate_passed"] = True
    assert "promotion_gate_passed must be false for schema-only phase" in validate_accepted_lore_packet_record(promoted, schema)

    canon = dict(valid_packet)
    canon["canon_write_allowed"] = True
    assert "canon_write_allowed must be false" in validate_accepted_lore_packet_record(canon, schema)

    runtime = dict(valid_packet)
    runtime["runtime_mutation_allowed"] = True
    assert "runtime_mutation_allowed must be false" in validate_accepted_lore_packet_record(runtime, schema)

    godot = dict(valid_packet)
    godot["godot_mutation_allowed"] = True
    assert "godot_mutation_allowed must be false" in validate_accepted_lore_packet_record(godot, schema)

    zonj = dict(valid_packet)
    zonj["zonj_compile_allowed"] = True
    assert "zonj_compile_allowed must be false" in validate_accepted_lore_packet_record(zonj, schema)

    scope = dict(valid_packet)
    scope["authority_scope"] = "CANON"
    assert "authority_scope must be LORE_ONLY" in validate_accepted_lore_packet_record(scope, schema)

    missing_scene = dict(valid_packet)
    missing_scene["SOURCE_SCENES"] = []
    assert "SOURCE_SCENES must contain at least one source scene" in validate_accepted_lore_packet_record(missing_scene, schema)
