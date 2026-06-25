#!/usr/bin/env python3
"""SAFE_SERVER_WRAPPER_BEHAVIOR_LANE gate.

Proof-only gate for engainos/server/safe_runtime_server_entrypoint.py behavior.
It imports the scaffold and inspects pure data contracts without starting any
runtime server, opening port 8080, running launch_engine.py, executing
ap_runtime.py, or bypassing the AP runtime relay boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import ast
import importlib
import json
import socket
import sys

GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SAFE_SERVER_WRAPPER_BEHAVIOR_BOARD"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = REPO_ROOT / "scratch/safe_server_wrapper_behavior_lane_report.json"
WRAPPER_PACKAGE = "tier1.engainos.server.safe_runtime_server_entrypoint"
WRAPPER_PATH = REPO_ROOT / "engainos/server/safe_runtime_server_entrypoint.py"
PORT_8080 = 8080

EXPECTED_ROUTES = {
    "/command",
    "/snapshot",
    "/scene/load",
    "/vault/link",
    "/vault/status",
    "/world/sync",
    "/world/load_mirror",
}

EXPECTED_PREFLIGHT_PAIRS = {
    "SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE": True,
    "SAFE_SERVER_WRAPPER_SCAFFOLD_ONLY": True,
    "SAFE_SERVER_ENTRYPOINT_IDENTIFIED": False,
    "SERVER_RUNTIME_LANE": "BLOCKED",
    "PORT_8080_ALLOWED": False,
    "route_contract_count": 7,
    "route_contracts_valid": True,
}

ALLOWED_READ_ONLY_ROUTES = {
    "/snapshot": {
        "status": "allowed",
        "requires_gateway": False,
        "requires_ap_relay": False,
        "requires_schema_validation": True,
        "direct_mutation_forbidden": True,
    },
    "/vault/status": {
        "status": "allowed",
        "requires_gateway": False,
        "requires_ap_relay": False,
        "requires_schema_validation": True,
        "direct_mutation_forbidden": True,
    },
}

PREFLIGHT_ONLY_ROUTES = {
    "/command": {
        "status": "allowed_preflight_only",
        "requires_gateway": True,
        "requires_ap_relay": True,
        "requires_schema_validation": True,
        "direct_mutation_forbidden": True,
    },
}

BLOCKED_MUTATING_ROUTES = {
    "/scene/load": "blocked",
    "/vault/link": "blocked",
    "/world/sync": "blocked",
    "/world/load_mirror": "blocked",
}

BLOCKED_MUTATING_REQUIRED_FLAGS = {
    "requires_gateway": True,
    "requires_ap_relay": True,
    "requires_schema_validation": True,
    "direct_mutation_forbidden": True,
}

FORBIDDEN_SOURCE_FRAGMENTS = (
    "bind_socket",
    "uvicorn.run",
    "HTTPServer",
    "RuntimeHTTPServer",
    "scene_manager.load_scene",
    "vault_linker.link",
    "bulk_load_scenes",
    "execute_tick",
    "timeline.write",
)


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "TRUE" if self.passed else "FALSE"


def port_open(host: str = "127.0.0.1", port: int = PORT_8080) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def wrapper_module() -> Any:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    return importlib.import_module(WRAPPER_PACKAGE)


def route_contracts_by_route(module: Any) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for contract in getattr(module, "ROUTE_CONTRACTS", ()):
        if hasattr(contract, "to_dict"):
            data = contract.to_dict()
        elif isinstance(contract, dict):
            data = dict(contract)
        else:
            data = dict(vars(contract))
        route = data.get("route")
        if isinstance(route, str):
            contracts[route] = data
    return contracts


def source_has_open_write_call(source: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    tree = ast.parse(source, filename=str(WRAPPER_PATH))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "open":
            continue

        modes: list[str] = []
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
            modes.append(node.args[1].value)
        for keyword in node.keywords:
            if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                modes.append(keyword.value.value)
        if any("w" in mode or "a" in mode or "+" in mode for mode in modes):
            hits.append({"lineno": getattr(node, "lineno", None), "modes": modes})
    return hits


def gate_preflight_packet_shape() -> GateResult:
    module = wrapper_module()
    fn = getattr(module, "build_safe_runtime_server_preflight", None)
    preflight = fn() if callable(fn) else None
    errors: list[str] = []
    if not callable(fn):
        errors.append("build_safe_runtime_server_preflight_missing")
    if not isinstance(preflight, dict):
        errors.append("preflight_result_not_dict")
    else:
        for key, expected in EXPECTED_PREFLIGHT_PAIRS.items():
            if preflight.get(key) != expected:
                errors.append(f"{key}_expected_{expected!r}_got_{preflight.get(key)!r}")
    passed = not errors
    return GateResult(
        "GATE_PREFLIGHT_PACKET_SHAPE_PROVEN",
        passed,
        "build_safe_runtime_server_preflight returns dict with required blocked/scaffold fields." if passed else "Preflight packet shape failed required fields.",
        {"errors": errors, "preflight": preflight},
    )


def gate_route_set_exact() -> GateResult:
    contracts = route_contracts_by_route(wrapper_module())
    actual_routes = set(contracts)
    missing = sorted(EXPECTED_ROUTES - actual_routes)
    extra = sorted(actual_routes - EXPECTED_ROUTES)
    passed = not missing and not extra and len(contracts) == 7
    return GateResult(
        "GATE_ROUTE_SET_EXACT",
        passed,
        "ROUTE_CONTRACTS contains exactly the seven approved safe-wrapper routes." if passed else "ROUTE_CONTRACTS route set differs from approved behavior lane list.",
        {"actual_routes": sorted(actual_routes), "missing_routes": missing, "extra_routes": extra, "route_contract_count": len(contracts)},
    )


def gate_allowed_and_preflight_route_behavior() -> GateResult:
    contracts = route_contracts_by_route(wrapper_module())
    errors: dict[str, list[str]] = {}
    expectations = ALLOWED_READ_ONLY_ROUTES | PREFLIGHT_ONLY_ROUTES
    for route, expected_fields in expectations.items():
        contract = contracts.get(route, {})
        route_errors: list[str] = []
        for field_name, expected in expected_fields.items():
            if contract.get(field_name) is not expected and contract.get(field_name) != expected:
                route_errors.append(f"{field_name}_expected_{expected!r}_got_{contract.get(field_name)!r}")
        if route_errors:
            errors[route] = route_errors
    passed = not errors
    return GateResult(
        "GATE_ALLOWED_READONLY_AND_PREFLIGHT_ROUTE_BEHAVIOR",
        passed,
        "Read-only routes remain read-only allowed and /command remains preflight-only." if passed else "Allowed/preflight route behavior diverges.",
        {"route_errors": errors},
    )


def gate_blocked_route_behavior() -> GateResult:
    contracts = route_contracts_by_route(wrapper_module())
    errors: dict[str, list[str]] = {}
    for route, expected_status in BLOCKED_MUTATING_ROUTES.items():
        contract = contracts.get(route, {})
        route_errors: list[str] = []
        if contract.get("status") != expected_status:
            route_errors.append(f"status_expected_{expected_status!r}_got_{contract.get('status')!r}")
        for field_name, expected in BLOCKED_MUTATING_REQUIRED_FLAGS.items():
            if contract.get(field_name) is not expected:
                route_errors.append(f"{field_name}_expected_{expected!r}_got_{contract.get(field_name)!r}")
        if route_errors:
            errors[route] = route_errors
    passed = not errors
    return GateResult(
        "GATE_BLOCKED_ROUTE_BEHAVIOR",
        passed,
        "Blocked mutating routes remain blocked and require gateway/AP relay/schema validation/no direct mutation." if passed else "Blocked mutating route behavior diverges.",
        {"route_errors": errors},
    )


def gate_source_contains_no_forbidden_direct_effects() -> GateResult:
    source = WRAPPER_PATH.read_text(encoding="utf-8")
    forbidden_fragments = [fragment for fragment in FORBIDDEN_SOURCE_FRAGMENTS if fragment in source]
    open_write_calls = source_has_open_write_call(source)
    passed = not forbidden_fragments and not open_write_calls
    return GateResult(
        "GATE_SOURCE_CONTAINS_NO_FORBIDDEN_DIRECT_EFFECTS",
        passed,
        "Wrapper source contains none of the forbidden direct server/runtime/mutation effects." if passed else "Wrapper source contains forbidden direct effects.",
        {"forbidden_fragments": forbidden_fragments, "open_write_calls": open_write_calls},
    )


def gate_port_8080_still_closed() -> GateResult:
    open_now = port_open()
    return GateResult(
        "GATE_PORT_8080_STILL_CLOSED",
        not open_now,
        "Port 8080 remains closed after behavior probing." if not open_now else "Port 8080 is open.",
        {"port_8080_open": open_now},
    )


def main() -> int:
    results = [
        gate_preflight_packet_shape(),
        gate_route_set_exact(),
        gate_allowed_and_preflight_route_behavior(),
        gate_blocked_route_behavior(),
        gate_source_contains_no_forbidden_direct_effects(),
        gate_port_8080_still_closed(),
    ]
    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "SAFE_SERVER_WRAPPER_BEHAVIOR_LANE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "SAFE_SERVER_WRAPPER_BEHAVIOR_LANE",
        "SAFE_SERVER_WRAPPER_BEHAVIOR_LANE": all_passed,
        "ROUTE_CONTRACT_BEHAVIOR_PROVEN": results[1].passed and results[2].passed and results[3].passed,
        "PREFLIGHT_PACKET_SHAPE_PROVEN": results[0].passed,
        "BLOCKED_ROUTES_REMAIN_BLOCKED": results[3].passed,
        "READ_ONLY_ROUTES_REMAIN_READ_ONLY": results[2].passed,
        "MUTATING_ROUTES_REQUIRE_GATEWAY_AND_AP_RELAY": results[3].passed,
        "SERVER_RUNTIME_LANE": "BLOCKED",
        "PORT_8080_ALLOWED": False,
        "port_8080_open": results[5].details.get("port_8080_open"),
        "gates": [asdict(result) | {"status": result.status} for result in results],
        "acceptance": "ACCEPTED_BEHAVIOR_TRUE" if all_passed else "REJECTED_BEHAVIOR_NOT_PROVEN",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        print(f"[gate_safe_server_wrapper_behavior_lane][{result.gate_name}] {result.status}: {result.message}")
    print(f"[gate_safe_server_wrapper_behavior_lane][SAFE_SERVER_WRAPPER_BEHAVIOR_LANE] {'TRUE' if all_passed else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_behavior_lane][ROUTE_CONTRACT_BEHAVIOR_PROVEN] {'TRUE' if report['ROUTE_CONTRACT_BEHAVIOR_PROVEN'] else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_behavior_lane][PREFLIGHT_PACKET_SHAPE_PROVEN] {'TRUE' if report['PREFLIGHT_PACKET_SHAPE_PROVEN'] else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_behavior_lane][BLOCKED_ROUTES_REMAIN_BLOCKED] {'TRUE' if report['BLOCKED_ROUTES_REMAIN_BLOCKED'] else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_behavior_lane][READ_ONLY_ROUTES_REMAIN_READ_ONLY] {'TRUE' if report['READ_ONLY_ROUTES_REMAIN_READ_ONLY'] else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_behavior_lane][MUTATING_ROUTES_REQUIRE_GATEWAY_AND_AP_RELAY] {'TRUE' if report['MUTATING_ROUTES_REQUIRE_GATEWAY_AND_AP_RELAY'] else 'FALSE'}")
    print("[gate_safe_server_wrapper_behavior_lane][SERVER_RUNTIME_LANE] BLOCKED")
    print("[gate_safe_server_wrapper_behavior_lane][PORT_8080_ALLOWED] FALSE")
    print(f"[gate_safe_server_wrapper_behavior_lane][port_8080_open] {str(report['port_8080_open']).lower()}")
    print(f"[gate_safe_server_wrapper_behavior_lane][REPORT] {REPORT_PATH}")
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
