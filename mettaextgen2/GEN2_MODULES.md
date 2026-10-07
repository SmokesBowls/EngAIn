# Mettaext Gen2 — Module Interfaces

Status: DRAFT, 2026-10-06. No code exists. This defines the module
boundaries before implementation so that Gen2 does not become a monolith.

> **Modules describe. Authorities interpret. Adapters translate.**

Three independent replacement axes follow from that:

| Change | Must not require changing |
|---|---|
| An extractor module (rules → Claude → Qwen → deterministic parser) | `parse_artifact.v2`, other modules, any consumer |
| A downstream system's internal representation | Gen2 |
| An adapter | Gen2 or the consumer's authority logic |

---

## 1. Common module contract

Every module implements the same interface. This is the only way modules
talk to each other.

```
name                 stable identifier
version              semver; recorded in the artifact (run.modules[])
implementation_kind  rules | model | hybrid
requires             annotation kinds it reads
produces             annotation kinds it may write (enforced by orchestrator)

run(doc: SourceDocument, view: AnnotationView, config) -> ModuleOutput

ModuleOutput {
  annotations[]   new annotations only, each of a kind in `produces`
  challenges[]    {target_annotation_id, reason}: the only way to dispute another module
  diagnostics[]   {level, message}: never silent
}
```

### 1.1 Rules every module obeys

1. **Read-only past.** A module reads prior annotations through
   `AnnotationView`. It cannot modify or delete them; it can only challenge.
2. **Declared output only.** The orchestrator rejects any annotation whose
   kind is not in the module's `produces`.
3. **Provenance is not optional.** Every annotation's span is constructed
   through the shared span library (§3.1), so its offsets are validated
   against the raw source. A module cannot emit a claim without a span.
4. **Confidence is proposal strength.** It is a value in 0..1. A module scores
   its own evidence and never copies or inflates another module's confidence.
   The Reconciler alone weighs evidence across modules.
5. **No lane interpretation.** Each module has a FORBIDDEN list (§2), and
   the assembler re-checks the whole artifact against the lane line
   (`GEN2_OUTPUT_CONTRACT.md` §3.1).
6. **Fail closed, fail visible.** A failing module emits a diagnostic and
   **zero** annotations; partial output is never passed on. Modules that
   depend on it are skipped, and the artifact carries a warning naming what
   is missing. An artifact never implies completeness it lacks.
7. **Determinism.** `rules` modules are deterministic for the same input and
   version. `model` modules record model id, prompt version and decoding
   settings in `run.modules[]`. Their output is evidence only and passes the
   same validation (co-dependent workflow: local models are gated workers,
   never planners).
8. **No consumer imports.** No Gen2 module imports Topologist, Engionality,
   WorldField, GodotSim, Paradox, MrLore or EngAInOS code. This mirrors the
   existing rule "Passroom never imports topologist".

### 1.2 Orchestration and ordering

The orchestrator builds a DAG from `requires`/`produces` and runs it. Order
between modules that have no edge between them is **not** fixed. The
ordering experiment (design §9) permutes those orders, and also tests
whether edges are missing, using challenge rate ("correction pressure") as
the signal.

---

## 2. Modules

Each entry lists Input, Output, Allowed, Forbidden, Dependencies, Failure
mode, Confidence and Provenance, then the corpus cases that exercise it.
Kind names in `code` are annotation kinds.

### 2.1 `source_loader`
- **Input:** a source reference `(source key, file, root)` and the expected sha256.
- **Output:** a `SourceDocument`: raw text, sha256, line index, and a normalised view (curly/straight quotes and apostrophes unified) with an offset map back to raw.
- **Allowed:** reading and hashing the file; normalising for matching.
- **Forbidden:** altering raw text; repairing typos (`Was.he`, `North Star..`).
- **Dependencies:** none.
- **Failure mode:** missing file or hash mismatch, so the run aborts. Nothing is extracted from an unpinned source.
- **Confidence:** not applicable.
- **Provenance:** defines `source_text_id` and `source_sha256`.
- **Cases:** 17, 18 (apostrophe and quote variants).

