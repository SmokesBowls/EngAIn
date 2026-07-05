# GODOT MCP PROBE CONTRACT v1

STATUS: CANDIDATE_PROBE

## Purpose

This lane evaluates whether a Godot MCP server can safely reduce raw `.tscn` text-templating, stdout-grep fragility, and hand-written scene mutation risk inside EngAIn/GodotSim.

## Candidate Tools

PRIMARY_CANDIDATE: hi-godot/godot-ai
SECONDARY_CANDIDATE: mkdevkit/godot-mcp

## Authority Boundary

Godot MCP is not authority.
Godot MCP is not EngAInOS.
Godot MCP is not GodotSim truth.
Godot MCP is not Aider.
Godot MCP does not decide acceptance.

Godot MCP may only be tested as an editor bridge or runtime inspection bridge.

## Allowed Probe Goals

The MCP probe may test whether structured tool calls can:

- inspect the current Godot scene tree
- add a simple 3D node
- set a typed Vector3 position
- attach a simple script
- run a scene
- capture a screenshot or frame
- read node position/state
- assert node state
- produce a machine-readable report

## Forbidden During Probe

The probe may not:

- replace existing gates
- delete existing builder/gate code
- mutate EngAInOS authority files
- mutate canon/AP/Trixel/Retrographer authority
- install network-facing services without explicit human approval
- open remote/LAN access
- treat MCP output as final acceptance

## Required Proof Before Adoption

MCP adoption may only proceed if all are TRUE:

- MCP_SERVER_STARTS_LOCALHOST_ONLY
- GODOT_PLUGIN_ENABLES_WITHOUT_PROJECT_BREAKAGE
- MCP_CLIENT_CONNECTS
- MCP_CAN_READ_SCENE_TREE
- MCP_CAN_SET_TYPED_VECTOR3_PROPERTY
- MCP_CAN_RUN_SCENE
- MCP_CAN_CAPTURE_SCREENSHOT_OR_STATE
- MCP_CAN_ASSERT_PLAYER_POSITION
- EXISTING_GODOTSIM_GATES_STILL_PASS

## Current Status

GODOT_MCP_ADOPTED: FALSE
GODOT_MCP_PROBE_ALLOWED: TRUE
GODOT_MCP_REPLACES_BUILDER: FALSE
GODOT_MCP_REPLACES_GATES: FALSE

FINAL_STAMP: GODOT_MCP_PROBE_ALLOWED_NOT_ADOPTED
