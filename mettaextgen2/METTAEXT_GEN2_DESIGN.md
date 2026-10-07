# Mettaext Gen2 — Design

Status: DESIGN (no Gen2 code exists). Drafted 2026-10-06 from `mettaextgen2.md`
plus a read-only audit of tier1/engainos, tier1/paradox_machine,
tier2/topologist, tier2/cartographer, tier2/engionality, tier2/worldfield,
tier2/godotsim, tier3/mettaext and Book 09 (chapters 048–055).

Each section marks itself **DECIDED** (settled in the design discussion),
**AUDIT-FOUND** (forced by what the code or manuscript actually contains), or
**OPEN** (needs a decision before build).

---

## 1. Terminology — DECIDED

Gen2 is a different extractor, not a revision of tier3/mettaext. Its internal
stages are **extractors**, named by function. They are never called
"Pass 1/2/3": that name belongs to the manuscript metta-pass workflow
(currently on 021–023), which is a separate process at a different scope.

| Name | Scope |
|---|---|
| Manuscript metta pass | Editorial workflow over chapters; produces the yaml scene-meta blocks |
| Gen2 extractor | One specialised stage inside a single Gen2 extraction run |
| Gen2 Reconciler | Final stage of one run; local epistemic authority only |
| Old Mettaext passes | `tier3/mettaext/passroom/pass1..pass5`; legacy, unchanged |

## 2. Core model: progressive semantic annotation — DECIDED

- The source text is immutable. Extractors add **annotations** onto spans of it.
- Every extractor sees all prior annotations.
- An extractor does not re-classify a span that is already confidently
  classified. It may **enrich** it (add a relation, state, or location) or
  **challenge** it.
- A span may take part in many facts without becoming many entities.
  "Zephyr's staff" yields a CHARACTER, an ITEM, an ownership relation, and
  possibly an origin. It is still one CHARACTER and one ITEM.
- Early extractors make the **least semantically dangerous** decisions
  first. Grammar such as "this is a possessive" is safe. Inventing a new
  character from an unfamiliar capitalised token is the most dangerous
  decision, and comes last and with the most evidence.

Candidate extractor chain (the order is a hypothesis; see §9):

```
Linguistic → Entity → Relationship/State → Spatial → Temporal/Event
          → Visual/Thematic → Remainder → Reconciler
```

This chain is now specified as **independent modules with explicit
interfaces** in `GEN2_MODULES.md`: one responsibility each, a declared
`requires`/`produces`, allowed and forbidden assertions, and failure,
confidence and provenance rules. The chain above is the default DAG order;
the experiment in §9 varies it.

## 3. Evidence classes — DECIDED (author metadata), AUDIT-FOUND (shape)

Book 09 chapters interleave prose with fenced ```` ```yaml ```` `scene meta:`
blocks under `### scene NNN.N — title` headers. These blocks come from the
manuscript metta passes (location, time, POV, participants, per-entity
state, explicit non-inferences).

Gen2 treats them as a **distinct, higher-authority evidence class**. It does
not strip them and does not read them as prose.

| Class | Source | Authority | Rule |
|---|---|---|---|
| `AUTHOR_METADATA` | yaml `scene meta` blocks, scene headers | Higher than prose inference | Prose extractors may not contradict it; conflicts become CHALLENGEs, never silent overrides |
| `PROSE` | Narrative text | Normal | Subject to the full extractor chain |
| `REGISTRY_PRIOR` | Committed entity registry entries | Context only | May be matched or challenged, never mutated by Gen2 |

**Metta is structured evidence, not structured declarations.** Gen2 must not
reduce a scene-meta block to a list of entities. A block carries at least
five kinds of statement, and each one constrains extraction differently:

