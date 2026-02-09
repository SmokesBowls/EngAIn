#!/usr/bin/env python3
"""
ap_quest_rules.py — AP Rule Evaluator for Quest3D

First AP-driven subsystem. Declarative rules control quest lifecycle.
The Quest3D kernel is a dumb state machine — AP rules tell it what to do.

Architecture:
  AP rules (THIS FILE)  →  evaluates predicates against world state
                         →  emits effect deltas
  Quest3D kernel        →  applies deltas (snapshot-in → snapshot-out)
  QuestTracker.gd       →  renders QuestSummary (read-only)

AP Rule Schema (from ZW-AP-SPEC v0.1):
  {
    "type": "ap_rule",
    "id": "rule_id",
    "requires": [predicate_exprs],    # ALL must be true
    "effects": [effect_exprs],         # Deltas to emit
    "conflicts": [predicate_exprs],    # ANY true → vetoed
    "priority": int,                   # Higher runs first
    "tags": ["quest", ...]
  }

Predicates: flag(entity, key) == value, has_item(entity, item, count),
            at_location(entity, loc), quest_status(quest_id) == status
Effects:    activate_quest(id), complete_quest(id), fail_quest(id),
            set_flag(entity, key, value), grant_item(entity, item, count)

Pure functional. No side effects. Returns deltas, never mutates.
"""

from typing import Dict, List, Tuple, Any, Optional


# ============================================================
# AP RULE DEFINITIONS (Declarative — the rules ARE the logic)
# ============================================================

# These rules define the lifecycle for a "collect item" quest type.
# Rule authors write THESE. The engine evaluates them.

QUEST_RULES: List[Dict] = [

    # ── Rule 1: Quest becomes available when preconditions met ──
    {
        "type": "ap_rule",
        "id": "quest_available_to_active",
        "tags": ["quest", "lifecycle"],
        "priority": 10,
        "requires": [
            # Quest exists and is inactive
            {"pred": "quest_status", "quest_id": "$quest_id", "equals": "inactive"},
            # All quest preconditions are satisfied
            {"pred": "quest_preconditions_met", "quest_id": "$quest_id"},
        ],
        "conflicts": [],
        "effects": [
            {"op": "activate_quest", "quest_id": "$quest_id"}
        ],
        "description": "Activate a quest when all its preconditions are satisfied."
    },

    # ── Rule 2: Quest completes when all required objectives met ──
    {
        "type": "ap_rule",
        "id": "quest_objectives_complete",
        "tags": ["quest", "lifecycle"],
        "priority": 20,
        "requires": [
            {"pred": "quest_status", "quest_id": "$quest_id", "equals": "active"},
            {"pred": "all_required_objectives_met", "quest_id": "$quest_id"},
        ],
        "conflicts": [],
        "effects": [
            {"op": "complete_quest", "quest_id": "$quest_id"}
        ],
        "description": "Complete a quest when all required objectives are satisfied."
    },

    # ── Rule 3: Quest fails when failure condition triggers ──
    {
        "type": "ap_rule",
        "id": "quest_failure_check",
        "tags": ["quest", "lifecycle"],
        "priority": 30,  # Higher priority — failure overrides completion
        "requires": [
            {"pred": "quest_status", "quest_id": "$quest_id", "equals": "active"},
            {"pred": "any_failure_condition_met", "quest_id": "$quest_id"},
        ],
        "conflicts": [],
        "effects": [
            {"op": "fail_quest", "quest_id": "$quest_id"}
        ],
        "description": "Fail a quest when any failure condition is met."
    },
]


# ============================================================
# PREDICATE EVALUATOR (Pure functional)
# ============================================================

