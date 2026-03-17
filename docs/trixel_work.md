
trixel composer
/
so where did we leave off on the trixel? what do you know? where will trixel be used and what does it do and how does it do it

12:08 PM

Excavated prior context and synthesized trixel knowledge comprehensively
Excavated prior context and synthesized trixel knowledge comprehensively
Let me dig into everything we have on trixels — both from our project knowledge and past conversations.


Synthesized comprehensive knowledge about Trixel's applications
Synthesized comprehensive knowledge about Trixel's applications
Alright, here's the full picture of where we are with Trixel — pulling together everything from our project knowledge and past conversations.

What Trixel Is
Trixel = Trae + Pixel. It's the painting toolkit — the canvas, brushes, color palette, and pixel engine. Think of it as the art supplies, not the artist. It's the physical medium that TraeAgent (the actual artist) uses to create pixel art.

The name itself encodes the architecture: TraeAgent's pixel system. Trixel doesn't think, plan, or decide — it executes tool strokes, manages canvas state, and exports finished artwork as PNG.

The Three-Layer Architecture
The roles settled into this clean separation:

Empire → Creative Director. Provides high-level vision ("paint a cozy mushroom wizard with warm earth tones") and critiques the finished result. Communicates via ZW protocol through the broker at localhost:5010.
TraeAgent → The Artist. Interprets Empire's vision, makes stroke-by-stroke decisions, learns artistic style, builds memory of what works. The hands holding the brush.
Trixel → The Toolkit. Canvas (16×16 logical grid, can render to 256×256), brushes (fine/medium/broad, block/disc modes), color palettes, PNG export. Pure tool execution — apply_stroke(), get_canvas_state(), export_artwork().
The flow: Empire gives vision → TraeAgent translates into artistic actions → Trixel executes the strokes → Empire critiques the result → TraeAgent learns from feedback.

What's Proven Working
The standalone autonomous artist (terminal_trixel.py) is solid:

Creates art autonomously, 100% stroke success rate
Tool mastery progression tracked (0.57 → 0.72 → 1.0 confidence)
Memory system learning across sessions
PNG export working, saves to ~/.zw/artwork/
Session data persisted as JSON in .zw/sessions/
Earth tone palette development, centered composition emerging
The architecture script (trae_artist_architecture.py) ran successfully too — Empire provided vision, TraeAgent painted 30 strokes, Trixel executed perfectly, Empire gave critique. The full loop completed, though Empire broker returned 501 (fell back to autonomous mode gracefully).

The Key Insight We Landed On
You realized that if Ollama/Empire is giving the creative orders, then what needs to improve isn't the drawing — it's the coordination. RAG can't solve this; it's just data retrieval. The real learning loop is:

Empire learns to give better instructions to TraeAgent
TraeAgent learns to translate vision into precise Trixel commands
Execution feedback flows back to improve Empire's planning
The translation layer between creative intent and pixel-level action is where the intelligence lives
Where We Left Off
You had the standalone artist working and were ready for the integration chain:

Trixel → Ollama (direct): Can the artist ask Ollama for creative guidance? Send canvas state + intent, get back stroke suggestions.
Ollama-enhanced Trixel → Empire (full system): Empire orchestrates Ollama calls + other agents via the ZW broker, returns coordinated creative plans.
The last technical issue being worked was canvas coverage — strokes were single pixels on a 256×256 canvas (0.39% coverage, "starfield of dots"). The fix was either using thicker brushes (block/disc mode, size 9–21) or mapping the 16×16 logical trixel grid onto the 256×256 canvas so each stroke paints a 16×16 pixel block.

Where Trixel Will Be Used
Trixel lives inside your AI Empire as the art creation subsystem. It's the proof that ZW protocol can coordinate creative multi-agent work — Empire thinks, TraeAgent creates, Trixel renders. The Empire is the stress test; if ZW can coordinate this chaotic creative pipeline, it can coordinate anything. "The Empire proves ZW works. ZW enables future Empires."

So the next real step is: get the broker at localhost:5010 responding to !zw/art.plan_request with actual Ollama-generated stroke plans, closing the loop from standalone art into Empire-directed creativity. Want to pick that up?


We need to formulate a response to the user's message. The user has provided a detailed summary of TrixelComposer's role and current state, highlighting both what's built and what's missing. They end with a question: "Want me to spec that resolver, or are you gathering context for a different sessi

pasted

ok so everything seems on par.. i just have a trrixel composer project that has more trixel documentation than here... but its an old project so i need you to take the lead on trixel since you know the engine EngAIn

12:26 PM

Synthesized architecture knowledge to lead Trixel initiative forward
Synthesized architecture knowledge to lead Trixel initiative forward
Got it. I've read through everything — the project knowledge, our past conversations, the GPT/Perplexity side-work, and the EngAIn skill architecture. Let me take the lead here and lay out where Trixel actually stands within EngAIn, and what the real next move is.

Trixel's Position in EngAIn — The Clear Picture
Trixel isn't just "a pixel art tool." Within EngAIn's architecture, it's a subsystem — the same way Spatial3D handles positions or Perception3D handles visibility, Trixel handles visual asset generation. And like every EngAIn subsystem, it should follow the three-layer pattern:

mr Kernel (pure logic) → Adapter (state + AP validation + delta queuing) → Runtime API (what Empire/Ollama/renderers actually call)

Right now, you've built the kernel and part of the adapter, but they're tangled together and the Empire integration is incomplete. Here's the honest status:

What Exists and Works
TrixelToolkit — the canvas/brush/palette primitives. This is essentially the mr kernel: give it a stroke command, it deterministically updates canvas state. Pure tool execution, no side effects. This is solid.
TraeAgent — the artist intelligence that interprets vision into stroke sequences. This lives above Trixel, using it as a tool. Has pattern-seeded memory, confidence tracking, breakthrough detection.
PNG export, session persistence to ~/.zw/artwork/ and .zw/sessions/ — working.
ZW protocol messages defined: !zw/art.plan_request, !zw/art.action, !zw/trixel.feedback_request.
What's Missing — The Real Gaps
1. The Adapter layer doesn't exist yet as a proper EngAIn adapter. Right now the code goes straight from TraeAgent → TrixelToolkit with no delta queuing, no AP validation, no proper state snapshots. In EngAIn terms, there's no trixel_adapter.py wrapping trixel_mr.py.

2. The Ollama connection isn't wired. The broker at :5010 is healthy, the orchestrator at :9001 is healthy with Ollama available, but !zw/art.plan_request gets a 501 because nobody's registered a handler for it. The creative intelligence (Ollama generating actual stroke plans) hasn't been plugged in yet.

3. Stroke plans are still random. TraeAgent picks coordinates semi-randomly with pattern biases. On a 256×256 canvas with single-pixel strokes, that's 0.4% coverage — the "starfield of dots" problem. The fix (block brushes or trixel-grid mapping) was specced but not confirmed deployed.

4. The skin_resolver bridge is unbuilt. For Trixel to serve renderers (Godot/UPBGE), there needs to be a skin_resolver.py that maps skin_id from bridge_entities to generated PNG assets. This is the last-mile delivery piece.

