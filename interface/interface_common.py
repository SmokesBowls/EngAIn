#!/usr/bin/env python3
"""
Shared helpers for EngAInOS operator interface commands.

This file is not a command by itself.
Command files import from here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INTERFACE_DIR = REPO_ROOT / "interface"
STATE_PATH = INTERFACE_DIR / "interface_state.json"
LEDGER_PATH = INTERFACE_DIR / "ledger.jsonl"
PROTECTED_FILES_PATH = INTERFACE_DIR / "protected_files.json"
PACKETS_DIR = INTERFACE_DIR / "packets"
RESULTS_DIR = INTERFACE_DIR / "results"
LOGS_DIR = INTERFACE_DIR / "logs"


def ensure_interface_dirs() -> None:
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_ledger(entry: dict[str, Any]) -> None:
    ensure_interface_dirs()
    entry = dict(entry)
    entry.setdefault("timestamp_utc", now_utc())
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def is_protected(path_text: str) -> bool:
    protected = load_json(PROTECTED_FILES_PATH, {"protected_files": []})
    normalized = str(Path(path_text))
    return normalized in protected.get("protected_files", [])


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd or REPO_ROOT),
        text=True,
        capture_output=True,
    )


def print_process_result(result: subprocess.CompletedProcess[str]) -> None:
    print(f"EXIT_CODE={result.returncode}")
    print("----- STDOUT -----")
    print(result.stdout)
    print("----- STDERR -----")
    print(result.stderr)
