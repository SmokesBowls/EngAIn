#!/usr/bin/env python3
"""
EngAIn Game Proof #008 — MrLore narrative concurrence.

Input:
    scratch/gameproof_006/output/accepted_spatial_truth_packet.json
    scratch/gameproof_007/output/proposed_metric_layout_packet.json
    scratch/gameproof_005/output/topology_artifact.json

Output:
    scratch/gameproof_008/output/mrlore_narrative_concurrence_report.json
    scratch/gameproof_008/output/gate_report.json
    scratch/gameproof_008/output/concurred_metric_layout_packet.json
    scratch/gameproof_008/output/gameproof_report.json

This proof does not call EngAInOS authority runtime, Trixel, GodotSim, or Godot.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

ACCEPTED_TRUTH_PATH = (
    REPO_ROOT
    / "scratch"
    / "gameproof_006"
    / "output"
    / "accepted_spatial_truth_packet.json"
)
PROPOSED_LAYOUT_PATH = (
    REPO_ROOT
    / "scratch"
    / "gameproof_007"
    / "output"
    / "proposed_metric_layout_packet.json"
)
TOPO_ARTIFACT_PATH = (
    REPO_ROOT
    / "scratch"
    / "gameproof_005"
    / "output"
    / "topology_artifact.json"
)

OUTPUT_DIR = REPO_ROOT / "scratch" / "gameproof_008" / "output"
PROOF_ID = "gameproof_008"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def run() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    print("=" * 72)
    print("EngAIn Game Proof #008 — MrLore Narrative Concurrence Proof")
    print("=" * 72)
    print(f"Accepted Truth  : {ACCEPTED_TRUTH_PATH}")
    print(f"Proposed Layout : {PROPOSED_LAYOUT_PATH}")
    print(f"Topo Artifact   : {TOPO_ARTIFACT_PATH}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()

    violations: list[str] = []
    files_written: list[str] = []

    # Check dependencies
    missing_deps = []
    for p in (ACCEPTED_TRUTH_PATH, PROPOSED_LAYOUT_PATH, TOPO_ARTIFACT_PATH):
        if not p.exists():
            missing_deps.append(str(p.relative_to(REPO_ROOT)))

    if missing_deps:
        report = {
            "proof_id": PROOF_ID,
            "passed": False,
            "created_at": utc_now(),
            "violations": [
                f"MISSING_UPSTREAM_PROOF_DEPENDENCY: {missing_deps}. Ensure previous proofs have run."
            ],
            "files_written": [],
        }
        write_json(OUTPUT_DIR / "gameproof_report.json", report)
        print(report["violations"][0])
        return 2

    # Load inputs
    accepted_spatial_truth = read_json(ACCEPTED_TRUTH_PATH)
    proposed_metric_layout = read_json(PROPOSED_LAYOUT_PATH)
    topology_artifact = read_json(TOPO_ARTIFACT_PATH)
    source_prose = topology_artifact.get("source_prose")

    # Import MrLore checkers and gates
    from tier1.mrlore.gates.gate_narrative_concurrence import (
        evaluate_metric_layout_for_concurrence,
    )
    from tier1.mrlore.mrlore_narrative_concurrence_checker import (
        verify_concurrence,
    )

    print("[1/4] Running MrLore narrative concurrence checks")
    try:
        concurrence_report = verify_concurrence(
            accepted_spatial_truth=accepted_spatial_truth,
            proposed_metric_layout=proposed_metric_layout,
            source_prose=source_prose,
        )
    except Exception as exc:
        import traceback
        violations.append(
            "MrLore concurrence check crashed:\n" + traceback.format_exc()
        )
        return _write_report(violations, files_written, None)

    report_path = OUTPUT_DIR / "mrlore_narrative_concurrence_report.json"
    write_json(report_path, concurrence_report)
    files_written.append(str(report_path.relative_to(REPO_ROOT)))
    print(f"      decision: {concurrence_report['concurrence_decision']}")
    print(f"      contradictions: {len(concurrence_report['contradictions'])}")
    print(f"      unresolved findings: {len(concurrence_report['unresolved_findings'])}")
    print(f"      wrote: {report_path}")

    print("[2/4] Executing MrLore Concurrence Gate")
    gate_report = evaluate_metric_layout_for_concurrence(
        proposed_metric_layout=proposed_metric_layout,
        concurrence_report=concurrence_report,
    )
    gate_path = OUTPUT_DIR / "gate_report.json"
    write_json(gate_path, gate_report)
    files_written.append(str(gate_path.relative_to(REPO_ROOT)))
    print(f"      gate decision: {gate_report['decision']}")
    print(f"      wrote: {gate_path}")

    concurred_packet = gate_report.get("concurred_metric_layout_packet")
    if concurred_packet is not None:
        concurred_path = OUTPUT_DIR / "concurred_metric_layout_packet.json"
        write_json(concurred_path, concurred_packet)
        files_written.append(str(concurred_path.relative_to(REPO_ROOT)))
        print(f"      wrote: {concurred_path}")

    print("[3/4] Checking boundaries and constraints")

    if concurrence_report.get("concurrence_decision") != "CONCURRED":
        violations.append(
            f"concurrence failed: contradictions={concurrence_report.get('contradictions')}; "
            f"findings={concurrence_report.get('unresolved_findings')}"
        )

    if gate_report.get("decision") != "CONCURRED":
        violations.append(
            f"gate rejected proposal: violations={gate_report.get('violations')}"
        )

    if concurred_packet is None:
        violations.append("Gate returned no concurred_metric_layout_packet")
    else:
        if concurred_packet.get("packet_type") != "narratively_concurred_metric_layout":
            violations.append("concurred packet has wrong packet_type")
        if concurred_packet.get("lifecycle") != "CONCURRED":
            violations.append("concurred packet has wrong lifecycle")
        # Ensure layout coords are unaltered
        orig_entities = proposed_metric_layout.get("entities", [])
        new_entities = concurred_packet.get("metric_layout", {}).get("entities", [])
        if orig_entities != new_entities:
            violations.append("coordinates mutated during concurrence check")

    return _write_report(violations, files_written, gate_report)


def _write_report(
    violations: list[str],
    files_written: list[str],
    gate_report: dict[str, Any] | None,
) -> int:
    report = {
        "proof_id": PROOF_ID,
        "passed": not violations,
        "created_at": utc_now(),
        "inputs": [
            str(ACCEPTED_TRUTH_PATH.relative_to(REPO_ROOT)),
            str(PROPOSED_LAYOUT_PATH.relative_to(REPO_ROOT)),
            str(TOPO_ARTIFACT_PATH.relative_to(REPO_ROOT)),
        ],
        "gate_id": gate_report.get("gate_id") if gate_report else None,
        "gate_decision": gate_report.get("decision") if gate_report else None,
        "violations": violations,
        "files_written": files_written,
        "boundaries": {
            "mrlore_altered_coordinates": False,
            "cartographer_rerun": False,
            "engainos_authority_called": False,
            "trixel_called": False,
            "godotsim_called": False,
            "godot_started": False,
            "runtime_mutated": False,
        },
        "next_required_stage": (
            "Milestone 009: EngAInOS contract and authority verification."
        ),
    }

    report_path = OUTPUT_DIR / "gameproof_report.json"
    write_json(report_path, report)
    print(f"      wrote: {report_path}")
    print()

    if violations:
        print("RESULT: FAILED HONESTLY")
        for v in violations:
            print(f"  - {v}")
        return 2

    print("RESULT: PASSED")
    print("MrLore narrative concurrence successfully checked and stamped coordinates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
