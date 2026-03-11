# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2026-03-11 - [Tkinter ScrolledText Accessibility & Data Loss]
**Learning:** Default Tkinter `ScrolledText` lacks essential undo/redo functionality (causing potential data loss) and visual distinction for status outputs. Standard practice in this codebase for visual accessibility is to use `tag_config` with specific semantic colors (`#51cf66` for success, `#ff6b6b` for error).
**Action:** Always enable `undo=True` and `autoseparators=True` when creating Tkinter text widgets, and use standard semantic colors for pass/fail output indicators to improve scannability.
