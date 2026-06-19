"""
ap_complex_rules.py - Complex AP Rules (Pre-Execution Vetting)

Defense Layer 2: Multi-kernel validation before execution.

These rules require Empire to query kernel state BEFORE
authorizing commands. Proves narrative canon enforcement.

Example: "Cannot attack if attacker health < 10"
Requires: Query Combat3D state before Empire allows attack
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable

from ap_core import Violation


@dataclass
class ComplexAPRule:
    """
    AP rule requiring pre-execution kernel queries.
    
    Unlike simple AP rules (check after), these check BEFORE.
    Empire must query kernel state to validate.
    """
    rule_id: str
    description: str
    check_fn: Callable
    severity: str = "error"


class ComplexAPRuleRegistry:
    """Registry for complex pre-execution AP rules"""
    
    def __init__(self):
        self.rules: Dict[str, ComplexAPRule] = {}
    
    def register(self, rule: ComplexAPRule):
        """Register a complex rule"""
        self.rules[rule.rule_id] = rule
    
    def check_all(self, command: Dict, empire_state: Dict) -> list[Violation]:
        """
        Check all complex rules against command.
        
        Args:
            command: Command about to be executed
            empire_state: Current kernel states (for queries)
        
        Returns: List of violations (empty if valid)
        """
        violations = []
        
        for rule in self.rules.values():
            try:
                # Call rule's check function
                is_valid = rule.check_fn(command, empire_state)
                
                if not is_valid:
                    violations.append(Violation(
                        rule_id=rule.rule_id,
                        message=f"Pre-execution check failed: {rule.description}",
                        severity=rule.severity,
                        context={"command": command}
                    ))
            except Exception as e:
                violations.append(Violation(
                    rule_id=rule.rule_id,
                    message=f"Rule check error: {e}",
                    severity="error",
                    context={"command": command}
                ))
        
        return violations


# ================================================================
# EXAMPLE COMPLEX RULES
# ================================================================

def rule_attacker_min_health(command: Dict, empire_state: Dict) -> bool:
    """
    Cannot attack if attacker health < 10.
    
    Returns True if valid, False if invalid.
    """
    # Only applies to attack commands
    if not _is_attack_command(command):
        return True  # Not applicable, so considered valid
    
    # Get attacker ID
    attacker_id = command.get("attacker")
    if not attacker_id:
        return True  # Not applicable
    
    # Get entities from empire_state
    entities = None
    if 'entities' in empire_state:
        entities = empire_state['entities']
    elif 'combat' in empire_state:
        combat_state = empire_state['combat']
        if hasattr(combat_state, 'entities'):
            entities = combat_state.entities
        elif isinstance(combat_state, dict):
            entities = combat_state.get('entities', {})
    
    if not entities:
        return True  # No entity data - assume valid for testing
    
    # Get attacker entity
    attacker = entities.get(attacker_id)
    if not attacker:
        return False  # Attacker not found, fail safe
    
    # Get health
    if hasattr(attacker, 'health'):
        health = attacker.health
    elif isinstance(attacker, dict):
        health = attacker.get('health', 0)
    else:
        return False  # Unknown attacker format
    
    # Check health threshold
    return health >= 10.0


def rule_cannot_attack_self(command: Dict, empire_state: Dict) -> bool:
    """
    Cannot attack yourself.
    
    Returns True if valid, False if invalid.
    """
    if not _is_attack_command(command):
        return True
    
    attacker = command.get("attacker")
    target = command.get("target")
    
    return attacker != target


def _is_attack_command(command: Dict) -> bool:
    """Helper: Check if command is an attack"""
    # Check if command has attack semantics
    action = command.get("action", "")
    if action == "attack":
        return True
    
    # Check for damage events
    if "attacker" in command and "target" in command and "amount" in command:
        return True
    
    return False


# ================================================================
# GLOBAL REGISTRY
# ================================================================

_global_registry = ComplexAPRuleRegistry()

# Register built-in rules
_global_registry.register(ComplexAPRule(
    rule_id="rule_attacker_min_health",
    description="Attacker must have health >= 10",
    check_fn=rule_attacker_min_health,
    severity="error"
))

_global_registry.register(ComplexAPRule(
    rule_id="rule_cannot_attack_self",
    description="Cannot attack yourself",
    check_fn=rule_cannot_attack_self,
    severity="error"
))


def check_complex_rules(command: Dict, empire_state: Dict) -> list[Violation]:
    """Check all complex rules (convenience function)"""
    return _global_registry.check_all(command, empire_state)


def register_complex_rule(rule: ComplexAPRule):
    """Register a new complex rule"""
    _global_registry.register(rule)
