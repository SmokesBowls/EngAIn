#!/usr/bin/env python3
"""VAULT_BOOT_SIDE_EFFECT_FENCE_LANE gate.

Classifies and fences boot-time vault side effects for the controlled runtime
salvage loop. This gate performs a local-only controlled runtime probe; it must
not delete files, bulk-copy folders, move archives, bind publicly, or leave port
8080 open.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import importlib.util
import json
import socket
import sys

GATE_LIFECYCLE = "PREFLIGHT"
GATE_BOARD = "ENGAINOS_VAULT_BOOT_SIDE_EFFECT_FENCE_BOARD"

PROJECT_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
TARGET_REL = "godotsim/godotsim_legacy/sim_runtime.py"
TARGET_PATH = PROJECT_ROOT / TARGET_REL
REPORT_PATH = PROJECT_ROOT / "scratch/vault_boot_side_effect_fence_lane_report.json"
SALVAGE_GATE_PATH = PROJECT_ROOT / "engainos/gates/gate_controlled_runtime_salvage_lane.py"

BOOT_INTENT_ENV = "ENGAIN_ALLOW_BOOT_VAULT_RELINK"
VAULT_PATH = "/home/mytruelove/Downloads/obsidianburdenNov25"
CONFIG_WRITE_PATH = "godotsim/godotsim_legacy/.engain_config.json"


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "TRUE" if self.passed else "FALSE"


def port_8080_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", 8080)) == 0


def load_salvage_gate_module() -> Any:
    spec = importlib.util.spec_from_file_location("_controlled_runtime_salvage_gate", SALVAGE_GATE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load salvage gate from {SALVAGE_GATE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def source_text() -> str:
    return TARGET_PATH.read_text(encoding="utf-8", errors="replace")


def gate_source_responsibility_and_classification() -> GateResult:
    source = source_text()
    config_abs_path = PROJECT_ROOT / CONFIG_WRITE_PATH
    config_text = config_abs_path.read_text(encoding="utf-8", errors="replace") if config_abs_path.exists() else ""
    detections = {
        "auto_relink_function": "def _auto_relink_vault" in source,
        "auto_relink_call": "_auto_relink_vault(runtime, _config_path)" in source,
        "auto_relink_log": "[VAULT] Auto-relinked" in source,
        "config_saved_log": "[VAULT] Config saved" in source,
        "config_write_call": 'open(config_path, "w")' in source,
        "config_file_name": ".engain_config.json" in source,
        "external_downloads_path_in_source": VAULT_PATH in source,
        "external_downloads_path_in_saved_config": VAULT_PATH in config_text,
        "saved_config_exists": config_abs_path.exists(),
        "boot_intent_env_flag": BOOT_INTENT_ENV in source,
        "default_no_auto_relink": "os.environ.get(BOOT_VAULT_RELINK_ENV" in source or "boot_vault_relink_allowed" in source,
    }
    behavior_classification = (
        "unsafe_default_behavior_fenced_optional_convenience"
        if detections["boot_intent_env_flag"] and detections["default_no_auto_relink"]
        else "unsafe_default_behavior_unfenced"
    )
    passed = (
        detections["auto_relink_function"]
        and detections["auto_relink_log"]
        and detections["config_saved_log"]
        and detections["config_write_call"]
        and detections["config_file_name"]
        and detections["external_downloads_path_in_saved_config"]
        and detections["boot_intent_env_flag"]
        and detections["default_no_auto_relink"]
    )
    return GateResult(
        "GATE_SOURCE_RESPONSIBILITY_AND_CLASSIFICATION",
        passed,
        "Boot-time vault relink/config write responsibility is located and fenced by explicit boot intent." if passed else "Boot-time vault side-effect source is missing an explicit default-off boot fence.",
        {"detections": detections, "behavior_classification": behavior_classification, "config_path": str(config_abs_path)},
    )


def gate_controlled_runtime_default_probe() -> GateResult:
    if port_8080_open():
        return GateResult(
            "GATE_CONTROLLED_RUNTIME_DEFAULT_PROBE",
            False,
            "Port 8080 was already open before the controlled probe.",
            {"port_8080_open_before": True},
        )

    salvage = load_salvage_gate_module()
    outcome = salvage.run_controlled_probe(TARGET_PATH)
    classification, evidence = salvage.classify_failure(outcome)
    combined_output = f"{outcome.stdout}\n{outcome.stderr}"
    auto_relink_observed = "[VAULT] Auto-relinked" in combined_output
    config_write_observed = "[VAULT] Config saved" in combined_output
    external_path_observed = VAULT_PATH in combined_output

    passed = (
        classification == "runtime_started_cleanly"
        and outcome.port_8080_open_during
        and not outcome.port_8080_public_exposure
        and not outcome.port_8080_open_after
        and not auto_relink_observed
        and not config_write_observed
        and not external_path_observed
    )
    return GateResult(
        "GATE_CONTROLLED_RUNTIME_DEFAULT_PROBE",
        passed,
        "Default controlled runtime starts cleanly without boot vault relink/config write side effects." if passed else "Default controlled runtime still exposes boot vault side effects or failed startup/cleanup.",
        {
            "classification": classification,
            "evidence": evidence,
            "port_8080_open_during": outcome.port_8080_open_during,
            "port_8080_open_after": outcome.port_8080_open_after,
            "port_8080_public_exposure": outcome.port_8080_public_exposure,
            "auto_relink_observed": auto_relink_observed,
            "config_write_observed": config_write_observed,
            "external_downloads_path_observed": external_path_observed,
            "stdout_tail": outcome.stdout,
            "stderr_tail": outcome.stderr,
        },
    )


def main() -> int:
    if Path.cwd().resolve() != PROJECT_ROOT.resolve():
        print(f"[gate_vault_boot_side_effect_fence_lane][WORKTREE] FALSE: cwd={Path.cwd().resolve()} expected={PROJECT_ROOT.resolve()}")
        return 1

    results = [
        gate_source_responsibility_and_classification(),
        gate_controlled_runtime_default_probe(),
    ]
    all_passed = all(result.passed for result in results)
    source_details = results[0].details
    probe_details = results[1].details

    behavior_classification = source_details.get("behavior_classification")
    report = {
        "refactor_id": "VAULT_BOOT_SIDE_EFFECT_FENCE_LANE_001",
        "tier_authority": "ENGAINOS_TIER1",
        "lane": "VAULT_BOOT_SIDE_EFFECT_FENCE_LANE",
        "VAULT_BOOT_SIDE_EFFECT_FENCE_LANE": all_passed,
        "BOOT_TIME_VAULT_AUTO_RELINK_DETECTED": bool(source_details.get("detections", {}).get("auto_relink_log")),
        "BOOT_TIME_CONFIG_WRITE_DETECTED": bool(source_details.get("detections", {}).get("config_write_call")),
        "EXTERNAL_DOWNLOADS_VAULT_PATH_DETECTED": bool(source_details.get("detections", {}).get("external_downloads_path_in_source") or source_details.get("detections", {}).get("external_downloads_path_in_saved_config")),
        "BOOT_TIME_VAULT_AUTO_RELINK_CLASSIFIED": behavior_classification in {"unsafe_default_behavior_fenced_optional_convenience", "unsafe_default_behavior_unfenced"},
        "BOOT_TIME_CONFIG_WRITE_CLASSIFIED": behavior_classification in {"unsafe_default_behavior_fenced_optional_convenience", "unsafe_default_behavior_unfenced"},
        "BEHAVIOR_CLASSIFICATION": behavior_classification,
        "DEFAULT_BOOT_SIDE_EFFECTS_ALLOWED": False,
        "CONTROLLED_RUNTIME_START_STILL_TRUE": probe_details.get("classification") == "runtime_started_cleanly",
        "PORT_8080_LOOPBACK_BIND": probe_details.get("port_8080_open_during") is True,
        "PORT_8080_PUBLIC_EXPOSURE": probe_details.get("port_8080_public_exposure") is True,
        "port_8080_open_after_probe": probe_details.get("port_8080_open_after"),
        "DEFAULT_BOOT_VAULT_AUTO_RELINK_OBSERVED": probe_details.get("auto_relink_observed"),
        "DEFAULT_BOOT_CONFIG_WRITE_OBSERVED": probe_details.get("config_write_observed"),
        "DEFAULT_EXTERNAL_DOWNLOADS_PATH_OBSERVED": probe_details.get("external_downloads_path_observed"),
        "BOOT_INTENT_ENV": BOOT_INTENT_ENV,
        "VAULT_AUTO_RELINK_PATH": VAULT_PATH,
        "CONFIG_WRITE_PATH": CONFIG_WRITE_PATH,
        "NO_DELETE": True,
        "NO_BULK_COPY": True,
        "NO_ARCHIVE_MOVEMENT": True,
        "gates": [asdict(result) | {"status": result.status} for result in results],
        "acceptance": "ACCEPTED_FENCE_TRUE" if all_passed else "REJECTED_FENCE_NOT_PROVEN",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    for result in results:
        print(f"[gate_vault_boot_side_effect_fence_lane][{result.gate_name}] {result.status}: {result.message}")
    print(f"[gate_vault_boot_side_effect_fence_lane][VAULT_BOOT_SIDE_EFFECT_FENCE_LANE] {'TRUE' if all_passed else 'FALSE'}")
    print(f"[gate_vault_boot_side_effect_fence_lane][BOOT_TIME_VAULT_AUTO_RELINK_CLASSIFIED] {'TRUE' if report['BOOT_TIME_VAULT_AUTO_RELINK_CLASSIFIED'] else 'FALSE'}")
    print(f"[gate_vault_boot_side_effect_fence_lane][BOOT_TIME_CONFIG_WRITE_CLASSIFIED] {'TRUE' if report['BOOT_TIME_CONFIG_WRITE_CLASSIFIED'] else 'FALSE'}")
    print(f"[gate_vault_boot_side_effect_fence_lane][DEFAULT_BOOT_SIDE_EFFECTS_ALLOWED] {'TRUE' if report['DEFAULT_BOOT_SIDE_EFFECTS_ALLOWED'] else 'FALSE'}")
    print(f"[gate_vault_boot_side_effect_fence_lane][CONTROLLED_RUNTIME_START_STILL_TRUE] {'TRUE' if report['CONTROLLED_RUNTIME_START_STILL_TRUE'] else 'FALSE'}")
    print(f"[gate_vault_boot_side_effect_fence_lane][PORT_8080_PUBLIC_EXPOSURE] {'TRUE' if report['PORT_8080_PUBLIC_EXPOSURE'] else 'FALSE'}")
    print("[gate_vault_boot_side_effect_fence_lane][NO_DELETE] TRUE")
    print("[gate_vault_boot_side_effect_fence_lane][NO_BULK_COPY] TRUE")
    print(f"[gate_vault_boot_side_effect_fence_lane][REPORT] {REPORT_PATH}")
    return 0 if all_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
