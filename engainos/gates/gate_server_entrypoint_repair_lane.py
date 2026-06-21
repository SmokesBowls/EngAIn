#!/usr/bin/env python3
"""
SERVER_ENTRYPOINT_REPAIR_LANE gate.

Purpose:
  Preflight-only blueprint for a future safe port-8080 EngAInOS server entrypoint.
  This gate does not import or execute runtime entrypoints and never opens a port.

Acceptance shape:
  - SAFE_SERVER_ENTRYPOINT_IDENTIFIED may become true only when an entrypoint proves
    AP relay + runtime gateway mediation and the AP runtime blocker laws remain true.
  - Until then, BLOCKED_PENDING_ENTRYPOINT_REPAIR remains true with concrete reasons.
  - SERVER_RUNTIME_LANE remains BLOCKED and PORT_8080_ALLOWED remains false.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import ast
import json
import socket

GATE_LIFECYCLE = "ACTIVE_CONTRACT"
GATE_BOARD = "ENGAINOS_SERVER_ENTRYPOINT_REPAIR_BOARD"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPORT_PATH = REPO_ROOT / "scratch/server_entrypoint_repair_lane_report.json"
PORT_8080 = 8080

REQUIRED_INSPECTION_PATHS = {
    "sim_runtime.py": REPO_ROOT / "godotsim/godotsim_legacy/sim_runtime.py",
    "http_handlers.py": REPO_ROOT / "godotsim/godotsim_legacy/http_handlers.py",
    "runtime_gateway.py": REPO_ROOT / "godotsim/godotsim_legacy/runtime_gateway.py",
    "runtime_core.py": REPO_ROOT / "godotsim/godotsim_legacy/runtime_core.py",
    "ap_runtime_relay.py": REPO_ROOT / "engainos/relays/ap_runtime_relay.py",
    "ap_runtime.py": REPO_ROOT / "godotengain/engainos/core/ap_runtime.py",
}

# Future approved wrapper candidates must be added here deliberately. The legacy
# sim entrypoint is inspected as an unsafe baseline, not as an approved candidate.
SAFE_ENTRYPOINT_CANDIDATES = [
    REPO_ROOT / "engainos/server/safe_runtime_server_entrypoint.py",
    REPO_ROOT / "engainos/server/runtime_8080_authority_entrypoint.py",
]

MUTATION_ENDPOINT_MARKERS = (
    '"/command"',
    '"/scene/load"',
    '"/vault/link"',
    '"/world/sync"',
    '"/world/load_mirror"',
    '"/combat/damage"',
    '"/inventory/take"',
    '"/inventory/drop"',
    '"/inventory/wear"',
    '"/dialogue/ask"',
)

DIRECT_MUTATION_MARKERS = (
    "scene_manager.load_scene(",
    "vault_linker.link(",
    "bulk_load_scenes(",
    "runtime.load_scene(",
    "select_active_scene(",
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


@dataclass(frozen=True)
class EntrypointAssessment:
    path: str
    exists: bool
    safe_server_entrypoint: bool
    reasons: list[str]
    binds_port_8080: bool = False
    starts_server: bool = False
    has_main_block: bool = False
    references_runtime_gateway: bool = False
    references_ap_runtime_relay: bool = False
    references_ap_runtime_directly: bool = False
    references_execute_intent: bool = False
    references_timeline_fence: bool = False
    references_scene_validation: bool = False


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


def method_source(path: Path, class_name: str, method_name: str) -> str:
    source = read_source(path)
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    return ast.get_source_segment(source, child) or ""
    return ""


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


def assess_candidate(path: Path) -> EntrypointAssessment:
    if not path.exists():
        return EntrypointAssessment(
            path=str(path),
            exists=False,
            safe_server_entrypoint=False,
            reasons=["candidate file does not exist; wrapper still needs repair work"],
        )

    source = read_source(path)
    tree = ast.parse(source, filename=str(path))
    binds_port_8080 = "8080" in source and ("ThreadingHTTPServer" in source or "HTTPServer" in source or "uvicorn" in source)
    starts_server = "serve_forever" in source or "uvicorn.run" in source or "ThreadingHTTPServer" in source
    main = has_main_block(tree)
    references_gateway = "RuntimeGateway" in source or "runtime_gateway" in source
    references_relay = "APRuntimeRelay" in source or "build_ap_runtime_relay" in source or "ap_runtime_relay" in source
    references_ap_direct = "APRuntimeIntegration(" in source or "godotengain.engainos.core.ap_runtime" in source
    references_execute = "allow_execute" in source
    references_timeline = "enable_timeline_write" in source
    references_scene_validation = "_validate_scene" in source or "validate_scene" in source or "relative_to" in source

    reasons: list[str] = []
    if not binds_port_8080:
        reasons.append("does not define the future port-8080 server surface")
    if not starts_server:
        reasons.append("does not define server startup")
    if not main:
        reasons.append("does not provide an explicit __main__/startup guard")
    if not references_gateway:
        reasons.append("does not prove RuntimeGateway mediation")
    if not references_relay:
        reasons.append("does not prove APRuntimeRelay mediation")
    if references_ap_direct:
        reasons.append("references APRuntimeIntegration directly instead of relay boundary")
    if not references_execute:
        reasons.append("does not require explicit allow_execute intent")
    if not references_timeline:
        reasons.append("does not require enable_timeline_write timeline consent")
    if not references_scene_validation:
        reasons.append("does not prove anchored scene/rule path/schema validation")

    safe = not reasons
    return EntrypointAssessment(
        path=str(path),
        exists=True,
        safe_server_entrypoint=safe,
        reasons=reasons,
        binds_port_8080=binds_port_8080,
        starts_server=starts_server,
        has_main_block=main,
        references_runtime_gateway=references_gateway,
        references_ap_runtime_relay=references_relay,
        references_ap_runtime_directly=references_ap_direct,
        references_execute_intent=references_execute,
        references_timeline_fence=references_timeline,
        references_scene_validation=references_scene_validation,
    )


def gate_required_files_inspected() -> GateResult:
    missing = [str(path) for path in REQUIRED_INSPECTION_PATHS.values() if not path.exists()]
    parsed: list[str] = []
    parse_errors: dict[str, str] = {}
    for label, path in REQUIRED_INSPECTION_PATHS.items():
        if not path.exists():
            continue
        try:
            parse_source(path)
            parsed.append(label)
        except SyntaxError as exc:
            parse_errors[label] = str(exc)
    passed = not missing and not parse_errors and set(parsed) == set(REQUIRED_INSPECTION_PATHS)
    return GateResult(
        "GATE_REQUIRED_RUNTIME_FILES_INSPECTED",
        passed,
        "Required sim/runtime/HTTP/gateway/relay/AP files exist and parse for inspection." if passed else "Required inspection set is incomplete.",
        {"missing": missing, "parsed": parsed, "parse_errors": parse_errors},
    )


def gate_legacy_surfaces_not_safe() -> GateResult:
    sim_source = read_source(REQUIRED_INSPECTION_PATHS["sim_runtime.py"])
    http_source = read_source(REQUIRED_INSPECTION_PATHS["http_handlers.py"])
    sim_unsafe = "ThreadingHTTPServer((\"127.0.0.1\", 8080), RuntimeHTTPHandler)" in sim_source and "ap_runtime_relay" not in sim_source
    direct_http_mutations = [marker for marker in DIRECT_MUTATION_MARKERS if marker in http_source]
    mutation_endpoints = [marker for marker in MUTATION_ENDPOINT_MARKERS if marker in http_source]
    command_uses_gateway = "RuntimeGateway(self.runtime, dispatcher).submit(body)" in http_source
    passed = sim_unsafe and command_uses_gateway and bool(direct_http_mutations) and bool(mutation_endpoints)
    return GateResult(
        "GATE_LEGACY_SURFACES_CLASSIFIED_UNSAFE_FOR_8080",
        passed,
        "Legacy sim_runtime/http_handlers are not a safe 8080 entrypoint: command uses RuntimeGateway, but scene/vault/world paths still mutate directly." if passed else "Legacy server safety classification is incomplete.",
        {
            "sim_runtime_binds_8080_without_relay": sim_unsafe,
            "command_path_uses_runtime_gateway": command_uses_gateway,
            "direct_http_mutation_markers": direct_http_mutations,
            "mutation_endpoint_markers": mutation_endpoints,
        },
    )


def gate_runtime_gateway_boundary_present() -> GateResult:
    gateway_source = read_source(REQUIRED_INSPECTION_PATHS["runtime_gateway.py"])
    required = [
        "class RuntimeGateway",
        "def submit",
        "_missing_identity_fields",
        "check_complex_rules",
        "record_intent",
        "self.dispatcher.dispatch(raw_input)",
        "mutation_class",
    ]
    missing = [fragment for fragment in required if fragment not in gateway_source]
    passed = not missing
    return GateResult(
        "GATE_RUNTIME_GATEWAY_BOUNDARY_PRESENT",
        passed,
        "RuntimeGateway exists as the mutation mediation boundary." if passed else "RuntimeGateway boundary proof is incomplete.",
        {"missing_required_fragments": missing},
    )


def gate_relay_boundary_present() -> GateResult:
    relay_source = read_source(REQUIRED_INSPECTION_PATHS["ap_runtime_relay.py"])
    forbidden = [fragment for fragment in ["ZWAPEngine(", "StateProvider(", "execute_tick(", ".glob(", "write_text("] if fragment in relay_source]
    required = ["class APRuntimeRelay", "engainos_accepted", "handle_message", "allow_execute", "enable_timeline_write", "allow_history_read"]
    missing = [fragment for fragment in required if fragment not in relay_source]
    passed = not forbidden and not missing
    return GateResult(
        "GATE_AP_RUNTIME_RELAY_BOUNDARY_PRESENT",
        passed,
        "AP relay is present and does not directly engine/mutate/load/write/execute." if passed else "AP relay boundary proof failed.",
        {"forbidden_fragments": forbidden, "missing_required_fragments": missing},
    )


def gate_ap_runtime_blocker_law_present() -> GateResult:
    ap_path = REQUIRED_INSPECTION_PATHS["ap_runtime.py"]
    ap_source = read_source(ap_path)
    tree = ast.parse(ap_source, filename=str(ap_path))
    execute_src = method_source(ap_path, "APRuntimeIntegration", "_handle_execute_tick")
    required_execute = [
        'msg.get("allow_execute") is not True',
        'msg.get("enable_timeline_write") is True',
        "not self.enable_timeline_write",
        "self.enable_timeline_write and requested_timeline_write",
        "execute_tick(",
    ]
    required_loading = [
        "_resolve_scenes_dir",
        "_validate_scene_file_path",
        "_load_json_scene_file",
        "_validate_scene_dict",
        "scene_file.relative_to(self.scenes_dir)",
        "json.JSONDecodeError",
    ]
    missing_execute = [fragment for fragment in required_execute if fragment not in execute_src]
    missing_loading = [fragment for fragment in required_loading if fragment not in ap_source]
    main_blocked = has_main_block(tree) and "raise SystemExit" in ap_source and "APRuntimeIntegration()" not in ap_source.split('if __name__ == "__main__":')[-1]
    forbidden_loading = [fragment for fragment in ['scenes_dir or "scenes"', "scenes_dir or 'scenes'", 'Path("scenes")', "Path('scenes')"] if fragment in ap_source]
    passed = main_blocked and not missing_execute and not missing_loading and not forbidden_loading
    return GateResult(
        "GATE_AP_RUNTIME_BLOCKER_LAW_PRESENT",
        passed,
        "AP runtime direct run remains blocked; execute and timeline writes require explicit consent; scene/rule loading is anchored and validated." if passed else "AP runtime blocker law is incomplete.",
        {
            "direct_run_blocked": main_blocked,
            "missing_execute_fragments": missing_execute,
            "missing_loading_fragments": missing_loading,
            "forbidden_loading_fragments": forbidden_loading,
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


def gate_safe_entrypoint_blueprint(candidates: list[EntrypointAssessment]) -> GateResult:
    safe = [candidate for candidate in candidates if candidate.safe_server_entrypoint]
    blocked_reasons: list[str] = []
    if not safe:
        blocked_reasons.append("No approved wrapper candidate currently proves all safe-server invariants.")
        blocked_reasons.append("Legacy sim_runtime.py remains blocked because it binds 8080 directly through RuntimeHTTPHandler.")
        blocked_reasons.append("Legacy http_handlers.py still contains non-command mutation routes that bypass RuntimeGateway/APRuntimeRelay.")
    passed = bool(safe) or bool(blocked_reasons)
    return GateResult(
        "GATE_SAFE_SERVER_ENTRYPOINT_BLUEPRINT",
        passed,
        "SAFE_SERVER_ENTRYPOINT_IDENTIFIED." if safe else "BLOCKED_PENDING_ENTRYPOINT_REPAIR: safe wrapper is still required before port 8080 may open.",
        {
            "safe_server_entrypoint_identified": bool(safe),
            "blocked_pending_entrypoint_repair": not bool(safe),
            "safe_candidates": [asdict(candidate) for candidate in safe],
            "candidate_assessments": [asdict(candidate) for candidate in candidates],
            "blocked_reasons": blocked_reasons,
        },
    )


def main() -> int:
    candidates = [assess_candidate(path) for path in SAFE_ENTRYPOINT_CANDIDATES]
    blueprint_gate = gate_safe_entrypoint_blueprint(candidates)
    safe_identified = bool(blueprint_gate.details.get("safe_server_entrypoint_identified"))
    blocked_pending_repair = bool(blueprint_gate.details.get("blocked_pending_entrypoint_repair"))

    results = [
        gate_required_files_inspected(),
        gate_legacy_surfaces_not_safe(),
        gate_runtime_gateway_boundary_present(),
        gate_relay_boundary_present(),
        gate_ap_runtime_blocker_law_present(),
        gate_port_8080_closed(),
        blueprint_gate,
    ]
    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "SERVER_ENTRYPOINT_REPAIR_LANE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "SERVER_ENTRYPOINT_REPAIR_LANE",
        "SERVER_ENTRYPOINT_REPAIR_LANE": all_passed,
        "SERVER_RUNTIME_LANE": "BLOCKED",
        "PORT_8080_ALLOWED": False,
        "SAFE_SERVER_ENTRYPOINT_IDENTIFIED": safe_identified,
        "BLOCKED_PENDING_ENTRYPOINT_REPAIR": blocked_pending_repair,
        "safe_entrypoint_candidates": [asdict(candidate) for candidate in candidates],
        "gates": [asdict(result) | {"status": result.status} for result in results],
        "acceptance": "ACCEPTED_BLOCKED_PENDING_ENTRYPOINT_REPAIR" if all_passed and blocked_pending_repair else ("ACCEPTED_SAFE_ENTRYPOINT_IDENTIFIED" if all_passed else "REJECTED_REPAIR_PROOF_NOT_PROVEN"),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        print(f"[gate_server_entrypoint_repair_lane][{result.gate_name}] {result.status}: {result.message}")
    print(f"[gate_server_entrypoint_repair_lane][SERVER_ENTRYPOINT_REPAIR_LANE] {'TRUE' if all_passed else 'FALSE'}")
    print("[gate_server_entrypoint_repair_lane][SERVER_RUNTIME_LANE] BLOCKED")
    print("[gate_server_entrypoint_repair_lane][PORT_8080_ALLOWED] FALSE")
    print(f"[gate_server_entrypoint_repair_lane][SAFE_SERVER_ENTRYPOINT_IDENTIFIED] {'TRUE' if safe_identified else 'FALSE'}")
    print(f"[gate_server_entrypoint_repair_lane][BLOCKED_PENDING_ENTRYPOINT_REPAIR] {'TRUE' if blocked_pending_repair else 'FALSE'}")
    print(f"[gate_server_entrypoint_repair_lane][REPORT] {REPORT_PATH}")
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
