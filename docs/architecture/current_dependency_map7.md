# MrLore v2 Subsystem Dependency Map (`_mrlore`)

This document establishes the structural roles, calling patterns, schemas, and execution targets for the persistent continuity co-authoring and auditing suite under `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore`.

---

## 1. Governance & Synthesis Layer

Governs the indexing, synthesis rules, page contracts, and structural categories of the wiki synthesis databases.

### [MRLORE_SCHEMA.md](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/schema/MRLORE_SCHEMA.md)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/schema/MRLORE_SCHEMA.md`
* **Role:** The structural doctrine defining the purpose, contracts, directory rules, and quality standards for MrLore v2. Maps authority layers (narrative sources, canon decisions, editorial reviews, wiki synthesis, runtime exports).
* **Imports/Calls:** Standard markdown anchors.
* **Called By:** Referenced by external developers, session boot scripts, and ingestion operators during manual or automated wiki updates.
* **Hardcoded Paths:** `~/notebook/mrlore_v2/` (suggested root).
* **Safe to Move:** **No** (Foundational schema guiding parser layouts).
* **Notes:** Establishes the core doctrine: `raw source is truth | wiki is synthesis | chat is temporary`.

---

## 2. Ingestion & Auditing Suite (`tools/`)

The dynamic Python scripts and bash entry points automating the ingestion runs, registry compilation, structural linting, and character continuity auditing.

### [mrlore_session.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/mrlore_session.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/mrlore_session.py`
* **Role:** Session initializer and boot validator. Checks for required schema directories, scans parent Obsidian vault directories while applying standard exclusions, and indexes candidate MD/TXT source files.
* **Imports/Calls:** `pathlib`, `datetime`, `sys`
* **Called By:** Executed manually or via pipeline scripts to establish a healthy session boundary before starting ingestion.
* **Hardcoded Paths:** None (dynamically resolves parents relative to `__file__`).
* **Safe to Move:** **Yes**
* **Notes:** Excludes standard system subfolders like `.git`, `.obsidian`, `_mrlore`, `__pycache__`, and `.trash`.

---

### [mrlore_run_changed.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/mrlore_run_changed.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/mrlore_run_changed.py`
* **Role:** Primary pipeline driver. Reads lists of modified story chapters, classifies authority tiers, runs specific file ingests, triggers registry rebuilds, executes wiki lints, and runs the continuity checker.
* **Imports/Calls:** `ingest_source_stub.py`, `build_registry.py`, `lint_wiki.py`, `continuity_audit.py`, `yaml`
* **Called By:** Standalone triggers, CocoIndex runners, or local review hooks.
* **Hardcoded Paths:** `_mrlore`, `logs`, `wiki` (resolved dynamically relative to script path).
* **Safe to Move:** **Yes**
* **Notes:** Implements standard exit codes (0 = clean run, 1 = structural lint failure, 2 = canon conflicts flagged in `CONT-*.yaml`).

---

### [continuity_audit.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/continuity_audit.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/continuity_audit.py`
* **Role:** Character continuity and lexical checker. Analyzes newly-ingested chapters to flag logical character inconsistencies, emotional trajectory gaps, behavioral drift, or spelling anomalies (e.g. Neferati vs Nephoretti).
* **Imports/Calls:** `yaml`, `json`, `pathlib`, `datetime`
* **Called By:** `mrlore_run_changed.py` (during Pass 5c: Continuity Audit Phase).
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Writes flagged contradictions directly to first-class conflict manifests (`CONT-*.yaml` under `wiki/continuity/`).

---

### [promotion_eligibility_gate.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/promotion_eligibility_gate.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/promotion_eligibility_gate.py`
* **Role:** State promotion regulator. Validates whether provisional character details or lore claims are eligible to be merged into stable canon profiles.
* **Imports/Calls:** `authority_score_calculator`
* **Called By:** Registry tools during page synthesis.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Implements `authority_score_calculator` imports to prevent narrative scoring drift.

---

### [authority_score_calculator.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/authority_score_calculator.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/authority_score_calculator.py`
* **Role:** Numerical authority solver. Computes narrative confidence weights across story files based on drafting book indices, source classifications, and review loops.
* **Imports/Calls:** None.
* **Called By:** `promotion_eligibility_gate.py`
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Pure mathematical utility returning normalized confidence levels.

---

### [write_changed_manifest.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/write_changed_manifest.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/write_changed_manifest.py`
* **Role:** File sync tracker. Identifies changed prose files, compares checksum targets, and writes clean changed manifests for subsequent ingestion.
* **Imports/Calls:** `re`, `shutil`, `tempfile`
* **Called By:** Master pipeline schedules.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Works on a flat target of Posix paths.

---

### [propose_corrections.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/propose_corrections.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/propose_corrections.py`
* **Role:** Suggestion compiler. Formulates spelling and faction corrections based on contradiction records and writes proposal sheets.
* **Imports/Calls:** `yaml`, `re`
* **Called By:** Continuity audit review loops.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Safe to run interactively.

---

### [chapter_ledger_extractor.py](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/chapter_ledger_extractor.py)
* **File Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/tools/chapter_ledger_extractor.py`
* **Role:** Chronology tracker. Aggregates timestamps, relative day-counts, and chapter sequences into a single master temporal ledger.
* **Imports/Calls:** `re`, `json`
* **Called By:** Standalone timeline compiles.
* **Hardcoded Paths:** None.
* **Safe to Move:** **Yes**
* **Notes:** Resolves calendar alignments (Enkialu day-count vs relative era labels).

---

### [wiki/ Structural Synthesis](file:///home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/wiki/)
* **Directory Path:** `/home/mytruelove/Downloads/obsidianburdenNov25/_mrlore/wiki/`
* **Role:** The synthesis index directory. Aggregates index indices, operational run logs, timelines, location pages, character descriptions, open contradictions, and user canon decisions.
* **Core Components:**
  * `index.md`: Navigation index mapping links, status states, and canon layers.
  * `log.md`: Append-only chronological operation log capturing pipeline runs.
  * `continuity/`: Houses contradiction files (`CONT-*.yaml`).
* **Safe to Move:** **No** (Must match schema directory boundaries).
* **Notes:** Read by querying agents to retrieve authoritative context without having to rescan raw chapters.
