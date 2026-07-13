# CARTOGRAPHER METRIC LAYOUT CONTRACT v1

## Input

`accepted_spatial_truth`

Required fields:

- `packet_type = accepted_spatial_truth`
- `source_artifact_id`
- `entities`
- `qslinks`
- `olinks`
- `movelinks`

## Output

`engain.cartographer_metric_layout.v1`

Required fields:

- `artifact_id`
- `source_artifact_id`
- `source_packet_hash`
- `lifecycle`
- `coordinate_space = world_cell_y_up`
- `unit = meter`
- `axis_contract`
- `anchor_entity_id`
- `entities`
- `applied_constraints`
- `unresolved_constraints`

## Authority

Cartographer may concretize accepted qualitative topology into one deterministic
metric proposal. The proposal remains non-canonical until MrLore narrative
concurrence and EngAInOS contract/authority verification both succeed.

## Coordinate seam

- `x` is east/west.
- `y` is vertical/up.
- `z` is north/south/depth.
- `worldfield_grid` is not accepted as this packet's coordinate space.
- WorldField elevation is not resolved by this contract.

## Forbidden output

- images;
- sprites;
- textures;
- palettes;
- atlases;
- materials;
- meshes;
- Trixel packet fields;
- Godot scene or node fields;
- runtime mutation commands;
- canon decisions.

## Lifecycle

- solver writes `DRAFT`;
- technical validator reports pass/fail;
- Cartographer gate may advance `DRAFT` to `PROPOSED`;
- only later lanes may concur with or authorize the proposal.
