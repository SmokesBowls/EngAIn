# EngAIn — ID-Based Symbolic Parsing Blueprint

**Version:** 0.3
**Date:** November 9, 2026
**Status:** Proposed architecture — not implemented or verified
**Supersedes:** v0.2 (`lexicon id machine v2.md`). This sheet is the single current version.
**Proposed roles:** Lexicon = source inventory; Mettaext = intended semantic parser; EngAInOS = entity admission and identity (§13). Physical placement unresolved.
**Purpose:** Establish a stable, revision-safe identity foundation for manuscript interpretation and downstream EngAIn systems.

### Changes in v0.3

- Added §2, Architectural Rule — Lexicon-First, Two-Class Processing. "First Class / Second Class" is used instead of "Tier" to avoid collision with EngAIn's existing tier names.
- Proposed per-chapter occurrence allocation (§3, Layer 2; §11). `occ:87:1428` is an illustrative candidate, not an approved format. Vocabulary, mention and entity namespaces are unchanged.
- §13 rewritten: Integration Architecture (replaces the v0.2 Options A/B/C).
- §14 rewritten: Audit Findings and Remaining Verification (replaces the v0.2 audit checklist).
- Consistency edits: header "Candidate integration" line replaced by "Proposed roles"; §16 item 9 and §16 items 1 and 11 (separator, chapter key); §17 audit sentence; closing assessment updated to reflect the completed read-only audit.
- Dropped the conversational preamble that headed v0.2.

---

## 1. Objective

Convert authored manuscript prose into a stable, reusable representation that supports semantic recognition, identity resolution, grammatical analysis, and symbolic relationship processing.

The system must preserve every word and punctuation mark while allowing meaningful phrases to be recognized as complete units.

A failure to recognize a phrase must never corrupt the underlying word index or force unrelated identifiers to change.

**Core principle: Words are indexed independently of interpretation. Mentions group word occurrences. Entities represent recognized identities. Relationships connect those identities using grammatical and narrative evidence.**

The manuscript remains the source of authored canon.

Parsing results are interpretations of that source, not replacements for it.

## 2. Architectural Rule — Lexicon-First, Two-Class Processing

"Class" is used here instead of "tier" on purpose. EngAIn already uses tier for the `tier1/`–`tier3/` directories and for the actor authority tiers 0–3 in `AUTHORITY_TIER_SPEC_v1.md`.

### First Class — Source Inventory

Lexicon establishes the complete, persistent inventory of the canonical manuscript before semantic parsing.

Every word and punctuation mark is represented through:

- A reusable vocabulary or punctuation ID (`w#`, `p#`).
- A stable occurrence identity (`occ#`).
- An exact reference to the original source text.
- A source-revision record.

Inventory generation must not depend on whether a word describes a character, location, object, action, or grammatical relationship.

The inventory must be deterministic under a documented tokenization policy, lossless with respect to the retained manuscript, and independent of semantic interpretation.

**Authority rule:** Semantic processors cannot silently create, replace, renumber, or delete foundational inventory identities.

### Second Class — Semantic Claims

Parsers operate on the existing inventory by attaching evidence-backed claims to occurrence ranges.

Examples:

- `occ1201–occ1202` forms an item mention.
- `m17` resolves to `item7`.
- `item7` participates in a discovery event.
- That event provides narrative evidence supporting a scene object.

Claims must preserve:

- The originating occurrence references.
- The producing parser and version.
- Their classification and supporting evidence.
- Their acceptance, rejection, challenge, or supersession history.

Multiple parsers may propose different interpretations of the same occurrence range.

Disagreement must remain explicit until resolved by the appropriate authority.

**Authority rule:** A semantic claim does not become canonical truth merely because a parser emitted it.

### Parser Interchangeability

Mettaext, Gen2, rule-based extractors, or model-assisted extractors may operate over the same Lexicon inventory through a common annotation contract.

For example:

`Mettaext: occ44–occ45 → CHARACTER`

`Gen2: occ44–occ45 → REJECT CHARACTER`