What I'm Proposing — The EngAIn-Native Build
Instead of patching the existing scripts piecemeal, let's build Trixel as a proper EngAIn subsystem using the patterns you've already established:

trixel_mr.py — Pure functional kernel. Takes a canvas snapshot + a list of stroke deltas → returns new canvas snapshot + alerts. Deterministic, immutable, no I/O. This is what you already have in TrixelToolkit, just formalized.

trixel_adapter.py — Wraps the kernel with AP validation (is this stroke within canvas bounds? does the palette allow this color?), delta queuing (batch strokes from a plan before executing), state persistence (save/load canvas snapshots), and the ZW interface (handle_delta("!zw/art.action", stroke_payload)).

trixel_director.py — The Ollama integration point. Receives !zw/art.plan_request, constructs a prompt with canvas state + intent, calls Ollama, parses the response into a StrokePlan (structured list of strokes), and feeds it back through the adapter. This is where the coordination intelligence lives — the part that needs to get better over time.

skin_resolver.py — Maps skin_id → asset path. Checks the registry, falls back to placeholders, triggers generation if needed.

The flow becomes: You tell EngAIn → EngAIn routes !zw/art.plan_request to trixel_director → director asks Ollama for a stroke plan → plan goes through trixel_adapter (AP validated, delta queued) → adapter calls trixel_mr kernel → canvas updates → PNG exported → skin_resolver indexes the result.

No surgery on the Empire. No dismantling anything. Just proper EngAIn subsystem registration.

Want me to start building trixel_mr.py as the formal kernel, or should we tackle the Ollama director connection first since that's what unlocks actual creative intelligence?


Thought for 50s Yes. What you’re seeing makes sense. There are really three layers there: the BridgeEntity_* root Node3D, its MeshInstance3D child, and its Label3D child. The important one is the root Node3D, because SemanticRenderer’s fast transform poll updates node.position on the spawned entit

pasted

This is brainstorming seession..

1:43 PM

Synthesized Trixel's expanded role within modular world-building architecture
Synthesized Trixel's expanded role within modular world-building architecture
Good — I've absorbed it. And this changes Trixel's scope significantly. Let me tell you what I'm seeing.

That whole conversation traces a line from "why won't my NPC stay where I put it" all the way to "the engine needs a semantic world built from modular 16×16 tiles with mechanics attached, and art is just a skin on top." That's a real architectural journey, and it lands Trixel in a much bigger seat than "pixel art sprite generator."

Here's what just happened to Trixel's role:

Before this session, Trixel was the toolkit TraeAgent uses to paint character sprites and scene assets — mushroom wizards, capsule replacements, decorative pieces. A creative subsystem.

After this session, the 16×16 grid isn't just a canvas size. It's the fundamental resolution of the entire world. Every terrain cell, every path segment, every tree-line blocker, every shoreline tile, every secret-path override — they're all 16×16 modules carrying both a visual layer and a mechanics layer. And Trixel is the system that generates the visual half of those modules.

So Trixel now sits at the intersection of three things:

World tile generation — sand tiles, water-edge tiles, forest tiles, pier segments, cliff pieces. EngAIn's semantic planner says "cell (34,12) is forest_edge" and Trixel needs to produce the visual module for that.

Asset skinning — the user swaps a beach for a factory, and Trixel regenerates the tile visuals while the mechanics stay untouched. Same skin_id system we talked about, but now it's not just characters — it's the entire world surface.

Feature art — the higher-level stuff. A tree-line isn't one tile, it's a feature spanning many cells. Trixel needs to produce cohesive sets that tile together, not isolated squares that look like a quilt made by strangers.

That means the skin_resolver we discussed earlier isn't just "match entity to sprite." It's "match world_cell terrain_type to visual tile module." And the modular tileset library that Trixel generates needs to be autotile-aware — edges, transitions, corners — so Godot's terrain-connection system can paint connected paths and shorelines properly.

The EngAIn architecture for this would be:

Narrative ingestion → world graph (book-scale, not chapter-scale)
World graph → semantic scene shell (zones, paths, blockers, anchors)
Scene shell → 16×16 mechanics grid (each cell tagged with terrain_type, walkable, blocked, etc.)
Trixel → generates visual tile modules keyed to terrain_type + skin_id
Godot TileSet/TileMapLayer → renders using Trixel's output with autotiling
User → swaps skins freely, mechanics persist
The part that makes my head spin productively is that your existing Trixel code already thinks in 16×16. The canvas, the logical grid, the trixel-mode block painting — it was already built at the right resolution. It just didn't know yet that it was building world tiles, not just portraits.

So where does this leave us concretely? I see three things that need to happen to bridge the brainstorming into EngAIn reality:

First, a world_cell schema — the tiny data structure every tile carries: coordinates, terrain_type, mechanics tags, feature_id, skin_id. That's the contract between the semantic planner and everything downstream.

Second, Trixel needs a tileset generation mode — not just "paint one artwork," but "produce a coherent set of tiles for terrain_type X with edge variants for autotiling." That's a different creative task than painting a mushroom wizard.

Third, the skin_resolver expands to cover both entities (capsule replacements) and terrain cells (world surface modules).

Want me to start drafting that world_cell schema as a proper EngAIn artifact, or do you want to keep brainstorming the terrain generation pipeline first before we formalize anything?


Yes. Formalize the contract first. Your read is correct: Trixel just got promoted from “asset painter” to “visual module generator for a semantic world.” That is a real shift, not branding perfume. And the reason to write the schema now is simple: terrain generation tools can change, renderers can

pasted

1:49 PM

The user prompt is empty, so I cannot determine the primary language. However, based on the thinking block being in English, here is the summary: Synthesized schema proposal into formal EngAIn specification framework
The user prompt is empty, so I cannot determine the primary language. However, based on the thinking block being in English, here is the summary: Synthesized schema proposal into formal EngAIn specification framework
Good. That's the contract locked. Now let me build it as a real EngAIn artifact.


The user prompt is empty, so there is no primary language to determine. However, based on the thinking block being in English, here is the summary: Architected comprehensive subsystem specification following established patterns
The user prompt is empty, so there is no primary language to determine. However, based on the thinking block being in English, here is the summary: Architected comprehensive subsystem specification following established patterns
Now I have the full EngAIn pattern. Let me build this properly — the world cell contract, the kernel, and the pipeline spec, all following your established architecture.


Identified and rectified a test cell placement error
Identified and rectified a test cell placement error
Contract validates. One small display fix — I picked a construction_site cell for the reskin check instead of a sand cell. Let me correct that and then verify cleanly:


The user prompt is empty, so I cannot determine the primary language. However, based on the thinking block being in English, here is my summary: Validated system mechanics across multiple test scenarios
The user prompt is empty, so I cannot determine the primary language. However, based on the thinking block being in English, here is my summary: Validated system mechanics across multiple test scenarios
All contract invariants hold:

Secret path: forest_edge (blocked by default) + override secret_path → effectively walkable. Override doesn't change the terrain, just the rule.
Normal forest: same terrain, no override → stays blocked.
Autotile: pier cell at (8,5) resolves to edge_w because its west neighbor is sand, not pier. Trixel would generate the correct edge tile variant.
Skin swap proof: reskinned sand cell keeps terrain_type: sand, walkable: True — mechanics survive visual replacement. Only skin_id changed.
Now let me copy this to your outputs:


