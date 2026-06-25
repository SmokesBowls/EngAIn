# core/authority_gate.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from godotengain.engainos.core.ap_rule_evaluator import evaluate_rule
from godotengain.engainos.core.ap_rule_loader import load as load_ap_registry


Stage = Literal[
    "protocol",
    "contract",
    "authority",
    "reality",
    "ap",
    "conversion",
    "runtime",
]


REQUIRED_AUTHORITY_ENVELOPE_FIELDS = (
    "trace_id",
    "source",
    "actor_id",
    "actor_authority_tier",
    "reality_mode",
    "action",
    "payload",
)

ACTION_CLASSIFICATION = {
    "look": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.snapshot"],
        "write_set": [],
    },
    "status": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.status"],
        "write_set": [],
    },
    "snapshot": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.snapshot"],
        "write_set": [],
    },
    "entities": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.entities"],
        "write_set": [],
    },
    "examine": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.entities"],
        "write_set": [],
    },
    "talk": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.entities"],
        "write_set": [],
    },
    "segments": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.scene"],
        "write_set": [],
    },
    "command": {
        "required_tier": 3,
        "mutation_class": "unknown",
        "read_set": [],
        "write_set": ["unknown"],
    },
    "load_scene": {
        "required_tier": 2,
        "mutation_class": "runtime_mutation",
        "read_set": ["scene.registry"],
        "write_set": ["runtime.scene"],
    },
    "spawn_entity": {
        "required_tier": 2,
        "mutation_class": "runtime_mutation",
        "read_set": ["runtime.scene"],
        "write_set": ["runtime.entities"],
    },
    "update_entity": {
        "required_tier": 2,
        "mutation_class": "runtime_mutation",
        "read_set": ["runtime.entities"],
        "write_set": ["runtime.entities"],
    },
}

AP_MUTATION_UNKNOWN_REASON = (
    "Action mutation intent is unknown; AP requires explicit "
    "write_set or read-only classification"
)


