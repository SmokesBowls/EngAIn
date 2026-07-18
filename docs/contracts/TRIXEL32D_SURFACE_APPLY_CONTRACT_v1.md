# TRIXEL 3.2D SURFACE APPLICATION CONTRACT v1

Contract ID: `trixel32d_surface_apply.v1`

Status: contract-only; not implemented or wired

Repository authority: EngAIn

## 1. Purpose

This contract authorizes where and how one already validated
`trixel32d_surface_built.v1` artifact may enter an EngAIn scene application
lane.

It exists after Trixel has built canonical local-space geometry and after
EngAInOS has validated that response. It does not transport geometry and does
not attach anything to Godot or to the runtime.

The authority chain is:

```text
Trixel canonical local geometry
→ identity-complete EngAInOS response validation
→ EngAInOS application and collision authorization
→ future GodotSim physical execution/admission when requested
→ future runtime application executor
→ passive Godot presentation
```

The existence of this packet proves authorization only. It is not proof that
application occurred.

## 2. Normative upstream authority

This contract is subordinate to:

- `ENGAINOS_AUTHORITY_MAP.md`
- `docs/contracts/ENGAINOS_TIER1_AUTHORITY/ENGAINOS_AUTHORITY_MAP.md`
- `docs/contracts/GODOTSIM_TIER2_AUTHORITY/GODOTSIM_TIER2_SPATIAL_SIM_CONTRACT_v1.md`
- `docs/contracts/TRIXEL32D_SURFACE_REQUEST_CONTRACT_v1.md`
- `docs/contracts/TRIXEL32D_REQUEST_ASSEMBLY_AND_CONSUMER_v1.md`
- `HANDSHAKES.md`, section 7

If these authorities conflict, the stricter fail-closed rule governs until the
conflict is resolved explicitly.

## 3. Authority ownership

### 3.1 EngAInOS

EngAInOS is the only issuer of an accepted
`trixel32d_surface_apply.v1` packet.

EngAInOS owns:

- acceptance of the validated built surface into declared scene truth;
- the target scene, declared parent, and application slot;
- the local-to-scene transform;
- visibility intent;
- replacement and lifetime policy;
- presentation/static/dynamic classification;
- the governance decision and reality-mode checks;
- explicit collision authorization or denial under the same governance decision.

A caller may request these values, but caller-supplied values are intent, not
authorization. An implementation must derive the packet from an accepted
EngAInOS authority decision; it must not trust a client to self-issue one.

### 3.2 GodotSim

GodotSim owns simulation execution and physical-lane feasibility. Under the
current upstream contract, every GodotSim-to-EngAInOS statement must remain a
`godotsim.spatial_sim_packet.v1` packet.

GodotSim:

- may accept or refuse future physical execution of an EngAInOS-authorized
  static or dynamic surface;
- may report physical evidence only through the existing SpatialSimPacket
  contract until a separately approved contract extends that boundary;
- does not issue this application packet;
- does not grant AP, canon acceptance, or declared scene truth;
- cannot override an EngAInOS rejection;
- cannot change Trixel geometry, placement, visibility, lifetime, collision
  layer, or collision mask.

In v1, `collision.decision = GRANTED` is an explicit EngAInOS authorization,
not a GodotSim message or grant. Future execution may still fail closed if
GodotSim cannot admit that exact declaration.

### 3.3 Trixel

Trixel owns the canonical local geometry and its topology, ordering, normals,
UVs, colors, ownership, and provenance.

Trixel does not authorize scene placement, visibility, replacement, lifetime,
collision, runtime persistence, or canon mutation.

### 3.4 Godot

Godot is a passive presentation client. A future executor may ask Godot to
materialize an accepted application packet, but Godot may not choose or alter
its authority-bearing fields.

Godot may not:

- infer a target scene or parent;
- invent or repair a transform;
- select a replacement target;
- promote lifetime or persistence;
- enable collision without the exact grant required below;
- reinterpret local geometry to make it fit;
- treat successful rendering as authority acceptance.

## 4. Non-goals

Version 1 does not define or permit:

- request or response transport;
- a live dispatcher, endpoint, file watcher, or queue;
- scene-tree attachment;
- mesh, material, body, or collision-node creation;
- runtime or canonical-state mutation;
- transform inference from a camera, renderer, or current node state;
- geometry embedding inside the application packet;
- topology regeneration, simplification, repair, or collision approximation;
- in-place update semantics;
- wildcard replacement;
- a successful-application receipt.

A later execution receipt must use a different contract. An authorization packet
must never be rewritten to masquerade as execution evidence.

## 5. Normative packet shape