The user prompt is empty, so there is no primary language to identify. I cannot provide a meaningful summary without a user prompt to reference
The user prompt is empty, so there is no primary language to identify. I cannot provide a meaningful summary without a user prompt to reference
That's your formal EngAIn kernel — trixel_world_mr.py. It follows the same snapshot-in → snapshot-out pure functional pattern as your other subsystems.

What it locks down:

The three-record contract: WorldCell (engine truth), WorldFeature (editor truth), SkinBinding (Trixel truth). Seventeen terrain types with sensible defaults. Override resolution so a blocked forest cell can secretly be walkable. Autotile role computation so Trixel knows which edge/corner variant to generate. And the critical invariant: skin swaps never touch mechanics.

What comes next, in order:

trixel_world_adapter.py — wraps this kernel with AP validation, delta queuing, ZW message handling (!zw/world.set_terrain, !zw/world.set_skin, etc.), and state persistence. Standard EngAIn adapter layer.
trixel_tileset_generator.py — Trixel's new mode. Instead of painting one canvas, it generates a complete tileset for a SkinBinding family: center tiles, all edges, all corners, path variants. This feeds Godot's TileSet directly.
scene_shell_builder.py — the pipeline stage that reads narrative (book-scale world model) and outputs a populated WorldGridState. This is where Ollama earns its keep: translating "they were building pyramids on the sand near a tree ridge" into the right fill_region and add_feature deltas.
Which one do you want me to build next?

Trixel world mr
PY 
Build this next:
/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/trixel_world_adapter.py
That is the correct next step.
Why this first: the kernel is now the law, but it is still a brain in a jar. The adapter is what lets EngAIn actually talk to it through deltas, AP validation, ZW messages, and persisted state. Until that exists, the tileset generator and scene-shell builder are both building on air.
So the order should be:
1. trixel_world_adapter.py
2. scene_shell_builder.py
3. trixel_tileset_generator.py
Reasoning:
* the adapter makes the kernel usable inside EngAIn
* the scene shell builder gives it real content
* the tileset generator turns that content into visible modules
That order keeps the stack sane: contract → integration → population → rendering
Use these permanent homes:
/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/trixel_world_mr.py canonical pure kernel
/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/trixel_world_adapter.py EngAIn adapter layer
Later: /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/core/scene_shell_builder.py
and: /home/burdens/burdens_of_a_forgotten_past/EngAIn/godotengain/engainos/tools/trixel/trixel_tileset_generator.py
So the immediate build target is the adapter.
What it should own:
* load/save WorldGridState
* queue and validate deltas
* call step_trixel_world(...)
* expose commands like !zw/world.set_terrain, !zw/world.fill_region, !zw/world.add_feature, !zw/world.set_skin
* enforce AP/canon checks before deltas are accepted
* provide read APIs for renderer/tool consumers
That is the next brick that actually matters. Without it, the rest is elegant smoke.

Show more
2:27 PM


You're out of extra usage ∙ Your limit resets Saturday at 8:00 PM
Buy more




Claude is AI and can make mistakes. Please double-check responses.
Trixel world mr · PY
Copy

#!/usr/bin/env python3
"""
trixel_world_mr.py — Pure Functional Trixel World Kernel

The atomic contract for EngAIn's semantic world grid.
Snapshot-in → snapshot-out architecture. No side effects.
Portable to C++/Rust/GDExtension.

Three core records:
  world_cell    — the 16×16 mechanics unit (engine truth)
  world_feature — human-scale grouped structure (editor truth)
  skin_binding  — visual mapping layer (Trixel truth)

Design invariant:
  world_cell must NEVER depend on art.
  It can point to art through skin_id, but it cannot need
  the art to make sense. Mechanics survive skin swaps.
"""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple
from enum import Enum


# ============================================================
# ENUMS — Compact terrain language
# ============================================================

class TerrainType(Enum):
    """Base terrain classification. Compact by design.
    Interesting stuff lives in override_tags, not new terrain types."""
    SAND = "sand"
    SHORELINE = "shoreline"
    SHALLOW_WATER = "shallow_water"
    DEEP_WATER = "deep_water"
    FOREST_EDGE = "forest_edge"
    FOREST_DENSE = "forest_dense"
    TRAIL = "trail"
    PIER = "pier"
    ROCK = "rock"
    CLIFF = "cliff"
    SUBTERRANEAN_FLOOR = "subterranean_floor"
    SUBTERRANEAN_WALL = "subterranean_wall"
    GRASS = "grass"
    DIRT = "dirt"
    STONE_FLOOR = "stone_floor"
    CONSTRUCTION_SITE = "construction_site"
    VOID = "void"  # unassigned / out of bounds


class ElevationClass(Enum):
    SUBTERRANEAN = "subterranean"
    LOW = "low"
    GROUND = "ground"
    RAISED = "raised"
    RIDGE = "ridge"
    CLIFF = "cliff"
    PEAK = "peak"


class WaterClass(Enum):
    NONE = "none"
    SHALLOW = "shallow"
    DEEP = "deep"
    FLOWING = "flowing"


