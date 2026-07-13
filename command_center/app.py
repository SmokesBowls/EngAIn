#!/usr/bin/env python3
"""
EngAIn Command Center — Eel backend.

This is the ONLY place HTML talks to Python. It does not contain business
logic — it shells out to the existing interface/*.py scripts (Core) and to
stub adapter functions (Godot Adapter, fill in as they're built) and returns
raw text back to the page. The ledger tape in the UI is a mirror of
interface/ledger.jsonl, not a separate source of truth.

Setup:
    pip install eel
    python3 app.py

Assumes this folder sits next to /interface, i.e.:
    <repo_root>/interface/...
    <repo_root>/command_center/app.py
Override with the ENGAIN_ROOT env var if your layout differs.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import eel

HERE = Path(__file__).resolve().parent
REPO_ROOT = Path(os.environ.get("ENGAIN_ROOT", HERE.parent))
INTERFACE_DIR = REPO_ROOT / "interface"
LEDGER_PATH = INTERFACE_DIR / "ledger.jsonl"


def _run(args: list[str]) -> dict:
    """Run a command, return exit code + stdout + stderr as a plain dict."""
    result = subprocess.run(args, cwd=str(REPO_ROOT), text=True, capture_output=True)
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "passed": result.returncode == 0,
    }


def _py(script: str, *args: str) -> dict:
    return _run(["python3", str(INTERFACE_DIR / script), *args])


# ---------------------------------------------------------------------------
# Core commands — exposed to JS, one per button
# ---------------------------------------------------------------------------

@eel.expose
def get_status():
    return _py("000_status.py")


@eel.expose
def list_protected():
    return _py("010_show_protected_files.py")


@eel.expose
def get_ledger():
    if not LEDGER_PATH.exists():
        return {"entries": []}
    entries = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    entries.sort(key=lambda e: e.get("timestamp_utc", ""), reverse=True)
    return {"entries": entries}


@eel.expose
def create_packet(packet_id: str, title: str, command: str):
    return _py("030_create_task_packet.py", "--id", packet_id, "--title", title, "--command", command)


@eel.expose
def get_next_packet():
    return _py("040_show_next_command.py")


@eel.expose
def stamp_result(stamp: str, target: str, reason: str):
    return _py("080_stamp_result.py", "--stamp", stamp, "--target", target, "--reason", reason)


@eel.expose
def recover_file(target: str, dry_run: bool = True):
    args = ["--target", target]
    if dry_run:
        args.append("--dry-run")
    return _py("090_recover_file_from_git.py", *args)


# ---------------------------------------------------------------------------
# Godot adapter commands — STUBS. Replace the body once the adapter exists;
# the button wiring in app.js does not need to change when you do.
# ---------------------------------------------------------------------------

@eel.expose
def check_gd_syntax(target: str):
    """
    Placeholder. Real version should run:
      godot --headless --check-only --script <target>
    and translate the exit code/stderr into the same
    {exit_code, stdout, stderr, passed} shape as _run().
    """
    return {
        "exit_code": 1,
        "stdout": "",
        "stderr": "check_gd_syntax: adapter not implemented yet",
        "passed": False,
    }


@eel.expose
def validate_scene_structure(target: str):
    """Placeholder for a .tscn structural validator."""
    return {
        "exit_code": 1,
        "stdout": "",
        "stderr": "validate_scene_structure: adapter not implemented yet",
        "passed": False,
    }


if __name__ == "__main__":
    eel.init(str(HERE / "web"))
    try:
        # Preferred: app-mode Chrome/Chromium window (no tabs/URL bar).
        eel.start("index.html", size=(1180, 780), port=0, mode="chrome")
    except EnvironmentError:
        # No Chrome/Chromium found — fall back to a normal tab in
        # whatever the system default browser is.
        print("No Chrome/Chromium found — opening in default browser instead.")
        eel.start("index.html", size=(1180, 780), port=0, mode="default")
