from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RELAY_PATH = REPO_ROOT / "engainos/relays/ap_runtime_relay.py"
RELAY_BEHAVIOR_REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_relay_behavior_report.json"
REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_relay_real_integration_report.json"
SCRATCH_ROOT = REPO_ROOT / "scratch/ap_runtime_relay_real_integration"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "__read_error__": {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        }

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

def fresh_root(name: str) -> Path:
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

def make_relay(
    name: str,
    enable_timeline_write: bool = False,
) -> tuple[Any, Path]:
    from tier1.engainos.relays.ap_runtime_relay import build_ap_runtime_relay

    timeline_root = fresh_root(name)
    relay = build_ap_runtime_relay()

    relay.initialize_runtime(
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

    # Rebuild runtime with explicit timeline settings.
    # The relay forwards initialization to APRuntimeIntegration;
    # it still does not instantiate ZWAPEngine directly.
    relay.runtime_integration.enable_timeline_write = enable_timeline_write
    relay.runtime_integration.timeline_root = str(timeline_root)

    relay.initialize_runtime(
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

    return relay, timeline_root

def gate_prior_relay_behavior_report_accepted() -> GateResult:
    report = read_json(RELAY_BEHAVIOR_REPORT_PATH)

    passed = (
        report.get("acceptance") == "ACCEPTED_RELAY_BEHAVIOR_PROVEN"
        and report.get("relay_behavior_proven") is True
        and report.get("relay_may_not_manufacture_consent") is True
        and report.get("runtime_bridge_called_only_through_APRuntimeIntegration") is True
    )

    return GateResult(
        gate_name="GATE_PRIOR_RELAY_BEHAVIOR_REPORT_ACCEPTED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Prior relay behavior report is accepted." if passed else "Prior relay behavior report is missing or not accepted.",
        details={
            "report_path": str(RELAY_BEHAVIOR_REPORT_PATH),
            "acceptance": report.get("acceptance"),
            "relay_behavior_proven": report.get("relay_behavior_proven"),
            "relay_may_not_manufacture_consent": report.get("relay_may_not_manufacture_consent"),
            "runtime_bridge_called_only_through_APRuntimeIntegration": report.get("runtime_bridge_called_only_through_APRuntimeIntegration"),
            "read_error": report.get("__read_error__"),
        },
    )

def gate_real_simulate_through_relay_no_write() -> GateResult:
    relay, root = make_relay("real_simulate_no_write", enable_timeline_write=False)

    result = relay.forward(
        {
            "type": "ap_simulate_tick",
            "engainos_accepted": True,
            "context": {"hero": "hero"},
        }
    )

    info = timeline_info(root)

    passed = (
        result.get("type") == "ap_simulate_result"
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_REAL_SIMULATE_THROUGH_RELAY_NO_WRITE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Accepted simulate message reaches real runtime through relay and writes no timeline." if passed else "Real simulate-through-relay path failed.",
        details={
            "result": result,
            "timeline": info,
        },
    )

def gate_unaccepted_execute_rejected_before_runtime() -> GateResult:
    relay, root = make_relay("unaccepted_execute_rejected", enable_timeline_write=False)

    before_tick = getattr(relay.runtime_integration.engine, "_tick", None)

    result = relay.forward(
        {
            "type": "ap_execute_tick",
            "allow_execute": True,
            "context": {"hero": "hero"},
        }
    )

    after_tick = getattr(relay.runtime_integration.engine, "_tick", None)
    info = timeline_info(root)

    passed = (
        result.get("error") == "engainos_acceptance_required"
        and before_tick == after_tick
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_UNACCEPTED_EXECUTE_REJECTED_BEFORE_RUNTIME",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Unaccepted execute is rejected by relay before reaching runtime." if passed else "Unaccepted execute was not blocked before runtime.",
        details={
            "result": result,
            "before_tick": before_tick,
            "after_tick": after_tick,
            "timeline": info,
        },
    )

def gate_accepted_execute_without_allow_rejected_by_runtime() -> GateResult:
    relay, root = make_relay("accepted_execute_without_allow", enable_timeline_write=False)

    result = relay.forward(
        {
            "type": "ap_execute_tick",
            "engainos_accepted": True,
            "context": {"hero": "hero"},
        }
    )

    info = timeline_info(root)

    passed = (
        result.get("error") == "execution_intent_required"
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_ACCEPTED_EXECUTE_WITHOUT_ALLOW_REJECTED_BY_RUNTIME",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Accepted execute without allow_execute reaches real runtime and is rejected by runtime intent gate." if passed else "Runtime did not reject accepted execute without allow_execute.",
        details={
            "result": result,
            "timeline": info,
        },
    )

def gate_accepted_execute_allow_no_timeline() -> GateResult:
    relay, root = make_relay("accepted_execute_allow_no_timeline", enable_timeline_write=False)

    result = relay.forward(
        {
            "type": "ap_execute_tick",
            "engainos_accepted": True,
            "allow_execute": True,
            "context": {"hero": "hero"},
        }
    )

    info = timeline_info(root)

    passed = (
        result.get("type") == "ap_tick_execution"
        and result.get("applied") == ["wake_hero"]
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_ACCEPTED_EXECUTE_ALLOW_NO_TIMELINE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Accepted execute with allow_execute runs through real runtime without timeline write." if passed else "Accepted execute without timeline write failed.",
        details={
            "result": result,
            "timeline": info,
            "engine_enable_timeline_write_after_call": getattr(relay.runtime_integration.engine, "enable_timeline_write", None),
        },
    )

def gate_timeline_request_runtime_disabled_rejected() -> GateResult:
    relay, root = make_relay("timeline_request_runtime_disabled", enable_timeline_write=False)

    result = relay.forward(
        {
            "type": "ap_execute_tick",
            "engainos_accepted": True,
            "allow_execute": True,
            "enable_timeline_write": True,
            "context": {"hero": "hero"},
        }
    )

    info = timeline_info(root)

    passed = (
        result.get("error") == "timeline_write_not_allowed"
        and info["timeline_exists"] is False
    )

    return GateResult(
        gate_name="GATE_TIMELINE_REQUEST_RUNTIME_DISABLED_REJECTED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Real relay/runtime path rejects timeline write when runtime config is disabled." if passed else "Timeline write request was not rejected while runtime disabled.",
        details={
            "result": result,
            "timeline": info,
        },
    )

def gate_timeline_write_real_path_requires_both() -> GateResult:
    relay, root = make_relay("timeline_write_real_path_requires_both", enable_timeline_write=True)

    result_without_message_permission = relay.forward(
        {
            "type": "ap_execute_tick",
            "engainos_accepted": True,
            "allow_execute": True,
            "context": {"hero": "hero"},
        }
    )

    info_after_no_message_permission = timeline_info(root)

    # Use a fresh relay/runtime for the permission-positive path so the delta is not
    # weakened by a previous no-op state update.
    relay2, root2 = make_relay("timeline_write_real_path_positive", enable_timeline_write=True)

    result_with_message_permission = relay2.forward(
        {
            "type": "ap_execute_tick",
            "engainos_accepted": True,
            "allow_execute": True,
            "enable_timeline_write": True,
            "context": {"hero": "hero"},
        }
    )

    info_after_message_permission = timeline_info(root2)

    passed = (
        result_without_message_permission.get("type") == "ap_tick_execution"
        and info_after_no_message_permission["timeline_exists"] is False
        and result_with_message_permission.get("type") == "ap_tick_execution"
        and result_with_message_permission.get("delta") == {"flag.hero.awake": True}
        and info_after_message_permission["timeline_exists"] is True
        and info_after_message_permission["line_count"] == 1
    )

    return GateResult(
        gate_name="GATE_TIMELINE_WRITE_REAL_PATH_REQUIRES_BOTH",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Real relay/runtime path writes timeline only when runtime and caller both allow it." if passed else "Real timeline permission AND-gate failed.",
        details={
            "result_without_message_permission": result_without_message_permission,
            "timeline_after_no_message_permission": info_after_no_message_permission,
            "result_with_message_permission": result_with_message_permission,
            "timeline_after_message_permission": info_after_message_permission,
        },
    )

def gate_history_read_real_path_requires_intent() -> GateResult:
    relay, root = make_relay("history_read_real_path", enable_timeline_write=True)

    without_intent = relay.forward(
        {
            "type": "ap_execution_history",
            "engainos_accepted": True,
        }
    )

    with_intent = relay.forward(
        {
            "type": "ap_execution_history",
            "engainos_accepted": True,
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
        gate_name="GATE_HISTORY_READ_REAL_PATH_REQUIRES_INTENT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Real relay/runtime path requires allow_history_read for history access." if passed else "Real history-read intent gate failed.",
        details={
            "without_intent": without_intent,
            "with_intent": with_intent,
            "timeline": timeline_info(root),
        },
    )

def main() -> int:
    results = [
        gate_prior_relay_behavior_report_accepted(),
        gate_real_simulate_through_relay_no_write(),
        gate_unaccepted_execute_rejected_before_runtime(),
        gate_accepted_execute_without_allow_rejected_by_runtime(),
        gate_accepted_execute_allow_no_timeline(),
        gate_timeline_request_runtime_disabled_rejected(),
        gate_timeline_write_real_path_requires_both(),
        gate_history_read_real_path_requires_intent(),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_RUNTIME_RELAY_REAL_INTEGRATION_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "ap_runtime_relay_real_integration",
        "stack": "engainos_relay_boundary",
        "relay_path": str(RELAY_PATH),
        "relay_real_integration_proven": all_passed,
        "relay_calls_real_APRuntimeIntegration": all_passed,
        "relay_does_not_manufacture_consent_in_real_path": all_passed,
        "timeline_write_real_path_requires_both_permissions": all_passed,
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED_REAL_INTEGRATION_PROVEN" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "TRUE" if result.passed else "FALSE"
        print(f"[gate_ap_runtime_relay_real_integration][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_runtime_relay_real_integration][ALL_GATES] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_relay_real_integration][REAL_INTEGRATION_PROVEN] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_relay_real_integration][REPORT] {REPORT_PATH}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
