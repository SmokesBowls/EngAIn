# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING
# ---------------------------------------------------------------------------
# This file calls:   (standalone kernel — no imports from EngAIn yet)
# This file is called by: mettaext/pipeline_runner.py (future)
#                          godotsim/sim_runtime.py    (future)
# ---------------------------------------------------------------------------
"""
ap_runtime.py — Anti-Python Protocol Execution Kernel (v1, minimal)

Pure functional AP rule engine. Implements APSimKernel v1.1 spec.
Snapshot-in → tick → snapshot-out. No side effects, no I/O, no mutations.

Feed it your ZON/ZONJ snapshot data (zon_blocks, spatial_hints, entities)
and it will evaluate AP rules, resolve write-set conflicts, apply effects,
and emit a ZON tick packet per spec.

v1   — spatial_hint predicates + seed rules (proved tick loop).
v1.1 — zon_block predicates added:
           zon_block_type_exists("<type>")
           zon_where_exists("<where>")
           zon_state_equals("<where>", "<key>", "<value>")
       Seed rules now fire from compiler-extracted world state.
       compiler output → AP condition → behavior event.
"""

from __future__ import annotations

import time
import random
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple


# ============================================================
# TYPE ALIASES
# ============================================================

StateKey   = str          # e.g. "flag.door.locked", "stat.player.health"
EntityID   = str
RuleID     = str
ResourceID = str


# ============================================================
# IMMUTABLE DATA STRUCTURES
# ============================================================

@dataclass(frozen=True)
class APRule:
    """
    Canonical rule object. APSimKernel only consumes validated APRules.
    Never raw .zw text or loose dicts.
    """
    id:        RuleID
    tags:      FrozenSet[str]         = field(default_factory=frozenset)
    priority:  int                    = 0
    requires:  Tuple[str, ...]        = ()   # predicate expressions (strings)
    conflicts: Tuple[str, ...]        = ()   # veto predicates
    effects:   Tuple[str, ...]        = ()   # effect expressions
    read_set:  FrozenSet[StateKey]    = field(default_factory=frozenset)
    write_set: FrozenSet[StateKey]    = field(default_factory=frozenset)
    validated: bool                   = False


@dataclass(frozen=True)
class APStateView:
    """
    Immutable read-only view of world state at tick start.
    The kernel reads from here, writes to working_state (a plain dict copy).
    """
    flags:         Dict[str, Any]   = field(default_factory=dict)
    stats:         Dict[str, Any]   = field(default_factory=dict)
    inventory:     Dict[str, Any]   = field(default_factory=dict)
    entropy:       Dict[str, float] = field(default_factory=dict)
    locations:     Dict[str, str]   = field(default_factory=dict)
    spatial_hints: Tuple[str, ...]  = ()
    entities:      Dict[str, Any]   = field(default_factory=dict)
    zon_blocks:    Tuple[Any, ...]   = ()


@dataclass(frozen=True)
class StateChange:
    key:       StateKey
    old_value: Any
    new_value: Any


@dataclass(frozen=True)
class SideEffect:
    op_name: str          # e.g. "emit_event", "schedule_rule"
    args:    Dict[str, Any] = field(default_factory=dict)
    status:  str           = "success"


@dataclass(frozen=True)
class RuleFireRecord:
    rule_id:               RuleID
    predicates_satisfied:  bool
    effects_applied:       Tuple[StateChange, ...]  = ()


@dataclass(frozen=True)
class APTransaction:
    tick_id:      int
    timestamp:    float
    rules_fired:  Tuple[RuleFireRecord, ...]
    state_changes: Tuple[StateChange, ...]
    side_effects:  Tuple[SideEffect, ...]
    errors:        Tuple[str, ...]


@dataclass(frozen=True)
class APTransactionResult:
    status:      str           # "committed" | "aborted"
    transaction: APTransaction
    zon_packet:  Dict[str, Any]


