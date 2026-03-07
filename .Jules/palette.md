# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2024-06-25 - Reliable Dirty State Tracking with Undo in Tkinter
**Learning:** When enabling native undo functionality (`undo=True`) in a Tkinter `Text` or `ScrolledText` widget, relying solely on keyboard bindings (like `<KeyRelease>`) or mouse clicks to track dirty state becomes unreliable, as users can undo/redo changes via shortcuts without triggering these specific events. The document can also be changed via external pastes.
**Action:** Bind the `<<Modified>>` virtual event to accurately track any document changes (including undos and standard pastes). Crucially, the modified flag must be explicitly reset by calling `edit_modified(False)` within the event handler to ensure the event fires for subsequent modifications.