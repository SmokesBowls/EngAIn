# Mettaext Gen2 — Output Contract (`mettaext.parse_artifact.v2`)

Status: DRAFT, 2026-10-06. Derived from the existing contracts listed in §1;
§5 records the rulings. Module-level interfaces are in `GEN2_MODULES.md`.

> **Producer describes. Consumer interprets.**
> Gen2 emits evidence. Every interpretation into a lane's own truth
> (topology links, affect states, terrain profiles, coordinates, canon
> status, canonical identity) belongs to that lane's authority and is
> forbidden in a Gen2 artifact.

## 1. Sources of truth used

| Doc | What it fixes for Gen2 |
|---|---|
| `docs/contracts/METTAEXT_TIER3_EXTRACTION_MANAGEMENT/METTAEXT_TIER3_PARSE_AUTHORITY_CONTRACT_v1.md` | The governing lane contract: `mettaext.parse_artifact.v1`, hard rejects, permitted and forbidden statements |
| `docs/contracts/METTAEXT_TIER3_EXTRACTION_MANAGEMENT/mettaext_3rdlane_parse_proposals/LANE_INSTRUCTIONS.md` | "Parse power, not world power" |
| `docs/architecture/TIER2_PRODUCTION_MAP.md` | What each Tier 2 system produces and consumes |
| `docs/contracts/README_TIER_VS_LANE.md` | Lane ownership (trixelmap owns terrain intent; Engionality owns affect state) |
| `docs/contracts/GODOTSIM_TIER2_AUTHORITY/GODOTSIM_TIER2_SPATIAL_SIM_CONTRACT_v1.md` | Mettaext declares → EngAInOS validates → GodotSim simulates |
| `docs/contracts/ENGIONALITY_TIER2_AUTHORITY/ENGIONALITY_TIER2_AFFECT_AUTHORITY_CONTRACT_v1.md` | `affect_state` is Engionality-owned |
| `docs/contracts/MRLORE_TIER1_AUTHORITY/MRLORE_TIER1_CANON_REVIEW_CONTRACT_v1.md` | MrLore produces canon-review claims and contradictions |
| `docs/contracts/MRLORE_NARRATIVE_CONCURRENCE_CONTRACT_v1.md` | Concurrence needs the `source_prose` behind spatial truth |
| `tier3/mettaext/chapterroom/` (Pass A/B), `tier1/engainos/validators/runtime_stage_identity.py`, `tier1/engainos/tools/chapter_splitter/promote_stage_draft.py` | Scene identity: Chapterroom scene ids and runtime-stage ids (§5a). The older `tier3/mettaext/scene_identity.py` is a legacy alias/canonicaliser and is not the identity source |

Gen2 is a new implementation of the existing Mettaext Tier-3 lane. It does
not create a new lane, and it inherits that lane's authority boundary
unchanged.

## 2. Versioning — RULED

- `mettaext.parse_artifact.v1` stays **unchanged** for the legacy pipeline.
- Gen2 targets **`mettaext.parse_artifact.v2`**. The change is semantic, not
  just shape: v2 adds status, presence, alternatives, scoped aliases and
  unresolved states.
- The v2 contract file belongs in
  `docs/contracts/METTAEXT_TIER3_EXTRACTION_MANAGEMENT/` once accepted. Until
  then this document is its draft.

## 3. What Gen2 makes

A **governed evidence artifact**. It is not a Godot scene, not Topologist
links, not Engionality states and not WorldField classifications. It contains
what downstream authorities need for their own interpretation: entity
handles, presence, physicality evidence, aliases and alias candidates,
events, dialogue and speaker evidence, temporal, spatial, distance, affect
and terrain cues, metadata constraints, uncertainty and alternatives,
provenance, and confidence.

### 3.1 Allowed vs. forbidden assertions (the lane line)