@dataclass(frozen=True)
class TickContext:
    scene_id:        str
    active_entities: Tuple[EntityID, ...]  = ()
    delta_time:      float                 = 0.016
    mode:            str                   = "ingame"   # ingame|headless|scenario
    tick_number:     int                   = 0
    rng_seed:        int                   = 0


# ============================================================
# PREDICATE EVALUATOR (pure functions, no mutations)
# ============================================================

def _eval_predicate(pred: str, view: APStateView, ctx: TickContext, rng: random.Random) -> bool:
    """
    Evaluate a single predicate string against APStateView.
    Returns True/False. Never mutates. Never raises — returns False on error.

    Supported forms (v1 minimal):
        spatial_hint_exists("<hint>")
        flag(<entity>, "<name>") == <value>
        stat(<entity>, "<name>") > <value>
        entity_exists(<entity_id>)
        random_chance(<p>)
    """
    pred = pred.strip()

    # spatial_hint_exists("Earth/Sky/WhiteSky")
    if pred.startswith("spatial_hint_exists("):
        inner = pred[len("spatial_hint_exists("):-1].strip().strip('"').strip("'")
        return any(inner in h for h in view.spatial_hints)

    # entity_exists(eduhauana)
    if pred.startswith("entity_exists("):
        eid = pred[len("entity_exists("):-1].strip().strip('"').strip("'")
        return eid in view.entities

    # random_chance(0.25)
    if pred.startswith("random_chance("):
        try:
            p = float(pred[len("random_chance("):-1].strip())
            return rng.random() < p
        except ValueError:
            return False

    # flag(player, "has_key") == true
    if pred.startswith("flag("):
        try:
            inner, _, rhs = pred.partition(")")
            args = inner[len("flag("):].split(",")
            entity  = args[0].strip()
            fname   = args[1].strip().strip('"').strip("'")
            key     = f"flag.{entity}.{fname}"
            val     = view.flags.get(key)
            rhs     = rhs.strip()
            if "==" in rhs:
                expected = rhs.split("==")[1].strip().lower()
                return str(val).lower() == expected
            return bool(val)
        except Exception:
            return False

    # stat(player, "health") > 0
    if pred.startswith("stat("):
        try:
            inner, _, rhs = pred.partition(")")
            args   = inner[len("stat("):].split(",")
            entity = args[0].strip()
            sname  = args[1].strip().strip('"').strip("'")
            key    = f"stat.{entity}.{sname}"
            val    = float(view.stats.get(key, 0.0))
            rhs    = rhs.strip()
            if ">=" in rhs:
                return val >= float(rhs.split(">=")[1])
            if ">" in rhs:
                return val > float(rhs.split(">")[1])
            if "<=" in rhs:
                return val <= float(rhs.split("<=")[1])
            if "<" in rhs:
                return val < float(rhs.split("<")[1])
            if "==" in rhs:
                return val == float(rhs.split("==")[1])
            return val > 0
        except Exception:
            return False

    # zon_block_type_exists("STATE_DELTA")
    # True if any zon_block has @type == the given value.
    if pred.startswith("zon_block_type_exists("):
        btype = pred[len("zon_block_type_exists("):-1].strip().strip('"').strip("'")
        return any(
            isinstance(b, dict) and b.get("@type") == btype
            for b in view.zon_blocks
        )

    # zon_where_exists("Earth/Atmosphere")
    # True if any zon_block has @where == the given value.
    if pred.startswith("zon_where_exists("):
        where = pred[len("zon_where_exists("):-1].strip().strip('"').strip("'")
        return any(
            isinstance(b, dict) and b.get("@where") == where
            for b in view.zon_blocks
        )

    # zon_state_equals("Earth/Core", "core_stability", "stabilized")
    # True if a zon_block at @where has state[key] == value.
    if pred.startswith("zon_state_equals("):
        inner = pred[len("zon_state_equals("):-1]
        parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
        if len(parts) == 3:
            where, key, expected = parts
            return any(
                isinstance(b, dict)
                and b.get("@where") == where
                and isinstance(b.get("state"), dict)
                and str(b["state"].get(key, "")).lower() == expected.lower()
                for b in view.zon_blocks
            )
        return False

    # zon_block_type_exists("STATE_DELTA")
    if pred.startswith("zon_block_type_exists("):
        btype = pred[len("zon_block_type_exists("):-1].strip().strip('"').strip("'")
        return any(b.get("@type") == btype for b in view.zon_blocks if isinstance(b, dict))

    # zon_where_exists("Earth/Core")
    if pred.startswith("zon_where_exists("):
        where = pred[len("zon_where_exists("):-1].strip().strip('"').strip("'")
        return any(b.get("@where") == where for b in view.zon_blocks if isinstance(b, dict))

    # zon_state_equals("Earth/Core", "core_stability", "stabilized")
    if pred.startswith("zon_state_equals("):
        inner = pred[len("zon_state_equals("):-1]
        parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
        if len(parts) == 3:
            where, key, val = parts
            return any(
                b.get("@where") == where and
                isinstance(b.get("state"), dict) and
                str(b["state"].get(key, "")).lower() == val.lower()
                for b in view.zon_blocks if isinstance(b, dict)
            )
        return False

    # Unknown — log-worthy but non-fatal
    return False


