I agree with the architectural correction, especially the requirement that all four ID layers remain stable—not just vocabulary IDs.

There's one distinction I'd add before we finalize v0.2: freezing an identifier doesn't mean freezing every fact associated with it. An occurrence can move because earlier prose was inserted. A mention can be reclassified. An entity's relationships can change. The ID remains stable, while its metadata and interpretation have version histories.

And you're right about the correction cost. Splitting one sword into two can invalidate a whole network of relationships. We need dependency-aware reprocessing, not merely redirecting references.

I'm going to make three concrete recommendations in the revision:

* Use `occ#` identifiers, rather than making them optional. They're worth the modest storage and allocator cost because they'll give us durable references across manuscript revisions.

* Separate character identity from player control. A character should not need a new identity just because they become playable or stop being playable. We'll preserve `player#` as a proposed convention, but recommend `char#` for persistent character identities.

* Preserve exact spelling separately from normalized vocabulary. `The` and `the` can usually share a word ID, but capitalization must never be lost. Lemmatization—combining forms such as sword and swords—should not happen automatically.

These are design recommendations, not conclusions about what Gen2 currently implements.

# EngAIn — ID-Based Symbolic Parsing Blueprint

**Version:** 0.2
**Date:** November 9, 2026
**Status:** Proposed architecture — not implemented or verified
**Candidate integration:** Gen2, Mettaext, or shared parsing infrastructure
**Purpose:** Establish a stable, revision-safe identity foundation for manuscript interpretation and downstream EngAIn systems.

---

## 1. Objective

Convert authored manuscript prose into a stable, reusable representation that supports semantic recognition, identity resolution, grammatical analysis, and symbolic relationship processing.

The system must preserve every word and punctuation mark while allowing meaningful phrases to be recognized as complete units.

A failure to recognize a phrase must never corrupt the underlying word index or force unrelated identifiers to change.

**Core principle: Words are indexed independently of interpretation. Mentions group word occurrences. Entities represent recognized identities. Relationships connect those identities using grammatical and narrative evidence.**

The manuscript remains the source of authored canon.

Parsing results are interpretations of that source, not replacements for it.

## 2. The Four-Layer Identity Model

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

## 3. Complete Worked Example

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

## 4. Missed Spans and Corrections

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

## 5. Grammatical and Symbolic Processing

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

## 6. Identity Stability and Revision Rules

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

## 7. Derived Relationship Provenance

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

## 8. Punctuation and Whitespace

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

## 9. Capitalization and Normalization

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

## 10. Capacity and Allocation

Abandon the ambiguous global one-million-ID limit.

Each namespace needs its own allocation mechanism and capacity policy.

A manuscript containing one million word occurrences may have far fewer distinct vocabulary entries, but potentially millions of occurrence records.

Recommended characteristics:

- Independent, monotonic namespace allocators.
- Sufficient capacity for long-term corpus growth.
- No recycling of tombstoned identifiers.
- Atomic allocation where multiple writers are possible.
- Unique namespace-qualified identifiers.
- Stable serialization across Python, Godot, and other EngAIn consumers.

All IDs are serialized as strings or explicitly typed integer components.

If hierarchical IDs such as `12.1` or `12.1A` are later adopted, they must remain exact string or structured identifiers rather than floating-point numbers.

Their semantics are not yet approved.

## 11. Processing Architecture

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

## 12. Proposed Integration Options

### Option A — Gen2 integrated implementation

Gen2 owns lexical indexing, mention recognition, entity resolution, and symbolic parsing.

Best suited if its existing implementation already provides the necessary persistence, identity governance, and correction facilities.

### Option B — Shared identity/index component

Gen2 and Mettaext can submit recognized spans to shared infrastructure responsible for vocabulary, occurrences, mentions, identities, and revisions.

Best suited if both parsers need consistent access to durable identifiers.

### Option C — Hybrid design

A shared lossless index and identity registry provides stable references.

Gen2 or Mettaext performs semantic recognition and symbolic relationship extraction using that foundation.

This is a promising candidate because it separates long-term manuscript identity persistence from parser-specific interpretation.

**No integration option has been approved or verified against the codebase.**

Do not introduce a separate ID Machine simply to satisfy the conceptual diagram.

First inspect existing implementations and ownership boundaries.

## 13. Required Gen2 / Mettaext Audit

The implementation audit must establish:

1. Where source text enters the production pipeline.
2. How the parser tokenizes words and punctuation.
3. Whether it preserves all grammatical words.
4. How source offsets and document revisions are stored.
5. Whether stable vocabulary or occurrence identifiers already exist.
6. Whether semantic spans are represented independently of words.
7. Where character, location, and item IDs originate.
8. Whether mention resolution distinguishes identical descriptions from identical entities.
9. How aliases and recurring identities are resolved.
10. Whether relationship evidence and dependency tracking exist.
11. How parser corrections propagate to downstream consumers.
12. Whether a shared registry already performs any of these functions.
13. Whether Gen2 and Mettaext can be compared through their genuine execution paths.
14. Whether HTTP handlers bypass any intended parsing component.
15. Whether `pipeline_runner` actually invokes the expected production components.

Historical bypass behavior must be verified rather than assumed to represent either parser's output.

## 14. Acceptance Tests

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

## 15. Open Decisions

The following require approval or implementation evidence:

1. Final canonical ID spelling and namespace conventions.
2. Whether `char#` replaces `player#` for persistent narrative identity.
3. Whether dotted extensions such as `12.1A` have a justified role.
4. Exact normalization and case-sensitivity policy.
5. Source-revision alignment and occurrence reconciliation strategy.
6. Whether overlapping and discontinuous mentions require additional schema support.
7. Entity merge/split governance and approval requirements.
8. Relationship dependency tracking and downstream invalidation contracts.
9. Whether a shared component is necessary or whether Gen2 can own the architecture.
10. Compatibility requirements for existing EngAIn entity references.

## 16. Engineering Decision

The proposed baseline is:

**Immutable vocabulary and occurrence identities, versioned mention recognition, persistent entity identities, and provenance-aware relationship processing.**

The design must support semantic corrections without destabilizing the underlying manuscript index.

Gen2 and Mettaext must be audited against this requirement before any implementation placement decision.

The first implementation milestone should demonstrate correct lexical indexing and stable occurrence references on a small manuscript fixture before attempting full-world semantic resolution.

---

**Assessment boundary:** This is a proposed architecture for evaluation. It does not establish the existing functionality or operational status of Gen2, Mettaext, or other EngAIn subsystems. Verified component findings must be recorded in their own assessment threads.

### Assessment conclusion

Version 0.2 now gives us a coherent design to evaluate against actual code. It doesn't guarantee that Gen2 can correctly identify every character, object, or grammatical relationship, but it provides a stable foundation when those interpretations are imperfect.

The most consequential decision is keeping the lexical index independent of semantic interpretation. That allows us to improve or even replace the parser without having to rebuild the manuscript's identity foundation from scratch.

The next step is an inspection, not an implementation: establish what Gen2 and Mettaext already provide, then decide whether this architecture fits inside Gen2 or requires shared infrastructure.
