# EngAInOS Action Classification Contract v1

Status: doctrine / contract

Target system: EngAInOS AP stage, before runtime mutation rule evaluation.

Purpose: define that EngAInOS, not the caller, owns runtime action classification before AP evaluation.

## 1. Core doctrine

EngAInOS owns final runtime action classification.

A caller may submit intent, payload, actor identity, authority tier, reality mode, source, and trace metadata. A caller must not be trusted to assign the final authority requirements or mutation footprint of its own request.

The authority pipeline must treat caller-supplied classification fields as hints unless EngAInOS explicitly marks the caller or route as trusted.

## 2. Caller may supply

A caller may supply:

- `action`
- `payload`
- `actor_id`
- `actor_authority_tier`
- `reality_mode`
- `source`
- `trace_id`

These fields describe the request and its source context. They do not grant final classification authority.

## 3. Caller must not be trusted to supply final classification

A caller must not be trusted to supply final:

- `required_tier`
- `read_set`
- `write_set`
- `mutation_class`

Caller-supplied values for these fields are hints only unless explicitly marked trusted by EngAInOS.

## 4. EngAInOS derives classification

Before AP rule evaluation, EngAInOS derives the effective:

- `required_tier`
- `read_set`
- `write_set`
- `mutation_class`

This derived classification is the only classification AP may treat as authoritative.

## 5. FINALIZED rule

If `reality_mode == "FINALIZED"`, the effective required tier is at least `3`.

This rule applies even if the route/action table says a lower tier. FINALIZED state is highly restricted and cannot be lowered by caller-supplied metadata.

## 6. REPLAY rule

If `reality_mode == "REPLAY"`, read-only actions may pass to AP/log/snapshot handling, but runtime mutation and unknown actions must be blocked.

REPLAY does not mean all inspection must stop. It means mutation is forbidden and ambiguity fails closed.

## 7. Unknown action rule

Unknown action names are mutation-unknown and fail closed unless classified by EngAInOS.

A caller cannot make an unknown action safe by supplying friendly text, a low `required_tier`, or an empty `write_set`.

## 8. `@scope: canon` is not `reality_mode: FINALIZED`

`@scope: canon` and `reality_mode: FINALIZED` are not the same thing.

- `@scope: canon` means an AP rule or ZON artifact is promoted/active.
- `reality_mode: FINALIZED` means the target world/runtime state is highly restricted.

An active canon AP rule can govern DRAFT, IMBUED, FINALIZED, or REPLAY targets depending on its predicates. A FINALIZED target still requires FINALIZED authority constraints.

## 9. First action classification table

```python
ACTION_CLASSIFICATION = {
    "look": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.snapshot"],
        "write_set": [],
    },
    "status": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.status"],
        "write_set": [],
    },
    "snapshot": {
        "required_tier": 0,
        "mutation_class": "read_only",
        "read_set": ["runtime.snapshot"],
        "write_set": [],
    },
    "command": {
        "required_tier": 3,
        "mutation_class": "unknown",
        "read_set": [],
        "write_set": ["unknown"],
    },
    "load_scene": {
        "required_tier": 2,
        "mutation_class": "runtime_mutation",
        "read_set": ["scene.registry"],
        "write_set": ["runtime.scene"],
    },
    "spawn_entity": {
        "required_tier": 2,
        "mutation_class": "runtime_mutation",
        "read_set": ["runtime.scene"],
        "write_set": ["runtime.entities"],
    },
    "update_entity": {
        "required_tier": 2,
        "mutation_class": "runtime_mutation",
        "read_set": ["runtime.entities"],
        "write_set": ["runtime.entities"],
    },
}
```

## 10. Legacy command behavior

`action: "command"` is a legacy ambiguous wrapper.

In strict AP mode, `command` is classified as:

```text
required_tier: 3
mutation_class: unknown
read_set: []
write_set: ["unknown"]
```

This is a deliberate breaking change.

Reason:

A plain command payload such as:

```json
{"action": "command", "payload": {"text": "attack guard"}}
```

does not declare whether it is read-only, mutating, canon-affecting, combat-affecting, or scene-changing.

Therefore EngAInOS must fail closed until the command is migrated to a named action or sub-classified by an EngAInOS-owned action classifier.

Allowed migration path:

```text
command/look      -> look
command/status    -> status
command/snapshot  -> snapshot
command/load      -> load_scene
command/spawn     -> spawn_entity
command/update    -> update_entity
command/attack    -> combat.damage or combat.intent, once classified
```

Caller-supplied text is never enough to lower authority requirements.

## 11. Mutation class mapping

### `read_only`

Meaning: known non-mutating inspection/query action.

Gate mapping: `_is_mutating_action()` returns `False`.

Default with no AP rule: allowed.

### `runtime_mutation`

Meaning: known state-changing runtime action.

Gate mapping: `_is_mutating_action()` returns `True`.

Default with no AP authorizing rule: denied.

### `unknown`

Meaning: action cannot be proven read-only or safely classified.

Gate mapping: `_is_mutating_action()` returns `None`.

Default with no AP authorizing rule: denied with mutation-unknown reason.

`unknown` is not treated as mutating-true. It is treated as unclassified, which is stricter than mutating: it fails closed before any compatibility assumption is made.

This prevents future implementers from accidentally converting:

```text
unknown -> True
```

when it really means:

```text
unknown -> None -> fail closed
```

## 12. Final invariant

EngAInOS, not the caller, owns the effective action classification used by AP.

No caller-supplied action text, `required_tier`, `read_set`, `write_set`, or `mutation_class` may lower AP authority requirements unless EngAInOS has explicitly classified the route/action as trusted.
