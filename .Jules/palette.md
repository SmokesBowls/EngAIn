# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY
## 2025-03-09 - [Semantic Color Coding and Undo/Redo in Tkinter]
**Learning:** For Tkinter ScrolledText widgets in GUI applications, standard practice is to enable basic undo/redo functionality using `undo=True` and `autoseparators=True` during initialization. Additionally, setting semantic color-coding tags (e.g., `#51cf66` for success, `#ff6b6b` for error) using `tag_config` vastly improves visual accessibility and feedback mechanisms without custom CSS hacks.
**Action:** Always enable undo capabilities and leverage `tag_config` for semantic UI coloring when adding UX elements in Tkinter text components.
