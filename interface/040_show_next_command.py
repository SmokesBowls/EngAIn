#!/usr/bin/env python3
"""
Show the next pending task packet command.
"""

from __future__ import annotations

import json
from interface_common import PACKETS_DIR, load_json


def main() -> int:
    ensure_packets = list(PACKETS_DIR.glob("*.json"))
    
    pending_packets = []
    for path in ensure_packets:
        try:
            data = load_json(path, {})
            if data.get("status") == "PENDING":
                pending_packets.append(data)
        except Exception:
            continue

    # Sort by created_at or ID
    pending_packets.sort(key=lambda p: p.get("created_at", ""))

    print("NEXT_COMMAND_STATUS")
    print("=" * 60)

    if not pending_packets:
        print("NO_PENDING_COMMANDS")
        print("All task packets have been processed or no packets exist.")
        print("=" * 60)
        return 0

    next_packet = pending_packets[0]
    print("NEXT_COMMAND_FOUND")
    print(f"ID: {next_packet.get('id')}")
    print(f"TITLE: {next_packet.get('title')}")
    print(f"COMMAND: {next_packet.get('command')}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
