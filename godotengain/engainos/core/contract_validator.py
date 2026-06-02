# godotengain/engainos/core/contract_validator.py
"""
CONTRACT VALIDATOR v1.0
───────────────────────
Purpose: Enforce constitutional shape validation before AP gate evaluation.
Doctrine Boundaries:
  - DRAGON_AUTHORITY_DOCTRINE_v1.md
  - INTENT_CONTRACT_SCHEMA_v1.json
  - QUERY_CONTRACT_v1.json
  - TRUTH_SLICE_ABI_v1.md (anchor requirement)

Boundary Guarantees:
  ✅ Validates SHAPE, required fields, enums, and anchor presence
  ✅ Routes malformed payloads to Intent Shadow
  ❌ Does NOT validate permission (AP Gate responsibility)
  ❌ Does NOT route to builders (Capability Registry responsibility)
  ❌ Does NOT mutate state or execute business logic
  ❌ Does NOT verify cryptographic hash integrity (Protocol Envelope responsibility)

Flow:
  incoming payload → contract_validator.py → valid? 
    ├─ yes → ap_gate_hook.py
    └─ no  → intent_shadow.py
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass

import jsonschema
from jsonschema import Draft202012Validator, ValidationError

# -----------------------------------------------------------------------------
# Schema Loading (Production Pattern)
# -----------------------------------------------------------------------------
_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "schema"

def _load_schema(filename: str) -> dict:
    """Load frozen JSON Schema from constitutional docs."""
    path = _SCHEMA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Constitutional schema missing: {path}. "
            "Do not proceed without frozen schema artifacts."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Pre-compile validators for performance & strictness
try:
    _INTENT_VALIDATOR = Draft202012Validator(_load_schema("INTENT_CONTRACT_SCHEMA_v1.json"))
    _QUERY_VALIDATOR  = Draft202012Validator(_load_schema("QUERY_CONTRACT_SCHEMA_v1.json"))
except FileNotFoundError:
    # Graceful degradation for review/testing environments
    _INTENT_VALIDATOR = None
    _QUERY_VALIDATOR  = None


# -----------------------------------------------------------------------------
# Result Structure
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ValidationOutcome:
    """Immutable result of shape validation."""
    valid: bool
    trace_id: str
    contract_type: str  # "intent" | "query"
    error_code: Optional[str] = None
    error_detail: Optional[str] = None
    validated_payload: Optional[Dict[str, Any]] = None

    def to_shadow_record(self) -> dict:
        """Format for intent_shadow logging."""
        return {
            "trace_id": self.trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contract_type": self.contract_type,
            "valid": self.valid,
            "error_code": self.error_code,
            "error_detail": self.error_detail,
            "payload_snapshot": json.dumps(self.validated_payload or {}, ensure_ascii=False)[:2000]
        }


# -----------------------------------------------------------------------------
# Core Validation Logic
# -----------------------------------------------------------------------------

def _ensure_trace_id(payload: dict) -> str:
    """Guarantee deterministic traceability. Injects if missing."""
    meta = payload.setdefault("metadata", {})
    tid = meta.get("trace_id")
    if not tid or not isinstance(tid, str):
        tid = str(uuid.uuid4())
        meta["trace_id"] = tid
    return tid


def _validate_enrichment_safety(enrichment: dict) -> Optional[str]:
    """
    Constitutional guard: enrichment must never contain mutation-authorizing fields.
    Returns error string if violated, None if clean.
    """
    FORBIDDEN_KEYS = {
        "action", "operation", "execute", "mutate", "delta", "force", 
        "bypass", "override", "tier", "reality_mode"
    }
    found = [k for k in enrichment.keys() if k.lower() in FORBIDDEN_KEYS]
    if found:
        return f"Enrichment contains forbidden authority keys: {found}"
    return None


def validate_intent_contract(payload: dict) -> ValidationOutcome:
    """
    Validates INTENT_CONTRACT shape.
    Does NOT check AP rules, builder availability, or world rules.
    """
    if _INTENT_VALIDATOR is None:
        return ValidationOutcome(
            valid=False, trace_id=_ensure_trace_id(payload), contract_type="intent",
            error_code="SCHEMA_MISSING", error_detail="Intent schema not loaded."
        )

    trace_id = _ensure_trace_id(payload)
    
    # 1. JSON Schema Validation
    try:
        _INTENT_VALIDATOR.validate(payload)
    except ValidationError as e:
        return ValidationOutcome(
            valid=False, trace_id=trace_id, contract_type="intent",
            error_code="SCHEMA_VIOLATION", error_detail=e.message,
            validated_payload=payload
        )

    # 2. Constitutional Enrichment Guard
    if "enrichment" in payload:
        enrichment_err = _validate_enrichment_safety(payload["enrichment"])
        if enrichment_err:
            return ValidationOutcome(
                valid=False, trace_id=trace_id, contract_type="intent",
                error_code="ENRICHMENT_CONTAMINATION", error_detail=enrichment_err,
                validated_payload=payload
            )

    # 3. Shape-Only Success
    return ValidationOutcome(
        valid=True, trace_id=trace_id, contract_type="intent",
        validated_payload=payload
    )


def validate_query_contract(payload: dict) -> ValidationOutcome:
    """
    Validates QUERY_CONTRACT shape.
    Ensures bounded scope, registered type, and truth_anchor presence.
    Does NOT evaluate truth, visibility, or AP permissions.
    """
    if _QUERY_VALIDATOR is None:
        return ValidationOutcome(
            valid=False, trace_id=_ensure_trace_id(payload), contract_type="query",
            error_code="SCHEMA_MISSING", error_detail="Query schema not loaded."
        )

    trace_id = _ensure_trace_id(payload)

    # 1. JSON Schema Validation
    try:
        _QUERY_VALIDATOR.validate(payload)
    except ValidationError as e:
        return ValidationOutcome(
            valid=False, trace_id=trace_id, contract_type="query",
            error_code="SCHEMA_VIOLATION", error_detail=e.message,
            validated_payload=payload
        )

    # 2. Truth Anchor Presence (Shape Requirement)
    auth = payload.get("authority", {})
    if "truth_anchor" not in auth or not auth["truth_anchor"]:
        return ValidationOutcome(
            valid=False, trace_id=trace_id, contract_type="query",
            error_code="MISSING_TRUTH_ANCHOR", 
            error_detail="Query requires authority.truth_anchor to bind to canonical state.",
            validated_payload=payload
        )

    # 3. Shape-Only Success
    return ValidationOutcome(
        valid=True, trace_id=trace_id, contract_type="query",
        validated_payload=payload
    )


# -----------------------------------------------------------------------------
# Shadow Routing (Intent Shadow Integration)
# -----------------------------------------------------------------------------
def route_to_intent_shadow(outcome: ValidationOutcome) -> None:
    """
    Logs rejected payloads to intent_shadow. 
    Must never mutate world state or trigger execution.
    """
    if outcome.valid:
        return
        
    # Lazy import to avoid circular dependencies in bootstrap
    try:
        from godotengain.engainos.core.intent_shadow import log_rejection
        log_rejection(outcome.to_shadow_record())
    except ImportError:
        # Fallback for environments where shadow is not yet wired
        import logging
        logging.warning(
            f"[CONTRACT_VALIDATOR] Rejected {outcome.contract_type} "
            f"(trace:{outcome.trace_id}) [{outcome.error_code}]: {outcome.error_detail}"
        )


# -----------------------------------------------------------------------------
# Public Entry Point (for HTTP dispatchers)
# -----------------------------------------------------------------------------
def validate_payload(payload: dict, contract_type: str = "auto") -> ValidationOutcome:
    """
    Unified dispatcher. Routes to correct shape validator.
    Used by command_dispatcher.py / engainos_server.py endpoints.
    """
    if contract_type == "auto":
        # Heuristic routing based on payload structure
        if "query_type" in payload:
            contract_type = "query"
        elif "intent_type" in payload:
            contract_type = "intent"
        else:
            return ValidationOutcome(
                valid=False, trace_id=_ensure_trace_id(payload), 
                contract_type="unknown", error_code="UNKNOWN_CONTRACT",
                error_detail="Cannot route: missing intent_type or query_type. Wrap in correct contract."
            )

    if contract_type == "intent":
        return validate_intent_contract(payload)
    elif contract_type == "query":
        return validate_query_contract(payload)
    else:
        return ValidationOutcome(
            valid=False, trace_id=_ensure_trace_id(payload),
            contract_type=contract_type, error_code="UNSUPPORTED_CONTRACT",
            error_detail=f"Validator does not recognize contract type: {contract_type}"
        )