# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engainos/adapters/zonj_to_gamestate.py

"""
ZONJ-to-GameState Runtime Acceptance Adapter

Purpose:
  Convert validated ZONJ / ParseArtifact scene data into an EngAInOS-controlled
  GameStateDraft, then submit that draft to EngAInOS gates for acceptance before
  anything reaches GodotSim, Godot, Trixel, Engionality, or runtime presentation.

Authority:
  TIER_AUTHORITY: ENGAINOS_TIER1
  LANE: zonj_runtime_acceptance_adapter
  STACK: engainos/adapters

This adapter is not a parser.
This adapter is not a simulator.
This adapter is not canon authority.
This adapter is not presentation.

This adapter is the runtime acceptance adapter between structured ZONJ evidence
and committed EngAInOS game state.

Core Principle:
  The adapter may carry evidence to the courthouse.
  The adapter may not issue the verdict.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import json
import re
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
class GameStateDraft:
    contract: str
    source: str
    authority_tier: int
    authority_lane: str
    scene_id: str
    source_text_id: str
    draft_status: str
    entities: List[Dict[str, Any]]
    locations: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    gate_results: List[Dict[str, Any]]
    accepted_for_runtime: bool = False
    declaration_count: int = 0
    draft_empty: bool = True
    runtime_meaningful: bool = False


# ============================================================================
# FORBIDDEN AUTHORITY FIELDS (from contract Section 7)
# ============================================================================

FORBIDDEN_AUTHORITY_FIELDS = {
    # AP authority
    "ap_allowed",
    "ap_allowed_true",
    "allowed",
    "allowed_true",

    # Canon authority
    "canon",
    "canon_true",
    "canon_truth",
    "canon_approved",

    # Runtime acceptance / mutation
    "accepted_for_runtime",
    "runtime_mutation",
    "runtime_accepted",

    # Direct spawn / despawn
    "spawn",
    "despawn",
    "direct_spawn",

    # Quest completion
    "quest_complete",
    "quest_completed",
    "complete_quest",

    # Spatial / simulation authority
    "position",
    "velocity",
    "collision",

    # Combat / inventory mutation authority
    "health",
    "inventory",

    # Render authority
    "render_asset_authority",
    "render_asset",
    "rendered_assets",
}


# ============================================================================
# FILE I/O
# ============================================================================

def load_json_file(path: Path) -> Dict[str, Any]:
    """
    Read JSON from disk.
    Return dictionary.
    Raise ValueError if the JSON root is not a dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be a dictionary, got {type(data).__name__}")
    
    return data


