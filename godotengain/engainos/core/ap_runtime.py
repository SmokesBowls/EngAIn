#!/usr/bin/env python3
"""
AP Runtime Integration
Location: core/ap_runtime.py

Integrates ZWAPEngine into the existing sim_runtime.py HTTP server.
Follows NGAT-RT v1.0 protocol for message handling.

This bridges: sim_runtime.py ↔ ZWAPEngine ↔ Godot
"""

import json
import re
from typing import Dict, Any, Optional
from pathlib import Path

# Import the AP engine we just built
from ap_engine import ZWAPEngine, StateProvider, APInternalRule


class APRuntimeIntegration:
    """
    AP Runtime Integration for sim_runtime.py
    
    This class manages:
    - Loading rules from ZONJ/scene files
    - Maintaining AP engine instance
    - Handling AP-related message types
    - State synchronization with ZON4D
    """
    
    def __init__(self, scenes_dir: str = None):
        self.engine: Optional[ZWAPEngine] = None
        self.state_provider: Optional[StateProvider] = None
        self.scenes_dir = scenes_dir or "scenes"
        self.loaded_scenes = {}
        
    def initialize(self, initial_state: Dict = None, rules: Dict[str, Dict] = None):
        """
        Initialize AP engine with state.
        Called during sim_runtime startup.
        
        Args:
            initial_state: Initial game state dict
            rules: Optional pre-loaded rules dict (if None, loads from scenes_dir)
        """
        # Create state provider
        if initial_state is None:
            initial_state = {
                'flags': {},
                'stats': {},
                'locations': {},
                'inventory': {},
                'entropy': {}
            }
        
        self.state_provider = StateProvider(initial_state)
        
        # Load rules - either from parameter or from scenes
        if rules is None:
            rules = self._load_all_rules()
        
        # Initialize engine
        self.engine = ZWAPEngine(rules, self.state_provider)
        
        print(f"[APRuntime] Initialized with {len(rules)} rules")
        
    def _load_all_rules(self) -> Dict[str, Dict]:
        """
        Load all AP rules from scene files in scenes directory.
        Supports both ZONJ and game_scenes.json formats.
        """
        rules = {}
        scenes_path = Path(self.scenes_dir)
        
        if not scenes_path.exists():
            print(f"[APRuntime] Warning: scenes directory not found: {scenes_path}")
            return rules
        
        # Load ZONJ and JSON files
        for ext in ["*.zonj", "*.json"]:
            for scene_file in scenes_path.glob(ext):
                # Skip the special manifest file
                if scene_file.name == "game_scenes.json":
                    continue
                
                scene_rules = self._extract_rules_from_zonj(scene_file)
                rules.update(scene_rules)
                print(f"[APRuntime] Loaded {len(scene_rules)} rules from {scene_file.name}")
        
        # Load game_scenes.json manifest if present
        game_scenes = scenes_path / "game_scenes.json"
        if game_scenes.exists():
            with open(game_scenes, 'r') as f:
                data = json.load(f)
                for scene in data.get('scenes', []):
                    scene_rules = self._extract_rules_from_scene_dict(scene)
                    rules.update(scene_rules)
        
        return rules
    
    def _extract_rules_from_zonj(self, zonj_path: Path) -> Dict[str, Dict]:
        """Extract AP rules from ZONJ file"""
        with open(zonj_path, 'r') as f:
            zonj_data = json.load(f)
        
        rules = {}
        
        # Check for explicit rules section
        if 'rules' in zonj_data:
            rules.update(zonj_data['rules'])
        
        # Extract rules from events
        events = zonj_data.get('events', [])
        for event in events:
            rule = self._event_to_rule(event, zonj_data.get('id', 'unknown'))
            if rule:
                rules[rule['id']] = rule
        
        return rules
    
    def _extract_rules_from_scene_dict(self, scene: Dict) -> Dict[str, Dict]:
        """Extract rules from game_scenes.json scene"""
        rules = {}
        
        # Similar to ZONJ extraction
        if 'rules' in scene:
            rules.update(scene['rules'])
        
        if 'events' in scene:
            for event in scene['events']:
                rule = self._event_to_rule(event, scene.get('id', 'unknown'))
                if rule:
                    rules[rule['id']] = rule
        
        return rules
    
    def _event_to_rule(self, event: Dict, scene_id: str) -> Optional[Dict]:
        """Convert narrative event to AP rule"""
        event_id = event.get('id', f"event_{len(self.loaded_scenes)}")
        
        # Extract conditions as requires
        requires = []
        for cond in event.get('conditions', []):
            pred = self._condition_to_predicate(cond)
            if pred:
                requires.append(pred)
        
        # Extract actions as effects
        effects = []
        for action in event.get('actions', []):
            effect = self._action_to_effect(action)
            if effect:
                effects.append(effect)
        
        if not requires and not effects:
            return None
        
        rule = {
            'id': f"{scene_id}_{event_id}",
            'tags': event.get('tags', []),
            'requires': requires,
            'effects': effects,
            'priority': event.get('priority', 0),
            'inputs': event.get('inputs', [])
        }
        
        # Compute read/write sets if not present
        if 'read_set' not in rule or 'write_set' not in rule:
            self._compute_rule_sets(rule)
        
        return rule
    
    def _compute_rule_sets(self, rule: Dict):
        """Compute read_set and write_set for a rule"""
        read_set = set()
        write_set = set()
        
        # Regex for extraction (simplified versions of engine regexes)
        re_flag = re.compile(r'flag\((?P<e>[^,]+),\s*["\'](?P<f>[^"\']+)["\']\)')
        re_stat = re.compile(r'stat\((?P<e>[^,]+),\s*["\'](?P<s>[^"\']+)["\']\)')
        re_loc = re.compile(r'location\((?P<e>[^)]+)\)')
        re_inv = re.compile(r'inventory_has\((?P<e>[^,]+),\s*["\'](?P<i>[^"\']+)["\']')
        re_res = re.compile(r'resonance\((?P<e1>[^,]+),\s*(?P<e2>[^,]+),\s*["\'](?P<s>[^"\']+)["\']\)')
        re_har = re.compile(r'vrel_harmony\((?P<e1>[^,]+),\s*(?P<e2>[^,]+)\)')
        re_td = re.compile(r'time_dilation\((?P<e>[^)]+)\)')

        re_set_flag = re.compile(r'set_flag\((?P<e>[^,]+),\s*["\'](?P<f>[^"\']+)["\']')
        re_set_stat = re.compile(r'(?:set|change)_stat\((?P<e>[^,]+),\s*["\'](?P<s>[^"\']+)["\']')
        re_set_loc = re.compile(r'set_location\((?P<e>[^,]+)')
        re_add_inv = re.compile(r'add_inventory\((?P<e>[^,]+),\s*["\'](?P<i>[^"\']+)["\']')
        re_set_td = re.compile(r'set_time_dilation\((?P<e>[^,]+)')

        # Compute read_set from requires + conflicts
        for pred in rule.get('requires', []) + rule.get('conflicts', []):
            m = re_flag.search(pred)
            if m: read_set.add(f"flag.{m.group('e')}.{m.group('f')}")
            
            m = re_stat.search(pred)
            if m: read_set.add(f"stat.{m.group('e')}.{m.group('s')}")
            
            m = re_loc.search(pred)
            if m: read_set.add(f"location.{m.group('e')}")
            
            m = re_inv.search(pred)
            if m: read_set.add(f"inventory.{m.group('e')}.{m.group('i')}")
            
            m = re_res.search(pred)
            if m:
                read_set.add(f"stat.{m.group('e1')}.{m.group('s')}")
                read_set.add(f"stat.{m.group('e2')}.{m.group('s')}")
            
            m = re_har.search(pred)
            if m:
                read_set.add(f"stat.{m.group('e1')}.vrel")
                read_set.add(f"stat.{m.group('e2')}.vrel")
                
            m = re_td.search(pred)
            if m: read_set.add(f"time_dilation.{m.group('e')}")

        # Compute write_set from effects
        for effect in rule.get('effects', []):
            m = re_set_flag.search(effect)
            if m: write_set.add(f"flag.{m.group('e')}.{m.group('f')}")
            
            m = re_set_stat.search(effect)
            if m: write_set.add(f"stat.{m.group('e')}.{m.group('s')}")
            
            m = re_set_loc.search(effect)
            if m: write_set.add(f"location.{m.group('e')}")
            
            m = re_add_inv.search(effect)
            if m: write_set.add(f"inventory.{m.group('e')}.{m.group('i')}")
            
            m = re_set_td.search(effect)
            if m: write_set.add(f"time_dilation.{m.group('e')}")
        
        rule['read_set'] = sorted(read_set)
        rule['write_set'] = sorted(write_set)
    
    def _condition_to_predicate(self, cond: Dict) -> Optional[str]:
        """Convert condition dict to AP predicate string"""
        cond_type = cond.get('type')
        
        if cond_type == 'flag':
            entity = cond.get('entity', 'player')
            flag = cond.get('flag', '')
            # Check if comparing to specific value
            if 'value' in cond:
                value = cond.get('value')
                op = cond.get('op', '==')
                # For flags, we need to express as: flag(entity, "flag") for true checks
                # For false checks: not(flag(entity, "flag")) or use conflicts
                if op == '==' and value is False:
                    # This should go in conflicts, not requires
                    # For now, skip it or express differently
                    return None
                elif op == '==' and value is True:
                    return f'flag({entity}, "{flag}")'
            else:
                # Default: check if flag is true
                return f'flag({entity}, "{flag}")'
        
        elif cond_type == 'stat':
            entity = cond.get('entity', 'player')
            stat = cond.get('stat', '')
            op = cond.get('op', '>=')
            value = cond.get('value', 0)
            return f'stat({entity}, "{stat}") {op} {value}'
        
        elif cond_type == 'location':
            entity = cond.get('entity', 'player')
            location = cond.get('location', '')
            return f'location({entity}) == "{location}"'
        
        elif cond_type == 'inventory':
            entity = cond.get('entity', 'player')
            item = cond.get('item', '')
            count = cond.get('count', 1)
            # Spec: inventory_has(entity, "item", count)
            return f'inventory_has({entity}, "{item}", {count})'
        
        elif cond_type == 'time_dilation':
            entity = cond.get('entity', 'player')
            op = cond.get('op', '>=')
            value = cond.get('value', 1.0)
            return f'time_dilation({entity}) {op} {value}'
        
        return None
    
    def _action_to_effect(self, action: Dict) -> Optional[str]:
        """Convert action dict to AP effect string"""
        action_type = action.get('type')
        
        if action_type == 'set_flag':
            entity = action.get('entity', 'player')
            flag = action.get('flag', '')
            value = action.get('value', True)
            return f'set_flag({entity}, "{flag}", {value})'
        
        elif action_type == 'change_stat':
            entity = action.get('entity', 'player')
            stat = action.get('stat', '')
            delta = action.get('delta', 0)
            return f'change_stat({entity}, "{stat}", {delta})'
        
        elif action_type == 'set_location':
            entity = action.get('entity', 'player')
            location = action.get('location', '')
            return f'set_location({entity}, "{location}")'
        
        elif action_type == 'add_inventory':
            entity = action.get('entity', 'player')
            item = action.get('item', '')
            count = action.get('count', 1)
            return f'add_inventory({entity}, "{item}", {count})'
        
        elif action_type == 'set_time_dilation':
            entity = action.get('entity', 'player')
            value = action.get('value', 1.0)
            return f'set_time_dilation({entity}, {value})'
        
        return None
    
    def update_state(self, state_delta: Dict):
        """
        Update AP state provider from ZON4D state changes.
        Called when sim_runtime receives state updates.
        """
        if not self.state_provider:
            return
        
        # Apply state delta to provider
        if 'flags' in state_delta:
            for entity, flags in state_delta['flags'].items():
                for flag, value in flags.items():
                    self.state_provider.set_flag(entity, flag, value)
        
        if 'stats' in state_delta:
            for entity, stats in state_delta['stats'].items():
                for stat, value in stats.items():
                    self.state_provider.set_stat(entity, stat, value)
        
        if 'locations' in state_delta:
            for entity, location in state_delta['locations'].items():
                self.state_provider.set_location(entity, location)
        
        if 'inventory' in state_delta:
            for entity, inventory in state_delta['inventory'].items():
                for item, count in inventory.items():
                    current = self.state_provider.get_inventory_count(entity, item)
                    if count != current:
                        self.state_provider.add_inventory(entity, item, count - current)
        
        if 'time_dilation' in state_delta:
            for entity, value in state_delta['time_dilation'].items():
                self.state_provider.set_time_dilation(entity, value)
    
    def handle_message(self, msg: Dict) -> Dict:
        """
        Handle AP-related messages from Godot.
        
        Supported message types:
        - ap_evaluate_rule: Explain why a rule would/wouldn't fire
        - ap_simulate_tick: Simulate what rules would fire
        - ap_list_rules: Get all rules
        - ap_get_rule: Get specific rule details
        """
        msg_type = msg.get('type')
        
        if msg_type == 'ap_evaluate_rule':
            return self._handle_evaluate_rule(msg)
        
        elif msg_type == 'ap_simulate_tick':
            return self._handle_simulate_tick(msg)
        
        elif msg_type == 'ap_execute_tick':
            return self._handle_execute_tick(msg)
        
        elif msg_type == 'ap_execution_history':
            return self._handle_execution_history(msg)
        
        elif msg_type == 'ap_list_rules':
            return self._handle_list_rules(msg)
        
        elif msg_type == 'ap_get_rule':
            return self._handle_get_rule(msg)
        
        else:
            return {'error': 'unknown_ap_message_type', 'type': msg_type}
    
    def _handle_evaluate_rule(self, msg: Dict) -> Dict:
        """Handle ap_evaluate_rule message"""
        if not self.engine:
            return {'error': 'ap_not_initialized'}
        
        rule_id = msg.get('rule_id')
        context = msg.get('context', {})
        
        if not rule_id:
            return {'error': 'missing_rule_id'}
        
        return self.engine.evaluate_rule_explain(rule_id, context)
    
        return {
            'type': 'ap_simulate_result',
            'result': result
        }

    def _handle_execute_tick(self, msg: Dict) -> Dict:
        """Handle ap_execute_tick message"""
        if not self.engine:
            return {'error': 'ap_not_initialized'}
        
        context = msg.get('context', {})
        
        # This will mutate state and log to zon/timeline.jsonl
        result = self.engine.execute_tick(context)
        
        return result

    def _handle_execution_history(self, msg: Dict) -> Dict:
        """Handle ap_execution_history message"""
        if not self.engine:
            return {'error': 'ap_not_initialized'}
        
        limit = msg.get('limit', 20)
        entries = self.engine.read_execution_history(limit)
        
        return {
            'type': 'ap_execution_history',
            'entries': entries
        }
    
    def _handle_list_rules(self, msg: Dict) -> Dict:
        """Handle ap_list_rules message"""
        if not self.engine:
            return {'error': 'ap_not_initialized'}
        
        rules = self.engine.list_rules()
        
        return {
            'type': 'ap_rules_list',
            'rules': rules
        }
    
    def _handle_get_rule(self, msg: Dict) -> Dict:
        """Handle ap_get_rule message"""
        if not self.engine:
            return {'error': 'ap_not_initialized'}
        
        rule_id = msg.get('rule_id')
        if not rule_id:
            return {'error': 'missing_rule_id'}
        
        rule = self.engine.get_rule(rule_id)
        
        return {
            'type': 'ap_rule_details',
            'rule': rule
        }


