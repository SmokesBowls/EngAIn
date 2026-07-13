# MRLORE NARRATIVE CONCURRENCE CONTRACT v1

## Input

`accepted_spatial_truth` + `proposed_metric_layout` + `source_prose`

Required fields:

- from `accepted_spatial_truth`:
  - `packet_type = accepted_spatial_truth`
  - `entities`
  - `qslinks`
  - `olinks`
  - `movelinks`
- from `proposed_metric_layout`:
  - `packet_type = proposed_metric_layout`
  - `lifecycle = PROPOSED`
  - `entities` (with coordinate fields `x`, `y`, `z`)
- from `source_prose`:
  - The raw narrative text description matching the topology.

## Output

`narratively_concurred_metric_layout`

Required fields:

- `packet_type = narratively_concurred_metric_layout`
- `lifecycle = CONCURRED`
- `source_topology_artifact_id`
- `source_metric_layout_artifact_id`
- `concurrence_decision = CONCURRED`
- `contradictions`
- `unresolved_findings`
- `metric_layout` (containing the exact unaltered coordinates map)

## Authority

MrLore performs narrative concurrence over proposed spatial coordinates. The layout coordinates must preserve the qualitative relationships in the accepted spatial truth and contain no contradictions against the source prose. Successful concurrence transitions the proposal lifecycle to `CONCURRED`.

The packet remains non-canonical and non-runtime until subsequent EngAInOS authority verification is performed.

## Coordinate seam

- Horizontal grid spaces are not resolved here.
- Coordinated coordinates space must match `world_cell_y_up`.

## Forbidden output / acts

- Altering layout coordinates.
- Rerunning Cartographer.
- Inventing new narrative facts or canon.
- Rendering meshes or textures.
- Mutating simulation or game runtime.
