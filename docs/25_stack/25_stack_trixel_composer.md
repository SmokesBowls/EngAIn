Trixelcomposer tastes like a **real service with old artist ghosts still inside it**.

The clean identity is this: trixelcomposer should be an **observer-relative visual artifact and atlas service**. It does not own canon. It does not own world state. It does not decide terrain truth. It receives visual demand, resolves or composes visual references, and emits atlas/tile/artifact outputs marked non-authoritative.

The stack verdict is **AUTHORITY_WITH_FIX_FLAGS**.

It is not proof-only, because `demand_resolver.py`, `atlas_composer.py`, and `composer_abi_adapter.py` already form a real service shape. But it cannot be full authority-ready until random artist behavior is cut or quarantined, atlas metadata contracts are locked, generated recipe artifacts exist, and LibreSprite/trixelpixel integration is formalized.

---

## 1. PROJECT ROLE

Trixelcomposer owns **observer-relative visual artifact generation**.

It owns:

Trixelcomposer owns the visual demand resolver. `demand_resolver.py` explicitly says it transforms semantic runtime visual demands into deterministic visual artifact references while preserving isolation from canonical world-state authority. 

It owns atlas lookup and atlas replacement generation. `atlas_composer.py` states that `atlas_meta.json` is the UV topology contract, while trixelcomposer recipes are the semantic surface layer, such as shimmer, foam, and glow. It renders 16×16 tiles into the atlas layout and produces a drop-in replacement `atlas.png`. 

It owns thin ABI normalization for old composer/editor behavior. The adapter file says it does not rewrite legacy composers; it normalizes legacy methods and bridge payloads into `TRIXEL_COMPOSER_ABI_v1` envelope shapes. 

It owns:

`visual demand packet → tile_ref`

`terrain/surface/effect → recipe family`

`atlas_meta.json + recipe → generated atlas PNG`

`legacy composer action → ABI envelope`

`canvas snapshot → non-authoritative editor artifact`

It explicitly does **not** own:

Canonical world state.

Terrain truth.

Narrative truth.

Godot scene authority.

SemanticRenderer runtime addressing rules.

Human-authored pixel production inside trixelpixel/LibreSprite.

Trixelworld procedural terrain generation.

It may observe those systems and produce visual artifacts for them, but it must never become the authority that says “this terrain exists,” “this world cell is true,” or “this scene is canon.”

Neighboring projects that depend on it:

`godotnew/semantic` depends on trixelcomposer for atlas PNGs that preserve the existing `atlas_meta.json` UV layout.

`SemanticRenderer` depends on trixelcomposer outputs only if the generated atlas obeys the same tile order, tile width, tile height, and column layout.

`trixelworld` may depend on it for deterministic visual variants and generated terrain surface art.

`trixelpixel`/LibreSprite is a parallel human-production lane that can feed `.png`, sprite sheets, tilesets, and palettes into the visual ecosystem, but it currently does not import or depend on trixelcomposer. 

---

## 2. CURRENT WORKING STATUS

Confirmed working:

The terminal loop mechanically runs. The output file says session persistence, experience logging, tool mastery, PNG export, and the CLI runtime loop all worked in the observed run. 

Demand resolution is structurally real. It validates demand shape, reads `semantic_context`, checks terrain, surface, effect, world cell, and entropy seed, then resolves to atlas, recipe, generated variant, fallback, or unresolved envelope. 

Atlas composition is structurally real. It reads `atlas_meta.json`, uses `tile_order`, `columns`, `tile_width`, and `tile_height`, renders each role, pastes tiles into atlas coordinates, and saves `.zw/atlases/trixel_atlas_<terrain>_<seed>.png`. 

ABI adapters are real enough to normalize old terminal/enhanced composers into perception, plan, act-result envelopes. The adapter builds base fields with `schema_version`, `authority_level`, `authoritative`, `artifact_kind`, `source`, `composer_id`, `session_id`, `deterministic_seed`, and status. 

Partially working:

The visual demand resolver has a correct authority posture: atlas/recipe/generated/fallback outputs are marked `authority_level: observer_relative` and `authoritative: False`. 

The deterministic variant path exists. If a recipe family and entropy seed exist, it emits `trixel_variant://<family>_<hash>`, where the hash includes terrain, seed, world cell, and view hint. 

The ABI adapter wraps legacy behavior, but it still adapts the old behavior rather than replacing it with clean deterministic composition. It can carry legacy payloads forward, which is useful for transition, but dangerous if treated as final authority. 

Untested or not proven in the stack:

Actual generated atlas PNG compatibility inside Godot.

