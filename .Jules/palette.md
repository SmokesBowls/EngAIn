## 2025-05-23 - Import Paths and Python GUI UX
**Learning:** A broken application (due to incorrect imports) is the ultimate bad UX. Python's `sys.path` and package structure can be fragile if not tested in the environment where the user runs the tool. Fixes that enable the application to run are the highest priority UX improvements.
**Action:** Always verify that a Python script can be imported or run from the repo root before assuming the GUI is functional. Use `python -c "import module"` as a quick smoke test.

## 2025-05-23 - Unsaved Changes Indicator
**Learning:** Users rely heavily on visual cues like the `*` in the window title to know if their work is safe. This "invisible" feature prevents data loss and builds trust. Tkinter's `Text` widget adds a trailing newline which can complicate dirty checking; always use `"end-1c"` for consistent content comparison.
**Action:** When implementing save logic in Tkinter, ensure the content written to disk matches the in-memory representation used for change tracking, specifically handling the trailing newline.
## 2026-02-26 - [Tkinter Dirty State]
**Learning:** Relying on <KeyRelease> misses mouse-only edits (e.g. Paste) in text widgets.
**Action:** Use the <<Modified>> virtual event or additionally bind <ButtonRelease>.

## 2025-05-24 - Tkinter Event Bindings for Cursor and Dirty State
**Learning:** Implementing real-time cursor position tracking requires binding `<KeyRelease>`, `<ButtonRelease>`, and `<<Modified>>` to adequately cover all forms of interaction (keyboard, mouse clicks, and paste). However, the `<<Modified>>` event will only fire once unless `edit_modified(False)` is explicitly called afterward.
**Action:** When tracking cursor position or dirty state in Tkinter Text widgets, bind all three events and ensure the `edit_modified` flag is reset to `False` after processing `<<Modified>>`.
