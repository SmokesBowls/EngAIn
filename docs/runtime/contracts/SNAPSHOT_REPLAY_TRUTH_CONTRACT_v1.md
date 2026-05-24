# SNAPSHOT REPLAY TRUTH CONTRACT v1

Status: DRAFT CONTRACT
Scope: EngAIn snapshot semantics, replay semantics, canonical history, evidence classification, and the boundaries that prevent snapshot/replay/history/canon conflation
Repository root: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn`

---

## 1. Purpose

This contract freezes the distinction between snapshot, replay, evidence, history, and canon before those terms become silently synonymous across EngAIn subsystems.

The problem this contract addresses: a snapshot can be captured, replayed, stored, referenced, and rendered — and at each step, a system or operator can begin treating the artifact as more authoritative than it is.

- A snapshot captures live state at a moment. It is not canon.
- A replay reads from an archived snapshot or event sequence. It is not mutation, promotion, or canon authorship.
- Evidence is a record of what happened. It is not acceptance of what happened as truth.
- History is the canonical record. It is not automatically what runtime observed.
- Canon is what the canon gate accepted. It is not what was loaded, replayed, or rendered.

None of these collapse into each other silently.

Core law:

```text
snapshot != replay != evidence != history != canon
```

---

## 2. Upstream authority

This contract is subordinate to:

- `AGENTS.md` repository preservation rules;
- `godotengain/engainos/docs/architecture/AUTHORITY_TIER_SPEC_v1.md`;
- `docs/runtime/contracts/RUNTIME_STATE_AUTHORITY_CONTRACT_v1.md`;
- `docs/ap/contracts/AP_MUTATION_GOVERNANCE_CONTRACT_v1.md`;
- `docs/trae/contracts/TRAE_OPERATOR_AUTHORITY_CONTRACT_v1.md`;
- `docs/mrlore/contracts/MRLORE_AUTHORITY_CONTRACT_v1.md`;
- `system.manifest.md` runtime SSOT doctrine.

If this contract conflicts with the frozen AP authority tier spec, the AP authority tier spec wins.

---

## 3. Term definitions

### 3.1 Snapshot

A snapshot is a point-in-time capture of `EngAInRuntime.snapshot` or an equivalent runtime state record.

```text
snapshot = point-in-time capture of accepted live simulation state
```

A snapshot:

- represents live state at the moment of capture;
- may include draft, test, sandbox, or candidate state depending on reality mode at capture time;
- does not by itself constitute a canonical record;
- does not by itself constitute a history entry;
- does not authorize mutation when replayed or referenced.

### 3.2 Replay

A replay is a read-only traversal of a stored event sequence, snapshot chain, or state archive for observation, audit, debugging, or continuity evidence.

```text
replay = read-only traversal of archived state or events
```

A replay:

- must not mutate live runtime state;
- must not write canonical history;
- must not promote artifacts;
- must not generate accepted canon entries;
- may produce evidence artifacts (logs, diffs, reports);
- may be used to build promotion or continuity proposals — but those proposals are not themselves accepted by replay.

### 3.3 Evidence

Evidence is a record or artifact produced by or about a past runtime operation, snapshot, replay, generation, or audit process.

```text
evidence = observation artifact; not accepted state
```

Evidence:

- records what was observed or produced;
- is not the thing itself;
- is not canon unless a canon gate accepted it as such;
- may be referenced in mutation envelopes, promotion requests, and continuity reviews;
- must be labeled with its type so consumers do not conflate it with accepted state.

### 3.4 History

History is the canonical record of events, mutations, and state accepted by the canon gate under required authority.

```text
history = canonical record accepted by the canon gate
```

History:

- is not the same as runtime snapshot;
- is not the same as a replay log;
- is not the same as a capture archive;
- requires explicit canon gate approval to write;
- requires Tier 3/root authority for FINALIZED history entries;
- cannot be retroactively modified by runtime load, replay, or generation alone.

### 3.5 Canon

Canon is what the canon gate has accepted as authoritative world/simulation truth under the required authority.

```text
canon = canon-gate-accepted authoritative truth
```

Canon is not:

- what was loaded into runtime;
- what was replayed;
- what was rendered;
- what was generated;
- what was observed in a snapshot;
- what MrLore reviewed as continuity-safe;
- what AP permitted as a mutation.

---

## 4. Non-negotiable boundary law

Required distinctions:

```text
snapshot != replay
snapshot != canonical history
snapshot != canon
replay != canon
replay != mutation authority
replay != promotion
evidence != accepted state
evidence != truth
history != runtime snapshot
history != replay log
canon != rendered output
canon != loaded state
REPLAY mode is read-only
DREAM output is not history
```

Additional distinctions:

```text
capture archive != history record
stored snapshot != live snapshot
snapshot evidence != canon gate approval
replay log != accepted delta
continuity review != history write
MrLore continuity report != canon history entry
Trae-generated timeline artifact != history
Godot render of snapshot != authoritative state
```

---

## 5. Snapshot semantics

### 5.1 Live snapshot

`EngAInRuntime.snapshot` is live state for the running simulation.

It is not:

- an immutable record;
- a history entry;
- a canon gate artifact;
- a source of mutation authority.

Rules:

1. Live snapshot reflects current accepted runtime state.
2. Live snapshot may include non-canonical material (DRAFT, DREAM, test, loaded-but-not-promoted).
3. Live snapshot must not be treated as canonical history.
4. Live snapshot may be used as evidence in proposals, reviews, and promotion requests.
5. Live snapshot capture produces a stored snapshot, not a history record.

### 5.2 Stored snapshot

A stored snapshot is a point-in-time copy of live snapshot state, written to an archive for replay, audit, debugging, or continuity evidence.

Rules:

1. A stored snapshot preserves the live state at capture time, including its non-canonical status.
2. A stored snapshot does not become a history entry by being stored.
3. A stored snapshot must carry provenance: timestamp, runtime identity, reality mode, canonicality status at capture time.
4. Reading a stored snapshot is a read operation, not a mutation.
5. A stored snapshot may be promoted to history only through the promotion pipeline and canon gate.

Core law:

```text
stored snapshot != history record
```

### 5.3 Snapshot capture does not change authority

Capturing a snapshot does not:

- promote live state to canonical status;
- authorize mutation;
- write history;
- advance the promotion pipeline.

---

## 6. Replay semantics

### 6.1 REPLAY mode is read-only

REPLAY is an explicit reality mode.

Rules:

1. REPLAY must not write to live runtime state.
2. REPLAY must not write history.
3. REPLAY must not promote artifacts.
4. REPLAY must not apply accepted deltas.
5. REPLAY must not produce mutation envelopes with `decision = allowed` unless those envelopes are themselves replay-read artifacts (labeled as evidence, not live mutation).
6. REPLAY may read stored snapshots, event logs, archived delta chains.
7. REPLAY may produce evidence outputs (diffs, reports, continuity observations).
8. Evidence outputs from REPLAY require a non-REPLAY mutation request to become accepted state.

Core law:

```text
REPLAY is read-only
```

### 6.2 Replay evidence is not accepted state

A replay log, diff, or observation report is evidence.

It is not:

- accepted runtime state;
- a canon history entry;
- an approved mutation;
- a promotion record.

### 6.3 Replay cannot self-authorize transition out of REPLAY mode

A replay operation must not contain logic that promotes itself from REPLAY to DRAFT, IMBUED, or FINALIZED.

Mode transitions require explicit external authority, not replay completion.

---

## 7. Evidence classification

Evidence artifacts must be typed to prevent conflation with accepted state.

Required evidence type labels:

| Type | Meaning | Not accepted as |
|---|---|---|
| `runtime_snapshot_capture` | Point-in-time live state copy. | History, canon. |
| `replay_observation` | What REPLAY observed in an event/snapshot sequence. | Live mutation, history write. |
| `continuity_report` | MrLore continuity review output. | Mutation permission, canon. |
| `generation_output` | Trae/pipeline generated file or artifact. | Runtime truth, mutation authority. |
| `render_artifact` | Godot/Trixel visual projection. | Authoritative state. |
| `delta_record` | Record of what deltas were accepted or rejected. | Canon by itself. |
| `promotion_evidence` | Artifacts collected for a promotion request. | Promotion by themselves. |
| `intent_shadow` | Rejection evidence for a blocked mutation attempt. | Accepted state. |
| `history_entry` | Canon gate accepted canonical record. | Promoted without gate approval. |

Rules:

1. All evidence artifacts must carry a type label.
2. Consuming systems must not use evidence beyond its declared type without an explicit transition gate.
3. Evidence must not self-escalate.

---

## 8. Canonical history rules

History is written only through the canon gate under required authority.

Rules:

1. Runtime load does not write history.
2. Replay does not write history.
3. Snapshot capture does not write history.
4. Continuity review does not write history.
5. Generation does not write history.
6. Render does not write history.
7. AP `allowed` does not write history.
8. History entries require:
   - explicit canon gate invocation;
   - `actor_authority_tier` appropriate to the target history tier;
   - `reality_mode = FINALIZED` or equivalent canon context;
   - provenance chain from source artifact through promotion pipeline;
   - Tier 3/root authority for FINALIZED history.

Core law:

```text
canon history requires explicit canon gate approval under required authority
```

---

## 9. DREAM output is not history

DREAM mutations are symbolic, sandboxed, and non-canonical.

DREAM outputs may produce stored snapshots of sandbox state, but those snapshots:

- are labeled DREAM-sandboxed;
- cannot be promoted to history without leaving the sandbox;
- cannot be referenced as canonical evidence without a non-DREAM promotion path;
- cannot be confused with live runtime snapshots of IMBUED or FINALIZED state.

Core law:

```text
DREAM output is not history
DREAM snapshot != canonical snapshot
```

---

## 10. Subsystem-specific snapshot/replay rules

### 10.1 MrLore

MrLore may read snapshots and replay logs for continuity review.

MrLore continuity reports are evidence. They are not history entries.

```text
MrLore continuity report != history entry
```

### 10.2 Trixel

Trixel may embody snapshot-derived state for visualization.

Trixel renders are projection artifacts. They are not snapshot truth.

```text
Trixel render != snapshot truth
```

### 10.3 Trae

Trae may generate timeline/history-like files from snapshot evidence.

Trae outputs are generation artifacts. They are not history entries.

```text
Trae generated history artifact != canon history
```

### 10.4 Godot

Godot may render projections from snapshot data.

Godot node state is not authoritative snapshot truth.

```text
Godot render of snapshot != authoritative snapshot state
```

### 10.5 Dragon

Dragon may explain, summarize, or present snapshot and replay observations.

Dragon summaries are explanatory artifacts. They are not mutation authority or history.

```text
Dragon replay summary != canon history
```

---

## 11. Provenance requirements for snapshot/replay artifacts

Every snapshot-capture or replay-evidence artifact must carry:

- artifact type (from Section 7);
- source runtime identity and version;
- reality mode at capture/replay time;
- canonicality status at capture/replay time;
- timestamp or run ID;
- actor/requester identity when applicable;
- any promotion or review history;
- explicit label if non-canonical (DRAFT, DREAM, REPLAY, candidate, etc.).

---

## 12. Failure behavior

When snapshot/replay semantics are ambiguous, fail closed.

Fail closed when:

- a stored snapshot lacks reality mode or canonicality status;
- a replay evidence artifact is presented as an accepted mutation;
- an artifact self-labels as history without canon gate record;
- a consuming system attempts to apply REPLAY-mode output as a live delta;
- DREAM-sandboxed snapshot is presented as IMBUED or FINALIZED;
- provenance chain is missing or broken;
- evidence type label is absent.

---

## 13. Minimum audit checklist

Before trusting a snapshot, replay, or evidence artifact, verify:

1. What is the declared type of this artifact?
2. What reality mode was active when it was captured/produced?
3. What was the canonicality status at capture time?
4. Does it carry provenance (timestamp, actor, source runtime, mode)?
5. Is this REPLAY output? If so, does it claim mutation authority? (Must not.)
6. Is this DREAM output? If so, is it labeled as sandboxed?
7. Is this a history entry? If so, is there a canon gate record with Tier 3/root authority?
8. Is evidence type used only within its declared scope?
9. Are there any self-escalation attempts (replay promoting itself, snapshot claiming canon)?

---

## 14. Red-line rules

1. Snapshot is live state, not canonical history.
2. Stored snapshot is a capture artifact, not a history record.
3. REPLAY is read-only with no mutation, no history write, no promotion.
4. Evidence is typed and scoped — it does not self-escalate.
5. Canonical history requires explicit canon gate approval.
6. FINALIZED history requires Tier 3/root authority.
7. DREAM snapshots are sandboxed — not IMBUED or FINALIZED.
8. MrLore continuity report is evidence, not a history entry.
9. Trae-generated history artifact is not canon history.
10. Godot/Trixel renders are projections, not snapshot truth.
11. Dragon summaries are explanatory artifacts, not mutation or history authority.
12. No subsystem may self-promote from REPLAY or DREAM to canonical status.

---

## 15. Versioning

This is `SNAPSHOT_REPLAY_TRUTH_CONTRACT_v1`.

Backward-incompatible changes require a v2 contract or explicit amendment section.

Implementation may add replay harnesses, snapshot archivers, evidence type validators, canon gate integrations, or CI audit checks under this contract, but must not weaken snapshot/replay/history/canon distinctions.

---

## 16. Final invariant

Observation is not authorship. Archive is not canon.

```text
snapshot = point-in-time live state capture; not history, not canon.
stored snapshot = archive artifact; not history record.
replay = read-only traversal; no mutation, no history write.
evidence = typed observation record; does not self-escalate.
history = canon-gate-accepted record under required authority.
canon = authoritative truth; not what was loaded, replayed, rendered, or generated.
REPLAY is read-only.
DREAM output is not history.
Canon outranks observation.
```