Whether every `atlas_meta.json` in `godotnew/semantic/trixel/trixelassets` has matching recipes.

Whether `compile_recipe(scene_doc)` always returns renderer-compatible recipe shapes.

Whether `RecipeRenderer` and `TerminalCanvas` are stable when used as non-session atlas tools.

Whether generated `.zw/atlases/*.png` has a paired `atlas_meta.json` output or artifact envelope.

Whether deterministic visual variants are reproducible across machines and Python versions.

Whether trixelpixel/LibreSprite exports can be consumed automatically by trixelcomposer.

Abandoned, legacy, or proof-only:

The old autonomous terminal artist lane is legacy unless it becomes strictly plan-driven. The observed run says the loop is mechanically sound, but planning is random scatter, phase transitions get stuck, and output is noise without an intent layer. 

The Empire Bridge / old ZW creative-loop architecture is a mapped intention, not a trusted current production lane. The architectural map says bridge attachment and `plan()`/`act()` normalization were still gaps. 

The old “autonomous AI artist” identity should be demoted. Trixelcomposer is stronger as an artifact service than as a free-roaming artist.

---

## 3. ERROR PROFILE

Import/path errors:

`atlas_composer.py` imports `scene_server`, `terminal_trixel`, `RecipeRenderer`, and `TerminalCanvas` directly. If the package path is not arranged exactly right, atlas generation fails before it can produce artifacts. 

`demand_resolver.py` defaults `TRIXEL_ASSETS_ROOT` to `../godotnew/semantic/trixel/trixelassets`. That means running it from a moved project or different repo root can silently fall back to hardcoded atlas entries. 

`composer_abi_adapter.py` imports legacy modules inside adapter constructors. Missing `trixelcomposer.terminal_trixel` or `trixelcomposer.enhanced_trixel_core` will break adapter creation, not just optional legacy mode. 

Missing files:

Missing `atlas_meta.json` causes `atlas_composer.py` to raise `FileNotFoundError`. That is good fail-fast behavior, but it means atlas composition cannot generate new terrain until Godot-side atlas metadata exists. 

Missing recipe files are less clear. `demand_resolver.py` can map keywords to recipe families even if matching generated recipe artifacts do not exist. That creates “recipe refs without artifacts.” 

Duplicate files:

There are legacy overlaps between terminal composer, enhanced composer, old bridge maps, and new ABI adapter. The adapter exists because old method names and payload shapes were not unified.

Stale backups:

`terminal_trixel.py.orig` exists in the stack as an old snapshot. It should be treated as historical evidence only, not an import target or architectural source.

Schema mismatch:

`demand_resolver.py` emits `tile_ref`, `authority_level`, `authoritative`, and `derivation`. `composer_abi_adapter.py` emits fuller ABI envelopes with `schema_version`, `artifact_kind`, `source`, `composer_id`, `session_id`, base contract fields, and status. These are not yet the same envelope family. 

`atlas_composer.py` produces only a PNG path from `compose_atlas()`. It does not produce a full artifact envelope with digest, source demand, source recipe, atlas metadata digest, or tile refs. 

Runtime bridge mismatch:

Old maps expected composers to expose `perceive()`, `plan()`, and `act()`, but terminal/enhanced used `plan_action()` / `execute_action()` and `_autonomous_plan()` / `_execute_action()`. The current ABI adapter improves that, but the old mismatch explains why bridge behavior should stay candidate until tested. 

Godot scene/autoload mismatch:

Trixelcomposer should not assume Godot paths are present. `demand_resolver.py` can fall back to hardcoded entries when asset root is missing; that is acceptable for testing but dangerous if Godot expects actual atlas folders. 

Generated-output drift:

`atlas_composer.py` uses a default seed of `42`, then changes per-role seeds using `base_seed + role_index * 7919`. That is deterministic in code, but the output can drift if `compile_recipe()` changes, if recipes change, or if renderer behavior changes. 

Old architecture still present:

The old terminal artist behavior is still conceptually present through adapters. It can plan random brush actions and execute them. The stack itself says the result was random scatter without external guidance. 

---

## 4. CONTRADICTION PROFILE

Contradiction with own stated role:

The clean role is deterministic observer-relative artifact service. The old terminal artist role claims autonomous creative intelligence. Those are not the same. The terminal loop can execute and learn, but the observed planning behavior is random scatter, not reliable artifact composition. 

Contradiction with another project’s role:

Trixelpixel owns human-facing manual pixel production. Its map says it is a standalone C++ application that outputs `.ase`, `.png`, sprite sheets, tilesets, and palettes, and does not depend on trixelcomposer or trixelworld. 

