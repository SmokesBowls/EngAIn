# EngAIn Command Schema v1

Rule of thumb: if it mentions `.gd`, `.tscn`, node paths, scenes, or the editor —
it's a **Godot Adapter** command. If it mentions packets, ledgers, stamps, or
approvals — it's **Core**. If it's what you click — it's the **Command Center**.

## Layer 1 — EngAIn Core (engine-agnostic, already built)

These exist today in `interface/` and don't need to change. They know nothing
about Godot; they'd work identically if the target engine were Unity or Bevy.

| Script | Command | Notes |
|---|---|---|
| `000_status.py` | `get_status` | git state, protected files, dir paths |
| `010_show_protected_files.py` | `list_protected` | reads `protected_files.json` |
| `020_show_ledger.py` | `get_ledger` | reads `ledger.jsonl` |
| `030_create_task_packet.py` | `create_packet` | writes to `packets/` |
| `040_show_next_command.py` | `get_next_packet` | oldest PENDING packet |
| `050_record_command_output.py` | `record_result` | writes `results/`, flips packet to COMPLETED |
| `080_stamp_result.py` | `stamp` | PASS/FAIL/PARTIAL/VOID/RESTORED/BLOCKED |
| `090_recover_file_from_git.py` | `recover_file` | git is engine-agnostic |

**Core needs one addition:** an `attribution` field on every ledger entry —
`"actor": "human" | "orchestrator" | "adapter:godot"`. Cheap to add to
`append_ledger()`, and it's the thing that makes "I manuscript the .gd/.tscn
by hand" auditable instead of just asserted.

## Layer 2 — Godot Adapter (engine-specific, mostly new)

Everything below translates a Core action into a Godot-specific check. None
of this belongs in Core — if you ever add a second engine, this whole layer
gets swapped, Core doesn't move.

| Command | What it does | Status |
|---|---|---|
| `check_gd_syntax` | Runs Godot headless (`godot --headless --check-only --script <file>`) | new |
| `validate_scene_structure` | Parses a `.tscn` for structural sanity (unresolved `ext_resource`, dangling node paths, duplicate node names) | new |
| `run_headless_gate` | Runs a gate scene/script headless and captures pass/fail | exists (`070_run_headless_gate.py`) — already adapter-shaped, just needs to move into the adapter folder conceptually |
| `attach_behavior_to_entity` | Future: templated node/script attachment | not started |
| `export_engine_payload` | Future: package a validated scene+script bundle for handoff | not started |

## Layer 3 — Command Center (the UI you sit in)

Buttons call Core or Adapter commands. The UI never contains business logic —
it renders whatever Core/Adapter return and shows the ledger tape live.

```
command_center/
├── app.py              # Eel backend — subprocess bridge to interface/*.py
├── web/
│   ├── index.html      # panels + buttons
│   ├── style.css
│   └── app.js          # calls exposed Python fns, renders ledger tape
```

## Why this order matters

You're the manuscript-writer now, not an AI. That means the system's real job
is: **never let a script silently touch a `.gd`/`.tscn` file, always show you
what ran and what it returned, and log who (human vs orchestrator) did what.**
Core already does the "show status, log evidence, stamp results" half. The
Godot adapter is what's missing for the *validation* half of your new
workflow — and it should stay small and swappable, not baked into Core.
