#!/usr/bin/env python3
"""
Stamp a result into the EngAInOS ledger.
"""

from __future__ import annotations

import argparse

from interface_common import append_ledger


VALID_STAMPS = {"PASS", "FAIL", "PARTIAL", "VOID", "RESTORED", "BLOCKED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stamp", required=True, choices=sorted(VALID_STAMPS))
    parser.add_argument("--target", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    append_ledger(
        {
            "event": "result_stamp",
            "target": args.target,
            "stamp": args.stamp,
            "reason": args.reason,
        }
    )

    print("STAMP_RECORDED")
    print(f"TARGET={args.target}")
    print(f"STAMP={args.stamp}")
    print(f"REASON={args.reason}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
