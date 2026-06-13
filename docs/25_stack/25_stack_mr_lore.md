_mrlore taste: this is not a runtime project. It is a **canon firewall, evidence ledger, contradiction detector, identity review queue, and semantic-contract authority gate**. It should be treated as **AUTHORITY_WITH_FIX_FLAGS**, not full authority-ready, because the rules are strong but several queues and schema candidates still need human decisions.

## 1. PROJECT ROLE

_mrlore owns canon/lore review authority.

It owns:

Tier 0 prose protection. The ledger schema says extraction does not interpret, resolve contradictions, or promote canon, and no automated writer may mutate Tier 0 prose. It also requires every entry to trace back to verifiable source spans or quote IDs. 

Canon contradiction detection and routing. It can identify `contradiction_candidate`, `world_state_descriptor`, `unresolved_term`, timeline markers, relationship observations, and group agency checks, but it does not author the fix. 

Identity/entity review. The identity queue has 405 records split into ambiguous review candidates, bounded actor candidates, and identity braid candidates, all pending human review. 

Changed-file review flow. `collect_delta.py` reads CocoIndex flags, writes `raw/cocoindex_delta.txt`, then explicitly hands off to `tools/write_changed_manifest.py` and `tools/mrlore_run_changed.py`. 

It explicitly does **not** own:

Runtime execution, Godot scene loading, Trixel rendering, combat, behavior, AP mutation, or engine state.

Final authorship decisions. It detects, scores, stages, and blocks. Human decides.

Autonomous relationship promotion. Relationship predicates are review-only and require Tier 0 explicit prose or resolved canon decision.

Autonomous entity naming normalization. Identity braid candidates must stay in review until decided.

Neighboring projects that depend on _mrlore:

mettaext depends on _mrlore for clean canon-derived semantic facts and `.metta`-safe identity/relationship exports.

engainos depends on _mrlore to keep prose and canon ambiguity out of the runtime.

semantic contract consumers depend on _mrlore for prose-free scene/entity contracts.

canon reviewers depend on _mrlore for review queues, contradiction candidates, tier audits, and authority scores.

Trae depends on _mrlore as the judgment layer: Trae proposes; MrLore judges; human decides.

## 2. CURRENT WORKING STATUS

Confirmed working:

The vault tier audit exists and classifies 1,216 scanned files: 123 Tier 0 canon chapter prose, 140 Tier 1 canon/deep lore support files, 9 Tier 2 generated/parser artifacts, 651 Tier 3 loose notes, and 293 Tier 4 runtime/cache/script files. 

The changed-file sensor path is partly implemented: flags are collected, deduped, atomically written into `raw/cocoindex_delta.txt`, then handed to manifest/run tools. 

The latest full run report says 135 sources attempted, 135 ingested OK, 0 ingest errors, registry rebuild OK, lint OK, continuity audit clean, and 0 open `CONT-*.yaml`. 

The continuity audit report from 2026-06-07 says 135 sources audited and 0 findings. 

Partially working:

Chapter ledger extraction exists as a candidate contract and has been run, but it has triggered EXIT 2 on a low-confidence contradiction candidate in `001_the_ethereal_vigil.md`. 

Identity routing exists, but the queue is unresolved: 405 total records, including 294 ambiguous review candidates, 68 bounded actor candidates, and 43 identity braid candidates. 

Semantic scene/entity contracts exist as proof payloads and contract specs, but they are still candidate/proof-level, not proven as full automated canon-to-runtime export.

Untested or not fully proven:

Full promotion workflow from raw artifacts → ledger → identity resolution → semantic entity passport → mettaext/engainos export.

Human review application loop: `human_identity_reviews.jsonl` exists in the stack, but this profile cannot confirm that decisions have been applied to collapse the pending identity queue.

Complete relationship edge promotion. The predicate schema allows edges only with Tier 0 or resolved canon backing, but promotion tooling is not proven.

Abandoned, legacy, or proof-only:

Tier 3 loose notes and scratch files are explicitly review-only and individually promotable only after human review.

