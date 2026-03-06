# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2025-03-05 - Visual Accessibility and Feedback in Tkinter Text Widgets
**Learning:** In desktop GUIs (Tkinter `ScrolledText`), using just emojis (✅/❌) for parse/validation output isn't glanceable enough. Color-coding success/error states directly on the text using `tag_config` improves visual accessibility and helps users immediately understand system status without reading the full text.
**Action:** When adding log outputs or validation status to `Text` or `ScrolledText` widgets, always define success/error color tags (`#51cf66` and `#ff6b6b`) and apply them to status headers or labels.
