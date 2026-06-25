from __future__ import annotations

from pathlib import Path
from typing import Any

from engain_control.gate_result import GateResult


ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

ACTIVE_ENGIONALITY_PATHS = [
    ENGAIN_ROOT / "ENGIONALITY" / "gates",
    ENGAIN_ROOT / "ENGIONALITY" / "engionality_control_center.py",
]


def gate_no_legacy_imports(packet: dict[str, Any]) -> GateResult:
    forbidden_terms = [
        "engionality_legacy",
        "ENGIONALITY.engionality_legacy",
    ]

    checked_files: list[str] = []
    violations: list[str] = []

    for active_path in ACTIVE_ENGIONALITY_PATHS:
        if active_path.is_dir():
            files = sorted(active_path.rglob("*.py"))
        elif active_path.is_file():
            files = [active_path]
        else:
            continue

        for file_path in files:
            checked_files.append(str(file_path.relative_to(ENGAIN_ROOT)))
            text = file_path.read_text(encoding="utf-8", errors="replace")

            for term in forbidden_terms:
                if term in text:
                    violations.append(
                        f"{file_path.relative_to(ENGAIN_ROOT)} contains {term}"
                    )

    if violations:
        return GateResult(
            "gate_no_legacy_imports",
            "FALSE",
            f"Legacy quarantine import detected: {violations}",
        )

    return GateResult(
        "gate_no_legacy_imports",
        "TRUE",
        (
            "No active Engionality gate/control file imports legacy quarantine. "
            f"Checked {len(checked_files)} files."
        ),
    )
