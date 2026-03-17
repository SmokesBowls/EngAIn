# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2024-05-18 - Tkinter ScrolledText Accessibility & UX
**Learning:** Tkinter `ScrolledText` widgets do not support standard undo/redo functionality (e.g., Ctrl+Z) by default, which can lead to accidental data loss in editing interfaces. Also, mapping semantic meanings (success/error) to specific foreground colors enhances visual accessibility in output panels.
**Action:** Always initialize Tkinter `Text` or `ScrolledText` widgets intended for editing with `undo=True` and `autoseparators=True`. Use `tag_config` to create semantic color tags (e.g., `#51cf66` for success, `#ff6b6b` for error) and apply them to text insertions.
