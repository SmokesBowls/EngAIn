import json
from pathlib import Path


OUTPUT_DIR = Path(
    "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/proof_008_spatiotemporal_gate_stub"
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    accepted_temporal_truth = {
        "truth_packet_id": "accepted_temporal_gate_closed_001",
        "claims": [
            {
                "source_id": "guard_closed_gate",
                "target_id": "player_standing_behind_gate",
                "rel_type": "BEFORE",
            }
        ],
    }

    accepted_spatial_truth = {
        "truth_packet_id": "accepted_spatial_gate_blocks_path_001",
        "claims": [
            {"subject": "gate", "predicate": "blocks", "object": "path"},
            {"subject": "player", "predicate": "was_at", "object": "front_of_gate"},
        ],
    }

    proposed_claim = {
        "claim_id": "proposed_player_behind_gate_001",
        "subject": "player",
        "predicate": "is_at",
        "object": "behind_gate",
    }

    known_transition_events = []

    missing_transition = not any(
        event in known_transition_events
        for event in ["gate_opened", "player_crossed_gate", "teleportation_declared"]
    )

    if missing_transition:
        verdict = {
            "verdict": "SUSPENDED",
            "reason": (
                "The proposed spatial state places the player behind a blocking gate, "
                "but accepted temporal/spatial truth contains no transition event."
            ),
            "next_destination": "paradoxroom.PotentialTemporalStateSet",
            "candidates": [
                "candidate_1_gate_opened_before_crossing",
                "candidate_2_player_was_already_behind_gate",
                "candidate_3_teleportation_declared",
                "candidate_4_gate_does_not_actually_block_path",
            ],
        }
    else:
        verdict = {
            "verdict": "ACCEPTED",
            "reason": "A valid transition event exists.",
            "next_destination": "AcceptedSpatioTemporalTruthPacket",
            "candidates": [],
        }

    payload = {
        "proof": "Game Proof #008",
        "name": "SpatioTemporal Paradox Gate Stub",
        "real_runtime_touched": False,
        "canon_written": False,
        "accepted_temporal_truth": accepted_temporal_truth,
        "accepted_spatial_truth": accepted_spatial_truth,
        "proposed_claim": proposed_claim,
        "known_transition_events": known_transition_events,
        "gate_verdict": verdict,
    }

    out_path = OUTPUT_DIR / "proof_008_spatiotemporal_gate_stub_result.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("PROOF_008_SPATIOTEMPORAL_GATE_STUB_COMPLETE=TRUE")
    print(f"OUTPUT={out_path}")
    print(f"VERDICT={verdict['verdict']}")
    print("REAL_RUNTIME_TOUCHED=FALSE")
    print("CANON_WRITTEN=FALSE")


if __name__ == "__main__":
    main()
