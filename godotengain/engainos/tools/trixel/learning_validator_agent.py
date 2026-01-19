#!/usr/bin/env python3
"""
Learning Validator Agent (Memory Governance Spec v0.1)
------------------------------------------------------

Implements:
- !zw/memory.proposal -> !zw/memory.validation -> !zon/memory.commit OR rejection

Design goals:
- Stateless core: validate_proposal(proposal, memory_index=None, config=None)
- Deterministic IDs: stable hashing
- Replayable: output contains lineage + evidence references
- Safe: never silently overwrites; never self-promotes above tentative

I/O:
- JSON always supported
- YAML supported if `yaml` (PyYAML) is available
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


# ----------------------------
# Spec v0.1 Defaults
# ----------------------------

DEFAULT_CONFIG = {
    "min_distinct_contexts": 3,
    "allowed_promotions": ["tentative"],  # canon requires EmpireKernel later
    "default_decay_rate": "slow",
    "default_revocable": True,
    "conflict_policy": "block",  # block | allow_with_note
    "timestamp_utc": True,
}


# ----------------------------
# Helpers
# ----------------------------

def utc_now_iso() -> str:
    dt = datetime.now(timezone.utc)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_hash(obj: Any) -> str:
    """
    Stable hash for IDs. Uses canonical JSON (sorted keys).
    """
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def deep_get(d: Dict[str, Any], path: List[str], default=None):
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def ensure_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def load_data(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    if path.lower().endswith((".yaml", ".yml")):
        if yaml is None:
            raise RuntimeError("PyYAML not installed; cannot read YAML.")
        data = yaml.safe_load(text)  # type: ignore
        if not isinstance(data, dict):
            raise ValueError("Expected YAML top-level mapping/object.")
        return data

    # JSON fallback
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON top-level object.")
    return data


def save_data(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    if path.lower().endswith((".yaml", ".yml")):
        if yaml is None:
            raise RuntimeError("PyYAML not installed; cannot write YAML.")
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)  # type: ignore
        return

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)


# ----------------------------
# Data Contracts (minimal)
# ----------------------------

@dataclass(frozen=True)
class Decision:
    outcome: str              # approve | reject
    promote_to: Optional[str] # tentative | None


@dataclass
class ValidationResult:
    validation_block: Dict[str, Any]
    commit_block: Optional[Dict[str, Any]]
    rejection: Optional[Dict[str, Any]]


# ----------------------------
# Conflict Scan
# ----------------------------

def scopes_overlap(scope_a: Dict[str, Any], scope_b: Dict[str, Any]) -> bool:
    """
    Conservative overlap check:
    - Overlap if any shared applies_to AND moods overlap (if both specify)
    - If one omits moods, treat as potentially overlapping.
    """
    a_applies = set(ensure_list(scope_a.get("applies_to")))
    b_applies = set(ensure_list(scope_b.get("applies_to")))

    if a_applies and b_applies and a_applies.isdisjoint(b_applies):
        return False

    a_moods = set(ensure_list(scope_a.get("moods")))
    b_moods = set(ensure_list(scope_b.get("moods")))

    if a_moods and b_moods:
        return not a_moods.isdisjoint(b_moods)

    # If either doesn't specify moods, assume possible overlap
    return True


def find_conflicts(
    statement: str,
    proposed_scope: Dict[str, Any],
    memory_index: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    memory_index expected shape (loose):
    {
      "memories": [
        {
          "memory_id": "...",
          "lesson": {"statement": "..."},
          "authority": {"level": "tentative|canon"},
          "scope": {...}
        }, ...
      ]
    }
    """
    if not memory_index:
        return []

    conflicts: List[Dict[str, Any]] = []
    for m in ensure_list(memory_index.get("memories")):
        if not isinstance(m, dict):
            continue
        m_statement = deep_get(m, ["lesson", "statement"])
        if m_statement != statement:
            continue
        m_scope = m.get("scope") if isinstance(m.get("scope"), dict) else {}
        if scopes_overlap(proposed_scope, m_scope):
            conflicts.append({
                "memory_id": m.get("memory_id"),
                "authority": deep_get(m, ["authority", "level"]),
                "scope": m_scope,
            })
    return conflicts


# ----------------------------
# Core Validation Logic
# ----------------------------

def distinct_context_count(proposal: Dict[str, Any]) -> int:
    """
    Distinct contexts are approximated by:
    - unique iteration IDs, plus
    - unique (scene_tags + medium) fingerprints
    We take the max of these two signals.
    """
    iterations = ensure_list(deep_get(proposal, ["evidence", "iterations"], []))
    it_set = {str(x) for x in iterations if x is not None}

    scene_tags = ensure_list(deep_get(proposal, ["context", "scene_tags"], []))
    medium = deep_get(proposal, ["context", "medium"], None)
    # Build context fingerprint(s)
    # If iterations exist, each iteration counts as its own context already.
    # If not, fall back to tags+medium as a single context.
    if it_set:
        return len(it_set)

    fp = {
        "scene_tags": sorted({str(t) for t in scene_tags if t is not None}),
        "medium": str(medium) if medium is not None else None,
    }
    return 1 if fp["scene_tags"] or fp["medium"] else 0


