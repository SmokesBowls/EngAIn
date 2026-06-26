#!/usr/bin/env python3
"""
EngAIn Game Proof #006

Purpose:
    Prove that a validated, PROPOSED ProseTopologyArtifact can be accepted
    as spatial truth by the topologist gate.

Reads from #005:
    scratch/gameproof_005/output/topology_artifact.json
    scratch/gameproof_005/output/topology_validation_report.json

Pipeline:
    topology_artifact.json          (lifecycle: PROPOSED)
    topology_validation_report.json (passed: True)
    → gate_accept_proposed_topology_artifact
    → gate_report.json
    → accepted_spatial_truth_packet.json
    → runtime_payload.json
    → gameproof_report.json

This script does NOT:
    - call Trixel, Blender, Mechanimation, or Godot
    - mutate runtime
    - re-run pass1_spatial or the converter (those are #005's job)
    - invent or modify spatial relations

Exit codes:
    0 = proof passed (gate decision == ACCEPTED)
    2 = proof failed honestly
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

PROOF_005_OUT = REPO_ROOT / "scratch" / "gameproof_005" / "output"
ARTIFACT_PATH = PROOF_005_OUT / "topology_artifact.json"
REPORT_PATH   = PROOF_005_OUT / "topology_validation_report.json"

PROOF_ROOT  = REPO_ROOT / "scratch" / "gameproof_006"
OUTPUT_DIR  = PROOF_ROOT / "output"

PROOF_ID = "gameproof_006"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    print("EngAIn Game Proof #006 — Gate: PROPOSED → ACCEPTED spatial truth")
    print("=" * 72)
    print(f"Artifact : {ARTIFACT_PATH}")
    print(f"Report   : {REPORT_PATH}")
    print(f"Output   : {OUTPUT_DIR}")
    print()

    violations: list[str] = []
    files_written: list[str] = []

    # -- [1/4] Load #005 outputs ---------------------------------------------
    print("[1/4] Loading #005 artifact and validation report")

    for path, label in ((ARTIFACT_PATH, "topology_artifact"), (REPORT_PATH, "topology_validation_report")):
        if not path.exists():
            print(f"RESULT: FAILED — missing #005 output: {path}")
            print("Run Game Proof #005 first.")
            return 2

    artifact         = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    validation_report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    print(f"      artifact_id : {artifact.get('artifact_id')}")
    print(f"      lifecycle   : {artifact.get('lifecycle')}")
    print(f"      entities    : {len(artifact.get('entities', []))}")
    link_count = (
        len(artifact.get("olinks",    []))
        + len(artifact.get("qslinks",  []))
        + len(artifact.get("movelinks", []))
    )
    print(f"      links       : {link_count}")
    print(f"      val.passed  : {validation_report.get('passed')}")
    print(f"      val.violations: {len(validation_report.get('violations', []))}")

    # -- [2/4] Call gate -----------------------------------------------------
    print()
    print("[2/4] Calling gate_accept_proposed_topology_artifact")

    try:
        from tier2.topologist.gates.gate_accept_proposed_topology_artifact import (
            evaluate_topology_artifact_for_acceptance,
        )
        gate_result = evaluate_topology_artifact_for_acceptance(
            artifact=artifact,
            validation_report=validation_report,
        )
    except Exception as exc:
        import traceback
        err = traceback.format_exc()
        violations.append(f"gate import/call failed:\n{err}")
        print(f"      FAIL\n{err}")
        gate_result = None

    if gate_result is None:
        return _write_report(violations, files_written, None)

    print(f"      gate_id     : {gate_result['gate_id']}")
    print(f"      decision    : {gate_result['decision']}")
    print(f"      input_lifecycle  : {gate_result['input_lifecycle']}")
    print(f"      output_lifecycle : {gate_result['output_lifecycle']}")
    if gate_result["violations"]:
        for v in gate_result["violations"]:
            print(f"      VIOLATION: {v}")

    # -- [3/4] Write gate outputs --------------------------------------------
    print()
    print("[3/4] Writing gate outputs")

    gate_report_path = OUTPUT_DIR / "gate_report.json"
    write_json(gate_report_path, gate_result)
    files_written.append(str(gate_report_path.relative_to(REPO_ROOT)))
    print(f"      wrote: {gate_report_path}")

    accepted_packet = gate_result.get("accepted_spatial_truth_packet")
    if accepted_packet is not None:
        packet_path = OUTPUT_DIR / "accepted_spatial_truth_packet.json"
        write_json(packet_path, accepted_packet)
        files_written.append(str(packet_path.relative_to(REPO_ROOT)))
        print(f"      wrote: {packet_path}")

    runtime_payload = {
        "packet_type":              "game_state_draft",
        "proof_id":                 PROOF_ID,
        "status":                   "DRAFT_NOT_ACCEPTED",
        "created_at":               utc_now(),
        "runtime_mutation_allowed": False,
        "gate_id":                  gate_result["gate_id"],
        "gate_decision":            gate_result["decision"],
        "source_artifact_id":       artifact.get("artifact_id"),
        "accepted_spatial_truth":   accepted_packet,
        "presentation": {
            "art_assets_required_now":  False,
            "placeholder_render_allowed": True,
            "trixel_payload":           None,
            "blender_payload":          None,
            "mechanimation_payload":    None,
        },
    }

    runtime_path = OUTPUT_DIR / "runtime_payload.json"
    write_json(runtime_path, runtime_payload)
    files_written.append(str(runtime_path.relative_to(REPO_ROOT)))
    print(f"      wrote: {runtime_path}")

    # -- [4/4] Validate proof conditions -------------------------------------
    print()
    print("[4/4] Validating proof")

    if gate_result["decision"] != "ACCEPTED":
        violations.append(
            f"gate decision is '{gate_result['decision']}', expected 'ACCEPTED'. "
            f"Gate violations: {gate_result['violations']}"
        )

    if gate_result.get("accepted_spatial_truth_packet") is None:
        violations.append("gate returned no accepted_spatial_truth_packet")

    if runtime_payload["presentation"]["trixel_payload"] is not None:
        violations.append("trixel_payload must be null")

    if runtime_payload["runtime_mutation_allowed"] is not False:
        violations.append("runtime_mutation_allowed must be false")

    return _write_report(violations, files_written, gate_result)


def _write_report(
    violations: list[str],
    files_written: list[str],
    gate_result: dict[str, Any] | None,
) -> int:
    report = {
        "proof_id":     PROOF_ID,
        "passed":       not violations,
        "created_at":   utc_now(),
        "gate_id":      gate_result["gate_id"]    if gate_result else None,
        "gate_decision": gate_result["decision"]  if gate_result else None,
        "violations":   violations,
        "files_written": files_written,
        "notes": [
            "Reads #005 topology_artifact.json (lifecycle: PROPOSED) and "
            "topology_validation_report.json.",
            "Calls gate_accept_proposed_topology_artifact directly.",
            "Gate decision ACCEPTED advances the artifact to accepted spatial truth.",
            "No Trixel call was made.",
            "No Blender call was made.",
            "No Mechanimation call was made.",
            "No Godot runtime mutation was made.",
        ],
    }

    report_path = OUTPUT_DIR / "gameproof_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(report_path, report)
    print(f"      wrote: {report_path}")

    print()
    print("[Result]")

    if violations:
        print("RESULT: FAILED HONESTLY")
        for v in violations:
            print(f"  - {v}")
        return 2

    print("RESULT: PASSED")
    print()
    print("EngAIn accepted a validated ProseTopologyArtifact as spatial truth.")
    print("No art lane was required.")
    print("No external sibling tool was required.")
    print("No runtime mutation occurred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
