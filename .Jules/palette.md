# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2023-11-20 - Tkinter Text Widget Edits & State
**Learning:** `KeyRelease` and `ButtonRelease` are insufficient for tracking modifications in Tkinter text widgets since they miss interactions like context-menu pasting or programmed edits. Additionally, the `undo=True` and `autoseparators=True` flags offer critical native history tracking.
**Action:** Always bind the `<<Modified>>` virtual event (and reset it via `edit_modified(False)`) to capture all modifications, and configure text widgets with `undo=True` to provide expected text-editing UX.