def write_json_file(path: Path, data: Dict[str, Any]) -> None:
    """
    Write JSON to disk using indent=2 and sort_keys=True.
    Parent directories must be created.
    This function may write only to the declared gamestate draft staging folder,
    unless a test path is explicitly passed by the caller.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


# ============================================================================
# FORBIDDEN FIELD SCANNING (KEYS ONLY)
# ============================================================================

def find_forbidden_fields(value: Any, path: str = "$") -> List[str]:
    """
    Recursively scan dictionaries and lists for forbidden authority field names.

    This function checks dictionary keys only.

    This function must never scan string values, prose descriptions, names,
    dialogue, lore text, comments, warnings, or narrative content.

    A value like "Health Potion" is allowed.
    A key like "health" is rejected.

    A value like "the spawn point was overgrown" is allowed.
    A key like "spawn" is rejected.
    """
    violations: List[str] = []
    
    if isinstance(value, dict):
        for key, child in value.items():
            current_path = f"{path}.{key}" if path != "$" else key
            if key in FORBIDDEN_AUTHORITY_FIELDS:
                violations.append(f"{current_path} (forbidden key: {key})")
            violations.extend(find_forbidden_fields(child, current_path))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            current_path = f"{path}[{idx}]"
            violations.extend(find_forbidden_fields(item, current_path))
    
    return violations


# ============================================================================
# GATES
# ============================================================================

def gate_required_top_level_fields(packet: Dict[str, Any]) -> GateResult:
    """
    Validate required packet fields.
    """
    required = ["contract", "source", "scene_id", "source_text_id"]
    missing = [f for f in required if f not in packet]
    
    if missing:
        return GateResult(
            "GATE_REQUIRED_TOP_LEVEL_FIELDS",
            "FALSE",
            f"Missing required fields: {missing}",
            {"missing": missing}
        )
    
    return GateResult(
        "GATE_REQUIRED_TOP_LEVEL_FIELDS",
        "TRUE",
        "required fields present"
    )


def gate_scene_id_present(packet: Dict[str, Any]) -> GateResult:
    """
    Validate scene_id.
    """
    scene_id = packet.get("scene_id")
    
    if not isinstance(scene_id, str) or not scene_id.strip():
        return GateResult(
            "GATE_SCENE_ID_PRESENT",
            "FALSE",
            "scene_id must be a non-empty string"
        )
    
    return GateResult(
        "GATE_SCENE_ID_PRESENT",
        "TRUE",
        "scene_id present"
    )


def gate_no_runtime_authority_claim(packet: Dict[str, Any]) -> GateResult:
    """
    Reject forbidden authority fields.
    """
    violations = find_forbidden_fields(packet)
    
    if violations:
        return GateResult(
            "GATE_NO_RUNTIME_AUTHORITY_CLAIM",
            "FALSE",
            f"Forbidden authority fields found: {violations}",
            {"violations": violations}
        )
    
    return GateResult(
        "GATE_NO_RUNTIME_AUTHORITY_CLAIM",
        "TRUE",
        "no forbidden authority fields found"
    )


def gate_declared_records_have_trace(packet: Dict[str, Any]) -> GateResult:
    """
    Validate source_span and confidence on all declarations.
    """
    entities = packet.get("declared_entities", [])
    locations = packet.get("declared_locations", [])
    events = packet.get("declared_events", [])
    
    total_declarations = len(entities) + len(locations) + len(events)
    
    if total_declarations == 0:
        return GateResult(
            "GATE_DECLARED_RECORDS_HAVE_TRACE",
            "BYPASS",
            "no declarations present"
        )
    
    violations = []
    
    for idx, entity in enumerate(entities):
        if "source_span" not in entity:
            violations.append(f"declared_entities[{idx}] missing source_span")
        if "confidence" not in entity:
            violations.append(f"declared_entities[{idx}] missing confidence")
    
    for idx, location in enumerate(locations):
        if "source_span" not in location:
            violations.append(f"declared_locations[{idx}] missing source_span")
        if "confidence" not in location:
            violations.append(f"declared_locations[{idx}] missing confidence")
    
    for idx, event in enumerate(events):
        if "source_span" not in event:
            violations.append(f"declared_events[{idx}] missing source_span")
        if "confidence" not in event:
            violations.append(f"declared_events[{idx}] missing confidence")
    
    if violations:
        return GateResult(
            "GATE_DECLARED_RECORDS_HAVE_TRACE",
            "FALSE",
            f"Declarations missing trace evidence: {violations}",
            {"violations": violations}
        )
    
    return GateResult(
        "GATE_DECLARED_RECORDS_HAVE_TRACE",
        "TRUE",
        "declarations include trace evidence"
    )


def gate_declaration_count_recorded(draft: GameStateDraft) -> GateResult:
    """
    Validate declaration count is recorded.
    """
    if not hasattr(draft, "declaration_count"):
        return GateResult(
            "GATE_DECLARATION_COUNT_RECORDED",
            "FALSE",
            "declaration_count not present"
        )
    
    if not hasattr(draft, "draft_empty"):
        return GateResult(
            "GATE_DECLARATION_COUNT_RECORDED",
            "FALSE",
            "draft_empty not present"
        )
    
    if not hasattr(draft, "runtime_meaningful"):
        return GateResult(
            "GATE_DECLARATION_COUNT_RECORDED",
            "FALSE",
            "runtime_meaningful not present"
        )
    
    return GateResult(
        "GATE_DECLARATION_COUNT_RECORDED",
        "TRUE",
        "declaration count recorded"
    )


def gate_output_contract_is_gamestate_draft(draft: GameStateDraft) -> GateResult:
    """
    Validate output contract is exactly engainos.gamestate_draft.v1.
    """
    if draft.contract != "tier1.engainos.gamestate_draft.v1":
        return GateResult(
            "GATE_OUTPUT_CONTRACT_IS_GAMESTATE_DRAFT",
            "FALSE",
            f"Invalid contract: {draft.contract}"
        )
    
    return GateResult(
        "GATE_OUTPUT_CONTRACT_IS_GAMESTATE_DRAFT",
        "TRUE",
        "output contract valid"
    )


def gate_accepted_for_runtime_false(draft: GameStateDraft) -> GateResult:
    """
    Validate accepted_for_runtime is False.
    """
    if draft.accepted_for_runtime is not False:
        return GateResult(
            "GATE_ACCEPTED_FOR_RUNTIME_FALSE",
            "FALSE",
            "accepted_for_runtime must be False"
        )
    
    return GateResult(
        "GATE_ACCEPTED_FOR_RUNTIME_FALSE",
        "TRUE",
        "accepted_for_runtime remains false"
    )


def gate_no_filename_collision(output_path: Path, scene_id: str, in_memory_only: bool = False) -> GateResult:
    """
    Prevent silent clobbering of a different scene draft.

    TRUE:
      - output_path does not exist
      - OR output_path exists and contains the same scene_id

    FALSE:
      - output_path exists
      - AND it contains a different scene_id

    BYPASS:
      - disk write is disabled for an explicit in-memory test path

    This gate protects the draft folder from sanitized filename collisions.
    """
    if in_memory_only:
        return GateResult(
            "GATE_NO_FILENAME_COLLISION",
            "BYPASS",
            "in-memory test mode, disk write disabled"
        )
    
    if not output_path.exists():
        return GateResult(
            "GATE_NO_FILENAME_COLLISION",
            "TRUE",
            "output path does not exist"
        )
    
    try:
        existing = load_json_file(output_path)
        existing_scene_id = existing.get("scene_id")
        
        if existing_scene_id == scene_id:
            return GateResult(
                "GATE_NO_FILENAME_COLLISION",
                "TRUE",
                "output path exists with same scene_id"
            )
        else:
            return GateResult(
                "GATE_NO_FILENAME_COLLISION",
                "FALSE",
                f"output path already contains scene_id '{existing_scene_id}', refusing to overwrite with '{scene_id}'",
                {"existing_scene_id": existing_scene_id, "current_scene_id": scene_id}
            )
    except Exception as e:
        return GateResult(
            "GATE_NO_FILENAME_COLLISION",
            "FALSE",
            f"Failed to read existing draft: {e}"
        )


def _imported_module_names(script_path: Path) -> List[str]:
    """
    Return module names imported by this script.

    This checks actual Python import statements only.
    It does not scan docstrings, comments, prose, variable names, or string values.
    """
    source = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module)

    return imported


def _imports_forbidden_module(script_path: Path, forbidden_root: str) -> bool:
    """
    TRUE when an actual import targets forbidden_root or one of its submodules.
    """
    forbidden_root = forbidden_root.lower()
    for module_name in _imported_module_names(script_path):
        lowered = module_name.lower()
        if lowered == forbidden_root or lowered.startswith(f"{forbidden_root}."):
            return True
    return False


def gate_no_godotsim_imports(script_path: Path) -> GateResult:
    """
    Validate script does not import GodotSim.

    This gate checks import statements only.
    It must not fail because GodotSim appears in docstrings or comments.
    """
    try:
        if _imports_forbidden_module(script_path, "godotsim"):
            return GateResult(
                "GATE_NO_GODOTSIM_IMPORTS",
                "FALSE",
                "script imports GodotSim"
            )
        return GateResult(
            "GATE_NO_GODOTSIM_IMPORTS",
            "TRUE",
            "no GodotSim imports"
        )
    except Exception as e:
        return GateResult(
            "GATE_NO_GODOTSIM_IMPORTS",
            "FALSE",
            f"failed to inspect imports: {e}"
        )


def gate_no_trixel_imports(script_path: Path) -> GateResult:
    """
    Validate script does not import Trixel.

    This gate checks import statements only.
    It must not fail because Trixel appears in docstrings or comments.
    """
    try:
        if _imports_forbidden_module(script_path, "trixel"):
            return GateResult(
                "GATE_NO_TRIXEL_IMPORTS",
                "FALSE",
                "script imports Trixel"
            )
        return GateResult(
            "GATE_NO_TRIXEL_IMPORTS",
            "TRUE",
            "no Trixel imports"
        )
    except Exception as e:
        return GateResult(
            "GATE_NO_TRIXEL_IMPORTS",
            "FALSE",
            f"failed to inspect imports: {e}"
        )


def gate_no_mettaext_parser_imports(script_path: Path) -> GateResult:
    """
    Validate script does not import Mettaext parser internals.

    This gate checks import statements only.
    It must not fail because Mettaext or ParseArtifact appears in docstrings or comments.
    """
    try:
        for module_name in _imported_module_names(script_path):
            lowered = module_name.lower()
            if lowered == "mettaext" or lowered.startswith("mettaext."):
                return GateResult(
                    "GATE_NO_METTAEXT_PARSER_IMPORTS",
                    "FALSE",
                    f"script imports Mettaext module: {module_name}"
                )

        return GateResult(
            "GATE_NO_METTAEXT_PARSER_IMPORTS",
            "TRUE",
            "no Mettaext parser imports"
        )
    except Exception as e:
        return GateResult(
            "GATE_NO_METTAEXT_PARSER_IMPORTS",
            "FALSE",
            f"failed to inspect imports: {e}"
        )


# ============================================================================
# NORMALIZATION
# ============================================================================

def normalize_entities(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert declared_entities into draft entity records.
    Preserve evidence fields.
    Do not add runtime fields.
    """
    entities = packet.get("declared_entities", [])
    normalized = []
    
    for entity in entities:
        record = {
            "entity_id": entity.get("entity_id"),
            "name": entity.get("name"),
            "entity_type": entity.get("entity_type"),
            "source_span": entity.get("source_span"),
            "confidence": entity.get("confidence"),
        }
        normalized.append(record)
    
    return normalized


