from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PermitState = Literal["ALLOW", "DENY", "NO_CLAIM"]


@dataclass(frozen=True)
class PermitDecision:
    permit: PermitState
    message: str

    def is_allowed(self) -> bool:
        return self.permit == "ALLOW"

    def is_denied(self) -> bool:
        return self.permit == "DENY"

    def is_no_claim(self) -> bool:
        return self.permit == "NO_CLAIM"