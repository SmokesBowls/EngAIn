# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engain_control/gate_print.py

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from engain_control.gate_result import GateResult


GateFunction = Callable[[dict[str, Any]], GateResult]


def print_gate(result: GateResult) -> None:
    dots = "." * max(1, 38 - len(result.gate_name))
    print(f"  {result.gate_name} {dots} {result.passed} - {result.message}")


def print_script_result(script_name: str, results: Iterable[GateResult]) -> bool:
    result_list = list(results)

    # SKIPPED is non-failing.
    # A script passes if every gate is TRUE or SKIPPED.
    script_passed = all(
        gate.passed in ("TRUE", "SKIPPED")
        for gate in result_list
    )

    print(f"{script_name} RESULT: {'TRUE' if script_passed else 'FALSE'}")
    print("")

    return script_passed


def run_script_gates(
    script_name: str,
    packet: dict[str, Any],
    gates: list[GateFunction],
) -> bool:
    print(script_name)

    results: list[GateResult] = []

    for gate in gates:
        try:
            result = gate(packet)
        except Exception as exc:
            result = GateResult(
                gate_name=gate.__name__,
                passed="FALSE",
                message=f"Gate crashed: {type(exc).__name__}: {exc}",
            )

        results.append(result)
        print_gate(result)

    return print_script_result(script_name, results)