```json
{
  "contract": "trixel32d_surface_apply.v1",
  "packet_type": "trixel32d_surface_apply",
  "apply_id": "t32dapply_0123456789abcdef",
  "surface_binding": {
    "built_contract": "trixel32d_surface_built.v1",
    "request_id": "t32dreq_8b14a3bac98d1025",
    "surface_id": "t32dsurface_0123456789abcdef",
    "built_response_sha256": "64-lowercase-hex-characters"
  },
  "authorization": {
    "decision": "AUTHORIZED",
    "decision_id": "engainos-decision-id",
    "issued_by": "engainos",
    "actor_id": "authenticated-actor-id",
    "actor_authority_tier": 3,
    "reality_mode": "DRAFT",
    "authority_revision": "declared-authority-revision",
    "runtime_session_id": "trusted-runtime-session-id",
    "ap_rule_ids": ["accepted-rule-id"]
  },
  "target": {
    "scene_id": "declared-scene-id",
    "scene_revision": "declared-scene-revision",
    "parent_kind": "RUNTIME_CONTAINER",
    "parent_id": "declared-parent-id",
    "application_slot_id": "declared-surface-slot-id"
  },
  "local_to_scene": {
    "space": "SCENE_LOCAL_Y_UP",
    "basis_columns": [
      [1.0, 0.0, 0.0],
      [0.0, 1.0, 0.0],
      [0.0, 0.0, 1.0]
    ],
    "origin": [0.0, 0.0, 0.0]
  },
  "visibility": {
    "intent": "VISIBLE"
  },
  "replacement": {
    "mode": "CREATE_ONLY",
    "replaces_apply_id": null
  },
  "lifetime": {
    "mode": "SCENE_BOUND"
  },
  "classification": "PRESENTATION_ONLY",
  "collision": {
    "decision": "DENIED",
    "authorized_by_decision_id": "engainos-decision-id",
    "shape_policy": "NONE",
    "layer": 0,
    "mask": 0
  }
}
```

No field shown above is optional in v1. Explicit denial is data; omission is not
denial.

The schema is closed-world at every object level. The root object and each
nested object must contain exactly the keys defined in section 5 for its chosen
enum branch. Undeclared keys reject, including alternate transforms, renderer
paths, inferred collision shapes, persistence hints, compatibility flags, and
client-local authority fields.

## 6. Identity and surface binding

### 6.1 Application identity

`apply_id` must be a stable application-authorization identity with the form
`t32dapply_` followed by 16 lowercase hexadecimal characters.

An `apply_id` identifies one immutable authorization decision. Reissuing an
existing `apply_id` with different bytes is forbidden.

### 6.2 Built-surface binding

`surface_binding` must bind the application authorization to exactly one
validated built response:

- `built_contract` must equal `trixel32d_surface_built.v1`;
- `request_id` must match the built response request identity;
- `surface_id` must match the built response surface identity;
- `built_response_sha256` must be the SHA-256 of the exact validated built
  response bytes.

The application packet references geometry; it does not contain geometry.
A mismatch in any binding field rejects the packet before placement or physical
execution is considered.

The persisted proof response carries `contract`, `request_id`, and `surface_id`.
The EngAIn built-response gate now requires all three, matches `request_id`
against a separately supplied trusted request, recomputes deterministic
`surface_id`, rejects unknown or duplicate identity fields, and exposes the
SHA-256 of the exact byte buffer it parsed. The canonical 3×2 response is pinned
at SHA-256
`bc1951f55de00aa0114679fab1a46d80439d1b840309b0df4c9b835539dd2929`.

Application validation remains a separate, still-unimplemented gate. It must
consume the accepted packet and exact-byte SHA-256 returned by the byte-level
built-response validator; calling the dict-only semantic helper is insufficient
application evidence.

## 7. Authorization rules

`authorization.decision` must be `AUTHORIZED`. Rejections belong in authority
decision/Intent Shadow evidence, not in an application packet.

`authorization.issued_by` must be `engainos`.

`decision_id`, `actor_id`, `authority_revision`, and `runtime_session_id` must be
non-empty and must resolve to accepted EngAInOS authority evidence.
`runtime_session_id` must come from trusted runtime context and binds this
issuance to one runtime session; it must not be supplied or overridden by a
renderer/client. `ap_rule_ids` must be an array; it may be empty only when the
governing authority decision proves no AP rule was required.

`actor_authority_tier` uses the governance actor tiers in
`ENGAINOS_AUTHORITY_MAP.md`, not repository subsystem tier numbering:

- Tier 0: system/replay/validation actor;
- Tier 1: constrained AI actor;
- Tier 2: limited human operator;
- Tier 3: human authority root.

