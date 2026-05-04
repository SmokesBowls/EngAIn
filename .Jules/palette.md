## 2024-03-01 - Add Cursor Position Indicator to Tkinter GUI
**Learning:** Adding dynamic, context-aware information (like a cursor position tracking Ln/Col) is a high-value, low-effort micro-UX improvement for code editors. Tkinter `Text` / `ScrolledText` indices (row.col) map very nicely to this. For accessibility/robustness, checking `hasattr` before updating is crucial to avoid startup errors during widget initialization. Headless test runs of Tkinter code on Linux require both `python3-tk` and `xvfb` (`xvfb-run pytest`).
**Action:** When working on text editing widgets across different frameworks, prioritize adding a cursor position indicator early, as it significantly enhances user navigation and debugging. Always ensure proper headless testing dependencies are available in CI/development environments for GUI code.

## 2024-05-15 - Make Output Text Areas Read-Only
**Learning:** Using `tk.DISABLED` on a `ScrolledText` widget when it's meant to be an output display panel (like for parsed results or validation messages) prevents users from accidentally typing into it. It removes confusion about whether their typing in the output panel affects the application state. Setting `focus_set()` on the main input editor upon startup further streamlines the user workflow.
**Action:** When designing tools with an "Input -> Output" split pane, always ensure the Output pane is properly marked read-only and handle state toggles (`tk.NORMAL` -> insert text -> `tk.DISABLED`) during programmatic updates. Give immediate focus to the primary input area.

## 2024-10-24 - File label dirty state indicator
**Learning:** Relying purely on the window title for unsaved changes (`*`) can be easily missed if the window is maximized, the title bar is truncated, or the user is focused purely on the toolbars. Mirroring this indicator to the prominently displayed file path label within the UI greatly enhances visual awareness of the file's current dirty state.
**Action:** Ensure the dirty state `*` is clearly visible on in-app elements representing the file context, like labels or tabs, checking `hasattr` to prevent startup errors.
