## 2024-03-01 - Add Cursor Position Indicator to Tkinter GUI
**Learning:** Adding dynamic, context-aware information (like a cursor position tracking Ln/Col) is a high-value, low-effort micro-UX improvement for code editors. Tkinter `Text` / `ScrolledText` indices (row.col) map very nicely to this. For accessibility/robustness, checking `hasattr` before updating is crucial to avoid startup errors during widget initialization. Headless test runs of Tkinter code on Linux require both `python3-tk` and `xvfb` (`xvfb-run pytest`).
**Action:** When working on text editing widgets across different frameworks, prioritize adding a cursor position indicator early, as it significantly enhances user navigation and debugging. Always ensure proper headless testing dependencies are available in CI/development environments for GUI code.

## 2024-05-15 - Make Output Text Areas Read-Only
**Learning:** Using `tk.DISABLED` on a `ScrolledText` widget when it's meant to be an output display panel (like for parsed results or validation messages) prevents users from accidentally typing into it. It removes confusion about whether their typing in the output panel affects the application state. Setting `focus_set()` on the main input editor upon startup further streamlines the user workflow.
**Action:** When designing tools with an "Input -> Output" split pane, always ensure the Output pane is properly marked read-only and handle state toggles (`tk.NORMAL` -> insert text -> `tk.DISABLED`) during programmatic updates. Give immediate focus to the primary input area.

## 2024-04-09 - In-App Dirty State Indicator
**Learning:** Relying solely on the OS window title for dirty states (like `*` for unsaved changes) is insufficient because window titles can be truncated or overlooked by the user. Displaying the dirty state in an in-app label provides a much clearer and more accessible indication.
**Action:** Always include dirty state indicators within the application's UI itself, alongside any OS-level indicators, to ensure users are aware of unsaved changes.

## 2024-05-31 - Add Keyboard Shortcut Hints to Toolbar Buttons
**Learning:** While adding `accelerator` attributes to menu items is good practice, discovering shortcuts is often difficult for users who primarily interact with the main toolbar. Appending shortcut hints directly to primary toolbar button labels (e.g., `text="Parse (F5)"`) significantly improves keyboard shortcut discoverability in Tkinter GUIs. Also, setting the `accelerator` attribute on a Tkinter menu item only provides a visual hint; the actual keyboard shortcut functionality must be implemented by explicitly binding the corresponding event to the root window.
**Action:** When adding keyboard shortcuts to primary actions, ensure the shortcut hint is visible on the main UI element (like a toolbar button) in addition to the menu item, and always explicitly bind the event to the root window.
