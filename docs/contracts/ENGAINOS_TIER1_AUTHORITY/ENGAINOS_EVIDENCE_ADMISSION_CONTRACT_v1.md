# ENGAINOS_EVIDENCE_ADMISSION_CONTRACT_v1.md

**Version:** 1.0
**Status:** Proposed (2026-10-06). No gate implements it yet.
**Owning lane:** EngAInOS TIER1 governance (`engainos_1stlane_governance_authority`)

## 1. Purpose

EngAInOS governs a prose-derived fact at **two separate moments**, and they
do different jobs. This contract names those moments and their two output
states, so that "EngAInOS accepted it" is never ambiguous.

## 2. Terms

| Term | Meaning | Who may consume it | What it is NOT |
|---|---|---|---|
| **ADMITTED_EVIDENCE** | A proposal artifact (e.g. `mettaext.parse_artifact.v2`) that passed **intake**: valid contract, complete provenance, no lane violations | Lane authorities, **for interpretation only** (Topologist, Paradox, Engionality, WorldField/trixelmap, MrLore review) | Truth. It may not enter declared truth, runtime state, canon, or presentation |
| **ACCEPTED_DERIVED_TRUTH** | A lane authority's interpretation of admitted evidence that passed **final verification** | Declared truth / runtime and downstream consumers | Raw evidence. It always carries the id of the admitted evidence it derives from |

`ADMITTED_EVIDENCE ≠ ACCEPTED_DERIVED_TRUTH`. No path promotes admitted
evidence directly into declared truth.

## 3. Gate 1: Intake (admission)

Input: a proposal artifact from a TIER3 producer (first case:
`mettaext.parse_artifact.v2`).

Checks (deterministic, no interpretation):
1. Contract id, source, `authority_tier` and lane match the producer's contract.
2. Every declaration, cue and constraint carries a valid `source_span` with
   `source_text_id` and `source_sha256`.
3. Lane line holds. None of these appear: `position`, `velocity`,
   `collision`, `affect_state`, `terrain_profile`, topology links, canonical
   ids, canon claims, permission fields. These are the producer contract's
   hard rejects.
4. Identity handles are run-local and canonical fields are null (for example
   `canonical_scene_id`).

Verdicts:

| Verdict | Meaning |
|---|---|
| `ADMIT` | Artifact becomes ADMITTED_EVIDENCE, with an `admission_id` |
| `HOLD` | Structurally valid but not yet admissible (e.g. pinned source unavailable); retained and re-evaluable |
| `REJECT` | Contract or lane violation; recorded with reasons; never consumable |

Admission says nothing about whether the content is true.

## 4. Gate 2: Final verification

Input: a lane authority's derived output, which references the
`admission_id` it was derived from. Example chain for spatial truth (per
HANDSHAKES §5):

```
ADMITTED_EVIDENCE → Topologist → Cartographer → MrLore narrative concurrence
                  → EngAInOS final verification → ACCEPTED_DERIVED_TRUTH
```

Verdicts: `ACCEPT`, `REJECT`, `HOLD`, `CONFLICT`. `HOLD` means the evidence
has not resolved it yet; it may remain pending indefinitely. `CONFLICT`
means derived outputs or canon review disagree.

EngAInOS may request MrLore canon review at either gate. MrLore's findings
are input to EngAInOS's verdict, never the verdict itself (see
`MRLORE_TIER1_CANON_REVIEW_CONTRACT_v2.md`).

## 5. Naming note: `accepted_spatial_truth`

Topologist's packet type `accepted_spatial_truth` means *accepted by
Topologist's own gate*. Under this contract it is a lane-accepted derived
**proposal** until EngAInOS final verification, not ACCEPTED_DERIVED_TRUTH.
This contract does not rename the packet type, because that would be a code
change. Consumers must not read the word "accepted" in that name as EngAInOS
acceptance.

## 6. Records

Both gates record every verdict with its reasons, the inputs' hashes, and
the `admission_id`/derivation chain. Current implementation gap:
`core/intent_shadow.py` keeps rejections in memory only. Persisting the
records is a prerequisite for implementing this contract.

## 7. One-line contract

**Intake admits evidence for interpretation; final verification accepts
derived truth; nothing skips from the first to declared truth.**
