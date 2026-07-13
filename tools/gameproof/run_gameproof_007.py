#!/usr/bin/env python3
"""
EngAIn Game Proof #007 — Cartographer metric-layout proposal.

Input:
    scratch/gameproof_006/output/accepted_spatial_truth_packet.json

Output:
    scratch/gameproof_007/output/draft_metric_layout_artifact.json
    scratch/gameproof_007/output/metric_layout_validation_report.json
    scratch/gameproof_007/output/gate_report.json
    scratch/gameproof_007/output/proposed_metric_layout_packet.json
    scratch/gameproof_007/output/gameproof_report.json

This proof does not call MrLore, EngAInOS runtime, Trixel, GodotSim, or Godot.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = (
    REPO_ROOT
    / "scratch"
    / "gameproof_006"
    / "output"
    / "accepted_spatial_truth_packet.json"
)
OUTPUT_DIR = REPO_ROOT / "scratch" / "gameproof_007" / "output"
PROOF_ID = "gameproof_007"


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
    print("EngAIn Game Proof #007 — Cartographer Metric Layout Proposal")
    print("=" * 72)
    print(f"Input : {INPUT_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    violations: list[str] = []
    files_written: list[str] = []

    if not INPUT_PATH.exists():
        report = {
            "proof_id": PROOF_ID,
            "passed": False,
            "created_at": utc_now(),
            "violations": [
                "MISSING_UPSTREAM_PROOF_DEPENDENCY: "
                f"{INPUT_PATH}. Run tools/gameproof/run_gameproof_006.py first."
            ],
            "files_written": [],
        }
        write_json(OUTPUT_DIR / "gameproof_report.json", report)
        print(report["violations"][0])
        return 2

    accepted_spatial_truth = read_json(INPUT_PATH)

    from tier2.cartographer.gates.gate_propose_metric_layout import (
        evaluate_metric_layout_for_proposal,
    )
    from tier2.cartographer.layoutroom.topology_metric_layout_solver import (
        build_metric_layout,
    )
    from tier2.cartographer.reckoningroom.metric_layout_validator import (
        validate_metric_layout_artifact,
    )

    print("[1/4] Building DRAFT metric layout")
    try:
        draft_artifact_object = build_metric_layout(accepted_spatial_truth)
        draft_artifact = draft_artifact_object.to_dict()
    except Exception as exc:
        import traceback

        violations.append(
            "Cartographer solver failed:\n" + traceback.format_exc()
        )
        return _write_report(violations, files_written, None)

    draft_path = OUTPUT_DIR / "draft_metric_layout_artifact.json"
    write_json(draft_path, draft_artifact)
    files_written.append(str(draft_path.relative_to(REPO_ROOT)))
    print(f"      wrote: {draft_path}")

    print("[2/4] Validating metric layout")
    validation_report = validate_metric_layout_artifact(
        draft_artifact,
        accepted_spatial_truth,
    )
    validation_path = OUTPUT_DIR / "metric_layout_validation_report.json"
    write_json(validation_path, validation_report)
    files_written.append(str(validation_path.relative_to(REPO_ROOT)))
    print(f"      passed: {validation_report['passed']}")
    print(f"      wrote : {validation_path}")

    print("[3/4] Calling Cartographer proposal gate")
    gate_report = evaluate_metric_layout_for_proposal(
        draft_artifact,
        validation_report,
    )
    gate_path = OUTPUT_DIR / "gate_report.json"
    write_json(gate_path, gate_report)
    files_written.append(str(gate_path.relative_to(REPO_ROOT)))
    print(f"      decision: {gate_report['decision']}")
    print(f"      wrote   : {gate_path}")

    proposed_packet = gate_report.get("proposed_metric_layout_packet")
    if proposed_packet is not None:
        proposed_path = OUTPUT_DIR / "proposed_metric_layout_packet.json"
        write_json(proposed_path, proposed_packet)
        files_written.append(str(proposed_path.relative_to(REPO_ROOT)))
        print(f"      wrote   : {proposed_path}")

    print("[4/4] Checking proof conditions")

    if not validation_report.get("passed", False):
        violations.append(
            "metric-layout validation failed: "
            f"{validation_report.get('violations', [])}"
        )

    if gate_report.get("decision") != "PROPOSED":
        violations.append(
            f"gate decision was {gate_report.get('decision')}, expected PROPOSED"
        )

    if proposed_packet is None:
        violations.append("gate returned no proposed_metric_layout_packet")
    else:
        if proposed_packet.get("packet_type") != "proposed_metric_layout":
            violations.append("proposed packet has wrong packet_type")
        if proposed_packet.get("coordinate_space") != "world_cell_y_up":
            violations.append("proposed packet has wrong coordinate_space")
        if proposed_packet.get("lifecycle") != "PROPOSED":
            violations.append("proposed packet lifecycle is not PROPOSED")

        source_ids = {
            str(entity.get("entity_id"))
            for entity in accepted_spatial_truth.get("entities", [])
        }
        proposed_ids = {
            str(entity.get("entity_id"))
            for entity in proposed_packet.get("entities", [])
        }
        if source_ids != proposed_ids:
            violations.append(
                f"entity identity drift: source={sorted(source_ids)} "
                f"proposed={sorted(proposed_ids)}"
            )

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
        "input": str(INPUT_PATH.relative_to(REPO_ROOT)),
        "gate_id": gate_report.get("gate_id") if gate_report else None,
        "gate_decision": gate_report.get("decision") if gate_report else None,
        "violations": violations,
        "files_written": files_written,
        "boundaries": {
            "mrlore_called": False,
            "engainos_authority_called": False,
            "trixel_called": False,
            "godotsim_called": False,
            "godot_started": False,
            "runtime_mutated": False,
        },
        "next_required_stage": (
            "MrLore narrative concurrence over the combined accepted topology "
            "and proposed metric layout."
        ),
    }

    report_path = OUTPUT_DIR / "gameproof_report.json"
    write_json(report_path, report)

    print(f"      wrote: {report_path}")
    print()

    if violations:
        print("RESULT: FAILED HONESTLY")
        for violation in violations:
            print(f"  - {violation}")
        return 2

    print("RESULT: PASSED")
    print("Cartographer produced a deterministic PROPOSED metric layout.")
    print("The proposal has not yet received MrLore concurrence or EngAInOS authority.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