So trixelcomposer must not pretend to own the LibreSprite editor. It may consume exports or provide scripts/contracts, but trixelpixel remains the human art workstation.

Contradiction with current home/project decisions:

`demand_resolver.py` assumes `godotnew/semantic/trixel/trixelassets` as default asset root. That supports the current Godot semantic lane, but also means trixelcomposer’s test behavior can diverge from real runtime if that path is missing and it falls back to hardcoded atlas entries. 

File naming contradiction:

`atlas_composer.py` docstring says usage produces `.zw/atlases/trixel_atlas_shoreline_<hash>.png`, but the actual function saves `trixel_atlas_<terrain>_<seed>.png`. That is a contract mismatch: hash-named artifact versus seed-named artifact.  

Schema name contradiction:

The adapter says `TRIXEL_COMPOSER_ABI_v1`, but individual envelopes use names like `trixel_composer_perception.v1`, `trixel_editor_action.v1`, `trixel_composer_plan.v1`, and `trixel_composer_act_result.v1`. That is workable, but only if a single ABI document defines the family.  

Old vs new pipeline behavior:

Old pipeline: perceive → random/local/LLM plan → brush action → learn.

New service pipeline should be: demand packet → atlas lookup / recipe compile / deterministic variant → artifact envelope.

Those can coexist, but only if old terminal behavior is explicitly marked `legacy/editor_only/non_deterministic`, which the adapter partially does. 

---

## 5. PROPOSED ARCHITECTURE WAITING TO BE BUILT

System name: **Trixel Visual Demand Resolution Service**

Files implying it:

`demand_resolver.py`

`atlas_composer.py`

`composer_abi_adapter.py`

What exists:

A resolver accepts demand dictionaries and emits `tile_ref`.

An atlas composer can generate terrain atlases from `atlas_meta.json` and recipes.

Adapters can normalize legacy composer/editor outputs into envelopes.

What is missing:

A formal `visual_demand_packet.v1` schema.

A formal `trixel_artifact_envelope.v1`.

A policy saying exactly when fallback is allowed.

A generated artifact registry.

A digest trail from demand → recipe → atlas_meta → PNG.

A test harness proving identical demand produces identical output.

System name: **Atlas Contract Compiler**

Files implying it:

`atlas_composer.py`

Godot `atlas_meta.json` references

`SemanticRenderer` mentions in the docstring

What exists:

Reads Godot atlas topology and renders a same-layout replacement atlas. 

What is missing:

Validation that every role in `tile_order` has a valid transform or explicit default.

Generated `atlas_meta.json` copy beside the PNG.

Atlas hash/digest.

Godot import/update step.

Comparison test against original UV layout.

System name: **Legacy Composer Quarantine Adapter**

Files implying it:

`composer_abi_adapter.py`

`output_terminal_trixel.txt`

`architectual_map_trixel_composer.txt`

What exists:

Thin adapters for old terminal/enhanced composers.

Editor-only/non-authoritative fields.

Rejected result envelopes on execution exceptions. 

What is missing:

A hard block preventing non-deterministic plans from being used as production artifact plans.

A mode flag: `legacy_editor_only`, `deterministic_service`, `atlas_batch`.

A test proving `deterministic_seed` actually stabilizes output.

System name: **LibreSprite / TrixelPixel Export Bridge**

Files implying it:

`trixelpixel architectual map.txt`

`Random.js`, `Voxel.js`, `Heightmap.js`, `white_to_alpha.js`, `PerLineOscillation.js`, `ai.js`

What exists:

Trixelpixel is mapped as standalone C++/LibreSprite-style human production tool with JS scripts and exports. 

What is missing:

A formal export folder contract.

A palette handoff schema.

A way to convert `.ase` / sprite sheet / `.gpl` into trixelcomposer recipes or atlas overrides.

A rule for whether human art overrides generated atlas art.

---

## 6. INBOUND SCHEMA

### Inbound item: visual demand packet

Source project: semantic runtime, trixelworld, Godot semantic layer, or demand broker.

Expected filename/schema name: `visual_demand_packet.v1.json`

Required fields:

`demand_id`

`semantic_context.terrain`

`world_cell.x`

`world_cell.y`

`world_cell.z`

Optional fields:

`semantic_context.surface`

`semantic_context.effect`

`semantic_context.world_state`

`entropy_seed`

`view_address_hint`

`render_policy_id`

`palette_hint_id`

Failure behavior if missing:

If demand is not a dict, unresolved envelope.

If `semantic_context` is not a dict, unresolved envelope.

If terrain is missing, unresolved envelope.

