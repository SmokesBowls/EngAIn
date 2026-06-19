#!/usr/bin/env python3
"""
ap_world_rules.py — AP Rules for World State Transitions

First end-to-end "AP decides, Godot reports" cycle.

These rules evaluate world conditions and emit deltas that change
reality_mode and combat_state. The engine_summary projection picks
up the changes. Godot's EngineSummaryHUD renders them. No Godot
code changes needed.

The loop:
  AP evaluates predicates → emits deltas → kernel applies →
  engine_summary projects → Godot renders

Rule types:
  - Reality transitions: waking ↔ dream ↔ memory ↔ liminal
  - Combat transitions: idle ↔ engaged ↔ dead

All rules are pure, declarative, deterministic.
"""

from typing import Dict, List, Tuple, Any


# ============================================================
# WORLD STATE RULES (Declarative)
# ============================================================

WORLD_RULES: List[Dict] = [

    # ── Reality Mode Rules ─────────────────────────────────────

    {
        "type": "ap_rule",
        "id": "reality_enter_dream",
        "tags": ["reality", "world"],
        "priority": 10,
        "requires": [
            {"pred": "flag", "entity": "player", "key": "reality_mode", "equals": "waking"},
            {"pred": "flag", "entity": "player", "key": "dreaming", "equals": True},
        ],
        "conflicts": [],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "reality_mode", "value": "dream"}
        ],
        "description": "Enter dream state when dreaming flag is set."
    },

    {
        "type": "ap_rule",
        "id": "reality_exit_dream",
        "tags": ["reality", "world"],
        "priority": 10,
        "requires": [
            {"pred": "flag", "entity": "player", "key": "reality_mode", "equals": "dream"},
            {"pred": "flag_not", "entity": "player", "key": "dreaming"},
        ],
        "conflicts": [],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "reality_mode", "value": "waking"}
        ],
        "description": "Return to waking when dreaming flag cleared."
    },

    {
        "type": "ap_rule",
        "id": "reality_enter_memory",
        "tags": ["reality", "world"],
        "priority": 15,
        "requires": [
            {"pred": "flag", "entity": "player", "key": "touching_memory_stone", "equals": True},
        ],
        "conflicts": [
            {"pred": "flag", "entity": "player", "key": "reality_mode", "equals": "memory"},
        ],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "reality_mode", "value": "memory"}
        ],
        "description": "Enter memory mode when touching a memory stone."
    },

    {
        "type": "ap_rule",
        "id": "reality_exit_memory",
        "tags": ["reality", "world"],
        "priority": 15,
        "requires": [
            {"pred": "flag", "entity": "player", "key": "reality_mode", "equals": "memory"},
            {"pred": "flag_not", "entity": "player", "key": "touching_memory_stone"},
        ],
        "conflicts": [],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "reality_mode", "value": "waking"}
        ],
        "description": "Exit memory mode when no longer touching memory stone."
    },

    {
        "type": "ap_rule",
        "id": "reality_enter_liminal",
        "tags": ["reality", "world"],
        "priority": 20,  # Highest — liminal overrides other states
        "requires": [
            {"pred": "stat_gte", "entity": "player", "key": "entropy", "value": 80.0},
        ],
        "conflicts": [
            {"pred": "flag", "entity": "player", "key": "reality_mode", "equals": "liminal"},
        ],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "reality_mode", "value": "liminal"}
        ],
        "description": "Forced liminal state when entropy exceeds threshold."
    },

    {
        "type": "ap_rule",
        "id": "reality_exit_liminal",
        "tags": ["reality", "world"],
        "priority": 20,
        "requires": [
            {"pred": "flag", "entity": "player", "key": "reality_mode", "equals": "liminal"},
            {"pred": "stat_lt", "entity": "player", "key": "entropy", "value": 50.0},
        ],
        "conflicts": [],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "reality_mode", "value": "waking"}
        ],
        "description": "Exit liminal when entropy drops below recovery threshold."
    },

    # ── Combat State Rules ─────────────────────────────────────

    {
        "type": "ap_rule",
        "id": "combat_engage",
        "tags": ["combat", "world"],
        "priority": 10,
        "requires": [
            {"pred": "flag_not_eq", "entity": "player", "key": "combat_state", "value": "engaged"},
            {"pred": "any_hostile_nearby"},
        ],
        "conflicts": [
            {"pred": "stat_lte", "entity": "player", "key": "health", "value": 0},
        ],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "combat_state", "value": "engaged"}
        ],
        "description": "Enter combat when hostiles detected and player alive."
    },

    {
        "type": "ap_rule",
        "id": "combat_disengage",
        "tags": ["combat", "world"],
        "priority": 10,
        "requires": [
            {"pred": "flag", "entity": "player", "key": "combat_state", "equals": "engaged"},
            {"pred": "no_hostile_nearby"},
        ],
        "conflicts": [],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "combat_state", "value": "idle"}
        ],
        "description": "Exit combat when no hostiles remain."
    },

    {
        "type": "ap_rule",
        "id": "combat_death",
        "tags": ["combat", "world"],
        "priority": 30,  # Death overrides everything
        "requires": [
            {"pred": "stat_lte", "entity": "player", "key": "health", "value": 0},
        ],
        "conflicts": [
            {"pred": "flag", "entity": "player", "key": "combat_state", "equals": "dead"},
        ],
        "effects": [
            {"op": "set_flag", "entity": "player", "key": "combat_state", "value": "dead"}
        ],
        "description": "Player dies when health drops to zero."
    },
]


