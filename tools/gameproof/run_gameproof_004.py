#!/usr/bin/env python3
"""
EngAIn Game Proof #004

Purpose:
    Prove EngAIn can take the real Chapterroom scene packet from #003
    and pass it through real Passroom Pass 1 explicit extraction.

Pipeline:
    #003 scene packet text
    -> tier3.mettaext.passroom.passroom_bridge.run_pass1_explicit()
    -> explicit extraction artifact
    -> runtime-like game_state_draft wrapper

This script does NOT:
    - call Trixel
    - call Blender
    - call Mechanimation
    - start Godot
    - mutate runtime
    - write accepted game state
    - create final art
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tier3.mettaext.passroom.passroom_bridge import run_pass1_explicit


REPO_ROOT = Path(__file__).resolve().parents[2]

INPUT_SCENE_PACKET = (
    REPO_ROOT
    / "scratch"
    / "gameproof_003"
    / "output"
    / "chapterroom_real"
    / "scene_packets"
    / "chapter.scene_text"
    / "scene.scene_text.scene001.txt"
)

PROOF_ROOT = REPO_ROOT / "scratch" / "gameproof_004"
OUTPUT_DIR = PROOF_ROOT / "output"
PASSROOM_OUT = OUTPUT_DIR / "passroom_real"

PROOF_ID = "gameproof_004"
SCENE_ID = "scene.gameproof_004.passroom_pass1_explicit"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def inventory_output_files(base: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []

    if not base.exists():
        return files

    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue

        files.append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "size_bytes": path.stat().st_size,
            }
        )

    return files


def build_runtime_payload(passroom_result: dict[str, Any], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "game_state_draft",
        "proof_id": PROOF_ID,
        "scene_id": SCENE_ID,
        "status": "DRAFT_NOT_ACCEPTED",
        "created_at": utc_now(),
        "runtime_mutation_allowed": False,
        "source_scene_packet": str(INPUT_SCENE_PACKET.relative_to(REPO_ROOT)),
        "real_module_called": "tier3.mettaext.passroom.passroom_bridge.run_pass1_explicit",
        "real_call_mode": "direct_python_bridge",
        "passroom_result": passroom_result,
        "passroom_output_inventory": inventory,
        "presentation": {
            "art_assets_required_now": False,
            "placeholder_render_allowed": True,
            "trixel_payload": None,
            "blender_payload": None,
            "mechanimation_payload": None,
        },
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("EngAIn Game Proof #004 — Passroom Bridge")
    print("=" * 72)
    print(f"Input : {INPUT_SCENE_PACKET}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    if not INPUT_SCENE_PACKET.exists():
        print("RESULT: FAILED")
        print(f"  - missing #003 scene packet: {INPUT_SCENE_PACKET}")
        print()
        print("Run Game Proof #003 first.")
        return 2

    print("[1/4] Calling real passroom_bridge.run_pass1_explicit")
    passroom_result = run_pass1_explicit(
        scene_file=INPUT_SCENE_PACKET,
        output_dir=PASSROOM_OUT,
    )

    passroom_result_path = OUTPUT_DIR / "passroom_bridge_result.json"
    write_json(passroom_result_path, passroom_result)

    print(f"      wrote: {passroom_result_path}")
    print(f"      row_count: {passroom_result.get('row_count')}")
    print(f"      types    : {passroom_result.get('types')}")

    print()
    print("[2/4] Inventorying real Passroom output")
    inventory = inventory_output_files(PASSROOM_OUT)

    inventory_path = OUTPUT_DIR / "passroom_output_inventory.json"
    write_json(inventory_path, {"files": inventory})

    print(f"      files: {len(inventory)}")
    for item in inventory[:20]:
        print(f"      - {item['path']} ({item['size_bytes']} bytes)")

    print()
    print("[3/4] Building runtime-like game_state_draft wrapper")
    runtime_payload = build_runtime_payload(passroom_result, inventory)

    runtime_path = OUTPUT_DIR / "runtime_payload.json"
    write_json(runtime_path, runtime_payload)

    print(f"      wrote: {runtime_path}")

    print()
    print("[4/4] Validating proof")

    violations: list[str] = []

    if not isinstance(passroom_result, dict):
        violations.append("passroom_result must be a dict")

    if not passroom_result.get("output_exists"):
        violations.append("Passroom output file was not created")

    if int(passroom_result.get("row_count", 0)) <= 0:
        violations.append("Passroom output row_count must be greater than zero")

    if not inventory:
        violations.append("Passroom output inventory is empty")

    presentation = runtime_payload["presentation"]

    if presentation["trixel_payload"] is not None:
        violations.append("trixel_payload must be null")

    if presentation["blender_payload"] is not None:
        violations.append("blender_payload must be null")

    if presentation["mechanimation_payload"] is not None:
        violations.append("mechanimation_payload must be null")

    if runtime_payload["runtime_mutation_allowed"] is not False:
        violations.append("runtime_mutation_allowed must be false")

    report = {
        "proof_id": PROOF_ID,
        "passed": not violations,
        "checks_run": 8,
        "violations": violations,
        "notes": [
            "This proof consumes the scene packet produced by Game Proof #003.",
            "This proof calls the real Passroom Python bridge.",
            "No fake extractor was used.",
            "No subprocess was used.",
            "No argparse/stdout parsing was used.",
            "No Trixel call was made.",
            "No Blender call was made.",
            "No Mechanimation call was made.",
            "No Godot runtime mutation was made.",
            "Payload is a draft only.",
        ],
        "files_written": [
            str(passroom_result_path.relative_to(REPO_ROOT)),
            str(inventory_path.relative_to(REPO_ROOT)),
            str(runtime_path.relative_to(REPO_ROOT)),
        ],
    }

    report_path = OUTPUT_DIR / "gameproof_report.json"
    write_json(report_path, report)

    print(f"      wrote: {report_path}")

    if violations:
        print()
        print("RESULT: FAILED")
        for violation in violations:
            print(f"  - {violation}")
        return 2

    print()
    print("RESULT: PASSED")
    print()
    print("EngAIn called the real Passroom Python bridge and wrapped its output as a game_state_draft.")
    print("No art lane was required.")
    print("No external sibling tool was required.")
    print("No runtime mutation occurred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
