from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate import run_preserve_entity_allowlist_registry_gate
from tier1.mrlore.mrlore_review_rail_health_runner import run_review_rail_health


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _scene_packet(path: Path, scene_id: str, terrain_family: str, text: str) -> None:
    _write_json(
        path,
        {
            "contract": "engain.scene_packet.v1",
            "scene_id": scene_id,
            "chapter_id": "chapter.demo",
            "start_line": 10,
            "end_line": 12,
            "environment": {"terrain_family": terrain_family},
            "text": text,
        },
    )


def _write_preserve_registry(engain_dir: Path) -> None:
    registry_path = engain_dir / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"
    _write_json(
        registry_path,
        {
            "contract": "engain.mrlore_preserve_entity_allowlist.v1",
            "registry_type": "PRESERVE_ENTITY_ALLOWLIST",
            "authority_owner": "NARRATIVE_TEAM",
            "runtime_authority": False,
            "canon_authority": False,
            "terms": [
                {"term": "Geralt", "term_type": "character", "status": "PROPOSED"},
            ],
        },
    )
    run_preserve_entity_allowlist_registry_gate(registry_path)


def _write_revision_breathing_input_stubs(engain_dir: Path) -> None:
    claims_dir = engain_dir / "mrlore" / "claims"
    contradictions_dir = engain_dir / "mrlore" / "contradictions"
    review_dir = engain_dir / "mrlore" / "review"
    by_chapter_dir = review_dir / "by_chapter"
    timeline_dir = engain_dir / "mrlore" / "timeline"
    lexicon_dir = engain_dir / "mrlore" / "lexicon"
    for directory in (claims_dir, contradictions_dir, review_dir, by_chapter_dir, timeline_dir, lexicon_dir):
        directory.mkdir(parents=True, exist_ok=True)

    (claims_dir / "proposed_claims.temporal_enriched.jsonl").write_text("", encoding="utf-8")
    (claims_dir / "proposed_claims.cosmic_enriched.jsonl").write_text("", encoding="utf-8")
    (contradictions_dir / "temporal_collision_classifications.jsonl").write_text("", encoding="utf-8")
    (review_dir / "temporal_aware_quality_review_queue.jsonl").write_text("", encoding="utf-8")
    _write_json(by_chapter_dir / "temporal_aware_review_by_chapter.json", {"chapters": []})
    _write_json(timeline_dir / "coming_calendar.json", {"comings": []})
    _write_json(lexicon_dir / "predicate_collision_policy.json", {"predicate_classes": {}})