Both claims reference identical source evidence and can be compared without converting between incompatible token inventories.

Parser interchangeability does not authorize multiple independent canonical identity registries or competing production execution paths.

### Runtime Provenance

A parser claim that an object should exist in a scene is distinct from proof that the object actually spawned.

EngAIn must preserve the chain:

**Occurrence → Mention → Entity → Narrative event → Admitted scene representation → Runtime spawn receipt**

A question such as "Which paragraph caused this sword to spawn?" must be answerable by tracing that chain backward to its supporting manuscript occurrence and paragraph.

### Correction and Recovery

Semantic interpretations may be challenged, corrected, superseded, or invalidated without renumbering the underlying lexical inventory.

Corrections to entities and events must also trigger review of dependent relationships and runtime-derived representations.

A lexical inventory may itself require repair if tokenization or source-revision matching was defective. Such repairs must be explicit, versioned, and auditable.

### Architectural Priority

**First class means foundational authority. Second class means derived interpretive authority—not lesser importance or lesser computational complexity.**

Parsing remains responsible for difficult semantic questions, but it no longer controls whether the underlying manuscript evidence exists or can be identified.

The initial implementation must establish this authority boundary before choosing the permanent chapter-key convention, ID separators, storage technology, or parser integration mechanism.

## 3. The Four-Layer Identity Model

The proposed architecture uses four independent namespaces.

| Layer | Namespace | Responsibility |
|---|---|---|
| 1. Vocabulary | `w#` | Unique reusable word identities |
| 2. Occurrence | `occ#` | Individual appearances in source text |
| 3. Mention | `m#` | Recognized spans of source occurrences |
| 4. Entity | `loc#`, `item#`, `char#`, etc. | Persistent identities of recognized things |

Punctuation uses its own symbol namespace, `p#`, referenced through occurrence records.

Each namespace has its own allocator.

The number `7` in `w7` is completely independent of the number `7` in `item7`.

No ID is a mathematical quantity or a substitute for its semantic classification.

### Layer 1 — Vocabulary

Every distinct registered word receives a permanent vocabulary identifier.

Examples:

- `w1` = in
- `w2` = the
- `w3` = mountain
- `w4` = of
- `w5` = korath

All repeated appearances reuse the established vocabulary identifier.

Ordinary grammatical words are included without exception.

No stop-word removal is permitted in the lossless indexing layer.

IDs are initially allocated in first-encounter order, but subsequent manuscript edits must not cause renumbering.

Vocabulary identity is independent of where a word appears.

### Layer 2 — Occurrence

Every appearance of a word or punctuation symbol can receive a persistent occurrence ID.

For example, the same word `w2` might appear at:

- `occ2` in Chapter 1
- `occ184` in Chapter 2
- `occ7291` in Chapter 14

Each occurrence references the same vocabulary entry but a different source position.

The occurrence ID is an **allocation ordinal, never a source-position number**.

An occurrence record contains source information such as:

- `occurrence_id`
- `symbol_id`
- `document_id`
- `source_revision`
- `char_start`
- `char_end`
- `sequence_position`
- `surface_text`
- `status`

Offsets and source positions are revision-dependent metadata.

When a paragraph is inserted earlier in the manuscript, unchanged occurrences retain their IDs even though their offsets and sequence positions may change.

Occurrence matching across revisions must use source-diff and alignment evidence. If an occurrence cannot be matched confidently, the system must not silently assign an old ID to potentially different content.

#### Chapter-scoped occurrence allocation (v0.3, proposed)

Vocabulary and entity IDs grow only as new identities are discovered. Occurrence IDs grow with essentially every word and punctuation mark. A 140-chapter manuscript might hold 50,000 vocabulary entries but several million occurrences.

The proposal is one occurrence allocator per chapter instead of one counter for the whole manuscript.

Illustrative candidate only, not an approved identifier format:

`occ:87:1428` = occurrence 1,428 in the chapter identified by `87`.

Each chapter's allocator starts at 1 independently.