class Concealment(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Confidence(Enum):
    """How the engine knows this fact."""
    EXPLICIT = "explicit"           # directly stated in text
    INFERRED_HIGH = "inferred_high"  # strong corpus evidence
    INFERRED_MEDIUM = "inferred_medium"
    INFERRED_LOW = "inferred_low"   # scene-completion guess


class AutotileRole(Enum):
    """Edge/corner roles for tileset generation."""
    CENTER = "center"
    EDGE_N = "edge_n"
    EDGE_S = "edge_s"
    EDGE_E = "edge_e"
    EDGE_W = "edge_w"
    CORNER_NE = "corner_ne"
    CORNER_NW = "corner_nw"
    CORNER_SE = "corner_se"
    CORNER_SW = "corner_sw"
    INNER_NE = "inner_ne"
    INNER_NW = "inner_nw"
    INNER_SE = "inner_se"
    INNER_SW = "inner_sw"
    PATH_STRAIGHT_H = "path_straight_h"
    PATH_STRAIGHT_V = "path_straight_v"
    PATH_TURN_NE = "path_turn_ne"
    PATH_TURN_NW = "path_turn_nw"
    PATH_TURN_SE = "path_turn_se"
    PATH_TURN_SW = "path_turn_sw"
    PATH_END_N = "path_end_n"
    PATH_END_S = "path_end_s"
    PATH_END_E = "path_end_e"
    PATH_END_W = "path_end_w"
    PATH_CROSS = "path_cross"
    PATH_T_N = "path_t_n"
    PATH_T_S = "path_t_s"
    PATH_T_E = "path_t_e"
    PATH_T_W = "path_t_w"
    SINGLE = "single"  # isolated tile, no neighbors of same type


# ============================================================
# IMMUTABLE DATA STRUCTURES
# ============================================================

@dataclass(frozen=True)
class WorldCell:
    """The atomic 16×16 mechanics unit.

    This is engine truth. It does NOT depend on art.
    skin_id is a pointer, not a dependency.

    Rule: defaults describe the terrain.
          Interesting stuff lives in override_tags.
    """
    cell_id: str                    # stable: "cx_034_cy_012"
    x: int                          # grid column
    y: int                          # grid row
    tile_size: int = 16             # pixels per cell side

    # --- Terrain semantics ---
    terrain_type: str = TerrainType.VOID.value
    elevation_class: str = ElevationClass.GROUND.value
    walkable: bool = True
    movement_cost: float = 1.0      # 1.0 = normal, >1 = slow, 0 = impassable
    blocker: bool = False
    concealment: str = Concealment.NONE.value
    water_class: str = WaterClass.NONE.value
    buildable: bool = False

    # --- Grouping ---
    feature_ids: Tuple[str, ...] = ()   # one cell can belong to multiple features
    override_tags: Tuple[str, ...] = ()  # "secret_path", "ritual_gate", "giant_only"
    socket_ids: Tuple[str, ...] = ()     # spawn, interaction, prop, patrol anchor

    # --- Visual binding (pointer only) ---
    skin_id: str = ""               # key into skin_binding table
    variant_seed: int = 0           # visual variation without mechanics change

    # --- Dynamic state ---
    state_flags: Tuple[str, ...] = ()  # "revealed", "flooded", "collapsed", "burning"

    def with_terrain(self, terrain_type: str, **overrides) -> 'WorldCell':
        """Immutable update: change terrain and related fields."""
        defaults = TERRAIN_DEFAULTS.get(terrain_type, {})
        merged = {**defaults, **overrides}
        return WorldCell(
            cell_id=self.cell_id,
            x=self.x,
            y=self.y,
            tile_size=self.tile_size,
            terrain_type=terrain_type,
            elevation_class=merged.get("elevation_class", self.elevation_class),
            walkable=merged.get("walkable", self.walkable),
            movement_cost=merged.get("movement_cost", self.movement_cost),
            blocker=merged.get("blocker", self.blocker),
            concealment=merged.get("concealment", self.concealment),
            water_class=merged.get("water_class", self.water_class),
            buildable=merged.get("buildable", self.buildable),
            feature_ids=self.feature_ids,
            override_tags=self.override_tags,
            socket_ids=self.socket_ids,
            skin_id=merged.get("skin_id", self.skin_id),
            variant_seed=self.variant_seed,
            state_flags=self.state_flags,
        )

    def with_override(self, tag: str) -> 'WorldCell':
        """Add an override tag (e.g., secret_path)."""
        if tag in self.override_tags:
            return self
        return WorldCell(
            cell_id=self.cell_id, x=self.x, y=self.y,
            tile_size=self.tile_size,
            terrain_type=self.terrain_type,
            elevation_class=self.elevation_class,
            walkable=self.walkable,
            movement_cost=self.movement_cost,
            blocker=self.blocker,
            concealment=self.concealment,
            water_class=self.water_class,
            buildable=self.buildable,
            feature_ids=self.feature_ids,
            override_tags=(*self.override_tags, tag),
            socket_ids=self.socket_ids,
            skin_id=self.skin_id,
            variant_seed=self.variant_seed,
            state_flags=self.state_flags,
        )

    def with_skin(self, skin_id: str) -> 'WorldCell':
        """Swap visual binding. Mechanics untouched."""
        return WorldCell(
            cell_id=self.cell_id, x=self.x, y=self.y,
            tile_size=self.tile_size,
            terrain_type=self.terrain_type,
            elevation_class=self.elevation_class,
            walkable=self.walkable,
            movement_cost=self.movement_cost,
            blocker=self.blocker,
            concealment=self.concealment,
            water_class=self.water_class,
            buildable=self.buildable,
            feature_ids=self.feature_ids,
            override_tags=self.override_tags,
            socket_ids=self.socket_ids,
            skin_id=skin_id,
            variant_seed=self.variant_seed,
            state_flags=self.state_flags,
        )

    def with_feature(self, feature_id: str) -> 'WorldCell':
        """Assign cell to a feature group."""
        if feature_id in self.feature_ids:
            return self
        return WorldCell(
            cell_id=self.cell_id, x=self.x, y=self.y,
            tile_size=self.tile_size,
            terrain_type=self.terrain_type,
            elevation_class=self.elevation_class,
            walkable=self.walkable,
            movement_cost=self.movement_cost,
            blocker=self.blocker,
            concealment=self.concealment,
            water_class=self.water_class,
            buildable=self.buildable,
            feature_ids=(*self.feature_ids, feature_id),
            override_tags=self.override_tags,
            socket_ids=self.socket_ids,
            skin_id=self.skin_id,
            variant_seed=self.variant_seed,
            state_flags=self.state_flags,
        )


@dataclass(frozen=True)
class WorldFeature:
    """Human-scale grouped structure.

    A feature is what the editor shows: "tree_line_north",
    "pier_main", "secret_path_01". It spans multiple cells
    and carries grouped mechanics and narrative provenance.
    """
    feature_id: str                  # "tree_line_north_01"
    feature_type: str                # "tree_line", "shoreline", "trail", etc.
    cell_ids: Tuple[str, ...] = ()   # member cells

    # --- Grouped mechanics ---
    default_rules: Tuple[Tuple[str, str], ...] = ()
    # e.g., (("walkable", "false"), ("blocker", "true"))

    override_rules: Tuple[Tuple[str, str], ...] = ()
    # e.g., (("secret_path", "walkable=true,concealment=high"),)

    # --- Provenance ---
    narrative_source: str = ""       # chapter ref or corpus inference
    confidence: str = Confidence.INFERRED_MEDIUM.value

    # --- Activation ---
    activation_conditions: Tuple[str, ...] = ()
    # e.g., ("chapter_3_revealed", "player_has_map")

    def with_cells(self, cell_ids: Tuple[str, ...]) -> 'WorldFeature':
        """Immutable update: set member cells."""
        return WorldFeature(
            feature_id=self.feature_id,
            feature_type=self.feature_type,
            cell_ids=cell_ids,
            default_rules=self.default_rules,
            override_rules=self.override_rules,
            narrative_source=self.narrative_source,
            confidence=self.confidence,
            activation_conditions=self.activation_conditions,
        )


@dataclass(frozen=True)
class SkinBinding:
    """Visual mapping layer — Trixel's contract.

    Maps a terrain_type + style to the actual visual module.
    This is what Trixel generates: tile assets keyed by
    skin_id with autotile variants.
    """
    skin_id: str                    # "beach_primordial_v1"
    terrain_type: str               # what semantic type this binds to
    module_family: str              # "sand_base", "shore_edge", "forest_band"
    autotile_role: str = AutotileRole.CENTER.value
    asset_ref: str = ""             # path to visual module / tileset entry
    style_tags: Tuple[str, ...] = ()  # "pixel", "painterly", "industrial"
    supports_variants: bool = True
    variant_count: int = 1          # how many visual variants exist
    variant_rules: str = ""         # weighting or seed behavior


@dataclass(frozen=True)
class WorldGridConfig:
    """Immutable configuration for the world grid kernel."""
    grid_width: int = 64            # cells wide
    grid_height: int = 64           # cells tall
    tile_size: int = 16             # pixels per cell side
    default_terrain: str = TerrainType.VOID.value
    default_skin: str = ""


@dataclass(frozen=True)
class WorldGridState:
    """Immutable world grid snapshot.

    The canonical state of the semantic world.
    cells: Dict[cell_id, WorldCell]
    features: Dict[feature_id, WorldFeature]
    skin_table: Dict[skin_id, SkinBinding]
    """
    cells: Dict[str, dict] = field(default_factory=dict)
    features: Dict[str, dict] = field(default_factory=dict)
    skin_table: Dict[str, dict] = field(default_factory=dict)
    tick: float = 0.0


# ============================================================
# TERRAIN DEFAULTS — Compact base rules
# ============================================================

TERRAIN_DEFAULTS: Dict[str, dict] = {
    TerrainType.SAND.value: {
        "walkable": True, "movement_cost": 1.1, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": True,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.SHORELINE.value: {
        "walkable": True, "movement_cost": 1.3, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.SHALLOW.value, "buildable": False,
        "elevation_class": ElevationClass.LOW.value,
    },
    TerrainType.SHALLOW_WATER.value: {
        "walkable": True, "movement_cost": 2.0, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.SHALLOW.value, "buildable": False,
        "elevation_class": ElevationClass.LOW.value,
    },
    TerrainType.DEEP_WATER.value: {
        "walkable": False, "movement_cost": 0.0, "blocker": True,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.DEEP.value, "buildable": False,
        "elevation_class": ElevationClass.LOW.value,
    },
    TerrainType.FOREST_EDGE.value: {
        "walkable": False, "movement_cost": 0.0, "blocker": True,
        "concealment": Concealment.MEDIUM.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.FOREST_DENSE.value: {
        "walkable": False, "movement_cost": 0.0, "blocker": True,
        "concealment": Concealment.HIGH.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.TRAIL.value: {
        "walkable": True, "movement_cost": 0.8, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.PIER.value: {
        "walkable": True, "movement_cost": 1.0, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.RAISED.value,
    },
    TerrainType.ROCK.value: {
        "walkable": False, "movement_cost": 0.0, "blocker": True,
        "concealment": Concealment.LOW.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.RAISED.value,
    },
    TerrainType.CLIFF.value: {
        "walkable": False, "movement_cost": 0.0, "blocker": True,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.CLIFF.value,
    },
    TerrainType.SUBTERRANEAN_FLOOR.value: {
        "walkable": True, "movement_cost": 1.2, "blocker": False,
        "concealment": Concealment.LOW.value,
        "water_class": WaterClass.NONE.value, "buildable": True,
        "elevation_class": ElevationClass.SUBTERRANEAN.value,
    },
    TerrainType.SUBTERRANEAN_WALL.value: {
        "walkable": False, "movement_cost": 0.0, "blocker": True,
        "concealment": Concealment.HIGH.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.SUBTERRANEAN.value,
    },
    TerrainType.GRASS.value: {
        "walkable": True, "movement_cost": 1.0, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": True,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.DIRT.value: {
        "walkable": True, "movement_cost": 1.0, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": True,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.STONE_FLOOR.value: {
        "walkable": True, "movement_cost": 0.9, "blocker": False,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": True,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.CONSTRUCTION_SITE.value: {
        "walkable": True, "movement_cost": 1.5, "blocker": False,
        "concealment": Concealment.LOW.value,
        "water_class": WaterClass.NONE.value, "buildable": True,
        "elevation_class": ElevationClass.GROUND.value,
    },
    TerrainType.VOID.value: {
        "walkable": False, "movement_cost": 0.0, "blocker": True,
        "concealment": Concealment.NONE.value,
        "water_class": WaterClass.NONE.value, "buildable": False,
        "elevation_class": ElevationClass.GROUND.value,
    },
}


# ============================================================
# PURE UTILITY FUNCTIONS
# ============================================================

def make_cell_id(x: int, y: int) -> str:
    """Deterministic cell ID from grid coordinates."""
    return f"cx_{x:03d}_cy_{y:03d}"


def create_empty_grid(config: WorldGridConfig) -> Dict[str, dict]:
    """Generate a blank grid of void cells. Pure function."""
    cells = {}
    for y in range(config.grid_height):
        for x in range(config.grid_width):
            cid = make_cell_id(x, y)
            cell = WorldCell(
                cell_id=cid, x=x, y=y,
                tile_size=config.tile_size,
                terrain_type=config.default_terrain,
                skin_id=config.default_skin,
            )
            cells[cid] = _cell_to_dict(cell)
    return cells


def _cell_to_dict(cell: WorldCell) -> dict:
    """Serialize a frozen WorldCell to a plain dict for state storage."""
    return {
        "cell_id": cell.cell_id, "x": cell.x, "y": cell.y,
        "tile_size": cell.tile_size,
        "terrain_type": cell.terrain_type,
        "elevation_class": cell.elevation_class,
        "walkable": cell.walkable,
        "movement_cost": cell.movement_cost,
        "blocker": cell.blocker,
        "concealment": cell.concealment,
        "water_class": cell.water_class,
        "buildable": cell.buildable,
        "feature_ids": list(cell.feature_ids),
        "override_tags": list(cell.override_tags),
        "socket_ids": list(cell.socket_ids),
        "skin_id": cell.skin_id,
        "variant_seed": cell.variant_seed,
        "state_flags": list(cell.state_flags),
    }


def _dict_to_cell(d: dict) -> WorldCell:
    """Deserialize a dict back to a frozen WorldCell."""
    return WorldCell(
        cell_id=d["cell_id"], x=d["x"], y=d["y"],
        tile_size=d.get("tile_size", 16),
        terrain_type=d.get("terrain_type", TerrainType.VOID.value),
        elevation_class=d.get("elevation_class", ElevationClass.GROUND.value),
        walkable=d.get("walkable", False),
        movement_cost=d.get("movement_cost", 0.0),
        blocker=d.get("blocker", True),
        concealment=d.get("concealment", Concealment.NONE.value),
        water_class=d.get("water_class", WaterClass.NONE.value),
        buildable=d.get("buildable", False),
        feature_ids=tuple(d.get("feature_ids", [])),
        override_tags=tuple(d.get("override_tags", [])),
        socket_ids=tuple(d.get("socket_ids", [])),
        skin_id=d.get("skin_id", ""),
        variant_seed=d.get("variant_seed", 0),
        state_flags=tuple(d.get("state_flags", [])),
    )


def _feature_to_dict(feat: WorldFeature) -> dict:
    return {
        "feature_id": feat.feature_id,
        "feature_type": feat.feature_type,
        "cell_ids": list(feat.cell_ids),
        "default_rules": [list(r) for r in feat.default_rules],
        "override_rules": [list(r) for r in feat.override_rules],
        "narrative_source": feat.narrative_source,
        "confidence": feat.confidence,
        "activation_conditions": list(feat.activation_conditions),
    }


def _skin_to_dict(skin: SkinBinding) -> dict:
    return {
        "skin_id": skin.skin_id,
        "terrain_type": skin.terrain_type,
        "module_family": skin.module_family,
        "autotile_role": skin.autotile_role,
        "asset_ref": skin.asset_ref,
        "style_tags": list(skin.style_tags),
        "supports_variants": skin.supports_variants,
        "variant_count": skin.variant_count,
        "variant_rules": skin.variant_rules,
    }


def get_neighbors(x: int, y: int, grid_w: int, grid_h: int) -> Dict[str, Optional[str]]:
    """Return neighbor cell_ids for autotile resolution. Pure."""
    dirs = {
        "n":  (x, y - 1), "s":  (x, y + 1),
        "e":  (x + 1, y), "w":  (x - 1, y),
        "ne": (x + 1, y - 1), "nw": (x - 1, y - 1),
        "se": (x + 1, y + 1), "sw": (x - 1, y + 1),
    }
    result = {}
    for direction, (nx, ny) in dirs.items():
        if 0 <= nx < grid_w and 0 <= ny < grid_h:
            result[direction] = make_cell_id(nx, ny)
        else:
            result[direction] = None
    return result


def resolve_autotile_role(
    cell_terrain: str,
    neighbor_terrains: Dict[str, Optional[str]]
) -> str:
    """Determine autotile role from neighbor terrain types. Pure.

    This is the core of edge/corner resolution for tileset generation.
    Trixel uses this to know which tile variant to produce.
    """
    same = set()
    for d in ("n", "s", "e", "w"):
        if neighbor_terrains.get(d) == cell_terrain:
            same.add(d)

    # Cardinal neighbor matching
    has_n = "n" in same
    has_s = "s" in same
    has_e = "e" in same
    has_w = "w" in same

    count = len(same)

    if count == 0:
        return AutotileRole.SINGLE.value
    if count == 4:
        return AutotileRole.CENTER.value

    # Edges (3 same neighbors)
    if count == 3:
        if not has_n: return AutotileRole.EDGE_N.value
        if not has_s: return AutotileRole.EDGE_S.value
        if not has_e: return AutotileRole.EDGE_E.value
        if not has_w: return AutotileRole.EDGE_W.value

    # Corners (2 adjacent same neighbors)
    if count == 2:
        if has_s and has_e: return AutotileRole.CORNER_NW.value
        if has_s and has_w: return AutotileRole.CORNER_NE.value
        if has_n and has_e: return AutotileRole.CORNER_SW.value
        if has_n and has_w: return AutotileRole.CORNER_SE.value
        # Straight paths
        if has_n and has_s: return AutotileRole.PATH_STRAIGHT_V.value
        if has_e and has_w: return AutotileRole.PATH_STRAIGHT_H.value

    # One neighbor = end cap
    if count == 1:
        if has_n: return AutotileRole.PATH_END_S.value
        if has_s: return AutotileRole.PATH_END_N.value
        if has_e: return AutotileRole.PATH_END_W.value
        if has_w: return AutotileRole.PATH_END_E.value

    return AutotileRole.CENTER.value  # fallback


def resolve_cell_walkability(cell_dict: dict) -> bool:
    """Resolve effective walkability considering overrides. Pure.

    A cell that is normally blocked (e.g., forest_edge) can become
    walkable if it has a 'secret_path' override tag.
    """
    base_walkable = cell_dict.get("walkable", False)
    overrides = cell_dict.get("override_tags", [])

    # Override tags that grant walkability
    WALKABLE_OVERRIDES = {"secret_path", "ritual_gate", "hidden_passage", "forced_path"}
    # Override tags that revoke walkability
    BLOCKING_OVERRIDES = {"collapsed", "barricade", "sealed"}

    if any(tag in BLOCKING_OVERRIDES for tag in overrides):
        return False
    if any(tag in WALKABLE_OVERRIDES for tag in overrides):
        return True

    # Dynamic state flags
    state_flags = cell_dict.get("state_flags", [])
    if "collapsed" in state_flags or "flooded" in state_flags:
        return False

    return base_walkable


# ============================================================
# CORE KERNEL — snapshot-in → snapshot-out
# ============================================================

def step_trixel_world(
    snapshot_in: dict,
    deltas: List[dict],
    config: WorldGridConfig,
    delta_time: float = 0.0
) -> Tuple[dict, List[str], List[dict]]:
    """
    Pure functional step for the Trixel World grid.

    Args:
        snapshot_in:  {"trixel_world": {"cells": {...}, "features": {...},
                       "skin_table": {...}, "tick": float}}
        deltas:       List of queued changes
        config:       Immutable grid configuration
        delta_time:   Time step (mostly unused for terrain, but needed
                      for state_flag timers like burning duration)

    Returns:
        (snapshot_out, accepted_delta_ids, alerts)

    Delta types:
        "set_terrain"     — change terrain type on cell(s)
        "set_skin"        — change visual binding on cell(s)
        "add_override"    — add override tag to cell(s)
        "remove_override" — remove override tag from cell(s)
        "add_feature"     — register a world feature
        "assign_feature"  — assign cells to an existing feature
        "set_state_flag"  — add dynamic state flag
        "clear_state_flag"— remove dynamic state flag
        "register_skin"   — add a skin binding to the table
        "fill_region"     — bulk set terrain for a rectangular region
    """
    world = snapshot_in.get("trixel_world", {})
    cells = dict(world.get("cells", {}))         # mutable working copy
    features = dict(world.get("features", {}))
    skin_table = dict(world.get("skin_table", {}))
    tick = world.get("tick", 0.0)

    accepted_ids = []
    alerts = []

    for delta in deltas:
        d_id = delta.get("id", "unknown")
        d_type = delta.get("type", "")
        payload = delta.get("payload", {})

        try:
            if d_type == "set_terrain":
                terrain = payload["terrain_type"]
                for cid in payload.get("cell_ids", []):
                    if cid in cells:
                        cell = _dict_to_cell(cells[cid])
                        cell = cell.with_terrain(terrain)
                        cells[cid] = _cell_to_dict(cell)
                accepted_ids.append(d_id)

            elif d_type == "set_skin":
                sid = payload["skin_id"]
                for cid in payload.get("cell_ids", []):
                    if cid in cells:
                        cell = _dict_to_cell(cells[cid])
                        cell = cell.with_skin(sid)
                        cells[cid] = _cell_to_dict(cell)
                accepted_ids.append(d_id)

            elif d_type == "add_override":
                tag = payload["tag"]
                for cid in payload.get("cell_ids", []):
                    if cid in cells:
                        cell = _dict_to_cell(cells[cid])
                        cell = cell.with_override(tag)
                        cells[cid] = _cell_to_dict(cell)
                accepted_ids.append(d_id)

            elif d_type == "remove_override":
                tag = payload["tag"]
                for cid in payload.get("cell_ids", []):
                    if cid in cells:
                        c = cells[cid]
                        tags = [t for t in c.get("override_tags", []) if t != tag]
                        c = {**c, "override_tags": tags}
                        cells[cid] = c
                accepted_ids.append(d_id)

            elif d_type == "add_feature":
                feat = WorldFeature(
                    feature_id=payload["feature_id"],
                    feature_type=payload.get("feature_type", "unknown"),
                    cell_ids=tuple(payload.get("cell_ids", [])),
                    narrative_source=payload.get("narrative_source", ""),
                    confidence=payload.get("confidence", Confidence.INFERRED_MEDIUM.value),
                )
                features[feat.feature_id] = _feature_to_dict(feat)
                # Tag member cells
                for cid in feat.cell_ids:
                    if cid in cells:
                        cell = _dict_to_cell(cells[cid])
                        cell = cell.with_feature(feat.feature_id)
                        cells[cid] = _cell_to_dict(cell)
                accepted_ids.append(d_id)

            elif d_type == "assign_feature":
                fid = payload["feature_id"]
                new_cells = payload.get("cell_ids", [])
                if fid in features:
                    f = features[fid]
                    existing = list(f.get("cell_ids", []))
                    for cid in new_cells:
                        if cid not in existing:
                            existing.append(cid)
                        if cid in cells:
                            cell = _dict_to_cell(cells[cid])
                            cell = cell.with_feature(fid)
                            cells[cid] = _cell_to_dict(cell)
                    f = {**f, "cell_ids": existing}
                    features[fid] = f
                accepted_ids.append(d_id)

            elif d_type == "set_state_flag":
                flag = payload["flag"]
                for cid in payload.get("cell_ids", []):
                    if cid in cells:
                        c = cells[cid]
                        flags = list(c.get("state_flags", []))
                        if flag not in flags:
                            flags.append(flag)
                        cells[cid] = {**c, "state_flags": flags}
                accepted_ids.append(d_id)

            elif d_type == "clear_state_flag":
                flag = payload["flag"]
                for cid in payload.get("cell_ids", []):
                    if cid in cells:
                        c = cells[cid]
                        flags = [f for f in c.get("state_flags", []) if f != flag]
                        cells[cid] = {**c, "state_flags": flags}
                accepted_ids.append(d_id)

            elif d_type == "register_skin":
                skin = SkinBinding(
                    skin_id=payload["skin_id"],
                    terrain_type=payload.get("terrain_type", ""),
                    module_family=payload.get("module_family", ""),
                    autotile_role=payload.get("autotile_role", AutotileRole.CENTER.value),
                    asset_ref=payload.get("asset_ref", ""),
                    style_tags=tuple(payload.get("style_tags", [])),
                    supports_variants=payload.get("supports_variants", True),
                    variant_count=payload.get("variant_count", 1),
                )
                skin_table[skin.skin_id] = _skin_to_dict(skin)
                accepted_ids.append(d_id)

            elif d_type == "fill_region":
                terrain = payload["terrain_type"]
                x0, y0 = payload["x_min"], payload["y_min"]
                x1, y1 = payload["x_max"], payload["y_max"]
                skin_id = payload.get("skin_id", "")
                for gy in range(y0, y1 + 1):
                    for gx in range(x0, x1 + 1):
                        cid = make_cell_id(gx, gy)
                        if cid in cells:
                            cell = _dict_to_cell(cells[cid])
                            cell = cell.with_terrain(terrain)
                            if skin_id:
                                cell = cell.with_skin(skin_id)
                            cells[cid] = _cell_to_dict(cell)
                accepted_ids.append(d_id)

            else:
                alerts.append({
                    "level": "WARN",
                    "code": "unknown_delta_type",
                    "message": f"Unknown delta type: {d_type}",
                    "delta_id": d_id,
                })

        except (KeyError, TypeError, ValueError) as e:
            alerts.append({
                "level": "ERROR",
                "code": "delta_processing_error",
                "message": str(e),
                "delta_id": d_id,
            })

    snapshot_out = {
        "trixel_world": {
            "cells": cells,
            "features": features,
            "skin_table": skin_table,
            "tick": tick + delta_time,
        }
    }

    return snapshot_out, accepted_ids, alerts


# ============================================================
# QUERY FUNCTIONS — Pure read-only accessors
# ============================================================

def get_walkable_cells(cells: Dict[str, dict]) -> List[str]:
    """Return IDs of all effectively walkable cells."""
    return [cid for cid, c in cells.items() if resolve_cell_walkability(c)]


def get_cells_by_terrain(cells: Dict[str, dict], terrain_type: str) -> List[str]:
    """Return IDs of cells matching a terrain type."""
    return [cid for cid, c in cells.items() if c.get("terrain_type") == terrain_type]


def get_cells_by_feature(cells: Dict[str, dict], feature_id: str) -> List[str]:
    """Return IDs of cells belonging to a feature."""
    return [cid for cid, c in cells.items() if feature_id in c.get("feature_ids", [])]


def get_skin_for_cell(
    cell_dict: dict,
    skin_table: Dict[str, dict],
    neighbor_terrains: Dict[str, Optional[str]]
) -> Optional[dict]:
    """Resolve the full skin binding for a cell, including autotile role.

    This is what the renderer calls to know which visual module to use.
    """
    sid = cell_dict.get("skin_id", "")
    if not sid or sid not in skin_table:
        return None

    base_skin = skin_table[sid]
    # Resolve autotile role from neighbors
    role = resolve_autotile_role(
        cell_dict.get("terrain_type", ""),
        neighbor_terrains
    )

    return {**base_skin, "resolved_autotile_role": role}


def compute_grid_statistics(cells: Dict[str, dict]) -> dict:
    """Compute summary statistics for a world grid. Pure."""
    total = len(cells)
    walkable = sum(1 for c in cells.values() if resolve_cell_walkability(c))
    blocked = sum(1 for c in cells.values() if c.get("blocker", False))
    terrain_counts = {}
    for c in cells.values():
        t = c.get("terrain_type", "void")
        terrain_counts[t] = terrain_counts.get(t, 0) + 1

    return {
        "total_cells": total,
        "walkable_cells": walkable,
        "blocked_cells": blocked,
        "walkable_pct": round(walkable / max(total, 1) * 100, 1),
        "terrain_distribution": terrain_counts,
    }


# ============================================================
# EXAMPLE: Build a beach scene
# ============================================================

def build_example_beach(config: WorldGridConfig = None) -> dict:
    """
    Demonstrate the contract with a tiny beach scene.
    Pure function — returns a complete world snapshot.

    Layout (16×16 grid):
        Rows 0-2:   deep_water
        Rows 3-4:   shallow_water
        Row  5:     shoreline
        Rows 6-10:  sand (with pier column 8-9)
        Rows 11-13: grass
        Rows 14-15: forest_edge (with secret_path at col 7)
    """
    if config is None:
        config = WorldGridConfig(grid_width=16, grid_height=16, tile_size=16)

    cells = create_empty_grid(config)

    # --- Terrain fill ---
    terrain_bands = [
        (range(0, 3),   TerrainType.DEEP_WATER.value),
        (range(3, 5),   TerrainType.SHALLOW_WATER.value),
        (range(5, 6),   TerrainType.SHORELINE.value),
        (range(6, 11),  TerrainType.SAND.value),
        (range(11, 14), TerrainType.GRASS.value),
        (range(14, 16), TerrainType.FOREST_EDGE.value),
    ]

    for row_range, terrain in terrain_bands:
        for y in row_range:
            for x in range(config.grid_width):
                cid = make_cell_id(x, y)
                if cid in cells:
                    cell = _dict_to_cell(cells[cid])
                    cell = cell.with_terrain(terrain)
                    cells[cid] = _cell_to_dict(cell)

    # --- Pier feature (columns 8-9, rows 3-8) ---
    pier_cells = []
    for y in range(3, 9):
        for x in (8, 9):
            cid = make_cell_id(x, y)
            if cid in cells:
                cell = _dict_to_cell(cells[cid])
                cell = cell.with_terrain(TerrainType.PIER.value)
                pier_cells.append(cid)
                cells[cid] = _cell_to_dict(cell)

    pier_feature = WorldFeature(
        feature_id="pier_main",
        feature_type="pier",
        cell_ids=tuple(pier_cells),
        default_rules=(("walkable", "true"), ("movement_cost", "1.0")),
        narrative_source="chapter_01",
        confidence=Confidence.EXPLICIT.value,
    )

    # --- Secret path through forest (col 7, rows 14-15) ---
    secret_cells = []
    for y in (14, 15):
        cid = make_cell_id(7, y)
        if cid in cells:
            cell = _dict_to_cell(cells[cid])
            cell = cell.with_override("secret_path")
            secret_cells.append(cid)
            cells[cid] = _cell_to_dict(cell)

    secret_feature = WorldFeature(
        feature_id="secret_path_01",
        feature_type="hidden_path",
        cell_ids=tuple(secret_cells),
        override_rules=(("secret_path", "walkable=true,concealment=high"),),
        narrative_source="chapter_03",
        confidence=Confidence.EXPLICIT.value,
        activation_conditions=("chapter_3_revealed",),
    )

    # --- Construction site (sand area, cols 4-6, rows 7-9) ---
    construction_cells = []
    for y in range(7, 10):
        for x in range(4, 7):
            cid = make_cell_id(x, y)
            if cid in cells:
                cell = _dict_to_cell(cells[cid])
                cell = cell.with_terrain(TerrainType.CONSTRUCTION_SITE.value)
                construction_cells.append(cid)
                cells[cid] = _cell_to_dict(cell)

    construction_feature = WorldFeature(
        feature_id="pyramid_site_01",
        feature_type="construction_zone",
        cell_ids=tuple(construction_cells),
        narrative_source="corpus_wide",
        confidence=Confidence.EXPLICIT.value,
    )

    # --- Skin bindings ---
    skin_table = {}
    for terrain in TerrainType:
        sid = f"default_{terrain.value}_v1"
        skin = SkinBinding(
            skin_id=sid,
            terrain_type=terrain.value,
            module_family=f"{terrain.value}_base",
            style_tags=("pixel", "primordial"),
        )
        skin_table[sid] = _skin_to_dict(skin)

    # Apply default skins to all cells
    for cid in cells:
        c = cells[cid]
        terrain = c.get("terrain_type", TerrainType.VOID.value)
        c["skin_id"] = f"default_{terrain}_v1"
        cells[cid] = c

    features = {
        "pier_main": _feature_to_dict(pier_feature),
        "secret_path_01": _feature_to_dict(secret_feature),
        "pyramid_site_01": _feature_to_dict(construction_feature),
    }

    return {
        "trixel_world": {
            "cells": cells,
            "features": features,
            "skin_table": skin_table,
            "tick": 0.0,
        }
    }


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("TRIXEL WORLD MR KERNEL — Contract Validation")
    print("=" * 60)

    # Build example scene
    config = WorldGridConfig(grid_width=16, grid_height=16, tile_size=16)
    snapshot = build_example_beach(config)
    world = snapshot["trixel_world"]

    # Statistics
    stats = compute_grid_statistics(world["cells"])
    print(f"\nGrid: {config.grid_width}×{config.grid_height} = {stats['total_cells']} cells")
    print(f"Walkable: {stats['walkable_cells']} ({stats['walkable_pct']}%)")
    print(f"Blocked:  {stats['blocked_cells']}")
    print(f"\nTerrain distribution:")
    for terrain, count in sorted(stats["terrain_distribution"].items()):
        print(f"  {terrain:25s} {count:4d} cells")

    # Features
    print(f"\nFeatures: {len(world['features'])}")
    for fid, feat in world["features"].items():
        print(f"  {fid}: {feat['feature_type']} ({len(feat['cell_ids'])} cells, "
              f"confidence={feat['confidence']})")

    # Skin table
    print(f"\nSkin bindings: {len(world['skin_table'])}")

    # Test secret path walkability
    secret_cell_id = make_cell_id(7, 14)
    secret_cell = world["cells"][secret_cell_id]
    print(f"\nSecret path cell {secret_cell_id}:")
    print(f"  terrain_type:   {secret_cell['terrain_type']}")
    print(f"  base walkable:  {secret_cell['walkable']}")
    print(f"  override_tags:  {secret_cell['override_tags']}")
    print(f"  EFFECTIVE walk: {resolve_cell_walkability(secret_cell)}")

    # Test a normal forest cell (should be blocked)
    normal_forest = make_cell_id(5, 14)
    normal_cell = world["cells"][normal_forest]
    print(f"\nNormal forest cell {normal_forest}:")
    print(f"  terrain_type:   {normal_cell['terrain_type']}")
    print(f"  base walkable:  {normal_cell['walkable']}")
    print(f"  EFFECTIVE walk: {resolve_cell_walkability(normal_cell)}")

    # Test autotile resolution
    pier_cell_id = make_cell_id(8, 5)
    neighbors = get_neighbors(8, 5, config.grid_width, config.grid_height)
    neighbor_terrains = {}
    for d, ncid in neighbors.items():
        if ncid and ncid in world["cells"]:
            neighbor_terrains[d] = world["cells"][ncid].get("terrain_type")
        else:
            neighbor_terrains[d] = None
    role = resolve_autotile_role(
        world["cells"][pier_cell_id]["terrain_type"],
        neighbor_terrains
    )
    print(f"\nAutotile: cell {pier_cell_id} (pier) → role={role}")

    # Test delta: swap all sand to factory skin
    deltas = [{
        "id": "reskin_sand_001",
        "type": "set_skin",
        "payload": {
            "skin_id": "factory_floor_v1",
            "cell_ids": get_cells_by_terrain(world["cells"], TerrainType.SAND.value),
        }
    }]

    snapshot_out, accepted, alerts = step_trixel_world(
        snapshot, deltas, config
    )

    print(f"\nDelta test: reskin sand → factory_floor_v1")
    print(f"  Accepted: {accepted}")
    print(f"  Alerts:   {alerts}")

    # Verify mechanics survived the skin swap
    # Pick a cell that is definitely sand (col 2, row 8 — outside construction zone)
    reskinned_cell = snapshot_out["trixel_world"]["cells"][make_cell_id(2, 8)]
    print(f"  Reskinned cell terrain: {reskinned_cell['terrain_type']} (should still be sand)")
    print(f"  Reskinned cell skin:    {reskinned_cell['skin_id']} (should be factory_floor_v1)")
    print(f"  Reskinned cell walkable:{reskinned_cell['walkable']} (should still be True)")

    print("\n" + "=" * 60)
    print("CONTRACT VALIDATION COMPLETE")
    print("=" * 60)






Trixel applications and functionality - Claude
