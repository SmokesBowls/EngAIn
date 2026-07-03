# LibreSprite Code Blueprint (v1)

This document is the **Instruction Forge** blueprint for the LibreSprite starter set parser family. It defines the exact file locations, allowed imports, type annotations, structures, and function skeletons required for implementation.

---

## 1. Directory Layout

The starter set must be placed in a package module under the `trixel/` lane:

```text
trixel/
  libresprite/
    ├── __init__.py
    ├── ls_sprite_parser_mr.py
    ├── ls_palette_parser_mr.py
    ├── ls_cel_parser_mr.py
    ├── ls_image_parser_mr.py
    └── ls_semantic_parser_mr.py
```

---

## 2. Boundary Architecture

```text
LIBRA_KNOWS_LOCAL_PAYLOAD_SHAPE = TRUE
LIBRA_DEFINES_PAYLOAD_SHAPE = FALSE
LIBRA_KNOWS_FINAL_ENGAINOS_PACKET = FALSE
CONDUCTOR_SHAPES_PAYLOAD = TRUE
CONDUCTOR_WRAPS_FOR_ENGAINOS = TRUE
```

* `LsSemanticAdapter` does **not** instantiate runtime entities. It produces an asset-semantic *proposal* (`EngainEntitySemantic`) from art truth.
* Trixel owns the art/asset truth. The Conductor is responsible for wrapping/normalizing/rejecting the payload for EngAInOS ingestion.

---

## 3. Code Blueprints & Skeletons

### File 1: `trixel/libresprite/__init__.py`
**Imports & Exports Contract:**

```python
"""
Trixel LibreSprite Parser Family package initialization.
This package handles visual asset parsing and semantic mapping on the Trixel-side boundary.
"""
from __future__ import annotations

from .ls_sprite_parser_mr import LsSpriteMetadata, parse_sprite_metadata
from .ls_palette_parser_mr import LsPaletteColor, LsPalette, parse_palette
from .ls_cel_parser_mr import LsCel, LsFrameTag, parse_cels, parse_frame_tags
from .ls_image_parser_mr import LsImageBuffer, LsImageAnalysis, analyze_image_buffer
from .ls_semantic_parser_mr import (
    ColorMode,
    PlayDirection,
    CollisionType,
    EntityType,
    EngainEntitySemantic,
    LsSemanticRules,
    LsSemanticAdapter,
)

__all__ = [
    "LsSpriteMetadata", "parse_sprite_metadata",
    "LsPaletteColor", "LsPalette", "parse_palette",
    "LsCel", "LsFrameTag", "parse_cels", "parse_frame_tags",
    "LsImageBuffer", "LsImageAnalysis", "analyze_image_buffer",
    "ColorMode", "PlayDirection", "CollisionType", "EntityType",
    "EngainEntitySemantic", "LsSemanticRules", "LsSemanticAdapter",
]
```

---

### File 2: `trixel/libresprite/ls_sprite_parser_mr.py`
**Document settings and metadata parser.**

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Literal

ColorMode = Literal["RGB", "RGBA", "INDEXED", "GRAYSCALE"]

@dataclass(frozen=True)
class LsSpriteMetadata:
    filename: str
    width: int
    height: int
    color_mode: ColorMode
    layer_count: int
    frame_count: int
    palette_name: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "width": self.width,
            "height": self.height,
            "color_mode": self.color_mode,
            "layer_count": self.layer_count,
            "frame_count": self.frame_count,
            "palette_name": self.palette_name,
        }

def parse_sprite_metadata(source: Union[Path, dict]) -> LsSpriteMetadata:
    """
    Parses top-level sprite properties.
    
    Allows two paths:
      1. Path: Reads file directly or via CLI query wrapper.
      2. dict: Standard deserialized document configuration payload.
    """
    if isinstance(source, dict):
        return LsSpriteMetadata(
            filename=source["filename"],
            width=int(source["width"]),
            height=int(source["height"]),
            color_mode=source["color_mode"],
            layer_count=int(source["layer_count"]),
            frame_count=int(source["frame_count"]),
            palette_name=source.get("palette_name"),
        )
    
    # Path binary-reading fallback logic
    raise NotImplementedError("Direct binary file parsing is deferred; use JSON snapshot source.")
