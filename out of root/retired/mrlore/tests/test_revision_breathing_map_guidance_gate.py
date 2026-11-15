from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_revision_breathing_map_guidance_gate import run_guidance_gate


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _valid_record() -> dict:
    return {
        "chapter_id": "chapter.book006.036_highland_giants",
        "book_id": "book006",
        "chapter_number": 36,
        "pressure_score": 123.45,
        "pressure_rank_global": 12,
        "pressure_percentile_global": 91.11,
        "pressure_rank_within_book": 3,
        "pressure_percentile_within_book": 75.0,
        "pressure_tier_global": "VERY_HIGH_BREATHING_PRESSURE",
        "pressure_tier_within_book": "BOOK_HIGH_PRESSURE",
        "detected_event_pressure": ["SEQUENTIAL_STATE_CHANGE_LOAD"],
        "missing_breath_type": ["TRANSITION_BREATH"],
        "expected_internal_feeling": "Reader should have enough internal space to absorb the event load.",
        "revision_guidance": "Add human breathing review without rewriting from this diagnostic.",
        "do_not_change": ["Do not rewrite prose from this diagnostic.", "Do not reorder canon events automatically."],
        "author_action_required": True,
        "DIAGNOSTIC_REVISION_GUIDANCE_ONLY": True,
        "PRESSURE_SCORE_DIAGNOSTIC_NOT_QUALITY_JUDGMENT": True,
        "HIGH_PRESSURE_NOT_BAD_CHAPTER": True,
        "HIGH_PRESSURE_STATE_CHANGE_HUMAN_REVIEW": True,
        "AUTHOR_REVISES_MANUALLY": True,
        "CANON_WRITTEN": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "ACCEPTED_LORE_PACKETS_CREATED": False,
        "ZONJ_COMPILED": False,
        "GODOT_TOUCHED": False,
        "RUNTIME_TOUCHED": False,
    }


def test_guidance_gate_accepts_revision_guidance_records_without_mutation(tmp_path: Path) -> None:
    breathing_map = tmp_path / ".engain" / "mrlore" / "revision" / "breathing_map.jsonl"
    manifest_path = tmp_path / ".engain" / "manifests" / "mrlore_revision_breathing_map_guidance_gate_manifest.json"
    _write_jsonl(breathing_map, [_valid_record()])
    before = breathing_map.read_text(encoding="utf-8")

    manifest = run_guidance_gate(breathing_map, manifest_path)

    assert manifest["MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE"] is True
    assert manifest["BREATHING_MAP_FOUND"] is True
    assert manifest["RECORDS_READ"] == 1
    assert manifest["REQUIRED_GUIDANCE_FIELDS_PRESENT"] is True
    assert manifest["PRESSURE_RANKING_FIELDS_PRESENT"] is True
    assert manifest["FORBIDDEN_REWRITE_FIELDS_ABSENT"] is True
    assert manifest["AUTHOR_ACTION_REQUIRED_TRUE"] is True
    assert manifest["SAFETY_LOCKS_PRESENT"] is True
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["ACCEPTED_LORE_PACKET_CREATED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest_path.exists()
    assert breathing_map.read_text(encoding="utf-8") == before


def test_guidance_gate_rejects_score_only_records(tmp_path: Path) -> None:
    breathing_map = tmp_path / ".engain" / "mrlore" / "revision" / "breathing_map.jsonl"
    manifest_path = tmp_path / ".engain" / "manifests" / "mrlore_revision_breathing_map_guidance_gate_manifest.json"
    score_only = {
        "chapter_id": "chapter.book006.036_highland_giants",
        "book_id": "book006",
        "chapter_number": 36,
        "pressure_score": 123.45,
        "pressure_rank_global": 12,
        "pressure_rank_within_book": 3,
        "DIAGNOSTIC_REVISION_GUIDANCE_ONLY": True,
        "PRESSURE_SCORE_DIAGNOSTIC_NOT_QUALITY_JUDGMENT": True,
        "HIGH_PRESSURE_NOT_BAD_CHAPTER": True,
        "HIGH_PRESSURE_STATE_CHANGE_HUMAN_REVIEW": True,
        "AUTHOR_REVISES_MANUALLY": True,
        "CANON_WRITTEN": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "ACCEPTED_LORE_PACKETS_CREATED": False,
        "ZONJ_COMPILED": False,
        "GODOT_TOUCHED": False,
        "RUNTIME_TOUCHED": False,
    }
    _write_jsonl(breathing_map, [score_only])

    manifest = run_guidance_gate(breathing_map, manifest_path)

    assert manifest["MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE"] is False
    assert manifest["REQUIRED_GUIDANCE_FIELDS_PRESENT"] is False
    assert manifest["missing_required_fields_count"] > 0


def test_guidance_gate_rejects_rewrite_artifacts_and_author_action_false(tmp_path: Path) -> None:
    breathing_map = tmp_path / ".engain" / "mrlore" / "revision" / "breathing_map.jsonl"
    manifest_path = tmp_path / ".engain" / "manifests" / "mrlore_revision_breathing_map_guidance_gate_manifest.json"
    bad = _valid_record()
    bad["author_action_required"] = False
    bad["replacement_paragraph"] = "This is forbidden generated prose."
    _write_jsonl(breathing_map, [bad])

    manifest = run_guidance_gate(breathing_map, manifest_path)

    assert manifest["MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE"] is False
    assert manifest["AUTHOR_ACTION_REQUIRED_TRUE"] is False
    assert manifest["FORBIDDEN_REWRITE_FIELDS_ABSENT"] is False
    assert manifest["forbidden_rewrite_fields_count"] == 1
