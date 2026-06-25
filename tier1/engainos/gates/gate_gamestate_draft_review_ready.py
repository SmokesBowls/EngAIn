# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/gates/gate_gamestate_draft_review_ready.py

"""
EngAInOS GameState Draft Review Gate

Purpose:
  Determine whether an EngAInOS GameStateDraft is ready for review.
  
  This gate does NOT accept runtime state.
  This gate does NOT commit GameState.
  This gate does NOT spawn entities.
  This gate does NOT call GodotSim.
  This gate does NOT start workers.
  
  This gate only says whether a draft is safe to place before the next
  EngAInOS acceptance decision.

Authority:
  TIER_AUTHORITY: ENGAINOS_TIER1
  LANE: gamestate_draft_review_gate
  STACK: engainos/gates

One-Line Rule:
  A GameStateDraft may become REVIEW_READY, but it may not become
  ACCEPTED_GAMESTATE in this gate.

CRITICAL INVARIANT:
  This gate detects forbidden authority claims in the input draft,
  but its output is structurally incapable of carrying those claims forward.
  The output fields accepted_for_runtime, committed_gamestate, and starts_workers
  are HARDCODED to False, never copied from input.
"""

from __future__ import annotations
GATE_LIFECYCLE = "SUPPORT_LIBRARY"
GATE_BOARD = "ENGAINOS_SYSTEM_CONTRACT_BOARD"


from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import json
import sys

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass(frozen=True)
class GateResult:
    gate_name: str
    status: Literal["TRUE", "FALSE", "BYPASS"]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class DraftReviewResult:
    contract: str
    source: str
    authority_tier: int
    authority_lane: str
    scene_id: str
    review_status: Literal[
        "GAMESTATE_DRAFT_REVIEW_READY",
        "GAMESTATE_DRAFT_REVIEW_REJECTED",
        "BLOCKED_PENDING_TIER1_REVIEW",
    ]
    accepted_for_runtime: bool
    committed_gamestate: bool
    starts_workers: bool
    gate_results: List[Dict[str, Any]]

# ============================================================================
# FILE I/O
# ============================================================================

