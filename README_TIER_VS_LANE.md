# TIER vs. LANE Governance Specification

In the EngAIn architecture, safety and state governance are split into two orthogonal axes: **Tiers** and **Lanes**.

```
              TIER (Who decides)
               Tier 3: Human Authority Root
               Tier 2: Human Operator Limited
               Tier 1: AI Agent
               Tier 0: System
                      │
                      ▼
  LANE ───────────────┼───────────────► LANE
 (Where work happens) │              (Where work happens)
  e.g., Core / AP     │               e.g., Godot Client
```

---

## 1. Tiers: Who Decides

A **Tier** designates the authority level of the actor executing the command or requesting the state change:
- **Tier 3 (Human Root)**: Absolute authority to override rules and write to finalized canon.
- **Tier 2 (Human Operator)**: Assisted operator state, allowing mutations in DRAFT or IMBUED modes.
- **Tier 1 (AI Agent)**: Automated, programmatically constrained operations. Cannot edit finalized files or bypass core gates.
- **Tier 0 (System)**: Internal machinery and deterministic validation pipelines.

---

## 2. Lanes: Where Work May Happen

A **Lane** defines the boundary or path where a given set of operations or processes is permitted to run:
- **AP/Core Lane**: Authors state transitions, runs rule checks, and validates constraints.
- **Presentation Lane (Godot/UPBGE)**: Renders snapshots and submits commands. It has *zero* state authority.
- **Narrative Pipeline Lane (Mettaext)**: Performs text ingestion and ZON memory bridge compilation.
- **Tooling/Migration Lane**: Conducts code checks and helper executions.

### Key Rules
1. **No Lane Theft**: Subsystems must not execute code or claim authority outside their designated lane (e.g., presentation layer writing state).
2. **Lane Separation Invariant**: The Core must never import presentation layer code (`aproom ← core ← tools ← godot`).
3. **Fail-Closed**: Any operation in an uncertain or overlapping lane state must fail-closed immediately to protect project integrity.
