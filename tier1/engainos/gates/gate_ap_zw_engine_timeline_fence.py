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

REPORT_PATH = REPO_ROOT / "scratch/ap_zw_engine_timeline_fence_report.json"
SCRATCH_ROOT = REPO_ROOT / "scratch/ap_zw_engine_timeline_fence"

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    status: str
    message: str
    details: dict[str, Any]

def build_probe_rules() -> dict[str, dict[str, Any]]:
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

def gate_dry_run_does_not_write_timeline() -> GateResult:
    from tier1.engainos.core.ap_zw_engine import ZWAPEngine

    dry_root = SCRATCH_ROOT / "dry_run"
    timeline_path = dry_root / "zon/timeline.jsonl"

    if timeline_path.exists():
        timeline_path.unlink()

    engine = ZWAPEngine(
        build_probe_rules(),
        enable_timeline_write=False,
        timeline_root=str(dry_root),
    )

    result = engine.execute_tick({"hero": "hero"})
    timeline_exists = timeline_path.exists()

    passed = timeline_exists is False

    return GateResult(
        gate_name="GATE_DRY_RUN_DOES_NOT_WRITE_TIMELINE",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="execute_tick does not write timeline when enable_timeline_write is False." if passed else "execute_tick wrote timeline during dry-run mode.",
        details={
            "timeline_path": str(timeline_path),
            "timeline_exists": timeline_exists,
            "execute_result": result,
            "warnings": getattr(engine, "_warnings", []),
        },
    )

def gate_enabled_write_uses_explicit_scratch_root() -> GateResult:
    from tier1.engainos.core.ap_zw_engine import ZWAPEngine

    write_root = SCRATCH_ROOT / "enabled_write"
    timeline_path = write_root / "zon/timeline.jsonl"

    if timeline_path.exists():
        timeline_path.unlink()

    engine = ZWAPEngine(
        build_probe_rules(),
        enable_timeline_write=True,
        timeline_root=str(write_root),
    )

    result = engine.execute_tick({"hero": "hero"})
    timeline_exists = timeline_path.exists()

    lines = []
    if timeline_exists:
        lines = timeline_path.read_text(encoding="utf-8").splitlines()

    passed = timeline_exists and len(lines) == 1

    return GateResult(
        gate_name="GATE_ENABLED_WRITE_USES_EXPLICIT_SCRATCH_ROOT",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="execute_tick writes only when explicitly enabled and uses explicit scratch root." if passed else "enabled timeline write did not behave as expected.",
        details={
            "timeline_path": str(timeline_path),
            "timeline_exists": timeline_exists,
            "line_count": len(lines),
            "lines": lines,
            "execute_result": result,
        },
    )

def gate_default_constructor_is_fenced() -> GateResult:
    from tier1.engainos.core.ap_zw_engine import ZWAPEngine

    engine = ZWAPEngine(build_probe_rules())

    enabled = getattr(engine, "enable_timeline_write", None)
    root = getattr(engine, "timeline_root", "missing")

    passed = enabled is False and root is None

    return GateResult(
        gate_name="GATE_DEFAULT_CONSTRUCTOR_IS_FENCED",
        passed=passed,
        status="TRUE" if passed else "FALSE",
        message="ZWAPEngine defaults to timeline-write disabled." if passed else "ZWAPEngine does not default to fenced timeline mode.",
        details={
            "enable_timeline_write": enabled,
            "timeline_root": root,
        },
    )

def main() -> int:
    results = [
        gate_default_constructor_is_fenced(),
        gate_dry_run_does_not_write_timeline(),
        gate_enabled_write_uses_explicit_scratch_root(),
    ]

    all_passed = all(result.passed for result in results)

    report = {
        "refactor_id": "AP_ZW_ENGINE_TIMELINE_FENCE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "engainos_core_authority",
        "stack": "engainos",
        "runtime_wiring_allowed": all_passed,
        "timeline_write_default": "disabled",
        "timeline_write_requires_explicit_enable": True,
        "gates": [asdict(result) for result in results],
        "acceptance": "ACCEPTED" if all_passed else "REJECTED",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        label = "PASS" if result.passed else "FAIL"
        print(f"[gate_ap_zw_engine_timeline_fence][{result.gate_name}] {label}: {result.message}")

    print(f"[gate_ap_zw_engine_timeline_fence][RUNTIME_WIRING_ALLOWED] {'true' if all_passed else 'false'}")
    print(f"[gate_ap_zw_engine_timeline_fence][REPORT] {REPORT_PATH}")
    print(f"[gate_ap_zw_engine_timeline_fence][ALL_GATES] {'true' if all_passed else 'false'}")

    return 0 if all_passed else 2

if __name__ == "__main__":
    raise SystemExit(main())
