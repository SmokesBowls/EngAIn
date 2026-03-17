"""
ap_core.py - AP Rule Enforcement (Anti-Python)

Axioms: physics, social rules, magic constraints
check_ap(snapshot, delta) -> list[Violation]

Rules are DECLARATIVE, not imperative.
They explain WHY things fail, not just that they failed.
"""

from dataclasses import dataclass
from typing import Dict, List, Callable, Any

@dataclass
class Violation:
    """
    A rule violation detected by AP system.
    
    Represents: "This delta violates this axiom because..."
    """
    rule_id: str           # "no_double_guard"
    message: str           # "Entity already guarding location"
    severity: str          # "error", "warning", "info"
    context: Dict = None   # Extra data for debugging
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}

class ApRule:
    """
    A single AP rule/axiom.
    
    Example: "No entity can guard two locations simultaneously"
    """
    
    def __init__(self, rule_id: str, check_fn: Callable, severity: str = "error"):
        self.rule_id = rule_id
        self.check_fn = check_fn  # fn(snapshot, delta) -> Optional[str]
        self.severity = severity
    
    def check(self, snapshot: Dict, delta: Dict) -> List[Violation]:
        """
        Check if this rule is violated.
        
        Returns: List of violations (empty if rule passes)
        """
        message = self.check_fn(snapshot, delta)
        
        if message:
            return [Violation(
                rule_id=self.rule_id,
                message=message,
                severity=self.severity
            )]
        
        return []

class ApSystem:
    """
    The AP rule enforcement system.
    
    Registers axioms, checks deltas for violations.
    """
    
    def __init__(self):
        self.rules: Dict[str, ApRule] = {}
    
    def register_rule(self, rule_id: str, check_fn: Callable, severity: str = "error"):
        """Register an AP rule"""
        self.rules[rule_id] = ApRule(rule_id, check_fn, severity)
    
    def check_ap(self, snapshot: Dict, delta: Dict) -> List[Violation]:
        """
        Check all AP rules against a proposed delta.
        
        Returns: List of violations (empty if all rules pass)
        """
        violations = []
        
        for rule in self.rules.values():
            rule_violations = rule.check(snapshot, delta)
            violations.extend(rule_violations)
        
        return violations
    
    def is_valid(self, snapshot: Dict, delta: Dict) -> bool:
        """Quick check: does delta violate any rules?"""
        return len(self.check_ap(snapshot, delta)) == 0

# Global AP system (can be per-world later)
_global_ap = ApSystem()

def register_rule(rule_id: str, check_fn: Callable, severity: str = "error"):
    """Register an AP rule globally"""
    _global_ap.register_rule(rule_id, check_fn, severity)

def check_ap(snapshot: Dict, delta: Dict) -> List[Violation]:
    """Check all AP rules"""
    return _global_ap.check_ap(snapshot, delta)

def is_valid(snapshot: Dict, delta: Dict) -> bool:
    """Quick validation check"""
    return _global_ap.is_valid(snapshot, delta)

# Example rules (can be removed/replaced)

def rule_no_negative_health(snapshot: Dict, delta: Dict) -> str:
    """Physical law: health cannot be negative"""
    if "entities" in delta:
        for entity_id, entity_data in delta["entities"].items():
            if "health" in entity_data:
                if entity_data["health"] < 0:
                    return f"Entity {entity_id} health cannot be negative"
    return None

def rule_no_double_guard(snapshot: Dict, delta: Dict) -> str:
    """Social rule: entity cannot guard two locations"""
    # Example implementation (customize for your world)
    guards = delta.get("guards", {})
    guard_counts = {}
    
    for location, guard_id in guards.items():
        guard_counts[guard_id] = guard_counts.get(guard_id, 0) + 1
        if guard_counts[guard_id] > 1:
            return f"Guard {guard_id} assigned to multiple locations"
    
    return None

# Auto-register example rules
register_rule("no_negative_health", rule_no_negative_health, severity="error")
register_rule("no_double_guard", rule_no_double_guard, severity="warning")