Reality-mode rules:

- `REPLAY` rejects every application packet;
- `FINALIZED` requires Tier 3;
- Tier 1 AI authority may not authorize mutation of `FINALIZED` state;
- a tier is necessary but not sufficient: AP and current runtime law must also
  accept the application;
- missing, unknown, or contradictory authority evidence rejects fail-closed.

A future implementation must obtain actor tier and reality mode from the trusted
EngAInOS authority envelope. Values copied from an untrusted request do not
satisfy this contract.

## 8. Target and placement rules

`target` identifies where the surface is allowed to exist in declared runtime
space.

Required fields:

- `scene_id`: exact accepted EngAInOS scene identity;
- `scene_revision`: exact scene revision against which authorization was made;
- `parent_kind`: one of `SCENE_ROOT`, `RUNTIME_CONTAINER`, or `ENTITY_MOUNT`;
- `parent_id`: exact declared parent identity valid for `parent_kind`;
- `application_slot_id`: exact stable slot in which this surface may appear.

A renderer-specific node path is not a declared parent identity and must not be
used as `parent_id`. A future adapter may resolve a declared parent identity to
a client-local node path, but that resolution cannot broaden the authorized
parent.

The scene revision is a compare-and-swap boundary. If the active scene revision
differs, application rejects as stale rather than retargeting automatically.

The surface may appear only in the exact scene, parent, and slot declared. No
fallback to scene root, current scene, nearest parent, or newly created
container is permitted.

## 9. Transform rules

`local_to_scene` is the complete placement transform from Trixel local Y-up
coordinates into the declared scene.

Rules:

- `space` must equal `SCENE_LOCAL_Y_UP`;
- `basis_columns` must contain exactly three columns of three finite numbers;
- `origin` must contain exactly three finite numbers;
- for Trixel-local point `p = [x, y, z]`, consumers must calculate exactly:

```text
scene_point = origin
            + basis_columns[0] × x
            + basis_columns[1] × y
            + basis_columns[2] × z
```

- the three arrays are mathematical basis columns and map directly to Godot
  `Basis(x_axis, y_axis, z_axis)` columns; transposition is forbidden;
- Trixel-local coordinate values are the input units and the basis coefficients
  express their complete conversion into EngAIn scene-local units; no second
  scale, unit factor, parent compensation, or post-transform is permitted;
- the basis determinant must be finite and strictly positive;
- zero scale, singular transforms, reflection, and handedness reversal reject;
- no default identity transform is permitted when the block is absent;
- no consumer may modify the transform to compensate for camera, parent, or
  renderer state.

The positive-determinant requirement preserves the handedness and winding of
the validated Trixel geometry. Mirrored placement requires a future contract
version with an explicit winding/normal policy.

## 10. Visibility rules

`visibility.intent` must be exactly `VISIBLE` or `HIDDEN`.

There is no `INHERIT`, `AUTO`, or omitted default in v1. Visibility does not
change collision authority: a hidden surface with granted collision remains
physical, and a visible surface with denied collision remains nonphysical.

A presentation client may be unable to display an authorized visible surface,
but it may not rewrite the authorization to hidden. It must report the failure
through a future execution receipt.

## 11. Replacement rules

`replacement.mode` must be one of:

- `CREATE_ONLY`: the application slot must be empty;
- `REPLACE_EXACT`: the slot must contain exactly the application identified by
  `replaces_apply_id`.

For `CREATE_ONLY`, `replaces_apply_id` must be null.

For `REPLACE_EXACT`, `replaces_apply_id` must be a valid prior `apply_id` and
must match the currently accepted occupant of the same scene, parent, and slot.
A missing or mismatched occupant rejects. Wildcard replacement, replace-current,
upsert, merge, and nearest-match behavior are forbidden.

Replacement is atomic: the prior occupant remains accepted if the new
application fails. No partial removal or partial attachment is permitted.

Version 1 defines no in-place update. A changed transform, visibility, lifetime,
classification, collision decision, or surface binding requires a new
`apply_id`, normally using `REPLACE_EXACT`.

## 12. Lifetime rules

`lifetime.mode` must be one of:

- `SCENE_BOUND`: valid only in `authorization.runtime_session_id` and remove
  when the exact scene revision is no longer active;
- `RUNTIME_SESSION`: may survive scene deactivation only inside the exact
  `authorization.runtime_session_id`;
- `CANONICAL_PERSISTENT`: may be recorded as declared persistent world state.

`SCENE_BOUND` and `RUNTIME_SESSION` reject if the active trusted session identity
does not exactly match the authorization. The packet may not be replayed into a
new session by copying or substituting a session identity.

