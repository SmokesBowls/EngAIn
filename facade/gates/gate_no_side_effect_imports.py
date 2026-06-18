# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_no_side_effect_imports.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_no_side_effect_imports(packet: dict[str, Any]) -> GateResult:
    """Validate no side effects are present in import attempts."""
    import_attempts = packet.get("import_attempts", [])

    for idx, attempt in enumerate(import_attempts):
        if not attempt.get("side_effects_checked"):
            return GateResult(
                "gate_no_side_effect_imports",
                "FALSE",
                f"Import attempt at index {idx} did not check for side effects",
            )

        if attempt.get("has_side_effects"):
            return GateResult(
                "gate_no_side_effect_imports",
                "FALSE",
                f"Import attempt at index {idx} has side effects",
            )

    return GateResult(
        "gate_no_side_effect_imports",
        "TRUE",
        "No side effects detected in import attempts",
    )