"""
world_tree_mr.py — Trixel Tree Visual System  v4  (Gfig-backed generation)

V4 replaces invented branch heuristics with authored curve guides.

Each species has a Gfig scaffold file in data/gfig/:
    oak_scaffold   — broad rounded arcs, two main crown layers
    pine_scaffold  — tiered horizontal boughs narrowing to apex
    birch_scaffold — slender drooping arcs, slight lean
    dead_scaffold  — sparse angular stubs, no organic flow

The Gfig curves are sampled into point sequences, normalised to [0,1],
then scaled into the tree's actual world-space geometry at render time.
Those points feed the influence field — they are NEVER rendered directly.

Visible improvement targets for V4:
    oak:   stronger crown silhouette, real interior gaps, no cloud
    pine:  layered boughs, not ladder rungs
    birch: droop and airy gaps from authored arcs, not random
    dead:  clean angular branching, trunk-as-structure not trunk-as-block

Asset discovery:
    data/ is resolved relative to this file's location.
    No hardcoded /usr/share/... paths in the module body.
    Scripts discover GIMP data from DATA_ROOT (data/ sibling folders).

Rendering passes (same as V3, scaffold replaced):
    1. shadow_mass  — field-sampled, inside shifted ellipse
    2. bark         — directional trunk grain, upward
    3. leaf_mass    — influence-field sampled, envelope-gated
    4. canopy_edge  — perimeter ring, thinner threshold
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    surface_behavior_mr.py      (Same Folder)
#                     trixel_recipes_mr.py        (Same Folder)
#                     trixel_brush_adapter.py     (Same Folder)
#                     engine_mr.py                (Same Folder)
#                     engine_debug_mr.py          (Same Folder)
#                     brushes/gfig_parser_mr.py   (Different Folder: brushes/)
# This file is called by: trixel_demo_mr.py       (Same Folder)
#                          __main__ (CLI direct execution)
# ---------------------------------------------------------------------------

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from surface_behavior_mr import (
    TREE_BARK, TREE_SHADOW_MASS, TREE_LEAF_MASS, TREE_CANOPY_EDGE,
    SurfaceBehavior,
)
from trixel_recipes_mr import build

if TYPE_CHECKING:
    from trixel_brush_adapter import AssetRegistry
    from engine_mr import SurfaceBuffer

# ---------------------------------------------------------------------------
# Data root discovery — relative to this file, not hardcoded
# ---------------------------------------------------------------------------

_HERE      = Path(__file__).parent           # data/
_GFIG_DIR  = _HERE / "gfig"                 # data/gfig/


def _find_gimp_data() -> Optional[Path]:
    """
    Find an asset root containing at least brushes/, dynamics/, and palettes/.
    Callers that pass gimp_root explicitly bypass this entirely.
    """
    candidates = [
        # Project-local roots
        _HERE / "data",           # if script lives in trixelworld/
        _HERE.parent / "data",    # if script lives in trixelworld/brushes/ or similar
        _HERE,                    # if script itself lives inside an extracted data/ bundle

        # Stock/system roots
        Path("/usr/share/gimp/3.0"),
        Path("/usr/local/share/gimp/3.0"),
        Path("/usr/share/gimp/2.0"),
        Path("/usr/local/share/gimp/2.0"),

        # User-local installs
        Path.home() / ".config" / "GIMP" / "3.0",
        Path.home() / ".config" / "GIMP" / "2.10",
        Path.home() / ".gimp-2.10",
    ]

    required = ("brushes", "dynamics", "palettes")

    for c in candidates:
        if c.is_dir() and all((c / sub).is_dir() for sub in required):
            return c

    return None

# ---------------------------------------------------------------------------
# LCG — deterministic
# ---------------------------------------------------------------------------

def _lcg(s: int) -> int:
    return (s * 1664525 + 1013904223) & 0xFFFFFFFF

def _lcg_f(s: int) -> float:
    return _lcg(s) / 0x100000000


# ---------------------------------------------------------------------------
# Scaffold loading — Gfig -> world-space field points
# ---------------------------------------------------------------------------

def _load_scaffold(
    species: str,
    trunk_top_x: float,
    trunk_top_y: float,
    canopy_radius: float,
) -> list[list[tuple[float, float, float]]]:
    """
    Load the Gfig scaffold for a species, sample its curves, and
    map the resulting points into world space.

    Returns a list of branches, where each branch is a list of 
    (world_x, world_y, weight) points.
    """
    from brushes.gfig_parser_mr import parse_gfig, sample_arc, sample_line, normalise

    gfig_path = _GFIG_DIR / f"{species}_scaffold"
    if not gfig_path.exists():
        return []

    fig = parse_gfig(gfig_path)

    CANVAS = 256.0
    ANCHOR_NX = 0.5    # trunk top is at x=128 in template
    ANCHOR_NY = 0.33   # trunk top is at y=85 in template
    SCALE = canopy_radius * 2.2

    branches: list[list[tuple[float, float, float]]] = []

    # Sample arcs — these are the primary branch guides
    for arc in fig.arcs():
        pts = sample_arc(arc, 8)
        norm = normalise(pts, CANVAS, CANVAS)
        branch: list[tuple[float, float, float]] = []
        n = len(norm)
        for i, p in enumerate(norm):
            # Weight peaks at endpoints (i=0, i=n-1), dips at midpoint
            t = i / max(n - 1, 1)
            end_bias = abs(2 * t - 1)    # 1 at endpoints, 0 at midpoint
            w = 0.55 + end_bias * 0.45
            wx = trunk_top_x + (p.x - ANCHOR_NX) * SCALE
            wy = trunk_top_y + (p.y - ANCHOR_NY) * SCALE
            branch.append((wx, wy, w))
        branches.append(branch)

    # Sample lines — trunk guide and branch stubs
    for line in fig.lines():
        pts = sample_line(line, 6)
        norm = normalise(pts, CANVAS, CANVAS)
        branch = []
        for i, p in enumerate(norm):
            t = i / max(len(norm) - 1, 1)
            w = 0.40 + 0.45 * t    # tips of lines = branch endpoints
            wx = trunk_top_x + (p.x - ANCHOR_NX) * SCALE
            wy = trunk_top_y + (p.y - ANCHOR_NY) * SCALE
            branch.append((wx, wy, w))
        branches.append(branch)

    return branches


# ---------------------------------------------------------------------------
# TreeLayerDef
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TreeLayerDef:
    behaviour:    SurfaceBehavior
    recipe_name:  str
    colour:       tuple[int, int, int]
    colour_shift: float
    stamp_budget: int
    density_bias: float


# ---------------------------------------------------------------------------
# TreeDef
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TreeDef:
    """
    Complete visual system declaration for one tree species.

    scaffold_file:   name of data/gfig/<species>_scaffold (without extension)
    influence_reach: how far a scaffold point's weight extends,
                     as fraction of canopy_radius
    """
    name:             str
    label:            str
    trunk_ratio:      float
    taper:            float
    canopy_shape:     str
    canopy_density:   float
    lean_angle:       float
    wind_bias:        Optional[float]
    void_fraction:    float
    influence_reach:  float
    bark_layer:       TreeLayerDef
    shadow_layer:     TreeLayerDef
    leaf_layer:       TreeLayerDef
    edge_layer:       TreeLayerDef
    description:      str


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

_OAK_BARK   = ( 55,  40,  25)
_PINE_BARK  = ( 45,  30,  20)
_BIRCH_BARK = (200, 195, 185)
_DEAD_BARK  = ( 60,  50,  40)
_OAK_LEAF   = ( 38,  78,  28)
_PINE_LEAF  = ( 18,  58,  28)
_BIRCH_LEAF = ( 65, 105,  42)
_SHADOW     = ( 18,  28,  12)


# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

TREE_OAK = TreeDef(
    name="oak", label="Oak Tree",
    trunk_ratio=0.18, taper=0.32,
    canopy_shape="round", canopy_density=0.88,
    lean_angle=0.0, wind_bias=None,
    void_fraction=0.18, influence_reach=0.55,
    bark_layer=TreeLayerDef(TREE_BARK, "charcoal_grain", _OAK_BARK, 0.0, 320, 1.0),
    shadow_layer=TreeLayerDef(TREE_SHADOW_MASS, "oil_smear", _SHADOW, -0.2, 180, 0.88),
    leaf_layer=TreeLayerDef(TREE_LEAF_MASS, "acrylic_variant", _OAK_LEAF, 0.0, 300, 0.88),
    edge_layer=TreeLayerDef(TREE_CANOPY_EDGE, "bristle_rake", _OAK_LEAF, 0.18, 150, 0.52),
    description="Broad rounded crown, thick rough bark, dense clustered foliage.",
)

TREE_PINE = TreeDef(
    name="pine", label="Pine Tree",
    trunk_ratio=0.10, taper=0.55,
    canopy_shape="conical", canopy_density=0.75,
    lean_angle=0.0, wind_bias=None,
    void_fraction=0.10, influence_reach=0.52,
    bark_layer=TreeLayerDef(TREE_BARK, "hatch_texture", _PINE_BARK, 0.0, 280, 1.0),
    shadow_layer=TreeLayerDef(TREE_SHADOW_MASS, "oil_smear", _SHADOW, -0.28, 140, 0.82),
    leaf_layer=TreeLayerDef(TREE_LEAF_MASS, "bristle_rake", _PINE_LEAF, 0.0, 340, 0.80),
    edge_layer=TreeLayerDef(TREE_CANOPY_EDGE, "charcoal_grain", _PINE_LEAF, 0.12, 110, 0.40),
    description="Conical tiered crown, tight dark needle clusters, thin tapering trunk.",
)

TREE_BIRCH = TreeDef(
    name="birch", label="Birch Tree",
    trunk_ratio=0.08, taper=0.45,
    canopy_shape="oval_v", canopy_density=0.58,
    lean_angle=0.08, wind_bias=math.pi * 1.1,
    void_fraction=0.30, influence_reach=0.62,
    bark_layer=TreeLayerDef(TREE_BARK, "hard_pixel", _BIRCH_BARK, 0.0, 220, 1.0),
    shadow_layer=TreeLayerDef(TREE_SHADOW_MASS, "charcoal_grain", _SHADOW, -0.15, 100, 0.68),
    leaf_layer=TreeLayerDef(TREE_LEAF_MASS, "acrylic_variant", _BIRCH_LEAF, 0.0, 210, 0.60),
    edge_layer=TreeLayerDef(TREE_CANOPY_EDGE, "bristle_rake", _BIRCH_LEAF, 0.22, 110, 0.36),
    description="Slender, airy canopy with organic gaps. Pale bark, drooping branch form.",
)

TREE_DEAD = TreeDef(
    name="dead", label="Dead Tree",
    trunk_ratio=0.12, taper=0.60,
    canopy_shape="irregular", canopy_density=0.0,
    lean_angle=0.15, wind_bias=None,
    void_fraction=1.0, influence_reach=0.3,
    bark_layer=TreeLayerDef(TREE_BARK, "hatch_texture", _DEAD_BARK, 0.0, 480, 1.0),
    shadow_layer=TreeLayerDef(TREE_SHADOW_MASS, "charcoal_grain", (28,22,18), -0.1, 50, 0.40),
    leaf_layer=TreeLayerDef(TREE_LEAF_MASS, "charcoal_grain", _DEAD_BARK, 0.1, 0, 0.0),
    edge_layer=TreeLayerDef(TREE_CANOPY_EDGE, "hatch_texture", (48,38,28), 0.0, 0, 0.0),
    description="No foliage. Bare angular stubs. Structural hatch only.",
)

ALL_TREES: dict[str, TreeDef] = {
    t.name: t for t in [TREE_OAK, TREE_PINE, TREE_BIRCH, TREE_DEAD]
}


# ---------------------------------------------------------------------------
# Envelope functions — species outer shape
# ---------------------------------------------------------------------------

def _inside_envelope(
    px: float, py: float,
    cx: float, cy: float,
    rx: float, ry: float,
    top_x: float, top_y: float,
    canopy_radius: float,
    shape: str,
    scale: float,
    seed: int,
) -> bool:
    if shape == "conical":
        dy = py - top_y
        if dy < -canopy_radius * 0.05:
            return False
        tier = dy / max(canopy_radius, 1)
        max_x = canopy_radius * scale * (0.12 + 0.88 * tier)
        return abs(px - top_x) <= max_x

    elif shape == "oval_v":
        dx = (px - cx) / max(rx * scale, 1)
        ry_eff = ry * scale * (1.20 if py > cy else 1.0)
        dy = (py - cy) / max(ry_eff, 1)
        return math.sqrt(dx*dx + dy*dy) < 1.0

    elif shape == "round":
        dx = (px - cx) / max(rx, 1)
        dy = (py - cy) / max(ry, 1)
        dist = math.sqrt(dx*dx + dy*dy)
        angle = math.atan2(dy, dx)
        s = _lcg(int(abs(angle) * 800) & 0xFFFFFFFF ^ seed)
        wobble = (_lcg_f(s) - 0.5) * 0.20
        return dist < (scale + wobble)

    else:  # irregular, oval_h
        dx = (px - cx) / max(rx * scale, 1)
        dy = (py - cy) / max(ry * scale, 1)
        return math.sqrt(dx*dx + dy*dy) < 1.1


# ---------------------------------------------------------------------------
# Influence field from scaffold points
# ---------------------------------------------------------------------------

def _influence_at(
    px: float, py: float,
    field: list[list[tuple[float, float, float]]],
    reach: float,
) -> float:
    """Smoothed max-influence from all scaffold field points."""
    if not field:
        return 0.5
    best = 0.0
    for branch in field:
        for fx, fy, fw in branch:
            dist = math.sqrt((px - fx)**2 + (py - fy)**2)
            t = max(0.0, 1.0 - dist / max(reach, 1))
            # Smooth falloff: t^2 so influence drops off faster away from curves
            best = max(best, t * t * fw)
    return min(1.0, best)


# ---------------------------------------------------------------------------
# Zone density
# ---------------------------------------------------------------------------

def _zone_density(px, py, cx, cy, rx, ry) -> float:
    dx = (px - cx) / max(rx, 1)
    dy = (py - cy) / max(ry, 1)
    d  = math.sqrt(dx*dx + dy*dy)
    if d < 0.40: return 1.00
    if d < 0.70: return 0.82
    if d < 0.90: return 0.48
    if d < 1.08: return 0.20
    return 0.0


# ---------------------------------------------------------------------------
# Void pockets
# ---------------------------------------------------------------------------

def _in_void(px, py, cx, cy, cr, void_frac, seed) -> bool:
    if void_frac <= 0: return False
    for i in range(3):
        s = _lcg(seed + i * 1009 + 7)
        vx = cx + (_lcg_f(s) - 0.5) * cr * 0.88
        s = _lcg(s)
        vy = cy + (_lcg_f(s) - 0.60) * cr * 0.72
        s = _lcg(s)
        vr = cr * (0.10 + _lcg_f(s) * void_frac * 0.62)
        if math.sqrt((px-vx)**2 + (py-vy)**2) < vr:
            return True
    return False


# ---------------------------------------------------------------------------
# Trunk strokes
# ---------------------------------------------------------------------------

def _trunk_paths(bx, by, tx, ty, width, n, seed):
    paths = []
    s = seed
    dx = tx - bx; dy = ty - by
    L  = math.sqrt(dx*dx + dy*dy)
    ux = dx / max(L,1); uy = dy / max(L,1)
    perp_x = -uy; perp_y = ux

    for _ in range(n):
        s = _lcg(s)
        lat  = (_lcg_f(s) - 0.5) * width * 0.85
        s = _lcg(s)
        wamp = _lcg_f(s) * width * 0.12
        s = _lcg(s)
        wfreq = 2.5 + _lcg_f(s) * 1.5
        pts = []
        for step in range(13):
            t   = step / 12
            wav = math.sin(t * math.pi * wfreq) * wamp
            pts.append((bx + dx*t + perp_x*(lat+wav),
                        by + dy*t + perp_y*(lat+wav)))
        paths.append(pts)
    return paths


# ---------------------------------------------------------------------------
# Core draw function
# ---------------------------------------------------------------------------

def draw_tree(
    buf: "SurfaceBuffer",
    tree: TreeDef,
    registry: "AssetRegistry",
    x: float, y: float,
    trunk_height: float,
    canopy_radius: float,
    seed: int = 42,
) -> dict:
    """
    Render a complete tree.

    V4: scaffold field is loaded from data/gfig/<species>_scaffold,
    sampled along its curves, and mapped to world-space.
    The field drives leaf placement probabilistically — never renders directly.
    """
    from engine_mr import stroke_to_events, StrokeEvent
    from engine_debug_mr import stamp_blended

    stats: dict[str, int] = {}
    s = seed

    # Geometry
    lean_dx = math.sin(tree.lean_angle) * trunk_height
    top_x   = x + lean_dx
    top_y   = y - trunk_height
    trunk_w = canopy_radius * tree.trunk_ratio

    canopy_cx = top_x
    canopy_cy = top_y + canopy_radius * 0.07
    if tree.wind_bias is not None:
        wo = canopy_radius * 0.07
        canopy_cx += math.cos(tree.wind_bias) * wo
        canopy_cy += math.sin(tree.wind_bias) * wo * 0.5

    shape = tree.canopy_shape
    if shape == "conical":   rx, ry = canopy_radius * 0.52, canopy_radius
    elif shape == "oval_v":  rx, ry = canopy_radius * 0.62, canopy_radius * 1.18
    elif shape == "oval_h":  rx, ry = canopy_radius * 1.18, canopy_radius * 0.72
    else:                    rx, ry = canopy_radius, canopy_radius

    # Load Gfig scaffold (cached per call — no global state)
    field = _load_scaffold(tree.name, top_x, top_y, canopy_radius)
    reach = canopy_radius * tree.influence_reach

    def _recipe(layer: TreeLayerDef):
        return build(registry, layer.recipe_name)

    def _col(layer: TreeLayerDef, extra: float = 0.0) -> tuple[int,int,int]:
        r, g, b = layer.colour
        shift = int((layer.colour_shift + extra) * 65)
        return (max(0,min(255,r+shift)), max(0,min(255,g+shift)), max(0,min(255,b+shift)))

    def _br_sp(recipe) -> tuple[float, float]:
        if recipe is None: return 12.0, 1.0
        if recipe.is_variant():
            c = recipe.variant_bundle.cells
            return max(c[0].width, c[0].height)/2.0, recipe.variant_bundle.step
        if recipe.shape:
            return (recipe.shape.radius or (recipe.shape.width or 32)/2.0,
                    recipe.shape.spacing_pct)
        return 12.0, 1.0

    # -------------------------------------------------------------------
    # Pass 1: Shadow mass
    # -------------------------------------------------------------------
    sl = tree.shadow_layer
    sr = _recipe(sl)
    if sr and sl.stamp_budget > 0 and tree.canopy_density > 0.1:
        scx = canopy_cx + canopy_radius * 0.07
        scy = canopy_cy + canopy_radius * 0.09
        br, sp = _br_sp(sr)
        n = 0; si = s + 10000
        while n < sl.stamp_budget:
            si = _lcg(si)
            px_ = scx + (_lcg_f(si) - 0.5) * rx * 1.75
            si = _lcg(si)
            py_ = scy + (_lcg_f(si) - 0.52) * ry * 1.75
            if not _inside_envelope(px_, py_, scx, scy, rx*0.88, ry*0.88,
                                    top_x, top_y, canopy_radius, shape, 0.88, seed):
                continue
            si = _lcg(si)
            if _lcg_f(si) > sl.density_bias: continue
            ev = StrokeEvent(px_, py_, 0.48, 0.5, 0.0, random_seed=si)
            stamp_blended(buf, sr, ev, 0, _col(sl), sl.behaviour.blend_mode)
            n += 1
        stats["shadow"] = n

    # -------------------------------------------------------------------
    # Pass 2: Bark (Trunk and Boughs)
    # -------------------------------------------------------------------
    bl = tree.bark_layer
    br_r = _recipe(bl)
    if br_r and bl.stamp_budget > 0:
        paths = _trunk_paths(x, y, top_x, top_y, trunk_w,
                             max(1, bl.stamp_budget // 42), seed + 1000)
        br, sp = _br_sp(br_r)
        n = 0
        
        # 2A: Main Trunk
        trunk_budget = int(bl.stamp_budget * 0.55)
        for path in paths:
            evs = stroke_to_events(path, spacing_pct=sp,
                                    base_radius=max(br, trunk_w*0.35),
                                    pressure=0.82, seed=s+1100)
            for idx, ev in enumerate(evs):
                stamp_blended(buf, br_r, ev, idx, _col(bl), bl.behaviour.blend_mode)
                n += 1
                if n >= trunk_budget: break
            if n >= trunk_budget: break
            
        # 2B: Authored Wood (Branches)
        # Branches start thick near trunk and taper. Pressure controls dynamics.
        branch_budget = bl.stamp_budget - n
        if branch_budget > 0 and field:
            budget_per_branch = max(5, branch_budget // len(field))
            for b_idx, branch in enumerate(field):
                b_pts = [(bx, by) for bx, by, bw in branch]
                if not b_pts: continue
                
                # Double-pass for branches so they look rich
                for pass_i in range(2):
                    offset_x = (_lcg_f(s + b_idx * 10 + pass_i) - 0.5) * trunk_w * 0.2
                    offset_y = (_lcg_f(s + b_idx * 10 + pass_i + 1) - 0.5) * trunk_w * 0.2
                    offset_pts = [(px + offset_x, py + offset_y) for px, py in b_pts]
                    
                    evs = stroke_to_events(offset_pts, spacing_pct=sp, 
                                           base_radius=br * 1.5, pressure=0.8, seed=s+2000+b_idx+pass_i*7)
                    total_evs = len(evs)
                    for idx, ev in enumerate(evs):
                        t = idx / max(total_evs - 1, 1)
                        # Taper pressure: base=0.9, tip=0.1
                        taper_p = 0.9 - (t * 0.8)
                        
                        te = StrokeEvent(
                            position_x=ev.position_x, 
                            position_y=ev.position_y,
                            pressure=max(0.01, taper_p), 
                            velocity=ev.velocity, 
                            direction=ev.direction,
                            random_seed=ev.random_seed
                        )
                        stamp_blended(buf, br_r, te, idx, _col(bl), bl.behaviour.blend_mode)
                        n += 1
                        if n >= bl.stamp_budget: break
                    if n >= bl.stamp_budget: break
                if n >= bl.stamp_budget: break

        stats["bark"] = n

    # -------------------------------------------------------------------
    # Pass 3: Leaf mass — scaffold-anchored field sampling
    # -------------------------------------------------------------------
    ll = tree.leaf_layer
    lr = _recipe(ll)
    if lr and ll.stamp_budget > 0 and tree.canopy_density > 0.05:
        br, sp = _br_sp(lr)
        n = 0; cand = 0; max_cand = ll.stamp_budget * 25
        si = s + 20000

        while n < ll.stamp_budget and cand < max_cand:
            cand += 1
            si = _lcg(si)
            px_ = canopy_cx + (_lcg_f(si) - 0.5) * rx * 2.20
            si = _lcg(si)
            py_ = canopy_cy + (_lcg_f(si) - 0.50) * ry * 2.20

            if not _inside_envelope(px_, py_, canopy_cx, canopy_cy, rx, ry,
                                    top_x, top_y, canopy_radius, shape, 1.0, seed):
                continue

            zone = _zone_density(px_, py_, canopy_cx, canopy_cy, rx, ry)
            if zone < 0.12: continue

            if _in_void(px_, py_, canopy_cx, canopy_cy, canopy_radius,
                        tree.void_fraction, seed + cand * 7):
                continue

            # Scaffold influence: higher weight near authored branch curves
            infl  = _influence_at(px_, py_, field, reach)
            
            # Rigid branch clipping: reject leaves totally if they are too far from structural wood
            if infl < 0.08: continue
            
            # Accept probability: influence raised by field, modulated by zone and density
            accept = infl * zone * ll.density_bias * tree.canopy_density
            si = _lcg(si)
            if _lcg_f(si) > accept: continue

            extra_light = (1.0 - zone) * 0.14
            ev = StrokeEvent(px_, py_, 0.65 + zone*0.28, 0.65, 0.0, random_seed=si)
            stamp_blended(buf, lr, ev, 0, _col(ll, extra_light), ll.behaviour.blend_mode)
            n += 1

        stats["leaves"] = n

    # -------------------------------------------------------------------
    # Pass 4: Canopy edge — perimeter ring, scaffold-biased
    # -------------------------------------------------------------------
    el = tree.edge_layer
    er = _recipe(el)
    if er and el.stamp_budget > 0 and tree.canopy_density > 0.1:
        br, sp = _br_sp(er)
        n = 0; cand = 0; max_cand = el.stamp_budget * 22
        si = s + 30000

        while n < el.stamp_budget and cand < max_cand:
            cand += 1
            si = _lcg(si)
            ang   = _lcg_f(si) * 2 * math.pi
            si = _lcg(si)
            dist_ = 0.70 + _lcg_f(si) * 0.42
            px_ = canopy_cx + math.cos(ang) * rx * dist_
            py_ = canopy_cy + math.sin(ang) * ry * dist_

            if not _inside_envelope(px_, py_, canopy_cx, canopy_cy, rx, ry,
                                    top_x, top_y, canopy_radius, shape, 1.08, seed):
                continue

            zone  = _zone_density(px_, py_, canopy_cx, canopy_cy, rx, ry)
            infl  = _influence_at(px_, py_, field, reach)
            accept = (zone * 0.55 + infl * 0.45) * el.density_bias * tree.canopy_density
            si = _lcg(si)
            if _lcg_f(si) > accept: continue

            ev = StrokeEvent(px_, py_, 0.52 + zone*0.22, 0.60, ang, random_seed=si)
            stamp_blended(buf, er, ev, 0, _col(el), el.behaviour.blend_mode)
            n += 1

        stats["edge"] = n

    return stats


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.path.insert(0, str(_HERE))
    from trixel_brush_adapter import AssetRegistry
    from engine_debug_mr import solid_bg, text, save_png

    # Asset discovery — no hardcoded paths
    gimp_root = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_gimp_data()
    out_dir   = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/trixel_trees")
    out_dir.mkdir(parents=True, exist_ok=True)

    if gimp_root is None:
        print("Could not find GIMP data. Pass path as first argument.")
        sys.exit(1)

    print(f"GIMP data: {gimp_root}")
    print(f"Gfig scaffolds: {_GFIG_DIR}")
    print(f"Output: {out_dir}")

    print("\nLoading assets...")
    registry = AssetRegistry()
    for sub in ("brushes", "dynamics", "palettes", "patterns", "tool-presets", "gradients", "gflare"):
        p = gimp_root / sub
        if p.exists():
            registry.load_from_directory(p)

    # Verify scaffold files load
    print("\nScaffold check:")
    for species in ("oak", "pine", "birch", "dead"):
        path = _GFIG_DIR / f"{species}_scaffold"
        if path.exists():
            from brushes.gfig_parser_mr import parse_gfig
            fig = parse_gfig(path)
            pts = _load_scaffold(species, 0, 0, 100)
            print(f"  {species:8s}: {fig.name!r}  "
                  f"arcs={len(fig.arcs())} lines={len(fig.lines())}  "
                  f"field_pts={len(pts)}")
        else:
            print(f"  {species}: MISSING {path}")

    W, H = 980, 460
    buf = solid_bg(W, H, 235)
    text(buf, 8, 6,  "TRIXEL TREE SYSTEMS  V4  GFIG-BACKED GENERATION", colour=(40,40,40))
    text(buf, 8, 16, "scaffold = authored curves  influence = hidden field", colour=(80,80,80))

    configs = [
        (TREE_OAK,   215, 405, 248,  90, 42),
        (TREE_PINE,  448, 408, 228,  70, 99),
        (TREE_BIRCH, 660, 402, 208,  62, 17),
        (TREE_DEAD,  860, 400, 175,  50, 77),
    ]

    for tree_def, tx, ty, th, cr, sd in configs:
        print(f"  {tree_def.label}...", end=" ", flush=True)
        stats = draw_tree(buf, tree_def, registry, tx, ty, th, cr, seed=sd)
        total = sum(stats.values())
        text(buf, tx - 38, ty + 14, tree_def.label, colour=(55, 55, 55))
        print(f"{total} stamps  ({' '.join(f'{k}={v}' for k,v in stats.items())})")

    out = out_dir / "tree_demo_v4.png"
    save_png(buf, out)
    print(f"\n✓  {out}")
