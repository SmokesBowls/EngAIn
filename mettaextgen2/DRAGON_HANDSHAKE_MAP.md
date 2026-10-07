# Dragon Handshake Map — the first real Mettaext → Godot path

Status: OBSERVED RECORD, 2026-10-06. This traces the first Dragon-initiated
build (2026-09-20, `dragonreq_20260920_173218_ca8151c2`), from git history,
the coordination mailboxes, the EngAIn session journal and the audit repo.
Nothing was run to produce it. It **describes** an existing seam. It does
not redesign the Dragon.

Primary audit record: `/mnt/data-drive/engain-avatar-audit/full audit/09-20-2026-first-dragon-initiated-build-traced.md`
(audit repo commit `83a5732`). Times below are PDT.

## 1. The path as it actually ran

| # | Step | Producer → consumer | Artifact / route | Evidence |
|---|---|---|---|---|
| 0 | Evidence read, **night before** (09-19 ~21:20) | Dragon request `dragonreq_20260920_041635_a5559b0a` (read-only) → Editor agent → **`engain_door.py`** subprocesses (`status`, then many `query`) | Door reads stageroom files directly (no HTTP). `--source …/book_01_book_of_genesis/003_first_contact.md`, `ENGAIN_ROOT=…/EngAIn` | `coordination/outbox_handled/…041635…json`; `consumed/editor_report.20260919_212058_2061.attempt0.json` |
| 1 | Human prompt | Player → Godot runtime ("…build the first scene… lets see where we crash") | client request `dragon3d_216d775f…_1` | EngAIn session journal `runtime/sessions/5b5fd1f5…bdba2e.journal` (~#151); `snapshots/perception_cap_702e95b2…_1.json` |
| 2 | Turn routed | `hermes_session_adapter.py` → EngAIn `POST /dispatch` on `127.0.0.1:8767` → Hermes model | presence authority server | `engain_continuity_client.py:36,170`; adapter `:2494-2524`; `tier1/engainos/server/presence_authority_server.py` |
| 3 | Build request written | Dragon reply's `[EDITOR_REQUEST]` block → mailbox | `coordination/outbox/dragonreq_20260920_173218_ca8151c2.json`, schema **`engain.dragon_request.v1`** (`message_id, parent_message_id, source, destination, body, created_at`). **Body is free prose** | adapter `_extract_editor_directive :2177-2214`, `_publish_dragon_directive :2146-2175` |
| 4 | Human gate | Editor dock lists the request → **human clicks "Execute (DIRECT_WRITE)"** → `hermes chat … -q "<body>"` | request moved to `outbox_handled/` | `addons/hermes_editor/hermes_bridge.gd:748-810`, `hermes_dock.gd:556-636` |
| 5 | Build | Editor Hermes agent, using its own file-write/patch tools | new `.tscn`, `.gd`, `WorldComposition.tscn` edit | report diffs; no MCP, no Godot editor API |
| 6 | Load check | bridge → headless Godot `coordination_report_validator.gd` (load + instantiate) | **`engain.editor_report.v1`** `consumed/editor_report.20260920_104544_ffe7.attempt0.json` | `hermes_bridge.gd:851-902` |
| 7 | Result back to Dragon | report → `/dispatch` as `coordination_report` | `tool_events_handled/event_01789926344572195872_6873d451.json` | adapter `:1841-1915` |
| 8 | Commit | a Claude session (not Dragon) | `bf5d182` | git |

All coordination paths are under `/mnt/data-drive/engain-runtime-mailboxes/dragon3d/coordination/`.

## 2. The Mettaext seam: `engain_door.py`

The only point where Mettaext evidence entered this path is the **door**:
`/mnt/data-drive/godot_engain_3d_avatar/engain_door.py`. It is a standalone
CLI that the Dragon's bridge calls as a subprocess. Its interface was frozen
**before** implementation in
`full audit/09-15-2026-engain-door-contract-v1.md`, with amendments for
fail-closed stem collision (09-15) and authored-boundary provenance (09-19).

- **CLI:** `status | ingest | query --source <abs chapter path> [--query <text>]`. `ingest` is explicit only; `query` never ingests.
- **stdout:** exactly one JSON document, with `"authority": "evidence_only"` on every reply.
- **What `query` reads (door v1):**
  - lane A: `passroom/<scene_id>/out_pass1_<scene_id>.txt`, narration and dialogue lines only;
  - lane B: `passroom/<scene_id>/<scene_id>.zonj.json` → `=entities_observed`, returning only `name, known, spawnable, classification, mentions` (`engain_door.py:396-423`).
- **What `status` reads:** `chapterroom/scene_packets/<chapter>/scene_packets_index.json`.

**Fields the build actually relied on:** `chapter_id` and `scene_id`
(Chapterroom form, `scene.book001.003_first_contact.scene001`), the scene
heading, the five raw `scene meta:` lines, narration lines, and per-entity
`known/spawnable/classification/mentions`.

**Never consumed:** `presence`, `physicality`, `@entities_manifested`,
`environment`, and the boundary-proof fields. The door version used predates
the 09-19 provenance amendment (Dragon-repo commit `1e4084d`).

## 3. What the proof establishes, stated precisely

- **Presence semantics were obeyed, but not by contract.** The scene
  instantiated present entities only (about 200 Nephoretti as a MultiMesh,
  plus one provisional Senareth). It withheld the Giants, the Aeon Keeper and
  the named Vairis/Elyraen/Olythae. That rule lives **only in the prose
  request body**, which the Dragon's model wrote from the door evidence. It is
  not in the packet: the zonj marks every observed entity `presence` `local` or
  `unknown`. It is not in any Dragon code either.
  The operational rule demonstrated is:
  ```
  PRESENT     → may instantiate
  REFERENCED  → do not instantiate
  UNRESOLVED  → do not instantiate
  ```
  Gen2's `presence` field would be the **first time this distinction is
  carried as data** rather than inferred by a model at build time.
- **The evidence was noisy in the way Gen2 exists to fix.** The same zonj's
  `=entities_observed` lists `Tomorrow` and `someone` beside the real names:
  the capitalised-word failure, in the evidence the Dragon consumed. The
  model compensated.
- **EngAInOS validated nothing evidence- or authority-related on this
  path.** `/dispatch` handled session/presence bookkeeping and relayed the
  report as prompt text. The only gates were Godot-side: the request-shape
  check, a **human Execute click**, and a headless load/instantiate check.
- **Provenance is a label, not a link.** The scene root records
  `source_authority = "Mettaext evidence_only"` and
  `source_packet_id = "scene.book001.003_first_contact.scene001"`, but no
  hash or version. Stageroom was regenerated at 10:01 on 09-20, after the
  night-before reads and before the build. What the Dragon cited is therefore
  not byte-proven to match what is on disk; the current index now says
  `SCENE_BOUNDARY_AUTHORED`, while the scene says
  `authored_boundary_status = "unknown"`.

## 4. Implications for Gen2 (preserve and version; do not invent)

1. **The Gen2 → Dragon handshake is the door.** Gen2 replaces the passroom
   outputs the door reads (`out_pass1_*.txt`, `*.zonj.json`). The seam should
   be **versioned**, as a door contract amendment or v2 that adds a lane
   reading `mettaext.parse_artifact.v2`. It should not be replaced. The CLI
   shape, the one-JSON stdout, `"authority": "evidence_only"`, explicit-only
   `ingest`, and fail-closed errors are kept as they are.
2. **Field mapping the door v2 lane would need** (proposal):

   | door v1 field (legacy zonj) | Gen2 v2 source |
   |---|---|
   | `name` | `declared_entities[].surface` (+ `local_ref`) |
   | `known` | `status == KNOWN` |
   | `classification` | `entity_type` + `status` |
   | `mentions` | count of spans / coref chain |
   | `spawnable` | **not emitted by Gen2.** Spawnability is a GodotSim/EngAInOS decision. Replace it with `presence` + `physicality_evidence`, the fields the Dragon actually needed |
   | *(missing)* | `presence` (present / referenced / absent / unknown), `alternatives[]`, `source_span`, `source_sha256`, scene block (§5a of the output contract) |

3. **Provenance should travel to the scene.** A door v2 reply carries
   `source_sha256` and the artifact id, so a built scene can record a hash
   and not just a label. That is a small Dragon-side metadata addition, and it
   needs approval in the Dragon repo.
4. **Open governance question.** Under
   `ENGAINOS_EVIDENCE_ADMISSION_CONTRACT_v1` (Proposed), lanes interpret
   **admitted** evidence. The door currently serves stageroom output with no
   intake admission. It is "evidence_only", but unadmitted. Either the door
   reads only admitted artifacts, or the human Execute click is recognised as
   the admission act for this path. That is a ruling, not a Gen2 decision.
5. **Corpus candidate (cross-book).** `Tomorrow` and `someone` in Book 01
   chapter 003, scene 001, would be a natural `B01-34` case: a capitalised
   temporal word and an indefinite pronoun emitted as entities. It is not added
   yet; it needs the Book 01 source pinned.

## 5. Loose ends noted by the trace

- The audit's claim that the "two unaccounted files" were ruled out is wrong.
  They are a 10:36 runtime perception capture (`perception_cap_44694dd…_3.*`)
  from a different turn.
- The scratch verifier `/mnt/data-drive/EngAIn_Recovery/07_TMP/hermes-verify-0wz2i1fa.py`
  is still on disk. Its "run then delete" command timed out at the approval
  prompt rather than being refused by a rule.
- Headless Godot was launched for validation, although the request said not to run Godot.
- Runtime and visual loading of the built scene was never verified.
- The Editor's Hermes tool-call log for the build turn (possibly in
  `~/.hermes/state.db`) was not opened.
