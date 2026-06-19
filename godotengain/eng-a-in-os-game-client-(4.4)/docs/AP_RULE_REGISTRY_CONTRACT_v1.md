# EngAInOS AP Rule Registry Contract v1

Status: doctrine / contract

Target system: EngAInOS AP stage rule discovery and validation.

Purpose: define how AP rule files are discovered, structurally parsed, validated, filtered into active registries, and reported before any predicate/effects evaluator is wired into `authority_gate.py`.

Scope of this contract: rule registry discovery and load-time validation only.

Out of scope for this contract:

- predicate expression evaluation
- effects execution
- runtime mutation
- wiring the loader into `authority_gate.py`
- changing `evaluate()` from `ap_registry=[]`

## 1. Registry root

The EngAInOS AP rule registry root is:

```text
godotengain/engainos/rules/
```

Each immediate child directory is a registry name.

The first registry is:

```text
godotengain/engainos/rules/runtime_mutation/
```

Registry name:

```text
runtime_mutation
```

## 2. Runtime mutation registry purpose

The `runtime_mutation` registry contains AP rules that decide whether a classified runtime action may proceed toward runtime execution.

It does not classify actions. Action classification is owned by:

```text
godotengain/engainos/docs/ACTION_CLASSIFICATION_CONTRACT_v1.md
```

It does not mutate runtime state directly. It produces AP decisions and telemetry.

## 3. Rule file extension

AP rule files use the `.zon` extension.

The loader must only discover files matching:

```text
*.zon
```

Non-`.zon` files are ignored unless a future contract explicitly adds another profile/extension.

## 4. Rule profile

The first non-empty line of an AP rule file must declare the ZON AP profile:

```text
#ZON ap/0.1; caps=...; guard=...
```

For this first loader slice, the loader must require:

```text
#ZON ap/0.1
```

Unknown profiles or missing profile headers are load-time errors.

The loader may preserve `caps` and `guard` metadata as strings but must not grant authority based on them in this slice.

## 5. Required metadata fields

Each AP rule file must contain exactly one value for:

- `@id`
- `@scope`
- `@status`
- `@priority`

Required field meanings:

- `@id`: globally unique rule ID. Convention: `rule:<domain>.<name>`.
- `@scope`: promotion state for the rule artifact.
- `@status`: active/tombstone state.
- `@priority`: integer priority. Higher priority sorts earlier.

Missing, duplicated, or malformed required metadata is a load-time error.

## 6. Required blocks

Each AP rule file must contain these blocks:

- `=requires`
- `=read_set`
- `=write_set`
- `=effects`

Each block must terminate with:

```text
=end
```

For this first loader slice, block lines are parsed as raw strings after the leading list marker `- ` is removed where present.

The loader must not evaluate `=requires` or execute `=effects` in this slice.

## 7. Scope handling

Valid `@scope` values are:

- `open_loop`
- `canon`
- `style`
- `log`

Scope behavior:

```text
open_loop -> structurally loaded for audit, excluded from active registry
canon     -> eligible for active registry when status=active
style     -> advisory only; write_set and effects must be empty
log       -> telemetry only; effects must be empty
```

Load-time validation:

- `@scope: style` with non-empty `=write_set` is invalid.
- `@scope: style` with non-empty `=effects` is invalid.
- `@scope: log` with non-empty `=effects` is invalid.

Invalid rule files are rejected at load time.

## 8. Status handling

Valid `@status` values are:

- `active`
- `disabled`

Status behavior:

```text
active   -> eligible for active registry if @scope is canon
disabled -> loaded for audit/history but excluded from active registry
```

Disabled rules are tombstones. They must not fire.

## 9. Active registry filter

A rule enters the active registry only when:

```text
@status == active
AND
@scope == canon
AND
load-time validation passed
```

Rules with `@scope: open_loop`, `@scope: style`, `@scope: log`, or `@status: disabled` may be returned in an audit list, but must not enter the active registry.

## 10. Duplicate IDs

Duplicate `@id` values within a registry are a load-time registry error.

The loader must reject the registry result rather than choosing one file silently.

