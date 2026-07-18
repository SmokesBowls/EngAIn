# TRIXEL 3.2D SURFACE REQUEST CONTRACT v1

## Goal Description

Establish a self-contained handshake spine between the EngAIn runtime and Trixel 3.2D to request and produce verified, mathematically complete 3D surface geometry from a 2D height field.

---

## 1. Request Contract

Packet Type: `trixel32d_surface_request`

### Orientation & Axis Mapping
The request must explicitly bind 2D grid/field coordinates to 3D spatial directions under `orientation`:
```json
"orientation": {
  "basis_authority": "VECTORS",
  "field_axis_binding": {
    "field_x_increases_along": "RIGHT",
    "field_y_increases_along": "FORWARD"
  },
  "vectors": {
    "forward": [0.70710678, 0.0, -0.70710678],
    "right": [0.70710678, 0.0, 0.70710678],
    "up": [0.0, 1.0, 0.0]
  },
  "tolerance": 0.0001
}
```

#### Normative Projection Equations
```text
column_offset = (field_x - center_column) × cell_width
row_offset    = (field_y - center_row) × cell_depth

top_center = right × column_offset + forward × row_offset + up × elevation

half_right   = right × (cell_width / 2)
half_forward = forward × (cell_depth / 2)
```

#### Normalized Working-Vector Rule
For numerical stability and exact geometry alignment, processors must normalize `right`, `forward`, and `up` to unit length (length = 1.0 exactly in float precision) immediately after raw vector checks pass. These normalized vectors must be used exclusively for coordinate projection, corner calculation, normal vector math, boundary checking, extrusion math, and yaw calculation.

### Coordinate Space Policy
Enforces standard Y-up coordinate orientation:
- `coordinate_space = WORLD_FIELD_GRID_TO_LOCAL_Y_UP`
- `up_axis_policy = MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION` (i.e. `up` must equal `[0, 1, 0]` within `tolerance`).

### Field Coverage Model
Supports `DENSE` field configurations where all coordinates in the grid must exist exactly once.
```json
"planar_config": {
  "field_width_columns": 3,
  "field_height_rows": 2,
  "field_coverage": "DENSE",
  "cell_width": 0.1,
  "cell_depth": 0.1,
  "center_column": 1.0,
  "center_row": 0.5
}
```
Validation rules:
- `pixel_field_data.length == field_width_columns × field_height_rows`
- `field_x` must be from 0 inclusive to `field_width_columns` exclusive for all cells.
- `field_y` must be from 0 inclusive to `field_height_rows` exclusive for all cells.
- Every coordinate in that grid must appear exactly once. Duplicate or missing coordinates -> REJECTED.

### Gap Fill Policy
Mandates exact independent per-cell extrusion to ensure predictable rendering outputs:
```json
"gap_fill": {
  "enabled": true,
  "mode": "PER_CELL_EXTRUSION",
  "adjacency_policy": "ALL_FACES_INDEPENDENT",
  "resolved_color": [0.35, 0.35, 0.35, 1.0],
  "thickness_local_units": 0.025
}
```
Rule: Each cell generates exactly 5 gap-fill faces (1 bottom + 4 vertical sides). No face culling or height bridging occurs.

---

## 2. Response / Handshake Contract

Packet Type: `trixel32d_surface_built`

### Identity-complete response envelope

Every response must carry:

```json
{
  "contract": "trixel32d_surface_built.v1",
  "packet_type": "trixel32d_surface_built",
  "request_id": "t32dreq_<16-lowercase-hex>",
  "surface_id": "t32dsurface_<16-lowercase-hex> or null",
  "status": "BUILT or REJECTED"
}
```

Rules:

- `contract` and `packet_type` are exact, not compatibility hints.
- Validation requires a separately supplied trusted accepted request. The request
  must pass the complete `trixel32d_surface_request` validator before any response
  identity can be accepted. A response must not embed or self-supply its own
  `request_context`.
- `request_id` must exactly equal the trusted request's
  `identity.request_id`.
- `topology_policy` must exactly equal the trusted request's
  `construction.topology_policy`; the response may not select or rewrite topology.
- For `BUILT`, `surface_id` must equal:

```text
"t32dsurface_" + first_16_lowercase_hex(
    SHA-256(request_id + ":" + topology_policy)
)
```

- For `REJECTED`, `surface_id` must be null and all geometry/provenance arrays
  must be empty.
- Root objects are closed-world by status. Missing or unknown root fields reject.
- Wrong JSON types at any traversed response node reject rather than escaping the
  boundary as exceptions.
- JSON nesting deeper than 64 container levels rejects before immutable packet
  construction.
- Duplicate JSON keys and nonstandard numeric constants (`NaN`, `Infinity`,
  `-Infinity`) reject before semantic validation.