Tier 4 runtime/cache/script files are explicitly “do not ingest” material in the audit. 

Semantic scene/entity proof JSONs are proof-only examples until validated against actual exported canon payloads.

## 3. ERROR PROFILE

Import/path errors:

Likely around `_mrlore/cocowatch`, because `collect_delta.py` assumes `_HERE.parent` is `MRLORE_ROOT`, and `coco_flow.py` assumes the vault root is `MRLORE_ROOT.parent`. If the folder moves, delta paths break.

Potential CocoIndex dependency/import failure: `coco_flow.py` imports `cocoindex`, `FileLike`, `PatternFilePathMatcher`, and `localfs`. If the environment lacks CocoIndex, the sensor lane fails before manifest creation.

Missing files:

The run report includes many `[NOT FOUND]` entries under `building_the_world/markor/...`, even though the final exit code is clean. That means missing legacy references exist but were not fatal in that run. 

Duplicate files:

Tier audit shows duplicate-looking generated files like `out_pass1_05_the garden_blooms.txt` and `out_pass1_05_the_garden_blooms.txt`, plus corresponding `.metta` duplicates. 

Stale backups / loose archives:

Tier 3 contains `mrlore_first_ingest.tar.gz`, `tree.txt`, `project_tree.txt`, and broad scratch material. These should not feed authority directly. 

Schema mismatch:

`ARTIFACT_SCHEMA` forbids classification, confidence scoring, canon logic, relationship mapping, and wiki routing in Pass 1, while `CHAPTER_LEDGER_SCHEMA` handles object classes and confidence later. Any extractor that mixes Pass 1 and ledger responsibilities is wrong. 

Runtime bridge mismatch:

Semantic scene/entity contracts require runtime-safe, prose-free outputs. If engainos or Godot reads provenance, labels, raw quotes, or human trace strings for behavior, that violates the firewall.

Godot scene/autoload mismatch:

_mrlore does not own Godot autoloads. Any Godot issue that claims _mrlore authority is a boundary error. _mrlore can supply contracts; Godot must consume them.

Generated-output drift:

Tier audit shows generated `_work` outputs, ZONJ files, `.metta` files, and parser artifacts living near source material. These can drift from Tier 0 and must never outrank raw chapter prose.

Old architecture still present:

The audit still references `/home/mytruelove/Downloads/obsidianburdenNov25`, while current project memory says the active EngAIn root has moved away from Downloads. That is a serious path-authority smell. Keep _mrlore, but relocate or re-root cleanly before trusting automation deeper.

## 4. CONTRADICTION PROFILE

Contradictions against own role:

If _mrlore is called “canon authority” and then allowed to edit canon prose, that contradicts its own contract. It may judge and stage, but Tier 0 prose remains protected.

If _mrlore outputs runtime behavior directly instead of neutral contracts, that contradicts the semantic firewall.

Contradictions against other projects:

Trae may propose changes, but is explicitly not canon authority. If Trae resolves canon conflicts or modifies Tier 0 prose, it violates the lane.

engainos executes state and AP authority. It should not decide canon truth.

mettaext may consume structured knowledge, but it should not promote raw extraction into canon.

Current home/project decision contradictions:

The stack still references Downloads paths. Your current doctrine says not to use Downloads as the working root. So the audit is historically useful, but path authority should be refreshed in the active repo root before deeper trust.

File naming contradictions:

`23_beyond_identity.md` lacks zero-padding unlike surrounding chapter files.

Several words are misspelled or variant-named: `sacrafice`, `ummade`, `hier`, `convergance`, `defered`, `unravealing`, `farwell`. These may be canon filenames, typos, or legacy drift. They should not be auto-normalized.

Schema name contradictions:

`ARTIFACT_SCHEMA` is Pass 1 and forbids classification; `CHAPTER_LEDGER_SCHEMA` is Pass 2/3 and permits object classes. If a tool writes ledger fields into artifacts, the schema boundary is broken.

Old vs new pipeline behavior:

Older generated `out_pass1`, `out_pass2`, `.metta`, and ZONJ outputs appear in tier audits. The new rule is manifest-gated, audit-only, source-truth anchored, and human-reviewed before promotion. Any older direct-ingest behavior should be treated as legacy evidence, not authority.

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

Proposed system: **Semantic Translation Buffer / Canon Firewall**

Implied by: `SEMANTIC_BUFFER_SCHEMA.md`, `ARTIFACT_SCHEMA.md`, `CHAPTER_LEDGER_SCHEMA.md`.

Missing before real: complete scanner, validation, review application, promotion gate, immutable archive, and deterministic replay.

Proposed system: **Relationship Graph Governance**

Implied by: `RELATIONSHIP_PREDICATES.md`, `RELATIONSHIP_PHRASE_REGISTRY.md`.

Missing before real: edge storage, provenance verification, temporal anchoring, conflict handling, and promotion into official codex graph.

Proposed system: **Identity Resolution Review Loop**

Implied by: `identity_review_queue.md`, `identity_review_queue.jsonl`, `human_identity_reviews.jsonl`.

Missing before real: human decisions applied to collapse ambiguous candidates, generate canonical entity IDs, and update downstream entity contracts.

Proposed system: **Semantic Scene Cut 1 / Region Matrix**

Implied by: `SEMANTIC_SCENE_CONTRACT.md`, `scene.proof.001.json`.

Missing before real: exporter from canon/ledger into scene regions, validation against full chapter scenes, and consumer-side proof in trixel/Godot.

Proposed system: **Semantic Entity Cut 2 / Entity Passport**

Implied by: `SEMANTIC_ENTITY_CONTRACT.md`, `entity.proof.001.json`.

Missing before real: canonical entity ID map, archetype assignment authority, faction role rules, spawn rules, and proof that runtime ignores provenance.

Proposed system: **CocoIndex Changed-File Sensor**

Implied by: `coco_flow.py`, `collect_delta.py`.

Missing before real: full vault source root coverage, active-root path correction, repeated change detection tests, and integration with `write_changed_manifest.py`.

## 6. INBOUND SCHEMA

Raw chapters

Source project: vault / canon prose source.

Expected filename/schema: `book_##/.../*.md` or `.txt`, treated as Tier 0 when listed in tier audit.

Required fields: actual file path, chapter text, stable chapter number/name, source hash or equivalent.

Optional fields: book title, arc labels, line offsets if precomputed.

Failure behavior: missing file becomes `[NOT FOUND]`; unresolvable span becomes low confidence; low confidence triggers EXIT 2.

Changed-file manifests

Source project: CocoIndex / cocowatch / manifest tooling.

Expected filename/schema: `raw/cocoindex_delta.txt`, then `raw/changed_files.txt`.

Required fields: vault-relative changed source paths, deduped and stable sorted.

Optional fields: generated timestamp, count, source label.

Failure behavior: no changed files returns clean no-op; malformed paths should stop before ingest.

Review decisions

Source project: human canon reviewer.

Expected filename/schema: `human_identity_reviews.jsonl`, canon decision records, resolved `CONT-*.yaml`.

Required fields: surface form or candidate ID, reviewer decision, target canonical entity or rejection/defer status, reviewer notes, timestamp.

Optional fields: confidence, merge/split rationale, affected chapters, aliases.

Failure behavior: pending records remain pending; ambiguous identity cannot promote.

Trae/MrLore run outputs

Source project: Trae and MrLore tooling.

Expected filename/schema: `run_*.md`, `continuity_audit_*.md`, chapter ledger reports, failure YAML.

Required fields: sources attempted, ingested OK, skipped by tier, lint status, continuity status, exit code.

Optional fields: missing file list, open CONT count, registry rebuild status.

Failure behavior: EXIT 1 means mechanical/tooling halt; EXIT 2 means successful safety stop requiring human review.

## 7. OUTBOUND SCHEMA

To mettaext

Expected filename/schema: candidate `.metta` exports or structured relationship/entity facts.

