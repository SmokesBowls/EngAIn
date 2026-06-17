# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engain_control/gate_result.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# TRUE    = Claim passed validation.
# FALSE   = Contradiction, authority violation, missing required field, or crash.
# SKIPPED = Optional claim was inspected and absent.
#           No claim was made, so no authority violation occurred.
GateState = Literal["TRUE", "FALSE", "SKIPPED"]


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: GateState
    message: str

    def is_true(self) -> bool:
        return self.passed == "TRUE"

    def is_false(self) -> bool:
        return self.passed == "FALSE"

    def is_skipped(self) -> bool:
        return self.passed == "SKIPPED"