def validate_required_fields(proposal: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    prop = proposal.get("!zw/memory.proposal") if "!zw/memory.proposal" in proposal else proposal
    if not isinstance(prop, dict):
        return ["proposal_root_not_object"]

    statement = deep_get(prop, ["lesson", "statement"])
    if not statement or not isinstance(statement, str):
        errors.append("missing_lesson.statement")

    domain = deep_get(prop, ["lesson", "domain"])
    if domain is not None and not isinstance(domain, str):
        errors.append("lesson.domain_not_string")

    proposed_by = deep_get(prop, ["proposed_by", "agent"])
    if not proposed_by or not isinstance(proposed_by, str):
        errors.append("missing_proposed_by.agent")

    run_id = deep_get(prop, ["proposed_by", "run_id"])
    if run_id is not None and not isinstance(run_id, str):
        errors.append("proposed_by.run_id_not_string")

    # evidence artifacts optional but should be structured if present
    artifacts = deep_get(prop, ["evidence", "artifacts"], [])
    if artifacts is not None and not isinstance(artifacts, list):
        errors.append("evidence.artifacts_not_list")

    # context medium recommended
    medium = deep_get(prop, ["context", "medium"])
    if medium is not None and not isinstance(medium, str):
        errors.append("context.medium_not_string")

    return errors


def validate_scope_bounded(prop: Dict[str, Any]) -> List[str]:
    """
    Spec v0.1: scope must be explicitly bounded for commits.
    For proposals, we can accept missing scope, but commit will require
    at least applies_to in derived scope.
    """
    issues: List[str] = []
    # Proposal may include context.medium and intended applies-to; but the commit needs applies_to.
    # We'll derive applies_to from medium if not supplied, but enforce it exists by commit time.
    return issues


def derive_scope(prop: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive a commit scope from proposal context.
    v0.1: medium -> applies_to default mapping
    """
    ctx = prop.get("context") if isinstance(prop.get("context"), dict) else {}
    medium = ctx.get("medium")

    # default mapping
    applies_to: List[str] = []
    if isinstance(medium, str):
        if "2d" in medium:
            applies_to = ["2d_pixel_art"]
        elif "3d" in medium:
            applies_to = ["3d_geometry"]
        else:
            applies_to = [medium]
    else:
        applies_to = ["unspecified_medium"]

    scope: Dict[str, Any] = {
        "applies_to": applies_to
    }

    scene_tags = ensure_list(ctx.get("scene_tags"))
    # crude: treat some tags as moods if present
    moods = [t for t in scene_tags if isinstance(t, str) and t.lower() in {"cozy", "mystical", "dramatic", "noir"}]
    if moods:
        scope["moods"] = sorted({m.lower() for m in moods})

    # excludes can be proposed later; keep empty by default
    return scope


def validate_proposal(
    proposal: Dict[str, Any],
    memory_index: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    validator_agents: Optional[List[str]] = None,
    validator_name: str = "style_judge",
) -> ValidationResult:
    """
    Stateless validation:
      - Accepts proposal (wrapped or unwrapped)
      - Optionally checks conflicts against memory_index
      - Returns validation block and either commit or rejection
    """
    cfg = dict(DEFAULT_CONFIG)
    if config:
        cfg.update(config)

    # unwrap if needed
    prop = proposal.get("!zw/memory.proposal") if "!zw/memory.proposal" in proposal else proposal
    if not isinstance(prop, dict):
        raise ValueError("proposal must be an object/dict (or contain !zw/memory.proposal mapping).")

    proposal_id = prop.get("id")
    if not proposal_id or not isinstance(proposal_id, str):
        # deterministically derive one
        proposal_id = "memprop_" + stable_hash(prop)

    statement = deep_get(prop, ["lesson", "statement"], "")
    domain = deep_get(prop, ["lesson", "domain"], None)

    # required fields
    field_errors = validate_required_fields({"!zw/memory.proposal": prop})
    reasons: List[str] = []
    if field_errors:
        reasons.extend(field_errors)

    # distinct context gate
    dcount = distinct_context_count(prop)
    min_ctx = int(cfg["min_distinct_contexts"])
    if dcount < min_ctx:
        reasons.append(f"insufficient_distinct_contexts:{dcount}<{min_ctx}")

    # derive scope + conflicts
    proposed_scope = derive_scope(prop)
    conflicts = find_conflicts(statement, proposed_scope, memory_index)

    conflict_policy = cfg.get("conflict_policy", "block")
    if conflicts and conflict_policy == "block":
        reasons.append(f"conflicts_found:{len(conflicts)}")

    # decision
    approve = len(reasons) == 0
    promote_to = "tentative" if approve else None

    # validators list
    validators = validator_agents[:] if validator_agents else [validator_name]

    validation_id = "memval_" + stable_hash({
        "proposal_id": proposal_id,
        "statement": statement,
        "validators": validators,
        "decision": "approve" if approve else "reject",
    })

    validation_block: Dict[str, Any] = {
        "!zw/memory.validation": {
            "id": validation_id,
            "proposal_id": proposal_id,
            "validators": [{"agent": v} for v in validators],
            "checks": {
                "conflict_scan": "no_conflicts_found" if not conflicts else "conflicts_found",
                "conflicts": conflicts,
                "distinct_contexts": dcount,
                "domain_bleed_risk": "low",  # v0.1 stub; expand later
            },
            "decision": {
                "outcome": "approve" if approve else "reject",
                "promote_to": promote_to,
            },
            "notes": [] if approve else reasons,
        }
    }

    if not approve:
        rejection = {
            "proposal_id": proposal_id,
            "validation_id": validation_id,
            "outcome": "reject",
            "reasons": reasons,
            "conflicts": conflicts,
        }
        return ValidationResult(validation_block=validation_block, commit_block=None, rejection=rejection)

    # Build commit (tentative only)
    if promote_to not in cfg["allowed_promotions"]:
        # Safety: spec says validator cannot promote above tentative
        rejection = {
            "proposal_id": proposal_id,
            "validation_id": validation_id,
            "outcome": "reject",
            "reasons": [f"illegal_promotion:{promote_to}"],
            "conflicts": conflicts,
        }
        # mutate validation to reflect rejection
        validation_block["!zw/memory.validation"]["decision"]["outcome"] = "reject"
        validation_block["!zw/memory.validation"]["decision"]["promote_to"] = None
        validation_block["!zw/memory.validation"]["notes"] = rejection["reasons"]
        return ValidationResult(validation_block=validation_block, commit_block=None, rejection=rejection)

    memory_id = "vismem_" + stable_hash({
        "statement": statement,
        "scope": proposed_scope,
        "domain": domain,
    })

    commit_block: Dict[str, Any] = {
        "!zon/memory.commit": {
            "memory_id": memory_id,
            "lesson": {
                "statement": statement,
                **({"domain": domain} if isinstance(domain, str) else {}),
            },
            "authority": {
                "level": promote_to,
                "granted_by": validator_name,
                "timestamp": utc_now_iso() if cfg.get("timestamp_utc", True) else datetime.now().isoformat(timespec="seconds"),
            },
            "scope": proposed_scope,
            "lifecycle": {
                "confidence": float(prop.get("confidence_estimate", 0.75) or 0.75),
                "decay_rate": cfg.get("default_decay_rate", "slow"),
                "revocable": bool(cfg.get("default_revocable", True)),
            },
            "lineage": {
                "source_proposal": proposal_id,
                "source_validation": validation_id,
                "evidence_refs": ensure_list(deep_get(prop, ["evidence", "iterations"], [])),
                "artifact_refs": ensure_list(deep_get(prop, ["evidence", "artifacts"], [])),
            },
        }
    }

    return ValidationResult(validation_block=validation_block, commit_block=commit_block, rejection=None)


# ----------------------------
# CLI
# ----------------------------

def cmd_validate(args: argparse.Namespace) -> int:
    proposal = load_data(args.proposal)
    memory_index = load_data(args.memory_index) if args.memory_index else None

    validator_agents = args.validators.split(",") if args.validators else None
    res = validate_proposal(
        proposal=proposal,
        memory_index=memory_index,
        validator_agents=validator_agents,
        validator_name=args.validator_name,
    )

    outdir = args.outdir or "."
    os.makedirs(outdir, exist_ok=True)

    validation_path = os.path.join(outdir, f"{args.out_prefix}validation.json")
    save_data(validation_path, res.validation_block)

    if res.commit_block:
        commit_path = os.path.join(outdir, f"{args.out_prefix}commit.json")
        save_data(commit_path, res.commit_block)
        if args.update_index:
            index = memory_index if memory_index else {"memories": []}
            index.setdefault("memories", [])
            # Store the inner commit payload in index
            index["memories"].append(res.commit_block["!zon/memory.commit"])
            save_data(args.update_index, index)
        return 0

    # rejection
    rejection_path = os.path.join(outdir, f"{args.out_prefix}rejection.json")
    save_data(rejection_path, res.rejection or {"error": "unknown_rejection"})
    return 2


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Learning Validator Agent (Memory Governance Spec v0.1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate a memory proposal and emit validation + commit/rejection")
    v.add_argument("proposal", help="Path to proposal JSON/YAML")
    v.add_argument("--memory-index", dest="memory_index", default=None, help="Existing memory index JSON/YAML for conflict scan")
    v.add_argument("--outdir", default=".", help="Output directory")
    v.add_argument("--out-prefix", default="", help="Prefix for output filenames")
    v.add_argument("--validator-name", default="style_judge", help="Primary validator identity (granted_by)")
    v.add_argument("--validators", default=None, help="Comma-separated validator agents (default: validator-name only)")
    v.add_argument("--update-index", default=None, help="If set, append approved commits into this memory index file")
    v.set_defaults(func=cmd_validate)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
