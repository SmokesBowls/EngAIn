from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

GATE_PATH = REPO_ROOT / "engainos/gates/gate_gamestate_draft_review_ready.py"
SCRATCH_DIR = REPO_ROOT / "scratch/gamestate_draft_review_contract"
REPORT_PATH = REPO_ROOT / "scratch/gamestate_draft_review_contract_report.json"

@dataclass(frozen=True)
class BoardGateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

def load_review_module() -> Any:
    spec = importlib.util.spec_from_file_location("gamestate_draft_review_ready_probe", GATE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {GATE_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["gamestate_draft_review_ready_probe"] = module
    spec.loader.exec_module(module)
    return module

def write_case(case_id: str, payload: dict[str, Any]) -> Path:
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    path = SCRATCH_DIR / f"{case_id}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path

def normalize_result(result: Any) -> dict[str, Any]:
    if hasattr(result, "__dict__"):
        value = dict(result.__dict__)
        if "gate_results" in value:
            value["gate_results"] = list(value["gate_results"])
        return value

    if isinstance(result, dict):
        return result

    return {"repr": repr(result), "type": type(result).__name__}

def call_review(module: Any, payload: dict[str, Any]) -> dict[str, Any]:
    path = write_case(payload["case_id"], payload["draft"])
    draft = module.load_json_file(path)

    if hasattr(module, "review_gamestate_draft_file"):
        result = module.review_gamestate_draft_file(path)
    elif hasattr(module, "review_gamestate_draft"):
        result = module.review_gamestate_draft(draft)
    elif hasattr(module, "build_draft_review_result"):
        # build_draft_review_result is a historical helper and its signature
        # may not accept source=. Call it positionally only.
        result = module.build_draft_review_result(draft)
    else:
        raise AttributeError("No known gamestate draft review entrypoint found.")

    return normalize_result(result)

def case_payload(case_id: str, draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "draft": draft,
    }

def make_base_draft() -> dict[str, Any]:
    return {
        "contract": "engainos.gamestate_draft.v1",
        "source": "engainos.zonj_runtime_acceptance_adapter",
        "authority_tier": 1,
        "authority_lane": "zonj_runtime_acceptance_adapter",
        "scene_id": "scene.test_review",
        "draft_status": "PENDING_ACCEPTANCE",
        "accepted_for_runtime": False,
        "declaration_count": 1,
        "draft_empty": False,
        "runtime_meaningful": True,
        "gate_results": [
            {
                "gate_name": "GATE_TEST_ADAPTER_READY",
                "status": "TRUE",
                "message": "test adapter gate passed",
                "details": {},
            }
        ],
        "entities": [
            {
                "entity_id": "hero",
                "entity_type": "character",
            }
        ],
        "proposed_changes": [],
        "validated_packets": [],
    }


def nested_smuggle(base: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
    draft = json.loads(json.dumps(base))
    draft["entities"][0]["nested_payload"] = {
        "inner": [
            {
                key: value,
            }
        ]
    }
    return draft

def evaluate_case(module: Any, case_id: str, draft: dict[str, Any], expected_ready: bool) -> BoardGateResult:
    result = call_review(module, case_payload(case_id, draft))

    review_status = result.get("review_status")
    accepted_for_runtime = result.get("accepted_for_runtime")
    committed_gamestate = result.get("committed_gamestate")
    starts_workers = result.get("starts_workers")

    hardcoded_safety = (
        accepted_for_runtime is False
        and committed_gamestate is False
        and starts_workers is False
    )

    if expected_ready:
        status_ok = review_status == "GAMESTATE_DRAFT_REVIEW_READY"
    else:
        status_ok = review_status in {
            "GAMESTATE_DRAFT_REVIEW_REJECTED",
            "BLOCKED_PENDING_TIER1_REVIEW",
        }

    passed = hardcoded_safety and status_ok

    return BoardGateResult(
        gate_name=f"GATE_GAMESTATE_DRAFT_{case_id.upper()}",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message=f"{case_id} behaved as expected." if passed else f"{case_id} did not behave as expected.",
        details={
            "expected_ready": expected_ready,
            "review_status": review_status,
            "accepted_for_runtime": accepted_for_runtime,
            "committed_gamestate": committed_gamestate,
            "starts_workers": starts_workers,
            "result": result,
        },
    )

def main() -> int:
    module = load_review_module()
    base = make_base_draft()

    cases = [
        ("valid_review_ready", base, True),
        ("top_level_accepted_for_runtime_rejected", {**base, "accepted_for_runtime": True}, False),
        ("top_level_committed_gamestate_rejected", {**base, "committed_gamestate": {"scene_id": "scene.test_review"}}, False),
        ("top_level_starts_workers_rejected", {**base, "starts_workers": True}, False),
        ("nested_accepted_for_runtime_rejected", nested_smuggle(base, "accepted_for_runtime", True), False),
        ("nested_committed_gamestate_rejected", nested_smuggle(base, "committed_gamestate", {"scene_id": "scene.test_review"}), False),
        ("nested_starts_workers_rejected", nested_smuggle(base, "starts_workers", True), False),
    ]

    results = [
        evaluate_case(module, case_id, draft, expected_ready)
        for case_id, draft, expected_ready in cases
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "GAMESTATE_DRAFT_REVIEW_CONTRACT_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "gamestate_draft_review_contract",
        "parameterized_gate": str(GATE_PATH),
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_gamestate_draft_review_contract][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_gamestate_draft_review_contract][REPORT] {REPORT_PATH}")
    print(f"[gate_gamestate_draft_review_contract][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