# ============================================================
# PREDICATE EVALUATOR
# ============================================================

def evaluate_predicate(pred: Dict, world: Dict) -> bool:
    """Evaluate a single predicate against world state. Pure."""
    pred_type = pred.get("pred", "")
    entities = world.get("entities", {})

    if pred_type == "flag":
        entity = entities.get(pred.get("entity", ""), {})
        return entity.get("flags", {}).get(pred["key"]) == pred["equals"]

    elif pred_type == "flag_not":
        entity = entities.get(pred.get("entity", ""), {})
        val = entity.get("flags", {}).get(pred["key"])
        return val is None or val is False

    elif pred_type == "flag_not_eq":
        entity = entities.get(pred.get("entity", ""), {})
        return entity.get("flags", {}).get(pred["key"]) != pred.get("value")

    elif pred_type == "stat_gte":
        entity = entities.get(pred.get("entity", ""), {})
        return entity.get("stats", {}).get(pred["key"], 0) >= pred["value"]

    elif pred_type == "stat_lt":
        entity = entities.get(pred.get("entity", ""), {})
        return entity.get("stats", {}).get(pred["key"], 0) < pred["value"]

    elif pred_type == "stat_lte":
        entity = entities.get(pred.get("entity", ""), {})
        val = entity.get("stats", {}).get(pred.get("key"), None)
        if val is None:
            val = entity.get("combat", {}).get(pred.get("key"), 0)
        return val <= pred["value"]

    elif pred_type == "any_hostile_nearby":
        for eid, edata in entities.items():
            if eid == "player":
                continue
            if edata.get("flags", {}).get("hostile", False):
                return True
        return False

    elif pred_type == "no_hostile_nearby":
        for eid, edata in entities.items():
            if eid == "player":
                continue
            if edata.get("flags", {}).get("hostile", False):
                return False
        return True

    return False


# ============================================================
# EFFECT EMITTER
# ============================================================

def emit_effects(effects: List[Dict]) -> List[Dict]:
    """Convert AP effects into world deltas. Pure."""
    deltas = []
    for eff in effects:
        op = eff.get("op", "")
        if op == "set_flag":
            deltas.append({
                "type": "world/set_flag",
                "entity": eff["entity"],
                "key": eff["key"],
                "value": eff["value"]
            })
    return deltas


