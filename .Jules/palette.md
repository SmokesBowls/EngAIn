## 2024-03-01 - Add Cursor Position Indicator to Tkinter GUI
**Learning:** Adding dynamic, context-aware information (like a cursor position tracking Ln/Col) is a high-value, low-effort micro-UX improvement for code editors. Tkinter `Text` / `ScrolledText` indices (row.col) map very nicely to this. For accessibility/robustness, checking `hasattr` before updating is crucial to avoid startup errors during widget initialization. Headless test runs of Tkinter code on Linux require both `python3-tk` and `xvfb` (`xvfb-run pytest`).
**Action:** When working on text editing widgets across different frameworks, prioritize adding a cursor position indicator early, as it significantly enhances user navigation and debugging. Always ensure proper headless testing dependencies are available in CI/development environments for GUI code.

## 2024-05-15 - Make Output Text Areas Read-Only
**Learning:** Using `tk.DISABLED` on a `ScrolledText` widget when it's meant to be an output display panel (like for parsed results or validation messages) prevents users from accidentally typing into it. It removes confusion about whether their typing in the output panel affects the application state. Setting `focus_set()` on the main input editor upon startup further streamlines the user workflow.
**Action:** When designing tools with an "Input -> Output" split pane, always ensure the Output pane is properly marked read-only and handle state toggles (`tk.NORMAL` -> insert text -> `tk.DISABLED`) during programmatic updates. Give immediate focus to the primary input area.

## 2026-03-24 - Prevent Tkinter Button Flash on Custom Dark Themes
**Learning:** When styling Tkinter buttons with custom background colors for dark themes, they will flash their default system colors (often light gray) when clicked, creating a jarring UX. Setting the `activebackground` and `activeforeground` properties is necessary to maintain theme consistency during interactions.
**Action:** Always specify `activebackground` and `activeforeground` explicitly when configuring Tkinter `tk.Button` with custom `bg` and `fg` colors, ensuring the active states match the surrounding theme.

## 2026-06-12 - Auto-switch active tabs in Tkinter Notebooks for context relevance
**Learning:** In Tkinter applications using `ttk.Notebook`, when an action generates output in a specific tab (like "Parse" or "Validate"), users may not realize the action succeeded if that tab isn't currently active. Programmatically switching to the relevant tab (`notebook.select(frame)`) provides immediate, visible confirmation of the result and improves navigation flow.
**Action:** Always auto-switch the active tab in `ttk.Notebook` to match the context of the user's latest action, ensuring they don't have to manually click to find the output they just requested.