`CANONICAL_PERSISTENT` is a canonical mutation. It requires Tier 3 when the
target reality mode is `FINALIZED`, must pass AP/runtime law, and may never be
inferred from an existing asset, fixture, save file, or successful render.

A fixture proof must use `SCENE_BOUND` or remain unapplied. It must never promote
itself to persistent state.

## 13. Classification rules

`classification` must be one of:

- `PRESENTATION_ONLY`: visible presentation is permitted; physical participation
  is forbidden;
- `STATIC_SPATIAL`: fixed physical participation may be granted;
- `DYNAMIC_SPATIAL`: runtime-driven physical participation may be granted.

Classification is an upper bound, not an automatic collision grant.

`PRESENTATION_ONLY` requires collision `DENIED`.

`STATIC_SPATIAL` or `DYNAMIC_SPATIAL` may still declare collision `DENIED`.
Collision `GRANTED` requires one of these spatial classifications plus all
requirements in section 14.

## 14. Collision and physical-presence rules

`collision.decision` must be exactly `DENIED` or `GRANTED`. Missing collision
data rejects; there is no compatibility default.

### 14.1 Explicit denial

When `decision` is `DENIED`:

- `authorized_by_decision_id` must exactly equal
  `authorization.decision_id`;
- `shape_policy` must be `NONE`;
- `layer` must be `0`;
- `mask` must be `0`.

No body, shape, navigation obstacle, or physical proxy may be created.

### 14.2 Explicit grant

When `decision` is `GRANTED`:

- classification must be `STATIC_SPATIAL` or `DYNAMIC_SPATIAL`;
- `authorized_by_decision_id` must exactly equal
  `authorization.decision_id`, whose trusted EngAInOS evidence must explicitly
  authorize collision for the same scene revision, surface binding, transform,
  classification, shape policy, layer, and mask;
- `shape_policy` must be `CANONICAL_MESH_EXACT` in v1;
- `layer` must be an integer from 1 through `4294967295`;
- `mask` must be an integer from 0 through `4294967295`.

`CANONICAL_MESH_EXACT` permits collision derived from the exact accepted
canonical triangles only. Convex hulls, simplification, decimation, primitive
substitution, gap closing, and inferred collision volumes are forbidden in v1.

This authorization does not claim that physical execution succeeded. A future
GodotSim/runtime executor must either admit the exact declaration or reject it
without attachment and report through the already governed simulation evidence
lane. It may not weaken or rewrite collision parameters to make them executable.

## 15. Determinism and immutability

Given identical validated built-response bytes, authority evidence, target,
transform, visibility, replacement, lifetime, classification, and collision
inputs, serialization of the authorization packet must be deterministic.

After issuance:

- the packet is immutable;
- authority-bearing fields cannot be filled from runtime defaults;
- an executor cannot silently normalize, repair, or broaden the packet;
- a changed decision requires a new `apply_id`;
- logs, screenshots, consume reports, or successful rendering cannot promote or
  modify the authorization.

## 16. Fail-closed rejection conditions

Reject before any attachment, allocation of physical objects, or runtime
mutation if any of the following is true:

- any required field is absent, null where prohibited, malformed, non-finite, or
  unknown;
- contract or packet type is wrong;
- application, request, surface, decision, session, scene, parent, or slot identity
  is malformed or unresolved;
- built-response checksum or identity binding does not match;
- authority evidence is missing, untrusted, rejected, stale, or incompatible
  with reality mode;
- scene revision is stale;
- parent or application slot is absent or outside declared scene truth;
- transform is singular, reflected, non-finite, or interpreted in another space;
- visibility is implicit;
- replacement target is ambiguous or does not match exactly;
- lifetime exceeds granted authority;
- classification and collision contradict each other;
- collision is granted without exact trusted EngAInOS authorization for all
  collision-bearing fields;
- any consumer would need to invent a default to proceed.

A rejected packet causes no mutation. Rejection evidence belongs in Intent
Shadow and/or a future rejection report, not in a partially applied scene.

## 17. Promotion and execution separation

The following are distinct and must never be collapsed:

```text
built geometry != validated geometry
validated geometry != application authorization
application authorization != physical-lane admission
physical-lane admission != execution
execution != canon acceptance
successful rendering != runtime truth
```

A future runtime executor must validate this whole packet again at the point of
use and emit a separate deterministic receipt. That work is outside v1's
current contract-only ticket.

## 18. Red-line invariant

```text
EngAInOS decides whether and where the surface may enter declared runtime space.
GodotSim may admit explicitly bounded physical participation but cannot grant AP.
Trixel geometry remains immutable.
Godot displays or embodies only the accepted declaration.
Missing authority means no application.
```
