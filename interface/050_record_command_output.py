#!/usr/bin/env python3
"""
Record the output of a executed task packet.
"""

from __future__ import annotations

import argparse
import sys

from interface_common import (
    PACKETS_DIR,
    RESULTS_DIR,
    append_ledger,
    load_json,
    now_utc,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="ID of the task packet executed")
    parser.add_argument("--exit-code", type=int, required=True, help="Exit code of the execution")
    parser.add_argument("--stdout", required=True, help="Captured stdout")
    parser.add_argument("--stderr", required=True, help="Captured stderr")
    args = parser.parse_args()

    packet_path = PACKETS_DIR / f"{args.target}.json"
    if not packet_path.exists():
        print(f"ERROR: Task packet not found at {packet_path}")
        return 1

    packet_data = load_json(packet_path, {})
    packet_data["status"] = "COMPLETED"
    packet_data["completed_at"] = now_utc()
    write_json(packet_path, packet_data)

    result_data = {
        "packet_id": args.target,
        "exit_code": args.exit_code,
        "stdout": args.stdout,
        "stderr": args.stderr,
        "completed_at": now_utc(),
    }

    result_path = RESULTS_DIR / f"{args.target}_result.json"
    write_json(result_path, result_data)

    print("COMMAND_OUTPUT_RECORDED")
    print(f"TARGET={args.target}")
    print(f"EXIT_CODE={args.exit_code}")
    print(f"RESULT_PATH={result_path}")

    append_ledger(
        {
            "event": "record_command_output",
            "target": args.target,
            "exit_code": args.exit_code,
            "passed": args.exit_code == 0,
        }
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
