#!/usr/bin/env python3
"""
EngAIn Game Proof #003

Purpose:
    Prove EngAIn can call the real Chapterroom bridge directly.

Pipeline:
    real text file
    -> tier3.mettaext.chapterroom.chapterroom_bridge.run_chapter()
    -> Pass A / Pass B / Pass C outputs
    -> runtime-like game_state_draft wrapper

This script does NOT:
    - call Trixel
    - call Blender
    - call Mechanimation
    - start Godot
    - mutate runtime
    - write accepted game state
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tier3.mettaext.chapterroom.chapterroom_bridge import run_chapter


REPO_ROOT = Path(__file__).resolve().parents[2]
PROOF_ROOT = REPO_ROOT / "scratch" / "gameproof_003"
INPUT_PATH = PROOF_ROOT / "input" / "scene_text.txt"
OUTPUT_DIR = PROOF_ROOT / "output"
CHAPTERROOM_OUT = OUTPUT_DIR / "chapterroom_real"

PROOF_ID = "gameproof_003"
SCENE_ID = "scene.gameproof_003.chapterroom_bridge"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def read_json_if_possible(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def inventory_output_files(base: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []

    if not base.exists():
        return files

    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue

        rel = path.relative_to(REPO_ROOT)
        item: dict[str, Any] = {
            "path": str(rel),
            "size_bytes": path.stat().st_size,
        }

        if path.suffix.lower() == ".json":
            parsed = read_json_if_possible(path)
            item["json_parse_ok"] = parsed is not None
            if isinstance(parsed, dict):
                item["json_keys"] = sorted(str(k) for k in parsed.keys())[:30]
            elif isinstance(parsed, list):
                item["json_list_length"] = len(parsed)
        else:
            item["json_parse_ok"] = False

        files.append(item)

    return files


def build_runtime_payload(chapterroom_result: dict[str, Any], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "game_state_draft",
        "proof_id": PROOF_ID,
        "scene_id": SCENE_ID,
        "status": "DRAFT_NOT_ACCEPTED",
        "created_at": utc_now(),
        "runtime_mutation_allowed": False,
        "source_path": str(INPUT_PATH.relative_to(REPO_ROOT)),
        "real_module_called": "tier3.mettaext.chapterroom.chapterroom_bridge.run_chapter",
        "real_call_mode": "direct_python_bridge",
        "chapterroom_result": chapterroom_result,
        "chapterroom_output_inventory": inventory,
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
    print("EngAIn Game Proof #003 — Chapterroom Bridge")
    print("=" * 72)
    print(f"Input : {INPUT_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    if not INPUT_PATH.exists():
        print(f"RESULT: FAILED — missing input {INPUT_PATH}")
        return 2

    print("[1/4] Calling real chapterroom_bridge.run_chapter")
    chapterroom_result = run_chapter(
        chapter_file=INPUT_PATH,
        output_dir=CHAPTERROOM_OUT,
        target_words=900,
    )

    bridge_result_path = OUTPUT_DIR / "chapterroom_bridge_result.json"
    write_json(bridge_result_path, chapterroom_result)

    print(f"      wrote: {bridge_result_path}")
    print(f"      result keys: {sorted(chapterroom_result.keys())}")

    print()
    print("[2/4] Inventorying real Chapterroom output")
    inventory = inventory_output_files(CHAPTERROOM_OUT)

    inventory_path = OUTPUT_DIR / "chapterroom_output_inventory.json"
    write_json(inventory_path, {"files": inventory})

    print(f"      files: {len(inventory)}")
    for item in inventory[:20]:
        print(f"      - {item['path']} ({item['size_bytes']} bytes)")

    print()
    print("[3/4] Building runtime-like game_state_draft wrapper")
    runtime_payload = build_runtime_payload(chapterroom_result, inventory)

    runtime_path = OUTPUT_DIR / "runtime_payload.json"
    write_json(runtime_path, runtime_payload)

    print(f"      wrote: {runtime_path}")

    print()
    print("[4/4] Validating proof")

    violations: list[str] = []

    if not isinstance(chapterroom_result, dict):
        violations.append("chapterroom_result must be a dict")

    if not inventory:
        violations.append("chapterroom_bridge produced no output files")

    scene_packet_files = [
        item for item in inventory
        if item["path"].endswith(".txt") and "scene_packets" in item["path"]
    ]

    if not scene_packet_files:
        violations.append("chapterroom_bridge produced no scene packet text files")

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
        "checks_run": 7,
        "violations": violations,
        "notes": [
            "This proof calls the real Chapterroom Python bridge.",
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
            str(bridge_result_path.relative_to(REPO_ROOT)),
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
    print("EngAIn called the real Chapterroom Python bridge and wrapped its output as a game_state_draft.")
    print("No art lane was required.")
    print("No external sibling tool was required.")
    print("No runtime mutation occurred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