Reason: duplicate IDs destroy deterministic authority and telemetry.

## 11. Sort order

Active rules are sorted deterministically by:

```text
@priority descending
@id ascending
```

This matches the AP evaluation contract and allows priority-based veto rules such as:

```text
rule:runtime_mutation.replay_blocks_all priority 2000
rule:runtime_mutation.reality_mode_gate priority 1000
```

## 12. Loaded rule dict shape

The loader should produce rule dictionaries shaped like:

```python
{
    "id": "rule:runtime_mutation.replay_blocks_all",
    "scope": "canon",
    "status": "active",
    "priority": 2000,
    "requires": [
        'envelope.reality_mode == "REPLAY"',
    ],
    "read_set": [
        "envelope.reality_mode",
    ],
    "write_set": [],
    "effects": [
        "decision.allowed = false",
        'decision.blocked_by = "rule:runtime_mutation.replay_blocks_all"',
    ],
    "source_path": "godotengain/engainos/rules/runtime_mutation/replay_blocks_all.zon",
    "profile": "ap/0.1",
    "caps": "authority",
    "guard": "canon.safe",
}
```

The exact in-memory class may change later, but these keys are the first-slice contract for downstream tests.

## 13. Loader result shape

The loader should return both active rules and audit information.

Suggested result shape:

```python
{
    "registry": "runtime_mutation",
    "active_rules": [...],
    "audit_rules": [...],
    "errors": [],
}
```

If registry loading fails closed due to invalid rule files or duplicate IDs, `errors` must explain why.

A first implementation may raise a typed exception instead of returning errors, but it must not silently drop invalid active rule files.

## 14. Failure Domains

The AP stack contains multiple fail-closed mechanisms operating at different stages.

These mechanisms are not interchangeable.

### 14.1 Registry Load-Time Rejection

Occurs during:

- `ap_rule_loader.py`
- registry validation

Examples:

- malformed ZON file
- missing `@id`
- invalid profile/version
- `@scope: style` with non-empty `write_set`
- `@scope: log` with non-empty `effects`
- invalid priority value

Result:

- rule is not loaded
- rule never enters active registry
- request processing is unaffected except rule absence

Authority meaning:

The rule artifact itself is invalid.

### 14.2 Request-Time Classification Denial

Occurs during:

- action classification
- pre-AP evaluation

Examples:

- unknown action
- `mutation_class == unknown`
- unsupported runtime action

Result:

- request denied
- fail closed
- no AP rule evaluation required

Authority meaning:

The request cannot be safely classified.

Mapping:

```text
mutation_class: unknown
-> _is_mutating_action() returns None
-> fail closed
```

This is not the same as:

```text
mutation_class: runtime_mutation
```

which maps to:

```text
-> _is_mutating_action() returns True
-> continue into AP evaluation
```

### 14.3 AP Evaluation Denial

Occurs during:

- predicate evaluation
- priority resolution
- conflict resolution

Examples:

- REPLAY mutation veto
- insufficient authority tier
- `blocked_by` higher-priority rule

Result:

- request denied
- `ap_decision` produced
- telemetry emitted

Authority meaning:

The request was understood and classified, but AP determined it is not allowed.

### 14.4 Runtime Execution Failure

Occurs after AP approval.

Examples:

- runtime endpoint unavailable
- entity not found
- scene load failure

Result:

- execution error
- authority already granted

Authority meaning:

Permission existed. Execution failed.

### 14.5 Failure-domain invariant

A rule-file rejection means the rule is invalid.

A request denial means the rule is valid but the request is not allowed.

These are different failure domains and must not be conflated.

## 15. First implementation ticket boundary

The first implementation after this contract should create:

```text
godotengain/engainos/core/ap_rule_loader.py
```

It must not wire the loader into:

```text
godotengain/engainos/core/authority_gate.py
```

`authority_gate.evaluate()` must keep:

```python
ap_registry=[]
```

until the predicate/effects evaluator and wiring ticket are explicitly approved.

## 16. Final invariant

The AP rule registry owns rule artifact validity and active-rule discovery only.

It does not own action classification, predicate truth, effects execution, AP approval, or runtime mutation.