def evaluate_predicate(pred: Dict, world: Dict, bindings: Dict) -> bool:
    """
    Evaluate a single AP predicate against world state.
    
    Args:
        pred: Predicate definition from rule
        world: Full world state (entities + quest)
        bindings: Variable bindings (e.g. $quest_id → "q_find_sword")
    
    Returns:
        True if predicate is satisfied
    """
    pred_type = pred.get("pred", "")

    if pred_type == "quest_status":
        quest_id = _resolve(pred.get("quest_id", ""), bindings)
        expected = pred.get("equals", "")
        actual = _get_quest_field(world, quest_id, "status")
        return actual == expected

    elif pred_type == "quest_preconditions_met":
        quest_id = _resolve(pred.get("quest_id", ""), bindings)
        quest = _get_quest(world, quest_id)
        if not quest:
            return False
        preconditions = quest.get("preconditions", [])
        if not preconditions:
            return True  # No preconditions = always available
        return all(_eval_condition(c, world) for c in preconditions)

    elif pred_type == "all_required_objectives_met":
        quest_id = _resolve(pred.get("quest_id", ""), bindings)
        quest = _get_quest(world, quest_id)
        if not quest:
            return False
        objectives = quest.get("objectives", [])
        required = [o for o in objectives if not o.get("optional", False)]
        if not required:
            return False  # No objectives = can't complete
        return all(o.get("status") == "satisfied" for o in required)

    elif pred_type == "any_failure_condition_met":
        quest_id = _resolve(pred.get("quest_id", ""), bindings)
        quest = _get_quest(world, quest_id)
        if not quest:
            return False
        failure_conditions = quest.get("failure_conditions", [])
        if not failure_conditions:
            return False
        return any(_eval_condition(c, world) for c in failure_conditions)

    elif pred_type == "flag":
        entity_id = _resolve(pred.get("entity", ""), bindings)
        key = pred.get("key", "")
        expected = pred.get("equals", True)
        entities = world.get("entities", {})
        actual = entities.get(entity_id, {}).get("flags", {}).get(key)
        return actual == expected

    elif pred_type == "has_item":
        entity_id = _resolve(pred.get("entity", ""), bindings)
        item = pred.get("item", "")
        count = pred.get("count", 1)
        entities = world.get("entities", {})
        actual = entities.get(entity_id, {}).get("items", {}).get(item, 0)
        return actual >= count

    elif pred_type == "at_location":
        entity_id = _resolve(pred.get("entity", ""), bindings)
        expected = pred.get("location", "")
        entities = world.get("entities", {})
        actual = entities.get(entity_id, {}).get("location", "")
        return actual == expected

    return False


def _eval_condition(condition: Dict, world: Dict) -> bool:
    """Evaluate a quest condition (from quest definition) against world."""
    ctype = condition.get("type", "")
    entity_id = condition.get("target_entity", "")
    key = condition.get("key", "")
    value = condition.get("value", True)
    entities = world.get("entities", {})
    entity = entities.get(entity_id, {})

    if ctype == "flag_set":
        return entity.get("flags", {}).get(key) == value
    elif ctype == "has_item":
        threshold = value if isinstance(value, (int, float)) else 1
        return entity.get("items", {}).get(key, 0) >= threshold
    elif ctype == "at_location":
        return entity.get("location", "") == value
    elif ctype == "health_above":
        return entity.get("combat", {}).get("health", 0) > value
    elif ctype == "health_below":
        return entity.get("combat", {}).get("health", 0) < value
    elif ctype == "tick_deadline":
        current_tick = world.get("quest", {}).get("tick", 0.0)
        return current_tick > value  # Past deadline = condition met (for failure)
    elif ctype == "quest_complete":
        target = world.get("quest", {}).get("quests", {}).get(key, {})
        return target.get("status") == "completed"
    return False


# ============================================================
# EFFECT EMITTER (Pure — returns deltas, never mutates)
# ============================================================

