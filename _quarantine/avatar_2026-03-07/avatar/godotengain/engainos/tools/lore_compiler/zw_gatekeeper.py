# zw_gatekeeper.py
"""
ZW Gatekeeper

The Gatekeeper enforces the direction of authority in the ZW/ZON ecosystem:

    JSON  →  ZW   (uplift, import)
    ZW    →  ZON  (projection, archival)

Prohibited:
    - ZW → JSON (generic flattening)
    - JSON overriding canonical ZW meaning
    - Any "round trip" JSON → ZW → JSON pipeline

This module is intentionally small, explicit, and opinionated.
All cross-boundary data motion MUST go through here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import hashlib
import json
import time


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ZWBlock:
    """
    Canonical runtime semantic block.

    This is *not* a JSON dict. It is a semantic object used by the ZW runtime.
    """
    id: str
    type: str
    scope: str
    context: Dict[str, Any]
    action: str
    meta: Dict[str, Any] = field(default_factory=dict)

    # Optional: capture original source for debugging (never for authority)
    source_json: Optional[Dict[str, Any]] = None

    def to_runtime_packet(self) -> Dict[str, Any]:
        """
        This is the *only* structured conversion allowed out of ZW:
        a runtime-internal packet for the ZW engine / Godot layer.

        NOTE: This is NOT "ZW → JSON" for external systems.
        This dict must never be treated as an authoritative persistence format.
        """
        return {
            "id": self.id,
            "type": self.type,
            "scope": self.scope,
            "context": self.context,
            "action": self.action,
            "meta": self.meta,
        }


@dataclass
class ZONBlock:
    """
    Archival 4D memory block.

    - @when: time span (start~end)
    - @where: hierarchical location path
    - =delta: idempotent, patchable evolution
    - @sig: canonical signature for integrity/provenance
    """
    when: str
    where: str
    delta: Dict[str, Any]
    sig: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        """
        ZON is explicitly JSON-native, so this is allowed.
        """
        return {
            "@when": self.when,
            "@where": self.where,
            "=delta": self.delta,
            "@sig": self.sig,
            "_meta": self.meta,
        }


# ---------------------------------------------------------------------------
# Gatekeeper Invariants
# ---------------------------------------------------------------------------

class GatekeeperViolation(Exception):
    """Raised when a forbidden direction or pattern is attempted."""
    pass


def _canonicalize_for_signature(data: Dict[str, Any]) -> str:
    """
    Deterministically canonicalize a dict for signing.

    - Sorted keys
    - No whitespace differences
    - UTF-8 encoded JSON string
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _default_signer(payload: Dict[str, Any]) -> str:
    """
    Default signature implementation: SHA-256 of canonicalized payload.

    You can replace this with a real key-based signing method later.
    """
    canonical = _canonicalize_for_signature(payload).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------------
# JSON → ZW (uplift)
# ---------------------------------------------------------------------------

def json_to_zw(
    raw: Dict[str, Any],
    id_field: str = "id",
    type_field: str = "type",
    scope_field: str = "scope",
    action_field: str = "action",
    context_field: str = "context",
    meta_field: str = "meta",
    *,
    strict: bool = True,
) -> ZWBlock:
    """
    Uplift a JSON-like dict into a canonical ZWBlock.

    This is the ONLY entry point for JSON into ZW-space.

    - JSON is treated as *input*, never as authority.
    - Missing required fields either raise (strict) or are defaulted.
    - Any additional keys are folded into meta for inspection, not power.
    """

    if not isinstance(raw, dict):
        raise GatekeeperViolation(f"json_to_zw expects dict, got {type(raw)}")

    # Extract required fields with minimal assumptions.
    try:
        id_val = str(raw.get(id_field) or f"zw_{int(time.time() * 1000)}")
        type_val = str(raw.get(type_field) or "unknown")
        scope_val = str(raw.get(scope_field) or "World")
        action_val = str(raw.get(action_field) or "noop")
    except Exception as e:
        raise GatekeeperViolation(f"Failed to normalize required fields: {e}")

    context_val = raw.get(context_field) or {}
    meta_val = raw.get(meta_field) or {}

    if strict:
        # Validate types roughly; you can strengthen this later.
        if not isinstance(context_val, dict):
            raise GatekeeperViolation("context must be a dict in strict mode")
        if not isinstance(meta_val, dict):
            raise GatekeeperViolation("meta must be a dict in strict mode")

    # Fold any extra keys into meta[_raw_extras] for inspection.
    known_keys = {id_field, type_field, scope_field, action_field, context_field, meta_field}
    extras = {k: v for k, v in raw.items() if k not in known_keys}
    if extras:
        meta_val.setdefault("_raw_extras", extras)

    zw = ZWBlock(
        id=id_val,
        type=type_val,
        scope=scope_val,
        context=context_val,
        action=action_val,
        meta=meta_val,
        source_json=raw.copy(),
    )

    return zw


