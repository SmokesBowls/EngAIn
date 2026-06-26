#!/usr/bin/env python3
"""
chapterroom_bridge.py — EngAIn internal callable for the chapterroom A→B→C pipeline.

This is the Python API. Not a CLI, not a subprocess wrapper.

Import and call run_chapter() directly:

    from tier3.mettaext.chapterroom.chapterroom_bridge import run_chapter
    result = run_chapter(chapter_file, output_dir)

The chapterroom_runner.py main() and the individual pass main() functions are
operator conveniences for running from a terminal. They are not the contract.
This file is.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tier3.mettaext.chapterroom.passA_chapter_intake import intake
from tier3.mettaext.chapterroom.passB_scene_boundary_provider import choose_boundaries
from tier3.mettaext.chapterroom.passC_scene_packet_writer import write_packets


def run_chapter(
    chapter_file: Path,
    output_dir: Path,
    target_words: int = 900,
) -> dict[str, Any]:
    """
    Drive Pass A → Pass B → Pass C and return a structured result.

    All three passes are called as Python — no subprocess, no argparse,
    no stdout parsing.

    Args:
        chapter_file:  Raw chapter .txt or .md file.
        output_dir:    Directory for intermediate and final outputs.
        target_words:  Mechanical fallback scene size for Pass B.

    Returns:
        {
            "chapter_id":      str,
            "passA_manifest":  dict,          # full Pass A output
            "passA_path":      Path,          # written JSON
            "passB_proposal":  dict,          # full Pass B output
            "passB_path":      Path,          # written JSON
            "passC_index":     dict,          # full Pass C index
            "scene_count":     int,
            "boundary_method": str,
        }
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Pass A: chapter text → chapter identity manifest
    passA_path = output_dir / f"out_passA_{chapter_file.stem}.json"
    manifest = intake(chapter_file, passA_path)

    # Pass B: manifest → scene boundary proposal (pure dict, no file I/O in the function)
    proposal = choose_boundaries(manifest, target_words)

    # Write the Pass B JSON for auditability (mirrors what passB main() does)
    safe_chapter = proposal["chapter_id"].replace("/", "_")
    passB_path = output_dir / f"out_passB_{safe_chapter}.json"
    passB_path.write_text(
        json.dumps(proposal, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Pass C: proposal → scene packet files + index
    index = write_packets(proposal, output_dir)

    return {
        "chapter_id": manifest["chapter_id"],
        "passA_manifest": manifest,
        "passA_path": passA_path,
        "passB_proposal": proposal,
        "passB_path": passB_path,
        "passC_index": index,
        "scene_count": index["scene_count"],
        "boundary_method": proposal["boundary_method"],
    }
