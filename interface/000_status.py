#!/usr/bin/env module
#!/usr/bin/env python3
"""
Show EngAInOS operator interface status.
"""

from __future__ import annotations

from interface_common import (
    LEDGER_PATH,
    PACKETS_DIR,
    RESULTS_DIR,
    PROTECTED_FILES_PATH,
    ensure_interface_dirs,
    load_json,
    run_command,
)


def main() -> int:
    ensure_interface_dirs()

    print("ENGAINOS_OPERATOR_INTERFACE_STATUS")
    print("=" * 60)

    git_status = run_command(["git", "status", "--short"])
    print("GIT_STATUS:")
    if git_status.stdout.strip():
        print(git_status.stdout)
    else:
        print("clean")

    print()
    print("PROTECTED_FILES:")
    protected = load_json(PROTECTED_FILES_PATH, {"protected_files": []})
    for path in protected.get("protected_files", []):
        print(f"- {path}")

    print()
    print(f"PACKETS_DIR: {PACKETS_DIR}")
    print(f"RESULTS_DIR: {RESULTS_DIR}")
    print(f"LEDGER_PATH: {LEDGER_PATH}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