def emit_effects(effects: List[Dict], bindings: Dict) -> List[Dict]:
    """
    Convert AP rule effects into Quest3D deltas.
    Pure function — returns list of deltas to feed to kernel.
    """
    deltas = []
    for effect in effects:
        op = effect.get("op", "")

        if op == "activate_quest":
            quest_id = _resolve(effect.get("quest_id", ""), bindings)
            deltas.append({"type": "quest/activate", "id": f"ap_{op}_{quest_id}", "quest_id": quest_id})

        elif op == "complete_quest":
            # Direct status override — kernel will accept this
            quest_id = _resolve(effect.get("quest_id", ""), bindings)
            deltas.append({"type": "quest/complete", "id": f"ap_{op}_{quest_id}", "quest_id": quest_id})

        elif op == "fail_quest":
            quest_id = _resolve(effect.get("quest_id", ""), bindings)
            deltas.append({"type": "quest/fail", "id": f"ap_{op}_{quest_id}", "quest_id": quest_id})

        elif op == "set_flag":
            entity = _resolve(effect.get("entity", ""), bindings)
            deltas.append({
                "type": "quest/set_flag", "id": f"ap_{op}",
                "entity": entity, "key": effect.get("key", ""),
                "value": effect.get("value", True)
            })

        elif op == "grant_item":
            entity = _resolve(effect.get("entity", ""), bindings)
            deltas.append({
                "type": "quest/grant_item", "id": f"ap_{op}",
                "entity": entity, "item": effect.get("item", ""),
                "count": effect.get("count", 1)
            })

    return deltas


# ============================================================
# AP RULE ENGINE (Minimal — evaluates rules, emits deltas)
# ============================================================

def evaluate_rules(
    rules: List[Dict],
    world: Dict,
    quest_ids: Optional[List[str]] = None
) -> Tuple[List[Dict], List[Dict]]:
    """
    Evaluate AP rules against current world state.
    
    For rules with $quest_id bindings, evaluates against each quest.
    
    Args:
        rules: List of AP rule definitions
        world: Full world state
        quest_ids: Specific quests to evaluate (None = all)
    
    Returns:
        (deltas, fired_rules) — deltas to feed to kernel, list of rule fires
    """
    all_deltas = []
    fired = []

    # Get quest IDs to evaluate
    if quest_ids is None:
        quest_ids = list(world.get("quest", {}).get("quests", {}).keys())

    # Sort rules by priority (higher first)
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)

    # Track which quests have already been acted on (prevent double-fire)
    acted_quests = set()

    for rule in sorted_rules:
        for quest_id in quest_ids:
            if quest_id in acted_quests:
                continue

            bindings = {"$quest_id": quest_id}

            # Check conflicts first
            conflicts = rule.get("conflicts", [])
            if conflicts and any(evaluate_predicate(c, world, bindings) for c in conflicts):
                continue

            # Check all requires
            requires = rule.get("requires", [])
            if not requires:
                continue
            if all(evaluate_predicate(r, world, bindings) for r in requires):
                # Rule fires!
                deltas = emit_effects(rule.get("effects", []), bindings)
                all_deltas.extend(deltas)
                fired.append({
                    "rule_id": rule["id"],
                    "quest_id": quest_id,
                    "effects_count": len(deltas)
                })
                acted_quests.add(quest_id)

    return all_deltas, fired


# ============================================================
# QUEST SUMMARY (Read-only projection for Godot)
# ============================================================

def get_quest_summaries(world: Dict) -> List[Dict]:
    """
    Generate flat QuestSummary list from world state.
    This is ALL the QuestTracker UI needs. Nothing else.
    
    Returns list of:
        {
            "id": str,
            "title": str,
            "status": str,
            "description": str,
            "progress": float,  # 0.0-1.0
            "objectives_done": int,
            "objectives_total": int,
            "objectives": [{"id": str, "description": str, "status": str, "optional": bool}]
        }
    """
    quests = world.get("quest", {}).get("quests", {})
    summaries = []

    for qid, quest in quests.items():
        objectives = quest.get("objectives", [])
        total = len(objectives)
        done = sum(1 for o in objectives if o.get("status") == "satisfied")
        progress = done / total if total > 0 else 0.0

        summaries.append({
            "id": qid,
            "title": quest.get("title", qid),
            "status": quest.get("status", "inactive"),
            "description": quest.get("description", ""),
            "progress": progress,
            "objectives_done": done,
            "objectives_total": total,
            "objectives": [
                {
                    "id": o.get("id", ""),
                    "description": o.get("description", ""),
                    "status": o.get("status", "pending"),
                    "optional": o.get("optional", False),
                }
                for o in objectives
            ]
        })

    return summaries