- The chapter key must be a stable document identity. It must not be a revision hash or a filename, or every edit or rename would re-prefix that chapter's occurrences.
- This bounds each local counter, not the total number of occurrence records stored. Storage still grows with the manuscript.
- All other namespaces (`w#`, `p#`, `m#`, entity IDs) keep their own, unchanged allocators.
- The permanent chapter key and separator have not been selected (§16 items 1 and 11). The colon compatibility concern remains open.

### Layer 3 — Mention

A mention identifies a recognized span of prose.

Examples:

- `m1` = mountain of Korath
- `m2` = Geralt
- `m3` = legendary sword

Each mention links to the exact occurrence IDs that produced it.

A mention is not necessarily an independently existing object.

It is a particular textual reference that may resolve to an entity.

Multiple mentions may resolve to the same entity, and a mention may remain unresolved when the evidence is insufficient.

Mentions are contiguous occurrence spans by default. Overlapping spans are permitted, including a larger location name containing a separately recognized proper name.

Noncontiguous constructions may require a future extension rather than forcing invalid contiguous ranges.

Mention IDs remain stable. Corrections are versioned, and a materially different mention is allocated a new ID rather than silently redefining an unrelated existing reference.

### Layer 4 — Entity

Entities represent persistent narrative identities.

Proposed categories include:

| Example | Intended type |
|---|---|
| `loc3` | Location |
| `item7` | Item or object |
| `char5` | Character |
| `event8` | Event |

These are independent ID namespaces.

The earlier `player#` convention remains under consideration. A persistent character identity should ideally remain unchanged when its gameplay role changes.

For example, `char5` could have a runtime attribute indicating that the character is player-controlled.

An entity may be referenced by many different mentions across chapters.

Two objects with identical descriptive words must not automatically share an entity ID.

## 4. Complete Worked Example

Original manuscript:

> In the mountain of Korath, Geralt found a legendary sword.

### Vocabulary registry

| ID | Word |
|---|---|
| `w1` | in |
| `w2` | the |
| `w3` | mountain |
| `w4` | of |
| `w5` | korath |
| `w6` | geralt |
| `w7` | found |
| `w8` | a |
| `w9` | legendary |
| `w10` | sword |

Punctuation:

- `p1` = comma
- `p2` = period

All IDs are illustrative.

### Occurrence sequence

```text
occ1  -> w1    In
occ2  -> w2    the
occ3  -> w3    mountain
occ4  -> w4    of
occ5  -> w5    Korath
occ6  -> p1    ,
occ7  -> w6    Geralt
occ8  -> w7    found
occ9  -> w8    a
occ10 -> w9    legendary
occ11 -> w10   sword
occ12 -> p2    .
```

The occurrence sequence preserves every word and punctuation symbol.

Whitespace and exact original formatting remain in the retained manuscript source rather than becoming separate vocabulary tokens.

### Mention recognition

```text
m1 = [occ3, occ4, occ5]
     "mountain of Korath"

m2 = [occ7]
     "Geralt"

m3 = [occ10, occ11]
     "legendary sword"
```

### Entity resolution

```text
m1 -> loc3
m2 -> char5
m3 -> item7
```

The primary semantic view can now contain:

```text
location: loc3
actor:    char5
action:   found
object:   item7
```

This is a compressed semantic interpretation, not a replacement for the original occurrence sequence.

The action and its participants remain supported by the original textual evidence.

An event record may associate the finding with the location. It must not automatically assert that Geralt permanently owns the sword.

## 5. Missed Spans and Corrections

Suppose the first parser pass fails to recognize "legendary sword" as one item.

The vocabulary and occurrence records still exist:

```text
w9  = legendary
w10 = sword

occ10 -> w9
occ11 -> w10
```

A later pass recognizes the combined phrase.

It creates:

```text
m3 = [occ10, occ11]
m3 -> item7
```

No existing word or occurrence ID needs to change.

If the span is subsequently judged incorrect, its association can be revised or superseded.

The lexical foundation remains intact.

