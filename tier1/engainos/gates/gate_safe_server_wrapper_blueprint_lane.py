#!/usr/bin/env python3
"""
SAFE_SERVER_WRAPPER_BLUEPRINT_LANE gate.

Purpose:
  Define the lawful EngAInOS server wrapper contract for future port-8080 use
  without implementing or launching a live server.

This gate is inspection/contract only. It must not import, execute, or start:
  - godotsim/godotsim_legacy/sim_runtime.py
  - godotengain/engainos/launch_engine.py
  - godotengain/engainos/core/ap_runtime.py

Contract doctrine:
  No HTTP route may directly mutate scene, vault, world, timeline, entity state,
  or rule state without EngAInOS gateway/relay acceptance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal
import ast
import json
import socket

GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SAFE_SERVER_WRAPPER_BLUEPRINT_BOARD"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = REPO_ROOT / "scratch/safe_server_wrapper_blueprint_lane_report.json"
PORT_8080 = 8080

SAFE_WRAPPER_BLUEPRINT = {
    "wrapper_file_path": "engainos/server/safe_runtime_server_entrypoint.py",
    "status": "blueprint_only_not_implemented",
    "must_not_launch_live_server_in_this_lane": True,
    "future_bind_host": "127.0.0.1",
    "future_bind_port": 8080,
    "authority_boundaries": {
        "runtime_gateway": "godotsim/godotsim_legacy/runtime_gateway.py",
        "ap_runtime_relay": "engainos/relays/ap_runtime_relay.py",
        "ap_runtime_blocked_direct": "godotengain/engainos/core/ap_runtime.py",
    },
}

REQUIRED_FILES = {
    "sim_runtime.py": REPO_ROOT / "godotsim/godotsim_legacy/sim_runtime.py",
    "http_handlers.py": REPO_ROOT / "godotsim/godotsim_legacy/http_handlers.py",
    "runtime_gateway.py": REPO_ROOT / "godotsim/godotsim_legacy/runtime_gateway.py",
    "ap_runtime_relay.py": REPO_ROOT / "engainos/relays/ap_runtime_relay.py",
    "ap_runtime.py": REPO_ROOT / "godotengain/engainos/core/ap_runtime.py",
}

SAFE_WRAPPER_PATH = REPO_ROOT / SAFE_WRAPPER_BLUEPRINT["wrapper_file_path"]

FORBIDDEN_RUNTIME_PROCESSES = (
    "godotsim/godotsim_legacy/sim_runtime.py",
    "godotsim/sim_runtime.py",
    "godotengain/engainos/launch_engine.py",
    "godotengain/engainos/core/ap_runtime.py",
)

RouteStatus = Literal["allowed", "blocked", "allowed_preflight_only"]


@dataclass(frozen=True)
class RouteContract:
    route: str
    status: RouteStatus
    requires_gateway: bool
    requires_ap_relay: bool
    requires_schema_validation: bool
    mutation_surface: str
    direct_mutation_forbidden: bool
    allowed_after: str
    notes: str


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "TRUE" if self.passed else "FALSE"


ROUTE_CONTRACTS: tuple[RouteContract, ...] = (
    RouteContract(
        route="/command",
        status="allowed_preflight_only",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="entity/world/action dispatch; may include AP runtime messages",
        direct_mutation_forbidden=True,
        allowed_after="RuntimeGateway accepts request and APRuntimeRelay validates/forwards AP messages without manufacturing authority flags.",
        notes="Read-only commands may be classified by RuntimeGateway, but wrapper must still schema-normalize before dispatch.",
    ),
    RouteContract(
        route="/snapshot",
        status="allowed",
        requires_gateway=False,
        requires_ap_relay=False,
        requires_schema_validation=True,
        mutation_surface="read-only snapshot export",
        direct_mutation_forbidden=True,
        allowed_after="Read-only response schema is validated and route contains no state mutation side effects.",
        notes="May read runtime snapshot only; must not hydrate by mutating canonical state during response.",
    ),
    RouteContract(
        route="/scene/load",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="scene state activation/load",
        direct_mutation_forbidden=True,
        allowed_after="EngAInOS gateway approves actor/reality/scene authority and AP relay accepts any AP/rule side effects.",
        notes="Must not call scene_manager.load_scene directly from HTTP transport.",
    ),
    RouteContract(
        route="/vault/link",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="vault registry/link state and scene registry population",
        direct_mutation_forbidden=True,
        allowed_after="Gateway validates authority and schema/path anchors; relay covers AP rule/timeline consequences if any.",
        notes="Must not call vault_linker.link directly from HTTP transport.",
    ),
    RouteContract(
        route="/vault/status",
        status="allowed",
        requires_gateway=False,
        requires_ap_relay=False,
        requires_schema_validation=True,
        mutation_surface="read-only vault status export",
        direct_mutation_forbidden=True,
        allowed_after="Read-only response schema is validated and no vault state is changed.",
        notes="Allowed as observation only; no implicit relink, scan, load, repair, or cache writes.",
    ),
    RouteContract(
        route="/world/sync",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="world build/sync/mirror/load side effects",
        direct_mutation_forbidden=True,
        allowed_after="Gateway accepts explicit authority; AP relay accepts rule/timeline intent; paths are anchored and dry-run/write mode is explicit.",
        notes="Must not build, mirror, chmod, rsync, bulk-load scenes, or write cache directly from HTTP transport.",
    ),
    RouteContract(
        route="/world/load_mirror",
        status="blocked",
        requires_gateway=True,
        requires_ap_relay=True,
        requires_schema_validation=True,
        mutation_surface="world mirror scene ingestion/load",
        direct_mutation_forbidden=True,
        allowed_after="Gateway accepts explicit authority and AP relay covers AP rule/timeline consequences before mirror load.",
        notes="Must not call bulk_load_scenes directly from HTTP transport.",
    ),
)

REQUIRED_ROUTES = {
    "/command",
    "/snapshot",
    "/scene/load",
    "/vault/link",
    "/vault/status",
    "/world/sync",
    "/world/load_mirror",
}

MUTATING_ROUTES = {
    "/command",
    "/scene/load",
    "/vault/link",
    "/world/sync",
    "/world/load_mirror",
}

READ_ONLY_ROUTES = {
    "/snapshot",
    "/vault/status",
}

ALLOWED_STATUSES = {"allowed", "blocked", "allowed_preflight_only"}


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


def gate_required_files_parse() -> GateResult:
    missing: list[str] = []
    parse_errors: dict[str, str] = {}
    parsed: list[str] = []
    for label, path in REQUIRED_FILES.items():
        if not path.exists():
            missing.append(str(path))
            continue
        try:
            parse_source(path)
            parsed.append(label)
        except SyntaxError as exc:
            parse_errors[label] = str(exc)
    passed = not missing and not parse_errors and set(parsed) == set(REQUIRED_FILES)
    return GateResult(
        "GATE_REQUIRED_BOUNDARY_FILES_PARSE",
        passed,
        "Required legacy/runtime gateway/relay/AP files exist and parse for blueprint inspection." if passed else "Required boundary file inspection failed.",
        {"missing": missing, "parse_errors": parse_errors, "parsed": parsed},
    )


def gate_wrapper_path_defined_blueprint_only() -> GateResult:
    wrapper_exists = SAFE_WRAPPER_PATH.exists()
    wrapper_safe = False
    wrapper_reasons: list[str] = []
    if wrapper_exists:
        source = read_source(SAFE_WRAPPER_PATH)
        tree = ast.parse(source, filename=str(SAFE_WRAPPER_PATH))
        wrapper_safe = (
            "RuntimeGateway" in source
            and "ap_runtime_relay" in source
            and "allow_execute" in source
            and "enable_timeline_write" in source
            and "8080" in source
            and has_main_block(tree)
            and "APRuntimeIntegration(" not in source
        )
        if not wrapper_safe:
            wrapper_reasons.append("Existing wrapper path does not prove all safe-entrypoint invariants.")
    else:
        wrapper_reasons.append("Wrapper file path is reserved by contract but not implemented in this blueprint lane.")

    passed = SAFE_WRAPPER_BLUEPRINT["wrapper_file_path"] == "engainos/server/safe_runtime_server_entrypoint.py"
    return GateResult(
        "GATE_SAFE_WRAPPER_FILE_PATH_DEFINED_BLUEPRINT_ONLY",
        passed,
        "Safe wrapper file path is defined as a blueprint and no live server implementation is required in this lane.",
        {
            "safe_wrapper_blueprint": SAFE_WRAPPER_BLUEPRINT,
            "wrapper_abs_path": str(SAFE_WRAPPER_PATH),
            "wrapper_exists": wrapper_exists,
            "wrapper_currently_proves_safe_entrypoint": wrapper_safe,
            "wrapper_reasons": wrapper_reasons,
        },
    )


def gate_route_contracts_complete() -> GateResult:
    routes = {contract.route for contract in ROUTE_CONTRACTS}
    missing = sorted(REQUIRED_ROUTES - routes)
    extra = sorted(routes - REQUIRED_ROUTES)
    duplicate_count = len(ROUTE_CONTRACTS) - len(routes)
    invalid_status = [contract.route for contract in ROUTE_CONTRACTS if contract.status not in ALLOWED_STATUSES]
    missing_schema_validation = [contract.route for contract in ROUTE_CONTRACTS if not contract.requires_schema_validation]
    passed = not missing and not extra and duplicate_count == 0 and not invalid_status and not missing_schema_validation
    return GateResult(
        "GATE_ROUTE_CONTRACTS_COMPLETE",
        passed,
        "All required HTTP routes have explicit status/gateway/relay/schema classifications." if passed else "HTTP route contract table is incomplete.",
        {
            "required_routes": sorted(REQUIRED_ROUTES),
            "contract_routes": sorted(routes),
            "missing_routes": missing,
            "extra_routes": extra,
            "duplicate_count": duplicate_count,
            "invalid_status_routes": invalid_status,
            "missing_schema_validation_routes": missing_schema_validation,
            "route_contracts": [asdict(contract) for contract in ROUTE_CONTRACTS],
        },
    )


def gate_no_direct_mutation_contract() -> GateResult:
    route_errors: dict[str, list[str]] = {}
    for contract in ROUTE_CONTRACTS:
        errors: list[str] = []
        if not contract.direct_mutation_forbidden:
            errors.append("direct mutation is not explicitly forbidden")
        if contract.route in MUTATING_ROUTES:
            if not contract.requires_gateway:
                errors.append("mutating route must require RuntimeGateway/EngAInOS gateway acceptance")
            if not contract.requires_ap_relay:
                errors.append("mutating route must require APRuntimeRelay for AP/rule/timeline consequences")
            if contract.status == "allowed":
                errors.append("mutating route cannot be live-allowed in blueprint lane")
        if contract.route in READ_ONLY_ROUTES:
            if contract.requires_gateway or contract.requires_ap_relay:
                errors.append("read-only route should not require mutation gateway/relay unless future policy changes")
            if contract.status != "allowed":
                errors.append("read-only route should be contract-allowed only as no-side-effect observation")
        if errors:
            route_errors[contract.route] = errors
    passed = not route_errors
    return GateResult(
        "GATE_NO_ROUTE_DIRECT_MUTATION_WITHOUT_GATEWAY_RELAY",
        passed,
        "Route contract forbids direct mutation and requires gateway/relay acceptance for every mutating surface." if passed else "One or more routes can mutate without required authority boundary.",
        {"route_errors": route_errors},
    )


def gate_legacy_server_still_not_safe_entrypoint() -> GateResult:
    sim_source = read_source(REQUIRED_FILES["sim_runtime.py"])
    http_source = read_source(REQUIRED_FILES["http_handlers.py"])
    sim_binds_without_relay = "ThreadingHTTPServer((\"127.0.0.1\", 8080), RuntimeHTTPHandler)" in sim_source and "ap_runtime_relay" not in sim_source
    direct_mutation_markers = [
        marker for marker in (
            "scene_manager.load_scene(",
            "vault_linker.link(",
            "bulk_load_scenes(",
            "runtime.load_scene(",
            "select_active_scene(",
        )
        if marker in http_source
    ]
    command_gateway_present = "RuntimeGateway(self.runtime, dispatcher).submit(body)" in http_source
    passed = sim_binds_without_relay and command_gateway_present and bool(direct_mutation_markers)
    return GateResult(
        "GATE_LEGACY_SERVER_REMAINS_BLOCKED_AS_SAFE_ENTRYPOINT",
        passed,
        "Existing sim_runtime/http_handlers do not qualify as the safe wrapper; future wrapper implementation remains pending." if passed else "Legacy server classification changed and needs review.",
        {
            "sim_runtime_binds_8080_without_relay": sim_binds_without_relay,
            "http_command_gateway_present": command_gateway_present,
            "http_direct_mutation_markers": direct_mutation_markers,
        },
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


def gate_ap_runtime_direct_run_remains_blocked() -> GateResult:
    ap_path = REQUIRED_FILES["ap_runtime.py"]
    source = read_source(ap_path)
    tree = ast.parse(source, filename=str(ap_path))
    main_tail = source.split('if __name__ == "__main__":')[-1]
    passed = has_main_block(tree) and "raise SystemExit" in source and "APRuntimeIntegration()" not in main_tail
    return GateResult(
        "GATE_AP_RUNTIME_DIRECT_RUN_REMAINS_BLOCKED",
        passed,
        "ap_runtime.py direct execution remains fail-closed." if passed else "ap_runtime.py direct-run blocker is missing or unsafe.",
        {"path": str(ap_path), "has_main_block": has_main_block(tree), "has_system_exit": "raise SystemExit" in source},
    )


def main() -> int:
    wrapper_path_gate = gate_wrapper_path_defined_blueprint_only()
    wrapper_currently_safe = bool(wrapper_path_gate.details.get("wrapper_currently_proves_safe_entrypoint"))

    results = [
        gate_required_files_parse(),
        wrapper_path_gate,
        gate_route_contracts_complete(),
        gate_no_direct_mutation_contract(),
        gate_legacy_server_still_not_safe_entrypoint(),
        gate_ap_runtime_direct_run_remains_blocked(),
        gate_port_8080_closed(),
    ]
    all_passed = all(result.passed for result in results)

    safe_entrypoint_identified = wrapper_currently_safe
    blocked_pending_wrapper_implementation = not safe_entrypoint_identified
    safe_server_wrapper_contract_defined = all_passed and not safe_entrypoint_identified

    report = {
        "refactor_id": "SAFE_SERVER_WRAPPER_BLUEPRINT_LANE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "SAFE_SERVER_WRAPPER_BLUEPRINT_LANE",
        "SAFE_SERVER_WRAPPER_BLUEPRINT_LANE": all_passed,
        "SAFE_SERVER_WRAPPER_CONTRACT_DEFINED": safe_server_wrapper_contract_defined,
        "SERVER_RUNTIME_LANE": "BLOCKED",
        "PORT_8080_ALLOWED": False,
        "SAFE_SERVER_ENTRYPOINT_IDENTIFIED": safe_entrypoint_identified,
        "BLOCKED_PENDING_WRAPPER_IMPLEMENTATION": blocked_pending_wrapper_implementation,
        "safe_wrapper_blueprint": SAFE_WRAPPER_BLUEPRINT,
        "route_contracts": [asdict(contract) for contract in ROUTE_CONTRACTS],
        "gates": [asdict(result) | {"status": result.status} for result in results],
        "acceptance": "ACCEPTED_BLUEPRINT_CONTRACT_DEFINED" if all_passed else "REJECTED_BLUEPRINT_CONTRACT_NOT_PROVEN",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for contract in ROUTE_CONTRACTS:
        print(
            "[gate_safe_server_wrapper_blueprint_lane][ROUTE] "
            f"{contract.route} status={contract.status} "
            f"requires_gateway={str(contract.requires_gateway).lower()} "
            f"requires_ap_relay={str(contract.requires_ap_relay).lower()} "
            f"requires_schema_validation={str(contract.requires_schema_validation).lower()}"
        )
    for result in results:
        print(f"[gate_safe_server_wrapper_blueprint_lane][{result.gate_name}] {result.status}: {result.message}")
    print(f"[gate_safe_server_wrapper_blueprint_lane][SAFE_SERVER_WRAPPER_BLUEPRINT_LANE] {'TRUE' if all_passed else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_blueprint_lane][SAFE_SERVER_WRAPPER_CONTRACT_DEFINED] {'TRUE' if safe_server_wrapper_contract_defined else 'FALSE'}")
    print("[gate_safe_server_wrapper_blueprint_lane][SERVER_RUNTIME_LANE] BLOCKED")
    print("[gate_safe_server_wrapper_blueprint_lane][PORT_8080_ALLOWED] FALSE")
    print(f"[gate_safe_server_wrapper_blueprint_lane][SAFE_SERVER_ENTRYPOINT_IDENTIFIED] {'TRUE' if safe_entrypoint_identified else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_blueprint_lane][BLOCKED_PENDING_WRAPPER_IMPLEMENTATION] {'TRUE' if blocked_pending_wrapper_implementation else 'FALSE'}")
    print(f"[gate_safe_server_wrapper_blueprint_lane][REPORT] {REPORT_PATH}")
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