def test_review_rail_health_runs_all_pre_canon_stages_and_keeps_safety_flags_false(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    packet_one = engain_dir / "scene_packets" / "chapter.demo" / "scene.demo.scene001.json"
    packet_two = engain_dir / "scene_packets" / "chapter.demo" / "scene.demo.scene002.json"
    _scene_packet(packet_one, "scene.demo.scene001", "coastal", "Geralt waits by the sea.")
    _scene_packet(packet_two, "scene.demo.scene002", "forest", "Geralt waits beneath the trees.")

    intake_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    _write_json(
        intake_path,
        {
            "contract": "engain.mrlore_scene_intake_manifest.v1",
            "engain_dir": str(engain_dir),
            "total_scenes_loaded": 2,
            "chapters": [
                {
                    "chapter_id": "chapter.demo",
                    "status": "MRLORE_READY",
                    "scenes": [
                        {"scene_id": "scene.demo.scene001", "packet_json": str(packet_one), "mr_lore_ready": True},
                        {"scene_id": "scene.demo.scene002", "packet_json": str(packet_two), "mr_lore_ready": True},
                    ],
                }
            ],
            "skipped": [],
        },
    )
    _write_preserve_registry(engain_dir)
    _write_revision_breathing_input_stubs(engain_dir)

    manifest = run_review_rail_health(intake_path)

    assert manifest["MRLORE_REVIEW_RAIL_HEALTH_RUNNER_COMPLETE"] is True
    assert manifest["STAGES_RUN"] == 16
    assert manifest["STAGES_PASSED"] == 16
    assert manifest["CLAIMS_STATUS"] == "PROPOSED"
    assert manifest["ACCEPTED_LORE_PACKET_EXISTS"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["GODOT_TOUCHED"] is False
    assert manifest["ZONJ_COMPILED"] is False
    assert manifest["CONTRADICTIONS_RESOLVED"] is False
    assert manifest["CLAIMS_PROMOTED"] is False
    assert manifest["CLAIMS_REJECTED"] is False
    assert [stage["status"] for stage in manifest["stages"]] == ["PASS"] * 16
    assert [stage["stage"] for stage in manifest["stages"]][-7:] == [
        "entity_candidate_quality_gate",
        "quality_aware_review_queue_builder",
        "quality_aware_queue_summary",
        "revision_breathing_map",
        "revision_breathing_map_guidance_gate",
        "manual_review_decision_schema",
        "manual_review_decision_example_writer",
    ]
    assert manifest["MRLORE_REVISION_BREATHING_MAP_COMPLETE"] is True
    assert manifest["MRLORE_REVISION_BREATHING_MAP_GUIDANCE_GATE_COMPLETE"] is True
    assert "revision_breathing_map" in manifest["STAGE_NAMES_PASSED"]
    assert "revision_breathing_map_guidance_gate" in manifest["STAGE_NAMES_PASSED"]
    assert manifest["QUALITY_AWARE_REVIEW_QUEUE_EXISTS"] is True
    assert manifest["REVISION_BREATHING_MAP_JSONL_EXISTS"] is True
    assert manifest["REVISION_BREATHING_MAP_MD_EXISTS"] is True
    assert manifest["REVISION_BREATHING_MAP_GUIDANCE_GATE_MANIFEST_EXISTS"] is True
    assert manifest["MANUAL_REVIEW_SCHEMA_EXISTS"] is True
    assert manifest["MANUAL_REVIEW_EXAMPLES_EXIST"] is True
    assert manifest["REAL_DECISIONS_CREATED"] is False

    health_path = engain_dir / "manifests" / "mrlore_review_rail_health_manifest.json"
    assert health_path.exists()
    persisted = json.loads(health_path.read_text(encoding="utf-8"))
    assert persisted["MRLORE_REVIEW_RAIL_HEALTH_RUNNER_COMPLETE"] is True


def test_review_rail_health_fails_if_accepted_lore_packet_exists(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    packet_one = engain_dir / "scene_packets" / "chapter.demo" / "scene.demo.scene001.json"
    _scene_packet(packet_one, "scene.demo.scene001", "coastal", "Geralt waits by the sea.")
    intake_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    _write_json(
        intake_path,
        {
            "contract": "engain.mrlore_scene_intake_manifest.v1",
            "engain_dir": str(engain_dir),
            "total_scenes_loaded": 1,
            "chapters": [
                {
                    "chapter_id": "chapter.demo",
                    "status": "MRLORE_READY",
                    "scenes": [
                        {"scene_id": "scene.demo.scene001", "packet_json": str(packet_one), "mr_lore_ready": True}
                    ],
                }
            ],
            "skipped": [],
        },
    )
    _write_preserve_registry(engain_dir)
    _write_revision_breathing_input_stubs(engain_dir)
    accepted_packet = engain_dir / "mrlore" / "accepted" / "accepted_lore_packet.json"
    _write_json(accepted_packet, {"status": "ACCEPTED"})

    manifest = run_review_rail_health(intake_path)

    assert manifest["MRLORE_REVIEW_RAIL_HEALTH_RUNNER_COMPLETE"] is False
    assert manifest["STAGES_RUN"] == 16
    assert manifest["STAGES_PASSED"] == 16
    assert manifest["ACCEPTED_LORE_PACKET_EXISTS"] is True
    assert str(accepted_packet) in manifest["accepted_lore_packet_paths"]
    assert manifest["CANON_WRITTEN"] is False
