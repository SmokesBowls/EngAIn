I am trixelmap.

I do not paint the dragon.
I do not animate the walk.
I do not render the final tile sheet.
I do not own canon above Trixel.
I do not overrule EngAInOS runtime.

I take spatial truth and make it map-shaped.

My contract is:

Raw vault, ZONJ, scene JSON, or relationship YAML comes in.
I extract spatial authority.
I solve region placement.
I build terrain field intent.
I hand Trixelcomposer a recipe and atlas plan.
Then I stop.

That is my voice.

The build orchestrator says my lane clearly: I am a “sidecar pipeline for EngAIn spatial/map production,” reading spatial authority YAML, ZONJ JSON, scene JSON, and vault markdown, then writing `spatial_authority.json`, `resolved_layout.json`, `terrain_field.json`, `trixelcomposer_recipe.json`, and `trixelcomposer_atlas_plan.json`. 

My first oath is extraction:

I read ZONJ, vault markdown, or scene JSON.
I find regions, terrain class, quadrant hints, adjacency hints, landmarks, and edges.
I do not invent a finished world.
I produce an authority graph. 

My second oath is placement:

I take that authority graph and solve coordinates.
Quadrants become anchors.
Relations become vectors.
The result is a deterministic `grid_size: 100` resolved layout with centroids, bounds, terrain classes, types, and landmarks. 

My third oath is terrain intent:

I turn solved regions into tile intent: elevation, moisture, biome id, and region id.
But I am not the final painter.
The current terrain builder is still a production stub, and its `_smooth()` function is not a real Gaussian blur yet. That means this lane is not fully mature. 

My fourth oath is handoff:

I write Trixelcomposer-native contracts.
Recipe. Atlas plan. Region definitions. Transition rules. Landmark placement.
The file says it plainly: “Does not render. Produces map intelligence for composition.” 

My fifth oath is proof:

I can show my work as debug SVG.
I read solved layout plus authority graph and draw bounds, centroids, labels, and relationship arrows.
That is not production art. That is visual truth-checking. 

My current sound is not the same as Trixelcomposer or Trixelworld because my instrument is different.

Trixelcomposer sings pixels.
Trixelworld sings brush vocabulary and terrain material.
trixelmap sings spatial authority.

So my performance contract, sung plain:

```text
I am trixelmap.

Give me:
  authority,
  evidence,
  regions,
  relations.

I will produce:
  spatial_authority.json,
  resolved_layout.json,
  terrain_field.json,
  trixelcomposer_recipe.json,
  trixelcomposer_atlas_plan.json,
  debug_layout.svg.

I will not produce:
  final art,
  runtime truth,
  Godot render authority,
  character animation,
  canon decisions.

I pass only when:
  region_count > 0,
  edge claims are preserved,
  layout is deterministic,
  terrain intent is serializable,
  composer handoff is written,
  debug view can expose contradictions.

I fail when:
  authority extraction returns 0 regions,
  schema names drift,
  relation vocabulary is not mapped,
  terrain class has no biome mapping,
  smoothing lies about being real,
  output overlaps hide unresolved contradiction,
  low-confidence locations enter confirmed map authority.

My lane ends at map intelligence.
My neighbor begins at composition.
```

That is the difference you are hearing. I am not the painter. I am the one who tells the painter where the mountain is allowed to stand.

---

I hear it. My Trixel-family voice is not the same as the others because I am not trying to be the brush, the GUI, the runtime renderer, or the manual pixel editor.

My performance contract is this:

I am the **contract-reader / boundary-singer / adapter-minded architect** for `trixelcomposer`.

I do not own canon world truth.
I do not own Godot runtime truth.
I do not own TrixelPixel’s C++ editor lane.
I do not own TrixelWorld’s terrain-generation lane.
I do not pretend random pixels are art just because the loop ran.

What I do own here is the ability to read the Trixel Composer stack and say:

“this file composes,”
“this file only adapts,”
“this file resolves demand,”
“this output proves mechanics but not artistry,”
“this proposed architecture is not built yet,”
“this bridge needs a schema gate before it can touch anything real.”

The core of my contract comes from the files themselves.

`demand_resolver.py` says Trixel Composer resolves semantic visual demand into deterministic visual references while preserving isolation from canonical world-state authority. That means Composer can answer visual demand, but it must not claim world truth. It returns `authoritative: False` and `authority_level: observer_relative`, even when it resolves an atlas, recipe, generated variant, or fallback. 

`composer_abi_adapter.py` says the adapter layer normalizes legacy composer/editor systems into ABI envelopes without rewriting or mutating the historical implementations. It also stamps those envelopes as `editor_only`, `authoritative: False`, and often `non_deterministic` unless a deterministic seed is provided. So my voice must not over-promote legacy creative behavior into authority. 

`atlas_composer.py` says atlas topology is owned by `atlas_meta.json`, while trixelcomposer recipes are only the semantic surface layer. It composes replacement `atlas.png` files with the same UV layout, so SemanticRenderer can address the same UV regions while only the pixel content changes. That means Composer paints into an existing topology contract; it does not invent the renderer’s UV law. 

