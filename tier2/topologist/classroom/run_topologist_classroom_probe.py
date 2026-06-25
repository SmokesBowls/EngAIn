#!/usr/bin/env python3
"""
classroom/run_topologist_classroom_probe.py
──────────────────────────────────────────────────────────────────────────────
First proof run for the Prose Geometrical Topologist.

This probe does NOT test prose extraction.
This probe does NOT call Godot.
This probe does NOT create coordinates.

The proof question is:
  "Can the Topologist define and validate a topology artifact without
   stealing GodotSim, Trixel, or EngAInOS authority?"

Steps
  1. Load fixture  →  classroom/fixtures/simple_guard_king_artifact.json
  2. Deserialise   →  ProseTopologyArtifact
  3. Validate      →  TopologyValidator → ValidationReport
  4. Write report  →  classroom/reports/simple_guard_king_report.json
  5. Print summary to stdout

Run from repo root:
    python -m tier2.topologist.classroom.run_topologist_classroom_probe
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# ── path setup ───────────────────────────────────────────────────────────────
# Allow running from repo root without installing the package.
_HERE = Path(__file__).resolve().parent          # classroom/
_TOPOLOGIST = _HERE.parent                       # tier2/topologist/
_TIER2 = _TOPOLOGIST.parent                     # tier2/
_REPO = _TIER2.parent                           # repo root
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tier2.topologist.artifactroom.topology_artifact import ProseTopologyArtifact
from tier2.topologist.reckoningroom.topology_validator import TopologyValidator


# ── paths ────────────────────────────────────────────────────────────────────
FIXTURE_PATH = _HERE / "fixtures" / "simple_guard_king_artifact.json"
REPORT_DIR   = _HERE / "reports"
REPORT_PATH  = REPORT_DIR / "simple_guard_king_report.json"


def run_probe() -> int:
    """
    Execute the classroom probe.
    Returns 0 on clean validation pass, 1 on violations found, 2 on error.
    """
    print("=" * 70)
    print("  Prose Geometrical Topologist — Classroom Probe #001")
    print("  Fixture : simple_guard_king_artifact")
    print("  Proof   : artifact law, not prose extraction")
    print("=" * 70)

    # ── 1. Load fixture ───────────────────────────────────────────────────
    print(f"\n[1/4] Loading fixture …  {FIXTURE_PATH}")
    if not FIXTURE_PATH.exists():
        print(f"  ERROR: fixture not found at {FIXTURE_PATH}")
        return 2

    with open(FIXTURE_PATH, "r", encoding="utf-8") as fh:
        raw_dict = json.load(fh)

    print(f"      artifact_id : {raw_dict.get('artifact_id')}")
    print(f"      lifecycle   : {raw_dict.get('lifecycle')}")
    print(f"      entities    : {len(raw_dict.get('entities', []))}")
    print(f"      qslinks     : {len(raw_dict.get('qslinks', []))}")
    print(f"      olinks      : {len(raw_dict.get('olinks', []))}")
    print(f"      movelinks   : {len(raw_dict.get('movelinks', []))}")

    # ── 2. Deserialise ────────────────────────────────────────────────────
    print("\n[2/4] Deserialising to ProseTopologyArtifact …")
    try:
        artifact = ProseTopologyArtifact.from_dict(raw_dict)
        print(f"      OK — {len(artifact.entities)} entities loaded")
    except Exception as exc:
        print(f"  ERROR during deserialisation: {exc}")
        return 2

    # ── 3. Validate ───────────────────────────────────────────────────────
    print("\n[3/4] Running TopologyValidator …")
    validator = TopologyValidator()
    report = validator.validate(artifact, raw_dict)

    print(f"      checks run  : {len(report.checks_run)}")
    print(f"      violations  : {len(report.violations)}")
    print(f"      PASSED      : {report.passed}")

    if report.violations:
        print("\n  ── VIOLATIONS ──────────────────────────────────────────")
        for v in report.violations:
            tag = f"[{v.link_id}] " if v.link_id else ""
            print(f"    ✗  {v.code.value}  {tag}")
            print(f"       {v.detail}")
    if report.notes:
        print("\n  ── NOTES ───────────────────────────────────────────────")
        for n in report.notes:
            print(f"    ℹ  {n}")

    # ── 4. Write report ───────────────────────────────────────────────────
    print(f"\n[4/4] Writing report …  {REPORT_PATH}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write(report.to_json(indent=2))
    print(f"      Written ({REPORT_PATH.stat().st_size} bytes)")

    # ── summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    if report.passed:
        print("  ✅  PROOF PASSED — artifact is topologically clean.")
        print("      No Godot coordinates.  No render fields.  No Trixel data.")
        print("      Lifecycle is open.  All links reference known entities.")
        print("      Ready for gate evaluation.")
        return 0
    else:
        print(f"  ❌  PROOF FAILED — {len(report.violations)} violation(s) found.")
        print("      See report for details.")
        return 1


if __name__ == "__main__":
    sys.exit(run_probe())