### Two identical descriptions, two actual objects

Two separate passages may both contain "legendary sword."

The same vocabulary IDs are used, but their occurrence and mention IDs differ.

```text
m3 -> item7

m27 -> item19
```

These can represent different swords if narrative evidence establishes distinct objects.

Alternatively, both mentions can resolve to `item7` if the narrative establishes that they refer to the same sword.

String similarity alone cannot determine physical identity.

## 6. Grammatical and Symbolic Processing

Grammar words and punctuation provide interpretation cues rather than automatically becoming interaction entities.

Registered symbols could include:

```text
w12   = or
w15   = and
w21   = in
p1    = comma
p2    = period
```

Suppose the entity registry contains:

```text
loc4  = Sundrift
loc55 = Falconridge
```

A semantic view can represent:

```text
loc4 w12 loc55
```

The corresponding language is:

"Sundrift or Falconridge"

A symbolic rule could recognize:

```text
LOCATION + OR + LOCATION
```

And produce a candidate structure:

```text
ALTERNATIVE(loc4, loc55)
```

This does not imply that the two locations physically interact.

It also does not establish what they are alternatives for. That requires wider grammatical or narrative context.

**Critical constraint:** Stable symbol lookup is deterministic; full language interpretation is not guaranteed to be deterministic or unambiguous.

Negation, quoted speech, temporal context, syntactic attachment, and other grammatical structures must still be considered.

## 7. Identity Stability and Revision Rules

All four namespaces follow the same fundamental rules.

1. Once allocated, an identifier is never reassigned to an unrelated record.
2. Identifiers are never renumbered solely because source positions change.
3. Corrected metadata and interpretations are versioned.
4. Deleted records may be tombstoned while retaining their historical identity.
5. Merges and splits must maintain explicit revision history.
6. Uncertain identity matches must not be silently accepted.
7. Historical references must remain resolvable or explicitly marked as superseded.

### Manuscript revisions

When prose is inserted, deleted, or rearranged:

- Existing vocabulary IDs are retained.
- Confidently matched occurrences retain their IDs.
- Newly introduced occurrences receive new IDs.
- Original and current source positions remain traceable by revision.
- Removed occurrences are tombstoned rather than reassigned.
- Dependent mentions are reviewed when their source coverage changes.

The ability to preserve occurrence identity across a substantial rewrite cannot always be guaranteed automatically. Ambiguous matches require new allocation or explicit reconciliation.

### Entity revision consequences

Suppose `item7` was initially believed to be one sword, but later evidence establishes that it represents two distinct swords.

The system must examine every relationship involving that identity.

Examples:

```text
HOLDS(char5, item7)
ATTACKS(item7, target9)
LOCATED_AT(item7, loc3)
```

These statements cannot simply be redirected to a new entity without considering which sword participated.

Affected derived relationships must be invalidated and re-evaluated against their evidence.

This is a dependency-reprocessing requirement, not merely an ID-remapping requirement.

## 8. Derived Relationship Provenance

Relationship records need their own lifecycle and evidence tracking.

Minimum proposed fields:

| Field | Purpose |
|---|---|
| `relationship_id` | Stable relationship-record identifier |
| `relation_type` | HOLDS, LOCATED_AT, ALTERNATIVE, etc. |
| `participants` | Referenced entity IDs |
| `evidence_mentions` | Source mention references |
| `source_revision` | Manuscript version |
| `parser_version` | Producing implementation |
| `derivation_dependencies` | Inputs supporting the relationship |
| `status` | Active, provisional, invalidated, superseded |
| `confidence` | Evidence confidence, if applicable |

A relationship may be directly supported by prose or inferred through additional rules. Its provenance must distinguish those cases.

When an entity or mention is corrected, dependent relationships are identified and reconsidered.

Downstream systems must not silently continue using invalidated relationships.

## 9. Punctuation and Whitespace

### Punctuation

Use a proposed `p#` namespace for punctuation symbol types.

Examples:

- `p1` = comma
- `p2` = period
- `p3` = question mark

