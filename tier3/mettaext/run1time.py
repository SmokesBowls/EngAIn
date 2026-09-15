#!/usr/bin/env python3
"""
run1time.py - HISTORICAL / DEPRECATED runner.
Delegates to canonical pipeline_runner.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tier3.mettaext import pipeline_runner


def main() -> None:
    print(
        "⚠️ [DEPRECATED] run1time.py is a historical runner. "
        "Delegating to canonical pipeline_runner.py."
    )
    if len(sys.argv) > 1:
        in_file = Path(sys.argv[1]).resolve()
    else:
        in_file = Path("03_Fist_contact.txt").resolve()

    if not in_file.exists():
        print(f"ERROR: missing input file: {in_file}")
        sys.exit(1)

    pipeline_runner.run_pipeline(str(in_file))


if __name__ == "__main__":
    main()

