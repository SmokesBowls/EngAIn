from __future__ import annotations

import copy
import json
from pathlib import Path

from tier1.mrlore.mrlore_coming_calendar_registry_gate import (
    install_default_coming_calendar_registry,
    run_coming_calendar_registry_gate,
)


def _registry() -> dict:
    return {
        "contract": "engain.mrlore_coming_calendar_registry.v1",
        "authority_owner": "AUTHOR_DECLARED",
        "runtime_authority": False,
        "canon_authority": False,
        "policy_effect": "TEMPORAL_CONTEXT_ONLY",
        "doctrine_locks": [
            "Chapter order is source retrieval order, not absolute story-time order.",
            "Cosmic Year is absolute world-history time.",
            "Coming ID groups regional manifestations.",
            "Regional names are aliases, not separate events.",
            "The Coming and The Shadow can be same event when they share the same shared_event_id.",
            "Branch-local elapsed years must map back to Cosmic Year.",
            "North and South manifestations with the same shared_event_id are concurrent unless explicitly marked otherwise.",
            "This registry does not write canon.",
            "This registry does not promote claims.",
            "This registry does not resolve contradictions.",
            "This registry does not touch runtime, Godot, or ZONJ.",
        ],
        "comings": [
            {
                "coming_id": "FIRST_COMING",
                "coming_number": 1,
                "cosmic_year_start": 3500,
                "shared_event_id": "EV-3500",
                "aliases": ["The Coming", "The Shadow", "The Darkness"],
                "status": "LOCKED",
                "notes": "North and South are concurrent First Coming manifestations.",
                "regional_manifestations": [
                    {
                        "region": "NORTH",
                        "regional_name": "The Coming",
                        "manuscript_chapter_ranges": ["B2.C6"],
                        "titles": ["The First Coming"],
                    },
                    {
                        "region": "SOUTH",
                        "regional_name": "The Shadow / The Darkness",
                        "manuscript_chapter_ranges": ["B20.C105", "B20.C106"],
                        "titles": ["Garden Grove", "Sky Fallen"],
                    },
                ],
            },
            {
                "coming_id": "SECOND_COMING",
                "coming_number": 2,
                "cosmic_year_start": 10500,
                "shared_event_id": "EV-10500",
                "aliases": ["The Second Coming", "The Second Shadow"],
                "status": "LOCKED",
                "notes": "Chapter B3.C13 is excluded if chapter 13 void applies.",
                "regional_manifestations": [
                    {
                        "region": "NORTH",
                        "regional_name": "The Second Coming",
                        "manuscript_chapter_ranges": ["B3.C10-B3.C15"],
                        "excluded_chapters": ["B3.C13"],
                        "titles": [
                            "Shadow Returns Second Coming",
                            "Escalation and Desperation",
                            "Nephilim Summoning",
                            "Convergence",
                            "Betrayal",
                        ],
                    },
                    {
                        "region": "SOUTH",
                        "regional_name": "The Second Shadow",
                        "manuscript_chapter_ranges": ["B21.C107-B21.C110"],
                        "titles": [
                            "The Waking",
                            "Evolution of the Keeper",
                            "The Thread and Cage",
                            "The Bleeding Convergence",
                        ],
                    },
                ],
            },
        ],
    }