```

---

### File 3: `trixel/libresprite/ls_palette_parser_mr.py`
**Palette metadata and color system mapper.**

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Sequence

@dataclass(frozen=True)
class LsPaletteColor:
    r: int
    g: int
    b: int
    a: int = 255
    index: Optional[int] = None
    label: Optional[str] = None

    def to_hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}{self.a:02X}"

    def to_dict(self) -> dict:
        return {
            "r": self.r,
            "g": self.g,
            "b": self.b,
            "a": self.a,
            "hex": self.to_hex(),
            "index": self.index,
            "label": self.label,
        }

@dataclass(frozen=True)
class LsPalette:
    name: str
    colors: tuple[LsPaletteColor, ...]
    columns: int = 0

    def get_color_by_index(self, idx: int) -> Optional[LsPaletteColor]:
        if 0 <= idx < len(self.colors):
            return self.colors[idx]
        return None

    def match_nearest(self, r: int, g: int, b: int, a: int = 255) -> LsPaletteColor:
        """Finds closest color in the palette using Euclidean distance in RGBA space."""
        best_dist = float("inf")
        best_color = self.colors[0]
        for color in self.colors:
            dist = (
                (color.r - r) ** 2 +
                (color.g - g) ** 2 +
                (color.b - b) ** 2 +
                (color.a - a) ** 2
            )
            if dist < best_dist:
                best_dist = dist
                best_color = color
        return best_color

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "columns": self.columns,
            "colors": [c.to_dict() for c in self.colors],
        }

def parse_palette(source: Union[Path, dict]) -> LsPalette:
    """Parses color data from GPL/PAL/HEX path sources or structured dictionaries."""
    if isinstance(source, dict):
        colors = []
        for idx, entry in enumerate(source.get("colors", [])):
            colors.append(LsPaletteColor(
                r=entry["r"],
                g=entry["g"],
                b=entry["b"],
                a=entry.get("a", 255),
                index=entry.get("index", idx),
                label=entry.get("label"),
            ))
        return LsPalette(
            name=source.get("name", "unknown_palette"),
            colors=tuple(colors),
            columns=source.get("columns", 0),
        )
        
    raise NotImplementedError("Direct GPL/PAL/HEX file reading is deferred; use JSON snapshot source.")
```

---

### File 4: `trixel/libresprite/ls_cel_parser_mr.py`
**Animation timeline cel layout and tags tracker.**

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Sequence, Literal

PlayDirection = Literal["forward", "reverse", "pingpong"]

@dataclass(frozen=True)
class LsCel:
    frame_index: int
    layer_name: str
    x: int
    y: int
    width: int
    height: int
    is_linked: bool
    image_ref_id: str

@dataclass(frozen=True)
class LsFrameTag:
    name: str
    from_frame: int
    to_frame: int
    play_direction: PlayDirection

def parse_cels(source: Union[Path, Sequence[dict]]) -> tuple[LsCel, ...]:
    if isinstance(source, list) or isinstance(source, tuple):
        cels = []
        for entry in source:
            cels.append(LsCel(
                frame_index=int(entry["frame_index"]),
                layer_name=entry["layer_name"],
                x=int(entry["x"]),
                y=int(entry["y"]),
                width=int(entry["width"]),
                height=int(entry["height"]),
                is_linked=bool(entry.get("is_linked", False)),
                image_ref_id=entry["image_ref_id"],
            ))
        return tuple(cels)
        
    raise NotImplementedError("Binary timeline parsing is deferred; use JSON snapshot lists.")