def eval_all_predicates(
    preds: Tuple[str, ...],
    view:  APStateView,
    ctx:   TickContext,
    rng:   random.Random,
) -> bool:
    """True only if ALL predicates pass."""
    return all(_eval_predicate(p, view, ctx, rng) for p in preds)


def eval_any_predicate(
    preds: Tuple[str, ...],
    view:  APStateView,
    ctx:   TickContext,
    rng:   random.Random,
) -> bool:
    """True if ANY predicate passes."""
    return any(_eval_predicate(p, view, ctx, rng) for p in preds)


# ============================================================
# EFFECT EXECUTOR (pure — returns changes, never mutates view)
# ============================================================

def _apply_effect(
    effect:        str,
    working_state: Dict[str, Any],
    ctx:           TickContext,
    rng:           random.Random,
) -> Tuple[List[StateChange], List[SideEffect]]:
    """
    Apply one effect expression to working_state (mutable copy only).
    Returns (state_changes, side_effects). Never touches APStateView.

    Supported (v1 minimal):
        set_flag(<entity>, "<name>", <value>)
        change_stat(<entity>, "<name>", <delta>)
        emit_event("<event_name>", {...})
    """
    effect = effect.strip()
    changes:      List[StateChange] = []
    side_effects: List[SideEffect]  = []

    # set_flag(door, "locked", false)
    if effect.startswith("set_flag("):
        try:
            inner = effect[len("set_flag("):-1]
            parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
            entity, fname, new_val_str = parts[0], parts[1], parts[2].lower()
            key   = f"flag.{entity}.{fname}"
            new_val = new_val_str == "true"
            old_val = working_state.get("flags", {}).get(key)
            working_state.setdefault("flags", {})[key] = new_val
            changes.append(StateChange(key=key, old_value=old_val, new_value=new_val))
        except Exception:
            pass

    # change_stat(player, "health", -10)
    elif effect.startswith("change_stat("):
        try:
            inner  = effect[len("change_stat("):-1]
            parts  = [p.strip().strip('"').strip("'") for p in inner.split(",")]
            entity, sname = parts[0], parts[1]
            delta  = float(parts[2])
            key    = f"stat.{entity}.{sname}"
            old_val = float(working_state.get("stats", {}).get(key, 0.0))
            new_val = old_val + delta
            working_state.setdefault("stats", {})[key] = new_val
            changes.append(StateChange(key=key, old_value=old_val, new_value=new_val))
        except Exception:
            pass

    # emit_event("door_opened", {door_id: door})
    elif effect.startswith("emit_event("):
        try:
            inner    = effect[len("emit_event("):-1]
            ev_name  = inner.split(",")[0].strip().strip('"').strip("'")
            side_effects.append(SideEffect(op_name="emit_event", args={"event": ev_name}))
        except Exception:
            pass

    return changes, side_effects


