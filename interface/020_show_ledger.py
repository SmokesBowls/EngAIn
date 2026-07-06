#!/usr/bin/env python3
"""
Show the EngAInOS operator ledger.
"""

from __future__ import annotations

import json

from interface_common import LEDGER_PATH


def main() -> int:
    print("ENGAINOS_LEDGER")
    print("=" * 60)

    if not LEDGER_PATH.exists():
        print("No ledger entries yet.")
        return 0

    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        print(json.dumps(entry, indent=2, sort_keys=True))
        print("-" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