### 2.2 `scene_segmenter`
- **Input:** `SourceDocument`, plus the Chapterroom scene packet it was given (`engain.scene_boundary_proposal.v1` / scene packet).
- **Output:** `region` annotations (prose / metadata_yaml / scene_header / structural_heading / separator); per region, a `scene` block with `source_scene_label` (from source markers) and the **inherited** `chapterroom_scene_id`, `chapter_id`, `boundary_method` and `authored_scene_boundaries_proven` (see `GEN2_OUTPUT_CONTRACT.md` §5a).
- **Allowed:** reading labels from source structure (`### scene 050.4`, yaml `scene:`); carrying Chapterroom identity through unchanged.
- **Forbidden:** minting or deriving any scene id; deriving the label from the Chapterroom index or the reverse; setting `runtime_stage_id`; silently re-segmenting when Chapterroom's boundaries disagree with the observed labels.
- **Dependencies:** `source_loader`; the Chapterroom input packet.
- **Failure mode:** an unparseable structure is marked `region: unknown` with a warning. When inherited boundaries disagree with the observed label regions (Book 09 today: `mechanical_word_chunk`), it emits a `scene_boundary_mismatch` warning and keeps both.
- **Confidence:** 1.0 for an explicit header label; inherited identity is passed through and not re-scored.
- **Provenance:** a span per region; the input packet id.
- **Cases:** 01, 29.

### 2.3 `metadata_reader`
- **Input:** `metadata_yaml` regions.
- **Output:** `metadata_constraint` annotations of kind assertion / presence_qualifier / editorial_placement / unresolved_state / non_inference.
- **Allowed:** reading author metadata as a higher-authority evidence class; tolerating different layouts (`scene meta:` nested vs. top-level keys).
- **Forbidden:** turning metadata names into entity declarations; resolving anything the metadata marks unresolved; dropping unknown keys (they are kept as raw `assertion`).
- **Dependencies:** `scene_segmenter`.
- **Failure mode:** a yaml parse error leaves the region raw, emits a warning, and produces no constraints from it.
- **Confidence:** 1.0 for the constraint's existence, which is not a claim that its content is true.
- **Provenance:** spans to the yaml line.
- **Cases:** 28, 29.

### 2.4 `linguistic_annotator`
- **Input:** `prose` regions.
- **Output:** `sentence`, `token`, `quote_region`, `possessive`, `contraction`, `capitalization_reason` (sentence_initial / heading / title / proper_candidate), `negation_scope`, `voice` (active/passive), `deixis`, `figurative` (simile, "as if").
- **Allowed:** grammatical and structural facts only.
- **Forbidden:** entity types, identities, relations. This module decides what words *are*, linguistically, never who they are.
- **Dependencies:** `scene_segmenter`.
- **Failure mode:** a sentence it cannot analyse is marked unanalysed. Downstream modules treat it as low-evidence, not as clean.
- **Confidence:** per annotation.
- **Provenance:** a token-level span.
- **Cases:** 01, 05, 09, 14, 21, 24, 27, 30, 31.

This module exists so that language structure constrains entity extraction
before anything names an entity. It addresses the "capitalised word becomes a
character" failure.

### 2.5 `entity_extractor`
- **Input:** linguistic annotations, metadata constraints, registry prior (read-only).
- **Output:** `entity_mention`, and `entity_candidate` with `local_ref`, type, status.
- **Allowed:** proposing entities; marking a candidate `KNOWN` only on a registry match.
- **Forbidden:** canonical ids; promoting a token whose `capitalization_reason` is sentence_initial or heading without further evidence; global identity claims.
- **Dependencies:** `linguistic_annotator`, `metadata_reader`.
- **Failure mode:** fail closed.
- **Confidence:** per candidate, with alternatives for type.
- **Provenance:** one span per mention.
- **Cases:** 01, 05, 06, 08, 09, 10, 20, 21, 24, 29.