Individual punctuation appearances use occurrence records, just like words.

A punctuation symbol type is not an individual punctuation occurrence.

### Whitespace

Do not create vocabulary tokens for ordinary spaces, tabs, or line breaks solely for manuscript reconstruction.

Instead, retain the complete original source.

Preserve exact source text, encoding, revision information, and offsets so the original prose can be recovered without guessing where whitespace belongs.

The indexed token stream does not replace the authoritative manuscript.

## 10. Capitalization and Normalization

**Proposed default:** Case-insensitive vocabulary matching while retaining the exact original spelling on every occurrence.

Examples:

```text
"The" -> w2
"the" -> w2
```

The original capitalization remains preserved in the occurrence's `surface_text` and the source document.

However, capitalization can carry meaning.

For example, "US" and "us" may have different interpretations.

"The Hague" is a named location even though its first word matches the ordinary determiner "the."

Therefore:

- Vocabulary normalization must be explicitly versioned.
- Proper-name recognition belongs to the mention/entity layers.
- The original surface text must always be preserved.
- Case-related ambiguities must have a defined handling policy.
- Lemmatization must be separate from vocabulary identity.

For example, "sword" and "swords" should not automatically become the same vocabulary entry simply because they share a lemma.

The final case-normalization policy remains open pending corpus tests.

## 11. Capacity and Allocation

Abandon the ambiguous global one-million-ID limit.

Each namespace needs its own allocation mechanism and capacity policy.

A manuscript containing one million word occurrences may have far fewer distinct vocabulary entries, but potentially millions of occurrence records.

Recommended characteristics:

- Independent, monotonic namespace allocators.
- Occurrence allocators scoped per chapter (§3, Layer 2).
- Sufficient capacity for long-term corpus growth.
- No recycling of tombstoned identifiers.
- Atomic allocation where multiple writers are possible.
- Unique namespace-qualified identifiers.
- Stable serialization across Python, Godot, and other EngAIn consumers.

All IDs are serialized as strings or explicitly typed integer components.

If hierarchical IDs such as `12.1` or `12.1A` are later adopted, they must remain exact string or structured identifiers rather than floating-point numbers.

Their semantics are not yet approved.

## 12. Processing Architecture

### Stage A — Source ingestion

Read canonical manuscript text.

Preserve source revisions, document identities, ordering, and verbatim content.

### Stage B — Lossless lexical indexing

Identify words and punctuation symbols.

Resolve vocabulary entries and allocate occurrence records.

This stage must not depend on successful semantic recognition.

### Stage C — Mention recognition

Identify spans representing characters, locations, objects, events, descriptions, and other meaningful units.

Create mention records tied to source occurrences.

### Stage D — Entity resolution

Associate mentions with established entities or create new entities when justified.

Retain ambiguity when identity is uncertain.

### Stage E — Symbolic parsing

Interpret grammatical cues, entity relationships, actions, alternatives, negations, and context.

Create evidence-backed structured relationships.

### Stage F — Dependency registration

Record which source occurrences, mentions, identities, and parser transformations support each relationship.

### Stage G — Downstream distribution

Publish stable identifiers and validated structured data to authorized EngAIn consumers.

Preserve provenance, versioning, and invalidation information.

### Stage H — Revision reconciliation

When the manuscript or parser changes, determine what can be retained and what must be recomputed.

Do not perform a blind full-ID replacement.

## 13. Integration Architecture

This section assigns architectural responsibility. It does not choose a directory, package, storage technology or wiring point. Physical placement of Lexicon stays unresolved until the implementation decision.

### Responsibilities

| Responsibility | Proposed owner | Class (§2) |
|---|---|---|
| Words, punctuation, occurrences, source references, source revisions | **Lexicon** (proposed authoritative source inventory) | First |
| Semantic parsing: mentions, entity candidates, events, relationships | **Mettaext** (original intended semantic parser) | Second |
| Additional semantic claims against the same inventory | Other processors (Gen2 rules, rule-based or model-assisted extractors) | Second |
| Entity admission and canonical entity identity | **EngAInOS**, under the existing authority contracts | — |

