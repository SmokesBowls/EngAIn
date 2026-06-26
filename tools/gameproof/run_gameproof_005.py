#!/usr/bin/env python3
"""
EngAIn Game Proof #005

Purpose:
    Prove the seam from Passroom spatial signals to Topologist artifact.

Pipeline:
    #003 Chapterroom scene packet
    -> passroom_bridge.run_pass1_explicit()
    -> pass1_spatial.process_file()
    -> topologist passroom_signal_converter
    -> TopologyValidator
    -> runtime-like game_state_draft wrapper

This script does NOT:
    - call Trixel
    - call Blender
    - call Mechanimation
    - start Godot
    - mutate runtime
    - write accepted game state
    - create final art
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tier3.mettaext.passroom.passroom_bridge import run_pass1_explicit
from tier3.mettaext.passroom.pass1_spatial import process_file as run_pass1_spatial


REPO_ROOT = Path(__file__).resolve().parents[2]

INPUT_SCENE_PACKET = (
    REPO_ROOT
    / "scratch"
    / "gameproof_003"
    / "output"
    / "chapterroom_real"
    / "scene_packets"
    / "chapter.scene_text"
    / "scene.scene_text.scene001.txt"
)

PROOF_ROOT = REPO_ROOT / "scratch" / "gameproof_005"
OUTPUT_DIR = PROOF_ROOT / "output"
PASSROOM_OUT = OUTPUT_DIR / "passroom_real"
SPATIAL_OUT = OUTPUT_DIR / "spatial_real"

PROOF_ID = "gameproof_005"
SCENE_ID = "scene.gameproof_005.passroom_to_topologist"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def inventory_output_files(base: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []

    if not base.exists():
        return files

    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue

        item: dict[str, Any] = {
            "path": str(path.relative_to(REPO_ROOT)),
            "size_bytes": path.stat().st_size,
        }

        if path.suffix.lower() == ".json":
            try:
                parsed = read_json(path)
                item["json_parse_ok"] = True
                if isinstance(parsed, dict):
                    item["json_keys"] = sorted(str(k) for k in parsed.keys())[:30]
            except Exception:
                item["json_parse_ok"] = False

        files.append(item)

    return files


def load_converter_callable() -> Callable[..., Any]:
    """
    Load the topologist converter without assuming the exact function name.

    Preferred names:
      - convert_spatial_signals_to_artifact
      - convert_passroom_signals_to_artifact
      - convert
    """

    module = importlib.import_module("tier2.topologist.artifactroom.passroom_signal_converter")

    for name in [
        "convert_spatial_signals_to_artifact",
        "convert_passroom_signals_to_artifact",
        "convert",
    ]:
        func = getattr(module, name, None)
        if callable(func):
            return func

    available = sorted(
        name for name in dir(module)
        if not name.startswith("_") and callable(getattr(module, name))
    )

    raise RuntimeError(
        "No supported converter callable found in "
        "tier2.topologist.artifactroom.passroom_signal_converter. "
        f"Available callables: {available}"
    )


def normalize_artifact(value: Any) -> dict[str, Any]:
    """
    Convert artifact object/dict into JSON-safe dict for report output.
    """

    if isinstance(value, dict):
        return value

    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        if isinstance(result, dict):
            return result

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)

    raise TypeError(f"Cannot normalize artifact of type {type(value).__name__}")


def run_topology_validator(artifact: Any) -> dict[str, Any]:
    """
    Try known validator paths and normalize the result.

    This is intentionally flexible because the validator API may be class-based
    or function-based depending on the current topologist implementation.
    """

    candidate_modules = [
        "tier2.topologist.reckoningroom.topology_validator",
        "tier2.topologist.topology_validator",
        "tier2.topologist.validator",
        "tier2.topologist.artifactroom.topology_validator",
    ]

    last_error: str | None = None

    for module_name in candidate_modules:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            last_error = f"{module_name}: import failed: {exc}"
            continue

        # Function style
        for function_name in ["validate", "validate_topology", "validate_artifact"]:
            func = getattr(module, function_name, None)
            if callable(func):
                result = func(artifact)
                return normalize_validation_report(result)

        # Class style
        for class_name in ["TopologyValidator", "Validator"]:
            cls = getattr(module, class_name, None)
            if cls is None:
                continue

            validator = cls()
            for method_name in ["validate", "validate_artifact", "run"]:
                method = getattr(validator, method_name, None)
                if callable(method):
                    result = method(artifact)
                    return normalize_validation_report(result)

    raise RuntimeError(f"No supported TopologyValidator API found. Last error: {last_error}")


def normalize_validation_report(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        report = dict(value)
    elif hasattr(value, "to_dict") and callable(value.to_dict):
        report = value.to_dict()
    elif hasattr(value, "__dict__"):
        report = dict(value.__dict__)
    else:
        report = {"raw_result": repr(value)}

    # Normalize common fields.
    passed = report.get("passed")
    if passed is None:
        passed = report.get("ok")
    if passed is None:
        violations = report.get("violations", [])
        passed = not violations

    violations = report.get("violations", [])
    if violations is None:
        violations = []

    checks_run = report.get("checks_run", report.get("check_count", None))

    return {
        "passed": bool(passed),
        "checks_run": checks_run,
        "violations": violations,
        "raw_report": report,
    }


def call_converter(func: Callable[..., Any], spatial_payload: dict[str, Any]) -> Any:
    """
    Call converter with likely supported signatures.
    """

    attempts: list[tuple[str, Callable[[], Any]]] = [
        (
            "payload_kwargs",
            lambda: func(
                spatial_payload=spatial_payload,
                artifact_id="topo.gameproof_005.passroom_spatial",
                scene_id=SCENE_ID,
            ),
        ),
        (
            "payload_positional_with_ids",
            lambda: func(
                spatial_payload,
                "topo.gameproof_005.passroom_spatial",
                SCENE_ID,
            ),
        ),
        (
            "payload_only",
            lambda: func(spatial_payload),
        ),
    ]

    errors: list[str] = []

    for label, attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            errors.append(f"{label}: {exc}")

    raise RuntimeError("Could not call converter. Attempts:\n" + "\n".join(errors))


def build_runtime_payload(
    pass1_result: dict[str, Any],
    spatial_result: dict[str, Any],
    topology_artifact: dict[str, Any],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "packet_type": "game_state_draft",
        "proof_id": PROOF_ID,
        "scene_id": SCENE_ID,
        "status": "DRAFT_NOT_ACCEPTED",
        "created_at": utc_now(),
        "runtime_mutation_allowed": False,
        "source_scene_packet": str(INPUT_SCENE_PACKET.relative_to(REPO_ROOT)),
        "chain": [
            "chapterroom_scene_packet",
            "passroom_pass1_explicit",
            "passroom_pass1_spatial",
            "topologist_passroom_signal_converter",
            "topology_validator",
            "game_state_draft",
        ],
        "pass1_result": pass1_result,
        "spatial_result": spatial_result,
        "topology_artifact": topology_artifact,
        "topology_validation_report": validation_report,
        "presentation": {
            "art_assets_required_now": False,
            "placeholder_render_allowed": True,
            "trixel_payload": None,
            "blender_payload": None,
            "mechanimation_payload": None,
        },
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PASSROOM_OUT.mkdir(parents=True, exist_ok=True)
    SPATIAL_OUT.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("EngAIn Game Proof #005 — Passroom to Topologist Seam")
    print("=" * 72)
    print(f"Input : {INPUT_SCENE_PACKET}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    if not INPUT_SCENE_PACKET.exists():
        print("RESULT: FAILED")
        print(f"  - missing #003 scene packet: {INPUT_SCENE_PACKET}")
        print("Run Game Proof #003 first.")
        return 2

    print("[1/6] Running Passroom pass1_explicit bridge")
    pass1_result = run_pass1_explicit(
        scene_file=INPUT_SCENE_PACKET,
        output_dir=PASSROOM_OUT,
    )

    pass1_result_path = OUTPUT_DIR / "pass1_explicit_result.json"
    write_json(pass1_result_path, pass1_result)

    pass1_output_path = Path(pass1_result["output_path"])

    print(f"      row_count: {pass1_result.get('row_count')}")
    print(f"      types    : {pass1_result.get('types')}")
    print(f"      wrote    : {pass1_result_path}")

    print()
    print("[2/6] Running Passroom pass1_spatial")
    spatial_output_path = SPATIAL_OUT / f"{pass1_output_path.stem}.spatial.json"
    spatial_result = run_pass1_spatial(
        pass1_path=pass1_output_path,
        output_path=spatial_output_path,
    )

    spatial_result_path = OUTPUT_DIR / "pass1_spatial_result.json"
    write_json(spatial_result_path, spatial_result)

    spatial_payload = read_json(spatial_output_path)

    print(f"      signal_count: {spatial_payload.get('signal_count')}")
    print(f"      wrote       : {spatial_output_path}")

    print()
    print("[3/6] Converting spatial signals to Topology artifact")
    converter = load_converter_callable()
    artifact_value = call_converter(converter, spatial_payload)
    topology_artifact = normalize_artifact(artifact_value)

    topology_artifact_path = OUTPUT_DIR / "topology_artifact.json"
    write_json(topology_artifact_path, topology_artifact)

    print(f"      wrote: {topology_artifact_path}")

    print()
    print("[4/6] Running TopologyValidator")
    validation_report = run_topology_validator(artifact_value)

    validation_report_path = OUTPUT_DIR / "topology_validation_report.json"
    write_json(validation_report_path, validation_report)

    print(f"      validator_passed: {validation_report.get('passed')}")
    print(f"      violations      : {len(validation_report.get('violations', []))}")
    print(f"      wrote           : {validation_report_path}")

    print()
    print("[5/6] Building runtime-like game_state_draft wrapper")
    runtime_payload = build_runtime_payload(
        pass1_result=pass1_result,
        spatial_result=spatial_result,
        topology_artifact=topology_artifact,
        validation_report=validation_report,
    )

    runtime_path = OUTPUT_DIR / "runtime_payload.json"
    write_json(runtime_path, runtime_payload)

    print(f"      wrote: {runtime_path}")

    print()
    print("[6/6] Validating game proof")
    violations: list[str] = []

    if int(spatial_payload.get("signal_count", 0)) <= 0:
        violations.append("pass1_spatial produced no signals")

    if not validation_report.get("passed"):
        violations.append("TopologyValidator did not pass")

    if validation_report.get("violations"):
        violations.append("TopologyValidator reported violations")

    presentation = runtime_payload["presentation"]

    if presentation["trixel_payload"] is not None:
        violations.append("trixel_payload must be null")

    if presentation["blender_payload"] is not None:
        violations.append("blender_payload must be null")

    if presentation["mechanimation_payload"] is not None:
        violations.append("mechanimation_payload must be null")

    if runtime_payload["runtime_mutation_allowed"] is not False:
        violations.append("runtime_mutation_allowed must be false")

    output_inventory = inventory_output_files(OUTPUT_DIR)

    report = {
        "proof_id": PROOF_ID,
        "passed": not violations,
        "chain": runtime_payload["chain"],
        "input_signal_count": spatial_payload.get("signal_count"),
        "validator_passed": validation_report.get("passed"),
        "validator_violations": validation_report.get("violations", []),
        "violations": violations,
        "notes": [
            "This proof closes the Passroom to Topologist seam.",
            "Passroom emits spatial signals.",
            "Topologist converts spatial signals into topology artifact law.",
            "TopologyValidator validates the artifact.",
            "No Trixel call was made.",
            "No Blender call was made.",
            "No Mechanimation call was made.",
            "No Godot runtime mutation was made.",
            "Payload is a draft only.",
        ],
        "files_written": [
            str(pass1_result_path.relative_to(REPO_ROOT)),
            str(spatial_result_path.relative_to(REPO_ROOT)),
            str(topology_artifact_path.relative_to(REPO_ROOT)),
            str(validation_report_path.relative_to(REPO_ROOT)),
            str(runtime_path.relative_to(REPO_ROOT)),
        ],
        "output_inventory": output_inventory,
    }

    report_path = OUTPUT_DIR / "gameproof_report.json"
    write_json(report_path, report)

    print(f"      wrote: {report_path}")

    if violations:
        print()
        print("RESULT: FAILED")
        for violation in violations:
            print(f"  - {violation}")
        return 2

    print()
    print("RESULT: PASSED")
    print()
    print("EngAIn converted Passroom spatial signals into a validated ProseTopologyArtifact.")
    print("No art lane was required.")
    print("No external sibling tool was required.")
    print("No runtime mutation occurred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