| Domain | Gen2 MAY emit | Gen2 MUST NOT emit | Owner of the interpretation |
|---|---|---|---|
| Identity | `local_ref` handles, alias **candidates** with scope | canonical entity ids, global alias commits | EngAInOS (registry) |
| Scene | `source_scene_label`; the Chapterroom scene id **inherited** from the input packet | any minted or derived scene id; `runtime_stage_id` (set only at EngAInOS promotion) | Chapterroom (proposal), EngAInOS (runtime stage) |
| Spatial | `SPATIAL_SIGNAL` (subject, relation phrase, object, frame hint) | RCC-8 / QSLINK / OLINK / MOVELINK interpretation | Topologist |
| Distance | `DISTANCE_CUE` (text, approximate) | metric coordinates, extents | Topologist → Cartographer |
| Placement | presence evidence (present / referenced / absent) | `position`, `velocity`, `collision`, spawn | GodotSim |
| Affect | `AFFECT_CUE` (entity_ref, cue text) | `AFFECT_STATE`, intensity, relationship deltas | Engionality |
| Terrain | `TERRAIN_DESCRIPTION` | `TERRAIN_PROFILE`, `environment_type`, region contracts | trixelmap / WorldField |
| Time | `TEMPORAL_CUE`, discourse order, backstory/recalled flags | temporal-law verdicts | Paradox Machine |
| Canon | continuity flags, alias candidates (as material for contradictions) | `canon_claims` (must be `[]`), canon status | MrLore (advising EngAInOS) |
| Permission | confidence as **proposal strength** | `allowed`, `ap_allowed`, `canon`, confidence-as-truth | EngAInOS |

Every v1 hard reject (parse contract §6) remains a hard reject in v2.

### 3.2 Proven consumer: the 3D Dragon

`/mnt/data-drive/godot_engain_3d_avatar` (Hermes Dragon + Editor) consumed
Mettaext evidence in a real build on 2026-09-20 (Genesis 003.1, commit
`bf5d182`). It reached that evidence only through **`engain_door.py`**,
whose interface is frozen in `engain-avatar-audit/full audit/09-15-2026-engain-door-contract-v1.md`
(`"authority": "evidence_only"`).

- **Gen2 must preserve:** scene identity in Chapterroom form, raw scene-meta
  lines, narration and dialogue, per-entity status, and **presence**. The
  Dragon needed presence and had to infer it from prose, because the legacy
  packet marked every entity `local`/`unknown`.
- **Gen2 does not change the Dragon.** The door is the seam to **version**
  (a v2 lane reading `parse_artifact.v2`), not replace.

Full trace, field mapping and open questions: `DRAGON_HANDSHAKE_MAP.md`.

## 4. Envelope (`mettaext.parse_artifact.v2`)

```
contract              "mettaext.parse_artifact.v2"
source                "mettaext"
authority_lane        "prose_to_structure"
authority_tier        3
source_text_id        REQUIRED  (e.g. "B09:048_the_ledger_born.md@<sha256>")
source_sha256         REQUIRED
parse_stage           REQUIRED  ("gen2")
scene                 { see §5a: source_scene_label, chapterroom_scene_id (inherited),
                        chapter_id, boundary_method, authored_scene_boundaries_proven,
                        runtime_stage_id: null }
run                   { run_id, modules: [{name, version, implementation_kind}] }
declared_entities[]   { local_ref, surface, entity_type, status, presence,
                        physicality_evidence?, evidence_class, source_span,
                        confidence, alternatives[] }
declared_locations[]  { local_ref, surface, status, evidence_class, source_span,
                        confidence, alternatives[] }
declared_events[]     { local_ref, actor_ref, action, target_ref?, object_ref?,
                        voice (active|passive), temporal_frame (scene|backstory|recalled),
                        source_span, confidence, alternatives[] }
alias_candidates[]    { surface, candidate_ref, scope (span|scene|chapter|arc|global),
                        status, evidence[], confidence }
speech[]              { kind (dialogue|recalled|inner), speaker_ref?, source_span, confidence }
spatial_signals[]     { subject_ref, relation_phrase, object_ref, frame_hint?,
                        source_span, confidence, alternatives[] }
distance_cues[]       { text, subject_ref?, object_ref?, axis_hint?, source_span, confidence }
temporal_cues[]       { text, cue_type, anchor_hint?, source_span, confidence }
affect_cues[]         { entity_ref, cue_text, source_span, confidence }
terrain_descriptions[]{ text, source_span, confidence }
metadata_constraints[]{ kind (assertion|presence_qualifier|editorial_placement|
                        unresolved_state|non_inference), subject?, text, source_span }
continuity_flags[]    { subject_ref, issue, source_spans[] }
challenges[]          { by_module, target_annotation, reason, outcome }
warnings[]
canon_claims          []   # MUST be empty
```

**`source_span`** (required on every declaration, cue and constraint):
`{ source_text_id, file, line, char_start, char_end, text }`. Offsets
always index the **raw** source, never normalised text.

**Handles.** `local_ref` values are run-local (`candidate_A`, `loc_3`). They
mean nothing outside the run. v1's `entity_id` / `location_id` are proposal
handles in the same sense ("names become handles", parse contract §11).

## 5. Rulings (2026-10-06)

