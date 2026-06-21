from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import importlib.util
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

AP_RUNTIME_PATH = REPO_ROOT / "godotengain/engainos/core/ap_runtime.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_behavior_probe_report.json"
SCRATCH_ROOT = REPO_ROOT / "scratch/ap_runtime_behavior_probe"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

def load_ap_runtime_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "historical_ap_runtime_behavior_probe",
        AP_RUNTIME_PATH,
    )

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {AP_RUNTIME_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["historical_ap_runtime_behavior_probe"] = module
    spec.loader.exec_module(module)
    return module

def build_rules() -> dict[str, dict[str, Any]]:
    return {
        "wake_hero": {
            "tags": ["probe"],
            "requires": [],
            "conflicts": [],
            "effects": [
                'set_flag(hero, "awake", true)'
            ],
            "priority": 1,
        }
    }

def fresh_timeline_root(name: str) -> Path:
    root = SCRATCH_ROOT / name
    timeline_path = root / "zon/timeline.jsonl"

    if timeline_path.exists():
        timeline_path.unlink()

    return root

def timeline_info(root: Path) -> dict[str, Any]:
    timeline_path = root / "zon/timeline.jsonl"

    lines: list[str] = []
    if timeline_path.exists():
        lines = timeline_path.read_text(encoding="utf-8").splitlines()

    return {
        "timeline_path": str(timeline_path),
        "timeline_exists": timeline_path.exists(),
        "line_count": len(lines),
        "lines": lines,
    }

def new_integration(
    module: Any,
    name: str,
    enable_timeline_write: bool = False,
) -> tuple[Any, Path]:
    timeline_root = fresh_timeline_root(name)

    integration = module.APRuntimeIntegration(
        project_root=str(REPO_ROOT),
        scenes_dir=str(SCRATCH_ROOT / "missing_scenes"),
        enable_timeline_write=enable_timeline_write,
        timeline_root=str(timeline_root),
    )

    integration.initialize(
        initial_state={
            "flags": {},
            "stats": {},
            "locations": {},
            "inventory": {},
            "entropy": {},
            "time_dilation": {},
        },
        rules=build_rules(),
    )

    return integration, timeline_root

def gate_engain_root_resolves_repo(module: Any) -> GateResult:
    actual = Path(module.ENGAIN_ROOT).resolve()
    expected = REPO_ROOT.resolve()

    passed = actual == expected

    return GateResult(
        gate_name="GATE_ENGAIN_ROOT_RESOLVES_REPO",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="AP runtime ENGAIN_ROOT resolves to repo root." if passed else "AP runtime ENGAIN_ROOT does not resolve to repo root.",
        details={
            "actual": str(actual),
            "expected": str(expected),
        },
    )

def gate_simulate_tick_no_timeline_write(module: Any) -> GateResult:
    integration, timeline_root = new_integration(
        module,
        "simulate_tick_no_write",
        enable_timeline_write=False,
    )

    result = integration.handle_message(
        {
            "type": "ap_simulate_tick",
            "context": {
                "hero": "hero",
            },
        }
    )

    info = timeline_info(timeline_root)

    passed = (
        result.get("type") == "ap_simulate_result"
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_SIMULATE_TICK_NO_TIMELINE_WRITE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="ap_simulate_tick returns simulation result and does not write timeline." if passed else "ap_simulate_tick did not behave as a non-writing simulation.",
        details={
            "result": result,
            "timeline": info,
        },
    )

def gate_execute_requires_intent(module: Any) -> GateResult:
    integration, timeline_root = new_integration(
        module,
        "execute_requires_intent",
        enable_timeline_write=False,
    )

    result = integration.handle_message(
        {
            "type": "ap_execute_tick",
            "context": {
                "hero": "hero",
            },
        }
    )

    info = timeline_info(timeline_root)

    passed = (
        result.get("error") == "execution_intent_required"
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_EXECUTE_REQUIRES_INTENT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="ap_execute_tick without allow_execute is rejected and writes no timeline." if passed else "ap_execute_tick executed without explicit intent.",
        details={
            "result": result,
            "timeline": info,
        },
    )

def gate_execute_without_timeline_write(module: Any) -> GateResult:
    integration, timeline_root = new_integration(
        module,
        "execute_without_timeline_write",
        enable_timeline_write=False,
    )

    result = integration.handle_message(
        {
            "type": "ap_execute_tick",
            "allow_execute": True,
            "context": {
                "hero": "hero",
            },
        }
    )

    info = timeline_info(timeline_root)

    passed = (
        result.get("type") == "ap_tick_execution"
        and result.get("applied") == ["wake_hero"]
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_EXECUTE_WITHOUT_TIMELINE_WRITE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="ap_execute_tick can execute with explicit intent while timeline write remains disabled." if passed else "ap_execute_tick without timeline write did not behave safely.",
        details={
            "result": result,
            "timeline": info,
            "engine_enable_timeline_write_after_call": getattr(integration.engine, "enable_timeline_write", None),
        },
    )

def gate_timeline_write_request_rejected_when_runtime_disabled(module: Any) -> GateResult:
    integration, timeline_root = new_integration(
        module,
        "timeline_request_runtime_disabled",
        enable_timeline_write=False,
    )

    result = integration.handle_message(
        {
            "type": "ap_execute_tick",
            "allow_execute": True,
            "enable_timeline_write": True,
            "context": {
                "hero": "hero",
            },
        }
    )

    info = timeline_info(timeline_root)

    passed = (
        result.get("error") == "timeline_write_not_allowed"
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_TIMELINE_WRITE_REQUEST_REJECTED_WHEN_RUNTIME_DISABLED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Timeline write request is rejected unless runtime was initialized with timeline writes enabled." if passed else "Timeline write was not properly rejected when runtime disabled.",
        details={
            "result": result,
            "timeline": info,
        },
    )

def gate_timeline_write_requires_both_permissions(module: Any) -> GateResult:
    integration, timeline_root = new_integration(
        module,
        "timeline_requires_both_permissions",
        enable_timeline_write=True,
    )

    result_without_message_permission = integration.handle_message(
        {
            "type": "ap_execute_tick",
            "allow_execute": True,
            "context": {
                "hero": "hero",
            },
        }
    )

    info_after_no_message_permission = timeline_info(timeline_root)

    result_with_message_permission = integration.handle_message(
        {
            "type": "ap_execute_tick",
            "allow_execute": True,
            "enable_timeline_write": True,
            "context": {
                "hero": "hero",
            },
        }
    )

    info_after_message_permission = timeline_info(timeline_root)

    passed = (
        result_without_message_permission.get("type") == "ap_tick_execution"
        and info_after_no_message_permission["timeline_exists"] is False
        and result_with_message_permission.get("type") == "ap_tick_execution"
        and info_after_message_permission["timeline_exists"] is True
        and info_after_message_permission["line_count"] == 1
    )

    return GateResult(
        gate_name="GATE_TIMELINE_WRITE_REQUIRES_BOTH_PERMISSIONS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Timeline write occurs only when runtime and message both explicitly allow it." if passed else "Timeline write permission logic failed.",
        details={
            "result_without_message_permission": result_without_message_permission,
            "timeline_after_no_message_permission": info_after_no_message_permission,
            "result_with_message_permission": result_with_message_permission,
            "timeline_after_message_permission": info_after_message_permission,
            "engine_enable_timeline_write_after_calls": getattr(integration.engine, "enable_timeline_write", None),
        },
    )

def gate_history_read_requires_intent(module: Any) -> GateResult:
    integration, timeline_root = new_integration(
        module,
        "history_read_requires_intent",
        enable_timeline_write=True,
    )

    without_intent = integration.handle_message(
        {
            "type": "ap_execution_history",
        }
    )

    with_intent = integration.handle_message(
        {
            "type": "ap_execution_history",
            "allow_history_read": True,
            "limit": 5,
        }
    )

    passed = (
        without_intent.get("error") == "history_read_intent_required"
        and with_intent.get("type") == "ap_execution_history"
        and isinstance(with_intent.get("entries"), list)
    )

    return GateResult(
        gate_name="GATE_HISTORY_READ_REQUIRES_INTENT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="ap_execution_history requires explicit allow_history_read intent." if passed else "ap_execution_history intent gate failed.",
        details={
            "without_intent": without_intent,
            "with_intent": with_intent,
            "timeline": timeline_info(timeline_root),
        },
    )

def main() -> int:
    module = load_ap_runtime_module()

    results = [
        gate_engain_root_resolves_repo(module),
        gate_simulate_tick_no_timeline_write(module),
        gate_execute_requires_intent(module),
        gate_execute_without_timeline_write(module),
        gate_timeline_write_request_rejected_when_runtime_disabled(module),
        gate_timeline_write_requires_both_permissions(module),
        gate_history_read_requires_intent(module),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_RUNTIME_BEHAVIOR_PROBE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "ap_runtime_behavior_probe",
        "stack": "godotengain_runtime_bridge",
        "ap_runtime_path": str(AP_RUNTIME_PATH),
        "behavioral_proof": all_passed,
        "relay_readiness_gate_allowed_next": all_passed,
        "relay_creation_allowed": False,
        "note": "This gate proves runtime behavior. It does not create or authorize the relay. A separate gate_ap_runtime_relay_readiness.py must pass before engainos/relays/ap_runtime_relay.py is created.",
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED_BEHAVIOR_PROVEN" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "TRUE" if result.passed else "FALSE"
        print(f"[gate_ap_runtime_behavior_probe][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_runtime_behavior_probe][ALL_GATES] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_behavior_probe][BEHAVIORAL_PROOF] {'true' if all_passed else 'false'}")
    print("[gate_ap_runtime_behavior_probe][RELAY_CREATION_ALLOWED] false")
    print(f"[gate_ap_runtime_behavior_probe][REPORT] {REPORT_PATH}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
