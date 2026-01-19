# authority_validator.py

"""
Runtime validator for Authority Tier Spec v1.

Provides small, pure functions that assert the
Tier × Reality matrix and determinism constraints.
"""

from dataclasses import dataclass
from typing import Literal

from reality_mode import RealityMode


Tier = Literal[0, 1, 2, 3]


@dataclass(frozen=True)
class AuthorityContext:
    tier: Tier
    mode: RealityMode


def spec_v1_allows_mutation(ctx: AuthorityContext) -> bool:
    """
    Pure function implementing the Authority × Reality matrix.

    Returns True if mutation is permitted in principle
    (AP, complex rules, etc. may still veto).
    """
    mode = ctx.mode
    tier = ctx.tier

    if mode == RealityMode.REPLAY:
        return False

    if mode == RealityMode.FINALIZED:
        return tier == 3

    if mode in (RealityMode.DRAFT, RealityMode.IMBUED, RealityMode.DREAM):
        # DREAM mutations are non-canonical at higher layers
        return True

    # Fail closed for unknown modes
    return False


def assert_spec_v1(ctx: AuthorityContext, accepted: bool) -> None:
    """
    Hard assertion: a gateway/empire decision must match the spec.

    If accepted=True when spec_v1_allows_mutation(ctx) is False,
    this is a violation of the frozen contract.
    """
    allowed = spec_v1_allows_mutation(ctx)
    if accepted and not allowed:
        raise AssertionError(
            f"Authority Tier Spec v1 violation: "
            f"accepted=True but matrix forbids mutation "
            f"(tier={ctx.tier}, mode={ctx.mode.name})"
        )