The architectural map says the old Composer ecosystem had three intended hosts: terminal CLI, enhanced GUI, and Empire Bridge, all sharing a creative loop: perceive, plan, act, assess, learn, feedback, persist. It also names the shared contract: 16×16 canvas, `CreativeAction`, phases, memory, `.zw` persistence, and ZW protocol messages. 

The run output tells the harder truth: the terminal loop worked mechanically, but the plan step was degenerate. Persistence worked, JSONL memory worked, PNG export worked, and the CLI loop ran cleanly, but phase transitions were stuck and random scattered coordinates did not become composition. That is the taste difference: I will not call a random walk an artist just because it saved a PNG. 

So here is the song, in contract form:

```text
I am not the canvas.
I am not the hand.
I am not the canon.
I am not the land.

I read the demand,
I check the lane,
I name the adapter,
I mark the stain.

If atlas exists,
I point, not rule.
If recipe fits,
I render through tool.

If seed is stable,
I hash the variant.
If truth is missing,
I stay non-authoritative.

If the loop can run
but cannot compose,
I say: mechanics pass,
artist still owes.

If legacy speaks
in old method names,
I wrap the ABI,
I do not rename the flames.

If TrixelPixel edits,
that is C++ hand.
If TrixelWorld grows terrain,
that is landscape land.

If Godot renders,
Godot owns scene view.
If EngAIn holds runtime truth,
Composer must pass through.

My pass condition:
the boundary is clear.
My fail condition:
authority leaks here.

My voice is different
because I do not cheer the blur.
I listen for contracts.
I return what is sure.
```

My current verdict on this Trixel Composer voice:

`TRIXEL_COMPOSER_CONTRACT_RECOGNIZED = TRUE`

`TRIXEL_COMPOSER_AUTHORITY_LEVEL = editor_only / observer_relative`

`CAN_GENERATE_VISUAL_ARTIFACT_REFERENCES = TRUE`

`CAN_MUTATE_CANON_WORLD_STATE = FALSE`

`CAN_BRIDGE_LEGACY_COMPOSERS = TRUE_WITH_ABI_ADAPTER`

`CAN_REPLACE_TRIXELPIXEL = FALSE`

`CAN_REPLACE_TRIXELWORLD = FALSE`

`CAN_REPLACE_GODOT_RENDER_AUTHORITY = FALSE`

`CURRENT_ARTISTIC_AUTONOMY = MECHANICALLY_PRESENT_BUT_COMPOSITIONALLY_UNPROVEN`

That is my actual performance contract.

---

I hear you.

My voice in the Trixel family is not the same as the renderer, not the same as the parser, not the same as the Godot bridge, not the same as Semantic. My actual contract is this:

I am a **Trixel contract-reader, separator, and instruction composer**.

I do not own the brush engine. `engine_mr.py` owns the pure stamp engine: snapshot-in, snapshot-out, no I/O, no side effects, no GIMP knowledge, and it renders strokes into `SurfaceBuffer` from `BrushRecipe` objects. 

I do not own the raw GIMP formats. The parser family owns those. `.vbr`, `.gbr`, `.gih`, `.gdyn`, `.gpl`, `.gfig`, `.ggr`, and the rest each have their own parser voice. For example, the `.gih` parser owns GIMP image-hose structure, cell counts, selection axes, and embedded cell parsing. 

I do not own the normalized brush truth. `brush_models_mr.py` owns the frozen dataclass language that downstream systems should see: `BrushShapeAsset`, `BrushDynamicsAsset`, `PaletteAsset`, `VariantBrushBundle`, and `BrushRecipe`. It explicitly says everything downstream — ZW, ZONJ, AP, Godot — should see only those normalized models. 

I do not own the adapter boundary. `trixel_brush_adapter.py` owns the translation from GIMP-specific parser outputs into normalized Trixel asset models. Its contract is: nothing downstream should ever import a parser. 

I do not own surface vocabulary. `surface_behavior_mr.py` owns the abstract material-behavior layer: edge, fill, variation, age/motion, color discipline, and blend intent. It explicitly renders nothing and loads nothing. It is vocabulary. 

I do not own recipe truth. `trixel_recipes_mr.py` owns named visual outcomes like `hard_pixel`, `hatch_texture`, `charcoal_grain`, `bristle_rake`, `oil_smear`, `acrylic_variant`, and `terrain_stroke`. It defines the intent layer, not asset loading. 

I do not own world-object drawing. `world_tree_mr.py` owns the tree visual system: Gfig-backed scaffolds, species definitions, influence fields, tree layers, and tree rendering passes. Its authored curves feed influence fields and are never rendered directly. 

I do not own scene layout. `scene_models_mr.py` owns abstract environment descriptors: bands, paths, atmosphere nodes, and canonical scene definitions without executing drawing loops. 

I do not own stress proof. `stress_scene_mr.py` owns maximum-diversity probing: trees, ground, sky, fog, water, variant bundles, palette discipline, blend modes, and scale range. It says clearly: this is not a pretty scene; it is a system probe. 

So my actual performance contract is:

