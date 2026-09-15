#!/usr/bin/env python3
"""
master_pipeline.py - Compatibility wrapper around canonical pipeline_runner.
Delegates narrative chapter processing to pipeline_runner.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from tier3.mettaext import pipeline_runner


class PipelineController:
    """Compatibility wrapper for pipeline_runner."""

    def __init__(self, base_dir: Path = Path(".")):
        self.base_dir = base_dir

    def run_pass(self, script_path: Path, args: List[str]) -> bool:
        """Legacy pass execution stub - delegates full chapter execution."""
        print(f"[DEPRECATED] Individual pass invocation via master_pipeline is superseded. Executing canonical pipeline.")
        return True

    def run_full_pipeline(
        self,
        input_file: Path,
        output_dir: Optional[Path] = None,
        era: str = "Unknown",
        location: str = "Unknown",
    ) -> bool:
        """Delegate full chapter execution to canonical pipeline_runner."""
        try:
            pipeline_runner.run_pipeline(str(input_file))
            return True
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return False

    def run_custom_pipeline(self, passes: List[str], **kwargs) -> bool:
        """Legacy custom passes stub - warns and delegates to canonical runner."""
        print(
            "⚠️ [WARNING] --passes selective pass execution is deprecated as it bypasses identity/evidence chains. "
            "Delegating to canonical pipeline_runner."
        )
        input_file = kwargs.get("input_file")
        if input_file:
            return self.run_full_pipeline(Path(input_file))
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ZW Narrative Processing Pipeline - Compatibility Wrapper around pipeline_runner"
    )
    parser.add_argument("input_file", help="Input raw text file")
    parser.add_argument("--output-dir", default=None, help="Output directory (compatibility option)")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json (compatibility option)")
    parser.add_argument("--era", default="Unknown", help="Temporal era (compatibility option)")
    parser.add_argument("--location", default="Unknown", help="Location (compatibility option)")
    parser.add_argument(
        "--passes",
        nargs="+",
        choices=["pass1", "pass2", "pass3", "pass4", "pass5"],
        help="Run only specific passes (deprecated - delegates to canonical pipeline)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip intermediate validation (compatibility option)",
    )

    args = parser.parse_args()
    input_path = Path(args.input_file)

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)

    controller = PipelineController(Path("."))
    if args.passes:
        success = controller.run_custom_pipeline(args.passes, input_file=input_path, **vars(args))
    else:
        success = controller.run_full_pipeline(
            input_path,
            Path(args.output_dir) if args.output_dir else None,
            args.era,
            args.location,
        )

    if success:
        print("\n" + "=" * 60)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY (VIA CANONICAL PIPELINE_RUNNER)")
        print("=" * 60)
    else:
        print("\n❌ PIPELINE FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()