If terrain exists but cannot match atlas or recipe, fallback to `trixel_fallback://neutral_gray`. This current fallback exists in code. 

### Inbound item: `trixelcomposer_recipe.json`

Source project: trixelcomposer recipes, trixelworld material system, human-authored visual recipe repo.

Expected filename/schema name: `trixelcomposer_recipe.v1.json`

Required fields:

`recipe_id`

`family`

`canvas.width`

`canvas.height`

`passes[]`

`passes[].type`

`passes[].seed` if deterministic output required

Optional fields:

`transform`

`palette`

`material_tags`

`surface_effects`

Failure behavior if missing:

Demand resolver may still emit `trixel_recipe://family`, but atlas composer may fail or render empty fallback if `compile_recipe()` fails. `atlas_composer.py` catches recipe compile failure and emits an empty gray tile. 

### Inbound item: `trixelcomposer_atlas_plan.json`

Source project: Godot semantic renderer / atlas planner / trixelworld.

Expected filename/schema name: `trixelcomposer_atlas_plan.v1.json`

Required fields:

`terrain`

`environment`

`seed`

`atlas_meta_path`

`tile_order`

`columns`

`tile_width`

`tile_height`

Optional fields:

`role_transforms`

`palette_hint_id`

`material_hint_id`

`output_dir`

Failure behavior if missing:

If `atlas_meta.json` is missing, fail fast with `FileNotFoundError`. 

### Inbound item: render policy

Source project: render policy owner / Godot semantic / runtime authority layer.

Expected filename/schema name: `render_policy.v1.json`

Required fields:

`policy_id`

`fallback_allowed`

`deterministic_required`

`allow_legacy_artist`

`allow_random`

`allowed_derivations`

Optional fields:

`max_variants`

`palette_lock`

`material_lock`

`human_override_priority`

Failure behavior if missing:

Current behavior defaults too permissive: fallback and recipe refs can happen without a policy object. This is a fix flag.

### Inbound item: palette/material hints

Source project: trixelworld, trixelpixel, Godot semantic assets, human art lane.

Expected filename/schema name: `palette_material_hints.v1.json`

Required fields:

`hint_id`

`palette`

`material_tags`

Optional fields:

`source_artifact`

`source_project`

`license`

`priority`

`human_override`

Failure behavior if missing:

Use recipe defaults or neutral fallback. Do not invent material truth.

---

## 7. OUTBOUND SCHEMA

### Outbound item: atlas PNG

Destination project: Godot semantic renderer, trixelworld, visual asset pipeline.

Expected filename/schema name:

Current: `.zw/atlases/trixel_atlas_<terrain>_<seed>.png`

Desired: `.zw/atlases/<terrain>/<atlas_digest>/atlas.png`

Required fields:

PNG image with width = `columns * tile_width`

PNG image with height = `rows * tile_height`

Tile positions matching `atlas_meta.json`

Optional fields:

Preview PNG

Debug contact sheet

Role-by-role tile outputs

Stability level: candidate.

Reason: output generation exists, but artifact naming and metadata pairing are not locked. 

### Outbound item: `atlas_meta.json`

Destination project: Godot semantic renderer.

Expected filename/schema name: `atlas_meta.json`

Required fields:

`tile_order`

`columns`

`tile_width`

`tile_height`

Optional fields:

`terrain`

`source_atlas_digest`

`generated_by`

`recipe_digest`

`role_transforms`

Stability level: stable as inbound Godot contract, candidate as trixelcomposer outbound.

Reason: trixelcomposer reads this contract, but does not yet write a generated paired copy. 

### Outbound item: tile refs

Destination project: runtime visual resolver, Godot semantic layer, trixelworld.

Expected filename/schema name: `tile_ref_resolution.v1.json`

Required fields:

`tile_ref`

`authority_level`

`authoritative`

`derivation`

Optional fields:

`demand_id`

`cache_key`

`variant_hash`

`recipe_family`

`atlas_digest`

Stability level: candidate.

Reason: `demand_resolver.py` already emits `tile_ref`, `authority_level`, `authoritative`, and `derivation`, but no schema version or digest. 

### Outbound item: artifact envelopes

Destination project: EngAIn runtime, asset registry, human review UI.

Expected filename/schema name: `trixel_artifact_envelope.v1.json`

Required fields:

`schema_version`

`artifact_kind`

`authority_level`

`authoritative`

`source`

`composer_id`

`session_id`

`status`

Optional fields:

`base_contract_version`

`base_scene_id`

`base_contract_digest`

`deterministic_seed`

`legacy_payload`