def normalize_locations(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert declared_locations into draft location records.
    Preserve evidence fields.
    Do not add spatial placement authority.
    """
    locations = packet.get("declared_locations", [])
    normalized = []
    
    for location in locations:
        record = {
            "location_id": location.get("location_id") or location.get("name"),
            "name": location.get("name"),
            "source_span": location.get("source_span"),
            "confidence": location.get("confidence"),
        }
        normalized.append(record)
    
    return normalized


def normalize_events(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert declared_events into draft event records.
    Preserve evidence fields.
    Do not complete quests.
    """
    events = packet.get("declared_events", [])
    normalized = []
    
    for event in events:
        record = {
            "event_id": event.get("event_id"),
            "actor": event.get("actor"),
            "action": event.get("action"),
            "target": event.get("target"),
            "source_span": event.get("source_span"),
            "confidence": event.get("confidence"),
        }
        normalized.append(record)
    
    return normalized


# ============================================================================
# BUILD DRAFT
# ============================================================================

def build_gamestate_draft(packet: Dict[str, Any], output_path: Optional[Path] = None, in_memory_only: bool = False) -> GameStateDraft:
    """
    Run input gates.
    Normalize declarations.
    Build GameStateDraft.
    Always set accepted_for_runtime=False.
    If any required gate is FALSE, draft_status='REJECTED_BY_ADAPTER'.
    Otherwise draft_status='PENDING_ACCEPTANCE'.
    """
    gate_results = []
    
    # Run input gates
    gate_results.append(gate_required_top_level_fields(packet))
    gate_results.append(gate_scene_id_present(packet))
    gate_results.append(gate_no_runtime_authority_claim(packet))
    gate_results.append(gate_declared_records_have_trace(packet))
    
    # Normalize declarations
    entities = normalize_entities(packet)
    locations = normalize_locations(packet)
    events = normalize_events(packet)
    
    declaration_count = len(entities) + len(locations) + len(events)
    draft_empty = declaration_count == 0
    runtime_meaningful = not draft_empty
    
    # Determine draft status
    any_false = any(g.status == "FALSE" for g in gate_results)
    draft_status = "REJECTED_BY_ADAPTER" if any_false else "PENDING_ACCEPTANCE"
    
    # Build draft
    draft = GameStateDraft(
        contract="tier1.engainos.gamestate_draft.v1",
        source="tier1.engainos.zonj_runtime_acceptance_adapter",
        authority_tier=1,
        authority_lane="zonj_runtime_acceptance_adapter",
        scene_id=packet.get("scene_id", ""),
        source_text_id=packet.get("source_text_id", ""),
        draft_status=draft_status,
        entities=entities,
        locations=locations,
        events=events,
        gate_results=[asdict(g) for g in gate_results],
        accepted_for_runtime=False,
        declaration_count=declaration_count,
        draft_empty=draft_empty,
        runtime_meaningful=runtime_meaningful,
    )
    
    # Run output gates
    gate_results.append(gate_declaration_count_recorded(draft))
    gate_results.append(gate_output_contract_is_gamestate_draft(draft))
    gate_results.append(gate_accepted_for_runtime_false(draft))
    
    # Run filename collision gate if output_path provided
    if output_path is not None:
        collision_result = gate_no_filename_collision(output_path, draft.scene_id, in_memory_only)
        gate_results.append(collision_result)
    
    # Run script import gates
    script_path = Path(__file__)
    gate_results.append(gate_no_godotsim_imports(script_path))
    gate_results.append(gate_no_trixel_imports(script_path))
    gate_results.append(gate_no_mettaext_parser_imports(script_path))
    
    # Update draft with all gate results, recomputing draft_status based on all gates
    final_any_false = any(g.status == "FALSE" for g in gate_results)
    final_draft_status = "REJECTED_BY_ADAPTER" if final_any_false else "PENDING_ACCEPTANCE"

    # Update draft with all gate results
    draft = GameStateDraft(
        contract=draft.contract,
        source=draft.source,
        authority_tier=draft.authority_tier,
        authority_lane=draft.authority_lane,
        scene_id=draft.scene_id,
        source_text_id=draft.source_text_id,
        draft_status=final_draft_status,
        entities=draft.entities,
        locations=draft.locations,
        events=draft.events,
        gate_results=[asdict(g) for g in gate_results],
        accepted_for_runtime=draft.accepted_for_runtime,
        declaration_count=draft.declaration_count,
        draft_empty=draft.draft_empty,
        runtime_meaningful=draft.runtime_meaningful,
    )
    
    return draft


def draft_to_dict(draft: GameStateDraft) -> Dict[str, Any]:
    """
    Convert dataclass to dictionary using asdict.
    Verify accepted_for_runtime remains False.
    """
    data = asdict(draft)
    
    if data.get("accepted_for_runtime") is not False:
        raise ValueError("accepted_for_runtime must be False")
    
    return data


# ============================================================================
# FILENAME UTILITIES
# ============================================================================

def safe_scene_filename(scene_id: str) -> str:
    """
    Convert scene_id into a safe filename.
    Allowed characters: letters, numbers, dot, dash, underscore.
    Replace all other characters with underscore.
    Append '.gamestate_draft.json'.
    """
    safe = re.sub(r'[^a-zA-Z0-9._-]', '_', scene_id)
    return f"{safe}.gamestate_draft.json"


def default_output_path(scene_id: str, project_root: Path) -> Path:
    """
    Return:
    project_root / 'data' / 'engainos' / 'gamestate_drafts' / safe_scene_filename(scene_id)
    """
    return project_root / 'data' / 'engainos' / 'gamestate_drafts' / safe_scene_filename(scene_id)


# ============================================================================
# PRINT
# ============================================================================

def print_gate_results(script_name: str, results: List[GateResult]) -> None:
    """
    Print each gate line.
    Print final ALL_GATES line.
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
      python engainos/adapters/zonj_to_gamestate.py input_packet.json

    Optional:
      python engainos/adapters/zonj_to_gamestate.py input_packet.json --project-root /path/to/EngAIn
      python engainos/adapters/zonj_to_gamestate.py input_packet.json --in-memory

    Exit codes:
      0 = adapter gates passed or bypassed
      1 = one or more gates failed
      2 = CLI usage, read error, write error, or malformed JSON
    """
    if argv is None:
        argv = sys.argv[1:]
    
    if len(argv) < 1:
        print("Usage: python engainos/adapters/zonj_to_gamestate.py input_packet.json [--project-root PATH] [--in-memory]")
        return 2
    
    input_path = Path(argv[0])
    
    # Parse optional flags
    project_root = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
    in_memory_only = "--in-memory" in argv
    
    if "--project-root" in argv:
        idx = argv.index("--project-root")
        if idx + 1 < len(argv):
            project_root = Path(argv[idx + 1])
    
    # Load input
    try:
        packet = load_json_file(input_path)
    except Exception as e:
        print(f"Error loading input: {e}")
        return 2
    
    # Determine output path
    output_path = default_output_path(packet.get("scene_id", "unknown"), project_root)
    
    # Build draft (includes all gates)
    draft = build_gamestate_draft(packet, output_path, in_memory_only)
    
    # Print gates
    gate_results = [GateResult(**g) for g in draft.gate_results]
    print_gate_results("zonj_to_gamestate", gate_results)
    
    # Check if any gate failed
    any_false = any(g.status == "FALSE" for g in gate_results)
    
    if any_false:
        print("Draft rejected by adapter gates. Not writing output.")
        return 1
    
    # Write output only if all gates passed
    if not in_memory_only:
        try:
            draft_dict = draft_to_dict(draft)
            write_json_file(output_path, draft_dict)
            print(f"Draft written to: {output_path}")
        except Exception as e:
            print(f"Error writing output: {e}")
            return 2
    else:
        print("In-memory mode: draft not written to disk")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())