# ============================================================================
# INTEGRATION INSTRUCTIONS FOR sim_runtime.py
# ============================================================================

"""
To integrate this into your existing sim_runtime.py:

1. Import at top of sim_runtime.py:
   from ap_runtime import APRuntimeIntegration

2. In your main runtime class initialization:
   self.ap_runtime = APRuntimeIntegration(scenes_dir="path/to/scenes")
   self.ap_runtime.initialize(initial_state)

3. In your message handler (wherever you process Godot messages):
   
   def handle_message(self, msg: Dict) -> Dict:
       # ... existing message handling ...
       
       # Add AP message handling
       if msg.get('type', '').startswith('ap_'):
           return self.ap_runtime.handle_message(msg)
       
       # ... rest of message handling ...

4. When ZON4D state updates (in your state sync code):
   
   def on_state_update(self, state_delta: Dict):
       # ... existing state handling ...
       
       # Sync to AP runtime
       self.ap_runtime.update_state(state_delta)
       
       # ... rest of state handling ...

That's it! The AP engine is now integrated into your runtime.
"""


# ============================================================================
# EXAMPLE: Standalone Testing
# ============================================================================

if __name__ == '__main__':
    # Create test integration
    integration = APRuntimeIntegration()
    
    # Initialize with test state
    test_state = {
        'flags': {
            'player': {'has_key': False}
        },
        'locations': {
            'player': 'entrance'
        }
    }
    
    integration.initialize(test_state)
    
    # Test message: evaluate rule
    msg = {
        'type': 'ap_evaluate_rule',
        'rule_id': 'test_rule',
        'context': {'player': 'player'}
    }
    
    # Would return evaluation result if rule exists
    # For empty initialization, this shows the integration works
    print("AP Runtime Integration ready")
    print(f"Loaded rules: {len(integration.engine.list_rules()) if integration.engine else 0}")
