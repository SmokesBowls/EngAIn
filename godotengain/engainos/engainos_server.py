# engainos_server.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from runtime_client import NGATRTClient, RuntimeClientError

app = FastAPI(title="EngAInOS Kernel+Supervisor Facade", version="0.1.0")

RUNTIME_BASE = os.environ.get("NGAT_RT_BASE_URL", "http://127.0.0.1:8080")
rt = NGATRTClient(base_url=RUNTIME_BASE, timeout_s=5.0, retries=1)


# ----------------------------
# Models
# ----------------------------

class CommandReq(BaseModel):
    action: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    properties: Optional[Dict[str, Any]] = None
    entity: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    context: Optional[str] = None
    player_rep: Optional[int] = None
    player_gold: Optional[int] = None


class CombatDamageReq(BaseModel):
    source: str = "unknown"
    target: str
    damage: float = 25.0


class InventoryTakeReq(BaseModel):
    actor: str
    item: str


class InventoryDropReq(BaseModel):
    actor: str
    item: str
    location: str = "world"


class InventoryWearReq(BaseModel):
    actor: str
    item: str


# ----------------------------
# Helpers
# ----------------------------

def _require_rt_json_snapshot() -> Dict[str, Any]:
    """
    Fetch snapshot from NGAT-RT and return parsed JSON.
    Raises HTTPException(502) on runtime/proxy failure.
    """
    try:
        r = rt.snapshot()
        if not (200 <= r.status < 300):
            raise HTTPException(
                status_code=502,
                detail=f"runtime snapshot HTTP {r.status}: {r.text()[:800]}",
            )
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


