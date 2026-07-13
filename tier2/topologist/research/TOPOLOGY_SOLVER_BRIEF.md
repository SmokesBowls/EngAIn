# Topology-to-Coordinates Solver Brief: Coordinate Axis Alignment & Remapping Contract

## 1. Problem Statement

A critical axis misalignment exists between the 2D heightfield terrain grid (`WorldField`) and the 3D physics/spatial runtime (`SpatialEntity`). If not explicitly reconciled, layout solvers will wire ground-plane coordinates incorrectly, leading to entities being buried, floating, or placed at wrong offsets.

### Coordinate Space Definitions

1. **`SpatialEntity.pos` (3D Vector Space)**
   - Used by `spatial3d_mr.py` / `SpatialEntity` and the physics integration loop.
   - **Gravity**: Defaults to `(0.0, -9.81, 0.0)` pulling along **-Y**.
   - **Axes**:
     - **X**: Horizontal right/left axis.
     - **Y**: Vertical up/down elevation axis.
     - **Z**: Horizontal forward/backward depth axis.

2. **`WorldField` (Chunked 2D Float Heightfield)**
   - Used by `world_field_nucleus.py` and `terrain_thresholds.py` to represent the heightmap of the terrain.
   - **Axes**:
     - **world_x**: Horizontal axis.
     - **world_y**: Horizontal axis (ground-plane grid).
     - **stored value (float)**: Elevation at coordinate `(world_x, world_y)`.

---

## 2. Non-Negotiable Solver Constraints

Any "topology → coordinates" solver or compiler mapping a qualitative topology artifact (`ProseTopologyArtifact`) and/or `WorldField` into concrete 3D positions (`SpatialEntity.pos` or `position_godot`) MUST follow this alignment contract:

### A. Explicit Axis Remap Step
The solver must not map the horizontal ground axis `world_y` from `WorldField` directly to `SpatialEntity.pos.y`. Instead, it must map:
- **`SpatialEntity.pos.x`** $\leftarrow$ **`WorldField.world_x`** (horizontal)
- **`SpatialEntity.pos.z`** $\leftarrow$ **`WorldField.world_y`** (horizontal)
- **`SpatialEntity.pos.y`** $\leftarrow$ **`WorldField.elevation_value`** (vertical)

```
       WorldField (2D Grid + Value)              SpatialEntity (3D Space)
       ┌──────────────────────────┐              ┌────────────────────────┐
       │ world_x (Horizontal)     │  ─────────►  │ pos.x (Horizontal X)   │
       │ world_y (Horizontal)     │  ─────────►  │ pos.z (Horizontal Z)   │
       │ elevation (Float Value)  │  ─────────►  │ pos.y (Vertical Y)     │
       └──────────────────────────┘              └────────────────────────┘
```

### B. Vertical Offset and Ground Alignment
1. **Vertical Pivot Alignment**: When placing a character/entity on the terrain, the vertical height `pos.y` should represent the foot contact level (ground level).
2. **Offset Compensation**: If an entity's mesh/shape is defined from its center, the solver must apply a vertical offset:
   $$\text{pos.y} = \text{elevation} + \text{height\_offset}$$
   where $\text{height\_offset} = \text{height} / 2$ to ensure the entity stands on the terrain surface instead of sinking halfway into the floor.

---

## 3. Reference Implementations and Conversions

For downstream engines (e.g., Godot vs. UPBGE/Blender):
- **Godot (standard)**: Uses Y-Up. Coordinates remain aligned with `SpatialEntity` (Y is vertical).
- **UPBGE/Blender**: Uses Z-Up. Axis conversion is defined in `bridge_integration.py` (`_godot_to_upbge_pos`) as:
  - `x_upbge` = `x_godot`
  - `y_upbge` = `-z_godot`
  - `z_upbge` = `y_godot` (which maps the vertical Y-Up to Z-Up).

---

## 4. Open Precision Gaps & Design Conventions

To ensure the solver compiles accurately and works consistently across all subsystems, the following gaps and design choices must be explicitly addressed:

### A. Horizontal Mapping Axis Convention
The mapping of `WorldField` ground axes to `SpatialEntity` 3D axes:
$$\text{pos.x} \leftarrow \text{world\_x}$$
$$\text{pos.z} \leftarrow \text{world\_y}$$
is a chosen convention to preserve horizontal relationships.
- **Enforcement**: This horizontal mapping must be mirrored identically across Trixel painting, `WorldField` edits, and entity placement. Any mismatch (e.g., swapping `x` and `z` in one subsystem) will result in a world that appears rotated or mirrored between subsystems.
- **Convention Audit**: The solver must lock this mapping as canonical and enforce it globally across all runtime layout engines.

### B. PGT-to-3D-Engine Unit Scale Conversion
The `height` value used for the pivot offset $\left(\text{height\_offset} = \text{height} / 2\right)$ is defined in the entity's PGT envelope (e.g., standard human height = 10 PGT units in `topological spacing.txt`).
- **Missing Conversion Factor**: Currently, the documentation only defines visual pixel scale (`1 PGT unit = 10 pixels`), but does not define the ratio between PGT units and Godot/UPBGE 3D units.
- **Scale Example**: If a standard human placeholder capsule is 1.8 meters tall in Godot/UPBGE 3D space:
  $$10 \text{ PGT units} = 1.8 \text{ Godot/UPBGE 3D units}$$
  $$1 \text{ PGT unit} = 0.18 \text{ Godot/UPBGE 3D units}$$
- **Required Solver Action**: The solver must resolve the exact scaling factor $\sigma$ where:
  $$\text{height\_meters} = \text{height\_pgt} \times \sigma$$
  and apply this scale before executing any coordinate offset calculations.