# ============================================================
# CONFLICT RESOLUTION (write-set based, per spec §4)
# ============================================================

def resolve_write_conflicts(eligible: List[APRule]) -> List[APRule]:
    """
    Priority-sorted eligible rules. First rule to claim a StateKey wins.
    Any later rule that touches the same key is skipped this tick.
    """
    applied:      List[APRule]        = []
    claimed_keys: FrozenSet[StateKey] = frozenset()

    for rule in sorted(eligible, key=lambda r: r.priority, reverse=True):
        if rule.write_set & claimed_keys:
            continue   # write conflict — skip
        applied.append(rule)
        claimed_keys = claimed_keys | rule.write_set

    return applied


# ============================================================
# ZON PACKET BUILDER (per ap_zon_packet_format_v1)
# ============================================================

def _build_zon_packet(
    txn:       APTransaction,
    ctx:       TickContext,
    eligible:  List[APRule],
    applied:   List[APRule],
    blocked:   List[Tuple[RuleID, str]],
    status:    str,
    duration:  float,
) -> Dict[str, Any]:
    return {
        "type":    "ap_tick",
        "tick":    ctx.tick_number,
        "status":  status,
        "scene":   ctx.scene_id,
        "eligible": [r.id for r in eligible],
        "fired":    [r.id for r in applied],
        "blocked":  [{"id": rid, "reason": reason} for rid, reason in blocked],
        "state_delta": {
            "flags":   {c.key: c.new_value for c in txn.state_changes if c.key.startswith("flag.")},
            "stats":   {c.key: c.new_value for c in txn.state_changes if c.key.startswith("stat.")},
            "items":   {},
            "entropy": {},
        },
        "metrics": {
            "ops":         len(txn.rules_fired),
            "predicates":  sum(len(r.requires) + len(r.conflicts) for r in applied),
            "duration_ms": round(duration * 1000, 3),
        },
    }


# ============================================================
# CORE KERNEL — run_tick (THE only place AP rules execute)
# ============================================================

def run_tick(
    rules:       List[APRule],
    view:        APStateView,
    ctx:         TickContext,
    rng:         random.Random,
) -> APTransactionResult:
    """
    Pure functional AP tick.

    snapshot_in (view + ctx) → run_tick → APTransactionResult

    This is the singular isolation core per APSimKernel v1.1 §1.1.
    Nothing else evaluates or applies AP rules.
    """
    t_start = time.monotonic()

    # ── 1. Candidate selection (all validated rules for this scene/context)
    candidates = [r for r in rules if r.validated]

    # ── 2. Predicate evaluation
    eligible: List[APRule]              = []
    blocked:  List[Tuple[RuleID, str]]  = []

    for rule in candidates:
        requires_ok  = eval_all_predicates(rule.requires,  view, ctx, rng)
        conflicts_ok = eval_any_predicate( rule.conflicts, view, ctx, rng) if rule.conflicts else False

        if requires_ok and not conflicts_ok:
            eligible.append(rule)
        else:
            reason = "requires_failed" if not requires_ok else "conflict_triggered"
            blocked.append((rule.id, reason))

    # ── 3. Write-set conflict resolution
    applied = resolve_write_conflicts(eligible)
    skipped = [r.id for r in eligible if r not in applied]
    blocked += [(rid, "write_conflict") for rid in skipped]

    # ── 4. Apply effects into working_state (mutable copy — never touches view)
    working_state: Dict[str, Any] = {
        "flags":   dict(view.flags),
        "stats":   dict(view.stats),
        "inventory": dict(view.inventory),
        "entropy": dict(view.entropy),
        "locations": dict(view.locations),
    }

    all_changes:      List[StateChange]  = []
    all_side_effects: List[SideEffect]   = []
    fire_records:     List[RuleFireRecord] = []

    for rule in applied:
        rule_changes: List[StateChange] = []
        rule_fx:      List[SideEffect]  = []

        for eff in rule.effects:
            c, s = _apply_effect(eff, working_state, ctx, rng)
            rule_changes.extend(c)
            rule_fx.extend(s)

        all_changes.extend(rule_changes)
        all_side_effects.extend(rule_fx)
        fire_records.append(RuleFireRecord(
            rule_id=rule.id,
            predicates_satisfied=True,
            effects_applied=tuple(rule_changes),
        ))

    # ── 5. Build transaction
    txn = APTransaction(
        tick_id=ctx.tick_number,
        timestamp=time.time(),
        rules_fired=tuple(fire_records),
        state_changes=tuple(all_changes),
        side_effects=tuple(all_side_effects),
        errors=(),
    )

    duration = time.monotonic() - t_start

    # ── 6. ZON packet
    zon_packet = _build_zon_packet(txn, ctx, eligible, applied, blocked, "committed", duration)

    return APTransactionResult(
        status="committed",
        transaction=txn,
        zon_packet=zon_packet,
    )


