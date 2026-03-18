"""
world_tree_mr.py — Trixel Tree Visual System  v3

The viewer should feel the branches, not see them.

v3 replaces direct branch-anchor rendering with an influence field approach:

  Support branches (hidden)
    Branch endpoints define a weighted field.
    They are never rendered directly.
    They bias WHERE leaf stamps are more likely to land.

  Cluster masses (visible)
    Candidate positions are scattered across the full canopy bounding box.
    Each candidate is accepted/rejected by:
      1. Species envelope  — pine cone, oak circle, birch oval, etc.
      2. Branch influence  — proximity to branch endpoints raises probability
      3. Zone density      — core denser than fringe
      4. Void pockets      — deterministic gaps for sky and breathing room

  Silhouette cleanup (per species)
    Envelope functions enforce species-specific outer shape.
    Pine stamps cannot land outside the conical outline.
    Birch's oval_v is taller than wide.
    Oak's round envelope has slight organic wobble.
    Dead tree: no leaf field at all.

The scaffold is felt, not seen.
The species identity lives in the envelope, not the branch count.

Rendering passes:
  1. shadow_mass  — soft dark volume, sampled inside shadow ellipse
  2. bark         — directional trunk grain strokes
  3. leaf_mass    — field-sampled, envelope-gated, influence-weighted
  4. canopy_edge  — perimeter ring samples, thinner envelope threshold
"""

# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING                                               v1
# ---------------------------------------------------------------------------
# This file calls:    surface_behavior_mr.py      (Same Folder)
#                     trixel_recipes_mr.py        (Same Folder)
#                     trixel_brush_adapter.py     (Same Folder)
#                     engine_mr.py                (Same Folder)
#                     engine_debug_mr.py          (Same Folder)
# This file is called by: trixel_demo_mr.py       (Same Folder)
#                          __main__ (CLI direct execution)
# ---------------------------------------------------------------------------

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from surface_behavior_mr import (
    SurfaceBehavior,
    TREE_BARK, TREE_SHADOW_MASS, TREE_LEAF_MASS, TREE_CANOPY_EDGE,
)
from trixel_recipes_mr import ALL_RECIPES, build

if TYPE_CHECKING:
    from trixel_brush_adapter import AssetRegistry
    from engine_mr import SurfaceBuffer


# ---------------------------------------------------------------------------
# LCG — deterministic, no random module
# ---------------------------------------------------------------------------

def _lcg(s: int) -> int:
    return (s * 1664525 + 1013904223) & 0xFFFFFFFF

def _lcg_f(s: int) -> float:
    return _lcg(s) / 0x100000000


# ---------------------------------------------------------------------------
# TreeLayerDef
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TreeLayerDef:
    """One rendering pass within the tree visual system."""
    behaviour:    SurfaceBehavior
    recipe_name:  str
    colour:       tuple[int, int, int]
    colour_shift: float
    stamp_budget: int    # max stamps this layer may place
    density_bias: float  # 0-1 scales the accept probability; lower = sparser/airier


# ---------------------------------------------------------------------------
# TreeDef
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TreeDef:
    """
    Complete visual system declaration for one tree species.

    canopy_density:  0=bare, 1=fully leafed (scales all leaf/edge passes)
    void_fraction:   0-0.4, size of void pockets punched through core
    influence_reach: how far a branch endpoint's weight extends,
                     as a fraction of canopy_radius (0.4=tight, 0.7=wide)
    """
    name:             str
    label:            str
    trunk_ratio:      float
    taper:            float
    canopy_shape:     str      # 'round'|'oval_v'|'oval_h'|'conical'|'irregular'
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
# Species declarations
# ---------------------------------------------------------------------------

TREE_OAK = TreeDef(
    name="oak", label="Oak Tree",
    trunk_ratio=0.18, taper=0.32,
    canopy_shape="round", canopy_density=0.88,
    lean_angle=0.0, wind_bias=None,
    void_fraction=0.20, influence_reach=0.58,
    bark_layer=TreeLayerDef(
        TREE_BARK, "charcoal_grain",
        _OAK_BARK, 0.0, stamp_budget=320, density_bias=1.0,
    ),
    shadow_layer=TreeLayerDef(
        TREE_SHADOW_MASS, "oil_smear",
        _SHADOW, -0.2, stamp_budget=180, density_bias=0.9,
    ),
    leaf_layer=TreeLayerDef(
        TREE_LEAF_MASS, "acrylic_variant",
        _OAK_LEAF, 0.0, stamp_budget=280, density_bias=0.85,
    ),
    edge_layer=TreeLayerDef(
        TREE_CANOPY_EDGE, "bristle_rake",
        _OAK_LEAF, 0.18, stamp_budget=160, density_bias=0.55,
    ),
    description="Broad rounded crown, thick rough bark, dense clustered foliage.",
)

