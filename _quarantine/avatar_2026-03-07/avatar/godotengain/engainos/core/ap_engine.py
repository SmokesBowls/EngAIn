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
        self.tick_count = 0
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
        Returns detailed diagnostic info per AP spec.
        """
        if rule_id not in self._rules:
            return {
                "type": "ap_rule_explanation",
                "rule_id": rule_id,
                "error": "rule_not_found"
            }
        
        rule = self._rules[rule_id]
        predicate_results = {}
        blocked_by = []

        # Check requirements
        for pred in rule.requires:
            satisfied = self._eval_predicate(pred, rule, context)
            pred_key = self._predicate_to_string(pred)
            predicate_results[pred_key] = satisfied
            if not satisfied:
                blocked_by.append(pred_key)

        eligible = len(blocked_by) == 0

        return {
            "type": "ap_rule_explanation",
            "rule_id": rule_id,
            "eligible": eligible,
            "blocked_by": blocked_by,
            "predicate_results": predicate_results,
            "write_set": rule.write_set
        }

    def _predicate_to_string(self, pred: str) -> str:
        """Prettify internal string predicates for diagnostic output"""
        try:
            if "flag(" in pred:
                # flag(entity, "flag") -> flag.entity.flag
                parts = pred.split("(")[1].split(")")[0].split(",")
                entity = parts[0].strip()
                flag = parts[1].strip().strip('"').strip("'")
                return f"flag.{entity}.{flag}"
            elif "stat(" in pred:
                # stat(entity, "stat") > 10 -> stat.entity.stat > 10
                parts = pred.split("(")[1].split(")")[0].split(",")
                entity = parts[0].strip()
                stat = parts[1].strip().strip('"').strip("'")
                # Get the rest of the comparison
                rest = pred.split(")")[-1].strip()
                return f"stat.{entity}.{stat} {rest}"
            elif "location(" in pred:
                # location(entity) == "loc" -> location.entity == loc
                entity = pred.split("(")[1].split(")")[0].strip()
                rest = pred.split(")")[-1].strip()
                return f"location.{entity} {rest}"
        except:
            pass
        return pred
    
    def simulate_tick(self, context: Dict) -> Dict:
        """
        Simulate what would happen this tick without mutating state.
        Returns a ap_tick_simulation per spec.
        """
        # 1. Get all rules in priority order (highest first)
        sorted_rules = sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)
        
        would_apply = []
        would_block = []
        conflicts = []
        explanations = {}
        
        # Track reserved resources for conflict resolution (write_set overlap)
        reserved_resources = {} # resource -> rule_id
        
        for rule in sorted_rules:
            # 2. Evaluate rule
            explanation = self.evaluate_rule_explain(rule.id, context)
            explanations[rule.id] = explanation
            
            if not explanation["eligible"]:
                would_block.append(rule.id)
                continue
            
            # 3. Check for resource conflicts
            conflict_found = False
            overlap_resources = []
            for resource in rule.write_set:
                if resource in reserved_resources:
                    conflict_found = True
                    overlap_resources.append({
                        "resource": resource,
                        "blocked_by": reserved_resources[resource]
                    })
            
            if conflict_found:
                conflicts.append({
                    "rule_id": rule.id,
                    "overlap": overlap_resources
                })
                would_block.append(rule.id)
            else:
                # 4. Success - reserve resources and apply
                would_apply.append(rule.id)
                for resource in rule.write_set:
                    reserved_resources[resource] = rule.id
        
        return {
            "type": "ap_tick_simulation",
            "would_apply": would_apply,
            "would_block": would_block,
            "conflicts": conflicts,
            "explanations": explanations
        }
    
    def execute_tick(self, context: Dict) -> Dict:
        """
        Execute one tick of the engine.
        1. Simulate to find what would apply
        2. Apply state changes
        3. Log to ZON timeline
        """
        self.tick_count += 1
        
        # Snapshot state before application
        before_state = self.state_provider.snapshot()
        
        # 1. Simulate
        plan = self.simulate_tick(context)
        
        # 2. Apply rules in priority order
        applied_ids = plan["would_apply"]
        for rule_id in applied_ids:
            rule = self._rules[rule_id]
            self._apply_rule(rule, context)
        
        # Snapshot after application
        after_state = self.state_provider.snapshot()
        
        # Calculate final delta
        delta = self._compute_state_delta(before_state, after_state)
        
        # 3. Log to ZON timeline
        log_entry = {
            "tick": self.tick_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "context": context,
            "applied_rules": applied_ids,
            "blocked_rules": plan["would_block"],
            "conflicts": plan["conflicts"],
            "state_delta": delta
        }
        
        self._append_zon_event(log_entry)
        
        return {
            "type": "ap_tick_execution",
            "tick": self.tick_count,
            "applied": applied_ids,
            "delta": delta
        }

    def _append_zon_event(self, entry: Dict):
        """Append event to zon/timeline.jsonl per specification"""
        import os
        from pathlib import Path
        
        # Ensure zon directory exists relative to current file or ROOT
        # In this project ROOT is parent of core
        core_dir = Path(__file__).resolve().parent
        root_dir = core_dir.parent
        zon_dir = root_dir / "zon"
        
        if not zon_dir.exists():
            os.makedirs(zon_dir, exist_ok=True)
            
        timeline_path = zon_dir / "timeline.jsonl"
        
        with open(timeline_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _compute_state_delta(self, before: Dict, after: Dict) -> Dict:
        """Compute what changed between two states"""
        delta = {}
        
        # 1. Compare flags
        for entity, flags in after.get("flags", {}).items():
            before_flags = before.get("flags", {}).get(entity, {})
            for flag, value in flags.items():
                if before_flags.get(flag) != value:
                    delta[f"flag.{entity}.{flag}"] = value
                    
        # 2. Compare stats
        for entity, stats in after.get("stats", {}).items():
            before_stats = before.get("stats", {}).get(entity, {})
            for stat, value in stats.items():
                if before_stats.get(stat) != value:
                    delta[f"stat.{entity}.{stat}"] = value
                    
        # 3. Compare locations
        for entity, loc in after.get("locations", {}).items():
            if before.get("locations", {}).get(entity) != loc:
                delta[f"location.{entity}"] = loc
                
        # 4. Compare inventory
        for entity, inv in after.get("inventory", {}).items():
            before_inv = before.get("inventory", {}).get(entity, {})
            for item, count in inv.items():
                if before_inv.get(item) != count:
                    delta[f"inventory.{entity}.{item}"] = count
        
        return delta
    
    def read_execution_history(self, limit: int = 20) -> List[Dict]:
        """
        Read raw execution history from zon/timeline.jsonl.
        Returns the latest 'limit' entries.
        """
        from pathlib import Path
        
        # Consistent path resolution
        core_dir = Path(__file__).resolve().parent
        root_dir = core_dir.parent
        timeline_path = root_dir / "zon" / "timeline.jsonl"
        
        if not timeline_path.exists():
            return []
        
        try:
            with open(timeline_path, "r") as f:
                lines = f.readlines()
            
            # Take last N lines and parse JSON
            entries = [json.loads(l) for l in lines[-limit:]]
            return entries
        except Exception as e:
            print(f"[APEngine] Error reading history: {e}")
            return []

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
