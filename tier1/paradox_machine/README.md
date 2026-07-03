# Paradox Machine

The Paradox Machine is the EngAIn temporal and spatio-temporal law layer.

It is not a narrator.
It is not a canon writer.
It is not a time-travel engine.
It is not a paradox resolver by itself.

Its first duty is to decide whether proposed narrative claims are lawful enough to become accepted truth, must be rejected, or must be suspended for paradoxroom investigation.

## Current Status

PARADOX_MACHINE_GATE_TRIAD_STATUS=PASS

Verified paths:

- ACCEPTED: `python -m proofs.proof_007_temporal_mvp`
- REJECTED: `python -m proofs.proof_007b_temporal_rejection`
- SUSPENDED: `python -m proofs.proof_008_spatiotemporal_gate_stub`

Combined health check:

- `python -m proofs.run_paradox_machine_gate_triad`

Read last combined result without rerunning proofs:

- `python -m proofs.read_paradox_machine_gate_triad_result`

## Safety Boundary

All current proofs are scratch-only.

CANON_WRITTEN=FALSE
RUNTIME_TOUCHED=FALSE

Proof outputs live under:

`/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/game_proofs/`

Lock files live under:

`/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/scratch/tier_relocation/paradox_machine/`

## Core Components

- `ProseTemporalArtifact`
- `TemporalValidator`
- `TemporalGate`
- `AcceptedTemporalTruthPacket`
- `PotentialTemporalStateSet`
- `paradoxroom`
- `Paradox Machine`

## Doctrine

Temporal validation checks proposed time claims.

It decides whether they are:

1. internally lawful,
2. compatible with accepted temporal truth,
3. compatible with accepted spatial truth,
4. routed to ACCEPTED, REJECTED, or SUSPENDED.

Suspension is not failure. Suspension means the claim needs more law, more context, or an explicit transition event.

## Deferred Features

Do not add these yet:

- full ISO-TimeML XML import/export
- full Allen Algebra composition
- full STN solving
- flashback classifier
- prophecy classifier
- observer-relative time
- branching timelines
- canon writer
- runtime mutation

## Required Health Check

Before changing temporal law code, run:

`python -m proofs.run_paradox_machine_gate_triad`

If this fails, stop and repair the proof lane before expanding the system.
