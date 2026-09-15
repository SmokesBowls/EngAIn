#!/usr/bin/env python3
"""
narrative_to_game.py - Thin compatibility wrapper around canonical pipeline_runner.
Delegates narrative chapter compilation to pipeline_runner.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tier3.mettaext import pipeline_runner


class UnifiedPipeline:
    """Thin compatibility wrapper for pipeline_runner."""

    def __init__(self, work_dir: Path | None = None):
        self.work_dir = work_dir or Path("./pipeline_work")

    def process_chapter(self, input_file: Path, output_dir: Path | None = None) -> Path:
        """Delegate chapter processing to canonical pipeline_runner."""
        pipeline_runner.run_pipeline(str(input_file))
        return input_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified narrative -> game pipeline (compatibility wrapper)")
    parser.add_argument("inputs", nargs="+", help="Input narrative files")
    parser.add_argument("--output", default="./game_scenes", help="Output directory (compatibility field)")
    parser.add_argument("--work-dir", default="./pipeline_work", help="Working directory (compatibility field)")

    args = parser.parse_args()

    pipeline = UnifiedPipeline(work_dir=Path(args.work_dir))
    for input_path in args.inputs:
        f = Path(input_path)
        if f.exists():
            pipeline.process_chapter(f, Path(args.output))


if __name__ == "__main__":
    main()
