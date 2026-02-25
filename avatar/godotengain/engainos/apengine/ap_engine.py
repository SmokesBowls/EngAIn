#!/usr/bin/env python3
"""
ZWAPEngine - Anti-Python Rule Engine v1.0
Faithful implementation of ap_manifest_v1.txt and ap_rule_parsing_v1_spec.txt

This is the Python-side AP engine that:
- Loads rules from narrative extraction
- Evaluates predicates deterministically
- Resolves conflicts via write-set analysis
- Applies effects to state
- Exposes query API for inspection

Location: core/ap_engine.py
Authority: ap_manifest_v1.txt, ap_rule_parsing_v1_spec.txt, ap_query_api_v1.txt
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time
import json


@dataclass
class APInternalRule:
    """
    Canonical internal rule structure per ap_rule_parsing_v1_spec.txt
    """
    id: str
    type: str = "ap_rule"
    tags: List[str] = None
    inputs: List[str] = None
    requires: List[str] = None
    conflicts: List[str] = None
    effects: List[str] = None
    priority: int = 0
    read_set: List[str] = None
    write_set: List[str] = None
    
    def __post_init__(self):
        self.tags = self.tags or []
        self.inputs = self.inputs or []
        self.requires = self.requires or []
        self.conflicts = self.conflicts or []
        self.effects = self.effects or []
        self.read_set = self.read_set or []
        self.write_set = self.write_set or []


class StateProvider:
    """
    Provides access to game state for predicate evaluation.
    This is the bridge to ZON/game state.
    """
    
    def __init__(self, initial_state: Optional[Dict] = None):
        self.state = initial_state or {
            "flags": {},      # entity_id -> {flag_name: bool}
            "stats": {},      # entity_id -> {stat_name: value}
            "locations": {},  # entity_id -> location_id
            "inventory": {},  # entity_id -> {item_id: count}
            "entropy": {}     # pool_id -> value
        }
    
    def get_flag(self, entity: str, flag: str) -> bool:
        return self.state["flags"].get(entity, {}).get(flag, False)
    
    def set_flag(self, entity: str, flag: str, value: bool):
        if entity not in self.state["flags"]:
            self.state["flags"][entity] = {}
        self.state["flags"][entity][flag] = value
    
    def get_stat(self, entity: str, stat: str) -> float:
        return self.state["stats"].get(entity, {}).get(stat, 0.0)
    
    def set_stat(self, entity: str, stat: str, value: float):
        if entity not in self.state["stats"]:
            self.state["stats"][entity] = {}
        self.state["stats"][entity][stat] = value
    
    def get_location(self, entity: str) -> Optional[str]:
        return self.state["locations"].get(entity)
    
    def set_location(self, entity: str, location: str):
        self.state["locations"][entity] = location
    
    def get_inventory_count(self, entity: str, item: str) -> int:
        return self.state["inventory"].get(entity, {}).get(item, 0)
    
    def add_inventory(self, entity: str, item: str, count: int = 1):
        if entity not in self.state["inventory"]:
            self.state["inventory"][entity] = {}
        current = self.state["inventory"][entity].get(item, 0)
        self.state["inventory"][entity][item] = current + count
    
    def get_entropy(self, pool: str) -> float:
        return self.state["entropy"].get(pool, 0.0)
    
    def snapshot(self) -> Dict:
        """Create a deep copy for predictive simulation"""
        import copy
        return copy.deepcopy(self.state)
    
    def restore(self, snapshot: Dict):
        """Restore from snapshot"""
        self.state = snapshot


class ZWAPEngine:
    """
    Minimal AP Engine implementing ap_manifest_v1.txt contracts.
    
    Provides:
    - Rule eligibility checking
    - Conflict resolution
    - Effect application
    - Query API for introspection
    - Predictive simulation
    """
    
    def __init__(self, rules: Dict[str, Dict], state_provider: Optional[StateProvider] = None):
        # Core state
        self._rules: Dict[str, APInternalRule] = {}
        self.state_provider = state_provider or StateProvider()
        
        # Execution tracking
        self._last_reserved: Dict[str, str] = {}  # resource_key -> rule_id
        self._recent_fires: List[Tuple[float, str, Dict]] = []  # (timestamp, rule_id, context)
        
        # Load rules
        for rule_id, rule_dict in rules.items():
            self._load_rule(rule_id, rule_dict)
    
    def _load_rule(self, rule_id: str, rule_dict: Dict):
        """Convert rule dict to APInternalRule"""
        rule = APInternalRule(
            id=rule_id,
            tags=rule_dict.get("tags", []),
            inputs=rule_dict.get("inputs", []),
            requires=rule_dict.get("requires", []),
            conflicts=rule_dict.get("conflicts", []),
            effects=rule_dict.get("effects", []),
            priority=rule_dict.get("priority", 0)
        )
        
        # Compute read/write sets
        rule.read_set = self._compute_read_set(rule)
        rule.write_set = self._compute_write_set(rule)
        
        self._rules[rule_id] = rule
    
    def _compute_read_set(self, rule: APInternalRule) -> List[str]:
        """
        Derive read set from requires + conflicts predicates.
        Per ap_rule_parsing_v1_spec.txt
        """
        read_keys = set()
        
        for pred in rule.requires + rule.conflicts:
            # Simple extraction - in production, parse properly
            if "flag(" in pred:
                # flag(entity, "flag_name") -> flag.entity.flag_name
                parts = pred.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 2:
                    entity = parts[0].strip()
                    flag_name = parts[1].strip().strip('"')
                    read_keys.add(f"flag.{entity}.{flag_name}")
            
            elif "stat(" in pred:
                parts = pred.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 2:
                    entity = parts[0].strip()
                    stat_name = parts[1].strip().strip('"')
                    read_keys.add(f"stat.{entity}.{stat_name}")
            
            elif "location(" in pred:
                parts = pred.split("(")[1].split(")")[0]
                entity = parts.strip()
                read_keys.add(f"location.{entity}")
            
            elif "inventory_has(" in pred:
                parts = pred.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 2:
                    entity = parts[0].strip()
                    item = parts[1].strip().strip('"')
                    read_keys.add(f"inventory.{entity}.{item}")
        
        return sorted(read_keys)
    
    def _compute_write_set(self, rule: APInternalRule) -> List[str]:
        """
        Derive write set from effects.
        Per ap_rule_parsing_v1_spec.txt
        """
        write_keys = set()
        
        for effect in rule.effects:
            if "set_flag(" in effect:
                parts = effect.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 2:
                    entity = parts[0].strip()
                    flag_name = parts[1].strip().strip('"')
                    write_keys.add(f"flag.{entity}.{flag_name}")
            
            elif "change_stat(" in effect or "set_stat(" in effect:
                parts = effect.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 2:
                    entity = parts[0].strip()
                    stat_name = parts[1].strip().strip('"')
                    write_keys.add(f"stat.{entity}.{stat_name}")
            
            elif "set_location(" in effect:
                parts = effect.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 1:
                    entity = parts[0].strip()
                    write_keys.add(f"location.{entity}")
            
            elif "add_inventory(" in effect:
                parts = effect.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 2:
                    entity = parts[0].strip()
                    item = parts[1].strip().strip('"')
                    write_keys.add(f"inventory.{entity}.{item}")
        
        return sorted(write_keys)
    
    def _eval_predicate(self, pred: str, rule: APInternalRule, context: Dict) -> bool:
        """
        Evaluate a single predicate against current state.
        
        Supports:
        - flag(entity, "flag_name")
        - stat(entity, "stat_name") > value
        - location(entity) == "location_id"
        - inventory_has(entity, "item", >= count)
        """
        pred = pred.strip()
        
        # flag(entity, "flag_name")
        if pred.startswith("flag("):
            parts = pred.split("(")[1].split(")")[0].split(",")
            if len(parts) >= 2:
                entity = parts[0].strip()
                flag_name = parts[1].strip().strip('"')
                # Resolve entity from context if it's a variable
                if entity in context:
                    entity = context[entity]
                return self.state_provider.get_flag(entity, flag_name)
        
        # stat(entity, "stat_name") > value
        if pred.startswith("stat("):
            # Extract operator
            for op in [">=", "<=", "==", "!=", ">", "<"]:
                if op in pred:
                    left, right = pred.split(op)
                    # Parse left side
                    parts = left.split("(")[1].split(")")[0].split(",")
                    if len(parts) >= 2:
                        entity = parts[0].strip()
                        stat_name = parts[1].strip().strip('"')
                        if entity in context:
                            entity = context[entity]
                        current_value = self.state_provider.get_stat(entity, stat_name)
                        target_value = float(right.strip())
                        
                        # Evaluate comparison
                        if op == ">": return current_value > target_value
                        if op == "<": return current_value < target_value
                        if op == ">=": return current_value >= target_value
                        if op == "<=": return current_value <= target_value
                        if op == "==": return current_value == target_value
                        if op == "!=": return current_value != target_value
        
        # location(entity) == "location_id"
        if pred.startswith("location("):
            if "==" in pred:
                left, right = pred.split("==")
                entity = left.split("(")[1].split(")")[0].strip()
                location_id = right.strip().strip('"')
                if entity in context:
                    entity = context[entity]
                return self.state_provider.get_location(entity) == location_id
        
        # inventory_has(entity, "item", >= count)
        if pred.startswith("inventory_has("):
            for op in [">=", "<=", "==", ">", "<"]:
                if op in pred:
                    parts = pred.split("(")[1].split(op)
                    left_parts = parts[0].split(",")
                    if len(left_parts) >= 2:
                        entity = left_parts[0].strip()
                        item = left_parts[1].strip().strip('"')
                        count = int(parts[1].split(")")[0].strip())
                        if entity in context:
                            entity = context[entity]
                        current = self.state_provider.get_inventory_count(entity, item)
                        
                        if op == ">=": return current >= count
                        if op == "<=": return current <= count
                        if op == "==": return current == count
                        if op == ">": return current > count
                        if op == "<": return current < count
        
        # Default: unknown predicate
        print(f"Warning: Unknown predicate: {pred}")
        return False
    
    def _is_rule_eligible(self, rule: APInternalRule, context: Dict) -> Tuple[bool, Optional[str]]:
        """
        Check if rule is eligible to fire.
        Returns: (eligible, reason_if_not)
        """
        # Check all requires
        for pred in rule.requires:
            if not self._eval_predicate(pred, rule, context):
                return False, f"Failed requirement: {pred}"
        
        # Check conflicts (if any evaluate to true, rule is blocked)
        for pred in rule.conflicts:
            if self._eval_predicate(pred, rule, context):
                return False, f"Conflict: {pred}"
        
        return True, None
    
    def _resolve_conflicts(self, candidates: List[APInternalRule], context: Dict) -> List[APInternalRule]:
        """
        Resolve conflicts between eligible rules.
        Returns rules that can fire without conflicts.
        """
        if not candidates:
            return []
        
        # Group by write targets
        by_target = {}
        for rule in candidates:
            for key in rule.write_set:
                if key not in by_target:
                    by_target[key] = []
                by_target[key].append(rule)
        
        # For each target with multiple writers, pick highest priority
        selected = set()
        for key, rules in by_target.items():
            if len(rules) == 1:
                selected.add(rules[0].id)
            else:
                # Pick highest priority
                best = max(rules, key=lambda r: r.priority)
                selected.add(best.id)
        
        return [r for r in candidates if r.id in selected]
    
    def _apply_rule(self, rule: APInternalRule, context: Dict):
        """
        Apply rule effects to state.
        """
        for effect in rule.effects:
            self._execute_effect(effect, rule, context)
        
        # Log fire
        timestamp = time.time()
        self._recent_fires.append((timestamp, rule.id, context.copy()))
        
        # Update reservations
        for key in rule.write_set:
            self._last_reserved[key] = rule.id
    
    def _execute_effect(self, effect: str, rule: APInternalRule, context: Dict):
        """Execute a single effect"""
        effect = effect.strip()
        
        # set_flag(entity, "flag", value)
        if effect.startswith("set_flag("):
            parts = effect.split("(")[1].split(")")[0].split(",")
            if len(parts) >= 3:
                entity = parts[0].strip()
                flag = parts[1].strip().strip('"')
                value = parts[2].strip().lower() == "true"
                if entity in context:
                    entity = context[entity]
                self.state_provider.set_flag(entity, flag, value)
        
        # set_stat(entity, "stat", value) or change_stat(entity, "stat", delta)
        elif effect.startswith("set_stat(") or effect.startswith("change_stat("):
            parts = effect.split("(")[1].split(")")[0].split(",")
            if len(parts) >= 3:
                entity = parts[0].strip()
                stat = parts[1].strip().strip('"')
                value = float(parts[2].strip())
                if entity in context:
                    entity = context[entity]
                
                if effect.startswith("set_stat"):
                    self.state_provider.set_stat(entity, stat, value)
                else:  # change_stat
                    current = self.state_provider.get_stat(entity, stat)
                    self.state_provider.set_stat(entity, stat, current + value)
        
        # set_location(entity, "location")
        elif effect.startswith("set_location("):
            parts = effect.split("(")[1].split(")")[0].split(",")
            if len(parts) >= 2:
                entity = parts[0].strip()
                location = parts[1].strip().strip('"')
                if entity in context:
                    entity = context[entity]
                self.state_provider.set_location(entity, location)
        
        # add_inventory(entity, "item", count)
        elif effect.startswith("add_inventory("):
            parts = effect.split("(")[1].split(")")[0].split(",")
            if len(parts) >= 2:
                entity = parts[0].strip()
                item = parts[1].strip().strip('"')
                count = int(parts[2].strip()) if len(parts) >= 3 else 1
                if entity in context:
                    entity = context[entity]
                self.state_provider.add_inventory(entity, item, count)
    
    # ========================================================================
    # PUBLIC QUERY API (per ap_query_api_v1.txt)
    # ========================================================================
    
    def list_rules(self) -> List[Dict]:
        """Return all rules with basic info"""
        return [
            {
                "id": r.id,
                "priority": r.priority,
                "tags": r.tags,
                "write_set": r.write_set
            }
            for r in self._rules.values()
        ]
    
    def get_rule(self, rule_id: str) -> Dict:
        """Get full rule details"""
        if rule_id not in self._rules:
            return {}
        
        rule = self._rules[rule_id]
        return {
            "id": rule.id,
            "priority": rule.priority,
            "tags": rule.tags,
            "inputs": rule.inputs,
            "requires": rule.requires,
            "conflicts": rule.conflicts,
            "effects": rule.effects,
            "read_set": rule.read_set,
            "write_set": rule.write_set
        }
    
    def evaluate_rule_explain(self, rule_id: str, context: Dict) -> Dict:
        """
        Explain why a rule would/wouldn't fire.
        Returns detailed diagnostic info.
        """
        if rule_id not in self._rules:
            return {"error": "Rule not found", "rule_id": rule_id}
        
        rule = self._rules[rule_id]
        eligible, reason = self._is_rule_eligible(rule, context)
        
        return {
            "rule_id": rule_id,
            "eligible": eligible,
            "reason": reason,
            "requires": [
                {
                    "predicate": pred,
                    "satisfied": self._eval_predicate(pred, rule, context)
                }
                for pred in rule.requires
            ],
            "conflicts": [
                {
                    "predicate": pred,
                    "triggered": self._eval_predicate(pred, rule, context)
                }
                for pred in rule.conflicts
            ],
            "write_set": rule.write_set
        }
    
    def simulate_tick(self, context: Dict) -> Dict:
        """
        Simulate what would happen this tick without mutating state.
        Returns predictive analysis.
        """
        # Save current state
        snapshot = self.state_provider.snapshot()
        
        try:
            # Find eligible rules
            eligible = []
            blocked = []
            
            for rule in self._rules.values():
                is_eligible, reason = self._is_rule_eligible(rule, context)
                if is_eligible:
                    eligible.append(rule)
                else:
                    blocked.append({
                        "rule_id": rule.id,
                        "reason": reason
                    })
            
            # Resolve conflicts
            would_apply = self._resolve_conflicts(eligible, context)
            
            # Apply to state
            for rule in would_apply:
                self._apply_rule(rule, context)
            
            # Capture state delta
            new_state = self.state_provider.snapshot()
            
            return {
                "would_apply": [r.id for r in would_apply],
                "would_block": blocked,
                "conflicts": [],  # TODO: detailed conflict info
                "state_delta": self._compute_state_delta(snapshot, new_state)
            }
        
        finally:
            # Restore state
            self.state_provider.restore(snapshot)
    
    def _compute_state_delta(self, before: Dict, after: Dict) -> Dict:
        """Compute what changed between two states"""
        delta = {}
        
        # Compare flags
        for entity in after["flags"]:
            if entity not in before["flags"]:
                delta[f"flags.{entity}"] = after["flags"][entity]
            else:
                for flag, value in after["flags"][entity].items():
                    if before["flags"][entity].get(flag) != value:
                        delta[f"flags.{entity}.{flag}"] = value
        
        # Similar for stats, location, inventory...
        # (simplified for now)
        
        return delta
    
    def recent_rule_fires(self, limit: int = 10) -> List[Dict]:
        """Get recent rule firings"""
        recent = self._recent_fires[-limit:]
        return [
            {
                "timestamp": ts,
                "rule_id": rule_id,
                "context": ctx
            }
            for ts, rule_id, ctx in recent
        ]


# ============================================================================
# INTEGRATION HELPER: Load rules from game scene JSON
# ============================================================================

def load_rules_from_scene(scene_path: str) -> Dict[str, Dict]:
    """
    Load AP rules from game scene JSON.
    This bridges the narrative extraction output → AP engine.
    """
    with open(scene_path, 'r') as f:
        scene_data = json.load(f)
    
    # Extract rules from scene
    # Format depends on your extraction pipeline output
    rules = scene_data.get("rules", {})
    
    return rules


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Create engine with test rules
    test_rules = {
        "open_door": {
            "id": "open_door",
            "inputs": ["player", "door"],
            "requires": [
                'flag(player, "has_key")',
                'location(player) == "door_location"'
            ],
            "effects": [
                'set_flag(door, "is_open", true)',
                'add_inventory(player, "key", -1)'
            ],
            "priority": 10,
            "tags": ["interaction", "door"]
        }
    }
    
    engine = ZWAPEngine(test_rules)
    
    # Set up test state
    engine.state_provider.set_flag("player_1", "has_key", True)
    engine.state_provider.set_location("player_1", "door_location")
    
    # Test rule evaluation
    context = {"player": "player_1", "door": "door_1"}
    result = engine.evaluate_rule_explain("open_door", context)
    print("Rule explanation:", json.dumps(result, indent=2))
    
    # Test simulation
    sim_result = engine.simulate_tick(context)
    print("\nSimulation result:", json.dumps(sim_result, indent=2))
