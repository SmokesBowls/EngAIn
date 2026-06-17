# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/gates/gate_affect_packet_relationships.py

from __future__ import annotations

from engain_control.gate_result import GateResult

# Mock packet for gate testing (in reality, this would be injected or loaded)
SAMPLE_PACKET_MINIMAL = {
    "contract": "engionality.affect_packet.v1",
    "source": "engionality",
    "authority_tier": 2,
    "scene_id": "scene_001",
    "tick": 1042,
    "entities": [{"entity_id": "mika_01", "affect_state": "fear", "intensity": 0.72}]
}

SAMPLE_PACKET_WITH_RELATIONSHIPS = {
    **SAMPLE_PACKET_MINIMAL,
    "entities": [{
        "entity_id": "mika_01",
        "affect_state": "fear",
        "intensity": 0.72,
        "relationship_deltas": [
            {"target_id": "geralt_01", "axis": "trust", "delta": -0.08}
        ]
    }]
}

SAMPLE_PACKET_MALFORMED_RELATIONSHIPS = {
    **SAMPLE_PACKET_MINIMAL,
    "entities": [{
        "entity_id": "mika_01",
        "affect_state": "fear",
        "intensity": 0.72,
        "relationship_deltas": [
            {"target_id": "geralt_01", "axis": "trust"} # MISSING 'delta'
        ]
    }]
}


def gate_relationship_deltas_valid_if_present() -> GateResult:
    """
    PROMISE: If relationship_deltas exists, it must contain target_id, axis, and delta (-1.0 to 1.0).
    BYPASS RULE: If relationship_deltas is absent, the gate SKIPPED (BYPASSES) cleanly.
    """
    # For testing, we evaluate against a specific packet. 
    # In production, this gate would receive the packet as an argument or read a test fixture.
    packet = SAMPLE_PACKET_MINIMAL  # Change to test different states

    for entity in packet.get("entities", []):
        rel_deltas = entity.get("relationship_deltas")
        
        # BYPASS CONDITION: Field is optional. If missing, we skip validation.
        if rel_deltas is None:
            return GateResult(
                gate_name="gate_relationship_deltas_valid_if_present",
                passed="SKIPPED",
                message="BYPASS: relationship_deltas is optional and absent",
            )
        
        # VALIDATION CONDITION: Field is present, so we must validate it.
        if not isinstance(rel_deltas, list):
            return GateResult(
                gate_name="gate_relationship_deltas_valid_if_present",
                passed="FALSE",
                message="relationship_deltas must be a list",
            )
            
        for rel in rel_deltas:
            if "target_id" not in rel or "axis" not in rel or "delta" not in rel:
                return GateResult(
                    gate_name="gate_relationship_deltas_valid_if_present",
                    passed="FALSE",
                    message="relationship_delta missing required fields (target_id, axis, delta)",
                )
            if not (-1.0 <= rel["delta"] <= 1.0):
                return GateResult(
                    gate_name="gate_relationship_deltas_valid_if_present",
                    passed="FALSE",
                    message=f"relationship_delta out of bounds: {rel['delta']}",
                )

    return GateResult(
        gate_name="gate_relationship_deltas_valid_if_present",
        passed="TRUE",
        message="relationship_deltas validated successfully",
    )