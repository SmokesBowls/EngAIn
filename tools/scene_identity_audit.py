#!/usr/bin/env python3
# tools/scene_identity_audit.py
#
# Standalone scene identity audit tool.
# Scans a vault or folder for scene files and reports identity drift.
#
# AUTHORITY:
#   Read-only. Never modifies files. Never renames anything.
#   Reports drift so YOU decide what to fix.
#   Uses mettaext.scene_identity for ALL identity logic.
#
# USAGE:
#   python3 tools/scene_identity_audit.py <path>          # scan folder
#   python3 tools/scene_identity_audit.py <path> --json   # JSON report
#   python3 tools/scene_identity_audit.py <path> --drift-only  # only show problems
#   python3 tools/scene_identity_audit.py <file>          # audit a single file

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Single import — all identity logic lives here, nowhere else
# ---------------------------------------------------------------------------

from mettaext.scene_identity import (
    _STRIP_EXTENSIONS,          # reuse the resolver's own extension list
    detect_identity_drift,
    to_canonical_scene_id,
    IdentityDrift,
)

# Derive the file-discovery set directly from the resolver's constant
# so they can never drift apart.
SCENE_FILE_EXTENSIONS = frozenset(_STRIP_EXTENSIONS)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def is_scene_file(path: Path) -> bool:
    """Return True if the file looks like a scene or draft file."""
    name = path.name.lower()
    return any(name.endswith(ext) for ext in SCENE_FILE_EXTENSIONS)


IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "compiled",
    "ingested",
    "loaded",
    "game_scenes",
    "game_scenes_unified",
    "docs",
    "files",
    "zw_repo-master",
}


def discover_scene_files(root: Path) -> list[Path]:
    """Recursively find all scene-like files under root."""
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in IGNORE_DIRS
        ]
        for fname in sorted(filenames):
            p = Path(dirpath) / fname
            if is_scene_file(p):
                found.append(p)
    return sorted(found)


# ---------------------------------------------------------------------------
# Scene ID extraction — try to read @id or scene_id from JSON files
# ---------------------------------------------------------------------------

def extract_scene_id_from_file(path: Path) -> str | None:
    """
    Attempt to read the scene ID declared inside the file.
    Returns None if the file isn't JSON or has no recognizable ID field.
    """
    if ".json" not in path.suffixes:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        for key in ("@id", "scene_id", "id"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Audit result
# ---------------------------------------------------------------------------

@dataclass
class AuditResult:
    path: str
    filename: str
    declared_scene_id: str | None
    filename_canonical: str
    filename_drift: bool
    filename_drift_reasons: list[str]
    id_drift: bool
    id_drift_reasons: list[str]

    @property
    def has_any_drift(self) -> bool:
        return self.filename_drift or self.id_drift

    def to_dict(self) -> dict:
        return asdict(self)


def audit_file(path: Path, base_root: Path | None = None) -> AuditResult:
    display_path = str(path.relative_to(base_root)) if base_root else str(path)
    filename = path.name

    # Audit filename — delegates entirely to the resolver
    fn_drift = detect_identity_drift(filename)

    # Audit declared scene ID (if JSON)
    declared_id = extract_scene_id_from_file(path)
    id_drift_obj: IdentityDrift | None = None
    if declared_id:
        id_drift_obj = detect_identity_drift(declared_id)

    return AuditResult(
        path=display_path,
        filename=filename,
        declared_scene_id=declared_id,
        filename_canonical=fn_drift.canonical,
        filename_drift=fn_drift.has_drift,
        filename_drift_reasons=fn_drift.drift_reasons,
        id_drift=bool(id_drift_obj and id_drift_obj.has_drift),
        id_drift_reasons=(id_drift_obj.drift_reasons if id_drift_obj else []),
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

RESET  = "\033[0m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"


def _c(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text


def print_text_report(results: list[AuditResult], drift_only: bool = False) -> None:
    total = len(results)
    drifted = [r for r in results if r.has_any_drift]
    clean   = [r for r in results if not r.has_any_drift]

    print(_c(f"\n{'='*60}", BOLD))
    print(_c("  SCENE IDENTITY AUDIT REPORT", BOLD))
    print(_c(f"{'='*60}", BOLD))
    print(f"  Files scanned:  {total}")
    print(f"  Clean:          {_c(str(len(clean)), GREEN)}")
    print(f"  Drifted:        {_c(str(len(drifted)), RED if drifted else GREEN)}")
    print()

    to_show = drifted if drift_only else results
    for r in to_show:
        if not r.has_any_drift:
            print(_c(f"  OK       {r.path}", GREEN))
            continue

        print(_c(f"  DRIFT    {r.path}", YELLOW))

        if r.filename_drift:
            print(f"           filename  : {r.filename}")
            print(f"           canonical : {_c(r.filename_canonical, CYAN)}")
            for reason in r.filename_drift_reasons:
                print(f"             • {reason}")

        if r.declared_scene_id:
            if r.id_drift:
                print(f"           @id       : {_c(r.declared_scene_id, RED)} (has drift)")
                for reason in r.id_drift_reasons:
                    print(f"             • {reason}")
            else:
                print(f"           @id       : {_c(r.declared_scene_id, GREEN)} (OK)")

        print()

    if not drifted:
        print(_c("  All files are identity-clean.\n", GREEN))


def print_json_report(results: list[AuditResult]) -> None:
    data = {
        "total": len(results),
        "clean": sum(1 for r in results if not r.has_any_drift),
        "drifted": sum(1 for r in results if r.has_any_drift),
        "results": [r.to_dict() for r in results],
    }
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scene identity audit tool. Read-only — never modifies files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/scene_identity_audit.py vault/scenes/
  python3 tools/scene_identity_audit.py vault/drafts/ --drift-only
  python3 tools/scene_identity_audit.py my_scene.zonj.json
  python3 tools/scene_identity_audit.py vault/ --json > report.json
        """,
    )
    parser.add_argument("path", help="File or folder to audit")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--drift-only", action="store_true", help="Only show drifted files")
    args = parser.parse_args()

    target = Path(args.path).expanduser().resolve()

    if not target.exists():
        print(f"ERROR: Path does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    if target.is_file():
        paths = [target]
        base_root = target.parent
    else:
        paths = discover_scene_files(target)
        base_root = target

    if not paths:
        print(f"No scene files found under: {target}", file=sys.stderr)
        sys.exit(0)

    results = [audit_file(p, base_root) for p in paths]

    if args.json:
        print_json_report(results)
    else:
        print_text_report(results, drift_only=args.drift_only)

    if any(r.has_any_drift for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
