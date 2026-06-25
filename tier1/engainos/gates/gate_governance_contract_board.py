from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REPORT_PATH = REPO_ROOT / "scratch/governance_contract_board_report.json"

from tier1.engainos.gates.gate_packet_identity import gate_packet_identity
from tier1.engainos.gates.gate_declared_truth_shape import gate_declared_truth_shape
from tier1.engainos.gates.gate_validated_packets_shape import gate_validated_packets_shape
from tier1.engainos.gates.gate_acceptance_rule import gate_acceptance_rule_enforced
from tier1.engainos.gates.gate_no_simulation_execution import gate_no_simulation_execution
from tier1.engainos.gates.gate_no_asset_production import gate_no_asset_production
from tier1.engainos.gates.gate_no_presentation_authority import gate_no_presentation_authority
from tier1.engainos.gates.gate_no_lane_theft_in_packet import gate_no_lane_theft_in_packet

@dataclass(frozen=True)
class BoardGateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

VALID_BASE_PACKET: dict[str, Any] = {
    "contract": "tier1.engainos.governance_packet.v1",
    "source": "engainos",
    "authority_tier": 1,
    "authority_lane": "governance",
    "scene_id": "scene.030_ummade_army",
    "decision_id": "decision_001",
    "decision_type": "runtime_acceptance",
    "acceptance_decision": "accepted",
    "declared_scene_truth": {
        "scene_id": "scene.030_ummade_army",
        "status": "declared",
    },
    "declared_entity_truth": [
        {
            "entity_id": "mika_01",
            "status": "declared",
        }
    ],
    "validated_packets": [
        {
            "source": "godotsim",
            "contract": "godotsim.spatial_sim_packet.v1",
            "result": "accepted",
        }
    ],
    "ap_validation": {
        "result": "passed",
        "gate_count": 3,
    },
}

def status_is_true(result: Any) -> bool:
    return getattr(result, "passed", None) == "TRUE" or getattr(result, "status", None) == "TRUE"

def status_is_false(result: Any) -> bool:
    return getattr(result, "passed", None) == "FALSE" or getattr(result, "status", None) == "FALSE"

def run_support_gate(name: str, fn: Any, packet: dict[str, Any], expected: str) -> BoardGateResult:
    result = fn(packet)

    if expected == "TRUE":
        passed = status_is_true(result)
    elif expected == "FALSE":
        passed = status_is_false(result)
    else:
        raise ValueError(f"Unsupported expected status: {expected}")

    return BoardGateResult(
        gate_name=name,
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=f"{name} returned expected {expected}" if passed else f"{name} did not return expected {expected}",
        details={
            "expected": expected,
            "actual_passed": getattr(result, "passed", None),
            "actual_status": getattr(result, "status", None),
            "actual_message": getattr(result, "message", None),
        },
    )

def main() -> int:
    valid = dict(VALID_BASE_PACKET)

    bad_simulation = {**VALID_BASE_PACKET, "position": [0.0, 0.0, 0.0]}
    bad_asset = {**VALID_BASE_PACKET, "asset_id": "mesh_001"}
    bad_presentation = {**VALID_BASE_PACKET, "render": True}
    bad_acceptance = {
        **VALID_BASE_PACKET,
        "ap_validation": {
            "result": "failed",
            "gate_count": 3,
        },
    }
    bad_validated_packet_embed = {
        **VALID_BASE_PACKET,
        "validated_packets": [
            {
                "source": "godotsim",
                "contract": "godotsim.spatial_sim_packet.v1",
                "result": "accepted",
                "position": [1, 2, 3],
            }
        ],
    }
    bad_declared_truth = {
        **VALID_BASE_PACKET,
        "declared_scene_truth": {
            "scene_id": "wrong_scene",
            "status": "declared",
        },
    }

    results = [
        run_support_gate("GATE_VALID_PACKET_IDENTITY", gate_packet_identity, valid, "TRUE"),
        run_support_gate("GATE_VALID_DECLARED_TRUTH_SHAPE", gate_declared_truth_shape, valid, "TRUE"),
        run_support_gate("GATE_VALID_VALIDATED_PACKETS_SHAPE", gate_validated_packets_shape, valid, "TRUE"),
        run_support_gate("GATE_VALID_ACCEPTANCE_RULE", gate_acceptance_rule_enforced, valid, "TRUE"),
        run_support_gate("GATE_VALID_NO_SIMULATION_EXECUTION", gate_no_simulation_execution, valid, "TRUE"),
        run_support_gate("GATE_VALID_NO_ASSET_PRODUCTION", gate_no_asset_production, valid, "TRUE"),
        run_support_gate("GATE_VALID_NO_PRESENTATION_AUTHORITY", gate_no_presentation_authority, valid, "TRUE"),
        run_support_gate("GATE_VALID_NO_LANE_THEFT", gate_no_lane_theft_in_packet, valid, "TRUE"),

        run_support_gate("GATE_REJECTS_SIMULATION_KEY", gate_no_simulation_execution, bad_simulation, "FALSE"),
        run_support_gate("GATE_REJECTS_ASSET_KEY", gate_no_asset_production, bad_asset, "FALSE"),
        run_support_gate("GATE_REJECTS_PRESENTATION_KEY", gate_no_presentation_authority, bad_presentation, "FALSE"),
        run_support_gate("GATE_REJECTS_FAILED_AP_ACCEPTANCE", gate_acceptance_rule_enforced, bad_acceptance, "FALSE"),
        run_support_gate("GATE_REJECTS_FULL_PACKET_EMBED_IN_VALIDATED_PACKETS", gate_validated_packets_shape, bad_validated_packet_embed, "FALSE"),
        run_support_gate("GATE_REJECTS_DECLARED_TRUTH_SCENE_MISMATCH", gate_declared_truth_shape, bad_declared_truth, "FALSE"),
        run_support_gate("GATE_REJECTS_LANE_THEFT_SIMULATION_KEY", gate_no_lane_theft_in_packet, bad_simulation, "FALSE"),
        run_support_gate("GATE_REJECTS_LANE_THEFT_ASSET_KEY", gate_no_lane_theft_in_packet, bad_asset, "FALSE"),
        run_support_gate("GATE_REJECTS_LANE_THEFT_PRESENTATION_KEY", gate_no_lane_theft_in_packet, bad_presentation, "FALSE"),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "ENGAINOS_GOVERNANCE_CONTRACT_BOARD_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_governance_contract_board",
        "support_libraries": [
            "gate_packet_identity.py",
            "gate_declared_truth_shape.py",
            "gate_validated_packets_shape.py",
            "gate_acceptance_rule.py",
            "gate_no_simulation_execution.py",
            "gate_no_asset_production.py",
            "gate_no_presentation_authority.py",
            "gate_no_lane_theft_in_packet.py",
        ],
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_governance_contract_board][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_governance_contract_board][REPORT] {REPORT_PATH}")
    print(f"[gate_governance_contract_board][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