Stability level: candidate.

Reason: adapter base fields already exist, but atlas outputs and demand outputs do not yet use the same full envelope. 

### Outbound item: deterministic visual variants

Destination project: visual demand broker, Godot renderer, trixelworld.

Expected filename/schema name: `deterministic_visual_variant.v1.json`

Required fields:

`variant_ref`

`recipe_family`

`terrain`

`entropy_seed`

`world_cell`

`view_address_hint`

`variant_hash`

Optional fields:

`render_policy_id`

`palette_hint_id`

`material_hint_id`

Stability level: candidate.

Reason: variant hashing exists, but artifact materialization does not yet prove that `trixel_variant://...` points to a real generated PNG or tile. 

---

## 8. AUTHORITY BOUNDARIES

Where trixelcomposer must stop and ask another project:

Ask semantic runtime / trixelworld when terrain identity is unclear.

Ask Godot semantic renderer when `atlas_meta.json` layout changes.

Ask render policy owner before using fallback in production.

Ask trixelpixel before treating human-authored art as generated art.

Ask canon/world-state owner before using `world_state` for anything beyond visual variation.

Ask asset registry before overwriting or promoting generated atlas PNGs.

Where another project must stop and ask trixelcomposer:

When it needs a deterministic visual reference from a semantic demand.

When it needs a generated atlas that preserves an existing Godot UV topology.

When it wants to normalize old terminal/enhanced composer behavior into ABI envelopes.

When it wants to know whether a visual artifact is generated, recipe-derived, atlas-derived, fallback, or unresolved.

When it wants to use trixelcomposer recipes as a semantic surface layer.

---

## 9. TOP 10 QUESTIONS FOR HUMAN REVIEW

1. Should random fallback artist behavior be deleted, or kept only behind `legacy_editor_only`?

2. Should production mode fail hard when no recipe exists, instead of returning `trixel_fallback://neutral_gray`?

3. Is `trixel_variant://...` allowed to be a reference-only URI, or must it always point to a generated file?

4. Should atlas output naming use seed names or digest names? Current docstring and code disagree.

5. Is `atlas_meta.json` owned by Godot only, or can trixelcomposer generate new atlas metadata?

6. Should human trixelpixel exports override generated recipes when both exist?

7. What is the official schema name: `TRIXEL_COMPOSER_ABI_v1`, `trixel_artifact_envelope.v1`, or both?

8. Should `world_state` be accepted in demand packets, or is that too close to canon authority?

9. What is the minimum artifact envelope required before another project may consume generated atlas PNGs?

10. Should `compile_recipe()` be inside trixelcomposer, or should recipes be compiled by a separate scene/material service?

---

## 10. STACK VERDICT

**AUTHORITY_WITH_FIX_FLAGS**

Why:

Trixelcomposer has a real center now. `demand_resolver.py` gives it a deterministic observer-relative service lane. `atlas_composer.py` gives it a real atlas-generation lane. `composer_abi_adapter.py` gives it a quarantine bridge for legacy editor behavior. Those are not imaginary.

But the stack is not clean enough for full authority. The old terminal artist still carries random scatter behavior. The observed run proves mechanics but not art intelligence. The adapter still normalizes legacy behavior instead of eliminating it. Atlas PNG generation exists, but outbound metadata and artifact envelopes are incomplete. Demand resolver emits recipe and variant refs that may not correspond to generated artifacts yet. Trixelpixel integration is mapped as a neighboring human-production lane, not actually wired.

So the correct status is:

```text
trixelcomposer
Status: AUTHORITY_WITH_FIX_FLAGS

Owns:
- observer-relative visual demand resolution
- atlas composition against existing atlas_meta topology
- generated visual variants
- editor/legacy ABI wrapping

Does not own:
- canon
- world truth
- Godot runtime authority
- trixelpixel manual production
- trixelworld terrain truth

Fix flags:
1. Kill/quarantine random fallback artist behavior.
2. Unify demand resolver output with artifact envelope output.
3. Make atlas PNG generation emit paired atlas_meta + digest.
4. Resolve atlas filename hash-vs-seed contradiction.
5. Require render policy before production fallback.
6. Materialize recipe/variant refs into actual generated artifacts.
7. Formalize trixelpixel export ingestion.
8. Add deterministic replay tests.
```

The clean rebuild sentence is:

```text
Trixelcomposer is not the artist king.
It is the visual artifact resolver and atlas compiler.
It receives semantic visual demand, preserves observer-relative authority, generates or references visual artifacts, and hands Godot/trixelworld/trixelpixel a non-canonical asset envelope they can safely consume.
```