def parse_frame_tags(source: Union[Path, Sequence[dict]]) -> tuple[LsFrameTag, ...]:
    if isinstance(source, list) or isinstance(source, tuple):
        tags = []
        for entry in source:
            tags.append(LsFrameTag(
                name=entry["name"],
                from_frame=int(entry["from_frame"]),
                to_frame=int(entry["to_frame"]),
                play_direction=entry.get("play_direction", "forward"),
            ))
        return tuple(tags)

    raise NotImplementedError("Binary timeline tag parsing is deferred; use JSON snapshot lists.")
```

---

### File 5: `trixel/libresprite/ls_image_parser_mr.py`
**Visual pixel analysis, silhouette hulls, and anchor metrics parser.**

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Literal

ColorMode = Literal["RGB", "RGBA", "INDEXED", "GRAYSCALE"]

@dataclass(frozen=True)
class LsImageBuffer:
    width: int
    height: int
    format: ColorMode
    pixels: bytes

@dataclass(frozen=True)
class LsImageAnalysis:
    image_id: str
    occupied_bounds: tuple[int, int, int, int]
    silhouette_mask: bytes
    anchors: Mapping[str, tuple[int, int]]
    cleaned_pixels: bytes

def analyze_image_buffer(
    buffer: LsImageBuffer, 
    anchor_color_map: Mapping[tuple[int, int, int, int], str]
) -> LsImageAnalysis:
    """
    Scans the raw image pixels to:
      1. Establish occupied non-transparent bounding box dimensions.
      2. Record coordinates of marker pixels mapping to target system labels.
      3. Clean the marker pixels (overwriting with transparency) to construct cleaned_pixels.
    """
    # Exclude markers, extract bounding limits, and output trace data.
    # Implementation details are delegated to the builder.
    pass
```

---

### File 6: `trixel/libresprite/ls_semantic_parser_mr.py`
**The Semantic Adapter mapping layouts, layers, tags, and markers to engine concepts.**

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence, Literal
from .ls_sprite_parser_mr import LsSpriteMetadata
from .ls_cel_parser_mr import LsCel, LsFrameTag
from .ls_image_parser_mr import LsImageAnalysis

CollisionType = Literal["none", "solid", "hazard", "slope"]
EntityType = Literal["actor", "prop", "projectile", "tile", "ui", "fx"]

@dataclass(frozen=True)
class EngainEntitySemantic:
    entity_id: str
    entity_type: EntityType
    states: dict[str, tuple[int, ...]]
    colliders: dict[str, tuple[int, int, int, int]]
    hotspots: dict[str, tuple[int, int]]
    layer_grouping: dict[str, tuple[str, ...]]

@dataclass(frozen=True)
class LsSemanticRules:
    layer_rules: Mapping[str, str]      # Prefix rule maps
    tag_rules: Mapping[str, str]        # Animation tag maps
    palette_rules: Mapping[str, str]    # Palette ramps maps
    anchor_rules: Mapping[str, str]     # Hotspot / alignment maps

class LsSemanticAdapter:
    def __init__(self, rules: LsSemanticRules):
        self.rules = rules

    def compile(
        self,
        meta: LsSpriteMetadata,
        cels: Sequence[LsCel],
        tags: Sequence[LsFrameTag],
        analyses: Mapping[str, LsImageAnalysis]
    ) -> EngainEntitySemantic:
        """
        Combines sprite parameters, active cell offsets, frame labels, 
        and bounding masks to yield an EngainEntitySemantic proposal object.
        """
        # Rules logic evaluation
        pass
```

---

## 4. Verification Gates

All files must pass the implementation validator:

```python
def verify_starter_set_gate(
    meta: LsSpriteMetadata,
    cels: tuple[LsCel, ...],
    tags: tuple[LsFrameTag, ...],
    analyses: dict[str, LsImageAnalysis],
    rules: LsSemanticRules
) -> tuple[bool, str]:
    """
    Verifies that the parser outputs conform to the Trixel boundary contract.
    Returns (True, "OK") if all gates pass, otherwise (False, failure_reason).
    """
    # 1. Check colors structure
    # 2. Check mask source traces exist
    # 3. Compile adapter output
    # 4. Enforce read-only constraint (no engine state mutated)
    pass
```