def load_json_file(path: Path) -> Dict[str, Any]:
    """
    Load a GameStateDraft JSON file.
    Return a dictionary.
    Raise ValueError if root is not a dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be a dictionary, got {type(data).__name__}")
    
    return data


def format_child_path(parent_path: str, key: str) -> str:
    if not parent_path:
        return key
    return f"{parent_path}.{key}"


def format_list_path(parent_path: str, index: int) -> str:
    if not parent_path:
        return f"[{index}]"
    return f"{parent_path}[{index}]"


def find_forbidden_keys(value: Any, forbidden_keys: set[str], path: str = "") -> List[str]:
    """
    Recursively find exact-token forbidden authority claims in dict keys and
    string values. Paths are emitted without a '$' root prefix, e.g.:
      top_level_key
      entities[0].metadata.worker_start
      entities[0].tags[1]
      a.b.c.d.e

    Matching is exact token only. A string like 'not_worker_start' is not a hit.
    """
    hits = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = format_child_path(path, str(key))

            if key in forbidden_keys:
                hits.append(child_path)

            hits.extend(find_forbidden_keys(child, forbidden_keys, child_path))

    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = format_list_path(path, index)
            hits.extend(find_forbidden_keys(child, forbidden_keys, child_path))

    elif isinstance(value, str) and value in forbidden_keys:
        hits.append(path)

    return hits


# ============================================================================
# GATES
# ============================================================================

def gate_draft_contract_valid(draft: Dict[str, Any]) -> GateResult:
    """
    Validate draft contract.
    """
    if draft.get("contract") != "tier1.engainos.gamestate_draft.v1":
        return GateResult(
            "GATE_DRAFT_CONTRACT_VALID",
            "FALSE",
            f"Invalid contract: {draft.get('contract')}",
            {"expected": "tier1.engainos.gamestate_draft.v1", "actual": draft.get("contract")}
        )
    
    return GateResult(
        "GATE_DRAFT_CONTRACT_VALID",
        "TRUE",
        "draft contract is valid"
    )

def gate_draft_source_valid(draft: Dict[str, Any]) -> GateResult:
    """
    Validate draft source.
    """
    if draft.get("source") != "tier1.engainos.zonj_runtime_acceptance_adapter":
        return GateResult(
            "GATE_DRAFT_SOURCE_VALID",
            "FALSE",
            f"Invalid source: {draft.get('source')}",
            {"expected": "tier1.engainos.zonj_runtime_acceptance_adapter", "actual": draft.get("source")}
        )
    
    return GateResult(
        "GATE_DRAFT_SOURCE_VALID",
        "TRUE",
        "draft source is valid"
    )

def gate_draft_authority_valid(draft: Dict[str, Any]) -> GateResult:
    """
    Validate authority_tier and authority_lane.
    """
    authority_tier = draft.get("authority_tier")
    authority_lane = draft.get("authority_lane")
    
    if authority_tier != 1:
        return GateResult(
            "GATE_DRAFT_AUTHORITY_VALID",
            "FALSE",
            f"Invalid authority_tier: {authority_tier}",
            {"expected": 1, "actual": authority_tier}
        )
    
    if authority_lane != "zonj_runtime_acceptance_adapter":
        return GateResult(
            "GATE_DRAFT_AUTHORITY_VALID",
            "FALSE",
            f"Invalid authority_lane: {authority_lane}",
            {"expected": "zonj_runtime_acceptance_adapter", "actual": authority_lane}
        )
    
    return GateResult(
        "GATE_DRAFT_AUTHORITY_VALID",
        "TRUE",
        "authority_tier and authority_lane are valid"
    )

def gate_draft_status_pending_acceptance(draft: Dict[str, Any]) -> GateResult:
    """
    Validate draft_status is PENDING_ACCEPTANCE.
    REJECTED_BY_ADAPTER must fail.
    
    This gate intentionally re-checks the adapter verdict.
    A rejected adapter draft is not review-ready.
    """
    draft_status = draft.get("draft_status")
    
    if draft_status == "REJECTED_BY_ADAPTER":
        return GateResult(
            "GATE_DRAFT_STATUS_PENDING_ACCEPTANCE",
            "FALSE",
            "draft was rejected by adapter, not review-ready",
            {"actual": draft_status}
        )
    
    if draft_status != "PENDING_ACCEPTANCE":
        return GateResult(
            "GATE_DRAFT_STATUS_PENDING_ACCEPTANCE",
            "FALSE",
            f"Invalid draft_status: {draft_status}",
            {"expected": "PENDING_ACCEPTANCE", "actual": draft_status}
        )
    
    return GateResult(
        "GATE_DRAFT_STATUS_PENDING_ACCEPTANCE",
        "TRUE",
        "draft_status is PENDING_ACCEPTANCE"
    )

def gate_accepted_for_runtime_false(draft: Dict[str, Any]) -> GateResult:
    """
    Validate accepted_for_runtime remains False in the INPUT draft.
    
    This is a hard authority gate.
    If the input draft claims accepted_for_runtime=True, this gate rejects it.
    The output DraftReviewResult will still have accepted_for_runtime=False.
    """
    if draft.get("accepted_for_runtime") is not False:
        return GateResult(
            "GATE_ACCEPTED_FOR_RUNTIME_FALSE",
            "FALSE",
            "input draft claims accepted_for_runtime is not False",
            {"actual": draft.get("accepted_for_runtime")}
        )
    
    return GateResult(
        "GATE_ACCEPTED_FOR_RUNTIME_FALSE",
        "TRUE",
        "input draft accepted_for_runtime is False"
    )

def gate_adapter_gate_results_present(draft: Dict[str, Any]) -> GateResult:
    """
    Validate adapter gate_results exist and are non-empty.
    """
    gate_results = draft.get("gate_results")
    
    if gate_results is None:
        return GateResult(
            "GATE_ADAPTER_GATE_RESULTS_PRESENT",
            "FALSE",
            "gate_results field is missing"
        )
    
    if not isinstance(gate_results, list):
        return GateResult(
            "GATE_ADAPTER_GATE_RESULTS_PRESENT",
            "FALSE",
            f"gate_results must be a list, got {type(gate_results).__name__}"
        )
    
    if len(gate_results) == 0:
        return GateResult(
            "GATE_ADAPTER_GATE_RESULTS_PRESENT",
            "FALSE",
            "gate_results is empty"
        )
    
    return GateResult(
        "GATE_ADAPTER_GATE_RESULTS_PRESENT",
        "TRUE",
        f"gate_results present with {len(gate_results)} entries"
    )

def gate_adapter_gate_results_all_true_or_bypass(draft: Dict[str, Any]) -> GateResult:
    """
    Validate every adapter gate result is TRUE or BYPASS.
    FALSE means the adapter found a problem and the draft is not review-ready.
    
    This gate intentionally performs defense-in-depth.
    It does not trust draft_status alone.
    It verifies that the adapter's recorded gates also support the verdict.
    """
    gate_results = draft.get("gate_results", [])
    
    if not isinstance(gate_results, list):
        return GateResult(
            "GATE_ADAPTER_GATE_RESULTS_ALL_TRUE_OR_BYPASS",
            "FALSE",
            "gate_results is not a list"
        )
    
    violations = []
    
    for idx, gate in enumerate(gate_results):
        if not isinstance(gate, dict):
            violations.append(f"gate_results[{idx}] is not a dict")
            continue
        
        gate_name = gate.get("gate_name")
        status = gate.get("status")
        message = gate.get("message")
        
        if gate_name is None:
            violations.append(f"gate_results[{idx}] missing gate_name")
        
        if status is None:
            violations.append(f"gate_results[{idx}] missing status")
        
        if message is None:
            violations.append(f"gate_results[{idx}] missing message")
        
        if status not in ["TRUE", "FALSE", "BYPASS"]:
            violations.append(f"gate_results[{idx}] has invalid status: {status}")
        
        if status == "FALSE":
            violations.append(f"gate_results[{idx}] ({gate_name}) is FALSE: {message}")
    
    if violations:
        return GateResult(
            "GATE_ADAPTER_GATE_RESULTS_ALL_TRUE_OR_BYPASS",
            "FALSE",
            f"Adapter gate violations: {violations}",
            {"violations": violations}
        )
    
    return GateResult(
        "GATE_ADAPTER_GATE_RESULTS_ALL_TRUE_OR_BYPASS",
        "TRUE",
        "all adapter gate results are TRUE or BYPASS"
    )

def gate_declaration_flags_present(draft: Dict[str, Any]) -> GateResult:
    """
    Validate declaration_count, draft_empty, and runtime_meaningful exist and agree.
    """
    declaration_count = draft.get("declaration_count")
    draft_empty = draft.get("draft_empty")
    runtime_meaningful = draft.get("runtime_meaningful")
    
    if declaration_count is None:
        return GateResult(
            "GATE_DECLARATION_FLAGS_PRESENT",
            "FALSE",
            "declaration_count is missing"
        )
    
    if draft_empty is None:
        return GateResult(
            "GATE_DECLARATION_FLAGS_PRESENT",
            "FALSE",
            "draft_empty is missing"
        )
    
    if runtime_meaningful is None:
        return GateResult(
            "GATE_DECLARATION_FLAGS_PRESENT",
            "FALSE",
            "runtime_meaningful is missing"
        )
    
    if not isinstance(declaration_count, int):
        return GateResult(
            "GATE_DECLARATION_FLAGS_PRESENT",
            "FALSE",
            f"declaration_count must be int, got {type(declaration_count).__name__}"
        )
    
    if not isinstance(draft_empty, bool):
        return GateResult(
            "GATE_DECLARATION_FLAGS_PRESENT",
            "FALSE",
            f"draft_empty must be bool, got {type(draft_empty).__name__}"
        )
    
    if not isinstance(runtime_meaningful, bool):
        return GateResult(
            "GATE_DECLARATION_FLAGS_PRESENT",
            "FALSE",
            f"runtime_meaningful must be bool, got {type(runtime_meaningful).__name__}"
        )
    
    # Consistency checks
    if declaration_count == 0:
        if draft_empty is not True:
            return GateResult(
                "GATE_DECLARATION_FLAGS_PRESENT",
                "FALSE",
                "declaration_count=0 but draft_empty is not True",
                {"declaration_count": declaration_count, "draft_empty": draft_empty}
            )
        if runtime_meaningful is not False:
            return GateResult(
                "GATE_DECLARATION_FLAGS_PRESENT",
                "FALSE",
                "declaration_count=0 but runtime_meaningful is not False",
                {"declaration_count": declaration_count, "runtime_meaningful": runtime_meaningful}
            )
    
    if declaration_count > 0:
        if draft_empty is not False:
            return GateResult(
                "GATE_DECLARATION_FLAGS_PRESENT",
                "FALSE",
                "declaration_count>0 but draft_empty is not False",
                {"declaration_count": declaration_count, "draft_empty": draft_empty}
            )
        if runtime_meaningful is not True:
            return GateResult(
                "GATE_DECLARATION_FLAGS_PRESENT",
                "FALSE",
                "declaration_count>0 but runtime_meaningful is not True",
                {"declaration_count": declaration_count, "runtime_meaningful": runtime_meaningful}
            )
    
    return GateResult(
        "GATE_DECLARATION_FLAGS_PRESENT",
        "TRUE",
        "declaration flags are present and consistent"
    )

def gate_no_committed_gamestate_fields(draft: Dict[str, Any]) -> GateResult:
    """
    Validate the INPUT draft does not claim committed GameState authority.
    """
    forbidden_keys = {
        "committed_gamestate",
        "accepted_gamestate",
        "accepted_runtime_state",
        "runtime_commit",
        "spawned_entities",
        "ap_allowed",
        "canon_approved",
        "accepted_for_runtime",
    }

    violations = find_forbidden_keys(draft, forbidden_keys)

    # Top-level accepted_for_runtime is allowed only when exactly False,
    # because the adapter contract requires that marker.
    if draft.get("accepted_for_runtime") is False:
        violations = [
            item for item in violations
            if item != "accepted_for_runtime"
        ]

    if violations:
        return GateResult(
            "GATE_NO_COMMITTED_GAMESTATE_FIELDS",
            "FALSE",
            f"Forbidden committed-state fields found in input draft: {violations}",
            {"violations": violations},
        )

    return GateResult(
        "GATE_NO_COMMITTED_GAMESTATE_FIELDS",
        "TRUE",
        "input draft has no committed GameState fields",
    )


def gate_no_worker_start_fields(draft: Dict[str, Any]) -> GateResult:
    """
    Validate the INPUT draft does not claim worker-start authority.
    """
    forbidden_keys = {
        "starts_workers",
        "start_workers",
        "worker_start",
        "start_worker",
        "spawn_worker",
        "spawn_workers",
        "workers_started",
        "run_godotsim",
        "launch_runtime",
        "start_runtime",
        "runtime_execute",
    }

    violations = find_forbidden_keys(draft, forbidden_keys)

    if violations:
        return GateResult(
            "GATE_NO_WORKER_START_FIELDS",
            "FALSE",
            f"Forbidden worker-start fields found in input draft: {violations}",
            {"violations": violations},
        )

    return GateResult(
        "GATE_NO_WORKER_START_FIELDS",
        "TRUE",
        "input draft has no worker-start fields",
    )

def gate_review_result_does_not_accept_runtime(result: DraftReviewResult) -> GateResult:
    """
    Validate the review gate's OUTPUT has:
    - accepted_for_runtime is False
    - committed_gamestate is False
    - starts_workers is False
    
    This gate verifies the review gate's own output invariant.
    It is a structural check, not the only defense against authority propagation.
    """
    if result.accepted_for_runtime is not False:
        return GateResult(
            "GATE_REVIEW_RESULT_DOES_NOT_ACCEPT_RUNTIME",
            "FALSE",
            "review result accepted_for_runtime must be False"
        )
    
    if result.committed_gamestate is not False:
        return GateResult(
            "GATE_REVIEW_RESULT_DOES_NOT_ACCEPT_RUNTIME",
            "FALSE",
            "review result committed_gamestate must be False"
        )
    
    if result.starts_workers is not False:
        return GateResult(
            "GATE_REVIEW_RESULT_DOES_NOT_ACCEPT_RUNTIME",
            "FALSE",
            "review result starts_workers must be False"
        )
    
    return GateResult(
        "GATE_REVIEW_RESULT_DOES_NOT_ACCEPT_RUNTIME",
        "TRUE",
        "review result output invariant is locked"
    )

# ============================================================================
# BUILD REVIEW RESULT
# ============================================================================

def build_draft_review_result(draft: Dict[str, Any]) -> DraftReviewResult:
    """
    Run all review-ready gates.
    Return GAMESTATE_DRAFT_REVIEW_READY only if all gates are TRUE or BYPASS.
    Return GAMESTATE_DRAFT_REVIEW_REJECTED if any gate is FALSE.
    Always set accepted_for_runtime=False.
    Always set committed_gamestate=False.
    Always set starts_workers=False.
    
    CRITICAL INVARIANT:
    This gate detects forbidden authority claims in the input draft,
    but its output is structurally incapable of carrying those claims forward.
    The output fields are HARDCODED to False, never copied from input.
    
    The review gate may reject a lying draft.
    The review gate may not repeat the lie in its own output.
    """
    gate_results = []
    
    # Run input gates
    gate_results.append(gate_draft_contract_valid(draft))
    gate_results.append(gate_draft_source_valid(draft))
    gate_results.append(gate_draft_authority_valid(draft))
    gate_results.append(gate_draft_status_pending_acceptance(draft))
    gate_results.append(gate_accepted_for_runtime_false(draft))
    gate_results.append(gate_adapter_gate_results_present(draft))
    gate_results.append(gate_adapter_gate_results_all_true_or_bypass(draft))
    gate_results.append(gate_declaration_flags_present(draft))
    gate_results.append(gate_no_committed_gamestate_fields(draft))
    gate_results.append(gate_no_worker_start_fields(draft))
    
    # Build locked result. Never copy authority fields from draft.
    # This is the structural invariant: the review gate cannot propagate authority claims.
    provisional_result = DraftReviewResult(
        contract="tier1.engainos.gamestate_draft_review_result.v1",
        source="tier1.engainos.gamestate_draft_review_gate",
        authority_tier=1,
        authority_lane="gamestate_draft_review_gate",
        scene_id=draft.get("scene_id", ""),
        review_status="BLOCKED_PENDING_TIER1_REVIEW",
        accepted_for_runtime=False,
        committed_gamestate=False,
        starts_workers=False,
        gate_results=[],
    )
    
    # Verify the output invariant
    gate_results.append(gate_review_result_does_not_accept_runtime(provisional_result))
    
    # Determine final review status
    final_any_false = any(g.status == "FALSE" for g in gate_results)
    final_review_status = (
        "GAMESTATE_DRAFT_REVIEW_REJECTED"
        if final_any_false
        else "GAMESTATE_DRAFT_REVIEW_READY"
    )
    
    # Return final result with hardcoded False values
    return DraftReviewResult(
        contract="tier1.engainos.gamestate_draft_review_result.v1",
        source="tier1.engainos.gamestate_draft_review_gate",
        authority_tier=1,
        authority_lane="gamestate_draft_review_gate",
        scene_id=draft.get("scene_id", ""),
        review_status=final_review_status,
        accepted_for_runtime=False,
        committed_gamestate=False,
        starts_workers=False,
        gate_results=[
            {
                "gate_name": g.gate_name,
                "status": g.status,
                "message": g.message,
                "details": g.details,
            }
            for g in gate_results
        ],
    )

# ============================================================================
# PRINT
# ============================================================================

def print_gate_results(script_name: str, results: List[GateResult]) -> None:
    """
    Print each gate line and final ALL_GATES line.
    """
    for result in results:
        print(f"[{script_name}][{result.gate_name}] {result.status}: {result.message}")
    
    any_false = any(r.status == "FALSE" for r in results)
    final = "false" if any_false else "true"
    print(f"[{script_name}][ALL_GATES] {final}")

# ============================================================================
# MAIN
# ============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI entrypoint.

    Usage:
      python engainos/gates/gate_gamestate_draft_review_ready.py path/to/draft.json

    Exit codes:
      0 = review-ready gates passed
      1 = one or more gates failed
      2 = CLI usage or file read error
    """
    if argv is None:
        argv = sys.argv[1:]
    
    if len(argv) < 1:
        print("Usage: python engainos/gates/gate_gamestate_draft_review_ready.py path/to/draft.json")
        return 2
    
    input_path = Path(argv[0])
    
    # Load draft
    try:
        draft = load_json_file(input_path)
    except Exception as e:
        print(f"Error loading draft: {e}")
        return 2
    
    # Build review result
    result = build_draft_review_result(draft)
    
    # Convert gate_results to GateResult objects for printing
    gate_results = [
        GateResult(
            gate_name=g["gate_name"],
            status=g["status"],
            message=g["message"],
            details=g["details"]
        )
        for g in result.gate_results
    ]
    
    # Print gates
    print_gate_results("gate_gamestate_draft_review_ready", gate_results)
    
    # Print result summary
    print(f"\nReview Status: {result.review_status}")
    print(f"accepted_for_runtime: {result.accepted_for_runtime}")
    print(f"committed_gamestate: {result.committed_gamestate}")
    print(f"starts_workers: {result.starts_workers}")
    
    # Exit code
    any_false = any(g.status == "FALSE" for g in gate_results)
    if any_false:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
