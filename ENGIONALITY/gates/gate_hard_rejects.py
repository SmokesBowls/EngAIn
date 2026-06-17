# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/engionality/gates/gate_hard_rejects.py

from __future__ import annotations

from engain_control.gate_result import GateResult

FORBIDDEN_KEYS = {"position", "velocity", "collision", "spawn", "despawn", "canon", "ap_allowed", "health", "location"}

def gate_no_lane_theft_in_packet() -> GateResult:
    """
    PROMISE: The packet contains NO spatial, execution, or TIER1 authority data.
    """
    packet = SAMPLE_PACKET_MINIMAL # Test fixture
    
    # Flatten packet keys for easy checking
    all_keys = set(packet.keys())
    for entity in packet.get("entities", []):
        all_keys.update(entity.keys())
        for rel in entity.get("relationship_deltas", []):
            all_keys.update(rel.keys())

    stolen_keys = all_keys.intersection(FORBIDDEN_KEYS)
    
    if stolen_keys:
        return GateResult(
            gate_name="gate_no_lane_theft_in_packet",
            passed="FALSE",
            message=f"HARD REJECT: Packet contains forbidden TIER1/Execution keys: {stolen_keys}",
        )

    return GateResult(
        gate_name="gate_no_lane_theft_in_packet",
        passed="TRUE",
        message="Packet is clean of spatial/execution/canon authority keys",
    )