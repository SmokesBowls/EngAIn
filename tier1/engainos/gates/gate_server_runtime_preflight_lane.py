#!/usr/bin/env python3
"""
SERVER_RUNTIME_PREFLIGHT_LANE gate.

Purpose:
  Identify the current safe/blocked runtime entry path before any future action
  may open port 8080. This gate is inspection-only: it must not import or run
  sim_runtime.py, launch_engine.py, or ap_runtime.py.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import ast
import json
import socket
import sys

GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SERVER_RUNTIME_PREFLIGHT_BOARD"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = REPO_ROOT / "scratch/server_runtime_preflight_lane_report.json"
PORT_8080 = 8080

ENTRYPOINTS: dict[str, list[Path]] = {
    "sim_runtime.py": [REPO_ROOT / "godotsim/godotsim_legacy/sim_runtime.py"],
    "launch_engine.py": [REPO_ROOT / "godotengain/engainos/launch_engine.py"],
    "runtime_core.py": [REPO_ROOT / "godotsim/godotsim_legacy/runtime_core.py"],
    "http_handlers.py": [REPO_ROOT / "godotsim/godotsim_legacy/http_handlers.py"],
    "runtime_gateway.py": [REPO_ROOT / "godotsim/godotsim_legacy/runtime_gateway.py"],
    "ap_runtime.py": [REPO_ROOT / "godotengain/engainos/core/ap_runtime.py"],
    "ap_runtime_relay.py": [REPO_ROOT / "engainos/relays/ap_runtime_relay.py"],
}

OPTIONAL_HISTORICAL_ENTRYPOINTS: dict[str, list[Path]] = {
    "launch_engine.py": [REPO_ROOT / "godotengain/eng-a-in-os-game-client-(4.4)/launch_engine.py"],
    "ap_runtime.py": [
        REPO_ROOT / "godotengain/eng-a-in-os-game-client-(4.4)/core/ap_runtime.py",
        REPO_ROOT / "ap/ap_runtime.py",
    ],
}

ALLOWED_CLASSIFICATIONS = {
    "allowed_preflight_only",
    "blocked_direct_run",
    "candidate_safe_server_entry",
    "legacy_compatibility_only",
    "support_library",
}


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "TRUE" if self.passed else "FALSE"


@dataclass(frozen=True)
class EntryClassification:
    name: str
    path: str
    classification: str
    reason: str
    binds_port_8080: bool = False
    has_main_block: bool = False
    imports_or_references_ap_runtime: bool = False
    imports_or_references_relay: bool = False
    imports_or_references_runtime_gateway: bool = False
    starts_server: bool = False
    optional_historical: bool = False


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
    hits: list[dict[str, str]] = []
    proc_root = Path("/proc")
    if not proc_root.exists():
        return hits
    forbidden_tokens = (
        "godotsim/godotsim_legacy/sim_runtime.py",
        "godotsim/sim_runtime.py",
        "godotengain/engainos/launch_engine.py",
    )
    for pid_dir in proc_root.iterdir():
        if not pid_dir.name.isdigit():
            continue
        cmdline_path = pid_dir / "cmdline"
        try:
            raw = cmdline_path.read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        cmdline = raw.replace(b"\x00", b" ").decode("utf-8", errors="replace")
        for token in forbidden_tokens:
            if token in cmdline:
                hits.append({"pid": pid_dir.name, "token": token, "cmdline": cmdline})
                break
    return hits


def classify_path(name: str, path: Path, optional_historical: bool = False) -> EntryClassification:
    if not path.exists():
        return EntryClassification(
            name=name,
            path=str(path),
            classification="blocked_direct_run" if not optional_historical else "legacy_compatibility_only",
            reason="Expected entrypoint path is missing." if not optional_historical else "Historical optional path is absent from active preflight.",
            optional_historical=optional_historical,
        )

    source = read_source(path)
    tree = ast.parse(source, filename=str(path))
    main = has_main_block(tree)
    binds_8080 = "8080" in source and "ThreadingHTTPServer" in source
    starts_server = "serve_forever" in source or "start_scene_server" in source or "ThreadingHTTPServer" in source
    references_ap_runtime = "APRuntimeIntegration" in source or "ap_runtime" in source
    references_relay = "ap_runtime_relay" in source or "APRuntimeRelay" in source or "build_ap_runtime_relay" in source
    references_gateway = "RuntimeGateway" in source or "runtime_gateway" in source

    if optional_historical:
        return EntryClassification(
            name=name,
            path=str(path),
            classification="legacy_compatibility_only",
            reason="Historical duplicate/compatibility path; not an approved server entry for EngAInOS preflight.",
            binds_port_8080=binds_8080,
            has_main_block=main,
            imports_or_references_ap_runtime=references_ap_runtime,
            imports_or_references_relay=references_relay,
            imports_or_references_runtime_gateway=references_gateway,
            starts_server=starts_server,
            optional_historical=True,
        )

    if name == "sim_runtime.py":
        if binds_8080 and starts_server and not references_relay:
            classification = "blocked_direct_run"
            reason = "Legacy HTTP server binds port 8080 directly and does not pass AP messages through engainos/relays/ap_runtime_relay.py."
        elif binds_8080 and references_relay and references_gateway:
            classification = "candidate_safe_server_entry"
            reason = "Server binds port 8080 only with relay and gateway references present."
        else:
            classification = "allowed_preflight_only"
            reason = "Runtime entry requires further preflight before direct server use."
    elif name == "launch_engine.py":
        if starts_server and references_ap_runtime and not references_relay:
            classification = "blocked_direct_run"
            reason = "Launch engine starts scene server and references APRuntimeIntegration directly instead of the approved relay boundary."
        else:
            classification = "allowed_preflight_only"
            reason = "Launch engine is inspection-only in this lane."
    elif name == "runtime_core.py":
        classification = "support_library"
        reason = "Runtime core owns state/subsystems and may instantiate simulation internals, but it is not the approved server entrypoint."
    elif name == "http_handlers.py":
        classification = "support_library"
        reason = "HTTP handler is transport support and does not bind a server by itself; future AP routes must be relay/gateway mediated."
    elif name == "runtime_gateway.py":
        classification = "support_library"
        reason = "Runtime gateway is governance support for runtime mutations, not a server entrypoint."
    elif name == "ap_runtime.py":
        if main and "raise SystemExit" in source:
            classification = "blocked_direct_run"
            reason = "AP runtime bridge has an explicit fail-closed __main__ blocker."
        else:
            classification = "blocked_direct_run"
            reason = "AP runtime bridge must not be run directly."
    elif name == "ap_runtime_relay.py":
        classification = "support_library"
        reason = "Approved AP relay boundary; relay carries accepted AP calls but must not open server ports."
    else:
        classification = "allowed_preflight_only"
        reason = "Unknown entrypoint inspected for preflight only."

    return EntryClassification(
        name=name,
        path=str(path),
        classification=classification,
        reason=reason,
        binds_port_8080=binds_8080,
        has_main_block=main,
        imports_or_references_ap_runtime=references_ap_runtime,
        imports_or_references_relay=references_relay,
        imports_or_references_runtime_gateway=references_gateway,
        starts_server=starts_server,
        optional_historical=False,
    )


def classify_entrypoints() -> list[EntryClassification]:
    classifications: list[EntryClassification] = []
    for name, paths in ENTRYPOINTS.items():
        for path in paths:
            classifications.append(classify_path(name, path, optional_historical=False))
    for name, paths in OPTIONAL_HISTORICAL_ENTRYPOINTS.items():
        for path in paths:
            if path.exists():
                classifications.append(classify_path(name, path, optional_historical=True))
    return classifications


def method_source(path: Path, class_name: str, method_name: str) -> str:
    source = read_source(path)
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    return ast.get_source_segment(source, child) or ""
    return ""


def gate_entrypoints_located_and_classified(classifications: list[EntryClassification]) -> GateResult:
    active = [item for item in classifications if not item.optional_historical]
    missing_active = [item for item in active if not Path(item.path).exists()]
    invalid_classes = [item for item in classifications if item.classification not in ALLOWED_CLASSIFICATIONS]
    passed = not missing_active and not invalid_classes and len(active) == sum(len(v) for v in ENTRYPOINTS.values())
    return GateResult(
        "GATE_ENTRYPOINTS_LOCATED_AND_CLASSIFIED",
        passed,
        "All required runtime/server entrypoints are located and classified." if passed else "Required entrypoint classification is incomplete.",
        {
            "missing_active": [asdict(item) for item in missing_active],
            "invalid_classes": [asdict(item) for item in invalid_classes],
            "classifications": [asdict(item) for item in classifications],
        },
    )


def gate_no_runtime_started() -> GateResult:
    port = port_open()
    forbidden = running_forbidden_processes()
    passed = not port and not forbidden
    return GateResult(
        "GATE_NO_RUNTIME_STARTED",
        passed,
        "Port 8080 is closed and forbidden runtime entrypoint processes are not running." if passed else "A forbidden runtime lane surface appears active.",
        {"port_8080_open": port, "forbidden_processes": forbidden},
    )


def gate_ap_runtime_direct_run_blocked() -> GateResult:
    path = REPO_ROOT / "godotengain/engainos/core/ap_runtime.py"
    source = read_source(path)
    tree = ast.parse(source, filename=str(path))
    passed = has_main_block(tree) and "raise SystemExit" in source and "APRuntimeIntegration()" not in source.split("if __name__ == \"__main__\":")[-1]
    return GateResult(
        "GATE_AP_RUNTIME_DIRECT_RUN_BLOCKED",
        passed,
        "ap_runtime.py has a direct-run SystemExit blocker and does not instantiate APRuntimeIntegration under __main__." if passed else "ap_runtime.py may still run directly.",
        {"path": str(path), "has_main_block": has_main_block(tree), "has_system_exit": "raise SystemExit" in source},
    )


def gate_future_server_requires_relay_gateway(classifications: list[EntryClassification]) -> GateResult:
    server_candidates = [item for item in classifications if not item.optional_historical and item.starts_server]
    unsafe_candidates = [
        item for item in server_candidates
        if item.binds_port_8080 and (not item.imports_or_references_relay or not item.imports_or_references_runtime_gateway)
    ]
    safe_candidates = [item for item in server_candidates if item.classification == "candidate_safe_server_entry"]
    blocked_pending_repair = not safe_candidates and bool(unsafe_candidates)
    passed = bool(safe_candidates) or blocked_pending_repair
    return GateResult(
        "GATE_FUTURE_SERVER_REQUIRES_RELAY_GATEWAY",
        passed,
        (
            "SAFE_SERVER_ENTRYPOINT_IDENTIFIED."
            if safe_candidates
            else "BLOCKED_PENDING_ENTRYPOINT_REPAIR: server candidates do not yet prove relay/gateway mediation."
        ),
        {
            "safe_candidates": [asdict(item) for item in safe_candidates],
            "unsafe_candidates": [asdict(item) for item in unsafe_candidates],
            "safe_server_entrypoint_identified": bool(safe_candidates),
            "blocked_pending_entrypoint_repair": blocked_pending_repair,
        },
    )


def gate_ap_relay_boundary_intact() -> GateResult:
    relay_path = REPO_ROOT / "engainos/relays/ap_runtime_relay.py"
    source = read_source(relay_path)
    forbidden = [fragment for fragment in ["ZWAPEngine(", "StateProvider(", "execute_tick(", ".glob(", "write_text("] if fragment in source]
    required = ["engainos_accepted", "handle_message", "allow_execute", "enable_timeline_write", "allow_history_read"]
    missing = [fragment for fragment in required if fragment not in source]
    passed = not forbidden and not missing
    return GateResult(
        "GATE_AP_RELAY_BOUNDARY_INTACT",
        passed,
        "AP relay carries accepted messages without direct engine/state/timeline/server side effects." if passed else "AP relay boundary is incomplete or bypass-prone.",
        {"forbidden_fragments": forbidden, "missing_required_fragments": missing},
    )


def gate_ap_runtime_law_intact() -> GateResult:
    ap_path = REPO_ROOT / "godotengain/engainos/core/ap_runtime.py"
    execute_src = method_source(ap_path, "APRuntimeIntegration", "_handle_execute_tick")
    all_source = read_source(ap_path)
    required_execute = [
        'msg.get("allow_execute") is not True',
        'msg.get("enable_timeline_write") is True',
        "not self.enable_timeline_write",
        "self.enable_timeline_write and requested_timeline_write",
        "execute_tick(",
    ]
    required_loading = [
        "_validate_scene_file_path",
        "_load_json_scene_file",
        "_validate_scene_dict",
        "scene_file.relative_to(self.scenes_dir)",
        "json.JSONDecodeError",
    ]
    missing_execute = [fragment for fragment in required_execute if fragment not in execute_src]
    missing_loading = [fragment for fragment in required_loading if fragment not in all_source]
    forbidden_loading = [fragment for fragment in ['scenes_dir or "scenes"', "scenes_dir or 'scenes'", 'Path("scenes")', "Path('scenes')"] if fragment in all_source]
    passed = not missing_execute and not missing_loading and not forbidden_loading
    return GateResult(
        "GATE_AP_RUNTIME_LAW_INTACT",
        passed,
        "Timeline writes are fenced and scene/rule loading remains path/schema validated." if passed else "AP runtime timeline or rule-loading law is not intact.",
        {
            "missing_execute_fragments": missing_execute,
            "missing_loading_fragments": missing_loading,
            "forbidden_loading_fragments": forbidden_loading,
        },
    )


def main() -> int:
    classifications = classify_entrypoints()
    future_server_gate = gate_future_server_requires_relay_gateway(classifications)
    safe_identified = bool(future_server_gate.details.get("safe_server_entrypoint_identified"))
    blocked_pending_repair = bool(future_server_gate.details.get("blocked_pending_entrypoint_repair"))

    results = [
        gate_entrypoints_located_and_classified(classifications),
        gate_no_runtime_started(),
        gate_ap_runtime_direct_run_blocked(),
        gate_ap_relay_boundary_intact(),
        gate_ap_runtime_law_intact(),
        future_server_gate,
    ]
    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "SERVER_RUNTIME_PREFLIGHT_LANE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "SERVER_RUNTIME_PREFLIGHT_LANE",
        "SERVER_RUNTIME_PREFLIGHT_LANE": all_passed,
        "SERVER_RUNTIME_LANE": "BLOCKED",
        "PORT_8080_ALLOWED": False,
        "SAFE_SERVER_ENTRYPOINT_IDENTIFIED": safe_identified,
        "BLOCKED_PENDING_ENTRYPOINT_REPAIR": blocked_pending_repair,
        "entrypoint_classifications": [asdict(item) for item in classifications],
        "gates": [asdict(result) | {"status": result.status} for result in results],
        "acceptance": "ACCEPTED_PREFLIGHT_TRUE" if all_passed else "REJECTED_PREFLIGHT_NOT_PROVEN",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for item in classifications:
        marker = "HISTORICAL" if item.optional_historical else "ACTIVE"
        print(f"[gate_server_runtime_preflight_lane][CLASSIFY][{marker}] {item.name} {item.classification}: {item.path}")
    for result in results:
        print(f"[gate_server_runtime_preflight_lane][{result.gate_name}] {result.status}: {result.message}")
    print(f"[gate_server_runtime_preflight_lane][SERVER_RUNTIME_PREFLIGHT_LANE] {'TRUE' if all_passed else 'FALSE'}")
    print("[gate_server_runtime_preflight_lane][SERVER_RUNTIME_LANE] BLOCKED")
    print("[gate_server_runtime_preflight_lane][PORT_8080_ALLOWED] FALSE")
    if safe_identified:
        print("[gate_server_runtime_preflight_lane][SAFE_SERVER_ENTRYPOINT_IDENTIFIED] TRUE")
    if blocked_pending_repair:
        print("[gate_server_runtime_preflight_lane][BLOCKED_PENDING_ENTRYPOINT_REPAIR] TRUE")
    print(f"[gate_server_runtime_preflight_lane][REPORT] {REPORT_PATH}")
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
