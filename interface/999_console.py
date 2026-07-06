#!/usr/bin/env python3
"""
Simple EngAInOS operator console.

This does not replace the individual command files.
It only gives the human a menu.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


INTERFACE_DIR = Path(__file__).resolve().parent


COMMANDS = {
    "1": ("Status", ["python3", str(INTERFACE_DIR / "000_status.py")]),
    "2": ("Protected files", ["python3", str(INTERFACE_DIR / "010_show_protected_files.py")]),
    "3": ("Ledger", ["python3", str(INTERFACE_DIR / "020_show_ledger.py")]),
    "4": ("Show next command", ["python3", str(INTERFACE_DIR / "040_show_next_command.py")]),
    "5": ("Recover file from git (dry-run)", ["python3", str(INTERFACE_DIR / "090_recover_file_from_git.py"), "--target", "tier2/godotsim/gates/gate_trigger_zone_multi_trigger_light_route_proof.py", "--dry-run"]),
}


def main() -> int:
    while True:
        print()
        print("ENGAINOS OPERATOR CONSOLE")
        print("=" * 60)
        for key, (label, _) in COMMANDS.items():
            print(f"[{key}] {label}")
        print("[q] Quit")

        choice = input("> ").strip().lower()

        if choice == "q":
            return 0

        if choice not in COMMANDS:
            print("Unknown choice.")
            continue

        _, command = COMMANDS[choice]
        subprocess.run(command)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
