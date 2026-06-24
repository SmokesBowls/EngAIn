#!/usr/bin/env python3
"""
Chapterroom Runner

Wires Pass A → Pass B → Pass C.

ABC provides scene packets.
Passroom compiles those packets later.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def safe_output_name(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run chapterroom Pass A/B/C.")
    parser.add_argument("chapter_file", help="Raw chapter text file.")
    parser.add_argument(
        "--output-dir",
        default="tier3/mettaext/stageroom/output/chapterroom",
        help="ABC output directory.",
    )
    parser.add_argument(
        "--target-words",
        type=int,
        default=900,
        help="Mechanical fallback target words if Pass B supports it.",
    )
    args = parser.parse_args()

    engain_root = Path(__file__).resolve().parents[3]
    chapter_file = Path(args.chapter_file).resolve()

    output_dir_arg = Path(args.output_dir)
    if output_dir_arg.is_absolute():
        output_dir = output_dir_arg.resolve()
    else:
        output_dir = (engain_root / output_dir_arg).resolve()

    output_dir.mkdir(parents=True, exist_ok=True)

    passA = output_dir / f"out_passA_{chapter_file.stem}.json"

    run([
        sys.executable,
        "-m",
        "tier3.mettaext.chapterroom.passA_chapter_intake",
        str(chapter_file),
        "--output",
        str(passA),
    ], cwd=engain_root)

    if not passA.exists():
        raise FileNotFoundError(f"Pass A output missing: {passA}")

    manifest = json.loads(passA.read_text(encoding="utf-8"))
    chapter_id = manifest["chapter_id"]

    passB = output_dir / f"out_passB_{safe_output_name(chapter_id)}.json"

    passB_cmd = [
        sys.executable,
        "-m",
        "tier3.mettaext.chapterroom.passB_scene_boundary_provider",
        str(passA),
        "--output",
        str(output_dir),
    ]

    # Pass B owns the exact output filename inside output_dir.
    passB_cmd.extend(["--target-words", str(args.target_words)])

    run(passB_cmd, cwd=engain_root)

    if not passB.exists() or passB.is_dir():
        candidates = sorted(
            p for p in output_dir.rglob(f"out_passB_{safe_output_name(chapter_id)}.json")
            if p.is_file()
        )
        if not candidates:
            raise FileNotFoundError(f"Pass B output missing: {passB}")
        passB = candidates[-1]

    run([
        sys.executable,
        "-m",
        "tier3.mettaext.chapterroom.passC_scene_packet_writer",
        str(passB),
        "--output-dir",
        str(output_dir),
    ], cwd=engain_root)

    index_path = output_dir / "scene_packets" / chapter_id / "scene_packets_index.json"

    print("[CHAPTERROOM] ABC_COMPLETE = TRUE")
    print(f"[CHAPTERROOM] CHAPTER_ID = {chapter_id}")
    print(f"[CHAPTERROOM] PASS_A = {passA}")
    print(f"[CHAPTERROOM] PASS_B = {passB}")
    print(f"[CHAPTERROOM] INDEX = {index_path}")

    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        print("[CHAPTERROOM] READY_FOR_PASSROOM:")
        for packet in index.get("packets", []):
            print(f"  python3 -m tier3.mettaext.passroom.pass1_explicit {packet['packet_path']}")
    else:
        print("[CHAPTERROOM] WARNING: scene_packets_index.json not found yet")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