### Context

- **Mettaext** is the original intended semantic parser. It previously completed manuscript-to-3D-render processing in Godot. Its semantic functionality has reportedly been restored after the bypass and file-path corrections (see §14 for what still needs verification).
- **Gen2** was developed while the bypass problem was misunderstood: Mettaext was believed to be failing. Its October 6 design (`mettaextgen2/METTAEXT_GEN2_DESIGN.md` §2: progressive evidence accumulation over an immutable source, least-dangerous decisions first, enrich or challenge rather than re-classify) remains valuable. Its implementation has not established superiority over Mettaext.

### Principles

1. **One intentional production parsing path.** Competing extractors must not each establish foundational identities or run as parallel production pipelines.
2. **Shared inventory, many claims.** Multiple semantic processors may contribute claims against Lexicon's inventory. They must not create competing canonical identity authorities.
3. **Entity identity stays with EngAInOS.** Lexicon does not allocate canonical entity IDs (`char#`, `loc#`, `item#`). Entity admission and identity must remain consistent with the existing authority contracts, including `docs/contracts/ENGAINOS_TIER1_AUTHORITY/ENGAINOS_EVIDENCE_ADMISSION_CONTRACT_v1.md`.
4. **Responsibility before placement.** Deciding what Lexicon owns does not decide where its code lives or how it is wired.

Do not introduce a separate ID Machine simply to satisfy the conceptual diagram.

## 14. Audit Findings and Remaining Verification

### Reported evidence (read-only source investigation, November 9, 2026)

These findings come from reading source in the repository checkout. They describe that checkout on that date, not necessarily the live system.

- **Gen2 infrastructure.** Gen2 (`tier3/mettaextgen2/`) has source hashes (`SourceDocument`, `source_text_id = <file>@<sha256>`), validated character spans (`Span`, re-checked byte-for-byte by the `parse_artifact.v2` validator), and an append-only annotation store with challenges.
- **No complete lexical inventory.** Gen2's tokenizer matches letters only and emits token records only for capitalised words. Punctuation, digits and lowercase words get no records. There are no vocabulary IDs and no persistent occurrence IDs. Gen2 IDs (`a#####`, `ent_NNN`, `loc_NNN`) are valid only within one run.
- **Gen2 modules re-read raw text independently.** There is no shared token layer underneath them.
- **Gen2 tests.** 45 Gen2 tests passed when run during the investigation.
- **Gen2 has no production consumer.** Nothing outside Gen2 and its corpus builder imports it or consumes `parse_artifact.v2`.
- **Legacy Mettaext has an established pipeline.** `pipeline_runner` runs Chapterroom, then Passroom passes 1–5, then writes to Stageroom. It does not push to the runtime. Pass 1 is line-based and keeps no character offsets.
- **Several components independently generate or transform identifiers:**
  - Pass 5 slugifies canonical names into entity IDs.
  - `world_rules.json` provides name-keyed canonical names.
  - The runtime `SceneExtractor` rediscovers entities from capitalised words.
  - The runtime bridge lowercases entity IDs.
  - `canonical_scene_id` rewrites scene IDs.
  - Gen2 assigns run-local references.
- **The historical HTTP/Vault-linking bypass contributed to misleading runtime results.** Mettaext edits were tested, while live runtime results came by another path.
- **Observation to recheck, not a current-state classification.** In this checkout, `/world/sync` in `tier2/godotsim/http_handlers.py` referenced `engain_ingest.py` and `mettaext/` at the repository root, and neither existed there. The owner reports file-path repairs. Those repairs may live outside this checkout, for example in the Godot project or another tree.

### Remaining verification

