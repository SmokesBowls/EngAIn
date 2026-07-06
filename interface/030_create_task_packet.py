#!/usr/bin/env python3
"""
Create a new task packet.
"""

from __future__ import annotations

import argparse

from interface_common import (
    PACKETS_DIR,
    append_ledger,
    now_utc,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Task packet ID")
    parser.add_argument("--title", required=True, help="Title of the task")
    parser.add_argument("--command", required=True, help="Command to be executed for this task")
    args = parser.parse_args()

    packet_data = {
        "id": args.id,
        "title": args.title,
        "command": args.command,
        "status": "PENDING",
        "created_at": now_utc(),
    }

    packet_path = PACKETS_DIR / f"{args.id}.json"
    write_json(packet_path, packet_data)

    print("TASK_PACKET_CREATED")
    print(f"PATH={packet_path}")
    print(f"ID={args.id}")
    print(f"TITLE={args.title}")
    print(f"COMMAND={args.command}")

    append_ledger(
        {
            "event": "create_task_packet",
            "packet_id": args.id,
            "title": args.title,
            "command": args.command,
        }
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
