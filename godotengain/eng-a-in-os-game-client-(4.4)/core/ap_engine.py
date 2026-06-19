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
import re
from dataclasses import dataclass
import time
import json
import os
from pathlib import Path

# Canonical module identity guard
CANONICAL_AP_ENGINE_MODULE = "godotengain.engainos.core.ap_engine"


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
            "entropy": {},     # pool_id -> value
            "time_dilation": {} # entity_id -> float (1.0 default)
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

    def get_time_dilation(self, entity: str) -> float:
        return self.state["time_dilation"].get(entity, 1.0)
    
    def set_time_dilation(self, entity: str, value: float):
        self.state["time_dilation"][entity] = value
    
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
        self._warnings: List[str] = []
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
            
            elif "set_time_dilation(" in effect:
                parts = effect.split("(")[1].split(")")[0].split(",")
                if len(parts) >= 1:
                    entity = parts[0].strip()
                    write_keys.add(f"time_dilation.{entity}")
        
        return sorted(write_keys)
    
    # --- Grammar ---
    # flag(entity, "flag")
    RE_FLAG = re.compile(r'^flag\((?P<e>[^,]+),\s*["\'](?P<f>[^"\']+)["\']\)$')
    # stat(entity, "stat") > value
    RE_STAT = re.compile(r'^stat\((?P<e>[^,]+),\s*["\'](?P<s>[^"\']+)["\']\)\s*(?P<op>>|>=|<|<=|==|!=)\s*(?P<v>[\d\.-]+)$')
    # resonance(e1, e2, "stat") > value
    RE_RESONANCE = re.compile(r'^resonance\((?P<e1>[^,]+),\s*(?P<e2>[^,]+),\s*["\'](?P<s>[^"\']+)["\']\)\s*(?P<op>>|>=|<|<=)\s*(?P<v>[\d\.-]+)$')
    # vrel_harmony(e1, e2) > value
    RE_HARMONY = re.compile(r'^vrel_harmony\((?P<e1>[^,]+),\s*(?P<e2>[^,]+)\)\s*(?P<op>>|>=|<|<=)\s*(?P<v>[\d\.-]+)$')
    # location(entity) == "loc"
    RE_LOCATION = re.compile(r'^location\((?P<e>[^)]+)\)\s*==\s*["\'](?P<v>[^"\']+)["\']$')
    # inventory_has(entity, "item", 2)  -- NEW: internal count
    RE_INVENTORY = re.compile(r'^inventory_has\((?P<e>[^,]+),\s*["\'](?P<i>[^"\']+)["\'](?:,\s*(?P<v>\d+))?\)$')
    # time_dilation(entity) > 0.5
    RE_TIME_DILATION_PRED = re.compile(r'^time_dilation\((?P<e>[^)]+)\)\s*(?P<op>>|>=|<|<=|==|!=)\s*(?P<v>[\d\.-]+)$')

    def _eval_predicate(self, pred: str, rule: APInternalRule, context: Dict, trace: Optional[Dict] = None) -> bool:
        """
        Evaluate a single predicate against current state.
        
        Grammar (STRICT):
        - flag(entity, "name")
        - stat(entity, "name") > 10
        - resonance(e1, e2, "name") > 0.8
        - vrel_harmony(e1, e2) > 0.5
        - location(entity) == "loc_id"
        - inventory_has(entity, "item", count)
        """
        pred = pred.strip()

        # 1. flag(e, "f")
        m = self.RE_FLAG.match(pred)
        if m:
            e, f = m.group('e'), m.group('f')
            e = context.get(e, e)
            return self.state_provider.get_flag(e, f)

        # 2. stat(e, "s") op v
        m = self.RE_STAT.match(pred)
        if m:
            e, s, op, v = m.group('e'), m.group('s'), m.group('op'), float(m.group('v'))
            e = context.get(e, e)
            cur = self.state_provider.get_stat(e, s)
            if trace is not None:
                trace[f"stat.{e}.{s}"] = cur
            if op == ">": return cur > v
            if op == ">=": return cur >= v
            if op == "<": return cur < v
            if op == "<=": return cur <= v
            if op == "==": return cur == v
            if op == "!=": return cur != v

        # 3. resonance(e1, e2, "s") op v
        m = self.RE_RESONANCE.match(pred)
        if m:
            e1, e2, s, op, v = m.group('e1'), m.group('e2'), m.group('s'), m.group('op'), float(m.group('v'))
            e1, e2 = context.get(e1, e1), context.get(e2, e2)
            v1, v2 = self.state_provider.get_stat(e1, s), self.state_provider.get_stat(e2, s)
            res = max(0.0, min(1.0, 1.0 - (abs(v1 - v2) / 100.0)))
            if trace is not None:
                trace[f"resonance.{e1}.{e2}.{s}"] = round(res, 3)
            if op == ">": return res > v
            if op == ">=": return res >= v
            if op == "<": return res < v
            if op == "<=": return res <= v

        # 4. vrel_harmony(e1, e2) op v
        m = self.RE_HARMONY.match(pred)
        if m:
            e1, e2, op, v = m.group('e1'), m.group('e2'), m.group('op'), float(m.group('v'))
            e1, e2 = context.get(e1, e1), context.get(e2, e2)
            v1, v2 = self.state_provider.get_stat(e1, "vrel"), self.state_provider.get_stat(e2, "vrel")
            har = max(0.0, min(1.0, 1.0 - abs(v1 - v2)))
            if trace is not None:
                trace[f"harmony.{e1}.{e2}"] = round(har, 3)
            if op == ">": return har > v
            if op == ">=": return har >= v
            if op == "<": return har < v
            if op == "<=": return har <= v

        # 5. location(e) == "v"
        m = self.RE_LOCATION.match(pred)
        if m:
            e, v = m.group('e'), m.group('v')
            e = context.get(e, e)
            return self.state_provider.get_location(e) == v

        # 6. inventory_has(e, "i", v)
        m = self.RE_INVENTORY.match(pred)
        if m:
            e, i, v = m.group('e'), m.group('i'), int(m.group('v') or 1)
            e = context.get(e, e)
            return self.state_provider.get_inventory_count(e, i) >= v

        # 7. time_dilation(e) op v
        m = self.RE_TIME_DILATION_PRED.match(pred)
        if m:
            e, op, v = m.group('e'), m.group('op'), float(m.group('v'))
            e = context.get(e, e)
            cur = self.state_provider.get_time_dilation(e)
            if trace is not None:
                trace[f"time_dilation.{e}"] = round(cur, 3)
            if op == ">": return cur > v
            if op == ">=": return cur >= v
            if op == "<": return cur < v
            if op == "<=": return cur <= v
            if op == "==": return cur == v
            if op == "!=": return cur != v


        
        # Default: unknown predicate
        self._log_warning(f"Unknown or malformed predicate: {pred}")
        return False

    def _log_warning(self, message: str):
        """Accumulated structured warning for the current tick"""
        self._warnings.append(message)
    
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
    
    def _resolve_conflicts(self, eligible_rules: List[APInternalRule]) -> Tuple[List[str], List[Dict]]:
        """
        Resolve conflicts between eligible rules based on write-set reservation.
        Rules are processed in priority order (assumed already sorted).
        
        Returns: (applied_rule_ids, conflict_details)
        """
        would_apply = []
        conflicts = []
        reserved_resources = {} # resource -> rule_id
        
        for rule in eligible_rules:
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
            else:
                # Success - reserve resources and apply
                would_apply.append(rule.id)
                for resource in rule.write_set:
                    reserved_resources[resource] = rule.id
                    
        return would_apply, conflicts
    
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
        
        # set_time_dilation(entity, value)
        elif effect.startswith("set_time_dilation("):
            parts = effect.split("(")[1].split(")")[0].split(",")
            if len(parts) >= 2:
                entity = parts[0].strip()
                value = float(parts[1].strip())
                if entity in context:
                    entity = context[entity]
                self.state_provider.set_time_dilation(entity, value)
    
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
        computed = {}
        for pred in rule.requires:
            satisfied = self._eval_predicate(pred, rule, context, trace=computed)
            pred_key = self._predicate_to_string(pred)
            predicate_results[pred_key] = satisfied
            if not satisfied:
                blocked_by.append(pred_key)

        # Check conflicts
        for pred in rule.conflicts:
            triggered = self._eval_predicate(pred, rule, context, trace=computed)
            if triggered:
                pred_key = self._predicate_to_string(pred)
                blocked_by.append(f"Conflict: {pred_key}")

        eligible = len(blocked_by) == 0

        return {
            "type": "ap_rule_explanation",
            "rule_id": rule_id,
            "eligible": eligible,
            "blocked_by": blocked_by,
            "predicate_results": predicate_results,
            "computed": computed,
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
        # 0. Reset warnings for new simulation
        self._warnings = []

        # 1. Get all rules in priority order (highest first)
        sorted_rules = sorted(self._rules.values(), key=lambda r: r.priority, reverse=True)
        
        would_apply = []
        would_block = []
        conflicts = []
        explanations = {}
        
        # 2. Filter rules by eligibility and handle resource conflicts
        eligible_rules = []
        for rule in sorted_rules:
            explanation = self.evaluate_rule_explain(rule.id, context)
            explanations[rule.id] = explanation
            
            if not explanation["eligible"]:
                would_block.append(rule.id)
            else:
                eligible_rules.append(rule)
        
        # 3. Resolve resource-level conflicts
        would_apply, tick_conflicts = self._resolve_conflicts(eligible_rules)
        
        # 4. Update would_block and conflicts list
        applied_set = set(would_apply)
        for rule_id in [r.id for r in eligible_rules]:
            if rule_id not in applied_set:
                would_block.append(rule_id)
        
        conflicts.extend(tick_conflicts)
        
        return {
            "type": "ap_tick_simulation",
            "would_apply": would_apply,
            "would_block": would_block,
            "conflicts": conflicts,
            "explanations": explanations,
            "warnings": list(self._warnings)
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
            "explanations": plan.get("explanations", {}),
            "warnings": plan.get("warnings", []),
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
        
        # Ensure zon directory exists relative to current file or ROOT
        env_root = os.environ.get("ENGAIN_ROOT")
        if env_root:
            root_dir = Path(env_root).resolve()
        else:
            core_dir = Path(__file__).resolve().parent
            root_dir = core_dir.parent.parent
            
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
        
        # 5. Compare time dilation
        for entity, td in after.get("time_dilation", {}).items():
            before_td = before.get("time_dilation", {}).get(entity, 1.0)
            if before_td != td:
                delta[f"time_dilation.{entity}"] = td
        
        return delta
    
    def read_execution_history(self, limit: int = 20) -> List[Dict]:
        """
        Read raw execution history from zon/timeline.jsonl.
        Returns the latest 'limit' entries.
        """
        # Consistent path resolution
        env_root = os.environ.get("ENGAIN_ROOT")
        if env_root:
            root_dir = Path(env_root).resolve()
        else:
            core_dir = Path(__file__).resolve().parent
            root_dir = core_dir.parent.parent
            
        timeline_path = root_dir / "zon" / "timeline.jsonl"
        
        if not timeline_path.exists():
            return []
        
        try:
            if not timeline_path.exists():
                return []
            with open(timeline_path, "r") as f:
                lines = f.readlines()
            
            # Take last N lines and parse JSON
            entries = []
            for l in lines[-limit:]:
                try:
                    entries.append(json.loads(l))
                except json.JSONDecodeError:
                    continue
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