### 2.6 `coreference_linker`
- **Input:** entity mentions, linguistic annotations.
- **Output:** `coref_chain`: pronouns, descriptions and fragments linked to a `local_ref` (voice → He → Vek'tar; The thing → Kulla).
- **Allowed:** in-text linking.
- **Forbidden:** splitting an entity on pronoun gender; resolving a pronoun whose antecedent is outside the span (it stays unresolved).
- **Dependencies:** `entity_extractor`.
- **Failure mode:** chains it cannot link are left open, not forced.
- **Confidence:** per link.
- **Provenance:** spans for both ends of each link.
- **Cases:** 02, 15, 22, 25, 26, 31, 33.

(This module is not in the original list. It is needed because pronoun and
description linking is a different problem from scoped naming.)

### 2.7 `alias_resolver`
- **Input:** entity candidates, coreference chains, registry prior, metadata.
- **Output:** `alias_candidate` `{surface, candidate_ref, scope, status, evidence[], confidence}`.
- **Allowed:** scoped candidates, defaulting to the narrowest scope the evidence supports.
- **Forbidden:** a permanent or global alias table; inferring `global` scope from a single scoped binding; accepting an alias the referent denies ("spirit").
- **Dependencies:** `entity_extractor`, `coreference_linker`.
- **Failure mode:** fail closed.
- **Confidence:** per candidate.
- **Provenance:** evidence spans.
- **Cases:** 03, 07, 10, 11, 12, 13, 16, 25, 29, 30.

### 2.8 `presence_detector`
- **Input:** entities, metadata presence qualifiers, negation scope, memory/grave contexts.
- **Output:** `presence` per entity per scene: present / referenced / absent.
- **Allowed:** presence evidence.
- **Forbidden:** spawn, position, or "spawnable" decisions (GodotSim / EngAInOS).
- **Dependencies:** `entity_extractor`, `metadata_reader`, `linguistic_annotator`.
- **Failure mode:** unknown presence stays `unknown`, never `present`.
- **Confidence:** per entity.
- **Provenance:** spans.
- **Cases:** 01, 02, 06, 28, 29.

### 2.9 `event_extractor`
- **Input:** entities, coreference, linguistic annotations (voice, negation).
- **Output:** `event` `{actor_ref, action, target_ref, object_ref, voice, temporal_frame}`, including item transfers.
- **Allowed:** what the text says happened, including passive events with unknown agents.
- **Forbidden:** inferred outcomes (quest completion, state changes beyond the text); turning a gesture into a transfer; turning a negated action into an event.
- **Dependencies:** `entity_extractor`, `coreference_linker`.
- **Failure mode:** fail closed.
- **Confidence:** per event, with alternatives.
- **Provenance:** spans.
- **Cases:** 02, 04, 19, 20, 31, 32, 33.

### 2.10 `dialogue_extractor`
- **Input:** quote regions, coreference, linguistic annotations.
- **Output:** `speech` `{kind: dialogue | recalled | inner, speaker_ref?}`.
- **Allowed:** speaker attribution when the span supports it.
- **Forbidden:** attributing a speaker from scene context the span does not contain (the speaker stays null, with alternatives).
- **Dependencies:** `linguistic_annotator`, `coreference_linker`.
- **Failure mode:** fail closed.
- **Confidence:** per attribution.
- **Provenance:** spans.
- **Cases:** 03, 18, 23, 24, 32, 33.

### 2.11 `temporal_cue_extractor`
- **Input:** linguistic annotations, metadata editorial placements.
- **Output:** `TEMPORAL_CUE` `{text, cue_type, anchor_hint}`, plus discourse order.
- **Allowed:** cues and order as written.
- **Forbidden:** temporal-law verdicts (Paradox); promoting an editorial date to a source fact.
- **Dependencies:** `linguistic_annotator`.
- **Failure mode:** fail closed.
- **Confidence:** per cue.
- **Provenance:** spans.
- **Cases:** 01, 07, 23, 32.

### 2.12 `spatial_cue_extractor`
- **Input:** entities, coreference, linguistic annotations.
- **Output:** `SPATIAL_SIGNAL` `{subject_ref, relation_phrase, object_ref, frame_hint, alternatives}`.
- **Allowed:** described relations, including frame hints ("behind him", relative to the character's facing).
- **Forbidden:** RCC-8 / QSLINK / OLINK / MOVELINK, coordinates, WorldField cells, absolute orientation the text does not give.
- **Dependencies:** `entity_extractor`, `coreference_linker`.
- **Failure mode:** fail closed.
- **Confidence:** per signal.
- **Provenance:** span text (MrLore concurrence needs it as `source_prose`).
- **Cases:** 02, 15, 30, 31, 33.

### 2.13 `distance_cue_extractor`
- **Input:** linguistic annotations, spatial signals.
- **Output:** `DISTANCE_CUE` `{text, subject_ref, object_ref, axis_hint}`.
- **Allowed:** quoting the measure as written ("ten paces").
- **Forbidden:** unit conversion into metric truth, or extents (Cartographer).
- **Dependencies:** `linguistic_annotator`; it reads `spatial_cue_extractor` output if present.
- **Failure mode:** fail closed.
- **Confidence:** per cue.
- **Provenance:** spans.
- **Cases:** 14, 16, 29, 30, 31.

### 2.14 `affect_cue_extractor`
- **Input:** entities, coreference, linguistic annotations.
- **Output:** `AFFECT_CUE` `{entity_ref, cue_text}`.
- **Allowed:** the evidence text attached to an entity.
- **Forbidden:** `AFFECT_STATE`, intensity, labels such as "afraid", relationship deltas (Engionality).
- **Dependencies:** `entity_extractor`, `coreference_linker`.
- **Failure mode:** fail closed.
- **Confidence:** per cue.
- **Provenance:** spans.
- **Cases:** 15, 16.

### 2.15 `terrain_cue_extractor`
- **Input:** linguistic annotations, locations.
- **Output:** `TERRAIN_DESCRIPTION` `{text}`.
- **Allowed:** descriptive spans.
- **Forbidden:** `TERRAIN_PROFILE`, `environment_type`, region contracts, keyword-table classification (trixelmap / WorldField).
- **Dependencies:** `linguistic_annotator`.
- **Failure mode:** fail closed.
- **Confidence:** per description.
- **Provenance:** spans.
- **Cases:** 07, 27.

### 2.16 `reconciler`
- **Input:** all annotations and challenges.
- **Output:** a per-annotation outcome (accepted / rejected / ambiguous-with-alternatives), `continuity_flags`, and a correction-pressure report.
- **Allowed:** intra-run epistemic reconciliation (design §5, §7).
- **Forbidden:** anything past the artifact boundary: registry commits, canonical ids, cross-run decisions. It is the module the original list called `uncertainty_handler`.
- **Dependencies:** all extractors.
- **Failure mode:** an unresolvable conflict leaves the item `ambiguous` with every alternative kept.
- **Confidence:** it computes reconciled confidence and records how.
- **Provenance:** keeps every supporting and challenging annotation id.
- **Cases:** 10, 13, 22, 32.

### 2.17 `artifact_assembler`
- **Input:** reconciled annotations and `run` metadata.
- **Output:** `mettaext.parse_artifact.v2`.
- **Allowed:** mapping and packaging, nothing else. It is deliberately boring.
- **Forbidden:** reinterpreting, adding, dropping or upgrading any annotation.
- **Dependencies:** `reconciler`.
- **Failure mode:** schema or lane-line validation failure means no artifact; the run reports why.
- **Confidence:** passed through unchanged.
- **Provenance:** required on every emitted item; an item without a span fails validation.
- **Cases:** all, via `global_expected_non_results`.

---

## 3. Shared libraries (not pipeline stages)

### 3.1 `span` / provenance
Builds and validates `source_span` against the raw text and the offset map.
Every module uses it. Provenance is enforced at creation and re-checked by
the assembler, never attached afterwards by a separate stage. A later
`provenance_builder` stage would let modules emit claims without provenance.

### 3.2 `annotation_store`
Append-only store. It gives modules a read-only `AnnotationView`, enforces
`produces`, and records challenges.

### 3.3 `lane_line`
The machine-readable form of `GEN2_OUTPUT_CONTRACT.md` §3.1: forbidden kinds
and fields. Used by the orchestrator (per module) and by the assembler (whole
artifact).

---

## 4. Downstream side (not Gen2)

```
parse_artifact.v2 → EngAInOS INTAKE (may consult MrLore) → ADMITTED_EVIDENCE
                                                              ├─ topologist adapter → Topologist → Cartographer
                                                              │      → MrLore narrative concurrence
                                                              ├─ paradox adapter
                                                              ├─ engionality adapter
                                                              ├─ worldfield / trixelmap adapter
                                                              └─ godotsim adapter
        lane outputs → EngAInOS FINAL VERIFICATION → ACCEPTED_DERIVED_TRUTH
```

- Adapters translate accepted evidence into each consumer's **existing**
  input format. Gen2 never imports them, and consumers never import Gen2.
- **Recommendation:** each adapter lives with its consumer, because translation
  into a lane's input is part of that lane's interpretation. Precedent:
  `tier2/topologist/artifactroom/passroom_signal_converter.py` is already
  Topologist's own adapter for the legacy `out_pass1_spatial` signals. A v2
  adapter sits beside it.

**Resolved (2026-10-06): EngAInOS governs twice.** Topologist consumes
**admitted** evidence (intake: contract, provenance and lane checks), not
final-approved truth. Final authority verification still comes **after**
Topologist → Cartographer → MrLore concurrence. This keeps HANDSHAKES §5's
order (interpretation before final verification) and puts an intake gate in
front of it. See
`docs/contracts/ENGAINOS_TIER1_AUTHORITY/ENGAINOS_EVIDENCE_ADMISSION_CONTRACT_v1.md`.
Note that Topologist's packet type `accepted_spatial_truth` is lane-accepted,
not EngAInOS-accepted (contract §5).

---

## 5. Where the code would live (proposal, not decided)

```
tier3/mettaextgen2/
  modules/<one file per module>.py
  lib/span.py  lib/annotation_store.py  lib/lane_line.py
  orchestrator.py
  schema/parse_artifact_v2.schema.json
  corpus/      (moved from mettaextgen2/corpus once accepted)
```

The import boundary is enforced by a gate in the style of the existing
`gates/` directories: no import of tier1 or tier2 consumer packages from
`tier3/mettaextgen2/`.

---

## 6. Implementation status (2026-10-06, first lever)

Code: `tier3/mettaextgen2/`. Run from repo root with `PYTHONPATH=.`.

| Implemented (v0.1.0, rules) | Not yet (their v2 sections are emitted empty, with a warning) |
|---|---|
| `source_loader`, `scene_segmenter`, `metadata_reader`, `linguistic_annotator`, `entity_extractor`, `presence_detector`, `reconciler`, `artifact_assembler`; libs `source`, `annotations`, `lane_line`, `artifact_schema` | `coreference_linker`, `alias_resolver` (the reconciler emits only span-scoped alias candidates), `event_extractor`, `dialogue_extractor`, temporal/spatial/distance/affect/terrain cue extractors |

- `python3 -m tier3.mettaextgen2.orchestrator --chapter-id … --scene-id …`: one Chapterroom scene → validated `parse_artifact.v2`.
- `python3 -m tier3.mettaextgen2.compare_legacy …`: legacy `=entities_observed` vs Gen2.
- `python3 -m tier3.mettaextgen2.corpus_runner`: corpus diagnostic (draft gold, not a score).
- Tests: `tier3/mettaextgen2/tests/` (unit tests + scene 048.5 acceptance).

**Corpus diagnostic, first run:** 68/76 evaluable checks pass; 97 expectations belong to modules not yet built. The remaining failures, in order of what they cost the Dragon:
1. **Presence from author metadata beyond `participants:`.** B09-29 (050.4) lists `damaged manifested Luminaire`, where descriptors are part of the entry, and records absence in `state ledger:` (`Five Mikas: Absent`, `Zaron: Absent and unresolved`). Owner: `metadata_reader` + `presence_detector`.
2. **Epithets and interface names declared as entities.** `Companion Protocol` (B09-07) and `The Anchor` (B09-16). Owner: `alias_resolver`.
3. **Known names seen only sentence-initially in a scene.** `Karvex` in 049 (B09-08) has no in-scene corroboration. It needs a registry prior or chapter-level evidence (design §6).
4. **Plural possessive.** `Mages’ Guild atrium` (B09-27) splits at `s’`. Owner: `linguistic_annotator`.
5. **Gold issue, not a Gen2 failure.** B01-34 expects `Nephoretti`, which is only implied ("two hundred beings") and never named in the span. Fix during author review.
