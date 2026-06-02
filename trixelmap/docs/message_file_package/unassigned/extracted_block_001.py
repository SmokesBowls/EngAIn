# trixelmap/spatial_layout_solver.py (revised)
"""
Tier 2 Resolution: Constraint graph → solved coordinates.
Deterministic quadrant-first placement with relationship refinement.
"""
import random
import numpy as np
from typing import Dict, List, Tuple, Optional

ENGINE_SEED = 42
GRID_SIZE = 100

# Hard quadrant anchors (normalized 0.0-1.0)
QUADRANT_ANCHORS = {
    "northwest": (0.20, 0.20),
    "northeast": (0.80, 0.20),
    "southwest": (0.20, 0.80),
    "southeast": (0.80, 0.80),
    "north": (0.50, 0.15),
    "south": (0.50, 0.85),
    "west": (0.15, 0.50),
    "east": (0.85, 0.50),
    "center": (0.50, 0.50),
    "east_coast": (0.90, 0.50),
    "west_coast": (0.10, 0.50),
    "north_coast": (0.50, 0.10),
    "south_coast": (0.50, 0.90),
}

REGION_SIZE_HINTS = {
    "light": 8,
    "medium": 14,
    "heavy": 22,
}


class DeterministicSpatialSolver:
    """
    Two-phase solver:
    Phase 1: Deterministic quadrant placement (hard constraints)
    Phase 2: Relationship refinement (soft constraints with repulsion)
    """
    
    def __init__(self, spatial_authority: Dict, seed: int = ENGINE_SEED):
        self.authority = spatial_authority
        self.rng = random.Random(seed)
        np.random.seed(seed)
        self.grid_size = GRID_SIZE
        
    def solve(self) -> Dict[str, Dict]:
        regions = self.authority.get("regions", {})
        edges = self.authority.get("edges", [])
        
        # Phase 1: Quadrant-based initial placement
        positions = self._phase1_quadrant_placement(regions)
        
        # Phase 2: Relationship refinement with repulsion
        positions = self._phase2_relationship_refinement(positions, regions, edges)
        
        # Rasterize bounds
        resolved = {}
        for rid, (cx, cy) in positions.items():
            rdata = regions[rid]
            size = REGION_SIZE_HINTS.get(rdata.get("size_hint", "medium"), 14)
            
            # Type-aware shaping
            if rdata.get("type") == "linear_spine":
                w, h = size * 1.8, size * 0.7
            else:
                w, h = size, size
            
            resolved[rid] = {
                "centroid": {"x": round(cx, 2), "y": round(cy, 2)},
                "bounds": {
                    "x_min": max(0, int(cx - w / 2)),
                    "y_min": max(0, int(cy - h / 2)),
                    "x_max": min(self.grid_size, int(cx + w / 2)),
                    "y_max": min(self.grid_size, int(cy + h / 2)),
                },
                "terrain_class": rdata.get("terrain_class", "default"),
                "type": rdata.get("type"),
                "landmarks": rdata.get("landmarks", []),
            }
        
        return {"version": "1.0", "grid_size": self.grid_size, "regions": resolved}
    
    def _phase1_quadrant_placement(self, regions: Dict) -> Dict[str, Tuple[float, float]]:
        """
        Place each region at its quadrant anchor with small deterministic jitter.
        This guarantees topology preservation from the start.
        """
        positions = {}
        
        for rid, rdata in regions.items():
            quadrant = rdata.get("quadrant_hint", "center")
            anchor = QUADRANT_ANCHORS.get(quadrant, QUADRANT_ANCHORS["center"])
            
            # Add small jitter to prevent exact overlap (±3 grid units)
            jitter_x = self.rng.uniform(-0.03, 0.03) * self.grid_size
            jitter_y = self.rng.uniform(-0.03, 0.03) * self.grid_size
            
            cx = anchor[0] * self.grid_size + jitter_x
            cy = anchor[1] * self.grid_size + jitter_y
            
            # Clamp to grid bounds
            cx = max(5, min(self.grid_size - 5, cx))
            cy = max(5, min(self.grid_size - 5, cy))
            
            positions[rid] = (cx, cy)
        
        return positions
    
    def _phase2_relationship_refinement(
        self,
        positions: Dict[str, Tuple[float, float]],
        regions: Dict,
        edges: List[Dict]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Apply relationship constraints with:
        - Strong repulsion to prevent collapse
        - Soft attraction for connected regions
        - Directional constraints (east_of, north_of, etc.)
        """
        max_iterations = 150
        learning_rate = 0.8
        
        for iteration in range(max_iterations):
            forces = {rid: [0.0, 0.0] for rid in positions}
            
            # 1. Repulsion: All regions repel each other (prevents collapse)
            region_ids = list(positions.keys())
            for i in range(len(region_ids)):
                for j in range(i + 1, len(region_ids)):
                    rid_a = region_ids[i]
                    rid_b = region_ids[j]
                    
                    pos_a = np.array(positions[rid_a])
                    pos_b = np.array(positions[rid_b])
                    
                    diff = pos_a - pos_b
                    dist = max(np.linalg.norm(diff), 1.0)
                    
                    # Strong repulsion force (inverse square law)
                    repulsion_strength = 15.0 / (dist ** 2)
                    direction = diff / dist
                    
                    forces[rid_a][0] += direction[0] * repulsion_strength
                    forces[rid_a][1] += direction[1] * repulsion_strength
                    forces[rid_b][0] -= direction[0] * repulsion_strength
                    forces[rid_b][1] -= direction[1] * repulsion_strength
            
            # 2. Relationship constraints (soft attraction/directional)
            for edge in edges:
                rid_from = edge["from"]
                rid_to = edge["to"]
                relation = edge["relation"].lower()
                
                pos_from = np.array(positions[rid_from])
                pos_to = np.array(positions[rid_to])
                
                diff = pos_to - pos_from
                dist = max(np.linalg.norm(diff), 1.0)
                
                # Determine constraint strength based on relation
                if "attach" in relation or "connect" in relation:
                    # Strong attraction to be adjacent
                    target_dist = 18.0
                    strength = 0.6
                elif "east_of" in relation:
                    # rid_to should be east of rid_from
                    if diff[0] < 0:  # Currently west, need to move east
                        strength = 0.8
                    else:
                        strength = 0.2  # Already correct, minor adjustment
                    target_dist = 25.0
                elif "west_of" in relation:
                    if diff[0] > 0:  # Currently east, need to move west
                        strength = 0.8
                    else:
                        strength = 0.2
                    target_dist = 25.0
                elif "north_of" in relation:
                    if diff[1] > 0:  # Currently south, need to move north
                        strength = 0.8
                    else:
                        strength = 0.2
                    target_dist = 25.0
                elif "south_of" in relation:
                    if diff[1] < 0:  # Currently north, need to move south
                        strength = 0.8
                    else:
                        strength = 0.2
                    target_dist = 25.0
                else:
                    # Generic proximity
                    target_dist = 30.0
                    strength = 0.3
                
                # Apply attraction/repulsion to reach target distance
                dist_error = dist - target_dist
                direction = diff / dist
                
                fx = direction[0] * dist_error * strength * 0.1
                fy = direction[1] * dist_error * strength * 0.1
                
                forces[rid_from][0] -= fx
                forces[rid_from][1] -= fy
                forces[rid_to][0] += fx
                forces[rid_to][1] += fy
            
            # 3. Apply forces with damping
            converged = True
            for rid in positions:
                fx, fy = forces[rid]
                
                # Dampen forces
                fx *= learning_rate
                fy *= learning_rate
                
                cx, cy = positions[rid]
                new_cx = cx + fx
                new_cy = cy + fy
                
                # Clamp to grid
                new_cx = max(5, min(self.grid_size - 5, new_cx))
                new_cy = max(5, min(self.grid_size - 5, new_cy))
                
                if abs(fx) > 0.5 or abs(fy) > 0.5:
                    converged = False
                
                positions[rid] = (new_cx, new_cy)
            
            if converged:
                break
        
        return positions


def solve_layout(spatial_authority: Dict, seed: int = ENGINE_SEED) -> Dict[str, Dict]:
    """
    Main entry point: Deterministic spatial solving.
    """
    solver = DeterministicSpatialSolver(spatial_authority, seed)
    return solver.solve()