1. Trace the currently restored Mettaext-to-Godot execution path end to end, including which server delivers the scene.
2. Verify the current state of the HTTP handlers and the Vault linker after the file-path repairs.
3. Compare Mettaext and Gen2 on identical manuscript passages through their genuine execution paths.
4. Identify which Gen2 capabilities genuinely improve on Mettaext.
5. Determine which redundant extraction and identity paths can be retired safely.
6. Validate a provenance chain from Lexicon occurrence through manuscript event to runtime spawn receipt (§2, Runtime Provenance).

Previously reported broken paths must not be classified as currently broken without rechecking them.

## 15. Acceptance Tests

| Test | Expected behavior |
|---|---|
| Vocabulary reuse | Repeated identical words reuse their vocabulary IDs |
| Common words | "The", "a", "or", and similar words are retained |
| Punctuation | Every punctuation occurrence remains traceable |
| Source fidelity | Original manuscript recovered exactly from retained source |
| Occurrence stability | Earlier insertions do not renumber unchanged matched occurrences |
| Deletion | Deleted occurrences are tombstoned, not reassigned |
| Missed semantic span | Corrected recognition requires no vocabulary renumbering |
| Multiword entity | Complete phrases resolve through mention records |
| Repeated reference | Multiple mentions can resolve to one established entity |
| Duplicate descriptions | Two physically distinct swords may retain separate identities |
| Ambiguous mention | Uncertain reference remains explicitly unresolved |
| Alternative syntax | "Sundrift or Falconridge" produces an alternative expression |
| Character role | Changing player-control status does not change character identity |
| Entity split | Dependent relationships are invalidated and re-derived |
| Normalization | Capitalization is preserved and ambiguities handled consistently |
| Source routing | Runtime traces prove which parser actually executed |
| Scale | Namespace allocation survives realistic full-manuscript indexing |

These are required behaviors, not tests currently reported as passing.

## 16. Open Decisions

The following require approval or implementation evidence:

1. Final canonical ID spelling and namespace conventions, including the separator. The `:` character is rewritten in some existing EngAIn paths, such as Godot node names and runtime scene-ID canonicalisation.
2. Whether `char#` replaces `player#` for persistent narrative identity.
3. Whether dotted extensions such as `12.1A` have a justified role.
4. Exact normalization and case-sensitivity policy.
5. Source-revision alignment and occurrence reconciliation strategy.
6. Whether overlapping and discontinuous mentions require additional schema support.
7. Entity merge/split governance and approval requirements.
8. Relationship dependency tracking and downstream invalidation contracts.
9. Physical placement and wiring of Lexicon (responsibility is assigned in §13; placement is not).
10. Compatibility requirements for existing EngAIn entity references.
11. The stable chapter key for chapter-scoped occurrence allocation. No numeric chapter identity exists in the current pipeline; the Chapterroom `chapter_id` is a filename-derived string.

## 17. Engineering Decision

The proposed baseline is:

**Immutable vocabulary and occurrence identities, versioned mention recognition, persistent entity identities, and provenance-aware relationship processing.**

The design must support semantic corrections without destabilizing the underlying manuscript index.

The read-only source audit is recorded in §14. Its remaining verification items must be completed before any implementation placement decision.

The first implementation milestone should demonstrate correct lexical indexing and stable occurrence references on a small manuscript fixture before attempting full-world semantic resolution.

---

**Assessment boundary:** This is a proposed architecture for evaluation. It does not establish the existing functionality or operational status of Gen2, Mettaext, or other EngAIn subsystems. Verified component findings must be recorded in their own assessment threads.

### Assessment conclusion

Version 0.2 gave us a coherent design to evaluate against actual code. It doesn't guarantee that Gen2 can correctly identify every character, object, or grammatical relationship, but it provides a stable foundation when those interpretations are imperfect.

The most consequential decision is keeping the lexical index independent of semantic interpretation. That allows us to improve or even replace the parser without having to rebuild the manuscript's identity foundation from scratch.

Version 0.3 records the read-only inspection (§14) and assigns responsibilities (§13): Lexicon as source inventory, Mettaext as the intended parser, EngAInOS as entity authority. The next step is still verification, not implementation: complete the §14 items before choosing placement or allocators.

This blueprint is not implementation authorization.
