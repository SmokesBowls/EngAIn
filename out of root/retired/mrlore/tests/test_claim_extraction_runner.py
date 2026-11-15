from __future__ import annotations

import json
from pathlib import Path

from tier1.mrlore.mrlore_claim_extraction_runner import run_claim_extraction


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_claim_extraction_reads_intake_manifest_and_writes_proposed_claims(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    packet_path = engain_dir / "scene_packets" / "chapter.demo" / "scene.demo.scene001.json"
    _write_json(
        packet_path,
        {
            "contract": "engain.scene_packet.v1",
            "scene_id": "scene.demo.scene001",
            "chapter_id": "chapter.demo",
            "start_line": 10,
            "end_line": 12,
            "environment": {
                "terrain_family": "coastal",
                "region": "east",
            },
            "text": "Geralt waits by the sea.\nThe wind turns cold.",
        },
    )
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
                        {
                            "scene_id": "scene.demo.scene001",
                            "packet_json": str(packet_path),
                            "mr_lore_ready": True,
                        }
                    ],
                }
            ],
            "skipped": [],
        },
    )

    manifest = run_claim_extraction(intake_path)

    claims_path = engain_dir / "mrlore" / "claims" / "proposed_claims.jsonl"
    extraction_manifest_path = engain_dir / "manifests" / "mrlore_claim_extraction_manifest.json"
    assert claims_path.exists()
    assert extraction_manifest_path.exists()

    claims = [json.loads(line) for line in claims_path.read_text(encoding="utf-8").splitlines()]
    assert manifest["CLAIMS_EXTRACTED"] is True
    assert manifest["CLAIMS_STATUS"] == "PROPOSED"
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
    assert manifest["scenes_processed"] == 1
    assert manifest["claims_written"] == len(claims)

    for claim in claims:
        assert claim["SOURCE_SCENE"] == "scene.demo.scene001"
        assert claim["source_scene"] == "scene.demo.scene001"
        assert claim["status"] == "PROPOSED"
        assert claim["claim_domain"] in {"entity", "environment"}
        assert claim["claim_type"]
        assert claim["subject"]
        assert claim["predicate"]
        assert claim["object"]

    assert any(
        claim["claim_domain"] == "entity"
        and claim["claim_type"] == "entity_presence"
        and claim["subject"] == "Geralt"
        and claim["predicate"] == "present_in"
        and claim["object"] == "scene.demo.scene001"
        for claim in claims
    )
    assert any(
        claim["claim_domain"] == "environment"
        and claim["claim_type"] == "environment_state"
        and claim["subject"] == "scene.demo.scene001"
        and claim["predicate"] == "terrain_family"
        and claim["object"] == "coastal"
        for claim in claims
    )


def test_claim_extraction_refuses_manifest_without_scene_packets(tmp_path: Path) -> None:
    engain_dir = tmp_path / ".engain"
    raw_chapter_path = tmp_path / "raw" / "chapter.txt"
    raw_chapter_path.parent.mkdir(parents=True, exist_ok=True)
    raw_chapter_path.write_text("Geralt is here.", encoding="utf-8")
    intake_path = engain_dir / "manifests" / "mrlore_scene_intake_manifest.json"
    _write_json(
        intake_path,
        {
            "contract": "engain.mrlore_scene_intake_manifest.v1",
            "engain_dir": str(engain_dir),
            "chapters": [
                {
                    "chapter_id": "chapter.raw_only",
                    "status": "MRLORE_READY",
                    "source_file": str(raw_chapter_path),
                    "scenes": [],
                }
            ],
        },
    )

    manifest = run_claim_extraction(intake_path)

    assert manifest["scenes_processed"] == 0
    assert manifest["claims_written"] == 0
    assert manifest["raw_chapters_read"] is False
    assert manifest["CANON_WRITTEN"] is False
    assert manifest["RUNTIME_TOUCHED"] is False
