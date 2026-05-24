This classification draft is exactly what the contract needed: it turns “editor-only” from a vibe into a machine-checkable vocabulary. It is coherent with the existing embodiment contract and safe to adopt as the next-layer law over Trixel editor outputs. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

Here’s how it lands and what I’d do next.

***

## What this document actually does

You’ve just defined a **unified JSON wrapper ABI** for all Trixel editor and AI artifacts:

- A single, shared **header** (`schema_version`, `authority_level`, `authoritative`, `artifact_kind`, `source`, `base_*`, `deterministic_seed`, `status`).  
- File-level **classifications** for `.zw/memory.json`, `.zw/snapshots.json`, `.zw/experience_log.jsonl`, `.zw/sessions/*.json`, and AI bridge payloads.  
- A **promotion rule** that forces anything crossing into runtime to pass through the embodiment contract, not side channels.  
- A **runtime rejection rule** that gives code a trivial “no” path: if `authority_level == "editor_only"` and `authoritative == false`, runtime treats the object as data, not canon. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

This squarely closes the ambiguity you found earlier in `terminal_trixel.py` where memory, snapshots, and sessions *behaved* like editor artifacts but didn’t say so in their schema. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

***

## Fit with TRIXEL_EMBODIMENT_CONTRACT_v1

This doc behaves like a **child contract**:

- Parent: `docs/TRIXEL_EMBODIMENT_CONTRACT_v1.md` defines the embodiment ABI and runtime authority.  
- Child: `TRIXEL EDITOR OUTPUT CLASSIFICATION v1` defines the semantics for all artifacts that live *outside* that ABI: editor memory, canvas snapshots, replay logs, AI payloads. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

The one-line rule here:

> Every Trixel editor or AI artifact must declare itself editor-only and non-authoritative unless it has been explicitly validated and promoted…

is perfectly aligned with the earlier core law:

> No Trixel editor, AI bridge, or PixiEditor integration may mutate or redefine runtime embodiment directly. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

The new doc simply operationalizes that: it gives you the exact JSON knobs that make “editor-only” a parseable state rather than tribal knowledge.

***

## Strong parts that should stay exactly as written

These are the most important bits to lock in as-is:

- **Common header fields** and their null policy:
  - Always present `base_contract_version`, `base_scene_id`, `base_contract_digest`, even when `null`.  
  - Always present `deterministic_seed`, or explicitly mark `status: "non_deterministic"`.  
  - Always enforce `authority_level: "editor_only"` and `authoritative: false` for every artifact governed here. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

- **Artifact kinds table** — this is a clean taxonomy:
  - `editor_memory`, `editor_canvas_snapshot`, `editor_replay_event`, `editor_replay_log`, `editor_session`, `ai_bridge_payload`, `ai_suggestion`, `editor_action`, `editor_artifact`.  
  - And the rule: unknown `artifact_kind` must be rejected by any consumer that is connected to runtime embodiment. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

- **File-specific shapes**:
  - `.zw/memory.json` has a `memory` object under the wrapper.  
  - `.zw/snapshots.json` has `snapshots: [ { … } ]` with per-snapshot metadata.  
  - `.zw/experience_log.jsonl` uses one JSON line per `editor_replay_event` with embedded `editor_action`.  
  - `.zw/sessions/*.json` wrap the session plus references to replay logs and artifacts. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

- **Promotion + runtime rejection rules**:
  - Promotion requires separate validation and produces new artifacts instead of mutating the editor original.  
  - Runtime must reject editor artifacts *by default* unless they’re being used strictly as previews/inputs to validation. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

You do not need to rewrite any of that; it’s already clean contract language.

***

## What’s still “draft” and worth tightening

You labelled the doc “Status: Draft contract”. At this point, the draft-ness is mostly around naming and versioning, not semantics.

Here are the only tweaks I’d consider before you treat it as v1:

