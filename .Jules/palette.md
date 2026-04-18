## 2024-03-01 - Add Cursor Position Indicator to Tkinter GUI
**Learning:** Adding dynamic, context-aware information (like a cursor position tracking Ln/Col) is a high-value, low-effort micro-UX improvement for code editors. Tkinter `Text` / `ScrolledText` indices (row.col) map very nicely to this. For accessibility/robustness, checking `hasattr` before updating is crucial to avoid startup errors during widget initialization. Headless test runs of Tkinter code on Linux require both `python3-tk` and `xvfb` (`xvfb-run pytest`).
**Action:** When working on text editing widgets across different frameworks, prioritize adding a cursor position indicator early, as it significantly enhances user navigation and debugging. Always ensure proper headless testing dependencies are available in CI/development environments for GUI code.

## 2024-05-15 - Make Output Text Areas Read-Only
**Learning:** Using `tk.DISABLED` on a `ScrolledText` widget when it's meant to be an output display panel (like for parsed results or validation messages) prevents users from accidentally typing into it. It removes confusion about whether their typing in the output panel affects the application state. Setting `focus_set()` on the main input editor upon startup further streamlines the user workflow.
**Action:** When designing tools with an "Input -> Output" split pane, always ensure the Output pane is properly marked read-only and handle state toggles (`tk.NORMAL` -> insert text -> `tk.DISABLED`) during programmatic updates. Give immediate focus to the primary input area.

## 2026-04-18 - Add In-App Dirty State Indicator
**Learning:** Relying solely on the OS window title for dirty state (unsaved changes) is a poor UX because it can be truncated, hidden by the OS, or overlooked. Displaying the dirty state in a persistent, in-app file label provides much better visibility and reduces the risk of accidental data loss. Checking `hasattr` before updating avoids startup race conditions.
**Action:** When implementing file editing GUIs, always mirror document state (like unsaved changes) in an in-app indicator (e.g., status bar or toolbar label) rather than relying exclusively on window titles.