@dataclass(frozen=True)
class APDecision:
    """
    Internal EngAInOS authority-gate decision.

    This object is intentionally richer than the public contract. It records
    exactly what was checked (tier, reality_mode) and internal debug data.

    Do not expose `to_dict()` as the external wire contract.
    Use `to_contract_dict()` when returning data to Godot, mettaext, agents,
    GodotSim, or any runtime-facing caller.
    """

    allowed: bool
    trace_id: str
    stage: Stage
    reason: str

    # Authority context (what was checked)
    actor_tier: Optional[int] = None
    reality_mode: Optional[str] = None

    errors: List[Dict[str, Any]] = field(default_factory=list)

    # Internal/debug fields.
    payload: Dict[str, Any] = field(default_factory=dict)
    fired_rules: List[Dict[str, Any]] = field(default_factory=list)
    protocol_type: Optional[str] = None
    epoch: Optional[str] = None
    tick: Optional[int] = None

    # Contract-facing optional fields.
    output: Optional[Dict[str, Any]] = None
    runtime_action: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Internal/debug serialization.
        Safe for logs, local debug reports, and trace inspection.
        Not safe as the public EngAInOS boundary contract.
        """
        return {
            "allowed": self.allowed,
            "trace_id": self.trace_id,
            "stage": self.stage,
            "reason": self.reason,
            "actor_tier": self.actor_tier,
            "reality_mode": self.reality_mode,
            "errors": self.errors,
            "payload": self.payload,
            "fired_rules": self.fired_rules,
            "protocol_type": self.protocol_type,
            "epoch": self.epoch,
            "tick": self.tick,
            "output": self.output,
            "runtime_action": self.runtime_action,
        }

    def to_contract_dict(self) -> Dict[str, Any]:
        """
        Public ENGAINOS_RUNTIME_AUTHORITY_CONTRACT_v1 projection.
        This is the only shape that should cross the EngAInOS boundary.
        """
        base: Dict[str, Any] = {
            "allowed": self.allowed,
            "trace_id": self.trace_id,
            "stage": self.stage,
            "reason": self.reason,
            "errors": self.errors,
        }

        if not self.allowed:
            return base

        base["ap_decision"] = self._contract_ap_decision()

        if self.output is not None:
            base["output"] = self.output

        if self.runtime_action is not None:
            base["runtime_action"] = self.runtime_action

        return base

    def _contract_ap_decision(self) -> Dict[str, Any]:
        """
        Translate internal state into the smaller public AP decision shape.
        """
        blocking_rule = _first_blocking_rule(self.fired_rules)
        first_rule = blocking_rule or _first_rule(self.fired_rules)

        return {
            "allowed": self.allowed,
            "rule_id": first_rule.get("rule_id") if first_rule else None,
            "blocked_by": blocking_rule.get("rule_id") if blocking_rule else None,
            "reason": self.reason,
            "read_set": _collect_read_set(self.fired_rules),
            "write_set": _collect_write_set(self.fired_rules),
            "tier": self.actor_tier,
            "reality_mode": self.reality_mode,
            "trace_id": self.trace_id,
        }


def _first_rule(rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return rules[0] if rules else None


def _first_blocking_rule(rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for rule in rules:
        if rule.get("allowed") is False or rule.get("blocked") is True:
            return rule
    return None


def _collect_read_set(rules: List[Dict[str, Any]]) -> List[str]:
    values: List[str] = []
    for rule in rules:
        for item in rule.get("read_set", []) or []:
            if item not in values:
                values.append(item)
    return values


def _collect_write_set(rules: List[Dict[str, Any]]) -> List[str]:
    values: List[str] = []
    for rule in rules:
        for item in rule.get("write_set", []) or []:
            if item not in values:
                values.append(item)
    return values


def _normalize_action(flat_inbound_contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize action through the EngAInOS-owned classification table.

    Caller-supplied required_tier/read_set/write_set/mutation_class values are
    preserved as caller_hints only. They do not lower authority requirements.
    """
    raw_action = flat_inbound_contract.get("action")
    payload = flat_inbound_contract.get("payload", {})

    raw_action_dict = dict(raw_action) if isinstance(raw_action, dict) else {"name": raw_action}
    action_name = str(raw_action_dict.get("name") or "").lower()

    caller_hints: Dict[str, Any] = {}
    for key in ("required_tier", "read_set", "write_set", "mutation_class"):
        if key in raw_action_dict:
            caller_hints[key] = raw_action_dict[key]
        if isinstance(payload, dict) and key in payload:
            caller_hints[f"payload.{key}"] = payload[key]

    classification = ACTION_CLASSIFICATION.get(
        action_name,
        {
            "required_tier": 3,
            "mutation_class": "unknown",
            "read_set": [],
            "write_set": ["unknown"],
        },
    )

    action = {
        **raw_action_dict,
        "name": action_name,
        "required_tier": int(classification["required_tier"]),
        "mutation_class": classification["mutation_class"],
        "read_set": list(classification["read_set"]),
        "write_set": list(classification["write_set"]),
    }

    if flat_inbound_contract.get("reality_mode") == "FINALIZED":
        action["required_tier"] = max(action["required_tier"], 3)

    if caller_hints:
        action["caller_hints"] = caller_hints

    return action


def _is_mutating_action(action: Dict[str, Any]) -> Optional[bool]:
    """
    Map EngAInOS-owned mutation_class to AP routing behavior.
    """
    mutation_class = action.get("mutation_class")
    if mutation_class == "read_only":
        return False
    if mutation_class == "runtime_mutation":
        return True
    if mutation_class == "unknown":
        return None
    return None


def _union(groups: List[List[str]]) -> List[str]:
    values: List[str] = []
    for group in groups:
        for item in group or []:
            if item not in values:
                values.append(item)
    return values


