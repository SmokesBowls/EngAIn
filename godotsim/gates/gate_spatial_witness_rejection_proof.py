# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotsim/gates/gate_spatial_witness_rejection_proof.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult
from godotsim.gates.gate_no_narrative_meaning import gate_no_narrative_meaning_in_packet
from godotsim.gates.gate_no_auto_entity_declaration import gate_no_auto_entity_declaration


VALID_BASE_PACKET: dict[str, Any] = {
    "contract": "godotsim.spatial_sim_packet.v1",
    "source": "godotsim",
    "authority_tier": 2,
    "scene_id": "scene.030_ummade_army",
    "sim_tick": 1042,
    "entities": [
        {
            "entity_id": "mika_01",
            "position": [12.5, 0.0, 8.3],
            "collision_role": "kinematic",
        }
    ],
}


BAD_NARRATIVE_PACKET: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "quest_completion": True,
}


BAD_ENTITY_DECLARATION_PACKET: dict[str, Any] = {
    **VALID_BASE_PACKET,
    "spawn": True,
}


def gate_narrative_meaning_rejection_path(packet: dict[str, Any]) -> GateResult:
    """
    PROOF: GodotSim must reject packets containing narrative meaning.
    Returns TRUE if the underlying gate correctly returns FALSE (rejection works).
    Returns FALSE if the underlying gate returns TRUE or SKIPPED (rejection failed).
    """
    result = gate_no_narrative_meaning_in_packet(BAD_NARRATIVE_PACKET)

    if result.passed == "FALSE":
        return GateResult(
            "gate_narrative_meaning_rejection_path",
            "TRUE",
            "Packet with quest_completion was correctly rejected",
        )

    return GateResult(
        "gate_narrative_meaning_rejection_path",
        "FALSE",
        f"Packet with quest_completion should have been rejected but got {result.passed}: {result.message}",
    )


def gate_entity_declaration_rejection_path(packet: dict[str, Any]) -> GateResult:
    """
    PROOF: GodotSim must reject packets containing entity declaration authority.
    Returns TRUE if the underlying gate correctly returns FALSE (rejection works).
    Returns FALSE if the underlying gate returns TRUE or SKIPPED (rejection failed).
    """
    result = gate_no_auto_entity_declaration(BAD_ENTITY_DECLARATION_PACKET)

    if result.passed == "FALSE":
        return GateResult(
            "gate_entity_declaration_rejection_path",
            "TRUE",
            "Packet with spawn authority was correctly rejected",
        )

    return GateResult(
        "gate_entity_declaration_rejection_path",
        "FALSE",
        f"Packet with spawn authority should have been rejected but got {result.passed}: {result.message}",
    )