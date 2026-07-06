#!/usr/bin/env python3
"""
Show protected files that worker tests must not modify.
"""

from __future__ import annotations

from interface_common import PROTECTED_FILES_PATH, load_json

def main() -> int:
    data = load_json(PROTECTED_FILES_PATH, {"protected_files": []})

    print("PROTECTED_FILES")
    print("=" * 60)

    for path in data.get("protected_files", []):
        print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
