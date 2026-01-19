#!/usr/bin/env python3
"""
EngAIn Bridge - Narrative to Runtime Integration
Location: core/engain_bridge.py

This wires together:
1. Narrative extraction output (Pass1→Pass2→Pass3→ZONJ)
2. AP rule engine (ZWAPEngine)
3. Godot runtime (via HTTP)

Usage:
    python engain_bridge.py --scene path/to/scene.zonj

This demonstrates the complete pipeline:
    Story Text → ZONJ → AP Rules → Game State → Godot Visualization
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Import the AP engine
from ap_engine import ZWAPEngine, StateProvider, APInternalRule


def load_zonj_scene(zonj_path: str) -> Dict:
    """Load ZONJ scene file"""
    with open(zonj_path, 'r') as f:
        return json.load(f)


def extract_rules_from_zonj(zonj_data: Dict) -> Dict[str, Dict]:
    """
    Extract AP rules from ZONJ scene data.
    
    ZONJ format contains:
    - entities: characters, objects, locations
    - events: narrative events with conditions
    - rules: explicit AP rules (if present)
    
    This converts narrative events → AP rules.
    """
    rules = {}
    
    # Check for explicit rules section
    if 'rules' in zonj_data:
        rules.update(zonj_data['rules'])
    
    # Convert narrative events to rules
    events = zonj_data.get('events', [])
    for i, event in enumerate(events):
        rule_id = f"event_{event.get('id', i)}"
        
        # Extract conditions as requires
        conditions = event.get('conditions', [])
        requires = []
        for cond in conditions:
            # Simple condition conversion
            # Example: {"type": "flag", "entity": "player", "flag": "has_key"}
            if cond.get('type') == 'flag':
                entity = cond.get('entity', 'player')
                flag = cond.get('flag', '')
                requires.append(f'flag({entity}, "{flag}")')
            elif cond.get('type') == 'location':
                entity = cond.get('entity', 'player')
                location = cond.get('location', '')
                requires.append(f'location({entity}) == "{location}"')
        
        # Extract effects
        actions = event.get('actions', [])
        effects = []
        for action in actions:
            if action.get('type') == 'set_flag':
                entity = action.get('entity', 'player')
                flag = action.get('flag', '')
                value = action.get('value', True)
                effects.append(f'set_flag({entity}, "{flag}", {value})')
        
        if requires or effects:
            rules[rule_id] = {
                'id': rule_id,
                'tags': event.get('tags', []),
                'requires': requires,
                'effects': effects,
                'priority': event.get('priority', 0)
            }
    
    return rules


def extract_initial_state_from_zonj(zonj_data: Dict) -> Dict:
    """
    Extract initial game state from ZONJ.
    
    Returns state dict with:
    - flags: entity flags
    - stats: entity stats
    - locations: entity positions
    - inventory: entity inventories
    """
    state = {
        'flags': {},
        'stats': {},
        'locations': {},
        'inventory': {}
    }
    
    # Extract entities
    entities = zonj_data.get('entities', [])
    for entity in entities:
        entity_id = entity.get('id', '')
        
        # Flags
        flags = entity.get('flags', {})
        if flags:
            state['flags'][entity_id] = flags
        
        # Stats
        stats = entity.get('stats', {})
        if stats:
            state['stats'][entity_id] = stats
        
        # Location
        location = entity.get('location')
        if location:
            state['locations'][entity_id] = location
        
        # Inventory
        inventory = entity.get('inventory', {})
        if inventory:
            state['inventory'][entity_id] = inventory
    
    return state


def compute_read_write_sets(rule: Dict) -> Dict:
    """
    Compute read/write sets for a rule per ap_rule_parsing_v1_spec.txt
    
    This should ideally be done during extraction, but we compute it here
    for rules that don't have it yet.
    """
    read_set = set()
    write_set = set()
    
    # Compute read_set from requires
    for pred in rule.get('requires', []):
        if 'flag(' in pred:
            # Extract entity and flag: flag(player, "has_key")
            try:
                args = pred.split('(')[1].split(')')[0].split(',')
                entity = args[0].strip()
                flag = args[1].strip().strip('"')
                read_set.add(f"flag.{entity}.{flag}")
            except:
                pass
        
        elif 'stat(' in pred:
            try:
                args = pred.split('(')[1].split(')')[0].split(',')
                entity = args[0].strip()
                stat = args[1].strip().strip('"')
                read_set.add(f"stat.{entity}.{stat}")
            except:
                pass
        
        elif 'location(' in pred:
            try:
                entity = pred.split('(')[1].split(')')[0].strip()
                read_set.add(f"location.{entity}")
            except:
                pass
    
    # Compute write_set from effects
    for effect in rule.get('effects', []):
        if 'set_flag(' in effect:
            try:
                args = effect.split('(')[1].split(')')[0].split(',')
                entity = args[0].strip()
                flag = args[1].strip().strip('"')
                write_set.add(f"flag.{entity}.{flag}")
            except:
                pass
        
        elif 'change_stat(' in effect or 'set_stat(' in effect:
            try:
                args = effect.split('(')[1].split(')')[0].split(',')
                entity = args[0].strip()
                stat = args[1].strip().strip('"')
                write_set.add(f"stat.{entity}.{stat}")
            except:
                pass
    
    rule['read_set'] = sorted(read_set)
    rule['write_set'] = sorted(write_set)
    
    return rule


def demo_narrative_to_runtime(zonj_path: str):
    """
    Full pipeline demonstration:
    1. Load ZONJ from narrative extraction
    2. Extract rules and state
    3. Initialize AP engine
    4. Run sample queries
    5. Simulate tick
    """
    print("="*70)
    print("EngAIn Bridge - Narrative to Runtime Demo")
    print("="*70)
    
    # Step 1: Load ZONJ
    print(f"\n[1/5] Loading ZONJ: {zonj_path}")
    zonj_data = load_zonj_scene(zonj_path)
    print(f"  ✓ Loaded {len(zonj_data.get('entities', []))} entities")
    print(f"  ✓ Found {len(zonj_data.get('events', []))} events")
    
    # Step 2: Extract rules
    print("\n[2/5] Extracting AP rules from narrative")
    rules = extract_rules_from_zonj(zonj_data)
    print(f"  ✓ Extracted {len(rules)} rules")
    
    # Compute read/write sets
    for rule_id, rule in rules.items():
        if not rule.get('read_set') or not rule.get('write_set'):
            compute_read_write_sets(rule)
    
    # Step 3: Extract initial state
    print("\n[3/5] Extracting initial game state")
    initial_state = extract_initial_state_from_zonj(zonj_data)
    print(f"  ✓ {len(initial_state['flags'])} entities with flags")
    print(f"  ✓ {len(initial_state['locations'])} entities with locations")
    
    # Step 4: Initialize AP engine
    print("\n[4/5] Initializing AP engine")
    provider = StateProvider(initial_state)
    engine = ZWAPEngine(rules, provider)
    print(f"  ✓ Loaded {len(engine.list_rules())} rules into AP engine")
    
    # Step 5: Query and simulate
    print("\n[5/5] Running AP queries")
    
    # List all rules
    all_rules = engine.list_rules()
    print(f"  ✓ All rules: {[r['id'] for r in all_rules]}")
    
    # Test with first entity as context
    entities = zonj_data.get('entities', [])
    if entities and all_rules:
        test_entity = entities[0]['id']
        context = {test_entity: test_entity}
        
        # Explain first rule
        first_rule_id = all_rules[0]['id']  # Get the ID, not the dict
        explanation = engine.evaluate_rule_explain(first_rule_id, context)
        print(f"\n  Explanation for '{first_rule_id}':")
        print(f"    Eligible: {explanation.get('eligible', False)}")
        print(f"    Reason: {explanation.get('reason', 'N/A')}")
        for req in explanation.get('requires', []):
            print(f"      - {req['predicate']}: {req['satisfied']}")
        
        # Simulate tick
        simulation = engine.simulate_tick(context)
        print(f"\n  Tick simulation:")
        print(f"    Would apply: {simulation['would_apply']}")
        print(f"    Would block: {simulation['would_block']}")
    
    print("\n" + "="*70)
    print("Demo complete - AP engine operational")
    print("="*70)


def create_test_zonj():
    """
    Create a minimal test ZONJ scene for demonstration.
    This simulates output from Pass1→Pass2→Pass3 pipeline.
    """
    test_scene = {
        "scene_id": "test_scene_01",
        "title": "Test Scene - Door Puzzle",
        "entities": [
            {
                "id": "player",
                "type": "character",
                "flags": {
                    "has_key": False
                },
                "stats": {
                    "health": 100,
                    "xp": 0
                },
                "location": "entrance"
            },
            {
                "id": "door",
                "type": "object",
                "flags": {
                    "is_open": False,
                    "is_locked": True
                },
                "location": "hallway"
            },
            {
                "id": "key",
                "type": "item",
                "location": "table"
            }
        ],
        "events": [
            {
                "id": "pickup_key",
                "tags": ["interaction", "item"],
                "conditions": [
                    {"type": "location", "entity": "player", "location": "table"}
                ],
                "actions": [
                    {"type": "set_flag", "entity": "player", "flag": "has_key", "value": True}
                ],
                "priority": 5
            },
            {
                "id": "unlock_door",
                "tags": ["interaction", "door"],
                "conditions": [
                    {"type": "flag", "entity": "player", "flag": "has_key"},
                    {"type": "location", "entity": "player", "location": "hallway"}
                ],
                "actions": [
                    {"type": "set_flag", "entity": "door", "flag": "is_locked", "value": False}
                ],
                "priority": 10
            }
        ]
    }
    
    # Write to file
    test_path = Path("/tmp/test_scene.zonj")
    with open(test_path, 'w') as f:
        json.dump(test_scene, f, indent=2)
    
    return str(test_path)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        zonj_path = sys.argv[1]
    else:
        print("No ZONJ file provided - creating test scene")
        zonj_path = create_test_zonj()
        print(f"Created test scene: {zonj_path}\n")
    
    demo_narrative_to_runtime(zonj_path)