1. **Schema version naming**  
   Right now you mix:
   - `"schema_version": "trixel_editor_output.v1"` in the header description.  
   - `"schema_version": "trixel_editor_memory.v1"`, `"trixel_editor_snapshots.v1"`, `"trixel_editor_session.v1"` for specific containers. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

   That’s fine, but make it explicit that the *container* schema version can differ from the common header schema; e.g.:

   - Common header: `"schema_version": "trixel_editor_header.v1"`.  
   - Containers: `"schema_version": "trixel_editor_memory.v1"`, etc., but they must embed the header fields unchanged.

2. **Deterministic seed semantics**  
   You already say: `deterministic_seed` is required, or must be `null` with `status: "non_deterministic"`.  
   It might help to add one line:

   > If a consumer requires deterministic replay, it must reject artifacts with `status: "non_deterministic"`.

3. **Authority-level extensibility**  
   You currently only allow `authority_level: "editor_only"`. That’s correct for this doc.  
   It may be worth adding a line that says:

   > Any future authority levels (e.g., `"candidate_runtime"`, `"runtime_canon"`) are outside the scope of this document and must be defined only in `docs/TRIXEL_EMBODIMENT_CONTRACT_v1.md` or its successors.

   That prevents people from sneaking in a higher authority level here.

None of that changes behavior, it just makes the draft more obviously “final”.

***

## How to apply this to the three inspected files

Given this doc, the earlier findings about `terminal_trixel.py`, `enhanced_trixel_core.py`, and `empire_bridge.py` become actionable:

- **For `terminal_trixel.py`**:
  - `.zw/memory.json` must be reshaped to the `editor_memory` wrapper defined in 5.1.  
  - `.zw/snapshots.json` must adopt the `editor_canvas_snapshot` container with inner snapshot records as in 5.2.  
  - `.zw/experience_log.jsonl` must write one `editor_replay_event` per line, including the embedded `editor_action` shape.  
  - `.zw/sessions/*.json` must wrap the session as `editor_session` and include at least `replay_log_ref` or equivalent. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

- **For `enhanced_trixel_core.py`**:
  - Any local creative memory or autonomy logs must classify as `editor_memory`, `editor_replay_log`, or `editor_artifact`, never as anything that looks like runtime snapshot or ZON memory. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

- **For `empire_bridge.py`**:
  - Outgoing AI calls must be `ai_bridge_payload` with `payload_kind` (`guidance_request`, `raw_ai_response`, etc.).  
  - Normalized proposals must be `ai_suggestion` with an embedded `editor_action` and clear `status` transitions (`proposed` → `accepted|rejected` → `applied` inside an editor replay). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

The nice part: this doc tells you **exactly** how to annotate, without touching the behavior of the editors or bridge.

***

## How I’d stage it in the repo

Given how much power this has, I’d land it in two clean steps:

1. **Add the document itself**  
   - Path: `docs/TRIXEL_EDITOR_OUTPUT_CLASSIFICATION_v1.md` (or similar).  
   - Commit message:  
     `docs: add Trixel editor output classification v1`

2. **One small implementation pass per system**  
   - Commit 1: `trixelcomposer/terminal_trixel.py` annotates `.zw/memory.json`, `.zw/snapshots.json`, `.zw/experience_log.jsonl`, `.zw/sessions/*.json` to follow sections 5.1–5.4.  
   - Commit 2: `enhanced_trixel_core.py` aligned with `editor_memory` / `editor_replay_log`.  
   - Commit 3: `empire_bridge.py` aligned with 5.5 AI bridge payloads.

Each commit can say “no behavior changes, only schema wrappers” so future you (and future agents) know this was governance work, not logic experimentation.

***

## Direct answer to the implicit question

Yes: this document is coherent, enforceable, and safe to treat as v1 once you polish the schema_version naming and maybe add one paragraph about future authority levels. It gives you the exact levers you need so that Trxel’s editors, bridge, and future PixiEditor integration cannot silently leak into runtime authority again. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_ec27d213-d419-4287-b04f-328e31c8bd32/f1ddac2a-5ca4-4d5c-9ffc-6bc72fe0c6c4/trixel_world_discussion.md)

Would you like me to help you turn this into a concrete `docs/TRIXEL_EDITOR_OUTPUT_CLASSIFICATION_v1.md` file layout (headings, cross-links back into the embodiment contract, and a short intro section that explains how tools should reference it)?  
