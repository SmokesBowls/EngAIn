# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2025-03-08 - Tkinter Editor Missing Standard Edit Support
**Learning:** Initializing Tkinter `ScrolledText` by default lacks native Undo (Ctrl+Z) and Redo (Ctrl+Y), and standard key-binding dirty tracking (via `<KeyRelease>`) entirely fails to capture mouse actions like Paste or Cut.
**Action:** Always enable `undo=True, autoseparators=True` for text editors. Furthermore, track edits using `<<Modified>>`, and critically, ensure you call `.edit_modified(False)` after handling it, or the event will never fire again for subsequent edits.