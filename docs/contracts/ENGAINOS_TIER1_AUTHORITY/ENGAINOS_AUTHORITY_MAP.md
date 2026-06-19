# EngAInOS Authority Map

This repo uses a five-lane governance structure.

The core rule:

> EngAInOS is not the mechanic itself. EngAInOS is the authority gate over mechanics.

> This map does not define Trixel authority. Trixel is a separate art/asset authority system and is documented in its own contract. /docs/contracts/TRIXEL_AUTHORITY_MAP.md

## Five-Lane Map

EngAInOS     -> governance / declared truth / contract gates
GodotSim     -> simulation execution
Engionality  -> synchronization execution
MrLore       -> canon / lore truth
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

## MrLore Lane

MrLore owns canon and lore truth.

MrLore is a peer authority lane, not a Godot dependency.

MrLore is authoritative over:

- canon facts
- lore continuity
- character identity
- faction identity
- world history
- timeline truth
- mythic structure
- named events
- accepted narrative constraints
- canon contradictions and resolutions

MrLore may produce canon references, lore packets, continuity decisions, narrative constraints, and accepted lore state.

EngAInOS should not invent canon.

EngAInOS should only care whether MrLore canon references are valid when they enter declared scene truth, entity truth, bridge contracts, runtime state, or presentation.

A non-Godot renderer may consume the same accepted MrLore canon references without breaking the architecture.

## Godot Lane

Godot owns presentation.

Godot may:

- display declared state
- consume EngAInOS scene/runtime contracts
- consume GodotSim runtime output
- consume Engionality sync output
- consume accepted MrLore canon/lore references

Godot may not decide authority.

Godot may not declare canon entities.

Godot may not promote inferred data into declared truth.

## Corollary

GodotSim and Engionality have execution authority inside their lanes.

Neither may write to declared truth without EngAInOS acceptance.

MrLore has canon and lore authority inside its lane.

MrLore may define canon/lore truth, including canon characters, factions, events, dialogue facts, and world history.

MrLore may not directly promote canon/lore output into EngAInOS declared scene truth, entity truth, quest truth, combat truth, inventory truth, dialogue runtime truth, AP truth, or runtime truth.

Godot has presentation authority only.

Godot may display what it is handed, but it may not decide what is real.

## Boundary Summary

EngAInOS owns declared truth.
GodotSim owns simulation execution.
Engionality owns synchronization execution.
MrLore owns canon and lore truth.
Godot owns presentation.
Trixel = separate art/asset authority, not defined here