def _build_telemetry(
    eligible: List[Dict[str, Any]],
    accepted: List[Dict[str, Any]],
    blocked: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    telemetry: List[Dict[str, Any]] = []
    accepted_ids = {rule.get("id") for rule in accepted}
    blocked_ids = {rule.get("id") for rule in blocked}

    for rule in accepted:
        telemetry.append(
            {
                "rule_id": rule.get("id"),
                "allowed": True,
                "decision": "fired",
                "scope": rule.get("scope"),
                "priority": rule.get("priority"),
                "read_set": rule.get("read_set", []) or [],
                "write_set": rule.get("write_set", []) or [],
            }
        )

    for rule in blocked:
        telemetry.append(
            {
                "rule_id": rule.get("id"),
                "allowed": False,
                "blocked": True,
                "decision": rule.get("decision", "blocked"),
                "reason": rule.get("reason", "AP rule blocked"),
                "blocked_by": rule.get("effects_result", {}).get("blocked_by"),
                "scope": rule.get("scope"),
                "priority": rule.get("priority"),
                "read_set": rule.get("read_set", []) or [],
                "write_set": rule.get("write_set", []) or [],
            }
        )

    for rule in eligible:
        rule_id = rule.get("id")
        if rule_id in accepted_ids or rule_id in blocked_ids:
            continue
        telemetry.append(
            {
                "rule_id": rule_id,
                "decision": rule.get("decision", "skipped"),
                "reason": rule.get("reason", "AP rule did not fire"),
                "scope": rule.get("scope"),
                "priority": rule.get("priority"),
                "read_set": rule.get("read_set", []) or [],
                "write_set": rule.get("write_set", []) or [],
            }
        )

    return telemetry


def _load_runtime_mutation_rules() -> List[Dict[str, Any]]:
    """Load active runtime_mutation AP rules for the AP stage only."""
    registry = load_ap_registry("runtime_mutation")
    return list(registry.get("active_rules", []) or [])


def _rule_with_decision(rule: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    decision = result.get("decision", {}) or {}
    enriched = dict(rule)
    enriched["effects_result"] = decision
    enriched["reason"] = decision.get("reason") or "AP rule evaluated"
    if decision.get("allowed") is False:
        enriched["decision"] = "blocked"
        enriched["blocked"] = True
        enriched["reason"] = decision.get("reason") or "AP rule blocked"
    elif decision.get("allowed") is True:
        enriched["decision"] = "fired"
        enriched["allowed"] = True
    return enriched


def _run_ap_rules(
    envelope: Dict[str, Any],
    action: Dict[str, Any],
    ap_registry: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Run the runtime_mutation AP registry for mutating/unknown actions only.

    Read-only actions are classified before AP mutation rules and are allowed by
    default unless a future read-policy registry exists. FINALIZED effective
    tier derivation is owned by _normalize_action before this AP slice runs.
    """
    mutation_classification = _is_mutating_action(action)

    if mutation_classification is False:
        return {
            "allowed": True,
            "reason": "No matching rule; action is non-mutating",
            "rule_id": None,
            "blocked_by": None,
            "read_set": [],
            "write_set": [],
            "fired_rules": [],
        }

    registry = ap_registry if ap_registry is not None else _load_runtime_mutation_rules()
    eligible: List[Dict[str, Any]] = list(registry or [])
    accepted: List[Dict[str, Any]] = []
    blocked: List[Dict[str, Any]] = []

    for rule in eligible:
        result = evaluate_rule(rule, envelope, action)
        if not result.get("predicate_passed"):
            continue

        decision = result.get("decision", {}) or {}
        enriched = _rule_with_decision(rule, result)
        if decision.get("allowed") is False:
            blocked.append(enriched)
            break
        if decision.get("allowed") is True:
            accepted.append(enriched)

    fired_allow = any(rule.get("effects_result", {}).get("allowed") is True for rule in accepted)

    if blocked:
        allowed = False
        rule_id = None
        blocked_by = blocked[0].get("effects_result", {}).get("blocked_by") or blocked[0].get("id")
        reason = blocked[0].get("reason", "AP rule blocked")
    elif mutation_classification is True and not fired_allow:
        allowed = False
        rule_id = None
        blocked_by = None
        reason = "No active AP rule authorized this mutation"
    elif mutation_classification is None:
        allowed = False
        rule_id = None
        blocked_by = None
        reason = AP_MUTATION_UNKNOWN_REASON
    else:
        allowed = fired_allow
        rule_id = accepted[0].get("id") if accepted else None
        blocked_by = None
        reason = accepted[0].get("reason", "AP rule evaluated") if accepted else "AP rule evaluated"

    return {
        "allowed": allowed,
        "reason": reason,
        "rule_id": rule_id,
        "blocked_by": blocked_by,
        "read_set": _union([rule.get("read_set", []) or [] for rule in accepted]),
        "write_set": _union([rule.get("write_set", []) or [] for rule in accepted]),
        "fired_rules": _build_telemetry(eligible, accepted, blocked),
    }


def validate_required_inbound_fields(envelope: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Enforce ENGAINOS_RUNTIME_AUTHORITY_CONTRACT_v1 required inbound fields.
    
    NOTE: 'envelope' here is the FLAT authority contract dict, NOT a nested
    ProtocolEnvelope. If a ProtocolEnvelope is used upstream, the caller must
    unwrap and flatten it before passing it to this function.
    """
    errors: List[Dict[str, Any]] = []

    for field_name in REQUIRED_AUTHORITY_ENVELOPE_FIELDS:
        if field_name not in envelope:
            errors.append(
                {
                    "code": "MISSING_REQUIRED_FIELD",
                    "field": field_name,
                    "message": f"Missing required authority envelope field: {field_name}",
                }
            )

    if "payload" in envelope and not isinstance(envelope["payload"], dict):
        errors.append(
            {
                "code": "INVALID_PAYLOAD",
                "field": "payload",
                "message": "payload must be an object/dict",
            }
        )

    return errors


def fail_closed(
    *,
    trace_id: str,
    stage: Stage,
    reason: str,
    errors: Optional[List[Dict[str, Any]]] = None,
    payload: Optional[Dict[str, Any]] = None,
    actor_tier: Optional[int] = None,
    reality_mode: Optional[str] = None,
) -> APDecision:
    """Helper to generate a standardized rejection decision."""
    return APDecision(
        allowed=False,
        trace_id=trace_id,
        stage=stage,
        reason=reason,
        actor_tier=actor_tier,
        reality_mode=reality_mode,
        errors=errors or [],
        payload=payload or {},
    )


def evaluate(flat_inbound_contract: Dict[str, Any]) -> APDecision:
    """
    Main entry point for the authority gate.
    
    Expects a FLAT dict conforming to ENGAINOS_RUNTIME_AUTHORITY_CONTRACT_v1 inbound shape.
    Returns an internal APDecision object, which the caller MUST project via 
    `to_contract_dict()` before sending across the EngAInOS boundary.
    """
    trace_id = flat_inbound_contract.get("trace_id", "unknown_trace")
    actor_tier = flat_inbound_contract.get("actor_authority_tier")
    reality_mode = flat_inbound_contract.get("reality_mode")
    payload = flat_inbound_contract.get("payload", {})

    # 1. Protocol / Contract Validation (Required Fields)
    validation_errors = validate_required_inbound_fields(flat_inbound_contract)
    if validation_errors:
        return fail_closed(
            trace_id=trace_id,
            stage="contract",
            reason="Inbound contract validation failed",
            errors=validation_errors,
            payload=payload,
            actor_tier=actor_tier,
            reality_mode=reality_mode,
        )

    # 2. Authority / Reality Mode Validation (Stubbed for WO1)
    # TODO: Integrate core/authority_validator.py and core/reality_mode.py here
    # if reality_mode == "REPLAY": return fail_closed(...)

    # 3. AP Rule Evaluation (runtime_mutation loader/evaluator slice)
    action = _normalize_action(flat_inbound_contract)
    ap_result = _run_ap_rules(flat_inbound_contract, action)

    # 4. AP Decision
    return APDecision(
        allowed=ap_result["allowed"],
        trace_id=trace_id,
        stage="ap",
        reason=ap_result["reason"],
        actor_tier=actor_tier,
        reality_mode=reality_mode,
        payload=payload,
        fired_rules=ap_result["fired_rules"],
    )