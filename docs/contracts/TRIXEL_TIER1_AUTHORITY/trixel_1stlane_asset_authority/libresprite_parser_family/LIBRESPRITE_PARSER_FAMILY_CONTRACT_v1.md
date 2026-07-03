# LibreSprite Parser Family Contract (v1)

This contract defines the architecture, authority boundaries, and execution gates for the LibreSprite parser family integration.

---

## 1. Purpose

The LibreSprite parser family acts strictly as a **Trixel-side asset extraction and parsing package**. Its sole responsibility is to translate raw visual and structural data from LibreSprite documents into normalized asset-semantic proposals. It does **not** manage or run gameplay logic.

```text
LibreSprite Document/Art Truth 
            │
            ▼
   ls_*_parser_mr.py  (Parser family)
            │
            ▼
  LsSemanticAdapter  (Produces asset-semantic proposals)
            │
            ▼
Trixel Asset Authority / Handoff
```

---

## 2. Authority Boundary & Conductor Split

> [!IMPORTANT]
> **Trixel Conductor shapes the payload; Libra fills the payload.**
>
> Libra (LibreSprite parser family) does not invent the payload. It does not decide what EngAInOS needs, and it does not know the final EngAInOS-facing packet shape. It only knows the local payload contract provided by the Trixel Conductor.

```text
Conductor knows:
  - why the payload is needed
  - what system asked for it
  - what EngAInOS will expect
  - what authority boundary applies
  - how to wrap/normalize/reject it

Libra knows:
  - what fields to extract
  - what dataclasses to emit
  - what types are allowed
  - what fields are forbidden
  - how to serialize its local payload
  - where its lane ends
```

### Boundary Rule Gates
```text
LIBRA_KNOWS_LOCAL_PAYLOAD_SHAPE = TRUE
LIBRA_DEFINES_PAYLOAD_SHAPE = FALSE
LIBRA_KNOWS_FINAL_ENGAINOS_PACKET = FALSE
CONDUCTOR_SHAPES_PAYLOAD = TRUE
CONDUCTOR_WRAPS_FOR_ENGAINOS = TRUE
```

* `LsSemanticAdapter` does **not** instantiate or mutate runtime EngAIn entities. It produces a local asset-semantic proposal (`EngainEntitySemantic`) from LibreSprite-authored art.
* The Conductor receives the payload, validates/normalizes it, and wraps it into a Conductor packet.
* EngAInOS maintains complete authority over accepting, rejecting, or instantiating these proposals through its own gates. The parser family must remain decoupled from runtime state.

---

## 3. Starter Set Files

The package must be implemented under the following path schema:

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

## 4. Import Restraints

### Allowed Imports
* Python Standard Library (e.g., `typing`, `dataclasses`, `pathlib`, `json`, `re`, `struct`, `math`).
* Co-located relative imports within the `trixel.libresprite` package (e.g., `from .ls_sprite_parser_mr import LsSpriteMetadata`).

### Forbidden Imports
* Any direct imports of EngAIn runtime core systems, managers, databases, or active game loop modules.
* Direct imports of entities that mutate gameplay state or register actors into active environments.

---

## 5. Packet / Dataclass Outputs

The output structures are strictly data-containers (frozen dataclasses):

```python
from typing import Literal, Mapping, Sequence, Optional

ColorMode = Literal["RGB", "RGBA", "INDEXED", "GRAYSCALE"]
PlayDirection = Literal["forward", "reverse", "pingpong"]
CollisionType = Literal["none", "solid", "hazard", "slope"]
EntityType = Literal["actor", "prop", "projectile", "tile", "ui", "fx"]

@dataclass(frozen=True)
class LsSpriteMetadata:
    filename: str
    width: int
    height: int
    color_mode: ColorMode
    layer_count: int
    frame_count: int
    palette_name: Optional[str] = None

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

@dataclass(frozen=True)
class LsSemanticRules:
    layer_rules: Mapping[str, str]
    tag_rules: Mapping[str, str]
    palette_rules: Mapping[str, str]
    anchor_rules: Mapping[str, str]

@dataclass(frozen=True)
class EngainEntitySemantic:
    entity_id: str
    entity_type: EntityType
    states: dict[str, tuple[int, ...]]
    colliders: dict[str, tuple[int, int, int, int]]
    hotspots: dict[str, tuple[int, int]]
    layer_grouping: dict[str, tuple[str, ...]]
```

---

## 6. Execution Gates

```text
LIBRESPRITE_STARTER_SET_GATE
```

### TRUE when:
* All five starter files exist in the `trixel/libresprite/` directory.
* Every module imports cleanly without external runner dependencies.
* All dataclasses serialize fully to JSON/dict equivalents without data loss.
* `LsPalette.to_dict()` retains full RGBA channel color definitions.
* `LsImageAnalysis` preserves the source-trace pixels alongside the marker-removed `cleaned_pixels` mask.
* `LsSemanticAdapter.compile()` yields a standalone `EngainEntitySemantic` proposal object.
* No module attempts to instantiate runtime entities or modify environment states.

### FALSE when:
* Parsers import runtime engine authority models directly.
* The adapter mutates global state or registers gameplay actors directly.
* Bounding hull or state estimation is assumed to be runtime truth instead of a proposal.
* Quantization or palette indexing discards actual RGBA channel representations.

---

## 7. Vertical Slice Proof

A validation script must be able to perform this sequential workflow:

1. **Load/Mock**: Ingest metadata snapshot or target binary.
2. **Collect Topology**: Extract layers, cels, and frame tags.
3. **Analyze Buffers**: Process cell pixel data, generating silhouette masks, occupied boundaries, and anchoring offsets (removing target marker pixels).
4. **Compile Proposal**: Feed collections and semantic rulesets (layer prefixes, state triggers, anchoring patterns) into `LsSemanticAdapter.compile()`.
5. **Verify Handoff**: Assert output is a serializable `EngainEntitySemantic` dataclass ready for engine ingestion.
