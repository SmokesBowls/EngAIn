# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_no_runtime_entrypoint_import.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_ENTRYPOINTS = {
    "launch_engine",
    "engainos_server",
    "runtime_client",
    "scene_server",
    "godot_adapter",
}


def gate_no_runtime_entrypoint_import(packet: dict[str, Any]) -> GateResult:
    """Validate runtime entrypoints are guarded, not imported."""
    runtime_entrypoints_guarded = packet.get("runtime_entrypoints_guarded")

    if not isinstance(runtime_entrypoints_guarded, list):
        return GateResult(
            "gate_no_runtime_entrypoint_import",
            "FALSE",
            "runtime_entrypoints_guarded must be a list",
        )

    for idx, entry in enumerate(runtime_entrypoints_guarded):
        if not isinstance(entry, dict):
            return GateResult(
                "gate_no_runtime_entrypoint_import",
                "FALSE",
                f"Runtime entrypoint at index {idx} must be a dict",
            )

        entrypoint = entry.get("entrypoint")
        if not isinstance(entrypoint, str) or not entrypoint.strip():
            return GateResult(
                "gate_no_runtime_entrypoint_import",
                "FALSE",
                f"Runtime entrypoint at index {idx} entrypoint must be a non-empty string",
            )

        if entrypoint in FORBIDDEN_ENTRYPOINTS:
            if not entry.get("not_imported_by_design"):
                return GateResult(
                    "gate_no_runtime_entrypoint_import",
                    "FALSE",
                    f"Runtime entrypoint '{entrypoint}' is not marked as not_imported_by_design",
                )

        if not isinstance(entry.get("not_imported_by_design"), bool):
            return GateResult(
                "gate_no_runtime_entrypoint_import",
                "FALSE",
                f"Runtime entrypoint at index {idx} not_imported_by_design must be boolean",
            )

    return GateResult(
        "gate_no_runtime_entrypoint_import",
        "TRUE",
        "Runtime entrypoints are properly guarded",
    )