# ============================================================
# RULE PARSER — .zw block dict → APRule
# ============================================================

def _derive_read_set(requires: List[str], conflicts: List[str]) -> FrozenSet[StateKey]:
    """Derive read_set from predicate expressions per ap_rule_parsing_v1_spec §3.2"""
    keys: List[StateKey] = []
    for pred in requires + conflicts:
        if pred.startswith("flag("):
            parts = pred[5:pred.index(")")].split(",")
            if len(parts) >= 2:
                keys.append(f"flag.{parts[0].strip()}.{parts[1].strip().strip(chr(34)).strip(chr(39))}")
        elif pred.startswith("stat("):
            parts = pred[5:pred.index(")")].split(",")
            if len(parts) >= 2:
                keys.append(f"stat.{parts[0].strip()}.{parts[1].strip().strip(chr(34)).strip(chr(39))}")
        elif pred.startswith("spatial_hint_exists("):
            keys.append("spatial_hints")
        elif pred.startswith("zon_block_type_exists("):
            keys.append("zon_blocks")
        elif pred.startswith("zon_where_exists("):
            where = pred[len("zon_where_exists("):].strip().strip("()").strip('"').strip("'")
            keys.append(f"zon_blocks.where.{where}")
        elif pred.startswith("zon_state_equals("):
            inner = pred[len("zon_state_equals("):-1].strip()
            parts = [p.strip().strip('"').strip("'") for p in inner.split(",")]
            if len(parts) == 3:
                keys.append(f"zon_blocks.state.{parts[0]}.{parts[1]}")
        elif pred.startswith("entity_exists("):
            keys.append("entities")
    return frozenset(keys)


def _derive_write_set(effects: List[str]) -> FrozenSet[StateKey]:
    """Derive write_set from effect expressions per ap_rule_parsing_v1_spec §3.3"""
    keys: List[StateKey] = []
    for eff in effects:
        if eff.startswith("set_flag("):
            parts = eff[9:eff.index(")")].split(",")
            if len(parts) >= 2:
                keys.append(f"flag.{parts[0].strip()}.{parts[1].strip().strip(chr(34)).strip(chr(39))}")
        elif eff.startswith("change_stat("):
            parts = eff[12:eff.index(")")].split(",")
            if len(parts) >= 2:
                keys.append(f"stat.{parts[0].strip()}.{parts[1].strip().strip(chr(34)).strip(chr(39))}")
        elif eff.startswith("adjust_entropy("):
            pool = eff[15:eff.index(")")].split(",")[0].strip().strip('"').strip("'")
            keys.append(f"entropy.{pool}")
        # emit_event → NOT a write per spec §3.4
    return frozenset(keys)


