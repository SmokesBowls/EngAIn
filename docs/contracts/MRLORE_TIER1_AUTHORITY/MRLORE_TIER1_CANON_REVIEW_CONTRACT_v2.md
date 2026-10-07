# MRLORE_TIER1_CANON_REVIEW_CONTRACT_v2.md

**Version:** 2.0
**Status:** Proposed (2026-10-06). The v2 packet has no gate yet. Existing
code (`tier1/mrlore/gates/`, `mrlore_control_center.py`,
`tier1/engainos/engainos_control_center.py`) continues to use the v1 packet
until v2 gates exist.
**Supersedes:** the handoff flow of `MRLORE_TIER1_CANON_REVIEW_CONTRACT_v1.md`
§10. The v1 file is kept unchanged as history apart from a supersession
notice.

## 1. What changed from v1, and why

v1 §10 placed MrLore **between** Mettaext and EngAInOS:

```
Mettaext → MrLore → (canon-safe candidates) → EngAInOS
```

This contradicted `METTAEXT_TIER3_PARSE_AUTHORITY_CONTRACT_v1.md` §9, in
which EngAInOS receives parse proposals and **consults** MrLore. It also
made MrLore a mandatory pre-gate on extraction. On 2026-10-06 the ruling
was that MrLore is **advisory to EngAInOS governance** and is not a gate in
the extraction path. v2 adopts that flow.

Nothing else about MrLore's authority changes. Per
`docs/ENGAINOS_1ST_AMENDMENT.md` and `ENGAINOS_AUTHORITY_MAP.md`, MrLore
owns canon and lore truth inside its lane. It may not promote that truth
into EngAInOS declared truth, runtime state, or presentation.

## 2. Flow (v2)

```
Mettaext Gen2 → parse_artifact.v2 → EngAInOS intake
                                       ├─ request MrLore review (when canon/lore validation is needed)
                                       │      ↓
                                       │   MrLore canon review finding (advisory)
                                       │      ↓
                                       └─ ADMIT / HOLD / REJECT
                                                  ↓ (ADMITTED_EVIDENCE)
                                    lane interpretation (Topologist → Cartographer → ...)
                                                  ↓
                                    MrLore narrative concurrence (spatial chain)
                                                  ↓
                                    EngAInOS final verification → ACCEPTED_DERIVED_TRUTH
```

Terms and gates are defined in
`../ENGAINOS_TIER1_AUTHORITY/ENGAINOS_EVIDENCE_ADMISSION_CONTRACT_v1.md`.
MrLore acts **on request** from EngAInOS. It does not intercept producer
output.

## 3. Packet: `mrlore.canon_review_packet.v2`

v2 keeps every v1 field and requirement (v1 §4–§6) and adds:

```json
{
  "contract": "mrlore.canon_review_packet.v2",
  "request_id": "engainos review request this answers",
  "admission_ref": "admission_id or intake artifact id under review",
  "findings": [
    {
      "finding_id": "f_001",
      "subject_ref": "local_ref or canonical id under review",
      "finding": "supported",
      "basis": "canon anchor / source spans relied on",
      "source_span": {"source_text_id": "...", "char_start": 0, "char_end": 0}
    }
  ]
}
```

`finding` vocabulary:

| Value | Meaning |
|---|---|
| `supported` | Consistent with established canon; anchor cited |
| `contradicted` | Conflicts with established canon; contradiction recorded |
| `ambiguous` | Canon admits more than one reading; nothing is flattened |
| `insufficient_evidence` | Canon has no anchor either way |
| `continuity_conflict` | Sources disagree with each other (e.g. a pronoun change for one character); surfaced, not fixed |

## 4. Authority boundary

MrLore MAY (unchanged from v1 §7): state canon status within its lane, name
aliases and lineage, identify contradictions, require source anchoring, and
stop for human review.

MrLore MUST NOT emit fields that are EngAInOS decisions: `allowed`,
`admitted`, `accepted`, `spawn`, runtime mutation, or any write to declared
scene, entity or runtime truth. A finding, including `canon_status:
confirmed`, is **input** to EngAInOS's verdict and never the verdict.

All v1 hard rejects (§6) still apply. In addition, EngAInOS MUST reject a
v2 packet if:
- `findings` is missing (it can be empty),
- any `finding` value is outside the vocabulary above,
- any finding lacks `basis`,
- the packet carries an EngAInOS verdict field (`allowed`, `admitted`,
  `accepted`).

## 5. Open (not decided by this contract)

- **Tier value.** v1 and the code use `authority_tier: 3`. The lane
  instructions (`mrlore_1stlane_canon_authority/LANE_INSTRUCTIONS.md`) state
  `authority_tier == 1`, and the folder is `MRLORE_TIER1_AUTHORITY`. v2 keeps
  `3` for compatibility with the existing gates until this is ruled.
- **Identity split.** The authority map gives MrLore authority over
  "character identity"; EngAInOS owns "declared entity truth". The reading
  used by the Gen2 design is that MrLore rules whether a name is a canon
  alias of an entity, and EngAInOS records and mints the declared-entity id.
  This needs confirmation.

## 6. One-line contract

**MrLore remembers and advises on request; EngAInOS decides; MrLore is
never a gate between extraction and governance.**
