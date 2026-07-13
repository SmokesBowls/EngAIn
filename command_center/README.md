# EngAIn Command Center

A local, offline HTML cockpit over the existing `interface/*.py` scripts.
No AI in the loop — every button is a deterministic subprocess call.

## Setup

```bash
pip install eel
```

Place this `command_center/` folder next to your existing `interface/`
folder (i.e. as a sibling under the repo root):

```
<repo_root>/
├── interface/
│   ├── 000_status.py
│   ├── ... (unchanged, do not move anything)
└── command_center/
    ├── app.py
    └── web/
```

If your layout differs, set `ENGAIN_ROOT` before launching:

```bash
ENGAIN_ROOT=/path/to/repo_root python3 command_center/app.py
```

## Run

```bash
cd command_center
python3 app.py
```

This opens a Chrome/Chromium window (Eel requires one installed) at
`web/index.html`, backed by the functions in `app.py`.

## What's real vs stubbed

- **Core tab** — fully wired to your existing scripts (000, 010, 020, 030,
  040, 080, 090). These work today, no changes needed on the Python side.
- **Godot Adapter tab** — `check_gd_syntax` and `validate_scene_structure`
  are stubs that always report FAIL with a clear "not implemented" message.
  Fill in the bodies in `app.py` once you decide the exact Godot headless
  invocation you want (see `engain_command_schema.md` for the shape).
- **Packets tab** — wired to `030_create_task_packet.py`.

## Extending

To add a new button:
1. Add a script-calling (or adapter-stub) function to `app.py`, decorated
   with `@eel.expose`.
2. Add a `<button class="tile" data-action="...">` (no-arg) or
   `data-form="..."` (needs a prompt) in `index.html`.
3. If it's a form-style button, add its branch in the `data-form` handler
   in `app.js`.

The ledger tape at the bottom is a live mirror of `ledger.jsonl` — anything
that calls `append_ledger()` on the Python side shows up there automatically
after a refresh.