TREE_PINE = TreeDef(
    name="pine", label="Pine Tree",
    trunk_ratio=0.10, taper=0.55,
    canopy_shape="conical", canopy_density=0.75,
    lean_angle=0.0, wind_bias=None,
    void_fraction=0.12, influence_reach=0.50,
    bark_layer=TreeLayerDef(
        TREE_BARK, "hatch_texture",
        _PINE_BARK, 0.0, stamp_budget=280, density_bias=1.0,
    ),
    shadow_layer=TreeLayerDef(
        TREE_SHADOW_MASS, "oil_smear",
        _SHADOW, -0.28, stamp_budget=140, density_bias=0.85,
    ),
    leaf_layer=TreeLayerDef(
        TREE_LEAF_MASS, "bristle_rake",
        _PINE_LEAF, 0.0, stamp_budget=320, density_bias=0.80,
    ),
    edge_layer=TreeLayerDef(
        TREE_CANOPY_EDGE, "charcoal_grain",
        _PINE_LEAF, 0.12, stamp_budget=120, density_bias=0.42,
    ),
    description="Conical tiered crown, tight dark needle clusters, thin tapering trunk.",
)

TREE_BIRCH = TreeDef(
    name="birch", label="Birch Tree",
    trunk_ratio=0.08, taper=0.45,
    canopy_shape="oval_v", canopy_density=0.58,
    lean_angle=0.08, wind_bias=math.pi * 1.1,
    void_fraction=0.32, influence_reach=0.65,
    bark_layer=TreeLayerDef(
        TREE_BARK, "hard_pixel",
        _BIRCH_BARK, 0.0, stamp_budget=220, density_bias=1.0,
    ),
    shadow_layer=TreeLayerDef(
        TREE_SHADOW_MASS, "charcoal_grain",
        _SHADOW, -0.15, stamp_budget=100, density_bias=0.70,
    ),
    leaf_layer=TreeLayerDef(
        TREE_LEAF_MASS, "acrylic_variant",
        _BIRCH_LEAF, 0.0, stamp_budget=200, density_bias=0.62,
    ),
    edge_layer=TreeLayerDef(
        TREE_CANOPY_EDGE, "bristle_rake",
        _BIRCH_LEAF, 0.22, stamp_budget=110, density_bias=0.38,
    ),
    description="Slender, airy canopy with organic gaps. Pale bark, drooping branch form.",
)

TREE_DEAD = TreeDef(
    name="dead", label="Dead Tree",
    trunk_ratio=0.12, taper=0.60,
    canopy_shape="irregular", canopy_density=0.0,
    lean_angle=0.15, wind_bias=None,
    void_fraction=1.0, influence_reach=0.3,
    bark_layer=TreeLayerDef(
        TREE_BARK, "hatch_texture",
        _DEAD_BARK, 0.0, stamp_budget=480, density_bias=1.0,
    ),
    shadow_layer=TreeLayerDef(
        TREE_SHADOW_MASS, "charcoal_grain",
        (28, 22, 18), -0.1, stamp_budget=60, density_bias=0.45,
    ),
    leaf_layer=TreeLayerDef(
        TREE_LEAF_MASS, "charcoal_grain",
        _DEAD_BARK, 0.1, stamp_budget=0, density_bias=0.0,
    ),
    edge_layer=TreeLayerDef(
        TREE_CANOPY_EDGE, "hatch_texture",
        (48, 38, 28), 0.0, stamp_budget=0, density_bias=0.0,
    ),
    description="No foliage. Bare structural hatch only.",
)

ALL_TREES: dict[str, TreeDef] = {
    t.name: t for t in [TREE_OAK, TREE_PINE, TREE_BIRCH, TREE_DEAD]
}


# ---------------------------------------------------------------------------
# Envelope functions — species outer shape
# ---------------------------------------------------------------------------