| Kind | Example (048.5) | Gen2 treatment |
|---|---|---|
| Assertion | `location: Mika's grave / Falcon Ridge` | Supporting evidence for prose annotations |
| Presence qualifier | `Mika Covenant (grave and memory only)` | Referenced, not present; never spawnable |
| Editorial placement | `time: Y17,511 M6 D22` + "not a source-exact calendar date" | Carried with its qualification; never promoted to source fact |
| Unresolved state | `protocol Key state: ... custody unresolved` | Preserved as unresolved; prose may add evidence but must not silently close it |
| Explicit non-inference | `Zaron state: ... no death, dormancy, merger ... is inferred` | Negative constraint; no extractor may emit the excluded states |

Gen2 receives these blocks parsed (yaml), not as prose, so the
structure survives into extraction.

Rules forced by what the blocks contain:

- Participant qualifiers are binding. In
  `Mika Covenant (grave and memory only)` and
  `Five Mikas (remote/interstitial watchers only)`, the named entity is
  **referenced**, not **present** or spawnable.
- Explicit non-inference statements are **negative constraints**.
  `"no death, dormancy, merger ... is inferred"` means no extractor may emit
  that state.
- Metadata is under active editorial revision. Every metadata observation
  carries the source file's content hash, so a re-extraction after an edit
  is distinguishable from the earlier one.
- Metadata names never enter the registry without prose or registry
  corroboration. They are evidence, not identity.

The old Mettaext seeded characters from every capitalised word on the
`participants:` line (`tier3/mettaext/passroom/pass2_enhanced.py:727-731`).
That behaviour is explicitly not carried forward.

## 4. Annotation record — DECIDED (shape), OPEN (serialisation)

Each annotation records:

```
annotation_id      run-local
extractor          which extractor produced it
evidence_class     AUTHOR_METADATA | PROSE | REGISTRY_PRIOR
span               {source_file, source_sha256, scene_id, line, char_start, char_end, text}
kind               token_class | entity | relation | spatial | temporal | affect | visual | remainder
value              kind-specific payload
confidence         0..1
status             see §5
alternatives[]     unresolved readings, each with its own supporting evidence
supports[]         annotation_ids that corroborate it
challenges[]       {by_annotation_id, reason}
```

Ambiguity is data. For "taken from the log", Gen2 emits **one** relation
with `alternatives: [removed_from_location, derived_from_material]`
and `status: unresolved`. Later evidence adds support to one of the
alternatives; it never replaces the annotation.

OPEN: the on-disk format (JSONL per run vs. a single artifact) and whether
character offsets are computed before or after quote/apostrophe
normalisation (see §8). Offsets must always refer back to the **raw** text.

## 5. Statuses and challenge flow — DECIDED

Entity statuses: `KNOWN` (in committed registry), `OBSERVED` (definitely
present in source, new), `CANDIDATE` (likely entity, uncertain),
`ALIAS_CANDIDATE` (may be an existing entity), `REJECTED` (not an entity).

```
raw prose → candidate annotation → support / challenge from later extractors
          → Reconciler → reconciled observation (+ registry proposal)
```

Annotations are not immutable, but they are never silently replaced. A later
extractor issues `CHALLENGE(target, reason)`, and the Reconciler decides
between rejected, revised, or still ambiguous. Full provenance is kept.

## 6. Identity — DECIDED, with AUDIT-FOUND structural correction

### 6.1 Local references only
- **Gen2 never mints canonical entity IDs.** Within a run it uses local
  references (`candidate_A`). These are meaningless outside that run.
- Canonical IDs are minted and merged only at the Tier-1 EngAInOS
  governance boundary.
- Strings are evidence about identity, not identity itself.

### 6.2 Aliases are scoped, not global (structural correction)
Book 09 shows that the same title refers to different beings in different
scopes:

| Surface | Where | Referent |
|---|---|---|
| The Keeper | 049:919 | Lentharis (appositive), Umbrageous spire |
| The Keeper | 050:239 | the node's keeper ("its"), not Lentharis |
| The Keeper | 052:331 | unresolved (possibly Geralt) |
| the Anchor | 050:189 | Geralt (epithet) |
| the Anchor | 055:888 | a condition Geralt bears, not a name |

So an alias is **not** an attribute of an entity. It is a relation:

```
ALIAS(surface, entity_ref, scope, evidence[], status)
scope ∈ {span, scene, chapter, arc/era, global}
```

The scope defaults to the narrowest scope the evidence supports.
Promoting an alias to `global` is itself a governed registry change.
Gen2 may never infer a global alias from a single scoped binding.

### 6.3 Other identity hazards found in Book 09
- **Name/word collision.** The Five Mikas are Red/Blue/Green/White/Violet,
  so capitalised "Red" (048:415) is a person and lowercase "red" (048:538)
  is a colour. Classifying by case alone is insufficient.
- **Pronoun inconsistency in source.** Kyh is "He" (052:81) and "she"
  (054:77, 055:743). Coreference must not split an entity on gender. The
  inconsistency is surfaced as a continuity flag, not fixed.
- **Disputed name.** "Was. he is dead." (050:199): the speaker rejects
  the name, but the entity is the same.
- **Casing variants of one entity.** "the Applicator" / "the applicator";
  "Mages’ Guild" / "guild".

## 7. Authority boundary — DECIDED

```
SOURCE → Gen2 extractors → Gen2 Reconciler
       → reconciled observations + registry proposals        ← Gen2 authority ends here
       → Tier-1 EngAInOS: ACCEPT | REJECT | HOLD | CONFLICT
       → persistent shared entity registry
       → Gen2 / MrLore / Paradox / Topologist / ... (read as REGISTRY_PRIOR)
```

- The **Reconciler's authority ends at the Gen2 output boundary.** It is
  intra-run epistemic reconciliation only.
- **Many systems may propose; only Tier-1 commits.** MrLore, Paradox and
  Topologist contribute evidence and proposals, never commits.
- **HOLD is a first-class verdict.** An alias candidate may stay pending for
  fifty chapters.
- The registry is an **entity** registry (characters, creatures, factions,
  named items, and possibly locations; see §11), held outside Gen2.

## 8. Current-state gaps — AUDIT-FOUND

The authority model above is doctrine. As of 2026-10-06 the code does not
implement its governance half.

### 8.1 EngAInOS cannot yet receive Gen2 output
| Gap | Evidence |
|---|---|
| No entity registry, no canonical ID minting, no alias table | No `ENTITY_*`/`entity_registry` anywhere; ids are free strings (`tier1/engainos/gates/gate_declared_truth_shape.py:56-61`) |
| Verdict is boolean; no HOLD/CONFLICT | `tier1/engainos/aproom/authority_gate.py:109-133` (`allowed: bool`) |
| Tier × reality-mode check stubbed | `authority_gate.py:549-550` (TODO) |
| AP rule set empty, so mutating actions error | HANDSHAKES.md:296-300 |
| No generic proposal envelope | `governance_packet.v1` exists only as a test fixture (`gate_governance_contract_board.py:36-63`) |
| Rejections/holds not persisted | `core/intent_shadow.py:242-321` (in-memory) |
| Proposer tiers hardcoded; Gen2/Paradox/Topologist absent | `core/agent_gateway.py:368-372` |
| Admission logic lives in tier2 | `tier2/godotsim/runtime_gateway.py` (flagged HANDSHAKES.md:21) |

Precedent to reuse: Paradox's gate already returns
ACCEPTED/REJECTED/SUSPENDED (`tier1/paradox_machine/gates/temporal_gate.py:17-63`),
which is the nearest existing shape to ACCEPT/REJECT/HOLD/CONFLICT.

### 8.2 Doctrine already violated
- Topologist mints scene-scoped ids itself:
  `entity_id = f"{scene_id}.{slugify(hint)}"`
  (`tier2/topologist/artifactroom/passroom_signal_converter.py:168-176`).
  This conflicts with "only EngAInOS mints".
- The design's "Topologist" is `tier2/topologist/`. `tier2/cartographer/` is
  the metric-layout stage downstream of it.

### 8.3 The capitalisation failure is two-headed
Gen2 fixes only one of the two places where capitalised tokens become
characters:

1. `tier3/mettaext/passroom/pass2_enhanced.py:61,674-733`: any
   capitalised 4+ letter word seen 3+ times becomes a `Character`. The old
   extractor, replaced by Gen2.
2. `tier2/godotsim/scene_extractor.py:303-321` (`_discover_entities`) plus
   `tier2/godotsim/scene_manager.py:185-206`: these independently rediscover
   capitalised words and promote them to simulated entities keyed by
   lowercased name.

**Integration requirement:** before Gen2 output feeds godotsim, path 2 must
be disabled for Gen2-sourced scenes, or changed to consume Gen2 entities. If
it is not, a clean Gen2 still produces junk entities at runtime. This is a
godotsim change and needs its own approval.

## 9. Extractor ordering experiment — DECIDED (method)

The manuscript teaches the order. There is **one Gen2 and one
cross-manuscript regression corpus**, not a corpus per book. Book 09 is the
seed: it supplied the first 28 cases (`B09-01` … `B09-28`). The corpus grows
only when some source exposes a failure mode the existing cases do not cover.
For example, a new Book 03 problem becomes `B03-29`. Case numbers are
corpus-global; the id prefix records which source supplied the case.

Sources are declared as keyed entries in the spec
(`sources.B09 = {book, title, root, files: {name: {sha256, chapter}}}`).
The builder has no notion of "book": it resolves `(source, file, line range)`
references and freezes the excerpts. Each excerpt carries `source`,
`source_book`, `source_chapter`, file, lines and sha256. Roots can be
overridden per source with `METTAEXT_GEN2_SOURCE_ROOT_<KEY>`.

| File | Role | Edited by |
|---|---|---|
| `corpus/gen2_cases_v1.json` | Sources + case spec: spans, anchor, evidence classes, problem tested, expected constraints, expected non-results, review state | Hand (author review happens here) |
| `corpus/build_gen2_corpus.py` | Resolves spans to verbatim text, attaches provenance, parses metadata yaml structurally. **Never interprets text.** | Code |
| `corpus/gen2_hard_passages_v1.json` | Generated corpus; `--check` fails if stale | Never by hand |

The corpus is frozen at three levels: chapter sha256 pins, a per-case anchor
string, and a fingerprint over the excerpt set (`frozen_passages_sha256`).
Expectations and review state can change; the excerpted text cannot without
a new `corpus_version`. Cases are `DRAFT_UNREVIEWED` until author review, and
scoring uses `REVIEWED` cases only.

**Expected non-results are the architectural contract.** Each case states
what a correct extractor must *not* produce, using a closed vocabulary that
the builder validates:

```
must_not_create_entity / _item / _location   must_not_alias
must_not_globalize_alias                     must_not_resolve
must_not_emit_transfer / _movement           must_not_mark_present
must_not_split_entity                        must_not_infer_state
must_not_treat_as_fact                       must_not_treat_as_dialogue
```

For example, B09-13 (the third "Keeper") requires `must_not_resolve`,
`must_not_alias → Lentharis` and `must_not_globalize_alias`. B09-28
(author metadata) requires `must_not_infer_state` for Zaron and Oreck, and
`must_not_treat_as_fact` for the editorial date. A non-result violation is a
hard failure regardless of how much else the extractor got right.

Run candidate orderings and measure:

- false entities (REJECTED-expected tokens emitted as entities)
- missed entities
- ambiguities correctly preserved vs. prematurely resolved
- wrong relations and transfers (e.g. B09-04 "Geralt took it" is a handshake)
- **correction pressure**: the rate of later-extractor CHALLENGEs against
  earlier extractors. Persistent challenges from extractor N to extractor
  M < N indicate a dependency violation in the ordering.
- final Reconciler accuracy against gold

Corpus categories: possessive-as-location, capitalised non-entities,
name/colour collision, scoped and colliding titles, epithets, unnamed→named
referents, title-only entities, item transfers (true, false, momentary
re-grab), from-as-material vs. from-as-location, negated movement and
location, recalled and unquoted speech, pronoun inconsistency, casing,
apostrophe and quote variants, and an author-metadata block.