# ============================================================
# HELPERS (Pure)
# ============================================================

def _resolve(value: str, bindings: Dict) -> str:
    """Resolve $variable references."""
    if value.startswith("$"):
        return bindings.get(value, value)
    return value


def _get_quest(world: Dict, quest_id: str) -> Optional[Dict]:
    return world.get("quest", {}).get("quests", {}).get(quest_id)


def _get_quest_field(world: Dict, quest_id: str, field: str) -> Any:
    quest = _get_quest(world, quest_id)
    if quest:
        return quest.get(field)
    return None


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Testing AP Quest Rules...")
    print("=" * 60)

    passed = 0

    # ── Setup: world with registered quests ──
    def make_world():
        return {
            "entities": {
                "player": {
                    "flags": {},
                    "items": {},
                    "location": "village",
                    "combat": {"health": 100}
                }
            },
            "quest": {
                "quests": {
                    "q_collect": {
                        "id": "q_collect",
                        "title": "Collect 3 Herbs",
                        "description": "Gather herbs for the healer.",
                        "status": "inactive",
                        "objectives": [
                            {
                                "id": "obj_herbs",
                                "description": "Collect 3 moonlit herbs",
                                "status": "pending",
                                "optional": False,
                                "conditions": [
                                    {"type": "has_item", "target_entity": "player", "key": "moonlit_herb", "value": 3}
                                ]
                            }
                        ],
                        "preconditions": [
                            {"type": "flag_set", "target_entity": "player", "key": "talked_to_healer", "value": True}
                        ],
                        "rewards": [
                            {"type": "set_flag", "target_entity": "player", "key": "healer_quest_done", "value": True}
                        ],
                        "failure_conditions": [],
                        "activated_at_tick": -1.0,
                        "completed_at_tick": -1.0,
                        "failed_at_tick": -1.0,
                    },
                    "q_timed": {
                        "id": "q_timed",
                        "title": "Urgent Message",
                        "description": "Deliver before tick 50.",
                        "status": "active",
                        "objectives": [
                            {
                                "id": "obj_deliver",
                                "description": "Deliver the message",
                                "status": "pending",
                                "optional": False,
                                "conditions": [
                                    {"type": "at_location", "target_entity": "player", "key": "location", "value": "castle"}
                                ]
                            }
                        ],
                        "preconditions": [],
                        "rewards": [],
                        "failure_conditions": [
                            {"type": "tick_deadline", "target_entity": "player", "key": "tick", "value": 50.0}
                        ],
                        "activated_at_tick": 0.0,
                        "completed_at_tick": -1.0,
                        "failed_at_tick": -1.0,
                    }
                },
                "tick": 10.0
            }
        }

    # ── Test 1: Rule doesn't fire when preconditions not met ──
    print("\n[Test 1] Quest stays inactive (precondition not met)")
    world = make_world()
    deltas, fired = evaluate_rules(QUEST_RULES, world)
    assert not any(f["quest_id"] == "q_collect" and f["rule_id"] == "quest_available_to_active" for f in fired)
    print("  ✅ q_collect NOT activated (no talked_to_healer flag)")
    passed += 1

    # ── Test 2: Rule fires when preconditions met ──
    print("\n[Test 2] Quest activates when preconditions met")
    world = make_world()
    world["entities"]["player"]["flags"]["talked_to_healer"] = True
    deltas, fired = evaluate_rules(QUEST_RULES, world)
    assert any(f["quest_id"] == "q_collect" and f["rule_id"] == "quest_available_to_active" for f in fired)
    activate_deltas = [d for d in deltas if d.get("type") == "quest/activate" and d.get("quest_id") == "q_collect"]
    assert len(activate_deltas) == 1
    print("  ✅ AP rule fired: quest_available_to_active → q_collect")
    print("  ✅ Delta emitted: quest/activate")
    passed += 1

    # ── Test 3: Completion rule fires when objectives met ──
    print("\n[Test 3] Quest completes when objectives satisfied")
    world = make_world()
    world["quest"]["quests"]["q_collect"]["status"] = "active"
    world["quest"]["quests"]["q_collect"]["objectives"][0]["status"] = "satisfied"
    deltas, fired = evaluate_rules(QUEST_RULES, world)
    assert any(f["quest_id"] == "q_collect" and f["rule_id"] == "quest_objectives_complete" for f in fired)
    complete_deltas = [d for d in deltas if d.get("type") == "quest/complete"]
    assert len(complete_deltas) == 1
    print("  ✅ AP rule fired: quest_objectives_complete → q_collect")
    print("  ✅ Delta emitted: quest/complete")
    passed += 1

    # ── Test 4: Failure rule fires on deadline ──
    print("\n[Test 4] Quest fails when failure condition met")
    world = make_world()
    world["quest"]["tick"] = 55.0  # Past deadline of 50
    deltas, fired = evaluate_rules(QUEST_RULES, world)
    assert any(f["quest_id"] == "q_timed" and f["rule_id"] == "quest_failure_check" for f in fired)
    fail_deltas = [d for d in deltas if d.get("type") == "quest/fail"]
    assert len(fail_deltas) == 1
    print("  ✅ AP rule fired: quest_failure_check → q_timed (deadline)")
    print("  ✅ Delta emitted: quest/fail")
    passed += 1

    # ── Test 5: Failure takes priority over completion ──
    print("\n[Test 5] Failure priority > completion")
    world = make_world()
    world["quest"]["tick"] = 55.0
    # Make q_timed also have objectives satisfied
    world["quest"]["quests"]["q_timed"]["objectives"][0]["status"] = "satisfied"
    deltas, fired = evaluate_rules(QUEST_RULES, world)
    # Failure should win (priority 30 > 20)
    q_timed_fires = [f for f in fired if f["quest_id"] == "q_timed"]
    assert len(q_timed_fires) == 1
    assert q_timed_fires[0]["rule_id"] == "quest_failure_check"
    print("  ✅ Failure rule (priority 30) beat completion rule (priority 20)")
    passed += 1

    # ── Test 6: QuestSummary generation ──
    print("\n[Test 6] QuestSummary projection")
    world = make_world()
    world["quest"]["quests"]["q_collect"]["status"] = "active"
    summaries = get_quest_summaries(world)
    assert len(summaries) == 2
    collect_sum = next(s for s in summaries if s["id"] == "q_collect")
    assert collect_sum["title"] == "Collect 3 Herbs"
    assert collect_sum["status"] == "active"
    assert collect_sum["progress"] == 0.0
    assert collect_sum["objectives_total"] == 1
    assert collect_sum["objectives"][0]["status"] == "pending"
    timed_sum = next(s for s in summaries if s["id"] == "q_timed")
    assert timed_sum["status"] == "active"
    print("  ✅ Summaries correct (2 quests, proper fields)")
    passed += 1

    # ── Test 7: Determinism ──
    print("\n[Test 7] Determinism")
    import copy
    world = make_world()
    world["entities"]["player"]["flags"]["talked_to_healer"] = True
    d1, f1 = evaluate_rules(QUEST_RULES, copy.deepcopy(world))
    d2, f2 = evaluate_rules(QUEST_RULES, copy.deepcopy(world))
    assert len(d1) == len(d2)
    assert [f["rule_id"] for f in f1] == [f["rule_id"] for f in f2]
    print("  ✅ Same input → same rules fired")
    passed += 1

    # ── Summary ──
    print("\n" + "=" * 60)
    print(f"AP Quest Rules: {passed} passed, 0 failed")
    print("=" * 60)

    print("\n--- Rule definitions ---")
    for rule in QUEST_RULES:
        print(f"  [{rule['priority']:2d}] {rule['id']}: {rule['description']}")