Required fields: canonical entity IDs, predicates, source provenance IDs, temporal scope, authority score or review status.

Optional fields: aliases, confidence warnings, relation qualifiers.

Stability level: candidate.

To engainos

Expected filename/schema: prose-free semantic contracts.

Required fields: scene/entity IDs, controlled enums, capabilities, topology, traversal, surface/material primitives, runtime_safe validation.

Optional fields: render hints, placeholder shell, spawn coordinates.

Stability level: candidate / proof-only until full export is tested.

To canon reviewers

Expected filename/schema: `identity_review_queue.md/jsonl`, `CONT-*.yaml`, ledger pending files, run reports.

Required fields: candidate type, evidence spans, conflict axis, confidence, source files, review status.

Optional fields: co-occurring tokens, score details, proposal availability.

Stability level: stable as review artifact, not stable as canon truth.

To semantic contract consumers

Expected filename/schema: `semantic_scene_contract_cut_1`, `semantic_entity_contract_cut_2`.

Required fields for scene: `contract_version`, `contract_type`, `scene.id`, `scene.scale`, `regions`, `validation.runtime_safe`.

Required fields for entity: `contract_version`, `contract_type`, `entities`, `entity_id`, controlled archetype/capabilities/shell/resolution, validation.

Optional fields: provenance, render hints, authority score.

Stability level: candidate / proof-only.

## 8. AUTHORITY BOUNDARIES

_mrlore must stop and ask another project when:

It needs runtime behavior, AP mutation, world-state execution, Godot scene structure, rendering interpretation, animation, combat, or UI.

It detects a canon contradiction that requires author intent.

It sees identity braid / ambiguous entity / bounded actor candidates.

It sees relationship edges without explicit Tier 0 or resolved canon backing.

It sees low-confidence extraction, unresolvable source spans, canon-breaking contradiction candidates, or world-state descriptors conflicting with active canon.

Another project must stop and ask _mrlore when:

It wants to consume canon as data.

It wants to promote generated summaries into lore truth.

It wants canonical entity IDs, aliases, relationship predicates, timeline anchors, or faction memberships.

It wants to pass prose-derived payloads into engainos/Godot/trixel runtime.

It wants to decide whether a contradiction is safe, blocked, cosmetic, structural, or canon-breaking.

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Is the active _mrlore root still under Downloads, or must all authority paths be re-rooted into the current EngAIn workspace?

2. Are the 123/135/139 chapter counts representing different snapshots, or is one the current canon count?

3. Should Book 13 remain void/removed in public continuity while retained as conspiracy/game-only material?

4. Which Tier 1 files should be migrated into `wiki/` as canon support, and which should remain historical notes?

5. Which Tier 3 files are promotable, especially character lore, chapter lore, and old generated pass outputs?

6. What is the canonical rule for identity braids: when is a name one actor, a collective actor, a title, a force, or a surface-term artifact?

7. How should `Nephoretti / Nefretti / Nehereti` variants resolve?

8. Should `Luminaire` and `Luminara` remain separate, alias-linked, or canonically unified?

9. Should relationship predicates be limited to the current small set, or expanded before mettaext consumes graph edges?

10. What exact event should happen on EXIT 2: pause only, write pending ledger, open review ticket, notify human, or block all downstream exports?

## 10. STACK VERDICT

**AUTHORITY_WITH_FIX_FLAGS**

Why: _mrlore has the right constitution. Tier 0 is protected. Extraction is audit-only. Low-confidence and canon-breaking items trigger EXIT 2. Identity and relationship systems are review-gated. Semantic scene/entity contracts are correctly prose-free. Changed-file collection is atomic and manifest-oriented.

But it is not fully `AUTHORITY_READY` yet because the stack still has unresolved identity queues, candidate schemas, proof-only semantic contracts, known missing legacy paths, duplicate generated outputs, and active-root uncertainty. The system is strong enough to be the canon/lore review authority, but deeper trust requires human decisions and path cleanup first.
