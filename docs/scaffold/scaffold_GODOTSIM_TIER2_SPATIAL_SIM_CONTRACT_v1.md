GodotSim sounds like **footsteps on a grid before the world is allowed to believe them**.

Not lore. Not art. Not final authority. It sounds like:

“Something wants to move. Is there space?”
“Something wants to touch. Are they close enough?”
“Something wants to collide. What actually happened?”
“Something wants to render. Here is where it truly is.”

So the contract voice is not poetic at the code level. It should be cold and physical:

```text
GodotSim does not decide canon.
GodotSim does not decide AP permission.
GodotSim does not decide visual art.
GodotSim does not decide story meaning.

GodotSim owns simulated spatial truth:
position, rotation, velocity, collision, reachability, proximity, scene occupancy, and sim tick.
```

That matches the current EngAInOS profile: EngAInOS owns runtime law/AP/Godot-facing authority, while `godotsim` owns “spatial/sim packets and scene simulation behavior,” and EngAInOS must ask GodotSim when spatial state, collision, position, velocity, physics, proximity, or reachability are unclear.  

The contract should be named something like:

```text
GODOTSIM_TIER2_SPATIAL_SIM_CONTRACT_v1.md
```

And the plain law should be:

```text
EngAInOS is TIER1 runtime authority.

GodotSim is TIER2 spatial simulation authority.

GodotSim may report physical/simulated truth.
GodotSim may not authorize mutation by itself.
GodotSim may not invent entities.
GodotSim may not decide canon.
GodotSim may not choose art assets.
GodotSim may not bypass AP.
GodotSim may not convert narrative directly into active runtime entities.

All GodotSim output entering EngAInOS must arrive as a SpatialSimPacket.
All SpatialSimPackets must be validated by EngAInOS before they affect runtime state.
```

The inbound packet should be simple:

```json
{
  "contract": "godotsim.spatial_sim_packet.v1",
  "source": "godotsim",
  "authority_tier": 2,
  "scene_id": "scene.030_ummade_army",
  "sim_tick": 1042,
  "entities": [
    {
      "entity_id": "geralt",
      "position": [0.0, 0.0, 0.0],
      "rotation": [0.0, 0.0, 0.0],
      "velocity": [0.0, 0.0, 0.0],
      "collision_role": "solid",
      "grounded": true
    }
  ],
  "contacts": [],
  "proximity": [],
  "physics_flags": {}
}
```

Minimum required fields:

```text
contract
source
authority_tier
scene_id
sim_tick or time
entities
entity_id
position
collision_role
```

Optional but useful:

```text
rotation
velocity
grounded
contacts
proximity
physics_flags
bounds
navigation_state
reachable_targets
blocked_paths
```

Hard reject conditions:

```text
Reject if source is not godotsim.
Reject if authority_tier is not 2.
Reject if scene_id is missing.
Reject if entity_id is missing.
Reject if position is missing outside DRAFT/TEST.
Reject if collision_role is not known.
Reject if packet tries to include AP allowed=true.
Reject if packet tries to include canon truth.
Reject if packet tries to include render asset authority.
Reject if packet includes new undeclared entities without EngAInOS approval.
```

The real boundary is this:

```text
GodotSim may say:
“entity A is at position X.”
“entity A touched entity B.”
“entity A cannot reach entity B.”
“entity A collided with wall C.”
“entity A is inside region R.”
“entity A is moving at velocity V.”

GodotSim may not say:
“therefore the quest completes.”
“therefore the door opens.”
“therefore canon changes.”
“therefore this entity is allowed.”
“therefore spawn this undeclared thing.”
```

EngAInOS listens to GodotSim like a judge listening to a field witness. GodotSim gives evidence. EngAInOS decides whether that evidence is allowed to mutate the runtime.

This is the clean handoff:

```text
Mettaext declares entities.
EngAInOS validates authority.
GodotSim simulates physical state.
EngAInOS accepts or rejects mutation.
Godot renderer displays accepted state.
Trixel supplies visual assets, not authority.
```

The one sentence version:

```text
GodotSim is the TIER2 witness of physical truth; EngAInOS is the TIER1 judge of whether that truth may change the world.
```

So when I listen to GodotSim, I do not hear “make a game.” I hear:

```text
tick
position
collision
reachability
blocked
accepted by physics
reported to authority
waiting for EngAInOS
```

That is the contract.