# ---------------------------------------------------------------------------
# ZW → ZON (projection)
# ---------------------------------------------------------------------------

def zw_to_zon(
    zw: ZWBlock,
    *,
    when: Optional[str] = None,
    where: Optional[str] = None,
    delta_builder: Optional[Callable[[ZWBlock], Dict[str, Any]]] = None,
    signer: Callable[[Dict[str, Any]], str] = _default_signer,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> ZONBlock:
    """
    Project a ZWBlock into a ZONBlock.

    - This is ONE-WAY: ZW → ZON, archival only.
    - No "flatten to generic JSON" is exposed here.
    - @when and @where can be supplied or inferred from context/meta.
    - The =delta content is derived using a provided delta_builder callback.

    delta_builder:
        Given a ZWBlock, returns the state delta to persist.
        If not provided, we fall back to a minimal delta containing
        the action and context.
    """

    if not isinstance(zw, ZWBlock):
        raise GatekeeperViolation(f"zw_to_zon expects ZWBlock, got {type(zw)}")

    # Infer @when if not provided: treat as "now~now".
    if when is None:
        now = int(time.time())
        when = f"{now}~{now}"

    # Infer @where if not provided: try context or scope.
    if where is None:
        # Prefer explicit location in context, then scope.
        loc = zw.context.get("Location") or zw.context.get("location") or zw.scope
        where = str(loc or "Unknown/Nowhere")

    # Build =delta
    if delta_builder is None:
        # Default: capture action and context only.
        delta = {
            "id": zw.id,
            "type": zw.type,
            "scope": zw.scope,
            "action": zw.action,
            "context": zw.context,
        }
    else:
        delta = delta_builder(zw)

    if not isinstance(delta, dict):
        raise GatekeeperViolation("delta_builder must return a dict")

    # Prepare payload for signing (without @sig).
    payload_for_sig = {
        "@when": when,
        "@where": where,
        "=delta": delta,
    }

    sig = signer(payload_for_sig)

    meta = dict(zw.meta) if zw.meta else {}
    extra_meta = extra_meta or {}
    meta.update(extra_meta)

    return ZONBlock(
        when=when,
        where=where,
        delta=delta,
        sig=sig,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Forbidden Patterns (hard brakes)
# ---------------------------------------------------------------------------

def zw_to_json_forbidden(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    This function exists ONLY to fail.

    If any system tries to call "ZW → JSON" through the Gatekeeper,
    it will explode loudly instead of silently normalizing meaning away.
    """
    raise GatekeeperViolation(
        "Forbidden operation: generic ZW → JSON conversion is not allowed. "
        "JSON may enter as input (json_to_zw) and ZON may be emitted (zw_to_zon.to_json()), "
        "but ZW itself is never flattened as an external JSON authority."
    )


# ---------------------------------------------------------------------------
# Simple Usage Example (for your future self or agents)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example raw JSON event coming from some external system or AI.
    raw_json_event = {
        "id": "evt_123",
        "type": "narrative_event",
        "scope": "Player",
        "action": "perform_activation_ritual",
        "context": {
            "Location": "Eldara/ForgeOfFirstMaking/MainChamber",
            "Item": "crimson_gauntlets",
            "CurrentDate": "Dingirash-15-3127",
        },
        "meta": {
            "event_type": "ARTIFACT_ACTIVATION",
            "requires_validation": True,
        },
        "some_external_field": "this_will_be_tucked_into_raw_extras",
    }

    # 1) JSON → ZW (uplift)
    zw_block = json_to_zw(raw_json_event)
    print("ZWBlock:", zw_block)

    # 2) ZW → ZON (projection)
    zon_block = zw_to_zon(zw_block)
    print("ZON JSON:", zon_block.to_json())

    # 3) Try to break the rules (this should raise)
    try:
        zw_to_json_forbidden(zw_block)
    except GatekeeperViolation as e:
        print("Expected violation:", e)