1. **v2, not mutated v1.** See §2.
2. **Flow: Mettaext → EngAInOS, and EngAInOS consults MrLore.**
   ```
   Book + Metta → Mettaext Gen2 → parse_artifact.v2 → EngAInOS
                                                       ├─ consult MrLore (advisory)
                                                       ├─ ACCEPT
                                                       ├─ REJECT
                                                       └─ HOLD
   ```
   MrLore advises on canon and lore and is not a gate between extraction and
   governance. **Reconciled:** `MRLORE_TIER1_CANON_REVIEW_CONTRACT_v2.md`
   (Proposed) adopts this flow, and v1 carries a supersession notice on its
   §10. MrLore keeps canon/lore authority in its own lane (First Amendment);
   its findings are input to EngAInOS verdicts, never the verdicts.
3. **Gen2 inherits scene identity; it never mints it** *(corrected
   2026-10-06; the first version wrongly claimed sub-scene identity did not
   exist).* Gen2's input is Chapterroom's scene packets: "ABC provides scene
   packets; Pass 1–5 compiles scene packets", and Gen2 replaces the compiler.
   Scene identity arrives with the input, and Gen2 carries it through
   unchanged. The three identity forms are separate and are never collapsed
   into one. See §5a.
4. **Affect cues allowed as evidence; affect state forbidden.** The same
   principle applies to terrain (description allowed, profile forbidden) and to
   space (signal allowed, link interpretation forbidden). See §3.1.
5. **Two EngAInOS gates.** Intake **admits** a v2 artifact as
   `ADMITTED_EVIDENCE` (contract, provenance and lane checks only; ADMIT /
   HOLD / REJECT). Lane authorities interpret admitted evidence. Final
   verification turns their derived output into `ACCEPTED_DERIVED_TRUTH`
   (ACCEPT / REJECT / HOLD / CONFLICT). `ADMITTED_EVIDENCE ≠
   ACCEPTED_DERIVED_TRUTH`. Defined in
   `docs/contracts/ENGAINOS_TIER1_AUTHORITY/ENGAINOS_EVIDENCE_ADMISSION_CONTRACT_v1.md`
   (Proposed).

## 5a. Scene identity: three forms, linked, never collapsed