def parse_rule_dict(d: Dict[str, Any]) -> APRule:
    """
    Convert a plain dict (e.g. loaded from .zonj.json zon_blocks or hardcoded)
    into a validated APRule. Marks validated=False if read/write sets can't be built.
    """
    rid      = str(d.get("id", "unknown"))
    tags     = frozenset(d.get("tags", []))
    priority = int(d.get("priority", 0))
    requires = tuple(d.get("requires", []))
    conflicts= tuple(d.get("conflicts", []))
    effects  = tuple(d.get("effects", []))

    read_set  = _derive_read_set(list(requires), list(conflicts))
    write_set = _derive_write_set(list(effects))
    validated = bool(rid and rid != "unknown")

    return APRule(
        id=rid, tags=tags, priority=priority,
        requires=requires, conflicts=conflicts, effects=effects,
        read_set=read_set, write_set=write_set, validated=validated,
    )


# ============================================================
# SNAPSHOT → APStateView builder
# ============================================================

def build_view_from_snapshot(snapshot: Dict[str, Any]) -> APStateView:
    """
    Convert a sim_runtime snapshot payload into an APStateView.
    Works with your existing /snapshot endpoint response.
    """
    payload = snapshot.get("payload", snapshot)   # handle envelope or raw

    entities      = payload.get("entities", {})
    spatial_hints = tuple(payload.get("spatial_hints", []))
    zon_blocks    = tuple(payload.get("zon_blocks", []))

    # Flatten entity stats/flags into canonical key form
    flags:  Dict[str, Any]   = {}
    stats:  Dict[str, Any]   = {}
    locations: Dict[str, str] = {}

    for eid, edata in (entities.items() if isinstance(entities, dict) else []):
        if not isinstance(edata, dict):
            continue
        for fname, fval in edata.get("flags", {}).items():
            flags[f"flag.{eid}.{fname}"] = fval
        for sname, sval in edata.get("stats", {}).items():
            stats[f"stat.{eid}.{sname}"] = sval
        if "location" in edata:
            locations[f"location.{eid}"] = edata["location"]

    return APStateView(
        flags=flags,
        stats=stats,
        inventory={},
        entropy={},
        locations=locations,
        spatial_hints=spatial_hints,
        entities=dict(entities) if isinstance(entities, dict) else {},
        zon_blocks=zon_blocks,
    )


# ============================================================
# HARDCODED SEED RULES (first-run proof of concept)
# ============================================================

SEED_RULES: List[APRule] = [
    parse_rule_dict({
        "id":       "white_sky_presence",
        "tags":     ["environment", "sky"],
        "priority": 10,
        "requires": ['spatial_hint_exists("Earth/Sky/WhiteSky")'],
        "conflicts": [],
        "effects":  ['emit_event("white_sky_detected")'],
    }),
    parse_rule_dict({
        "id":       "ethereal_realm_presence",
        "tags":     ["environment", "ethereal"],
        "priority": 8,
        "requires": ['spatial_hint_exists("Ethereal Realm")'],
        "conflicts": [],
        "effects":  ['emit_event("ethereal_realm_active")'],
    }),
    parse_rule_dict({
        "id":       "solar_core_presence",
        "tags":     ["environment", "solar"],
        "priority": 6,
        "requires": ['spatial_hint_exists("SolarSystem/Sun/Core")'],
        "conflicts": [],
        "effects":  ['emit_event("solar_core_detected")'],
    }),
    # ── ZON block rules — fire from compiler-extracted world state ──
    parse_rule_dict({
        "id":       "state_delta_exists",
        "tags":     ["zon", "world_state"],
        "priority": 5,
        "requires": ['zon_block_type_exists("STATE_DELTA")'],
        "conflicts": [],
        "effects":  ['emit_event("world_state_active")'],
    }),
    parse_rule_dict({
        "id":       "atmosphere_present",
        "tags":     ["zon", "environment", "atmosphere"],
        "priority": 5,
        "requires": ['zon_where_exists("Earth/Atmosphere")'],
        "conflicts": [],
        "effects":  ['emit_event("atmosphere_present")'],
    }),
    parse_rule_dict({
        "id":       "core_stabilized",
        "tags":     ["zon", "environment", "geology"],
        "priority": 7,
        "requires": ['zon_state_equals("Earth/Core", "core_stability", "stabilized")'],
        "conflicts": [],
        "effects":  ['emit_event("earth_core_stabilized")', 'set_flag(world, "core_stable", true)'],
    }),
    parse_rule_dict({
        "id":       "magnetic_field_sustainable",
        "tags":     ["zon", "environment", "atmosphere"],
        "priority": 7,
        "requires": ['zon_state_equals("Earth/Atmosphere", "magnetic_field", "approaching_sustainable")'],
        "conflicts": [],
        "effects":  ['emit_event("magnetic_field_sustainable")'],
    }),
    parse_rule_dict({
        "id":       "oxygen_nitrogen_balanced",
        "tags":     ["zon", "environment", "atmosphere"],
        "priority": 6,
        "requires": [
            'zon_state_equals("Earth/Atmosphere", "atmosphere", "oxygen_nitrogen_balance")',
            'zon_state_equals("Earth/Core", "core_stability", "stabilized")',
        ],
        "conflicts": [],
        "effects":  ['emit_event("atmosphere_breathable")', 'set_flag(world, "breathable", true)'],
    }),
]


