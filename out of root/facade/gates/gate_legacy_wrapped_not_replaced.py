# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/facade/gates/gate_legacy_wrapped_not_replaced.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


def gate_legacy_wrapped_not_replaced(packet: dict[str, Any]) -> GateResult:
    """Validate legacy modules are wrapped, not replaced."""
    legacy_wrapped = packet.get("legacy_wrapped")

    if not isinstance(legacy_wrapped, list):
        return GateResult(
            "gate_legacy_wrapped_not_replaced",
            "FALSE",
            "legacy_wrapped must be a list",
        )

    for idx, entry in enumerate(legacy_wrapped):
        if not isinstance(entry, dict):
            return GateResult(
                "gate_legacy_wrapped_not_replaced",
                "FALSE",
                f"Legacy entry at index {idx} must be a dict",
            )

        module = entry.get("module")
        if not isinstance(module, str) or not module.strip():
            return GateResult(
                "gate_legacy_wrapped_not_replaced",
                "FALSE",
                f"Legacy entry at index {idx} module must be a non-empty string",
            )

        if not isinstance(entry.get("wrapped"), bool):
            return GateResult(
                "gate_legacy_wrapped_not_replaced",
                "FALSE",
                f"Legacy entry at index {idx} wrapped must be boolean",
            )

        if not isinstance(entry.get("replaced"), bool):
            return GateResult(
                "gate_legacy_wrapped_not_replaced",
                "FALSE",
                f"Legacy entry at index {idx} replaced must be boolean",
            )

        # STRICT: Legacy source must be wrapped, not replaced, and not left unwrapped.
        if entry["wrapped"] is not True:
            return GateResult(
                "gate_legacy_wrapped_not_replaced",
                "FALSE",
                f"Legacy module '{module}' is not wrapped - Facade's promise is 'legacy wrapped, not replaced'",
            )

        if entry["replaced"] is True:
            return GateResult(
                "gate_legacy_wrapped_not_replaced",
                "FALSE",
                f"Legacy module '{module}' is marked as replaced - Facade must wrap, not replace",
            )

    return GateResult(
        "gate_legacy_wrapped_not_replaced",
        "TRUE",
        "Legacy modules are wrapped, not replaced",
    )