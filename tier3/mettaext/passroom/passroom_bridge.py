#!/usr/bin/env python3
"""
Passroom Bridge

Stable Python bridge for Mettaext Passroom.

This bridge exists so game proofs and EngAIn runtime-facing code can call
Passroom directly without subprocess, argparse, or stdout parsing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tier3.mettaext.passroom.pass1_explicit import process_file


TYPE_RE = re.compile(
    r'^\{type:(?P<type>[a-z_]+)'
    r'(?:,\s*speaker:(?P<speaker>[A-Za-z_]+))?'
    r'\}\s*(?P<text>.*)$'
)


def _read_pass1_units(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if not path.exists():
        return rows

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        match = TYPE_RE.match(line)
        if not match:
            rows.append(
                {
                    "line": line_no,
                    "type": "UNPARSED_LINE",
                    "speaker": None,
                    "text": line,
                }
            )
            continue

        rows.append(
            {
                "line": line_no,
                "type": match.group("type"),
                "speaker": match.group("speaker"),
                "text": match.group("text") or "",
            }
        )

    return rows


def run_pass1_explicit(scene_file: Path, output_dir: Path) -> dict[str, Any]:
    """
    Run Passroom Pass 1 explicit extraction against one scene packet text file.

    Args:
        scene_file:
            Path to a scene text file produced by Chapterroom Pass C.

        output_dir:
            Directory where passroom bridge artifacts should be written.

    Returns:
        dict containing paths, counts, and parsed output preview.

    Boundary:
        This does not call Trixel, Blender, Mechanimation, or Godot.
        This does not mutate runtime.
    """

    scene_file = Path(scene_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not scene_file.exists():
        raise FileNotFoundError(f"Missing scene_file: {scene_file}")

    out_path = output_dir / f"{scene_file.stem}.pass1_explicit.jsonl"

    process_file(scene_file, out_path)

    rows = _read_pass1_units(out_path)

    result = {
        "bridge": "tier3.mettaext.passroom.passroom_bridge.run_pass1_explicit",
        "pass": "pass1_explicit",
        "scene_file": str(scene_file),
        "output_path": str(out_path),
        "output_exists": out_path.exists(),
        "output_size_bytes": out_path.stat().st_size if out_path.exists() else 0,
        "row_count": len(rows),
        "types": sorted({str(row.get("type", "UNKNOWN")) for row in rows}),
        "preview": rows[:20],
    }

    return result
