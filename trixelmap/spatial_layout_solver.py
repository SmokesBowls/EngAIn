#!/usr/bin/env python3
"""
trixelmap/spatial_layout_solver.py

Tier 2 Resolution: Constraint graph → solved coordinates.
Deterministic quadrant-first placement with strength-weighted vector refinement.
"""
import random
import math
import numpy as np
from typing import Dict, List, Tuple

ENGINE_SEED = 42
GRID_SIZE = 100

QUADRANT_ANCHORS = {
    "northwest": (0.20, 0.20), "northeast": (0.80, 0.20),
    "southwest": (0.20, 0.80), "southeast": (0.80, 0.80),
    "north": (0.50, 0.15), "south": (0.50, 0.85),
    "west": (0.15, 0.50), "east": (0.85, 0.50),
    "center": (0.50, 0.50), "east_coast": (0.90, 0.50),
}

REGION_SIZE_HINTS = {"light": 8, "medium": 14, "heavy": 22}

# ✅ STRENGTH-WEIGHTED VECTORS: Maps relations to desired grid deltas
RELATION_VECTORS = {
    "north_of":       (0.0, -18.0),
    "south_of":       (0.0, 18.0),
    "east_of":        (18.0, 0.0),
    "west_of":        (-18.0, 0.0),
    "above":          (0.0, -18.0),
    "below":          (0.0, 6.0),
    "overlooks":      (0.0, -8.0),
    "adjacent_to":    (0.0, 0.0),
    "connected_to":   (0.0, 0.0),
    "contained_by":   (0.0, 0.0),  # Handled via clamping
}