# ============================================================
# RULE ENGINE
# ============================================================

def evaluate_world_rules(rules: List[Dict], world: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Evaluate AP world rules. Returns (deltas, fired_rules).
    Rules sorted by priority (higher first). First match per tag group wins.
    """
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)
    all_deltas = []
    fired = []
    acted_tags = set()  # Prevent double-fire within same domain

    for rule in sorted_rules:
        # Check if this domain already acted
        rule_tags = set(rule.get("tags", []))
        domain_tags = rule_tags - {"world"}  # "reality" or "combat"
        if domain_tags & acted_tags:
            continue

        # Check conflicts
        conflicts = rule.get("conflicts", [])
        if conflicts and any(evaluate_predicate(c, world) for c in conflicts):
            continue

        # Check requires
        requires = rule.get("requires", [])
        if not requires:
            continue
        if all(evaluate_predicate(r, world) for r in requires):
            deltas = emit_effects(rule.get("effects", []))
            all_deltas.extend(deltas)
            fired.append({"rule_id": rule["id"], "deltas": len(deltas)})
            acted_tags.update(domain_tags)

    return all_deltas, fired


def apply_world_deltas(world: Dict, deltas: List[Dict]) -> Dict:
    """
    Apply world deltas to produce new world state. Pure.
    Creates new dict, never mutates input.
    """
    import copy
    new_world = copy.deepcopy(world)

    for delta in deltas:
        dtype = delta.get("type", "")
        if dtype == "world/set_flag":
            entity_id = delta["entity"]
            if entity_id not in new_world.get("entities", {}):
                new_world.setdefault("entities", {})[entity_id] = {"flags": {}, "stats": {}}
            new_world["entities"][entity_id].setdefault("flags", {})[delta["key"]] = delta["value"]

    return new_world


# ============================================================
# FULL LOOP: evaluate → apply → summarize
# ============================================================

def ap_world_tick(world: Dict) -> Tuple[Dict, List[Dict]]:
    """
    One tick of AP world evaluation.
    Returns (new_world, fired_rules).
    This is the function sim_runtime calls each frame.
    """
    deltas, fired = evaluate_world_rules(WORLD_RULES, world)
    if deltas:
        world = apply_world_deltas(world, deltas)
    return world, fired


# ============================================================
# TESTING — FULL END-TO-END LOOP
# ============================================================

if __name__ == "__main__":
    from engine_summary import get_engine_summary
    import copy

    print("=" * 60)
    print("Testing AP World Rules — End-to-End Loop")
    print("AP decides → kernel applies → summary projects → (Godot renders)")
    print("=" * 60)

    passed = 0

    # ── Test 1: Dream transition ──
    print("\n[Test 1] Reality: waking → dream → waking")
    world = {
        "entities": {
            "player": {
                "flags": {"reality_mode": "waking", "dreaming": False},
                "stats": {"entropy": 10.0},
                "combat": {"health": 100},
                "location": "village"
            }
        },
        "quest": {"quests": {}, "tick": 1.0}
    }

    # Nothing should fire yet
    w1, fired1 = ap_world_tick(copy.deepcopy(world))
    s1 = get_engine_summary(w1, reality_mode=w1["entities"]["player"]["flags"].get("reality_mode", "waking"))
    assert s1["reality_mode"] == "waking"
    assert len(fired1) == 0
    print("  ✅ No rules fire (dreaming=False)")

    # Set dreaming flag → AP should flip to dream
    world["entities"]["player"]["flags"]["dreaming"] = True
    w2, fired2 = ap_world_tick(copy.deepcopy(world))
    rm2 = w2["entities"]["player"]["flags"]["reality_mode"]
    s2 = get_engine_summary(w2, reality_mode=rm2)
    assert rm2 == "dream"
    assert s2["reality_mode"] == "dream"
    assert any(f["rule_id"] == "reality_enter_dream" for f in fired2)
    print("  ✅ AP fired reality_enter_dream → DREAM")
    print("     Summary shows: REALITY=%s" % s2["reality_mode"])

    # Clear dreaming → AP should flip back
    w2["entities"]["player"]["flags"]["dreaming"] = False
    w3, fired3 = ap_world_tick(copy.deepcopy(w2))
    rm3 = w3["entities"]["player"]["flags"]["reality_mode"]
    s3 = get_engine_summary(w3, reality_mode=rm3)
    assert rm3 == "waking"
    assert s3["reality_mode"] == "waking"
    assert any(f["rule_id"] == "reality_exit_dream" for f in fired3)
    print("  ✅ AP fired reality_exit_dream → WAKING")
    passed += 1

    # ── Test 2: Memory stone ──
    print("\n[Test 2] Reality: waking → memory → waking")
    world2 = copy.deepcopy(world)
    world2["entities"]["player"]["flags"]["dreaming"] = False
    world2["entities"]["player"]["flags"]["touching_memory_stone"] = True
    w4, fired4 = ap_world_tick(copy.deepcopy(world2))
    rm4 = w4["entities"]["player"]["flags"]["reality_mode"]
    assert rm4 == "memory"
    assert any(f["rule_id"] == "reality_enter_memory" for f in fired4)
    print("  ✅ AP fired reality_enter_memory → MEMORY")

    w4["entities"]["player"]["flags"]["touching_memory_stone"] = False
    w5, fired5 = ap_world_tick(copy.deepcopy(w4))
    rm5 = w5["entities"]["player"]["flags"]["reality_mode"]
    assert rm5 == "waking"
    print("  ✅ AP fired reality_exit_memory → WAKING")
    passed += 1

    # ── Test 3: Liminal (entropy override) ──
    print("\n[Test 3] Reality: → liminal (entropy > 80)")
    world3 = copy.deepcopy(world)
    world3["entities"]["player"]["flags"]["dreaming"] = False
    world3["entities"]["player"]["stats"]["entropy"] = 85.0
    w6, fired6 = ap_world_tick(copy.deepcopy(world3))
    rm6 = w6["entities"]["player"]["flags"]["reality_mode"]
    assert rm6 == "liminal"
    assert any(f["rule_id"] == "reality_enter_liminal" for f in fired6)
    s6 = get_engine_summary(w6, reality_mode=rm6)
    assert s6["reality_mode"] == "liminal"
    print("  ✅ AP fired reality_enter_liminal → LIMINAL (entropy=85)")
    print("     Summary shows: REALITY=%s" % s6["reality_mode"])

    # Drop entropy → exit
    w6["entities"]["player"]["stats"]["entropy"] = 40.0
    w7, fired7 = ap_world_tick(copy.deepcopy(w6))
    rm7 = w7["entities"]["player"]["flags"]["reality_mode"]
    assert rm7 == "waking"
    print("  ✅ AP fired reality_exit_liminal → WAKING (entropy=40)")
    passed += 1

    # ── Test 4: Combat engage/disengage ──
    print("\n[Test 4] Combat: idle → engaged → idle")
    world4 = copy.deepcopy(world)
    world4["entities"]["player"]["flags"]["combat_state"] = "idle"
    world4["entities"]["goblin"] = {"flags": {"hostile": True}, "location": "village"}

    w8, fired8 = ap_world_tick(copy.deepcopy(world4))
    cs8 = w8["entities"]["player"]["flags"]["combat_state"]
    assert cs8 == "engaged"
    assert any(f["rule_id"] == "combat_engage" for f in fired8)
    s8 = get_engine_summary(w8)
    print("  ✅ AP fired combat_engage → ENGAGED (hostile goblin)")

    # Kill goblin (remove hostile)
    del w8["entities"]["goblin"]
    w9, fired9 = ap_world_tick(copy.deepcopy(w8))
    cs9 = w9["entities"]["player"]["flags"]["combat_state"]
    assert cs9 == "idle"
    assert any(f["rule_id"] == "combat_disengage" for f in fired9)
    print("  ✅ AP fired combat_disengage → IDLE (no hostiles)")
    passed += 1

    # ── Test 5: Death overrides everything ──
    print("\n[Test 5] Combat: death overrides (priority 30)")
    world5 = copy.deepcopy(world4)
    world5["entities"]["player"]["stats"]["health"] = 0
    world5["entities"]["player"]["combat"]["health"] = 0
    w10, fired10 = ap_world_tick(copy.deepcopy(world5))
    cs10 = w10["entities"]["player"]["flags"]["combat_state"]
    assert cs10 == "dead"
    assert any(f["rule_id"] == "combat_death" for f in fired10)
    # Combat engage should NOT have fired (death conflicts)
    assert not any(f["rule_id"] == "combat_engage" for f in fired10)
    s10 = get_engine_summary(w10)
    print("  ✅ AP fired combat_death → DEAD (health=0, overrides engage)")
    passed += 1

    # ── Test 6: Full loop with summary ──
    print("\n[Test 6] Full loop: AP → apply → summary → (Godot renders)")
    world6 = {
        "entities": {
            "player": {
                "flags": {"reality_mode": "waking", "combat_state": "idle"},
                "stats": {"entropy": 90.0, "health": 50},
                "combat": {"health": 50, "max_health": 100},
                "items": {"sword": 1},
                "location": "dark_forest"
            },
            "wolf": {"flags": {"hostile": True}, "location": "dark_forest"},
            "deer": {"flags": {}, "location": "dark_forest"},
        },
        "quest": {
            "quests": {
                "q1": {"status": "active", "title": "Hunt"},
                "q2": {"status": "completed", "title": "Travel"},
            },
            "tick": 120.5
        }
    }

    w_final, fired_final = ap_world_tick(copy.deepcopy(world6))
    rm_final = w_final["entities"]["player"]["flags"]["reality_mode"]
    cs_final = w_final["entities"]["player"]["flags"]["combat_state"]
    summary = get_engine_summary(w_final, delta_time=0.016, reality_mode=rm_final)

    print("  AP fired: %s" % [f["rule_id"] for f in fired_final])
    print("  ---")
    print("  EngineSummary (what Godot sees):")
    print("    TIME:     %.1fs" % summary["game_time"])
    print("    SCENE:    %s" % summary["scene_id"])
    print("    REALITY:  %s" % summary["reality_mode"])
    print("    COMBAT:   %s  HP %.0f/%.0f" % (summary["combat_state"], summary["player_health"], summary["player_health_max"]))
    print("    QUESTS:   %d active  %d done" % (summary["active_quests"], summary["completed_quests"]))
    print("    ENTITIES: %d" % summary["entities_count"])

    assert rm_final == "liminal"  # entropy 90 > 80
    assert cs_final == "engaged"  # wolf is hostile
    assert summary["reality_mode"] == "liminal"
    assert summary["active_quests"] == 1
    assert summary["completed_quests"] == 1
    print("  ✅ Full loop verified: AP decided, summary reflects, Godot would render")
    passed += 1

    # ── Test 7: Determinism ──
    print("\n[Test 7] Determinism")
    wa, fa = ap_world_tick(copy.deepcopy(world6))
    wb, fb = ap_world_tick(copy.deepcopy(world6))
    assert wa["entities"]["player"]["flags"] == wb["entities"]["player"]["flags"]
    assert [f["rule_id"] for f in fa] == [f["rule_id"] for f in fb]
    print("  ✅ Same input → same rules → same state")
    passed += 1

    print("\n" + "=" * 60)
    print(f"AP World Rules: {passed} passed, 0 failed")
    print("=" * 60)

    print("\n--- Rule definitions ---")
    for rule in WORLD_RULES:
        print(f"  [{rule['priority']:2d}] {rule['id']}: {rule['description']}")
