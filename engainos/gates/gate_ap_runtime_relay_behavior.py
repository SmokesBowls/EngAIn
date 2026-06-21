from __future__ import annotations
GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_AP_MIGRATION_AND_CONTRACT_BOARD"


from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import json
import sys
from typing import Any

REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RELAY_PATH = REPO_ROOT / "engainos/relays/ap_runtime_relay.py"
READINESS_REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_relay_readiness_report.json"
REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_relay_behavior_report.json"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

class FakeRuntimeIntegration:
    def __init__(self):
        self.messages = []
        self.initialized = False

    def initialize(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.initialized = True
        return {
            "type": "fake_initialized",
            "args_count": len(args),
            "kwargs_keys": sorted(kwargs.keys()),
        }

    def handle_message(self, msg: dict[str, Any]) -> dict[str, Any]:
        self.messages.append(dict(msg))
        return {
            "type": "fake_runtime_response",
            "received": dict(msg),
        }

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

def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def collect_imports(path: Path) -> list[str]:
    tree = ast.parse(read_source(path))
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        if isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return sorted(set(imports))

def gate_readiness_report_accepted() -> GateResult:
    report = read_json(READINESS_REPORT_PATH)

    passed = (
        report.get("acceptance") == "ACCEPTED_RELAY_READY"
        and report.get("relay_creation_allowed") is True
        and report.get("relay_file_allowed_next") == "engainos/relays/ap_runtime_relay.py"
    )

    return GateResult(
        gate_name="GATE_READINESS_REPORT_ACCEPTED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Relay readiness report authorizes ap_runtime_relay.py creation." if passed else "Relay readiness report does not authorize relay creation.",
        details={
            "report_path": str(READINESS_REPORT_PATH),
            "acceptance": report.get("acceptance"),
            "relay_creation_allowed": report.get("relay_creation_allowed"),
            "relay_file_allowed_next": report.get("relay_file_allowed_next"),
            "read_error": report.get("__read_error__"),
        },
    )

def gate_relay_file_exists() -> GateResult:
    passed = RELAY_PATH.exists()

    return GateResult(
        gate_name="GATE_RELAY_FILE_EXISTS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="AP runtime relay file exists." if passed else "AP runtime relay file is missing.",
        details={
            "relay_path": str(RELAY_PATH),
        },
    )

def gate_no_forbidden_runtime_bypass_source() -> GateResult:
    source = read_source(RELAY_PATH)

    forbidden_fragments = [
        "ZWAPEngine(",
        "StateProvider(",
        ".execute_tick(",
        ".simulate_tick(",
        ".read_execution_history(",
        ".set_flag(",
        ".set_stat(",
        ".set_location(",
        ".add_inventory(",
        "timeline.jsonl",
    ]

    forbidden_hits = [
        item for item in forbidden_fragments
        if item in source
    ]

    passed = not forbidden_hits

    return GateResult(
        gate_name="GATE_NO_FORBIDDEN_RUNTIME_BYPASS_SOURCE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Relay source does not bypass APRuntimeIntegration." if passed else "Relay source contains forbidden direct runtime bypass calls.",
        details={
            "forbidden_hits": forbidden_hits,
        },
    )

def gate_no_manufactured_consent_source() -> GateResult:
    source = read_source(RELAY_PATH)

    forbidden_fragments = [
        'allow_execute"] = True',
        "allow_execute'] = True",
        'enable_timeline_write"] = True',
        "enable_timeline_write'] = True",
        'allow_history_read"] = True',
        "allow_history_read'] = True",
        'setdefault("allow_execute", True)',
        "setdefault('allow_execute', True)",
        'setdefault("enable_timeline_write", True)',
        "setdefault('enable_timeline_write', True)",
        'setdefault("allow_history_read", True)',
        "setdefault('allow_history_read', True)",
    ]

    forbidden_hits = [
        item for item in forbidden_fragments
        if item in source
    ]

    passed = not forbidden_hits

    return GateResult(
        gate_name="GATE_NO_MANUFACTURED_CONSENT_SOURCE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Relay source does not manufacture caller consent." if passed else "Relay source manufactures execution, timeline, or history consent.",
        details={
            "forbidden_hits": forbidden_hits,
        },
    )

def gate_import_boundary() -> GateResult:
    imports = collect_imports(RELAY_PATH)

    forbidden_roots = {
        "engainos.core.ap_zw_engine",
        "engainos.core.ap_engine",
        "godot",
        "bpy",
        "uvicorn",
        "fastapi",
        "requests",
        "httpx",
        "socket",
        "subprocess",
    }

    forbidden = [
        item for item in imports
        if item in forbidden_roots or item.split(".")[0] in forbidden_roots
    ]

    passed = not forbidden

    return GateResult(
        gate_name="GATE_IMPORT_BOUNDARY",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Relay imports do not pull core engine or server/runtime modules directly." if passed else "Relay imports forbidden runtime/core/server modules.",
        details={
            "imports": imports,
            "forbidden": forbidden,
        },
    )

def gate_rejects_unaccepted_context() -> GateResult:
    from engainos.relays.ap_runtime_relay import APRuntimeRelay

    fake_runtime = FakeRuntimeIntegration()
    relay = APRuntimeRelay(runtime_integration=fake_runtime)

    result = relay.forward(
        {
            "type": "ap_simulate_tick",
            "context": {
                "hero": "hero",
            },
        }
    )

    passed = (
        result.get("error") == "engainos_acceptance_required"
        and fake_runtime.messages == []
    )

    return GateResult(
        gate_name="GATE_REJECTS_UNACCEPTED_CONTEXT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Relay rejects AP messages without EngAInOS acceptance marker." if passed else "Relay forwarded message without acceptance marker.",
        details={
            "result": result,
            "forwarded_messages": fake_runtime.messages,
        },
    )

def gate_forwards_caller_message_without_consent_mutation() -> GateResult:
    from engainos.relays.ap_runtime_relay import APRuntimeRelay

    fake_runtime = FakeRuntimeIntegration()
    relay = APRuntimeRelay(runtime_integration=fake_runtime)

    original = {
        "type": "ap_execute_tick",
        "engainos_accepted": True,
        "context": {
            "hero": "hero",
        },
    }

    result = relay.forward(original)

    received = fake_runtime.messages[0] if fake_runtime.messages else {}

    consent_keys = [
        "allow_execute",
        "enable_timeline_write",
        "allow_history_read",
    ]

    manufactured = [
        key for key in consent_keys
        if key in received and key not in original
    ]

    passed = (
        result.get("type") == "fake_runtime_response"
        and received == original
        and not manufactured
    )

    return GateResult(
        gate_name="GATE_FORWARDS_CALLER_MESSAGE_WITHOUT_CONSENT_MUTATION",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Relay forwards caller-supplied message without manufacturing consent." if passed else "Relay changed message or manufactured consent.",
        details={
            "original": original,
            "received": received,
            "manufactured": manufactured,
            "result": result,
        },
    )

def gate_initialize_runtime_does_not_bypass() -> GateResult:
    from engainos.relays.ap_runtime_relay import APRuntimeRelay

    fake_runtime = FakeRuntimeIntegration()
    relay = APRuntimeRelay(runtime_integration=fake_runtime)

    result = relay.initialize_runtime(
        initial_state={"flags": {}},
        rules={},
    )

    passed = fake_runtime.initialized is True and result.get("type") == "fake_initialized"

    return GateResult(
        gate_name="GATE_INITIALIZE_RUNTIME_DOES_NOT_BYPASS",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="Relay initialization forwards to APRuntimeIntegration without direct engine construction." if passed else "Relay initialization did not forward safely.",
        details={
            "result": result,
            "fake_runtime_initialized": fake_runtime.initialized,
        },
    )

def main() -> int:
    results = [
        gate_readiness_report_accepted(),
        gate_relay_file_exists(),
        gate_import_boundary(),
        gate_no_forbidden_runtime_bypass_source(),
        gate_no_manufactured_consent_source(),
        gate_rejects_unaccepted_context(),
        gate_forwards_caller_message_without_consent_mutation(),
        gate_initialize_runtime_does_not_bypass(),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_RUNTIME_RELAY_BEHAVIOR_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "ap_runtime_relay_behavior",
        "stack": "engainos_relay_boundary",
        "relay_path": str(RELAY_PATH),
        "relay_behavior_proven": all_passed,
        "runtime_bridge_called_only_through_APRuntimeIntegration": all_passed,
        "relay_may_not_manufacture_consent": all_passed,
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED_RELAY_BEHAVIOR_PROVEN" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "TRUE" if result.passed else "FALSE"
        print(f"[gate_ap_runtime_relay_behavior][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_runtime_relay_behavior][ALL_GATES] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_relay_behavior][RELAY_BEHAVIOR_PROVEN] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_relay_behavior][REPORT] {REPORT_PATH}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