def _envelope_meta(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract standard envelope meta fields safely.
    """
    return {
        "protocol": envelope.get("protocol"),
        "version": envelope.get("version"),
        "epoch": envelope.get("epoch"),
        "tick": envelope.get("tick"),
        "type": envelope.get("type"),
        "hash": envelope.get("hash"),
    }


def _payload(envelope: Dict[str, Any]) -> Dict[str, Any]:
    p = envelope.get("payload")
    return p if isinstance(p, dict) else {}


def _combat_entity(payload: Dict[str, Any], entity: str) -> Dict[str, Any]:
    combat = payload.get("combat", {})
    if not isinstance(combat, dict):
        return {}
    entities = combat.get("entities", {})
    if not isinstance(entities, dict):
        return {}
    e = entities.get(entity, {})
    return e if isinstance(e, dict) else {}


def _inventory_entity(payload: Dict[str, Any], entity: str) -> Dict[str, Any]:
    inv = payload.get("inventory", {})
    if not isinstance(inv, dict):
        return {}
    entities = inv.get("entities", {})
    if not isinstance(entities, dict):
        return {}
    e = entities.get(entity, {})
    return e if isinstance(e, dict) else {}


def _inventory_items(payload: Dict[str, Any]) -> Dict[str, Any]:
    inv = payload.get("inventory", {})
    if not isinstance(inv, dict):
        return {}
    items = inv.get("items", {})
    return items if isinstance(items, dict) else {}


def _inventory_items_held(payload: Dict[str, Any], entity: str) -> list[str]:
    items = _inventory_items(payload)
    held: list[str] = []
    for item_id, item in items.items():
        if isinstance(item, dict) and item.get("held_by") == entity:
            held.append(str(item_id))
    return held


def _inventory_items_worn(payload: Dict[str, Any], entity: str) -> list[str]:
    items = _inventory_items(payload)
    worn: list[str] = []
    for item_id, item in items.items():
        if not isinstance(item, dict):
            continue
        if item.get("held_by") == entity and bool(item.get("worn", False)):
            worn.append(str(item_id))
    return worn


def _project_engine_summary(
    envelope: Dict[str, Any],
    scene_id: str = "",
    reality_mode: str = "waking",
    delta_time: float = 0.0,
) -> Dict[str, Any]:
    """
    Produce the flat EngineSummary dict your Godot HUD expects.
    This uses runtime payload (combat/inventory/dialogue/quest/etc.).
    """
    meta = _envelope_meta(envelope)
    payload = _payload(envelope)

    # Time: your runtime uses payload.world.time (float)
    world = payload.get("world", {})
    game_time = float(world.get("time", 0.0)) if isinstance(world, dict) else 0.0

    # Entities count: runtime payload.entities exists but may be empty.
    entities = payload.get("entities", {})
    entities_count = len(entities) if isinstance(entities, dict) else 0

    # Quests: if/when you re-add quest slice in runtime, this will start working.
    quest = payload.get("quest", {})
    quests = {}
    if isinstance(quest, dict):
        quests = quest.get("quests", {}) if isinstance(quest.get("quests", {}), dict) else {}
    active_quests = 0
    completed_quests = 0
    for _qid, q in quests.items():
        if not isinstance(q, dict):
            continue
        st = str(q.get("status", "inactive"))
        if st == "active":
            active_quests += 1
        elif st == "completed":
            completed_quests += 1

    # Combat state from combat.entities.player
    player_combat = _combat_entity(payload, "player")
    hp = float(player_combat.get("health", 0.0))
    hp_max = float(player_combat.get("max_health", 100.0))
    if hp <= 0.0:
        combat_state = "dead"
    else:
        # Your combat adapter doesn’t currently expose engaged flags in snapshot.
        # Default to idle unless you later add engaged/in_combat.
        if bool(player_combat.get("engaged", False)) or bool(player_combat.get("in_combat", False)):
            combat_state = "engaged"
        else:
            combat_state = "idle"

    # Location/scene: use provided override if present, else "unknown"
    player_location = "unknown"
    if isinstance(entities, dict):
        p = entities.get("player", {})
        if isinstance(p, dict):
            player_location = str(p.get("location", "unknown"))

    effective_scene = scene_id.strip() or player_location

    # Pillars: you can make this smarter later
    pillar_status = {
        "engain": "running",
        "mvcar": "idle" if not quests else "running",
        "tv": "reserved",
    }

    return {
        **meta,
        # EngineSummary contract:
        "game_time": game_time,
        "scene_id": effective_scene if effective_scene else "unknown",
        "active_quests": active_quests,
        "completed_quests": completed_quests,
        "combat_state": combat_state,
        "reality_mode": reality_mode,
        "player_health": hp,
        "player_health_max": hp_max,
        "player_location": player_location,
        "entities_count": entities_count,
        "tick_rate": float(delta_time),
        "pillar_status": pillar_status,
    }


# ----------------------------
# Core facade endpoints
# ----------------------------

@app.get("/api/health")
def health():
    ok = rt.probe()
    # Returning some meta is convenient for debugging HUD versioning
    if not ok:
        return {"ok": False, "runtime_base": RUNTIME_BASE}
    env = _require_rt_json_snapshot()
    meta = _envelope_meta(env)
    return {"ok": True, "runtime_base": RUNTIME_BASE, **meta}


@app.get("/api/snapshot")
def snapshot():
    return _require_rt_json_snapshot()


@app.post("/api/command")
def command(req: CommandReq):
    try:
        r = rt.command(req.model_dump(exclude_none=True))
        if not (200 <= r.status < 300):
            raise HTTPException(status_code=502, detail=f"runtime command HTTP {r.status}: {r.text()[:800]}")
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/combat/damage")
def combat_damage(req: CombatDamageReq):
    try:
        r = rt.combat_damage(req.source, req.target, req.damage)
        if not (200 <= r.status < 300):
            raise HTTPException(status_code=502, detail=f"runtime combat/damage HTTP {r.status}: {r.text()[:800]}")
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/inventory/take")
def inventory_take(req: InventoryTakeReq):
    try:
        r = rt.inventory_take(req.actor, req.item)
        if not (200 <= r.status < 300):
            raise HTTPException(status_code=502, detail=f"runtime inventory/take HTTP {r.status}: {r.text()[:800]}")
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/inventory/drop")
def inventory_drop(req: InventoryDropReq):
    try:
        r = rt.inventory_drop(req.actor, req.item, req.location)
        if not (200 <= r.status < 300):
            raise HTTPException(status_code=502, detail=f"runtime inventory/drop HTTP {r.status}: {r.text()[:800]}")
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/inventory/wear")
def inventory_wear(req: InventoryWearReq):
    try:
        r = rt.inventory_wear(req.actor, req.item)
        if not (200 <= r.status < 300):
            raise HTTPException(status_code=502, detail=f"runtime inventory/wear HTTP {r.status}: {r.text()[:800]}")
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/dialogue/say")
def dialogue_say(payload: Dict[str, Any]):
    try:
        r = rt.dialogue_say(payload)
        if not (200 <= r.status < 300):
            raise HTTPException(status_code=502, detail=f"runtime dialogue/say HTTP {r.status}: {r.text()[:800]}")
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/dialogue/ask")
def dialogue_ask(payload: Dict[str, Any]):
    try:
        r = rt.dialogue_ask(payload)
        if not (200 <= r.status < 300):
            raise HTTPException(status_code=502, detail=f"runtime dialogue/ask HTTP {r.status}: {r.text()[:800]}")
        return r.json()
    except (RuntimeClientError, ValueError) as e:
        raise HTTPException(status_code=502, detail=str(e))


# ----------------------------
# HUD endpoints (read-only projections)
# ----------------------------

@app.get("/api/hud/engine")
def hud_engine():
    env = _require_rt_json_snapshot()
    p = _payload(env)
    meta = _envelope_meta(env)
    return {
        **meta,
        "entities_count": len(p.get("entities", {})) if isinstance(p.get("entities", {}), dict) else 0,
        "events_count": len(p.get("events", [])) if isinstance(p.get("events", []), list) else 0,
        "has_combat": isinstance(p.get("combat", None), dict),
        "has_inventory": isinstance(p.get("inventory", None), dict),
        "has_dialogue": isinstance(p.get("dialogue", None), dict),
    }


@app.get("/api/hud/combat")
def hud_combat(entity: str = Query("player")):
    env = _require_rt_json_snapshot()
    p = _payload(env)
    meta = _envelope_meta(env)
    e = _combat_entity(p, entity)
    if not e:
        # Keep stable shape; Godot HUD shouldn’t crash on missing entity
        return {**meta, "entity": entity, "health": 0, "max_health": 100, "alive": False}
    return {**meta, "entity": entity, **e}


@app.get("/api/hud/inventory")
def hud_inventory(entity: str = Query("player")):
    env = _require_rt_json_snapshot()
    p = _payload(env)
    meta = _envelope_meta(env)

    e = _inventory_entity(p, entity)
    held = _inventory_items_held(p, entity)
    worn = _inventory_items_worn(p, entity)

    # Mirror the shape you already showed in curl output
    out = {
        **meta,
        "entity": entity,
        "current_weight": float(e.get("current_weight", 0.0)),
        "load_allowed": float(e.get("load_allowed", e.get("load_max", 100.0))),
        "carry_count": int(e.get("carry_count", 0)),
        "items_held": held,
        "items_worn": worn,
    }
    return out


@app.get("/api/hud/engine_summary")
def hud_engine_summary(
    scene_id: str = Query("", description="Optional override scene id for HUD"),
    reality_mode: str = Query("waking", description="waking|dream|memory|liminal"),
    delta_time: float = Query(0.0, description="Optional tick delta for HUD"),
):
    env = _require_rt_json_snapshot()
    return _project_engine_summary(env, scene_id=scene_id, reality_mode=reality_mode, delta_time=delta_time)

