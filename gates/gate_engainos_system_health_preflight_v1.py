# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/gates/gate_engainos_system_health_preflight_v1.py

from __future__ import annotations

import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure repository root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


ENGAINOS_RUNTIME_MODULES = {
    "launch_engine": "tier1.engainos.launch_engine",
    "engainos_facade": "tier1.engainos.engainos_server",
    "scene_loader": "tier1.engainos.bridgeroom.scene_loader",
    "scene_server": "tier1.engainos.bridgeroom.scene_server",
    "ap_engine": "tier1.engainos.aproom.ap_engine",
    "ap_runtime": "tier1.engainos.aproom.ap_runtime",
}

ENGAINOS_RUNTIME_PATHS = {
    "mettaext_stageroom": ("tier3", "mettaext", "stageroom"),
    "mettaext_scene_packet_index": (
        "tier3", "mettaext", "stageroom", "output", "chapterroom", "scene_packets"
    ),
    "mettaext_passroom_output": (
        "tier3", "mettaext", "stageroom", "output", "passroom"
    ),
}


@dataclass(frozen=True)
class GateResult:
    passed: bool
    gate_name: str
    message: str
    details: dict[str, Any]


def gate_systems_reachable() -> GateResult:
    systems = {
        "engainos": "tier1.engainos",
        "godotsim": "tier2.godotsim",
        "engionality": "tier2.engionality",
        "mettaext": "tier3.mettaext",
    }

    details = {}
    passed = True

    for name, module_path in systems.items():
        try:
            # Attempt read-only ping import
            __import__(module_path)
            details[name] = {"reachable": True, "path": module_path}
        except Exception as exc:
            details[name] = {"reachable": False, "path": module_path, "error": str(exc)}
            passed = False

    return GateResult(
        passed=passed,
        gate_name="GATE_SYSTEMS_REACHABLE",
        message="All systems are reachable (ping imports successful)." if passed else "One or more systems are unreachable.",
        details=details,
    )


def gate_engainos_runtime_requirements(root: Path = ROOT) -> GateResult:
    module_details: dict[str, dict[str, Any]] = {}
    path_details: dict[str, dict[str, Any]] = {}
    passed = True

    for name, module_path in ENGAINOS_RUNTIME_MODULES.items():
        try:
            importlib.import_module(module_path)
            module_details[name] = {"importable": True, "path": module_path}
        except Exception as exc:
            module_details[name] = {
                "importable": False,
                "path": module_path,
                "error": str(exc),
            }
            passed = False

    for name, relative_parts in ENGAINOS_RUNTIME_PATHS.items():
        path = root.joinpath(*relative_parts)
        exists = path.is_dir()
        path_details[name] = {
            "exists": exists,
            "path": str(path),
            "type": "directory",
        }
        if not exists:
            passed = False

    return GateResult(
        passed=passed,
        gate_name="GATE_ENGAINOS_RUNTIME_REQUIREMENTS",
        message=(
            "EngAInOS runtime modules and data paths are available."
            if passed
            else "One or more EngAInOS runtime requirements are unavailable."
        ),
        details={"modules": module_details, "paths": path_details},
    )


def gate_lanes_valid() -> GateResult:
    readme_path = ROOT / "README_TIER_VS_LANE.md"
    map_path = ROOT / "ENGAINOS_AUTHORITY_MAP.md"

    checks = {
        "readme_exists": readme_path.exists(),
        "map_exists": map_path.exists(),
    }

    if checks["readme_exists"]:
        content = readme_path.read_text(encoding="utf-8")
        checks["readme_contains_lane"] = "LANE" in content
        checks["readme_contains_tier"] = "TIER" in content
    else:
        checks["readme_contains_lane"] = False
        checks["readme_contains_tier"] = False

    if checks["map_exists"]:
        content = map_path.read_text(encoding="utf-8")
        checks["map_contains_tiers"] = "Authority Tiers" in content
        checks["map_contains_reality_modes"] = "Reality Modes" in content
    else:
        checks["map_contains_tiers"] = False
        checks["map_contains_reality_modes"] = False

    passed = all(checks.values())

    return GateResult(
        passed=passed,
        gate_name="GATE_LANES_VALID",
        message="Tiers and lanes declarations are valid and verified." if passed else "Tiers or lanes specifications are invalid.",
        details=checks,
    )


def build_boot_decision(results: list[GateResult]) -> dict[str, Any]:
    failed = [result for result in results if not result.passed]

    if failed:
        return {
            "boot_allowed": False,
            "boot_status": "BOOT_BLOCKED",
            "blocked_by": failed[0].gate_name,
            "reason": failed[0].message,
            "systems_may_initialize": False,
            "scene_may_load": False,
            "runtime_mutation_allowed": False,
            "next_action": "RESTORE_SYSTEM_INTEGRITY_THEN_RETRY"
        }

    return {
        "boot_allowed": True,
        "boot_status": "BOOT_ACCEPTED",
        "blocked_by": None,
        "reason": "All core systems and EngAInOS runtime requirements are reachable.",
        "systems_may_initialize": True,
        "scene_may_load": False,
        "runtime_mutation_allowed": False,
        "next_action": "BOOT_SCENE_AUTHORIZATION_REQUEST"
    }


def print_gate(result: GateResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[engainos_system_health_preflight][{result.gate_name}] {status}: {result.message}")
    print(json.dumps(result.details, indent=2, sort_keys=True))


def main() -> int:
    results = [
        gate_systems_reachable(),
        gate_engainos_runtime_requirements(),
        gate_lanes_valid(),
    ]

    for result in results:
        print_gate(result)

    all_passed = all(result.passed for result in results)
    decision = build_boot_decision(results)

    print(f"[engainos_system_health_preflight][ALL_GATES] {str(all_passed).lower()}")
    print(json.dumps(decision, indent=2, sort_keys=True))

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