def _inside_envelope(
    px: float, py: float,
    cx: float, cy: float,     # canopy centre
    rx: float, ry: float,     # nominal radii
    top_x: float, top_y: float,
    canopy_radius: float,
    shape: str,
    envelope_scale: float,    # 1.0=nominal, 1.1=allow slight fringe
    seed: int,
) -> bool:
    """Return True if (px, py) is inside the species envelope."""

    if shape == "conical":
        # Cone narrows toward trunk top; no stamp above the tip
        dy = py - top_y
        if dy < -canopy_radius * 0.05:
            return False
        tier_frac = dy / max(canopy_radius, 1)
        max_x = canopy_radius * envelope_scale * (0.12 + 0.88 * tier_frac)
        return abs(px - top_x) <= max_x

    elif shape == "oval_v":
        dx = (px - cx) / max(rx * envelope_scale, 1)
        # Birch: lower portion of oval droops, so extend ry below centre
        if py > cy:
            ry_eff = ry * envelope_scale * 1.20
        else:
            ry_eff = ry * envelope_scale
        dy_n = (py - cy) / max(ry_eff, 1)
        return math.sqrt(dx*dx + dy_n*dy_n) < 1.0

    elif shape == "round":
        dx = (px - cx) / max(rx, 1)
        dy_n = (py - cy) / max(ry, 1)
        dist = math.sqrt(dx*dx + dy_n*dy_n)
        # Organic wobble: slight radius variation by angle
        angle = math.atan2(dy_n, dx)
        s = _lcg(int(abs(angle) * 800) & 0xFFFFFFFF ^ seed)
        wobble = (_lcg_f(s) - 0.5) * 0.22
        return dist < (envelope_scale + wobble)

    elif shape == "irregular":
        dx = (px - cx) / max(rx, 1)
        dy_n = (py - cy) / max(ry, 1)
        return math.sqrt(dx*dx + dy_n*dy_n) < envelope_scale * 1.1

    else:  # oval_h, fallback
        dx = (px - cx) / max(rx * envelope_scale, 1)
        dy_n = (py - cy) / max(ry * envelope_scale, 1)
        return math.sqrt(dx*dx + dy_n*dy_n) < 1.0


# ---------------------------------------------------------------------------
# Branch endpoint field
# ---------------------------------------------------------------------------

