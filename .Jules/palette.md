# PALETTE'S JOURNAL - CRITICAL LEARNINGS ONLY

## 2024-05-15 - [Visual Accessibility in Tkinter]
**Learning:** Using tags in `ScrolledText` to semantically color success/error messages greatly improves quick visual parsing of logs and validation results.
**Action:** Always utilize `tag_config` (`success` green, `error` red) for log or validation outputs in `ScrolledText` widgets.
