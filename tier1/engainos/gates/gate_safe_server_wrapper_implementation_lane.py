#!/usr/bin/env python3
"""SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE gate.

Verifies the scaffold at engainos/server/safe_runtime_server_entrypoint.py.
This gate is proof-only: it imports the scaffold and inspects source, but it must
not start sim_runtime.py, launch_engine.py, ap_runtime.py, or open port 8080.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import ast
import importlib
import json
import os
import socket
import subprocess
import sys

GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SAFE_SERVER_WRAPPER_IMPLEMENTATION_BOARD"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = REPO_ROOT / "scratch/safe_server_wrapper_implementation_lane_report.json"
WRAPPER_PACKAGE = "tier1.engainos.server.safe_runtime_server_entrypoint"
WRAPPER_PATH = REPO_ROOT / "engainos/server/safe_runtime_server_entrypoint.py"
PACKAGE_INIT_PATH = REPO_ROOT / "engainos/server/__init__.py"
PORT_8080 = 8080

REQUIRED_ROUTES = {
    "/command",
    "/snapshot",
    "/scene/load",
    "/vault/link",
    "/vault/status",
    "/world/sync",
    "/world/load_mirror",
}

EXPECTED_ROUTE_CONTRACTS: dict[str, dict[str, Any]] = {
    "/command": {
        "status": "allowed_preflight_only",
        "requires_gateway": True,
        "requires_ap_relay": True,
        "requires_schema_validation": True,
        "mutation_surface": "entity/world/action dispatch; may include AP runtime messages",
        "direct_mutation_forbidden": True,
        "allowed_after": "RuntimeGateway accepts request and APRuntimeRelay validates/forwards AP messages without manufacturing authority flags.",
        "notes": "Read-only commands may be classified by RuntimeGateway, but wrapper must still schema-normalize before dispatch.",
    },
    "/snapshot": {
        "status": "allowed",
        "requires_gateway": False,
        "requires_ap_relay": False,
        "requires_schema_validation": True,
        "mutation_surface": "read-only snapshot export",
        "direct_mutation_forbidden": True,
        "allowed_after": "Read-only response schema is validated and route contains no state mutation side effects.",
        "notes": "May read runtime snapshot only; must not hydrate by mutating canonical state during response.",
    },
    "/scene/load": {
        "status": "blocked",
        "requires_gateway": True,
        "requires_ap_relay": True,
        "requires_schema_validation": True,
        "mutation_surface": "scene state activation/load",
        "direct_mutation_forbidden": True,
        "allowed_after": "EngAInOS gateway approves actor/reality/scene authority and AP relay accepts any AP/rule side effects.",
        "notes": "Must not call the scene manager's scene-load API directly from HTTP transport.",
    },
    "/vault/link": {
        "status": "blocked",
        "requires_gateway": True,
        "requires_ap_relay": True,
        "requires_schema_validation": True,
        "mutation_surface": "vault registry/link state and scene registry population",
        "direct_mutation_forbidden": True,
        "allowed_after": "Gateway validates authority and schema/path anchors; relay covers AP rule/timeline consequences if any.",
        "notes": "Must not call the vault linker's link API directly from HTTP transport.",
    },
    "/vault/status": {
        "status": "allowed",
        "requires_gateway": False,
        "requires_ap_relay": False,
        "requires_schema_validation": True,
        "mutation_surface": "read-only vault status export",
        "direct_mutation_forbidden": True,
        "allowed_after": "Read-only response schema is validated and no vault state is changed.",
        "notes": "Allowed as observation only; no implicit relink, scan, load, repair, or cache writes.",
    },
    "/world/sync": {
        "status": "blocked",
        "requires_gateway": True,
        "requires_ap_relay": True,
        "requires_schema_validation": True,
        "mutation_surface": "world build/sync/mirror/load side effects",
        "direct_mutation_forbidden": True,
        "allowed_after": "Gateway accepts explicit authority; AP relay accepts rule/timeline intent; paths are anchored and dry-run/write mode is explicit.",
        "notes": "Must not build, mirror, chmod, rsync, bulk-load scenes, or write cache directly from HTTP transport.",
    },
    "/world/load_mirror": {
        "status": "blocked",
        "requires_gateway": True,
        "requires_ap_relay": True,
        "requires_schema_validation": True,
        "mutation_surface": "world mirror scene ingestion/load",
        "direct_mutation_forbidden": True,
        "allowed_after": "Gateway accepts explicit authority and AP relay covers AP rule/timeline consequences before mirror load.",
        "notes": "Must not call the bulk scene-load API directly from HTTP transport.",
    },
}

MUTATING_ROUTES = {"/command", "/scene/load", "/vault/link", "/world/sync", "/world/load_mirror"}
READ_ONLY_ROUTES = {"/snapshot", "/vault/status"}

FORBIDDEN_SOURCE_FRAGMENTS = (
    "uvicorn.run(",
    "ThreadingHTTPServer(",
    "HTTPServer(",
    ".bind(",
    "serve_forever(",
    "APRuntimeIntegration(",
    "scene_manager.load_scene(",
    "vault_linker.link(",
    "bulk_load_scenes(",
)

FORBIDDEN_RUNTIME_PROCESSES = (
    "godotsim/godotsim_legacy/sim_runtime.py",
    "godotsim/sim_runtime.py",
    "godotengain/engainos/launch_engine.py",
    "godotengain/engainos/core/ap_runtime.py",
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


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_source(path: Path) -> ast.Module:
    return ast.parse(read_source(path), filename=str(path))


def has_main_block(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.If):
            test = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
            if "__name__" in test and "__main__" in test:
                return True
    return False


def port_open(host: str = "127.0.0.1", port: int = PORT_8080) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def running_forbidden_processes() -> list[dict[str, str]]:
    proc_root = Path("/proc")
    hits: list[dict[str, str]] = []
    if not proc_root.exists():
        return hits
    for pid_dir in proc_root.iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            raw = (pid_dir / "cmdline").read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        cmdline = raw.replace(b"\x00", b" ").decode("utf-8", errors="replace")
        for token in FORBIDDEN_RUNTIME_PROCESSES:
            if token in cmdline:
                hits.append({"pid": pid_dir.name, "token": token, "cmdline": cmdline})
                break
    return hits


def route_contract_dicts_from_module(module: Any) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for contract in getattr(module, "ROUTE_CONTRACTS", ()):
        if hasattr(contract, "to_dict"):
            data = contract.to_dict()
        elif isinstance(contract, dict):
            data = dict(contract)
        else:
            data = {key: getattr(contract, key) for key in EXPECTED_ROUTE_CONTRACTS["/command"].keys() | {"route"} if hasattr(contract, key)}
        route = data.get("route")
        if isinstance(route, str):
            contracts[route] = data
    return contracts


def gate_files_created_and_parse() -> GateResult:
    missing = [str(path) for path in (PACKAGE_INIT_PATH, WRAPPER_PATH) if not path.exists()]
    parse_errors: dict[str, str] = {}
    for path in (PACKAGE_INIT_PATH, WRAPPER_PATH):
        if path.exists():
            try:
                parse_source(path)
            except SyntaxError as exc:
                parse_errors[str(path)] = str(exc)
    passed = not missing and not parse_errors
    return GateResult(
        "GATE_SAFE_SERVER_WRAPPER_FILES_CREATED_AND_PARSE",
        passed,
        "engainos/server package and safe_runtime_server_entrypoint.py exist and parse." if passed else "Wrapper package files are missing or invalid.",
        {"missing": missing, "parse_errors": parse_errors},
    )


def gate_wrapper_imports_without_side_effects() -> GateResult:
    before = port_open()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib, json; "
                f"m=importlib.import_module({WRAPPER_PACKAGE!r}); "
                "p=m.build_safe_runtime_server_preflight(include_route_contracts=False); "
                "print(json.dumps({'ok': True, 'port_allowed': p['PORT_8080_ALLOWED'], 'lane': p['SERVER_RUNTIME_LANE']}, sort_keys=True))"
            ),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
    )
    after = port_open()
    passed = proc.returncode == 0 and not before and not after and '"ok": true' in proc.stdout and '"port_allowed": false' in proc.stdout and '"lane": "BLOCKED"' in proc.stdout
    return GateResult(
        "GATE_SAFE_WRAPPER_IMPORTS_WITHOUT_SIDE_EFFECTS",
        passed,
        "Wrapper imports and preflight runs without opening port 8080 or starting runtime surfaces." if passed else "Wrapper import/preflight caused an error or side effect.",
        {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "port_8080_before_import": before,
            "port_8080_after_import": after,
        },
    )


def gate_no_auto_run_and_no_forbidden_calls() -> GateResult:
    source = read_source(WRAPPER_PATH)
    tree = ast.parse(source, filename=str(WRAPPER_PATH))
    forbidden_fragments = [fragment for fragment in FORBIDDEN_SOURCE_FRAGMENTS if fragment in source]
    main_block = has_main_block(tree)
    forbidden_import_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"socket", "uvicorn", "http.server"}:
                    forbidden_import_names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in {"socket", "uvicorn", "http.server"}:
                forbidden_import_names.append(module)
    passed = not forbidden_fragments and not main_block and not forbidden_import_names
    return GateResult(
        "GATE_NO_AUTO_RUN_SOCKET_SERVER_OR_DIRECT_MUTATION_CALLS",
        passed,
        "Wrapper has no __main__ auto-run, socket/server startup calls, or direct mutation calls." if passed else "Wrapper contains forbidden startup or mutation surface.",
        {
            "has_main_block": main_block,
            "forbidden_source_fragments": forbidden_fragments,
            "forbidden_import_names": forbidden_import_names,
        },
    )


def gate_route_contract_matches_blueprint() -> GateResult:
    module = importlib.import_module(WRAPPER_PACKAGE)
    actual = route_contract_dicts_from_module(module)
    missing = sorted(REQUIRED_ROUTES - set(actual))
    extra = sorted(set(actual) - REQUIRED_ROUTES)
    mismatches: dict[str, dict[str, Any]] = {}
    for route, expected in EXPECTED_ROUTE_CONTRACTS.items():
        if route not in actual:
            continue
        route_actual = dict(actual[route])
        route_actual.pop("route", None)
        if route_actual != expected:
            mismatches[route] = {"expected": expected, "actual": route_actual}
    passed = not missing and not extra and not mismatches
    return GateResult(
        "GATE_ROUTE_CONTRACT_MATCHES_BLUEPRINT",
        passed,
        "Wrapper route contract matches the approved safe-server blueprint." if passed else "Wrapper route contract diverges from blueprint.",
        {"missing_routes": missing, "extra_routes": extra, "mismatches": mismatches, "actual_routes": sorted(actual)},
    )


def gate_preflight_function_contract() -> GateResult:
    module = importlib.import_module(WRAPPER_PACKAGE)
    fn = getattr(module, "build_safe_runtime_server_preflight", None)
    preflight = fn() if callable(fn) else None
    errors: list[str] = []
    if not callable(fn):
        errors.append("build_safe_runtime_server_preflight_missing")
    if not isinstance(preflight, dict):
        errors.append("preflight_result_not_dict")
    else:
        expected_pairs = {
            "SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE": True,
            "SAFE_SERVER_WRAPPER_SCAFFOLD_ONLY": True,
            "SAFE_SERVER_ENTRYPOINT_IDENTIFIED": False,
            "SERVER_RUNTIME_LANE": "BLOCKED",
            "PORT_8080_ALLOWED": False,
            "import_side_effects_expected": False,
            "route_contracts_valid": True,
        }
        for key, expected in expected_pairs.items():
            if preflight.get(key) != expected:
                errors.append(f"{key}_expected_{expected!r}_got_{preflight.get(key)!r}")
        if preflight.get("route_contract_count") != len(REQUIRED_ROUTES):
            errors.append("route_contract_count_mismatch")
    passed = not errors
    return GateResult(
        "GATE_PREFLIGHT_FUNCTION_CONTRACT",
        passed,
        "Preflight function returns the required blocked/scaffold contract shape." if passed else "Preflight function contract is incomplete.",
        {"errors": errors, "preflight": preflight},
    )


def gate_mutating_and_readonly_route_policy() -> GateResult:
    module = importlib.import_module(WRAPPER_PACKAGE)
    contracts = route_contract_dicts_from_module(module)
    errors: dict[str, list[str]] = {}
    for route in MUTATING_ROUTES:
        contract = contracts.get(route, {})
        route_errors: list[str] = []
        if contract.get("status") == "allowed":
            route_errors.append("mutating_route_must_not_be_live_allowed")
        if contract.get("requires_gateway") is not True:
            route_errors.append("missing_gateway_requirement")
        if contract.get("requires_ap_relay") is not True:
            route_errors.append("missing_ap_relay_requirement")
        if contract.get("requires_schema_validation") is not True:
            route_errors.append("missing_schema_validation")
        if contract.get("direct_mutation_forbidden") is not True:
            route_errors.append("direct_mutation_not_forbidden")
        if route_errors:
            errors[route] = route_errors
    for route in READ_ONLY_ROUTES:
        contract = contracts.get(route, {})
        route_errors = []
        if contract.get("status") != "allowed":
            route_errors.append("read_only_route_must_be_allowed")
        if contract.get("requires_gateway") is not False:
            route_errors.append("read_only_route_must_not_require_gateway")
        if contract.get("requires_ap_relay") is not False:
            route_errors.append("read_only_route_must_not_require_ap_relay")
        if contract.get("requires_schema_validation") is not True:
            route_errors.append("missing_schema_validation")
        if contract.get("direct_mutation_forbidden") is not True:
            route_errors.append("direct_mutation_not_forbidden")
        if route_errors:
            errors[route] = route_errors
    passed = not errors
    return GateResult(
        "GATE_MUTATING_AND_READONLY_ROUTE_POLICY",
        passed,
        "Mutating routes require gateway/AP relay mediation; read-only routes are allowed only as no-mutation observation." if passed else "Route policy is unsafe.",
        {"route_errors": errors},
    )


def gate_port_8080_closed() -> GateResult:
    port = port_open()
    forbidden = running_forbidden_processes()
    passed = not port and not forbidden
    return GateResult(
        "GATE_PORT_8080_REMAINS_CLOSED",
        passed,
        "Port 8080 is closed and forbidden runtime entrypoint processes are absent." if passed else "Port 8080 or a forbidden runtime entrypoint is active.",
        {"port_8080_open": port, "forbidden_processes": forbidden},
    )


def main() -> int:
    # Ensure imports resolve from repo root when this gate is run as a script.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    results = [
        gate_files_created_and_parse(),
        gate_wrapper_imports_without_side_effects(),
        gate_no_auto_run_and_no_forbidden_calls(),
        gate_route_contract_matches_blueprint(),
        gate_preflight_function_contract(),
        gate_mutating_and_readonly_route_policy(),
        gate_port_8080_closed(),
    ]
    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE",
        "SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE": all_passed,
        "SAFE_RUNTIME_SERVER_ENTRYPOINT_IMPORTS_WITHOUT_SIDE_EFFECTS": results[1].passed,
        "ROUTE_CONTRACT_MATCHES_BLUEPRINT": results[3].passed,
        "NO_SOCKET_BIND": results[2].passed and results[6].details.get("port_8080_open") is False,
        "NO_UVICORN_RUN": "uvicorn.run(" not in read_source(WRAPPER_PATH),
        "NO_DIRECT_MUTATION_CALLS": results[2].passed,
        "SERVER_RUNTIME_LANE": "BLOCKED",
        "PORT_8080_ALLOWED": False,
        "SAFE_SERVER_ENTRYPOINT_IDENTIFIED": False,
        "gates": [asdict(result) | {"status": result.status} for result in results],
        "acceptance": "ACCEPTED_SCAFFOLD_TRUE" if all_passed else "REJECTED_SCAFFOLD_NOT_PROVEN",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        print(f"[gate_safe_server_wrapper_implementation_lane][{result.gate_name}] {result.status}: {result.message}")
    print(f"[gate_safe_server_wrapper_implementation_lane][SAFE_SERVER_WRAPPER_IMPLEMENTATION_LANE] {'TRUE' if all_passed else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_implementation_lane][SAFE_RUNTIME_SERVER_ENTRYPOINT_IMPORTS_WITHOUT_SIDE_EFFECTS] {'TRUE' if results[1].passed else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_implementation_lane][ROUTE_CONTRACT_MATCHES_BLUEPRINT] {'TRUE' if results[3].passed else 'FALSE'}")
    print("[gate_safe_server_wrapper_implementation_lane][SERVER_RUNTIME_LANE] BLOCKED")
    print("[gate_safe_server_wrapper_implementation_lane][PORT_8080_ALLOWED] FALSE")
    print(f"[gate_safe_server_wrapper_implementation_lane][REPORT] {REPORT_PATH}")
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
