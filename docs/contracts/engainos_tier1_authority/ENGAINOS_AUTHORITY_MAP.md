# EngAInOS Authority Map

This repo uses a five-lane governance structure.

The core rule:

> EngAInOS is not the mechanic itself. EngAInOS is the authority gate over mechanics.

## Five-Lane Map

EngAInOS     -> governance / declared truth / contract gates
GodotSim     -> simulation execution
Engionality  -> synchronization execution
Trixel       -> asset truth
Godot        -> presentation

## EngAInOS Lane

EngAInOS owns governance.

EngAInOS is authoritative over:

- declared scene truth
- declared entity truth
- bridge entity contracts
- AP / contract gates
- validation
- orchestration
- runtime acceptance
- project state
- which subsystem outputs are accepted into declared truth

EngAInOS does not need to execute every mechanic directly.

EngAInOS does not own asset production.

EngAInOS does not own Godot presentation.

## GodotSim Lane

GodotSim owns simulation execution.

GodotSim may execute systems such as:

- spatial simulation
- behavior
- perception
- combat
- inventory
- dialogue
- runtime state stepping
- snapshot publication

GodotSim has execution authority inside the simulation lane.

GodotSim may not write to declared truth unless EngAInOS accepts the output.

## Engionality Lane

Engionality owns synchronization execution.

Engionality may execute systems such as:

- timer sequence
- heartbeat
- music timing
- vocal timing
- animation timing
- transition timing
- audiovisual event synchronization

Engionality is the lane that keeps events aligned, such as sword swooshes, music changes, vocals, and animation beats.

Engionality has execution authority inside the synchronization lane.

Engionality may not write to declared truth unless EngAInOS accepts the output.

## Trixel Lane

Trixel owns asset truth.

Trixel is a peer authority lane, not a Godot dependency.

Trixel is authoritative over:

- asset IDs
- atlas IDs
- tile variants
- meshes
- skins
- sprites
- visual recipes
- asset manifests
- asset provenance
- asset supersession

Trixel may produce 2D, 3D, 4D, or any-D assets.

EngAInOS should not care how an asset was produced. EngAInOS should only care about valid asset references.

A non-Godot renderer may consume the same Trixel asset references without breaking the architecture.

## Godot Lane

Godot owns presentation.

Godot may:

- display declared state
- consume EngAInOS scene/runtime contracts
- consume GodotSim runtime output
- consume Engionality sync output
- consume Trixel asset references

Godot may not decide authority.

Godot may not declare canon entities.

Godot may not promote inferred data into declared truth.

## Corollary

GodotSim and Engionality have execution authority inside their lanes.

Neither may write to declared truth without EngAInOS acceptance.

Trixel has asset authority inside its lane.

Trixel may not declare scene, entity, quest, combat, inventory, dialogue, AP, or runtime truth.

Godot has presentation authority only.

Godot may display what it is handed, but it may not decide what is real.

## Boundary Summary

EngAInOS owns declared truth.
GodotSim owns simulation execution.
Engionality owns synchronization execution.
Trixel owns asset truth.
Godot owns presentation.
