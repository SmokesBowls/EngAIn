#!/usr/bin/env python3
"""
inventory3d_mr.py - Pure Functional Inventory Kernel (EngAIn)

Based on Zork's inventory model:
- Container + constraints + visibility rules
- Weight limit (LOAD-ALLOWED)
- Count limit (FUMBLE-NUMBER)
- Recursive weight calculation
- Worn items (reduced weight)

Architecture:
- Input: snapshot_in (immutable state)
- Input: deltas (inventory actions)
- Output: snapshot_out (new state)
- Output: alerts (behavior/UI triggers)

NO SIDE EFFECTS. Pure function.
"""

from typing import Dict, Any, List, Tuple, Set

# ============================================================
# CONSTANTS (Zork-style constraints)
# ============================================================

LOAD_MAX = 100  # Base max carrying capacity
FUMBLE_NUMBER = 7  # Max item count before fumble

WORN_WEIGHT_REDUCTION = 0.9  # Worn items weigh 90% less (Zork: count as 1 instead of full)

# ============================================================
# PURE FUNCTIONS (No State Mutation)
# ============================================================

def calculate_size(item_data: Dict) -> int:
    """
    Item's inherent size (P?SIZE in Zork).
    """
    return item_data.get("size", 5)


def calculate_weight_recursive(
    item_id: str,
    all_items: Dict[str, Dict],
    holder_id: str = None
) -> int:
    """
    Zork's recursive weight calculation:
    - size(obj) + Σ weight(child)
    - Exception: worn items on PLAYER count as reduced weight
    
    Args:
        item_id: Item to calculate weight for
        all_items: All items in the world
        holder_id: Entity holding this item (for worn check)
    
    Returns:
        Total recursive weight
    """
    item = all_items.get(item_id, {})
    
    # Start with inherent size
    weight = calculate_size(item)
    
    # Add children's weight
    children = item.get("children", [])
    for child_id in children:
        child = all_items.get(child_id, {})
        
        # Worn items weigh less (Zork: count as 1)
        if holder_id and child.get("worn", False):
            weight += int(calculate_weight_recursive(child_id, all_items, holder_id) * (1 - WORN_WEIGHT_REDUCTION))
        else:
            weight += calculate_weight_recursive(child_id, all_items, holder_id)
    
    return weight


def calculate_carry_count(entity_id: str, all_items: Dict[str, Dict]) -> int:
    """
    Zork's CCOUNT: count direct children, skip worn items.
    
    Returns:
        Number of non-worn items carried
    """
    count = 0
    for item_id, item_data in all_items.items():
        if item_data.get("held_by") == entity_id:
            if not item_data.get("worn", False):
                count += 1
    return count


def is_listable(item_data: Dict) -> bool:
    """
    Zork's visibility gating:
    - Not INVISIBLE
    - Not NDESCBIT (no-describe)
    """
    if item_data.get("invisible", False):
        return False
    if item_data.get("no_describe", False):
        return False
    return True


def get_inventory_list(entity_id: str, all_items: Dict[str, Dict]) -> List[str]:
    """
    Get listable items in inventory.
    
    Returns:
        List of item IDs that should be visible
    """
    inventory = []
    for item_id, item_data in all_items.items():
        if item_data.get("held_by") == entity_id:
            if is_listable(item_data):
                inventory.append(item_id)
    return inventory


# ============================================================
# MR KERNEL ENTRY POINT
# ============================================================

