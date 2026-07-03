from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_cosmic_year_context_enrichment import run_cosmic_year_context_enrichment


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _claim(claim_id: str, chapter_id: str, scene_id: str | None = None) -> dict:
    scene = scene_id or f"scene.{chapter_id.removeprefix('chapter.')}.scene001"
    return {
        "claim_id": claim_id,
        "claim_domain": "entity",
        "claim_type": "entity_presence",
        "subject": "Marduk",
        "predicate": "present_in",
        "object": scene,
        "status": "PROPOSED",
        "SOURCE_SCENE": scene,
        "source_scene": scene,
        "source_scene_id": scene,
        "chapter_id": chapter_id,
        "scene_index": 1,
        "temporal_basis": "CHAPTERROOM_SCENE_ORDER",
        "temporal_confidence": 1.0,
    }


def _registry() -> dict:
    return {
        "contract": "engain.mrlore_coming_calendar_registry.v1",
        "authority_owner": "AUTHOR_DECLARED",
        "runtime_authority": False,
        "canon_authority": False,
        "policy_effect": "TEMPORAL_CONTEXT_ONLY",
        "doctrine_locks": ["Cosmic Year is absolute world-history time."],
        "comings": [
            {
                "coming_id": "FIRST_COMING",
                "coming_number": 1,
                "cosmic_year_start": 3500,
                "shared_event_id": "EV-3500",
                "aliases": ["The Coming", "The Shadow"],
                "status": "LOCKED",
                "notes": "fixture",
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
                "notes": "fixture",
                "regional_manifestations": [
                    {
                        "region": "NORTH",
                        "regional_name": "The Second Coming",
                        "manuscript_chapter_ranges": ["B3.C10-B3.C15"],
                        "excluded_chapters": ["B3.C13"],
                    },
                    {
                        "region": "SOUTH",
                        "regional_name": "The Second Shadow",
                        "manuscript_chapter_ranges": ["B21.C107-B21.C110"],
                    },
                ],
            },
        ],
    }


def test_cosmic_year_context_enrichment_attaches_coming_context_by_chapter_range(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    output_path = engain_dir / "mrlore" / "claims" / "proposed_claims.cosmic_enriched.jsonl"
    _write_jsonl(
        claims_path,
        [
            _claim("claim.first.north", "chapter.book002.006_the_first_coming"),
            _claim("claim.first.south", "chapter.book020.105_garden_grove"),
            _claim("claim.second.south", "chapter.book021.110_the_bleeding_convergence"),
            _claim("claim.outside", "chapter.book009.040_unregistered"),
        ],
    )
    _write_json(registry_path, _registry())

    manifest = run_cosmic_year_context_enrichment(claims_path, registry_path)

    assert manifest["MRLORE_COSMIC_YEAR_CONTEXT_ENRICHMENT_COMPLETE"] is True
    assert manifest["CLAIMS_READ"] == 4
    assert manifest["CLAIMS_WRITTEN"] == 4
    assert manifest["CLAIMS_COSMIC_ENRICHED"] == 3
    assert manifest["CLAIMS_COSMIC_UNRESOLVED"] == 1
    assert manifest["COMING_REGISTRY_READ"] is True
    assert manifest["COSMIC_CONTEXT_BASIS"] == "COMING_CALENDAR_REGISTRY"

    enriched = _read_jsonl(output_path)
    first_north = enriched[0]
    assert first_north["coming_id"] == "FIRST_COMING"
    assert first_north["coming_number"] == 1
    assert first_north["cosmic_year_start"] == 3500
    assert first_north["shared_event_id"] == "EV-3500"
    assert first_north["region"] == "NORTH"
    assert first_north["regional_name"] == "The Coming"
    assert first_north["cosmic_context_basis"] == "COMING_CALENDAR_REGISTRY"

    first_south = enriched[1]
    assert first_south["coming_id"] == "FIRST_COMING"
    assert first_south["region"] == "SOUTH"
    assert first_south["regional_name"] == "The Shadow / The Darkness"

    second_south = enriched[2]
    assert second_south["coming_id"] == "SECOND_COMING"
    assert second_south["coming_number"] == 2
    assert second_south["cosmic_year_start"] == 10500
    assert second_south["shared_event_id"] == "EV-10500"
    assert second_south["region"] == "SOUTH"
    assert second_south["regional_name"] == "The Second Shadow"

    outside = enriched[3]
    assert outside["claim_id"] == "claim.outside"
    assert "coming_id" not in outside
    assert outside["cosmic_context_basis"] == "UNRESOLVED_COMING_CALENDAR_REGISTRY"


def test_cosmic_year_context_enrichment_respects_excluded_chapters(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    _write_jsonl(claims_path, [_claim("claim.second.excluded", "chapter.book003.013_void")])
    _write_json(registry_path, _registry())

    manifest = run_cosmic_year_context_enrichment(claims_path, registry_path)

    enriched = _read_jsonl(engain_dir / "mrlore" / "claims" / "proposed_claims.cosmic_enriched.jsonl")
    assert manifest["CLAIMS_COSMIC_ENRICHED"] == 0
    assert manifest["CLAIMS_COSMIC_UNRESOLVED"] == 1
    assert "coming_id" not in enriched[0]
    assert enriched[0]["cosmic_context_basis"] == "UNRESOLVED_COMING_CALENDAR_REGISTRY"


def test_cosmic_year_context_enrichment_preserves_source_claims_and_registry(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    _write_jsonl(claims_path, [_claim("claim.first.north", "chapter.book002.006_the_first_coming")])
    _write_json(registry_path, _registry())
    before_claims = claims_path.read_text(encoding="utf-8")
    before_registry = registry_path.read_text(encoding="utf-8")

    manifest = run_cosmic_year_context_enrichment(claims_path, registry_path)

    assert claims_path.read_text(encoding="utf-8") == before_claims
    assert registry_path.read_text(encoding="utf-8") == before_registry
    assert manifest["TEMPORAL_CLAIMS_ALTERED"] is False
    assert manifest["COMING_REGISTRY_ALTERED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False


def test_cosmic_year_context_enrichment_writes_manifest_with_safety_flags(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"
    registry_path = engain_dir / "mrlore" / "timeline" / "coming_calendar.json"
    _write_jsonl(claims_path, [_claim("claim.first.south", "chapter.book020.106_sky_fallen")])
    _write_json(registry_path, _registry())

    manifest = run_cosmic_year_context_enrichment(claims_path, registry_path)

    manifest_path = engain_dir / "manifests" / "mrlore_cosmic_year_context_manifest.json"
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["MRLORE_COSMIC_YEAR_CONTEXT_ENRICHMENT_COMPLETE"] is True
    assert written["ENGINE_AGNOSTIC"] is True
    assert written["RUNTIME_TOUCHED"] is False
    assert written["GODOT_TOUCHED"] is False
    assert written["ZONJ_COMPILED"] is False
    assert written["CANON_WRITTEN"] is False
    assert written["errors_count"] == manifest["errors_count"]
