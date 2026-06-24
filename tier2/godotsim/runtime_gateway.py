"""
runtime_gateway.py — Governance gate for EngAIn runtime mutations.

Governance logic extracted from empire_agent_gateway.py.
Routes through CommandDispatcher against the real EngAInRuntime.snapshot
instead of Empire.world_state.

Checks (in order):
    1. Global REPLAY mode — block all mutations server-wide
    2. Request-claimed REPLAY mode — block if caller declares REPLAY
    3. FINALIZED + authority < 3 — block globally or per-scene
    4. Complex AP rules against runtime.snapshot
    5. Route to CommandDispatcher.dispatch(raw_input)

Records IntentShadow on every rejection.
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .runtime_core import EngAInRuntime
    from .command_dispatcher import CommandDispatcher

from tier1.engainos.aproom.reality_mode import RealityMode, RealityContext, get_context as _get_global_context
from tier1.engainos.core.intent_shadow import record_intent
from tier1.engainos.aproom.canon import can_edit

try:
    from tier1.engainos.aproom.authority_gate import ACTION_CLASSIFICATION
except ImportError:
    ACTION_CLASSIFICATION = {}

try:
    from tier1.engainos.aproom.ap_complex_rules import check_complex_rules
    _HAS_COMPLEX_RULES = True
except ImportError:
    _HAS_COMPLEX_RULES = False

# ── Compatibility flag ───────────────────────────────────────────
# When False (default): mutation requests MUST carry explicit reality_mode
# and actor_authority_tier fields. Missing fields are rejected with a
# governance_rejected response and recorded in IntentShadow.
#
# Set to True only during transition to allow legacy callers that do not
# yet send these fields to proceed as DRAFT/Tier-1. Remove this flag
# and all references to it once all callers are updated.
allow_implicit_draft_tier1: bool = False

# ── Mode string → enum mapping ───────────────────────────────────

_MODE_MAP: Dict[str, RealityMode] = {
    "DRAFT":     RealityMode.DRAFT,
    "IMBUED":    RealityMode.IMBUED,
    "FINALIZED": RealityMode.FINALIZED,
    "DREAM":     RealityMode.DREAM,
    "REPLAY":    RealityMode.REPLAY,
    "TEST":      RealityMode.TEST,
}

# ── Decision record ──────────────────────────────────────────────

_counter = 0

def _next_id() -> str:
    global _counter
    _counter += 1
    return f"gw_{_counter}"


@dataclass
class GatewayDecision:
    """
    Result of a governance gate evaluation.

    accepted=True  → mutation is permitted; result carries dispatcher output.
    accepted=False → mutation is blocked; reason carries the rejection cause.
    status_code    → suggested HTTP status: 400 for malformed identity,
                     403 for authorization/mode failures.
    """
    accepted: bool
    reason: str
    command_id: str
    issuer: str
    authority_tier: int
    reality_mode: str
    status_code: int = 403
    timestamp: datetime = field(default_factory=datetime.now)
    result: Optional[Dict[str, Any]] = None


# ── Identity field validation ────────────────────────────────────

def _missing_identity_fields(raw_input: Dict[str, Any]) -> Optional[str]:
    """
    Return an error reason string if required mutation identity fields are
    absent or null, or None if both are explicitly present.

    Required fields:
        reality_mode         — must be a non-null string key in the request
        actor_authority_tier — must be a non-null key in the request

    When allow_implicit_draft_tier1 is True this check is bypassed, allowing
    legacy callers to proceed with DRAFT/Tier-1 defaults. That flag must not
    remain True permanently.
    """
    if allow_implicit_draft_tier1:
        return None

    missing = []
    if raw_input.get("reality_mode") is None:
        missing.append("reality_mode")
    if raw_input.get("actor_authority_tier") is None:
        missing.append("actor_authority_tier")

    if missing:
        return f"Missing required mutation identity fields: {', '.join(missing)}"
    return None


# ── Request context extraction ───────────────────────────────────

def _extract_request_context(
    raw_input: Dict[str, Any],
) -> Tuple[RealityContext, int, str, str]:
    """
    Pull governance fields from a request dict.

    Returns (per_request_context, authority_tier, issuer_id, source_system).

    Callers should run _missing_identity_fields() before calling this function.
    When both required fields are present, no defaults are applied to mode or tier.
    actor_id and source_system still default to "unknown"/"http" when absent.
    """
    mode_raw = str(raw_input.get("reality_mode", "DRAFT")).upper()
    mode = _MODE_MAP.get(mode_raw, RealityMode.DRAFT)

    try:
        tier = int(raw_input.get("actor_authority_tier", 1))
    except (TypeError, ValueError):
        tier = 1

    issuer = str(raw_input.get("actor_id", "unknown"))
    source = str(raw_input.get("source_system", "http"))

    scene_id = raw_input.get("scene_id") or raw_input.get("target_artifact")

    return RealityContext(mode=mode, scene_id=scene_id), tier, issuer, source


def _normalized_action_name(raw_input: Dict[str, Any]) -> str:
    """
    Classify legacy /command payloads by the effective command the dispatcher
    will run, not by the generic transport field name.

    This preserves fail-closed behavior for generic/unknown commands while
    allowing explicitly-classified read-only inspection commands to pass without
    mutation identity fields.
    """
    raw_action = raw_input.get("action")
    if isinstance(raw_action, dict):
        action = str(raw_action.get("name") or "").strip().lower()
    else:
        action = str(raw_action or "").strip().lower()

    command = str(raw_input.get("command") or "").strip().lower()
    text = str(raw_input.get("text") or "").strip().lower()

    if action and action not in ("command", "action"):
        effective = action
    elif command and command not in ("command", "action"):
        effective = command
    else:
        effective = text or action or command

    base = effective.split(" ", 1)[0] if effective else ""
    return {
        "l": "look",
        "stat": "status",
        "seg": "segments",
        "x": "examine",
    }.get(base, base)


def _is_classified_read_only(raw_input: Dict[str, Any]) -> bool:
    classification = ACTION_CLASSIFICATION.get(_normalized_action_name(raw_input), {})
    return classification.get("mutation_class") == "read_only"


# ── RuntimeGateway ───────────────────────────────────────────────

class RuntimeGateway:
    """
    Governance gate between request sources and EngAInRuntime mutation.

    Wraps CommandDispatcher.dispatch() with the tier/mode/AP checks
    from empire_agent_gateway.py, but operating on the real
    EngAInRuntime.snapshot instead of Empire.world_state.
    """

    def __init__(self, runtime: 'EngAInRuntime', dispatcher: 'CommandDispatcher'):
        self.runtime = runtime
        self.dispatcher = dispatcher

    def submit(self, raw_input: Dict[str, Any]) -> GatewayDecision:
        """
        Governance-gated entry point for all runtime mutations.

        Validates identity, mode, tier, and AP rules before routing to dispatcher.
        Records IntentShadow on every rejection path.
        """
        command_id = _next_id()
        req_ctx, tier, issuer, source = _extract_request_context(raw_input)
        is_read_only = _is_classified_read_only(raw_input)

        # ── 0. Explicit mutation identity required ────────────────
        identity_error = None if is_read_only else _missing_identity_fields(raw_input)
        if identity_error:
            return self._reject(
                command_id, issuer, tier, req_ctx, raw_input, source,
                identity_error,
                status_code=400,
            )

        # Resolve scene_id: prefer request, fall back to active scene in snapshot.
        scene_id = req_ctx.scene_id or self.runtime.snapshot.get("scene_id")

        # ── 1. Global REPLAY check (server-wide operational mode) ─
        global_ctx = _get_global_context()
        if not is_read_only and not global_ctx.allows_mutation():
            return self._reject(
                command_id, issuer, tier, req_ctx, raw_input, source,
                "REPLAY mode is active server-wide — mutations not allowed",
            )

        # ── 2. Per-request REPLAY check (caller declared REPLAY) ──
        if not is_read_only and not req_ctx.allows_mutation():
            return self._reject(
                command_id, issuer, tier, req_ctx, raw_input, source,
                "Request declares REPLAY mode — mutations not allowed",
            )

        # ── 3a. Global FINALIZED check ────────────────────────────
        if not is_read_only and global_ctx.is_canonical() and tier < 3:
            return self._reject(
                command_id, issuer, tier, req_ctx, raw_input, source,
                f"Server is in FINALIZED mode — requires Tier 3 authority (have Tier {tier})",
            )

        # ── 3b. Per-request FINALIZED check ──────────────────────
        if not is_read_only and req_ctx.is_canonical() and tier < 3:
            return self._reject(
                command_id, issuer, tier, req_ctx, raw_input, source,
                f"Request targets FINALIZED context — requires Tier 3 authority (have Tier {tier})",
            )

        # ── 3c. Scene-level FINALIZED check (canon system) ───────
        if not is_read_only and scene_id and not can_edit(scene_id) and tier < 3:
            return self._reject(
                command_id, issuer, tier, req_ctx, raw_input, source,
                f"Scene '{scene_id}' is FINALIZED — requires Tier 3 authority (have Tier {tier})",
            )

        # ── 4. Complex AP rules against runtime.snapshot ─────────
        if _HAS_COMPLEX_RULES:
            try:
                violations = check_complex_rules(raw_input, self.runtime.snapshot)
                if violations:
                    return self._reject(
                        command_id, issuer, tier, req_ctx, raw_input, source,
                        f"AP rule violation: {violations[0].message}",
                        extra={"violation_id": violations[0].rule_id},
                    )
            except Exception as e:
                print(f"[GATEWAY] AP rule check error: {e}")

        # ── 5. Route to real dispatcher ───────────────────────────
        result = self.dispatcher.dispatch(raw_input)

        return GatewayDecision(
            accepted=True,
            reason="accepted",
            command_id=command_id,
            issuer=issuer,
            authority_tier=tier,
            reality_mode=req_ctx.mode.value,
            result=result,
        )

    def _reject(
        self,
        command_id: str,
        issuer: str,
        tier: int,
        ctx: RealityContext,
        raw_input: Dict[str, Any],
        source: str,
        reason: str,
        extra: Optional[Dict[str, Any]] = None,
        status_code: int = 403,
    ) -> GatewayDecision:
        record_intent(
            issuer=issuer,
            command=raw_input,
            reason_rejected=reason,
            scene_id=ctx.scene_id,
            authority_tier=tier,
            reality_mode=ctx.mode.value,
            source=source,
            **(extra or {}),
        )
        print(f"[GATEWAY] Rejected {command_id} ({issuer} tier={tier} mode={ctx.mode.value}): {reason}")
        return GatewayDecision(
            accepted=False,
            reason=reason,
            command_id=command_id,
            issuer=issuer,
            authority_tier=tier,
            reality_mode=ctx.mode.value,
            status_code=status_code,
        )
