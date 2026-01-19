# tests/test_authority_spec_v1.py

"""
No-escape guardrail tests for Authority Tier Spec v1.

If these fail, core governance has drifted from the frozen spec.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from authority_validator import AuthorityContext, spec_v1_allows_mutation
from reality_mode import RealityMode


def test_matrix_matches_spec_v1():
    # DRAFT / IMBUED / DREAM: all tiers may mutate (non-canon as appropriate)
    for mode in (RealityMode.DRAFT, RealityMode.IMBUED, RealityMode.DREAM):
        for tier in (0, 1, 2, 3):
            ctx = AuthorityContext(tier=tier, mode=mode)
            assert spec_v1_allows_mutation(ctx) is True

    # FINALIZED: only Tier 3
    for tier in (0, 1, 2):
        ctx = AuthorityContext(tier=tier, mode=RealityMode.FINALIZED)
        assert spec_v1_allows_mutation(ctx) is False

    ctx = AuthorityContext(tier=3, mode=RealityMode.FINALIZED)
    assert spec_v1_allows_mutation(ctx) is True

    # REPLAY: nobody can mutate
    for tier in (0, 1, 2, 3):
        ctx = AuthorityContext(tier=tier, mode=RealityMode.REPLAY)
        assert spec_v1_allows_mutation(ctx) is False


if __name__ == "__main__":
    test_matrix_matches_spec_v1()
    print("✅ Authority Tier Spec v1 matrix validated")
