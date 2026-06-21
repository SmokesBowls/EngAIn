#!/usr/bin/env python3
"""
AP Runtime Blocker Lane Gate

Purpose:
  Preserve the AP runtime blocker verdict and keep SERVER_RUNTIME_LANE / port
  8080 blocked until the HTTP/Godot bridge proves it respects EngAInOS authority.

This gate is source/port inspection only. It must not import or execute
sim_runtime.py, launch_engine.py, or godotengain/engainos/core/ap_runtime.py.
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
GATE_BOARD = "ENGAINOS_AP_RUNTIME_BLOCKER_BOARD"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AP_RUNTIME_PATH = REPO_ROOT / "godotengain/engainos/core/ap_runtime.py"
RELAY_PATH = REPO_ROOT / "engainos/relays/ap_runtime_relay.py"
ROOT_CORE_COPY_PATH = REPO_ROOT / "engainos/core/ap_runtime.py"
REPORT_PATH = REPO_ROOT / "scratch/ap_runtime_blocker_lane_report.json"
PORT_8080 = 8080

FORBIDDEN_RELAY_CALL_NAMES = {
    "ZWAPEngine",
    "StateProvider",
    "execute_tick",
    "simulate_tick",
    "set_flag",
    "set_stat",
    "set_location",
    "add_inventory",
    "set_time_dilation",
    "write_text",
    "open",
}
FORBIDDEN_RELAY_ATTR_NAMES = {
    "execute_tick",
    "simulate_tick",
    "_load_all_rules",
    "_extract_rules_from_zonj",
    "_extract_rules_from_scene_dict",
    "set_flag",
    "set_stat",
    "set_location",
    "add_inventory",
    "set_time_dilation",
    "write_text",
    "glob",
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


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse(path: Path) -> ast.Module:
    return ast.parse(read_source(path), filename=str(path))


def find_class(tree: ast.Module, class_name: str) -> ast.ClassDef | None:
    return next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name), None)


def find_method(class_node: ast.ClassDef, method_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    return next(
        (
            node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name
        ),
        None,
    )


def method_source(path: Path, class_name: str, method_name: str) -> str:
    source = read_source(path)
    tree = ast.parse(source, filename=str(path))
    cls = find_class(tree, class_name)
    if cls is None:
        return ""
    method = find_method(cls, method_name)
    if method is None:
        return ""
    return ast.get_source_segment(source, method) or ""


def call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def port_open(host: str = "127.0.0.1", port: int = PORT_8080) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def gate_files_in_expected_places() -> GateResult:
    passed = AP_RUNTIME_PATH.exists() and RELAY_PATH.exists() and not ROOT_CORE_COPY_PATH.exists()
    return GateResult(
        "GATE_FILES_IN_EXPECTED_PLACES",
        passed,
        (
            "AP runtime remains in godotengain, relay exists in engainos/relays, and no engainos/core copy exists."
            if passed
            else "AP runtime/relay placement violates AP_RUNTIME_BLOCKER_LANE."
        ),
        {
            "ap_runtime_path": str(AP_RUNTIME_PATH),
            "ap_runtime_exists": AP_RUNTIME_PATH.exists(),
            "relay_path": str(RELAY_PATH),
            "relay_exists": RELAY_PATH.exists(),
            "forbidden_root_core_copy": str(ROOT_CORE_COPY_PATH),
            "forbidden_root_core_copy_exists": ROOT_CORE_COPY_PATH.exists(),
        },
    )


def gate_ap_runtime_not_runnable_as_is() -> GateResult:
    source = read_source(AP_RUNTIME_PATH)
    tree = ast.parse(source, filename=str(AP_RUNTIME_PATH))
    main_blocks = []
    unsafe_calls = []
    explicit_blocker = False

    for node in tree.body:
        if isinstance(node, ast.If):
            test = ast.get_source_segment(source, node.test) or ""
            if "__name__" in test and "__main__" in test:
                main_blocks.append({"lineno": node.lineno, "test": test})
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        name = call_name(child)
                        if name in {"APRuntimeIntegration", "initialize", "handle_message", "execute_tick"}:
                            unsafe_calls.append({"lineno": getattr(child, "lineno", None), "call": name})
                        if name in {"SystemExit", "RuntimeError"}:
                            explicit_blocker = True
                    if isinstance(child, ast.Raise):
                        explicit_blocker = True

    passed = bool(main_blocks) and explicit_blocker and not unsafe_calls
    return GateResult(
        "GATE_AP_RUNTIME_NOT_RUNNABLE_AS_IS",
        passed,
        (
            "ap_runtime.py has an explicit __main__ blocker and does not initialize/execute runtime from __main__."
            if passed
            else "ap_runtime.py is still runnable as-is or its __main__ block can initialize/execute runtime."
        ),
        {"main_blocks": main_blocks, "unsafe_main_calls": unsafe_calls, "explicit_blocker": explicit_blocker},
    )


def gate_execute_tick_respects_timeline_write() -> GateResult:
    src = method_source(AP_RUNTIME_PATH, "APRuntimeIntegration", "_handle_execute_tick")
    required = [
        'msg.get("allow_execute") is not True',
        'msg.get("enable_timeline_write") is True',
        "not self.enable_timeline_write",
        "self.enable_timeline_write and requested_timeline_write",
        "self.engine.enable_timeline_write",
        "execute_tick(",
    ]
    missing = [fragment for fragment in required if fragment not in src]
    passed = not missing
    return GateResult(
        "GATE_EXECUTE_TICK_RESPECTS_ENABLE_TIMELINE_WRITE",
        passed,
        (
            "_handle_execute_tick requires explicit execute intent and constrains engine timeline writes with enable_timeline_write."
            if passed
            else "_handle_execute_tick may bypass allow_execute or enable_timeline_write."
        ),
        {"missing_fragments": missing},
    )


def gate_rule_loading_anchored_and_schema_validated() -> GateResult:
    source = read_source(AP_RUNTIME_PATH)
    load_src = method_source(AP_RUNTIME_PATH, "APRuntimeIntegration", "_load_all_rules")
    resolve_src = method_source(AP_RUNTIME_PATH, "APRuntimeIntegration", "_resolve_scenes_dir")
    required_fragments = [
        "self.project_root / path",
        ".resolve()",
        "_validate_scene_file_path",
        "_load_json_scene_file",
        "_validate_scene_dict",
        "scene_file.relative_to(self.scenes_dir)",
        "json.JSONDecodeError",
    ]
    forbidden_fragments = [
        'scenes_dir or "scenes"',
        "scenes_dir or 'scenes'",
        'Path("scenes")',
        "Path('scenes')",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in source]
    forbidden = [fragment for fragment in forbidden_fragments if fragment in source]
    glob_on_self_scenes_dir = "self.scenes_dir.glob(ext)" in load_src
    anchors_relative_path = "self.project_root / path" in resolve_src
    passed = not missing and not forbidden and glob_on_self_scenes_dir and anchors_relative_path
    return GateResult(
        "GATE_RULE_LOADING_ANCHORED_AND_SCHEMA_VALIDATED",
        passed,
        (
            "Rule loading uses anchored scene paths plus path/schema validation before extracting rules."
            if passed
            else "Rule loading may use unanchored globbing or parse scenes without path/schema validation."
        ),
        {
            "missing_fragments": missing,
            "forbidden_fragments": forbidden,
            "glob_on_self_scenes_dir": glob_on_self_scenes_dir,
            "anchors_relative_path": anchors_relative_path,
        },
    )


def gate_dispatch_handlers_defined() -> GateResult:
    tree = parse(AP_RUNTIME_PATH)
    cls = find_class(tree, "APRuntimeIntegration")
    if cls is None:
        return GateResult("GATE_DISPATCH_HANDLERS_DEFINED", False, "APRuntimeIntegration class not found.")

    defined = {node.name for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    dispatch_calls = []
    handle = find_method(cls, "handle_message")
    if handle is not None:
        for node in ast.walk(handle):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr.startswith("_handle_"):
                    dispatch_calls.append(node.func.attr)
    missing = sorted({name for name in dispatch_calls if name not in defined})
    passed = bool(dispatch_calls) and not missing
    return GateResult(
        "GATE_DISPATCH_HANDLERS_DEFINED",
        passed,
        (
            "Every _handle_* referenced by handle_message is defined."
            if passed
            else "handle_message references undefined handlers."
        ),
        {"dispatch_calls": sorted(set(dispatch_calls)), "missing_handlers": missing},
    )


def gate_relay_has_no_runtime_side_effects() -> GateResult:
    tree = parse(RELAY_PATH)
    forbidden_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_name(node)
            if name in FORBIDDEN_RELAY_CALL_NAMES:
                forbidden_calls.append({"lineno": getattr(node, "lineno", None), "call": name})
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_RELAY_ATTR_NAMES:
                forbidden_calls.append({"lineno": getattr(node, "lineno", None), "call": node.func.attr})
    source = read_source(RELAY_PATH)
    forbidden_text = [fragment for fragment in ["ZWAPEngine(", "StateProvider(", "execute_tick(", ".glob(", "write_text("] if fragment in source]
    passed = not forbidden_calls and not forbidden_text
    return GateResult(
        "GATE_RELAY_HAS_NO_RUNTIME_SIDE_EFFECTS",
        passed,
        (
            "Relay source does not instantiate engine/state, load/glob scenes, write timeline/files, mutate state, or call execute_tick directly."
            if passed
            else "Relay source contains forbidden runtime side-effect calls."
        ),
        {"forbidden_calls": forbidden_calls, "forbidden_text": forbidden_text},
    )


def gate_server_runtime_lane_blocked() -> GateResult:
    open_now = port_open()
    bridge_authority_gate = False
    passed = not open_now and not bridge_authority_gate
    return GateResult(
        "GATE_SERVER_RUNTIME_LANE_BLOCKED",
        passed,
        (
            "SERVER_RUNTIME_LANE remains blocked: port 8080 is closed and no HTTP/Godot authority bridge gate is accepted."
            if passed
            else "SERVER_RUNTIME_LANE is not blocked or port 8080 is already open."
        ),
        {
            "port": PORT_8080,
            "host": "127.0.0.1",
            "port_8080_open": open_now,
            "http_godot_bridge_authority_gate_accepted": bridge_authority_gate,
            "server_runtime_lane_allowed": False,
        },
    )


def main() -> int:
    results = [
        gate_files_in_expected_places(),
        gate_ap_runtime_not_runnable_as_is(),
        gate_execute_tick_respects_timeline_write(),
        gate_rule_loading_anchored_and_schema_validated(),
        gate_dispatch_handlers_defined(),
        gate_relay_has_no_runtime_side_effects(),
        gate_server_runtime_lane_blocked(),
    ]
    all_passed = all(result.passed for result in results)
    report = {
        "refactor_id": "AP_RUNTIME_BLOCKER_LANE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "AP_RUNTIME_BLOCKER_LANE",
        "server_runtime_lane": "BLOCKED",
        "port_8080_allowed": False,
        "sim_runtime_launch_allowed": False,
        "launch_engine_allowed": False,
        "http_godot_bridge_authority_gate_required_before_server_runtime_lane": True,
        "gates": [asdict(result) | {"status": result.status} for result in results],
        "acceptance": "ACCEPTED_BLOCKER_LANE_HELD" if all_passed else "REJECTED_BLOCKER_LANE_NOT_PROVEN",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        print(f"[gate_ap_runtime_blocker_lane][{result.gate_name}] {result.status}: {result.message}")
    print(f"[gate_ap_runtime_blocker_lane][SERVER_RUNTIME_LANE] BLOCKED")
    print(f"[gate_ap_runtime_blocker_lane][PORT_8080_ALLOWED] false")
    print(f"[gate_ap_runtime_blocker_lane][ALL_GATES] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_runtime_blocker_lane][REPORT] {REPORT_PATH}")
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