def _branch_field(
    top_x: float, top_y: float,
    canopy_radius: float,
    species: str,
    n: int,
    seed: int,
) -> list[tuple[float, float, float]]:
    """
    Compute branch endpoints as influence field points.
    Returns list of (x, y, weight) where weight 0-1 controls local density.
    These points are NEVER rendered — they only bias leaf placement.
    """
    s = seed
    field: list[tuple[float, float, float]] = []

    if species == "oak":
        for i in range(n):
            s = _lcg(s)
            angle = math.pi * 1.12 + (i / max(n-1, 1)) * math.pi * 0.76
            s = _lcg(s)
            angle += (_lcg_f(s) - 0.5) * 0.55
            s = _lcg(s)
            length = 0.50 + _lcg_f(s) * 0.50
            droop  = max(0, length - 0.6) * canopy_radius * 0.22
            fx = top_x + math.cos(angle) * canopy_radius * length
            fy = top_y + math.sin(angle) * canopy_radius * length + droop
            field.append((fx, fy, 0.55 + length * 0.45))

    elif species == "pine":
        # Three tiers with jitter — tiered bands become density guides not rungs
        n_tiers = 3
        per_tier = max(3, n // n_tiers)
        for tier in range(n_tiers):
            tier_t  = tier / max(n_tiers - 1, 1)
            tier_y_base = top_y + tier_t * canopy_radius * 0.88
            max_w   = canopy_radius * (0.20 + 0.80 * tier_t)
            for j in range(per_tier):
                s = _lcg(s)
                # Each point in the tier has y-jitter so they don't align
                y_jitter = (_lcg_f(s) - 0.5) * canopy_radius * 0.18
                s = _lcg(s)
                side = -1 if j % 2 == 0 else 1
                spread = 0.45 + _lcg_f(s) * 0.55
                s = _lcg(s)
                x_jitter = (_lcg_f(s) - 0.5) * max_w * 0.30
                fx = top_x + side * max_w * spread + x_jitter
                fy = tier_y_base + y_jitter
                field.append((fx, fy, 0.50 + tier_t * 0.35))
                if len(field) >= n: break
            if len(field) >= n: break

    elif species == "birch":
        for i in range(n):
            s = _lcg(s)
            angle = math.pi * 1.15 + (i / max(n-1, 1)) * math.pi * 0.70
            s = _lcg(s)
            angle += (_lcg_f(s) - 0.5) * 0.60
            s = _lcg(s)
            length = 0.52 + _lcg_f(s) * 0.48
            droop  = length * canopy_radius * 0.32
            fx = top_x + math.cos(angle) * canopy_radius * length
            fy = top_y + math.sin(angle) * canopy_radius * length + droop
            field.append((fx, fy, 0.45 + length * 0.40))

    elif species == "dead":
        for i in range(min(n, 4)):
            s = _lcg(s)
            angle = math.pi * 1.1 + (i / 4) * math.pi * 0.8
            s = _lcg(s)
            angle += (_lcg_f(s) - 0.5) * 0.35
            s = _lcg(s)
            length = 0.28 + _lcg_f(s) * 0.30
            fx = top_x + math.cos(angle) * canopy_radius * length
            fy = top_y + math.sin(angle) * canopy_radius * length
            field.append((fx, fy, 0.30 + length * 0.40))

    return field[:n]


def _influence_at(
    px: float, py: float,
    field: list[tuple[float, float, float]],
    reach: float,             # influence radius in pixels
) -> float:
    """
    Weighted influence from all branch field points.
    Returns 0-1: 0=far from all branches, 1=right on a branch.
    Uses exponential falloff so influence blends smoothly.
    """
    if not field:
        return 0.5
    total = 0.0
    for fx, fy, fw in field:
        dist = math.sqrt((px-fx)**2 + (py-fy)**2)
        # Exponential falloff
        t = max(0.0, 1.0 - dist / max(reach, 1))
        total = max(total, t * fw)
    return min(1.0, total)


# ---------------------------------------------------------------------------
# Zone density
# ---------------------------------------------------------------------------

def _zone_density(px, py, cx, cy, rx, ry) -> float:
    dx = (px - cx) / max(rx, 1)
    dy = (py - cy) / max(ry, 1)
    d  = math.sqrt(dx*dx + dy*dy)
    if d < 0.42:  return 1.00
    if d < 0.72:  return 0.82
    if d < 0.92:  return 0.48
    if d < 1.08:  return 0.20   # allow thin fringe beyond nominal radius
    return 0.0


# ---------------------------------------------------------------------------
# Void pockets
# ---------------------------------------------------------------------------

def _in_void(px, py, cx, cy, cr, void_fraction, seed) -> bool:
    if void_fraction <= 0:
        return False
    for i in range(3):
        s = _lcg(seed + i * 1009 + 7)
        vx = cx + (_lcg_f(s) - 0.5) * cr * 0.90
        s = _lcg(s)
        vy = cy + (_lcg_f(s) - 0.62) * cr * 0.75
        s = _lcg(s)
        vr = cr * (0.10 + _lcg_f(s) * void_fraction * 0.65)
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
    ux = dx / max(L, 1); uy = dy / max(L, 1)
    px = -uy; py = ux

    for _ in range(n):
        s = _lcg(s)
        lat  = (_lcg_f(s) - 0.5) * width * 0.82
        s = _lcg(s)
        wamp = _lcg_f(s) * width * 0.13
        s = _lcg(s)
        wfreq = 2.5 + _lcg_f(s) * 1.5
        pts = []
        for step in range(13):
            t   = step / 12
            wav = math.sin(t * math.pi * wfreq) * wamp
            x   = bx + dx*t + px*(lat + wav)
            y   = by + dy*t + py*(lat + wav)
            pts.append((x, y))
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

    Leaf pass uses field sampling:
      - scatter many candidates across canopy bounding box
      - accept if: inside envelope AND influence*zone > random threshold
      - stop when stamp_budget is reached or candidates exhausted
    """
    from engine_mr import stroke_to_events
    from engine_debug_mr import stamp_blended

    stats: dict[str, int] = {}
    s = seed

    # Geometry
    lean_dx = math.sin(tree.lean_angle) * trunk_height
    top_x   = x + lean_dx
    top_y   = y - trunk_height
    trunk_w = canopy_radius * tree.trunk_ratio

    # Canopy centre
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

    # Build hidden branch field
    n_field = 10 + int(tree.canopy_density * 6)
    field = _branch_field(top_x, top_y, canopy_radius, tree.name, n_field, seed)
    influence_reach = canopy_radius * tree.influence_reach

    def _recipe(layer: TreeLayerDef):
        return build(registry, layer.recipe_name)

    def _col(layer: TreeLayerDef, extra: float = 0.0) -> tuple[int,int,int]:
        r, g, b = layer.colour
        shift = int((layer.colour_shift + extra) * 65)
        return (max(0, min(255, r+shift)),
                max(0, min(255, g+shift)),
                max(0, min(255, b+shift)))

    def _br_sp(recipe) -> tuple[float, float]:
        if recipe is None: return 12.0, 1.0
        if recipe.is_variant():
            cells = recipe.variant_bundle.cells
            return max(cells[0].width, cells[0].height)/2.0, recipe.variant_bundle.step
        if recipe.shape:
            return (recipe.shape.radius or (recipe.shape.width or 32)/2.0,
                    recipe.shape.spacing_pct)
        return 12.0, 1.0

    # --- Pass 1: Shadow ---
    sl = tree.shadow_layer
    sr = _recipe(sl)
    if sr and sl.stamp_budget > 0 and tree.canopy_density > 0.1:
        scx = canopy_cx + canopy_radius * 0.07
        scy = canopy_cy + canopy_radius * 0.09
        br, sp = _br_sp(sr)
        n = 0
        s_inner = s + 10000
        while n < sl.stamp_budget:
            s_inner = _lcg(s_inner)
            tx_ = scx + (_lcg_f(s_inner) - 0.5) * rx * 1.80
            s_inner = _lcg(s_inner)
            ty_ = scy + (_lcg_f(s_inner) - 0.52) * ry * 1.80
            if not _inside_envelope(tx_, ty_, scx, scy, rx*0.90, ry*0.90,
                                    top_x, top_y, canopy_radius, shape, 0.9, seed):
                continue
            s_inner = _lcg(s_inner)
            if _lcg_f(s_inner) > sl.density_bias: continue
            pts = [(tx_, ty_), (tx_ + _lcg_f(_lcg(s_inner))*br*1.2 - br*0.6,
                                ty_ + _lcg_f(_lcg(_lcg(s_inner)))*br*1.2 - br*0.6)]
            evs = stroke_to_events(pts, spacing_pct=sp*0.9, base_radius=br,
                                    pressure=0.48, seed=s_inner)
            for idx, ev in enumerate(evs):
                stamp_blended(buf, sr, ev, idx, _col(sl), sl.behaviour.blend_mode)
                n += 1
                if n >= sl.stamp_budget: break
        stats["shadow"] = n

    # --- Pass 2: Bark ---
    bl = tree.bark_layer
    br_r = _recipe(bl)
    if br_r and bl.stamp_budget > 0:
        paths = _trunk_paths(x, y, top_x, top_y, trunk_w, bl.stamp_budget // 40, seed+1000)
        br, sp = _br_sp(br_r)
        n = 0
        for path in paths:
            evs = stroke_to_events(path, spacing_pct=sp,
                                    base_radius=max(br, trunk_w * 0.35),
                                    pressure=0.82, seed=s+1100)
            for idx, ev in enumerate(evs):
                stamp_blended(buf, br_r, ev, idx, _col(bl), bl.behaviour.blend_mode)
                n += 1
                if n >= bl.stamp_budget: break
        stats["bark"] = n

    # --- Pass 3: Leaf mass (field-sampled) ---
    ll = tree.leaf_layer
    lr = _recipe(ll)
    if lr and ll.stamp_budget > 0 and tree.canopy_density > 0.05:
        br, sp = _br_sp(lr)
        n = 0
        candidates_tried = 0
        max_candidates = ll.stamp_budget * 18
        s_inner = s + 20000

        while n < ll.stamp_budget and candidates_tried < max_candidates:
            candidates_tried += 1
            s_inner = _lcg(s_inner)
            # Sample inside a box big enough for any species
            px_ = canopy_cx + (_lcg_f(s_inner) - 0.5) * rx * 2.20
            s_inner = _lcg(s_inner)
            py_ = canopy_cy + (_lcg_f(s_inner) - 0.50) * ry * 2.20

            # 1. Species envelope gate (strict = 1.0, fringe allow up to 1.08)
            if not _inside_envelope(px_, py_, canopy_cx, canopy_cy, rx, ry,
                                    top_x, top_y, canopy_radius, shape, 1.0, seed):
                continue

            # 2. Zone density
            zone_d = _zone_density(px_, py_, canopy_cx, canopy_cy, rx, ry)
            if zone_d < 0.12:
                continue

            # 3. Void pocket
            if _in_void(px_, py_, canopy_cx, canopy_cy, canopy_radius,
                        tree.void_fraction, seed + candidates_tried * 7):
                continue

            # 4. Influence weight * density_bias vs random threshold
            infl = _influence_at(px_, py_, field, influence_reach)
            # Combined accept weight: influence raises local density, zone amplifies
            accept_weight = infl * zone_d * ll.density_bias * tree.canopy_density
            s_inner = _lcg(s_inner)
            if _lcg_f(s_inner) > accept_weight:
                continue

            # Place one stamp at this candidate position
            ev_pressure = 0.65 + zone_d * 0.28
            from engine_mr import StrokeEvent, stamp_recipe
            ev = StrokeEvent(
                position_x=px_, position_y=py_,
                pressure=ev_pressure, velocity=0.65,
                direction=0.0, random_seed=s_inner,
            )
            # Colour lightens toward fringe
            extra_light = (1.0 - zone_d) * 0.14
            stamp_blended(buf, lr, ev, 0, _col(ll, extra_light), ll.behaviour.blend_mode)
            n += 1

        stats["leaves"] = n

    # --- Pass 4: Canopy edge (perimeter ring, field-sampled) ---
    el = tree.edge_layer
    er = _recipe(el)
    if er and el.stamp_budget > 0 and tree.canopy_density > 0.1:
        br, sp = _br_sp(er)
        n = 0
        candidates_tried = 0
        max_cand = el.stamp_budget * 20
        s_inner = s + 30000

        while n < el.stamp_budget and candidates_tried < max_cand:
            candidates_tried += 1
            s_inner = _lcg(s_inner)
            # Edge ring: dist 0.72-1.12 from centre
            angle_ = _lcg_f(s_inner) * 2 * math.pi
            s_inner = _lcg(s_inner)
            dist_   = 0.72 + _lcg_f(s_inner) * 0.40
            px_ = canopy_cx + math.cos(angle_) * rx * dist_
            py_ = canopy_cy + math.sin(angle_) * ry * dist_

            # Envelope gate (allow slight fringe overshoot)
            if not _inside_envelope(px_, py_, canopy_cx, canopy_cy, rx, ry,
                                    top_x, top_y, canopy_radius, shape, 1.08, seed):
                continue

            # Zone + influence + density_bias
            zone_d = _zone_density(px_, py_, canopy_cx, canopy_cy, rx, ry)
            infl   = _influence_at(px_, py_, field, influence_reach)
            accept = (zone_d * 0.6 + infl * 0.4) * el.density_bias * tree.canopy_density
            s_inner = _lcg(s_inner)
            if _lcg_f(s_inner) > accept: continue

            from engine_mr import StrokeEvent
            ev = StrokeEvent(
                position_x=px_, position_y=py_,
                pressure=0.52 + zone_d * 0.22, velocity=0.60,
                direction=angle_, random_seed=s_inner,
            )
            stamp_blended(buf, er, ev, 0, _col(el), el.behaviour.blend_mode)
            n += 1

        stats["edge"] = n

    return stats


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from trixel_brush_adapter import AssetRegistry
    from engine_debug_mr import solid_bg, text, save_png
    from pathlib import Path

    gimp_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/usr/share/gimp/2.0")
    out_dir   = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/trixel_trees")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading assets...")
    registry = AssetRegistry()
    for sub in ("brushes", "dynamics", "palettes"):
        p = gimp_root / sub
        if p.exists():
            registry.load_from_directory(p)

    W, H = 960, 460
    buf = solid_bg(W, H, 235)
    text(buf, 8, 6, "TRIXEL TREE SYSTEMS  V3  FIELD-SAMPLED CANOPY", colour=(40,40,40))
    text(buf, 8, 16, "branches = hidden influence  envelope = species identity", colour=(80,80,80))

    configs = [
        (TREE_OAK,   215, 400, 240,  88, 42),
        (TREE_PINE,  448, 405, 225,  70, 99),
        (TREE_BIRCH, 660, 400, 205,  62, 17),
        (TREE_DEAD,  862, 400, 175,  52, 77),
    ]

    for tree_def, tx, ty, th, cr, sd in configs:
        print(f"  {tree_def.label}...", end=" ", flush=True)
        stats = draw_tree(buf, tree_def, registry, tx, ty, th, cr, seed=sd)
        total = sum(stats.values())
        text(buf, tx - 38, ty + 14, tree_def.label, colour=(55, 55, 55))
        print(f"{total} stamps  ({' '.join(f'{k}={v}' for k,v in stats.items())})")

    out = out_dir / "tree_demo_v3.png"
    save_png(buf, out)
    print(f"\n✓  {out}")
