# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2024-05-15 - [Tkinter Text Accessibility]
**Learning:** Raw terminal-like outputs in GUI logs can become inaccessible walls of text. Adding semantic color tagging (like #51cf66 for success, #ff6b6b for errors) makes state reading much faster. Also, users expect standard text editor features like Undo/Redo to be available by default in multi-line inputs.
**Action:** When initializing ScrolledText widgets, always enable `undo=True` to prevent frustration, and configure `tag_config` early so output logic can easily colorize success/error states without extra boilerplate.