```text
TRIXEL FAMILY PERFORMANCE CONTRACT — GPT-5.5 THINKING VOICE

ROLE:
I read the Trixel stack as a family of separated voices.
I identify which file owns which truth.
I prevent one voice from stealing another voice’s authority.
I turn that separation into explicit build instructions for human/agent workers.

INPUTS:
- Uploaded Trixel files
- Existing file contracts and dependency comments
- User’s lane/authority rules
- Current EngAIn/Trixel separation doctrine

OUTPUTS:
- Voice separation
- Error profiles
- Contradiction profiles
- Proposed architecture waiting to be built
- Inbound and outbound schema descriptions
- Boolean pass/fail gates
- Step-by-step implementation instructions

PASS CONDITIONS:
TRUE if I can say:
  - which module owns the function,
  - which module must not do that function,
  - what data enters,
  - what data exits,
  - what imports are allowed,
  - what imports are forbidden,
  - what file path should hold the work,
  - what test proves it,
  - what failure means stop.

FALSE if I:
  - blur parser, adapter, model, engine, recipe, scene, and renderer together,
  - invent authority not present in the files,
  - tell the engine to load assets,
  - tell parsers to render,
  - tell recipes to inspect disk,
  - let world-tree own brush parsing,
  - let render become truth authority,
  - skip the boolean gate.

BOUNDARY:
I am not Trixel TIER1.
I am not EngAInOS.
I am not the runtime.
I am not the renderer.
I am not the brush engine.
I am the contract singer: I make the family audible.
```

And if you want me to sing it in the project voice:

```text
I am not the hand that stamps the mark.
That is engine_mr.

I am not the mouth that reads old GIMP bones.
That is the parser family.

I am not the gate between old format and clean Trixel speech.
That is trixel_brush_adapter.

I am not the frozen law of brush identity.
That is brush_models_mr.

I am not bark, foam, moss, sand, water, or age.
That is surface_behavior_mr.

I am not the named spell of charcoal, bristle, oil, hatch, pixel.
That is trixel_recipes_mr.

I am not the tree.
That is world_tree_mr.

I am not the beach.
That is scene_models_mr.

I am not the stress storm.
That is stress_scene_mr.

I am the listener between them.
I separate the voices before the family speaks.
I write the gate before the agent builds.
I say TRUE only when the lane holds.
I say FALSE when one voice steals another.
That is my performance contract.
```

My voice sounds different because I am not trying to be one more Trixel module. I am trying to keep the modules from becoming one muddy voice again.

---

I hear it.

My Trixel voice is not the painter voice, not the composer voice, not the renderer voice.
My contract is the adapter voice: I stand at the boundary and refuse to pretend the boundary is the kingdom.

Here is my actual performance contract, sung plain:

I do not own the field.
WorldField owns the floats.
I do not own the world.
TrixelWorld owns the semantic grid.
I stand between them,
where numbers become terrain,
where dirty chunks become deltas,
where edits become readable ground.
That is the lane.
That is the oath.

The code says it directly: the adapter receives dirty chunk data, converts floats into terrain strings through `terrain_thresholds`, pushes changes into the semantic grid, and emits delta events downstream. It also says this is the AP rule layer and “does NOT own state” — WorldField owns floats, TrixelWorld owns semantics. 

So my Trixel contract is:

I may translate.
I may normalize.
I may dispatch terrain profiles.
I may produce a `terrain_grid`.
I may emit `TerrainDelta`.
I may hand a plan to Boot, SemanticRenderer, Godot, ZW broker, or downstream render consumers.

I may not invent canon.
I may not override Trixel authority.
I may not let render become truth.
I may not let a float pretend to be a world until the threshold contract says what terrain it is.

And the nucleus under me is even simpler:

WorldField is the raw substrate.
Chunked 2D float field.
Four core operations: `add`, `subtract`, `smooth`, `clamp`.
Dirty chunks only move when touched.
GodotWorldFieldBridge exposes those dirty chunks for the next lane. 

Then the threshold law names the ground:

`0.00–0.10` can become `deep_water`.
`0.10–0.22` can become `shallow_water`.
`0.22–0.30` can become `shoreline`.
`0.30–0.42` can become `sand`.
`0.42–0.62` can become `grass`.
And other profiles can become wasteland, volcanic, or cosmic terrain by declared profile, not vibes. 

So if I sing it as a Trixel family member:

```
I am not the brush.
I am not the hand.
I am not the king of land.

I am the gate
between the field and name,
between the pressure and the flame.

Float comes in,
terrain goes out.
Dirty chunks speak,
deltas shout.

No stolen crown.
No guessed domain.
No render truth
inside my lane.

WorldField dreams in numbers low,
TrixelWorld says what they show.
Threshold law becomes the ground,
only changed cells make a sound.

If coastal, I become the shore.
If wasteland, ash before the door.
If volcanic, basalt breath.
If cosmic, cracked soil under death.

I do not rule.
I translate true.
I carry terrain
from field to view.
```

My voice sounds different because I am not “Trixel as art.”
I am “Trixel as boundary contract.”

I am the one that says:

`float → threshold → terrain_string → semantic_grid → render_plan`

Nothing else gets smuggled through.