def step_inventory(
    snapshot_in: Dict[str, Any],
    deltas: List[Dict[str, Any]],
    dt: float
) -> Tuple[Dict[str, Any], List[Dict], List[Dict]]:
    """
    Pure functional inventory resolution.
    
    Args:
        snapshot_in: Immutable world state
        deltas: Inventory actions to apply
        dt: Time delta (unused for inventory)
    
    Returns:
        (snapshot_out, accepted_deltas, alerts)
    """
    # Deep copy to ensure immutability
    snapshot_out = {
        "inventory3d": {
            "entities": {},
            "items": {}
        }
    }
    
    # Extract inventory state from input
    inv_in = snapshot_in.get("inventory3d", {})
    entities_in = inv_in.get("entities", {})
    items_in = inv_in.get("items", {})
    
    # Copy existing state
    for eid, edata in entities_in.items():
        snapshot_out["inventory3d"]["entities"][eid] = edata.copy()
    
    for iid, idata in items_in.items():
        snapshot_out["inventory3d"]["items"][iid] = idata.copy()
    
    accepted = []
    alerts = []
    
    # Process each delta
    for delta in deltas:
        delta_type = delta.get("type")
        payload = delta.get("payload", {})
        
        if delta_type == "inventory3d/take":
            result = _handle_take(
                snapshot_out["inventory3d"]["entities"],
                snapshot_out["inventory3d"]["items"],
                payload,
                alerts
            )
            if result:
                accepted.append(delta)
        
        elif delta_type == "inventory3d/drop":
            result = _handle_drop(
                snapshot_out["inventory3d"]["entities"],
                snapshot_out["inventory3d"]["items"],
                payload,
                alerts
            )
            if result:
                accepted.append(delta)
        
        elif delta_type == "inventory3d/wear":
            result = _handle_wear(
                snapshot_out["inventory3d"]["items"],
                payload,
                alerts
            )
            if result:
                accepted.append(delta)
        
        elif delta_type == "inventory3d/remove":
            result = _handle_remove(
                snapshot_out["inventory3d"]["items"],
                payload,
                alerts
            )
            if result:
                accepted.append(delta)
    
    # Update entity weights and counts
    for eid in snapshot_out["inventory3d"]["entities"].keys():
        _update_entity_capacity(
            eid,
            snapshot_out["inventory3d"]["entities"],
            snapshot_out["inventory3d"]["items"],
            alerts
        )
    
    return snapshot_out, accepted, alerts


# ============================================================
# DELTA HANDLERS (Internal)
# ============================================================

def _handle_take(
    entities: Dict[str, Dict],
    items: Dict[str, Dict],
    payload: Dict[str, Any],
    alerts: List[Dict]
) -> bool:
    """
    Handle TAKE action (Zork's ITAKE).
    
    Checks:
    - Item exists and is takeable
    - Weight constraint (LOAD-ALLOWED)
    - Count constraint (FUMBLE-NUMBER)
    """
    actor_id = payload.get("actor")
    item_id = payload.get("item")
    
    if not actor_id or not item_id:
        return False
    
    if actor_id not in entities or item_id not in items:
        return False
    
    actor = entities[actor_id]
    item = items[item_id]
    
    # Check if item is takeable (TAKEBIT)
    if not item.get("takeable", True):
        alerts.append({
            "type": "take_failed",
            "reason": "not_takeable",
            "actor": actor_id,
            "item": item_id
        })
        return False
    
    # Check if already held
    if item.get("held_by") == actor_id:
        alerts.append({
            "type": "take_failed",
            "reason": "already_held",
            "actor": actor_id,
            "item": item_id
        })
        return False
    
    # Calculate new weight if taken
    item_weight = calculate_weight_recursive(item_id, items, actor_id)
    current_weight = actor.get("current_weight", 0)
    load_allowed = actor.get("load_allowed", LOAD_MAX)
    
    if current_weight + item_weight > load_allowed:
        alerts.append({
            "type": "take_failed",
            "reason": "too_heavy",
            "actor": actor_id,
            "item": item_id,
            "current_weight": current_weight,
            "item_weight": item_weight,
            "limit": load_allowed
        })
        return False
    
    # Check count constraint (FUMBLE-NUMBER)
    carry_count = calculate_carry_count(actor_id, items)
    if carry_count >= FUMBLE_NUMBER:
        alerts.append({
            "type": "take_failed",
            "reason": "too_many_items",
            "actor": actor_id,
            "item": item_id,
            "carry_count": carry_count,
            "limit": FUMBLE_NUMBER
        })
        return False
    
    # TAKE SUCCESS
    old_location = item.get("held_by") or item.get("location", "world")
    item["held_by"] = actor_id
    item["location"] = None  # No longer in world
    
    alerts.append({
        "type": "item_taken",
        "actor": actor_id,
        "item": item_id,
        "from": old_location
    })
    
    return True


def _handle_drop(
    entities: Dict[str, Dict],
    items: Dict[str, Dict],
    payload: Dict[str, Any],
    alerts: List[Dict]
) -> bool:
    """
    Handle DROP action.
    """
    actor_id = payload.get("actor")
    item_id = payload.get("item")
    location = payload.get("location", "world")
    
    if not actor_id or not item_id:
        return False
    
    if actor_id not in entities or item_id not in items:
        return False
    
    item = items[item_id]
    
    # Check if actually held
    if item.get("held_by") != actor_id:
        alerts.append({
            "type": "drop_failed",
            "reason": "not_held",
            "actor": actor_id,
            "item": item_id
        })
        return False
    
    # DROP SUCCESS
    item["held_by"] = None
    item["location"] = location
    item["worn"] = False  # Can't wear dropped items
    
    alerts.append({
        "type": "item_dropped",
        "actor": actor_id,
        "item": item_id,
        "location": location
    })
    
    return True


