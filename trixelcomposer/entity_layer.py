"""entity_layer.py — entity overlay, separate from the terrain raster.

Entity positions are semantic data.  They must not be baked into PNG pixels
where they lose identity, become immovable, and collapse into whatever the
terrain renderer last painted over them.

This module is the stub home for entity data as it moves through the
rendering pipeline.  The terrain tile (PNG) and the entity layer (JSON
sidecar) are produced together but kept separate so any downstream system
— Godot, the dragon perception layer, a compositor — can handle them
independently.

Integration points (not yet wired):
    tile_address.py     world-cell / face / normal per entity
    scene_server.py     compile_recipe injects entities into the pass dict
    terminal_trixel.py  RecipeRenderer routes entity_marker → here, not canvas
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EntityMarker:
    """One entity positioned on a tile surface."""
    id:          str
    name:        str
    nx:          float                          # normalised x on tile [0.0, 1.0]
    marker_y:    float                          # normalised y (depth) on tile [0.0, 1.0]
    color:       Tuple[int, int, int]
    world_cell:  Optional[Tuple[int, int, int]] = None  # filled when TileAddress is known

    def tile_pixel(self, canvas_width: int, canvas_height: int) -> Tuple[int, int]:
        """Logical pixel position — reference only, not rendered into the raster."""
        x = int(round(self.nx       * (canvas_width  - 1)))
        y = int(round(self.marker_y * (canvas_height - 1)))
        return x, y


@dataclass
class EntityLayer:
    """All entity markers for one rendered tile, kept out of the raster."""
    scene_id:      str
    recipe:        str
    canvas_width:  int
    canvas_height: int
    markers:       List[EntityMarker] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id":      self.scene_id,
            "recipe":        self.recipe,
            "canvas_width":  self.canvas_width,
            "canvas_height": self.canvas_height,
            "markers": [asdict(m) for m in self.markers],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


def from_recipe_pass(
    scene_id:      str,
    recipe_name:   str,
    pass_data:     Dict[str, Any],
    canvas_width:  int = 16,
    canvas_height: int = 16,
) -> Optional[EntityLayer]:
    """Build an EntityLayer from an entity_marker pass dict.

    Returns None when the pass carries no entity list — recipe files often
    declare entity_marker config (marker_y, color) without injected positions,
    meaning there are no scene entities for this tile.
    """
    entities = pass_data.get("entities")
    if not entities:
        return None

    marker_y = float(pass_data.get("marker_y", 0.72))
    color    = tuple(int(c) for c in pass_data.get("color", [255, 255, 100]))

    markers = [
        EntityMarker(
            id=e.get("id", "unknown"),
            name=e.get("name", "?"),
            nx=float(e.get("nx", 0.5)),
            marker_y=marker_y,
            color=color,
        )
        for e in entities
    ]

    return EntityLayer(
        scene_id=scene_id,
        recipe=recipe_name,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        markers=markers,
    )
