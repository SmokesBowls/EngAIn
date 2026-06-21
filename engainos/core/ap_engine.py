from __future__ import annotations

from typing import Dict, List, Optional

from engainos.core.ap_core import (
    ApSystem,
    Violation,
    rule_no_double_guard,
    rule_no_negative_health,
)


DEFAULT_RULES_REGISTERED = [
    "no_negative_health",
    "no_double_guard",
]


def register_default_rules(system: Optional[ApSystem] = None) -> ApSystem:
    """
    Register the default EngAInOS AP rules into an ApSystem.

    This function is explicit on purpose.
    ap_core.py defines AP mechanism.
    ap_engine.py assembles EngAInOS default AP policy.
    """

    ap_system = system if system is not None else ApSystem()

    ap_system.register_rule(
        "no_negative_health",
        rule_no_negative_health,
        severity="error",
    )

    ap_system.register_rule(
        "no_double_guard",
        rule_no_double_guard,
        severity="error",
    )

    return ap_system


def build_default_ap_system() -> ApSystem:
    """
    Build a fresh AP system with the default EngAInOS AP rules registered.
    """

    return register_default_rules(ApSystem())


def check_default_ap(snapshot: Dict, delta: Dict) -> List[Violation]:
    """
    Check a snapshot/delta pair against the default EngAInOS AP rule set.
    """

    system = build_default_ap_system()
    return system.check_ap(snapshot, delta)


def is_default_valid(snapshot: Dict, delta: Dict) -> bool:
    """
    Return True only when the default EngAInOS AP rule set finds no violations.
    """

    return len(check_default_ap(snapshot, delta)) == 0
