#!/usr/bin/env python3
"""
Recover a file from git repository history.
"""

from __future__ import annotations

import argparse
import sys

from interface_common import (
    append_ledger,
    is_protected,
    repo_path,
    run_command,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Path to the target file to recover")
    parser.add_argument("--commit", default="HEAD", help="Git commit hash/ref to recover from")
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing")
    parser.add_argument("--force", action="store_true", help="Force recovery even if the file is protected")
    args = parser.parse_args()

    target = repo_path(args.target)
    protected = is_protected(args.target)

    print("GIT_RECOVERY")
    print(f"TARGET={args.target}")
    print(f"COMMIT={args.commit}")
    print(f"PROTECTED={protected}")

    if protected and not args.force and not args.dry_run:
        print("ERROR: Target file is protected. Overwriting requires --force.")
        return 1

    git_command = ["git", "show", f"{args.commit}:{args.target}"]

    if args.dry_run:
        print("DRY_RUN: Would execute git show command and write to file:")
        print(f"COMMAND: {' '.join(git_command)} > {target}")
        append_ledger(
            {
                "event": "recover_file_git",
                "target": args.target,
                "commit": args.commit,
                "dry_run": True,
            }
        )
        return 0

    result = run_command(git_command)
    if result.returncode != 0:
        print("ERROR: Git recovery failed.")
        print(result.stderr)
        return result.returncode

    try:
        target.write_text(result.stdout, encoding="utf-8")
        print("RECOVERY_COMPLETED")
        print(f"Successfully recovered {args.target} from commit {args.commit}")
        append_ledger(
            {
                "event": "recover_file_git",
                "target": args.target,
                "commit": args.commit,
                "dry_run": False,
                "passed": True,
            }
        )
        return 0
    except Exception as e:
        print(f"ERROR: Failed to write recovered file: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