## 10. Output contract — SUPERSEDED by `GEN2_OUTPUT_CONTRACT.md`

The first draft of this section had Gen2 project into each consumer's schema.
That was wrong in three places once checked against the existing contracts:
Gen2 would have emitted Topologist's RCC-8/OLINK/MOVELINK links,
Engionality's `affect_state`, and WorldField's `terrain_profile`. Each of
these belongs to the consumer's lane. `affect_state` is also a hard reject
in `METTAEXT_TIER3_PARSE_AUTHORITY_CONTRACT_v1` §6.

The output contract is now derived from the existing contracts
(`mettaext.parse_artifact.v1`, `TIER2_PRODUCTION_MAP.md`, the per-system
authority contracts) in `GEN2_OUTPUT_CONTRACT.md`. The rule there is:
**Gen2 describes; each consumer interprets in its own lane.**

The godotsim integration requirement in §8.3 still stands.

## 11. Open decisions

Rulings of 2026-10-06 (recorded in `GEN2_OUTPUT_CONTRACT.md` §5):
`parse_artifact.v2` (v1 untouched); flow Mettaext → EngAInOS with MrLore
advisory (the MrLore contract §10 is to be reconciled); Gen2 inherits scene identity from Chapterroom and never
mints it (three forms, `GEN2_OUTPUT_CONTRACT.md` §5a); affect,
terrain and spatial **cues** allowed, their interpretations forbidden.
Also ruled: EngAInOS governs twice. Intake admits `ADMITTED_EVIDENCE`;
final verification yields `ACCEPTED_DERIVED_TRUTH`; Topologist consumes
admitted evidence (`ENGAINOS_EVIDENCE_ADMISSION_CONTRACT_v1`, Proposed).
MrLore's flow is superseded by its v2 contract (Proposed).
Still open: where adapters and code live; the MrLore tier value; and the
identity split (MrLore rules canon aliases, EngAInOS mints declared-entity
ids). That split also refines §6.1 and §7 of this document.

1. **Sequencing vs. EngAInOS.** Gen2 could wait for the registry and proposal
   intake (ACCEPT/REJECT/HOLD/CONFLICT, persisted), or ship first and emit
   proposals that queue as HOLD. Recommendation: ship Gen2 first behind the
   adapters, with proposals written to a file queue that nothing commits.
   The authority boundary then exists from day one without blocking on
   EngAInOS.
2. **Proposal envelope.** A generic `registry_proposal` packet that any
   proposer can submit, gated per §7. It is not yet specified.
3. **Reconciler weighting.** Rule-based, statistical, or model-assisted.
   Under the co-dependent workflow (local models are gated workers, never
   planners), the leaning is a rule-based Reconciler, with model output
   entering only as evidence annotations.
4. **Registry scope.** Do locations get canonical IDs? Topologist and
   Worldfield key by scene and region today.
5. **Interim identity.** What consumers key on before canonical IDs exist.
   Run-local refs must never leak as if canonical.
6. **Topologist self-minting** (§8.2). Change Topologist to take
   Gen2 refs, or treat its `scene.slug` ids as local refs.
7. **MrLore preserve-entity allowlist.** The vault copy is
   `.engain/mrlore/lexicon/preserve_entity_allowlist.json`; the repo default
   lives in `tier1/mrlore/lexicon/`. It should become a proposal source, not a
   parallel registry.
8. **Normalisation layer.** Curly/straight apostrophes and quotes (050:422 is
   straight-quoted; Vek’tar/Vek'tar), source typos (`Was.he`, `North Star..`).
   Normalise for matching while keeping offsets on raw text. Typos are never
   "corrected" in source.

## 12. Non-goals

- Gen2 does not modify `tier3/mettaext/`. The old pipeline stays runnable.
- Gen2 does not write to the registry, the snapshot, or canon.
- Gen2 does not edit manuscript chapters or their metadata blocks.