def _write_registry(path: Path, registry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_default_registry_installs_when_missing_and_validates(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"

    assert not registry_path.exists()
    install_default_coming_calendar_registry(registry_path)
    manifest = run_coming_calendar_registry_gate(registry_path)

    assert registry_path.exists()
    assert manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is True
    assert manifest["REGISTRY_FOUND"] is True
    assert manifest["REGISTRY_JSON_VALID"] is True
    assert manifest["REGISTRY_SCHEMA_VALID"] is True
    assert manifest["COMINGS_LOADED"] == 4
    assert manifest["MANIFESTATIONS_LOADED"] == 8
    assert manifest["SHARED_EVENTS_LOADED"] == 4
    assert manifest["CHAPTER_RANGES_LOADED"] == 9
    assert manifest["TEMPORAL_ENRICHMENT_CAN_CONSUME"] is True
    assert manifest["errors_count"] == 0


def test_valid_registry_passes_and_preserves_chapter_ranges_and_safety_flags(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    registry = _registry()
    _write_registry(registry_path, registry)
    before_registry = registry_path.read_text(encoding="utf-8")

    manifest = run_coming_calendar_registry_gate(registry_path)

    assert manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is True
    assert manifest["COMINGS_LOADED"] == 2
    assert manifest["MANIFESTATIONS_LOADED"] == 4
    assert manifest["SHARED_EVENTS_LOADED"] == 2
    assert manifest["CHAPTER_RANGES_LOADED"] == 5
    assert manifest["DUPLICATE_COMING_IDS_FOUND"] is False
    assert manifest["CONFLICTING_SHARED_EVENT_IDS_FOUND"] is False
    assert manifest["POLICY_EFFECT"] == "TEMPORAL_CONTEXT_ONLY"
    assert manifest["RUNTIME_AUTHORITY"] is False
    assert manifest["CANON_AUTHORITY"] is False
    assert manifest["TEMPORAL_ENRICHMENT_CAN_CONSUME"] is True
    for flag in (
        "CLAIMS_ALTERED",
        "CANDIDATES_ALTERED",
        "QUEUES_ALTERED",
        "CLAIMS_PROMOTED",
        "CLAIMS_REJECTED",
        "CONTRADICTIONS_RESOLVED",
        "CANON_WRITTEN",
        "RUNTIME_TOUCHED",
        "GODOT_TOUCHED",
        "ZONJ_COMPILED",
    ):
        assert manifest[flag] is False
    assert registry_path.read_text(encoding="utf-8") == before_registry
    written = json.loads((engain_dir / "manifests" / "coming_calendar_registry_gate_manifest.json").read_text(encoding="utf-8"))
    assert written["chapter_ranges_by_coming"]["SECOND_COMING"]["NORTH"] == ["B3.C10-B3.C15"]


def test_duplicate_coming_id_fails(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    registry = _registry()
    duplicate = copy.deepcopy(registry["comings"][0])
    duplicate["shared_event_id"] = "EV-DUPLICATE"
    registry["comings"].append(duplicate)
    _write_registry(registry_path, registry)

    manifest = run_coming_calendar_registry_gate(registry_path)

    assert manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["DUPLICATE_COMING_IDS_FOUND"] is True
    assert manifest["TEMPORAL_ENRICHMENT_CAN_CONSUME"] is False
    assert manifest["errors_count"] > 0


def test_runtime_authority_true_fails(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    registry = _registry()
    registry["runtime_authority"] = True
    _write_registry(registry_path, registry)

    manifest = run_coming_calendar_registry_gate(registry_path)

    assert manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["RUNTIME_AUTHORITY"] is True
    assert manifest["TEMPORAL_ENRICHMENT_CAN_CONSUME"] is False
    assert any("runtime_authority" in error for error in manifest["errors"])


def test_canon_authority_true_fails(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    registry = _registry()
    registry["canon_authority"] = True
    _write_registry(registry_path, registry)

    manifest = run_coming_calendar_registry_gate(registry_path)

    assert manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["CANON_AUTHORITY"] is True
    assert manifest["TEMPORAL_ENRICHMENT_CAN_CONSUME"] is False
    assert any("canon_authority" in error for error in manifest["errors"])


def test_conflicting_shared_event_id_cosmic_years_fail_unless_approximate(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    registry = _registry()
    conflict = copy.deepcopy(registry["comings"][1])
    conflict["coming_id"] = "SECOND_COMING_ALT"
    conflict["cosmic_year_start"] = 10501
    registry["comings"].append(conflict)
    _write_registry(registry_path, registry)

    failed = run_coming_calendar_registry_gate(registry_path)

    assert failed["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is False
    assert failed["CONFLICTING_SHARED_EVENT_IDS_FOUND"] is True

    registry["comings"][-1]["cosmic_year_start_approx"] = True
    _write_registry(registry_path, registry)
    passed = run_coming_calendar_registry_gate(registry_path)

    assert passed["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is True
    assert passed["CONFLICTING_SHARED_EVENT_IDS_FOUND"] is False


def test_rejects_missing_manifestation_fields_and_bad_region(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    registry = _registry()
    registry["comings"][0]["regional_manifestations"][0]["region"] = "EAST"
    registry["comings"][0]["regional_manifestations"][0].pop("manuscript_chapter_ranges")
    _write_registry(registry_path, registry)

    manifest = run_coming_calendar_registry_gate(registry_path)

    assert manifest["MRLORE_COMING_CALENDAR_REGISTRY_GATE_COMPLETE"] is False
    assert manifest["REGISTRY_SCHEMA_VALID"] is False
    assert any("region" in error for error in manifest["errors"])
    assert any("manuscript_chapter_ranges" in error for error in manifest["errors"])