| Form | Example | Produced by | Status | Contract / code |
|---|---|---|---|---|
| **Manuscript label** | `048.5` | the author (`### scene 048.5 — …`, yaml `scene:`) | source text | — |
| **Chapterroom scene id** | `scene.book009.048_the_ledger_born.scene005` | Mettaext Chapterroom Pass A (`chapter.<bookNNN.>NNN_<slug>`) + Pass B (`build_scene_id`: `scene.<chapter minus "chapter.">.sceneNNN`) | proposal; carries `boundary_method`, `authored_scene_boundaries_proven` | `engain.scene_boundary_proposal.v1`; `tier3/mettaext/chapterroom/passA_chapter_intake.py:82`, `passB_scene_boundary_provider.py:23` |
| **Runtime-stage id** | `scene.book009.chapter048.stage005` (+ `book.009`, `chapter.048_<slug>`, `stage.book009.chapter048.slice005`, `source.book009.chapter048.slice005`) | EngAInOS promotion: operator supplies book/chapter/**stage** and `--accepted-by` | `ACCEPTED_RUNTIME_STAGE` | `engain.runtime_stage_packet.v1`; `tier1/engainos/tools/chapter_splitter/promote_stage_draft.py:76`, `tier1/engainos/validators/runtime_stage_identity.py` |

**How they link (the only links any code or contract establishes):**
- Label → Chapterroom id: **stored since 2026-10-06** (`source_scene_label` on Pass B/C entries); before that there was no stored link. Pass B numbers scenes by
  sequential index (`enumerate(chunks, start=1)`) and does not store the
  marker's own number on the scene entry; it survives only in the scene
  text's first line. `048.5 → scene005` holds only when a chapter's markers
  run 1..n without gaps. Gen2 must therefore record `source_scene_label` next
  to the inherited Chapterroom id, and never derive either from the other.
- Chapterroom id → runtime-stage id: **provenance link only.** Promotion
  records `promoted_from_scene_id` and `promoted_from_source_packet_id`. The
  stage number is operator-supplied, and no contract says it equals `sceneNNN`.
- The live SceneLoader loads by **Chapterroom id** (`StageroomSceneResolver`,
  commit `828ab2f1`), and the 3D Dragon cited a Chapterroom id as its
  `source_packet_id`. Both forms are therefore live at runtime level.

**v2 `scene` block:**
```
scene { source_scene_label:   "048.5" | null          # from the source text
        chapterroom_scene_id: "<inherited from input packet>"   # with source_scene_label also inherited from Pass B/C
        chapter_id:           "<inherited>"
        boundary_method:      "<inherited, as-is>"
        authored_scene_boundaries_proven: <inherited, as-is>
        runtime_stage_id:     null }                   # set only by EngAInOS promotion
```

**Chapterroom compatibility update (2026-10-06, done):**
1. **Book 09 format is now recognised.** Pass B accepts heading-prefixed
   markers (`### scene 048.5 — …`) and fenced ```` ```yaml ```` metadata in
   both observed layouts (nested `scene meta:`; top-level keys, with nested
   mappings flattened to dotted keys). Values are read with PyYAML
   `BaseLoader`, so they stay opaque strings exactly as written and `time:`
   is never coerced (09-19 rule 3). Verified in memory: chapter 048 gives 5
   authored scenes (`048.1`–`048.5`; `048.5` starts at line 467) and chapter
   050 gives 10 (corrected from an earlier miscount of 8). Book 01's plain format is unchanged.
2. **The label↔index link is now stored.** Pass B scene entries and the Pass C
   index carry `source_scene_label` and `source_scene_title` (additive), plus
   `scene_meta_format` / `scene_meta_error`. A broken metadata block keeps the
   authored boundary and reports why.
   Code: `tier3/mettaext/chapterroom/passB_scene_boundary_provider.py`,
   `passC_scene_packet_writer.py`. Tests:
   `tier3/mettaext/tests/test_authored_scene_markers_fenced_yaml.py` (17 new)
   plus the existing 09-19 suite (14), all passing. Stageroom outputs were
   **not** regenerated.

**`authored_scene_boundaries_proven` — ruled 2026-10-06: kept `true` for
author-written markers.** It is a **source fact**: explicit authored markers
were found and used for segmentation. It does not imply EngAInOS admission, an
accepted runtime stage, or canon promotion. `CHAPTERROOM_AUTHORITY_NOTE.md`
was updated to match the 09-19 design; its old "must remain false" wording is
marked superseded.

## 6. Still open

- **Metadata layout varies by chapter.** `048.5` nests under `scene meta:`;
  `050.4` uses top-level `scene`, `state ledger`, `continuity flags`. Gen2's
  `metadata_reader` tolerates both. Standardising the layout is a manuscript-
  workflow decision.
- **Tier label inconsistency** (flag only). The parse contract §10 lists
  MrLore as TIER3; its folder is `MRLORE_TIER1_AUTHORITY`.
- **Where downstream adapters live** (see `GEN2_MODULES.md` §4).
- **MrLore tier value** (3 in v1 and the code, 1 in its lane instructions) and
  the **identity split** (MrLore owns canon "character identity", EngAInOS
  owns declared entity truth and mints ids). Both are recorded as open in
  MrLore contract v2 §5.

## 7. Corpus coverage

The corpus is `corpus/gen2_hard_passages_v1.json`, with 33 cases. It tests
whether Gen2 produces a valid v2 artifact **without taking authority from
downstream lanes**. It does not test whether Gen2 "understands the book".
Contract rules that apply to every case are in `global_expected_non_results`.

| Requirement | Cases |
|---|---|
| Entity declaration / capitalised non-entities rejected | 01, 05, 06, 08, 09, 10, 20, 24, 29, 30, 31 |
| Locations, negated locations, location aliases | 01, 10, 17, 27, 32 |
| Events: actor / action / target; passive voice | 03, 18, 19, 20; 31, 32, 33 |
| Scoped alias candidates | 07, 11, 12, 13, 16, 25, 29 |
| Presence vs. reference | 01, 02, 06, 28, 29 |
| Scene labels / local scene refs (no invented id) | 01, 29 |
| Spatial signals incl. frame hints | 02, 15, 30, 31, 33 |
| Distance cues | 14, 16, 29, 30, 31 |
| Movement / negated movement | 02, 14, 16, 29, 31 |
| Temporal cues / backstory / recalled | 01, 07, 23, 32 |
| Affect cues, no affect state | 15, 16 |
| Terrain descriptions, no terrain profile | 07, 27 |
| Author metadata as structured evidence (two layouts) | 28, 29 |
| Continuity flags | 22 |

Affect and terrain are thin (two cases each), and no case covers a
cross-book alias. Cases are added when a source supplies a natural example,
never invented to fill the table.
