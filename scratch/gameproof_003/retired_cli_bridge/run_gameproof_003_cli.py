#!/usr/bin/env python3
"""
EngAIn Game Proof #003 CLI Bridge

Purpose:
    Prove EngAIn can call the real tier3/mettaext/chapterroom runner
    through its actual CLI contract.

This does NOT:
    - call Trixel
    - call Blender
    - call Mechanimation
    - start Godot
    - mutate runtime
    - write accepted game state

This DOES:
    - read real text from disk
    - call real chapterroom_runner as a module
    - capture its output files
    - wrap the result as a game_state_draft proof
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROOF_ROOT = REPO_ROOT / "scratch" / "gameproof_003"
INPUT_PATH = PROOF_ROOT / "input" / "scene_text.txt"
OUTPUT_DIR = PROOF_ROOT / "output"
REAL_CHAPTERROOM_OUT = OUTPUT_DIR / "chapterroom_real"

PROOF_ID = "gameproof_003_cli_bridge"
SCENE_ID = "scene.gameproof_003.real_chapterroom_cli"


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


def run_chapterroom_cli() -> subprocess.CompletedProcess[str]:
    REAL_CHAPTERROOM_OUT.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "tier3.mettaext.chapterroom.chapterroom_runner",
        str(INPUT_PATH),
        "--output-dir",
        str(REAL_CHAPTERROOM_OUT),
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def build_runtime_payload(result: subprocess.CompletedProcess[str], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "game_state_draft",
        "proof_id": PROOF_ID,
        "scene_id": SCENE_ID,
        "status": "DRAFT_NOT_ACCEPTED",
        "created_at": utc_now(),
        "runtime_mutation_allowed": False,
        "source_path": str(INPUT_PATH.relative_to(REPO_ROOT)),
        "real_module_called": "tier3.mettaext.chapterroom.chapterroom_runner",
        "real_call_mode": "python -m CLI",
        "real_returncode": result.returncode,
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
    print("EngAIn Game Proof #003 — CLI Bridge")
    print("=" * 72)
    print(f"Input : {INPUT_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    if not INPUT_PATH.exists():
        print(f"RESULT: FAILED — missing input {INPUT_PATH}")
        return 2

    print("[1/4] Calling real chapterroom_runner CLI")
    result = run_chapterroom_cli()

    print(f"      returncode: {result.returncode}")
    if result.stdout.strip():
        print("      stdout:")
        print(result.stdout)
    if result.stderr.strip():
        print("      stderr:")
        print(result.stderr)

    cli_result_path = OUTPUT_DIR / "chapterroom_cli_result.json"
    write_json(
        cli_result_path,
        {
            "cmd": [
                sys.executable,
                "-m",
                "tier3.mettaext.chapterroom.chapterroom_runner",
                str(INPUT_PATH),
                "--output-dir",
                str(REAL_CHAPTERROOM_OUT),
            ],
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
    )

    print()
    print("[2/4] Inventorying real chapterroom output")
    inventory = inventory_output_files(REAL_CHAPTERROOM_OUT)
    inventory_path = OUTPUT_DIR / "chapterroom_output_inventory.json"
    write_json(inventory_path, {"files": inventory})

    print(f"      files: {len(inventory)}")
    for item in inventory[:20]:
        print(f"      - {item['path']} ({item['size_bytes']} bytes)")

    print()
    print("[3/4] Building runtime-like game_state_draft wrapper")
    runtime_payload = build_runtime_payload(result, inventory)
    runtime_path = OUTPUT_DIR / "runtime_payload_cli_bridge.json"
    write_json(runtime_path, runtime_payload)
    print(f"      wrote: {runtime_path}")

    print()
    print("[4/4] Validating proof")

    violations: list[str] = []

    if result.returncode != 0:
        violations.append("real chapterroom_runner CLI returned non-zero")

    if not inventory:
        violations.append("real chapterroom_runner produced no output files")

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
        "checks_run": 6,
        "violations": violations,
        "notes": [
            "This proof calls the real tier3/mettaext/chapterroom runner through its CLI contract.",
            "No fake extractor was used.",
            "No Trixel call was made.",
            "No Blender call was made.",
            "No Mechanimation call was made.",
            "No Godot runtime mutation was made.",
            "Payload is a draft only.",
        ],
        "files_written": [
            str(cli_result_path.relative_to(REPO_ROOT)),
            str(inventory_path.relative_to(REPO_ROOT)),
            str(runtime_path.relative_to(REPO_ROOT)),
        ],
    }

    report_path = OUTPUT_DIR / "gameproof_cli_bridge_report.json"
    write_json(report_path, report)
    print(f"      wrote: {report_path}")

    if violations:
        print()
        print("RESULT: FAILED HONESTLY")
        for violation in violations:
            print(f"  - {violation}")
        return 2

    print()
    print("RESULT: PASSED")
    print()
    print("EngAIn called the real chapterroom runner and wrapped its output as a game_state_draft.")
    print("No art lane was required.")
    print("No external sibling tool was required.")
    print("No runtime mutation occurred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