# ============================================================
# SELF-TEST (run directly: python3 ap_runtime.py)
# ============================================================

if __name__ == "__main__":
    import json
    import urllib.request

    print("=" * 60)
    print("  ap_runtime.py — AP Kernel Self-Test")
    print("=" * 60)

    # ── Try to fetch live snapshot from sim_runtime
    snapshot: Dict[str, Any] = {}
    try:
        raw  = urllib.request.urlopen("http://127.0.0.1:8080/snapshot", timeout=3).read()
        snapshot = json.loads(raw)
        print(f"[ap] Live snapshot fetched from :8080")
    except Exception as e:
        print(f"[ap] No live runtime ({e}) — using synthetic snapshot")
        snapshot = {
            "payload": {
                "scene_id": "test.synthetic",
                "entities": {
                    "eduhauana": {"flags": {}, "stats": {"health": 100}},
                    "marduk":    {"flags": {}, "stats": {"health": 80}},
                },
                "spatial_hints": [
                    "Earth/Sky/WhiteSky",
                    "Ethereal Realm",
                    "SolarSystem/Sun/Core",
                ],
                "zon_blocks": [],
            }
        }

    # ── Build state view
    view = build_view_from_snapshot(snapshot)
    print(f"\n[ap] State view built:")
    print(f"     entities:      {list(view.entities.keys())}")
    print(f"     spatial_hints: {list(view.spatial_hints)}")
    print(f"     zon_blocks:    {len(view.zon_blocks)}")

    # ── Build tick context
    ctx = TickContext(
        scene_id=snapshot.get("payload", snapshot).get("scene_id", "test"),
        active_entities=tuple(view.entities.keys()),
        delta_time=0.016,
        mode="headless",
        tick_number=1,
        rng_seed=42,
    )

    # ── Seed RNG deterministically
    rng = random.Random(ctx.rng_seed)

    # ── Run tick with seed rules
    print(f"\n[ap] Running tick #{ctx.tick_number} with {len(SEED_RULES)} seed rules...")
    result = run_tick(SEED_RULES, view, ctx, rng)

    # ── Report
    txn = result.transaction
    pkt = result.zon_packet

    print(f"\n[ap] Tick result: {result.status}")
    print(f"     rules fired:    {len(txn.rules_fired)}")
    print(f"     state changes:  {len(txn.state_changes)}")
    print(f"     side effects:   {len(txn.side_effects)}")

    if txn.rules_fired:
        print(f"\n[ap] Fired rules:")
        for rec in txn.rules_fired:
            print(f"     ✅ {rec.rule_id}")

    if txn.side_effects:
        print(f"\n[ap] Side effects emitted:")
        for fx in txn.side_effects:
            print(f"     → {fx.op_name}: {fx.args}")

    print(f"\n[ap] ZON packet:")
    print(json.dumps(pkt, indent=2))

    print("\n[ap] ✅ Kernel self-test complete.")
