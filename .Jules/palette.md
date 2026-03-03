## 2025-05-23 - Import Paths and Python GUI UX
**Learning:** A broken application (due to incorrect imports) is the ultimate bad UX. Python's `sys.path` and package structure can be fragile if not tested in the environment where the user runs the tool. Fixes that enable the application to run are the highest priority UX improvements.
**Action:** Always verify that a Python script can be imported or run from the repo root before assuming the GUI is functional. Use `python -c "import module"` as a quick smoke test.

## 2025-05-23 - Unsaved Changes Indicator
**Learning:** Users rely heavily on visual cues like the `*` in the window title to know if their work is safe. This "invisible" feature prevents data loss and builds trust. Tkinter's `Text` widget adds a trailing newline which can complicate dirty checking; always use `"end-1c"` for consistent content comparison.
**Action:** When implementing save logic in Tkinter, ensure the content written to disk matches the in-memory representation used for change tracking, specifically handling the trailing newline.
## 2026-02-26 - [Tkinter Dirty State]
**Learning:** Relying on <KeyRelease> misses mouse-only edits (e.g. Paste) in text widgets.
**Action:** Use the <<Modified>> virtual event or additionally bind <ButtonRelease>.

## 2026-03-03 - Tkinter Cursor Tracking UX
**Learning:** Adding a real-time cursor position (Line/Col) to the status bar of a text editor is a high-value micro-UX enhancement that helps users orient themselves, especially in long files. To ensure it accurately reflects both keyboard and mouse-driven edits (including paste operations), bindings must include `<KeyRelease>`, `<ButtonRelease>`, and `<<Modified>>`. When using `<<Modified>>`, it is critical to reset the widget's modified flag (`edit_modified(False)`) so subsequent edits continue firing the event.
**Action:** Always include a mechanism to track line/column position in custom text editors to improve spatial awareness, and ensure event bindings cover all input modalities (keyboard, mouse, clipboard).
