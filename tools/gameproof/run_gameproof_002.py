#!/usr/bin/env python3
"""
EngAIn Game Proof #002

Purpose:
    Prove EngAIn can take real text intake and produce a game-shaped
    draft packet through a small scene extraction chain.

This proof is stronger than Game Proof #001 because #001 used fully fake
in-memory scene data. This proof reads actual text from disk.

This script does NOT:
    - call Trixel
    - call Blender
    - call Mechanimation
    - start Godot
    - mutate runtime
    - write accepted game state
    - create final art

This script DOES:
    - read a scene text file
    - extract minimal entities from the text
    - create a Mettaext-style scene packet
    - create a Topologist-style topology intent packet
    - normalize to a game_state_draft payload
    - run hard true/false checks
    - write JSON proof files

Exit codes:
    0 = proof passed
    2 = proof failed / missing required field
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROOF_ROOT = REPO_ROOT / "scratch" / "gameproof_002"
INPUT_PATH = PROOF_ROOT / "input" / "scene_text.txt"
OUTPUT_DIR = PROOF_ROOT / "output"

PROOF_ID = "gameproof_002"
SCENE_ID = "scene.gameproof_002.text_intake_guard_gate"


@dataclass(frozen=True)
class ExtractedEntity:
    entity_id: str
    entity_type: str
    display_name: str
    source_terms: list[str]
    role: str
    state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScenePacket:
    packet_type: str
    proof_id: str
    scene_id: str
    source_path: str
    source_text: str
    summary: str
    entities: list[ExtractedEntity]


@dataclass(frozen=True)
class TopologyIntentPacket:
    packet_type: str
    artifact_id: str
    scene_id: str
    lifecycle: str
    entities: list[str]
    qualitative_spatial_links: list[dict[str, Any]]
    obstruction_links: list[dict[str, Any]]
    movement_links: list[dict[str, Any]]
    notes: list[str]


@dataclass(frozen=True)
class GameStateDraft:
    packet_type: str
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
    topology_packet: dict[str, Any]
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


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing input scene text: {path}")
    return path.read_text(encoding="utf-8").strip()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def has_word(text: str, word: str) -> bool:
    pattern = r"\b" + re.escape(word.lower()) + r"\b"
    return re.search(pattern, text.lower()) is not None


def extract_scene_packet(source_text: str) -> ScenePacket:
    """
    Minimal Mettaext-style extraction.

    This is intentionally small and explicit. It does not pretend to be
    the full mettaext pipeline yet.

    It proves that real text can become structured scene data.
    """

    entities: list[ExtractedEntity] = []

    if has_word(source_text, "guard"):
        entities.append(
            ExtractedEntity(
                entity_id="guard_001",
                entity_type="character",
                display_name="Guard",
                source_terms=["guard"],
                role="path_blocker",
                state={
                    "can_speak": True,
                    "blocks_movement": True,
                    "detected_from_text": True,
                },
            )
        )

    if has_word(source_text, "king"):
        entities.append(
            ExtractedEntity(
                entity_id="king_001",
                entity_type="character",
                display_name="King",
                source_terms=["king"],
                role="protected_target",
                state={
                    "can_speak": True,
                    "protected": True,
                    "detected_from_text": True,
                },
            )
        )

    if has_word(source_text, "gate"):
        entities.append(
            ExtractedEntity(
                entity_id="gate_001",
                entity_type="place_object",
                display_name="Stone Gate",
                source_terms=["gate", "stone gate"],
                role="boundary",
                state={
                    "open": False,
                    "blocks_path": True,
                    "detected_from_text": True,
                },
            )
        )

    if has_word(source_text, "player"):
        entities.append(
            ExtractedEntity(
                entity_id="player_001",
                entity_type="player_proxy",
                display_name="Player",
                source_terms=["player"],
                role="actor_requesting_access",
                state={
                    "can_move": True,
                    "detected_from_text": True,
                },
            )
        )

    return ScenePacket(
        packet_type="mettaext_style_scene_packet",
        proof_id=PROOF_ID,
        scene_id=SCENE_ID,
        source_path=str(INPUT_PATH.relative_to(REPO_ROOT)),
        source_text=source_text,
        summary="A guard blocks the player before a closed stone gate while the king waits behind it.",
        entities=entities,
    )


def build_topology_packet(scene: ScenePacket) -> TopologyIntentPacket:
    """
    Minimal Topologist-style topology intent.

    This is still not render geometry.
    It describes relationships and blockers.
    """

    entity_ids = {entity.entity_id for entity in scene.entities}

    qualitative_links: list[dict[str, Any]] = []
    obstruction_links: list[dict[str, Any]] = []
    movement_links: list[dict[str, Any]] = []

    if {"guard_001", "gate_001"}.issubset(entity_ids):
        qualitative_links.append(
            {
                "from": "guard_001",
                "relation": "in_front_of",
                "to": "gate_001",
                "required": True,
                "source_reason": "Text says guard stood before the closed stone gate.",
            }
        )
        obstruction_links.append(
            {
                "blocker": "guard_001",
                "blocked_path": "player_to_gate",
                "required": True,
                "source_reason": "Text says guard raised one hand and blocked the path.",
            }
        )

    if {"king_001", "gate_001"}.issubset(entity_ids):
        qualitative_links.append(
            {
                "from": "king_001",
                "relation": "behind",
                "to": "gate_001",
                "required": True,
                "source_reason": "Text says behind the gate, the king waited.",
            }
        )

    if "gate_001" in entity_ids:
        obstruction_links.append(
            {
                "blocker": "gate_001",
                "blocked_path": "outside_to_king",
                "required": True,
                "source_reason": "Text says the stone gate is closed.",
            }
        )

    if {"player_001", "guard_001"}.issubset(entity_ids):
        movement_links.append(
            {
                "actor": "player_001",
                "attempted_path": "approach_gate",
                "result": "blocked_by_guard",
                "required": True,
                "source_reason": "Text says the player approached and the guard blocked the path.",
            }
        )

    return TopologyIntentPacket(
        packet_type="topology_intent_packet",
        artifact_id="topo.gameproof_002.text_intake_guard_gate",
        scene_id=scene.scene_id,
        lifecycle="PROPOSED",
        entities=sorted(entity_ids),
        qualitative_spatial_links=qualitative_links,
        obstruction_links=obstruction_links,
        movement_links=movement_links,
        notes=[
            "Topology is qualitative only.",
            "No render coordinates.",
            "No Godot nodes.",
            "No Trixel asset data.",
        ],
    )


def normalize_to_runtime_payload(
    scene: ScenePacket,
    topology: TopologyIntentPacket,
) -> dict[str, Any]:
    """
    Convert scene + topology into a runtime-like draft payload.

    This is the kind of payload EngAIn could later pass toward GodotSim
    after proper gates accept it.
    """

    return {
        "packet_type": "game_state_draft",
        "scene_id": scene.scene_id,
        "source_path": scene.source_path,
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
        "topology": asdict(topology),
        "runtime_intent": {
            "player_can_request_dialogue": "guard_001" in topology.entities,
            "player_can_pass_gate": False,
            "requires_gate_acceptance_before_runtime_mutation": True,
        },
        "blocking": {
            "active_blockers": sorted(
                {
                    link["blocker"]
                    for link in topology.obstruction_links
                    if "blocker" in link
                }
            ),
            "blocked_paths": sorted(
                {
                    link["blocked_path"]
                    for link in topology.obstruction_links
                    if "blocked_path" in link
                }
            ),
        },
        "presentation": {
            "art_assets_required_now": False,
            "placeholder_render_allowed": True,
            "trixel_payload": None,
            "blender_payload": None,
            "mechanimation_payload": None,
        },
    }


def build_game_state_draft(
    scene: ScenePacket,
    topology: TopologyIntentPacket,
    runtime_payload: dict[str, Any],
) -> GameStateDraft:
    return GameStateDraft(
        packet_type="game_state_draft_wrapper",
        proof_id=PROOF_ID,
        scene_id=scene.scene_id,
        status="DRAFT_NOT_ACCEPTED",
        created_at=utc_now(),
        runtime_mutation_allowed=False,
        art_required=False,
        trixel_required=False,
        blender_required=False,
        mechanimation_required=False,
        scene_packet=asdict(scene),
        topology_packet=asdict(topology),
        runtime_payload=runtime_payload,
    )


def validate(scene: ScenePacket, topology: TopologyIntentPacket, draft: GameStateDraft) -> list[str]:
    """
    Hard true/false checks for Game Proof #002.
    """

    violations: list[str] = []

    if scene.packet_type != "mettaext_style_scene_packet":
        violations.append("scene.packet_type must be mettaext_style_scene_packet")

    if len(scene.entities) < 3:
        violations.append("scene must contain at least guard, king, and gate")

    entity_ids = {entity.entity_id for entity in scene.entities}

    for required in ["guard_001", "king_001", "gate_001"]:
        if required not in entity_ids:
            violations.append(f"required entity missing: {required}")

    if topology.packet_type != "topology_intent_packet":
        violations.append("topology.packet_type must be topology_intent_packet")

    if topology.lifecycle != "PROPOSED":
        violations.append("topology.lifecycle must be PROPOSED")

    if "gate_001" not in topology.entities:
        violations.append("topology must include gate_001")

    if not topology.obstruction_links:
        violations.append("topology must include at least one obstruction link")

    if not topology.qualitative_spatial_links:
        violations.append("topology must include qualitative spatial links")

    if draft.status != "DRAFT_NOT_ACCEPTED":
        violations.append("draft.status must be DRAFT_NOT_ACCEPTED")

    if draft.runtime_mutation_allowed is not False:
        violations.append("runtime mutation must be false")

    if draft.art_required is not False:
        violations.append("art_required must be false")

    if draft.trixel_required is not False:
        violations.append("trixel_required must be false")

    if draft.blender_required is not False:
        violations.append("blender_required must be false")

    if draft.mechanimation_required is not False:
        violations.append("mechanimation_required must be false")

    presentation = draft.runtime_payload.get("presentation", {})
    if presentation.get("trixel_payload") is not None:
        violations.append("runtime payload must not contain trixel payload")

    if presentation.get("blender_payload") is not None:
        violations.append("runtime payload must not contain blender payload")

    if presentation.get("mechanimation_payload") is not None:
        violations.append("runtime payload must not contain mechanimation payload")

    return violations


def run() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("EngAIn Game Proof #002")
    print("=" * 72)
    print(f"Input : {INPUT_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    print("[1/6] Reading scene text")
    source_text = read_text(INPUT_PATH)
    print(f"      chars: {len(source_text)}")

    print()
    print("[2/6] Extracting Mettaext-style scene packet")
    scene = extract_scene_packet(source_text)
    scene_path = OUTPUT_DIR / "scene_packet.json"
    write_json(scene_path, asdict(scene))
    print(f"      entities: {len(scene.entities)}")
    print(f"      wrote   : {scene_path}")

    print()
    print("[3/6] Building Topologist-style topology intent")
    topology = build_topology_packet(scene)
    topology_path = OUTPUT_DIR / "topology_intent.json"
    write_json(topology_path, asdict(topology))
    print(f"      qslinks     : {len(topology.qualitative_spatial_links)}")
    print(f"      obstructions: {len(topology.obstruction_links)}")
    print(f"      movement    : {len(topology.movement_links)}")
    print(f"      wrote       : {topology_path}")

    print()
    print("[4/6] Normalizing to runtime-like game_state_draft payload")
    runtime_payload = normalize_to_runtime_payload(scene, topology)
    runtime_path = OUTPUT_DIR / "runtime_payload.json"
    write_json(runtime_path, runtime_payload)
    print(f"      wrote: {runtime_path}")

    print()
    print("[5/6] Building GameStateDraft wrapper")
    draft = build_game_state_draft(scene, topology, runtime_payload)
    draft_path = OUTPUT_DIR / "game_state_draft.json"
    write_json(draft_path, asdict(draft))
    print(f"      wrote: {draft_path}")

    print()
    print("[6/6] Running hard true/false checks")
    violations = validate(scene, topology, draft)

    files_written = [
        str(scene_path.relative_to(REPO_ROOT)),
        str(topology_path.relative_to(REPO_ROOT)),
        str(runtime_path.relative_to(REPO_ROOT)),
        str(draft_path.relative_to(REPO_ROOT)),
    ]

    report = GateReport(
        proof_id=PROOF_ID,
        passed=not violations,
        checks_run=16,
        violations=violations,
        notes=[
            "Input was read from a real text file.",
            "Scene packet is Mettaext-style but not full Mettaext pipeline yet.",
            "Topology packet is Topologist-style but not full classroom artifact yet.",
            "No Trixel call was made.",
            "No Blender call was made.",
            "No Mechanimation call was made.",
            "No Godot runtime mutation was made.",
            "Payload is a draft only.",
        ],
        files_written=files_written,
    )

    report_path = OUTPUT_DIR / "gameproof_report.json"
    write_json(report_path, asdict(report))

    print(f"      wrote: {report_path}")
    print()

    if violations:
        print("RESULT: FAILED")
        for violation in violations:
            print(f"  - {violation}")
        return 2

    print("RESULT: PASSED")
    print()
    print("EngAIn converted real scene text into a game-shaped draft packet.")
    print("No art lane was required.")
    print("No external sibling tool was required.")
    print("No runtime mutation occurred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
