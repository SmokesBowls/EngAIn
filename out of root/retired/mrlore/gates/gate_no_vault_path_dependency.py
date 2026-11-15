# /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/mrlore/gates/gate_no_vault_path_dependency.py

from __future__ import annotations

from typing import Any

from engain_control.gate_result import GateResult


FORBIDDEN_PATH_KEYS = {
    "vault_path",
    "obsidian_path",
    "local_vault_path",
    "absolute_vault_path",
}

FORBIDDEN_PATH_VALUES = {
    "/home/mytruelove",
    "obsidianburdenNov25",
    "Obsidianburdennov25",
}


def _check_value_for_paths(value: Any, found: list[str]) -> None:
    """Recursively check for forbidden path strings."""
    if isinstance(value, str):
        for forbidden in FORBIDDEN_PATH_VALUES:
            if forbidden in value:
                found.append(f"String contains forbidden path: {forbidden}")
    elif isinstance(value, dict):
        for k, v in value.items():
            if k in FORBIDDEN_PATH_KEYS:
                found.append(f"Forbidden key found: {k}")
            _check_value_for_paths(v, found)
    elif isinstance(value, list):
        for item in value:
            _check_value_for_paths(item, found)


def gate_no_vault_path_dependency(packet: dict[str, Any]) -> GateResult:
    """
    MrLore contract supervisor must not require or contain local vault paths.
    Obsidian vault discovery belongs to SOURCE_ADAPTERS/obsidian_adapter later.
    MrLore contract supervisor must be portable for the next user.
    """
    found_issues: list[str] = []
    _check_value_for_paths(packet, found_issues)

    if found_issues:
        return GateResult(
            "gate_no_vault_path_dependency",
            "FALSE",
            f"Hardcoded local paths detected: {found_issues}",
        )

    return GateResult(
        "gate_no_vault_path_dependency",
        "TRUE",
        "No local vault path dependencies found",
    )