def _handle_wear(
    items: Dict[str, Dict],
    payload: Dict[str, Any],
    alerts: List[Dict]
) -> bool:
    """
    Handle WEAR action (Zork's WEARBIT).
    
    Worn items reduce weight.
    """
    actor_id = payload.get("actor")
    item_id = payload.get("item")
    
    if not actor_id or not item_id:
        return False
    
    if item_id not in items:
        return False
    
    item = items[item_id]
    
    # Check if held
    if item.get("held_by") != actor_id:
        alerts.append({
            "type": "wear_failed",
            "reason": "not_held",
            "actor": actor_id,
            "item": item_id
        })
        return False
    
    # Check if wearable
    if not item.get("wearable", False):
        alerts.append({
            "type": "wear_failed",
            "reason": "not_wearable",
            "actor": actor_id,
            "item": item_id
        })
        return False
    
    # Check if already worn
    if item.get("worn", False):
        alerts.append({
            "type": "wear_failed",
            "reason": "already_worn",
            "actor": actor_id,
            "item": item_id
        })
        return False
    
    # WEAR SUCCESS
    item["worn"] = True
    
    alerts.append({
        "type": "item_worn",
        "actor": actor_id,
        "item": item_id
    })
    
    return True


def _handle_remove(
    items: Dict[str, Dict],
    payload: Dict[str, Any],
    alerts: List[Dict]
) -> bool:
    """
    Handle REMOVE action (unwear).
    """
    actor_id = payload.get("actor")
    item_id = payload.get("item")
    
    if not actor_id or not item_id:
        return False
    
    if item_id not in items:
        return False
    
    item = items[item_id]
    
    # Check if worn
    if not item.get("worn", False):
        alerts.append({
            "type": "remove_failed",
            "reason": "not_worn",
            "actor": actor_id,
            "item": item_id
        })
        return False
    
    # REMOVE SUCCESS
    item["worn"] = False
    
    alerts.append({
        "type": "item_removed",
        "actor": actor_id,
        "item": item_id
    })
    
    return True


def _update_entity_capacity(
    entity_id: str,
    entities: Dict[str, Dict],
    items: Dict[str, Dict],
    alerts: List[Dict]
) -> None:
    """
    Update entity's current_weight and carry_count.
    Fires alerts if limits exceeded.
    """
    entity = entities.get(entity_id)
    if not entity:
        return
    
    # Calculate current weight
    total_weight = 0
    for item_id, item_data in items.items():
        if item_data.get("held_by") == entity_id:
            total_weight += calculate_weight_recursive(item_id, items, entity_id)
    
    entity["current_weight"] = total_weight
    
    # Calculate carry count
    carry_count = calculate_carry_count(entity_id, items)
    entity["carry_count"] = carry_count
    
    # Check limits
    load_allowed = entity.get("load_allowed", LOAD_MAX)
    if total_weight > load_allowed:
        alerts.append({
            "type": "overloaded",
            "entity": entity_id,
            "current_weight": total_weight,
            "limit": load_allowed
        })
    
    if carry_count > FUMBLE_NUMBER:
        alerts.append({
            "type": "fumble_risk",
            "entity": entity_id,
            "carry_count": carry_count,
            "limit": FUMBLE_NUMBER
        })


# ============================================================
# TESTING (if run directly)
# ============================================================

if __name__ == "__main__":
    # Test inventory kernel
    test_snapshot = {
        "inventory3d": {
            "entities": {
                "player": {
                    "load_allowed": LOAD_MAX,
                    "current_weight": 0,
                    "carry_count": 0
                }
            },
            "items": {
                "sword": {
                    "size": 10,
                    "takeable": True,
                    "wearable": True,
                    "held_by": None,
                    "location": "world",
                    "worn": False,
                    "children": []
                },
                "shield": {
                    "size": 15,
                    "takeable": True,
                    "wearable": True,
                    "held_by": None,
                    "location": "world",
                    "worn": False,
                    "children": []
                }
            }
        }
    }
    
    # Test TAKE
    deltas = [
        {
            "type": "inventory3d/take",
            "payload": {
                "actor": "player",
                "item": "sword"
            }
        }
    ]
    
    snapshot_out, accepted, alerts = step_inventory(test_snapshot, deltas, 0.016)
    
    print("=== Inventory Test ===")
    print(f"Sword held by: {snapshot_out['inventory3d']['items']['sword']['held_by']}")
    print(f"Player weight: {snapshot_out['inventory3d']['entities']['player']['current_weight']}")
    print(f"Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert['type']}: {alert}")
