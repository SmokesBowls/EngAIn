#!/usr/bin/env python3
"""
Run active EngAInOS gates by lifecycle.

This runner reads each gate file's GATE_LIFECYCLE constant and runs only gates
that are meant to be rerunnable.

Default active lifecycles:
  ACTIVE_VERIFICATION
  ACTIVE_CONTRACT

It skips:
  PREFLIGHT
  RETIRED_AFTER_ACCEPTANCE
  ARCHIVED_NON_SIGNAL
  STALE_EXPECTATION

Doctrine:
  Migration preflight gates are not active rerun gates.
  Verification gates prove accepted migration state.
  Contract gates prove current system law.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GATES_ROOT = REPO_ROOT / "engainos/gates"
REPORT_PATH = REPO_ROOT / "scratch/active_gates_report.json"

DEFAULT_ACTIVE_LIFECYCLES = {
    "ACTIVE_VERIFICATION",
    "ACTIVE_CONTRACT",
}

SKIP_LIFECYCLES = {
    "PREFLIGHT",
    "RETIRED_AFTER_ACCEPTANCE",
    "ARCHIVED_NON_SIGNAL",
    "STALE_EXPECTATION",
    "SUPPORT_LIBRARY",
}


@dataclass(frozen=True)
class GateRun:
    path: str
    lifecycle: str
    selected: bool
    returncode: int | None
    stdout: str
    stderr: str
    status: str


def literal_assignment(path: Path, name: str) -> Any:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return None

        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                try:
                    return ast.literal_eval(node.value)
                except Exception:
                    return None

    return None


def discover_gate_files() -> list[Path]:
    return sorted(
        path for path in GATES_ROOT.glob("gate_*.py")
        if path.name != "run_active_gates.py"
    )


def run_gate(path: Path) -> GateRun:
    rel = path.relative_to(REPO_ROOT)
    lifecycle = literal_assignment(path, "GATE_LIFECYCLE") or "UNKNOWN"

    if lifecycle not in DEFAULT_ACTIVE_LIFECYCLES:
        return GateRun(
            path=str(rel),
            lifecycle=str(lifecycle),
            selected=False,
            returncode=None,
            stdout="",
            stderr="",
            status="SKIPPED",
        )

    env = dict(__import__("os").environ)
    existing_pythonpath = env.get("PYTHONPATH", "")
    repo_pythonpath = str(REPO_ROOT)
    env["PYTHONPATH"] = (
        repo_pythonpath
        if not existing_pythonpath
        else repo_pythonpath + ":" + existing_pythonpath
    )

    proc = subprocess.run(
        [sys.executable, str(rel)],
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
        env=env,
    )

    return GateRun(
        path=str(rel),
        lifecycle=str(lifecycle),
        selected=True,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        status="PASS" if proc.returncode == 0 else "FAIL",
    )


def main() -> int:
    gate_files = discover_gate_files()
    runs = [run_gate(path) for path in gate_files]

    selected = [run for run in runs if run.selected]
    failed = [run for run in selected if run.returncode != 0]
    unknown = [
        run for run in runs
        if run.lifecycle == "UNKNOWN"
    ]

    report = {
        "refactor_id": "ENGAINOS_ACTIVE_GATE_RUNNER_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_gate_board",
        "active_lifecycles": sorted(DEFAULT_ACTIVE_LIFECYCLES),
        "skip_lifecycles": sorted(SKIP_LIFECYCLES),
        "gate_count_total": len(runs),
        "gate_count_selected": len(selected),
        "gate_count_failed": len(failed),
        "gate_count_unknown_lifecycle": len(unknown),
        "runs": [asdict(run) for run in runs],
        "acceptance": "ACCEPTED" if not failed and not unknown else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for run in runs:
        if run.selected:
            print(
                f"[run_active_gates][{run.lifecycle}][{run.status}] "
                f"{run.path} returncode={run.returncode}"
            )
        else:
            print(
                f"[run_active_gates][{run.lifecycle}][SKIP] "
                f"{run.path}"
            )

    if unknown:
        print("[run_active_gates][UNKNOWN_LIFECYCLE] false")
        for run in unknown:
            print(f"[run_active_gates][UNKNOWN] {run.path}")

    print(f"[run_active_gates][REPORT] {REPORT_PATH}")
    print(f"[run_active_gates][ALL_SELECTED_GATES] {'true' if not failed else 'false'}")
    print(f"[run_active_gates][ALL_GATES_HAVE_LIFECYCLE] {'true' if not unknown else 'false'}")

    return 0 if not failed and not unknown else 2


if __name__ == "__main__":
    raise SystemExit(main())