class DeterministicSpatialSolver:
    def __init__(self, spatial_authority: Dict, seed: int = ENGINE_SEED):
        self.authority = spatial_authority
        self.rng = random.Random(seed)
        np.random.seed(seed)
        
    def solve(self) -> Dict[str, Dict]:
        regions = self.authority.get("regions", {})
        edges = self.authority.get("edges", [])
        
        # Phase 1: Quadrant Anchoring
        positions = self._phase1_quadrant_placement(regions)
        
        # Phase 2: Vector Refinement
        positions = self._phase2_vector_refinement(positions, regions, edges)
        
        # Rasterize bounds
        resolved = {}
        for rid, (cx, cy) in positions.items():
            rdata = regions[rid]
            size = REGION_SIZE_HINTS.get(rdata.get("size_hint", "medium"), 14)
            
            if rdata.get("type") == "linear_spine":
                w, h = size * 1.8, size * 0.7
            else:
                w, h = size, size
            
            resolved[rid] = {
                "centroid": {"x": round(cx, 2), "y": round(cy, 2)},
                "bounds": {
                    "x_min": max(0, int(cx - w / 2)), "y_min": max(0, int(cy - h / 2)),
                    "x_max": min(GRID_SIZE, int(cx + w / 2)), "y_max": min(GRID_SIZE, int(cy + h / 2)),
                },
                "terrain_class": rdata.get("terrain_class", "default"),
                "type": rdata.get("type"),
                "landmarks": rdata.get("landmarks", []),
            }
        return {"version": "1.0", "grid_size": GRID_SIZE, "regions": resolved}
    
    def _phase1_quadrant_placement(self, regions: Dict) -> Dict[str, Tuple[float, float]]:
        positions = {}
        for rid, rdata in regions.items():
            anchor = QUADRANT_ANCHORS.get(rdata.get("quadrant_hint", "center"), (0.5, 0.5))
            jitter = (self.rng.uniform(-0.03, 0.03) * GRID_SIZE, self.rng.uniform(-0.03, 0.03) * GRID_SIZE)
            positions[rid] = (anchor[0] * GRID_SIZE + jitter[0], anchor[1] * GRID_SIZE + jitter[1])
        return positions
    
    def _phase2_vector_refinement(self, positions, regions, edges) -> Dict[str, Tuple[float, float]]:
        max_iter = 120
        learning_rate = 0.6
        
        for _ in range(max_iter):
            forces = {rid: [0.0, 0.0] for rid in positions}
            
            # 1. Repulsion (prevents collapse)
            ids = list(positions.keys())
            for i in range(len(ids)):
                for j in range(i+1, len(ids)):
                    a, b = np.array(positions[ids[i]]), np.array(positions[ids[j]])
                    diff = a - b
                    dist = max(np.linalg.norm(diff), 2.0)
                    repulsion = 12.0 / (dist ** 1.5)
                    direction = diff / dist
                    forces[ids[i]][0] += direction[0] * repulsion
                    forces[ids[i]][1] += direction[1] * repulsion
                    forces[ids[j]][0] -= direction[0] * repulsion
                    forces[ids[j]][1] -= direction[1] * repulsion

            # 2. Relationship Constraints + Same-Anchor Sibling Spacing
            anchor_edges = {}
            for edge in edges:
                anchor_edges.setdefault(edge["to"], []).append(edge)

            for anchor_id, edge_list in anchor_edges.items():
                if anchor_id not in positions:
                    continue
                    
                ax, ay = positions[anchor_id]
                # Deterministic sort ensures consistent layout across runs
                edge_list.sort(key=lambda e: e["from"])
                n_siblings = len(edge_list)

                for idx, edge in enumerate(edge_list):
                    rid_from = edge["from"]
                    if rid_from not in positions:
                        continue

                    strength = edge.get("strength", 0.5)
                    relation = edge["relation"]
                    base_dx, base_dy = RELATION_VECTORS.get(relation, (0.0, 0.0))

                    # Sibling spacing: distribute children angularly around anchor
                    angle_offset = (idx / max(n_siblings, 1)) * 2 * math.pi
                    spacing_radius = 14.0  # grid units
                    sibling_dx = math.cos(angle_offset) * spacing_radius
                    sibling_dy = math.sin(angle_offset) * spacing_radius

                    # Combine directional target + sibling distribution
                    target_dx = (base_dx + sibling_dx) * strength
                    target_dy = (base_dy + sibling_dy) * strength

                    pos_from = np.array(positions[rid_from])
                    pos_to = np.array(positions[anchor_id])
                    
                    # Current offset: where 'from' actually is relative to 'to'
                    current_dx = pos_from[0] - pos_to[0]
                    current_dy = pos_from[1] - pos_to[1]
                    
                    # Error: desired offset - actual offset
                    err_x = target_dx - current_dx
                    err_y = target_dy - current_dy
                    
                    # Apply proportional correction
                    fx = err_x * 0.07 * strength
                    fy = err_y * 0.07 * strength
                    
                    forces[rid_from][0] += fx
                    forces[rid_from][1] += fy
                    forces[anchor_id][0] -= fx
                    forces[anchor_id][1] -= fy

            # Apply forces
            converged = True
            for rid in positions:
                fx, fy = forces[rid]
                cx, cy = positions[rid]
                cx += fx * learning_rate
                cy += fy * learning_rate
                cx = max(4, min(GRID_SIZE - 4, cx))
                cy = max(4, min(GRID_SIZE - 4, cy))
                
                if abs(fx) > 0.4 or abs(fy) > 0.4:
                    converged = False
                positions[rid] = (cx, cy)

            # 3. Containment Clamping (contained_by edges)
            for edge in edges:
                if edge["relation"] == "contained_by":
                    child, parent = edge["from"], edge["to"]
                    if child in positions and parent in positions:
                        pcx, pcy = positions[parent]
                        ccx, ccy = positions[child]
                        # Clamp child within parent's rough radius
                        positions[child] = (
                            max(4, min(GRID_SIZE-4, pcx + np.clip(ccx-pcx, -8, 8))),
                            max(4, min(GRID_SIZE-4, pcy + np.clip(ccy-pcy, -8, 8)))
                        )

            if converged: break
            
        return positions

def solve_layout(spatial_authority: Dict, seed: int = ENGINE_SEED) -> Dict[str, Dict]:
    return DeterministicSpatialSolver(spatial_authority, seed).solve()
