from __future__ import annotations

from dataclasses import dataclass

from engain_control.gate_result import GateResult


@dataclass(frozen=True)
class ScriptGateReport:
    script_name: str
    gates: list[GateResult]

    def status(self) -> str:
        if any(gate.passed == "FALSE" for gate in self.gates):
            return "FALSE"
        return "TRUE"


@dataclass(frozen=True)
class ControlCenterReport:
    system_name: str
    scripts: list[ScriptGateReport]

    def status(self) -> str:
        if any(script.status() == "FALSE" for script in self.scripts):
            return "FALSE"
        return "TRUE"

    def all_gates(self) -> list[GateResult]:
        gates: list[GateResult] = []
        for script in self.scripts:
            gates.extend(script.gates)
        return gates