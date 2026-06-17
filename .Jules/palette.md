## 2024-03-01 - Add Cursor Position Indicator to Tkinter GUI
**Learning:** Adding dynamic, context-aware information (like a cursor position tracking Ln/Col) is a high-value, low-effort micro-UX improvement for code editors. Tkinter `Text` / `ScrolledText` indices (row.col) map very nicely to this. For accessibility/robustness, checking `hasattr` before updating is crucial to avoid startup errors during widget initialization. Headless test runs of Tkinter code on Linux require both `python3-tk` and `xvfb` (`xvfb-run pytest`).
**Action:** When working on text editing widgets across different frameworks, prioritize adding a cursor position indicator early, as it significantly enhances user navigation and debugging. Always ensure proper headless testing dependencies are available in CI/development environments for GUI code.

## 2024-05-15 - Make Output Text Areas Read-Only
**Learning:** Using `tk.DISABLED` on a `ScrolledText` widget when it's meant to be an output display panel (like for parsed results or validation messages) prevents users from accidentally typing into it. It removes confusion about whether their typing in the output panel affects the application state. Setting `focus_set()` on the main input editor upon startup further streamlines the user workflow.
**Action:** When designing tools with an "Input -> Output" split pane, always ensure the Output pane is properly marked read-only and handle state toggles (`tk.NORMAL` -> insert text -> `tk.DISABLED`) during programmatic updates. Give immediate focus to the primary input area.

## 2024-04-09 - In-App Dirty State Indicator
**Learning:** Relying solely on the OS window title for dirty states (like `*` for unsaved changes) is insufficient because window titles can be truncated or overlooked by the user. Displaying the dirty state in an in-app label provides a much clearer and more accessible indication.
**Action:** Always include dirty state indicators within the application's UI itself, alongside any OS-level indicators, to ensure users are aware of unsaved changes.
## 2024-05-24 - Add Consistent Select All Shortcut to Tkinter Text Widgets
**Learning:** Tkinter's `Text` and `ScrolledText` widgets lack consistent cross-platform support for the 'Select All' keyboard shortcut.
**Action:** Explicitly bind both `<Control-a>` and `<Control-A>` to a custom method that applies the `tk.SEL` tag from `1.0` to `tk.END` and returns `'break'` to ensure expected functionality and prevent duplicate event handling.