The deterministic `surface_id` identifies the request/topology build identity.
It does not replace exact artifact-byte identity.

### Exact-byte validation and application binding

The EngAIn boundary must read one byte buffer once, calculate SHA-256 from that
buffer, and parse that same buffer. On success it returns both a deeply immutable
validated packet and the calculated response SHA-256. An independently trusted
expected SHA-256 may additionally lock a persisted fixture or transport artifact.

The response must not contain a self-referential checksum field. The calculated
SHA-256 is validator evidence consumed by later authorization contracts such as
`trixel32d_surface_apply.v1`.

Canonical first-proof lock:

```text
tier1/engainos/tests/fixtures/trixel32d_surface_built_3x2_first_proof.json
sha256 = bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929
request_id = t32dreq_8b14a3bac98d1025
surface_id = t32dsurface_0f5d9d7e96ed734a
```

### Rejection Semantics and Statuses
Validation is strictly fail-fast.

- `REJECTED`:
  - Request is invalid.
  - `geometry = null`
  - `errors` contains the first validation failure.
- `BUILT`:
  - Every requested cell was successfully built.
  - `rejected_cells` is empty.
  - `geometry` contains all cell range outputs.
  - `errors` is empty.

### Coordinate Space Policy
- `local_spatial_metadata.coordinate_space = TRIXEL_LOCAL_Y_UP`

### Cell Provenance Self-Description
Each cell's geometry must be self-describing, specifying start and count indices:
```json
"cell_geometry_ranges": [
  {
    "cell_key": "0,0",
    "source_cell_ordinal": 0,
    "field_x": 0,
    "field_y": 0,
    "surfaces": [
      {
        "role": "PRIMARY_PIXEL_FACE",
        "vertex_start": 0,
        "vertex_count": 4,
        "index_start": 0,
        "index_count": 6
      },
      {
        "role": "NEUTRAL_GAP_FILL",
        "vertex_start": 0,
        "vertex_count": 20,
        "index_start": 0,
        "index_count": 30
      }
    ]
  }
]
```

### Ordering Contract
- Cells must be emitted in row-major order:
  - Outer loop: `field_y` from 0 inclusive to `field_height_rows` exclusive.
  - Inner loop: `field_x` from 0 inclusive to `field_width_columns` exclusive.
- Faces within each cell must be emitted in order:
  1. PRIMARY_PIXEL_FACE (top)
  2. NEUTRAL_GAP_FILL bottom face
  3. NEUTRAL_GAP_FILL -field_y side (negative row)
  4. NEUTRAL_GAP_FILL +field_x side (positive column)
  5. NEUTRAL_GAP_FILL +field_y side (positive row)
  6. NEUTRAL_GAP_FILL -field_x side (negative column)

---

## 3. Asymmetric 3×2 Proof Fixture Request Example

```json
{
  "packet_type": "trixel32d_surface_request",
  "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
  "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
  "orientation": {
    "basis_authority": "VECTORS",
    "field_axis_binding": {
      "field_x_increases_along": "RIGHT",
      "field_y_increases_along": "FORWARD"
    },
    "vectors": {
      "forward": [0.70710678, 0.0, -0.70710678],
      "right": [0.70710678, 0.0, 0.70710678],
      "up": [0.0, 1.0, 0.0]
    },
    "tolerance": 0.0001
  },
  "planar_config": {
    "field_width_columns": 3,
    "field_height_rows": 2,
    "field_coverage": "DENSE",
    "cell_width": 0.1,
    "cell_depth": 0.1,
    "center_column": 1.0,
    "center_row": 0.5
  },
  "gap_fill": {
    "enabled": true,
    "mode": "PER_CELL_EXTRUSION",
    "adjacency_policy": "ALL_FACES_INDEPENDENT",
    "resolved_color": [0.35, 0.35, 0.35, 1.0],
    "thickness_local_units": 0.025
  },
  "pixel_field_data": [
    {"field_x": 0, "field_y": 0, "elevation": 1.0, "base_color": [1.0, 0.0, 0.0, 1.0]},
    {"field_x": 0, "field_y": 1, "elevation": 4.0, "base_color": [0.0, 0.0, 1.0, 1.0]},
    {"field_x": 1, "field_y": 0, "elevation": 2.0, "base_color": [0.0, 1.0, 0.0, 1.0]},
    {"field_x": 1, "field_y": 1, "elevation": 5.0, "base_color": [1.0, 1.0, 0.0, 1.0]},
    {"field_x": 2, "field_y": 0, "elevation": 3.0, "base_color": [1.0, 0.0, 1.0, 1.0]},
    {"field_x": 2, "field_y": 1, "elevation": 6.0, "base_color": [0.0, 1.0, 1.0, 1.0]}
  ]
}
```
