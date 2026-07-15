# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_safe_import_contract.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_safe_import_contract(packet: dict[str, Any]) -> GateResult:
    """Validate import_attempts structure proves safe import contract."""
    import_attempts = packet.get("import_attempts")

    if not isinstance(import_attempts, list):
        return GateResult(
            "gate_safe_import_contract",
            "FALSE",
            "import_attempts must be a list",
        )

    for idx, attempt in enumerate(import_attempts):
        if not isinstance(attempt, dict):
            return GateResult(
                "gate_safe_import_contract",
                "FALSE",
                f"Import attempt at index {idx} must be a dict",
            )

        for required_key in ("module", "side_effects_checked", "passed"):
            if required_key not in attempt:
                return GateResult(
                    "gate_safe_import_contract",
                    "FALSE",
                    f"Import attempt at index {idx} missing {required_key}",
                )

        if not isinstance(attempt["module"], str) or not attempt["module"].strip():
            return GateResult(
                "gate_safe_import_contract",
                "FALSE",
                f"Import attempt at index {idx} module must be a non-empty string",
            )

        if not isinstance(attempt["side_effects_checked"], bool):
            return GateResult(
                "gate_safe_import_contract",
                "FALSE",
                f"Import attempt at index {idx} side_effects_checked must be boolean",
            )

        if not isinstance(attempt["passed"], bool):
            return GateResult(
                "gate_safe_import_contract",
                "FALSE",
                f"Import attempt at index {idx} passed must be boolean",
            )

        # STRICT: A facade import attempt that reports passed=false cannot make the board green.
        if attempt["passed"] is not True:
            return GateResult(
                "gate_safe_import_contract",
                "FALSE",
                f"Import attempt at index {idx} reports passed=false - facade cannot bless a failed import",
            )

    return GateResult(
        "gate_safe_import_contract",
        "TRUE",
        "Safe import contract structure is valid and all imports passed",
    )