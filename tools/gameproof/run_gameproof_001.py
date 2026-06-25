#!/usr/bin/env python3
"""
EngAIn Game Proof #001

Purpose:
    Prove EngAIn can produce a game-shaped runtime packet without needing
    the art lane.

This script does NOT:
    - call Trixel
    - call Blender
    - call Mechanimation
    - start Godot
    - mutate runtime
    - write accepted game state

This script DOES:
    - create a tiny fake scene intake
    - create entities
    - create spatial/topology intent
    - create a game_state_draft payload
    - create a gate-style report
    - write JSON proof files

Exit codes:
    0 = proof passed
    2 = proof failed / missing required field
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "scratch" / "gameproof_001"

PROOF_ID = "gameproof_001"
SCENE_ID = "scene.gameproof_001.guard_king_gate"


@dataclass(frozen=True)
class EntityPacket:
    entity_id: str
    entity_type: str
    display_name: str
    role: str
    state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TopologyIntentPacket:
    """
    This is not render geometry.

    It is narrative/topological game intent:
    - who is near what
    - what blocks movement
    - what must remain true before runtime acceptance
    """

    artifact_id: str
    lifecycle: str
    entities: list[str]
    qualitative_spatial_links: list[dict[str, Any]]
    obstruction_links: list[dict[str, Any]]
    movement_links: list[dict[str, Any]]


@dataclass(frozen=True)
class ScenePacket:
    scene_id: str
    source: str
    summary: str
    entities: list[EntityPacket]
    topology_intent: TopologyIntentPacket


@dataclass(frozen=True)
class GameStateDraft:
    """
    This is a draft.

    It is not accepted runtime truth yet.
    """

    proof_id: str
    scene_id: str
    status: str
    created_at: str
    runtime_mutation_allowed: bool
    art_required: bool
    trixel_required: bool
    blender_required: bool
    mechanimation_required: bool
    scene_packet: dict[str, Any]
    runtime_payload: dict[str, Any]


@dataclass(frozen=True)
class GateReport:
    proof_id: str
    passed: bool
    checks_run: int
    violations: list[str]
    notes: list[str]
    files_written: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_fake_scene_packet() -> ScenePacket:
    """
    Build the smallest possible game-shaped scene.

    This is intentionally fake intake.
    The goal is proof of shape, not prose extraction.
    """

    entities = [
        EntityPacket(
            entity_id="guard_001",
            entity_type="character",
            display_name="Gate Guard",
            role="blocks_gate",
            state={
                "can_speak": True,
                "blocks_movement": True,
            },
        ),
        EntityPacket(
            entity_id="king_001",
            entity_type="character",
            display_name="King",
            role="protected_target",
            state={
                "can_speak": True,
                "authority_rank": "high",
            },
        ),
        EntityPacket(
            entity_id="gate_001",
            entity_type="place_object",
            display_name="Stone Gate",
            role="boundary",
            state={
                "open": False,
                "blocks_path": True,
            },
        ),
    ]

    topology = TopologyIntentPacket(
        artifact_id="topo.gameproof_001.guard_king_gate",
        lifecycle="PROPOSED",
        entities=[e.entity_id for e in entities],
        qualitative_spatial_links=[
            {
                "from": "guard_001",
                "relation": "in_front_of",
                "to": "gate_001",
                "required": True,
            },
            {
                "from": "king_001",
                "relation": "behind",
                "to": "gate_001",
                "required": True,
            },
        ],
        obstruction_links=[
            {
                "blocker": "gate_001",
                "blocked_path": "outside_to_throne_room",
                "required": True,
            },
            {
                "blocker": "guard_001",
                "blocked_path": "player_to_gate",
                "required": True,
            },
        ],
        movement_links=[],
    )

    return ScenePacket(
        scene_id=SCENE_ID,
        source="fake_env_rehearsal",
        summary="A guard stands before a closed stone gate while the king remains protected behind it.",
        entities=entities,
        topology_intent=topology,
    )


def normalize_scene_for_runtime(scene: ScenePacket) -> dict[str, Any]:
    """
    Convert scene packet into a runtime-like payload.

    This is not Godot output.
    This is the shape EngAIn would hand to a runtime layer after gates.
    """

    return {
        "packet_type": "game_state_draft",
        "scene_id": scene.scene_id,
        "entities": [
            {
                "id": entity.entity_id,
                "type": entity.entity_type,
                "name": entity.display_name,
                "role": entity.role,
                "state": entity.state,
            }
            for entity in scene.entities
        ],
        "blocking": {
            "closed_boundaries": ["gate_001"],
            "active_blockers": ["guard_001", "gate_001"],
        },
        "topology": asdict(scene.topology_intent),
        "runtime_intent": {
            "player_can_request_dialogue": True,
            "player_can_pass_gate": False,
            "requires_gate_acceptance_before_runtime_mutation": True,
        },
        "presentation": {
            "art_assets_required_now": False,
            "placeholder_render_allowed": True,
            "trixel_payload": None,
            "blender_payload": None,
            "mechanimation_payload": None,
        },
    }


def validate_game_state_draft(draft: GameStateDraft) -> list[str]:
    """
    Hard true/false checks.

    If any required shape is missing, return violations.
    """

    violations: list[str] = []

    payload = draft.runtime_payload

    if draft.runtime_mutation_allowed is not False:
        violations.append("runtime_mutation_allowed must be false for proof draft")

    if draft.art_required is not False:
        violations.append("art_required must be false for Game Proof #001")

    if draft.trixel_required is not False:
        violations.append("trixel_required must be false for Game Proof #001")

    if draft.blender_required is not False:
        violations.append("blender_required must be false for Game Proof #001")

    if draft.mechanimation_required is not False:
        violations.append("mechanimation_required must be false for Game Proof #001")

    if payload.get("packet_type") != "game_state_draft":
        violations.append("runtime_payload.packet_type must be game_state_draft")

    if not payload.get("scene_id"):
        violations.append("runtime_payload.scene_id is required")

    entities = payload.get("entities")
    if not isinstance(entities, list) or len(entities) < 1:
        violations.append("runtime_payload.entities must be a non-empty list")

    topology = payload.get("topology")
    if not isinstance(topology, dict):
        violations.append("runtime_payload.topology must be an object")
    else:
        if topology.get("lifecycle") != "PROPOSED":
            violations.append("topology.lifecycle must be PROPOSED")
        if not topology.get("entities"):
            violations.append("topology.entities is required")

    presentation = payload.get("presentation")
    if not isinstance(presentation, dict):
        violations.append("runtime_payload.presentation must be an object")
    else:
        if presentation.get("trixel_payload") is not None:
            violations.append("trixel_payload must be null")
        if presentation.get("blender_payload") is not None:
            violations.append("blender_payload must be null")
        if presentation.get("mechanimation_payload") is not None:
            violations.append("mechanimation_payload must be null")

    return violations


def run_proof() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("EngAIn Game Proof #001")
    print("=" * 72)
    print(f"Repo root : {REPO_ROOT}")
    print(f"Output dir: {OUTPUT_DIR}")
    print()

    print("[1/5] Building fake scene packet")
    scene = build_fake_scene_packet()
    scene_payload = asdict(scene)
    scene_path = OUTPUT_DIR / "scene_packet.json"
    write_json(scene_path, scene_payload)
    print(f"      wrote: {scene_path}")

    print()
    print("[2/5] Normalizing to runtime-like game_state_draft payload")
    runtime_payload = normalize_scene_for_runtime(scene)
    runtime_path = OUTPUT_DIR / "runtime_payload.json"
    write_json(runtime_path, runtime_payload)
    print(f"      wrote: {runtime_path}")

    print()
    print("[3/5] Building GameStateDraft")
    draft = GameStateDraft(
        proof_id=PROOF_ID,
        scene_id=scene.scene_id,
        status="DRAFT_NOT_ACCEPTED",
        created_at=utc_now(),
        runtime_mutation_allowed=False,
        art_required=False,
        trixel_required=False,
        blender_required=False,
        mechanimation_required=False,
        scene_packet=scene_payload,
        runtime_payload=runtime_payload,
    )

    draft_path = OUTPUT_DIR / "game_state_draft.json"
    write_json(draft_path, asdict(draft))
    print(f"      wrote: {draft_path}")

    print()
    print("[4/5] Running hard true/false checks")
    violations = validate_game_state_draft(draft)

    files_written = [
        str(scene_path.relative_to(REPO_ROOT)),
        str(runtime_path.relative_to(REPO_ROOT)),
        str(draft_path.relative_to(REPO_ROOT)),
    ]

    report = GateReport(
        proof_id=PROOF_ID,
        passed=not violations,
        checks_run=12,
        violations=violations,
        notes=[
            "No Trixel call was made.",
            "No Blender call was made.",
            "No Mechanimation call was made.",
            "No Godot runtime mutation was made.",
            "Payload is a draft only.",
            "This proves game-shaped state, not final art.",
        ],
        files_written=files_written,
    )

    report_path = OUTPUT_DIR / "gameproof_report.json"
    write_json(report_path, asdict(report))
    print(f"      wrote: {report_path}")

    print()
    print("[5/5] Result")
    if violations:
        print("      FAILED")
        for violation in violations:
            print(f"      - {violation}")
        return 2

    print("      PASSED")
    print()
    print("EngAIn produced a game-shaped draft packet.")
    print("No art lane was required.")
    print("No external sibling tool was required.")
    print("No runtime mutation occurred.")
    return 0


def main() -> int:
    return run_proof()


if __name__ == "__main__":
    raise SystemExit(main())
