# Code Refactor TRUE/FALSE Contract

This contract belongs to:

```text
docs/contracts/engainos_1stlane_governance_authority/CODE_REFACTOR_TRUE_FALSE_CONTRACT.md
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn

mkdir -p docs/contracts/engainos_1stlane_governance_authority

cat > docs/contracts/engainos_1stlane_governance_authority/CODE_REFACTOR_TRUE_FALSE_CONTRACT.md <<'EOF'
# Code Refactor TRUE/FALSE Contract

This contract belongs to:

```text
docs/contracts/engainos_1stlane_governance_authority/CODE_REFACTOR_TRUE_FALSE_CONTRACT.md
Purpose

This contract defines how code refactors are allowed to happen inside the EngAIn declared/runtime system.

A refactor is not a rewrite.

A refactor is only valid when it preserves authority, lane ownership, runtime meaning, schema meaning, and accepted contract behavior.

TIER / Lane Rule

TIER means system-wide authority rank.

Lane means ordered work boundary.

Stack means implementation family.

TIER names must always be written in caps:

TIER1
TIER2
TIER3

Inside EngAIn declared/runtime truth, EngAInOS is TIER1.

If an agent does not know what lane it is in, work must stop.

Unknown lane state is:

BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT

The agent must ask EngAInOS TIER1 before continuing.

Do not guess lane placement.

Do not self-assign authority.

Do not continue a refactor from an unknown lane.

Prime Refactor Rule

No refactor may change authority.

No refactor may create new truth.

No refactor may invent fallback behavior.

No refactor may silently change runtime output.

No refactor may move work into the wrong lane.

No refactor may hide a failing gate behind success logs.

Allowed Refactor Work

A valid refactor may:

move code into smaller files
split large scripts into smaller lane-owned modules
rename files when the lane and behavior remain proven
isolate adapters from authority code
isolate presentation code from declared truth code
remove duplicated logic after proving behavior is preserved
add TRUE/FALSE/BYPASS gates
add logs that prove contract behavior
add documentation that clarifies authority and lane ownership
Forbidden Refactor Work

A refactor may not:

change declared scene truth
change declared entity truth
change bridge entity meaning
change accepted snapshot schema
change authority ownership
add fallback entity creation
add inferred entity creation
let render become truth
let execution lanes write declared truth directly
allow stale scene replacement
bypass EngAInOS acceptance
touch another lane without declaring it
Required Gate States

Every refactor gate must return exactly one of:

TRUE
FALSE
BYPASS

TRUE means the refactor preserved the contract and the proof passed.

FALSE means the refactor violated the contract or the proof failed.

BYPASS means the gate was intentionally skipped because the checked lane, dependency, runtime, or feature path was not active in this test.

A FALSE gate blocks acceptance.

An unknown lane blocks acceptance.

Refactor Acceptance Outcomes

Every refactor must end in exactly one of:

ACCEPTED
REJECTED
BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT

ACCEPTED means all required gates returned TRUE or explicitly allowed BYPASS.

REJECTED means one or more required gates returned FALSE.

BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT means the refactor touched unclear lane ownership and must stop until EngAInOS TIER1 assigns the lane.

Code Movement Gates

Any refactor that moves, splits, renames, or extracts code must prove:

[TRUE/FALSE/BYPASS] Source file exists before refactor
[TRUE/FALSE/BYPASS] Destination file exists after refactor
[TRUE/FALSE/BYPASS] Imports / preload paths still resolve
[TRUE/FALSE/BYPASS] Public function names preserved or explicitly mapped
[TRUE/FALSE/BYPASS] Runtime entrypoint still resolves
[TRUE/FALSE/BYPASS] No authority ownership changed
[TRUE/FALSE/BYPASS] No lane ownership changed without contract update
[TRUE/FALSE/BYPASS] No new fallback behavior added
[TRUE/FALSE/BYPASS] No inferred truth added
[TRUE/FALSE/BYPASS] Existing test command still runs
[TRUE/FALSE/BYPASS] Existing output contract still matches
Semantic / Snapshot / Godot Refactor Gates

If the refactor touches Semantic, Godot, snapshots, bridge entities, hydration, Boot, SimClient, SceneClient, renderer, or actor spawning, these gates are required:

[TRUE/FALSE/BYPASS] Requested scene_id is preserved
[TRUE/FALSE/BYPASS] Snapshot payload still parses
[TRUE/FALSE/BYPASS] Snapshot payload.scene_id remains valid
[TRUE/FALSE/BYPASS] Snapshot bridge_entities_scene_id remains valid
[TRUE/FALSE/BYPASS] bridge_entities still exist
[TRUE/FALSE/BYPASS] bridge_entities count is unchanged unless intentionally accepted
[TRUE/FALSE/BYPASS] Only bridge_entities become render actors
[TRUE/FALSE/BYPASS] Renderer actor count equals accepted bridge_entities count
[TRUE/FALSE/BYPASS] Renderer did not invent entities
[TRUE/FALSE/BYPASS] Boot did not override accepted scene
[TRUE/FALSE/BYPASS] SimClient did not request stale scene
[TRUE/FALSE/BYPASS] Disk snapshot hydration still works
[TRUE/FALSE/BYPASS] Runtime snapshot hydration still works
Lane Ownership Rules

If a refactor touches declared scene truth, declared entity truth, bridge entity contracts, AP gates, validation, orchestration, project state, or runtime acceptance, it belongs to EngAInOS TIER1.

If a refactor touches simulation execution, it belongs to GodotSim.

If a refactor touches synchronization execution, it belongs to Engionality.

If a refactor touches canon or lore truth, it belongs to MrLore.

If a refactor touches presentation only, it belongs to Godot or render layer management.

If a refactor touches Trixel art/asset production, it does not belong to EngAInOS. It must use the Trixel TIER1 authority contract.

Required Refactor Report Format

Every refactor report must include:

REFACTOR_ID:
TIER_AUTHORITY:
LANE:
STACK:
FILES_CHANGED:
BEHAVIOR_CHANGE: yes/no
AUTHORITY_CHANGE: yes/no
SCHEMA_CHANGE: yes/no
RUNTIME_OUTPUT_CHANGE: yes/no
GATES:
- [TRUE/FALSE/BYPASS] gate_id — proof
ACCEPTANCE:
- ACCEPTED
- REJECTED
- BLOCKED_PENDING_TIER1_LANE_ASSIGNMENT
Final Law

A refactor is only clean when it proves:

same authority
same lane ownership
same accepted truth
same runtime meaning
same schema meaning
cleaner code placement
TRUE/FALSE/BYPASS gates recorded

