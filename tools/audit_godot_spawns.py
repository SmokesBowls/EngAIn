#!/usr/bin/env python3
# tools/audit_godot_spawns.py
"""
Audit the repo for places that can spawn Godot (or repeatedly restart it).

What it looks for:
- subprocess.Popen / subprocess.run / os.system / exec* calls that include "godot"
- shell scripts that call "godot"
- common "watch/restart" loops that can create process storms

It does NOT modify anything.

Run from repo root:
  python3 tools/audit_godot_spawns.py

Optional:
  python3 tools/audit_godot_spawns.py --root /path/to/repo --max-hits 200
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


DEFAULT_EXTS = {
    ".py", ".sh", ".bash", ".zsh", ".gd", ".tscn", ".md", ".txt", ".json", ".yml", ".yaml"
}

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    "archive", "reports", "cleanup_reports", "cleanup_reports_hh", "tmp", "ingested", "loaded"
}

# Patterns: ordered from most-specific to broader hints.
PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("python.Popen_godot", re.compile(r"\bsubprocess\.Popen\s*\(.*?godot", re.IGNORECASE)),
    ("python.run_godot", re.compile(r"\bsubprocess\.(?:run|call|check_call|check_output)\s*\(.*?godot", re.IGNORECASE)),
    ("python.os_system_godot", re.compile(r"\bos\.system\s*\(.*?godot", re.IGNORECASE)),
    ("python.exec_godot", re.compile(r"\bos\.(?:execv|execve|execl|execlp|execvp)\s*\(.*?godot", re.IGNORECASE)),
    ("shell_godot", re.compile(r"(^|\s)(?:\.\/)?godot(\s|$)|(^|\s)godot4?(\s|$)", re.IGNORECASE)),
    # "restart loops" that tend to cause storms
    ("loop_while_true", re.compile(r"^\s*(while\s+True\s*:|for\s+\w+\s+in\s+iter\()", re.MULTILINE)),
    ("watcher_keywords", re.compile(r"\b(watch|autoreload|auto[-_ ]?reload|restart|reconnect|respawn)\b", re.IGNORECASE)),
]

CONTEXT = 3  # lines above/below


def _iter_files(root: Path, exts: set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # prune dirs
        dirnames[:] = [n for n in dirnames if n not in SKIP_DIRS and not n.startswith(".zw")]
        for fn in filenames:
            p = d / fn
            if p.suffix.lower() in exts:
                # skip huge files
                try:
                    if p.stat().st_size > 2_000_000:
                        continue
                except OSError:
                    continue
                yield p


def _read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _line_index(text: str, pos: int) -> int:
    return text.count("\n", 0, pos)


def _extract_context(lines: List[str], idx: int, context: int) -> str:
    lo = max(0, idx - context)
    hi = min(len(lines), idx + context + 1)
    out = []
    for i in range(lo, hi):
        prefix = ">>" if i == idx else "  "
        out.append(f"{prefix} {i+1:5d}: {lines[i].rstrip()}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repo root (default: .)")
    ap.add_argument("--max-hits", type=int, default=200, help="Stop after this many hits")
    ap.add_argument("--ext", action="append", default=None, help="Extra extension to scan (repeatable), e.g. --ext .ini")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[AUDIT] ERROR: root not found: {root}")
        return 2

    exts = set(DEFAULT_EXTS)
    if args.ext:
        for e in args.ext:
            if not e.startswith("."):
                e = "." + e
            exts.add(e.lower())

    hits = 0
    printed_files = 0

    print(f"[AUDIT] Scanning for Godot spawn/restart triggers under: {root}")
    print(f"[AUDIT] Extensions: {', '.join(sorted(exts))}")
    print(f"[AUDIT] Skipping dirs: {', '.join(sorted(SKIP_DIRS))}")
    print("")

    for p in _iter_files(root, exts):
        text = _read_text(p)
        if text is None:
            continue

        # Quick prefilter: only deep-scan if file mentions "godot" or looks like a watcher.
        lower = text.lower()
        if "godot" not in lower and "restart" not in lower and "reconnect" not in lower and "autoreload" not in lower:
            continue

        lines = text.splitlines()
        file_hits = []

        for label, rx in PATTERNS:
            for m in rx.finditer(text):
                idx = _line_index(text, m.start())
                # Guard: if this is a loop keyword but file doesn't mention godot at all, skip that hit.
                if label in ("loop_while_true", "watcher_keywords") and "godot" not in lower:
                    continue
                file_hits.append((idx, label))

        if not file_hits:
            continue

        file_hits.sort(key=lambda x: (x[0], x[1]))
        if printed_files == 0:
            print("[AUDIT] HITS (file:line, with context):\n")

        printed_files += 1
        print(f"=== {p.relative_to(root)} ===")
        # de-dup by line number (keep most specific label first due to PATTERNS order)
        seen = set()
        for idx, label in file_hits:
            if idx in seen:
                continue
            seen.add(idx)
            print(f"[{label}]")
            print(_extract_context(lines, idx, CONTEXT))
            print("")
            hits += 1
            if hits >= args.max_hits:
                print(f"[AUDIT] Reached max hits ({args.max_hits}). Stopping.")
                return 0

    if hits == 0:
        print("[AUDIT] No obvious Godot spawn/restart triggers found in scanned files.")
        print("[AUDIT] If you still saw a Godot swarm, use process ancestry to find the spawner:")
        print("        pgrep -a godot")
        print("        for pid in $(pgrep godot); do ps -o pid,ppid,etime,cmd -p $pid; done")
        print("        # then inspect the parent PID with: ps -o pid,ppid,etime,cmd -p <PPID>")
        return 0

    print(f"[AUDIT] Done. Total hits: {hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
