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
