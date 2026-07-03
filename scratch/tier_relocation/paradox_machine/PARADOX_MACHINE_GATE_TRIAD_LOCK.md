# Paradox Machine Gate Triad Lock

## Status

PARADOX_MACHINE_GATE_TRIAD_STATUS=PASS

The Paradox Machine now has a minimal working three-outcome gate proof.

## Proven Outcomes

### Game Proof #007 — ACCEPTED Path

The temporal artifact pipeline accepted internally consistent temporal claims.

Result:

- VERDICT=ACCEPTED
- CONSISTENT=True
- REAL_RUNTIME_TOUCHED=FALSE
- CANON_WRITTEN=FALSE

Meaning:

A proposed `ProseTemporalArtifact` can pass through:

prose/fake intake → artifact → validator → TemporalGate → accepted destination

without touching runtime or canon.

---

### Game Proof #007b — REJECTED Path

The temporal validator rejected contradictory temporal claims.

Result:

- VERDICT=REJECTED
- CONSISTENT=False
- PASS=True
- REAL_RUNTIME_TOUCHED=FALSE
- CANON_WRITTEN=FALSE

Meaning:

The validator is not merely accepting every artifact. It can detect a direct temporal contradiction such as:

e1 BEFORE e2  
e2 BEFORE e1

and route the artifact to rejection.

---

### Game Proof #008 — SUSPENDED Path

The spatio-temporal stub suspended a missing-transition contradiction.

Result:

- VERDICT=SUSPENDED
- REAL_RUNTIME_TOUCHED=FALSE
- CANON_WRITTEN=FALSE

Meaning:

The system can identify a claim that is not simply accepted or rejected, but needs paradoxroom investigation.

Example law:

If accepted spatial truth says the gate blocks the path, and accepted temporal truth has no transition event such as gate opened, player crossed, or teleportation declared, then a proposed claim placing the player behind the gate must be suspended.

## Doctrine Lock

Temporal validation is not narration.

Temporal validation is not canon writing.

Temporal validation is not time travel.

Temporal validation is not paradox resolution.

Temporal validation only decides whether proposed time claims are:

1. internally lawful,
2. compatible with accepted temporal truth,
3. compatible with accepted spatial truth,
4. ACCEPTED, REJECTED, or SUSPENDED.

## Architecture Lock

Core names:

- `ProseTemporalArtifact`
- `TemporalValidator`
- `TemporalGate`
- `AcceptedTemporalTruthPacket`
- `PotentialTemporalStateSet`
- `paradoxroom`
- `Paradox Machine`

## Expansion Boundary

Do not expand into full runtime until the triad remains stable.

Deferred features:

- full ISO-TimeML XML import/export
- full Allen Algebra composition
- full STN solving
- flashback classifier
- prophecy classifier
- observer-relative time
- branching timelines
- canon writer
- runtime mutation

## Safety Lock

CANON_WRITTEN=FALSE  
RUNTIME_TOUCHED=FALSE

