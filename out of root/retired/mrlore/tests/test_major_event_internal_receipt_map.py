from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_major_event_internal_receipt_map import (
    SAFETY_LOCKS,
    run_major_event_internal_receipt_map,
)


FORBIDDEN_FIELDS = {
    "rewritten_scene",
    "replacement_paragraph",
    "replacement_scene",
    "generated_prose",
    "suggested_rewrite",
    "new_chapter_text",
    "canon_patch",
    "accepted_lore_packet",
}


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def test_major_event_internal_receipt_map_writes_seeded_event_level_revision_lane(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    breathing_map_path = engain_dir / "mrlore" / "revision" / "breathing_map.jsonl"
    _write_jsonl(
        breathing_map_path,
        [
            {
                "chapter_id": "book006.030_ummade_army",
                "pressure_score": 1731.591,
                "pressure_rank_global": 5,
                "pressure_tier_global": "VERY_HIGH_BREATHING_PRESSURE",
                "primary_pressure_source": "CLAIM_DENSITY_AND_TEMPORAL_COLLISION_LOAD",
                "claim_density": {"claims_per_scene": 69.889, "scene_count": 9},
            }
        ],
    )

    manifest = run_major_event_internal_receipt_map(engain_dir=engain_dir)

    output_jsonl = engain_dir / "mrlore" / "revision" / "internal_receipt_map.jsonl"
    output_md = engain_dir / "mrlore" / "revision" / "internal_receipt_map.md"
    focus_md = engain_dir / "mrlore" / "revision" / "focus" / "ch30_ch38_internal_receipt_map.md"
    output_manifest = engain_dir / "manifests" / "mrlore_major_event_internal_receipt_map_manifest.json"

    assert output_jsonl.exists()
    assert output_md.exists()
    assert focus_md.exists()
    assert output_manifest.exists()

    assert manifest["MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP_COMPLETE"] is True
    assert manifest["MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP_V1"] is True
    assert manifest["MRLORE_MAJOR_EVENT_INTERNAL_RECEIPT_MAP_V1_1_AUTHOR_PRIORITY_CLEANUP"] is True
    assert manifest["SEEDED_CH30_CH38_EVENT_MAP"] is True
    assert manifest["UNIVERSAL_EVENT_EXTRACTION_USED"] is False
    assert manifest["FOCUS_CH30_CH38_WRITTEN"] is True
    assert manifest["BREATHING_MAP_READ"] is True
    assert manifest["BREATHING_MAP_USED_AS_PRESSURE_SIGNAL_ONLY"] is True
    assert manifest["SAFETY_LOCKS_PRESENT"] is True
    assert manifest["errors_count"] == 0

    for flag in [
        "CANON_WRITTEN",
        "CLAIMS_PROMOTED",
        "CLAIMS_REJECTED",
        "CONTRADICTIONS_RESOLVED",
        "ACCEPTED_LORE_PACKET_CREATED",
        "GENERATED_PROSE_CREATED",
        "REPLACEMENT_PROSE_CREATED",
        "ZONJ_COMPILED",
        "GODOT_TOUCHED",
        "RUNTIME_TOUCHED",
    ]:
        assert manifest[flag] is False

    records = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert manifest["EVENT_RECORDS_WRITTEN"] == len(records)
    assert len(records) >= 12

    for record in records:
        for field in [
            "event_id",
            "event_type",
            "source_anchor_hint",
            "existing_payoff_evidence",
            "internal_receipt_status",
            "receipt_kind",
            "missing_or_expected_receipt",
            "author_action",
            "do_not_change",
            "revision_priority",
        ]:
            assert field in record
        assert record["safety_locks"] == SAFETY_LOCKS
        assert record["source_basis"] == "SEEDED_CH30_CH38_EVENT_MAP_V1"
        serialized = json.dumps(record, ensure_ascii=False)
        for forbidden in FORBIDDEN_FIELDS:
            assert forbidden not in serialized
        for flag in [
            "CANON_WRITTEN",
            "CLAIMS_PROMOTED",
            "CLAIMS_REJECTED",
            "CONTRADICTIONS_RESOLVED",
            "ACCEPTED_LORE_PACKET_CREATED",
            "GENERATED_PROSE_CREATED",
            "REPLACEMENT_PROSE_CREATED",
            "ZONJ_COMPILED",
            "GODOT_TOUCHED",
            "RUNTIME_TOUCHED",
        ]:
            assert record[flag] is False

    by_event_id = {record["event_id"]: record for record in records}
    camp = by_event_id["book006.030.event002.camp_denies_249"]
    assert camp["event_type"] == "REALITY_DENIAL_AFTER_UNMAKING"
    assert camp["internal_receipt_status"] == "PRESENT_BUT_NEEDS_PERSONAL_CUT"
    assert camp["revision_priority"] == "PATCH_REQUIRED"
    assert camp["author_action_required"] is True
    assert camp["breathing_map_pressure_signal"]["pressure_score"] == 1731.591

    ship = by_event_id["book006.030.event003.heaven_ship_theft_decision"]
    assert ship["internal_receipt_status"] == "PRESENT_BUT_WEAPONIZED"
    assert ship["revision_priority"] == "PATCH_REQUIRED"
    assert ship["author_action_required"] is True

    army = by_event_id["book006.030.event001.army_unmade_by_xalzirith"]
    assert army["internal_receipt_status"] == "PRESENT_BUT_COULD_USE_PERSONAL_CUT"
    assert army["revision_priority"] == "OPTIONAL_REVIEW"
    assert army["author_action_required"] is True

    triage = by_event_id["book006.031.event001.zephyr_crash_triage"]
    assert triage["internal_receipt_status"] == "PRESENT"
    assert triage["revision_priority"] == "NO_PATCH_EXPECTED"
    assert triage["author_action_required"] is False

    kael_roric = by_event_id["book006.031.event002.kael_roric_survive_sleeping"]
    assert kael_roric["revision_priority"] == "NO_PATCH_EXPECTED"
    assert kael_roric["author_action_required"] is False

    body_protection = by_event_id["book006.031.event004.zephyr_protects_bodies_from_salvage"]
    assert body_protection["revision_priority"] == "NO_PATCH_EXPECTED"
    assert body_protection["author_action_required"] is False

    five_body = by_event_id["book006.031.event003.zephyr_finds_five_bodies"]
    assert five_body["revision_priority"] == "PATCH_REQUIRED"

    echo_tower = by_event_id["book006.031.event005.echo_tower_resurrection_route"]
    assert echo_tower["revision_priority"] == "PATCH_REQUIRED"

    restored_250 = by_event_id["book006.034.event001.250_restored_survivors"]
    assert restored_250["revision_priority"] == "PATCH_REQUIRED"

    markdown = output_md.read_text(encoding="utf-8")
    focus_markdown = focus_md.read_text(encoding="utf-8")
    assert "# MrLore Major Event Internal Receipt Map" in markdown
    assert "This is not chapter-wide emotional advice." in markdown
    assert "## CH030 — book006.030_ummade_army" in focus_markdown
    assert "Event 2 — Camp has no knowledge the 249 existed" in focus_markdown
    assert "## Patch Required" in focus_markdown
    assert "## Optional Review" in focus_markdown
    assert "## No Patch Expected" in focus_markdown
    assert "- Revision priority: PATCH_REQUIRED" in focus_markdown
    assert "- Author action required: false" in focus_markdown
    assert "Source anchor" in focus_markdown
    assert "Patch target" in focus_markdown
    assert "Do not change:" in focus_markdown


def test_major_event_internal_receipt_map_can_filter_one_book(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"

    manifest = run_major_event_internal_receipt_map(engain_dir=engain_dir, book_id="book007")

    output_jsonl = engain_dir / "mrlore" / "revision" / "internal_receipt_map.jsonl"
    records = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert manifest["FILTER_BOOK_ID"] == "book007"
    assert manifest["FILTER_CHAPTER_ID"] is None
    assert manifest["FILTER_CHAPTER_NUMBER"] is None
    assert manifest["EVENT_RECORDS_WRITTEN"] == 2
    assert {record["book_id"] for record in records} == {"book007"}
    assert manifest["CHAPTERS_COVERED"] == [
        "book007.037_the_circle_of_progress",
        "book007.038_luminaire_keeper",
    ]


def test_major_event_internal_receipt_map_can_filter_single_chapter(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"

    manifest = run_major_event_internal_receipt_map(
        engain_dir=engain_dir,
        chapter_id="book006.031_the_crash_site",
    )

    output_jsonl = engain_dir / "mrlore" / "revision" / "internal_receipt_map.jsonl"
    focus_md = engain_dir / "mrlore" / "revision" / "focus" / "ch30_ch38_internal_receipt_map.md"
    records = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    focus_markdown = focus_md.read_text(encoding="utf-8")

    assert manifest["FILTER_BOOK_ID"] is None
    assert manifest["FILTER_CHAPTER_ID"] == "book006.031_the_crash_site"
    assert manifest["FILTER_CHAPTER_NUMBER"] is None
    assert manifest["EVENT_RECORDS_WRITTEN"] == 5
    assert {record["chapter_id"] for record in records} == {"book006.031_the_crash_site"}
    assert "## CH031 — book006.031_the_crash_site" in focus_markdown
    assert "## CH030 — book006.030_ummade_army" not in focus_markdown


def test_major_event_internal_receipt_map_can_filter_single_chapter_number(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"

    manifest = run_major_event_internal_receipt_map(engain_dir=engain_dir, chapter_number=34)

    output_jsonl = engain_dir / "mrlore" / "revision" / "internal_receipt_map.jsonl"
    records = [json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert manifest["FILTER_BOOK_ID"] is None
    assert manifest["FILTER_CHAPTER_ID"] is None
    assert manifest["FILTER_CHAPTER_NUMBER"] == 34
    assert manifest["EVENT_RECORDS_WRITTEN"] == 1
    assert records[0]["event_id"] == "book006.034.event001.250_restored_survivors"
    assert records[0]["revision_priority"] == "PATCH_REQUIRED"
