"""EngAInOS AP rule registry loader.

Structural loader for ZON AP profile ap/0.1 rule files. This module only
parses and validates rule artifacts; it does not evaluate predicates, execute
effects, import authority_gate, or mutate runtime state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


VALID_SCOPES = {"open_loop", "canon", "style", "log"}
VALID_STATUSES = {"active", "disabled"}
REQUIRED_METADATA = ("id", "scope", "status", "priority")
REQUIRED_BLOCKS = ("requires", "read_set", "write_set", "effects")
PROFILE = "ap/0.1"


class APRuleLoadError(ValueError):
    """Raised when an AP rule file or registry is invalid."""


def default_registry_root() -> Path:
    """Return the EngAInOS AP rules root."""
    return Path(__file__).resolve().parents[1] / "rules"


def load(registry: str, registry_root: Optional[Path | str] = None) -> Dict[str, Any]:
    """Load and structurally validate a named AP rule registry.

    Args:
        registry: Registry directory name, for example ``runtime_mutation``.
        registry_root: Optional AP rules root override for tests/tools.

    Returns:
        Dict with ``registry``, ``active_rules``, ``audit_rules``, and ``errors``.

    Raises:
        APRuleLoadError: if the registry path, a rule file, or registry-level
            invariants are invalid.
    """
    root = Path(registry_root) if registry_root is not None else default_registry_root()
    registry_path = root / registry
    if not registry_path.is_dir():
        raise APRuleLoadError(f"AP registry not found: {registry_path}")

    audit_rules = [_parse_rule_file(path) for path in sorted(registry_path.glob("*.zon"))]
    _validate_unique_ids(audit_rules)

    active_rules = [
        rule
        for rule in audit_rules
        if rule["status"] == "active" and rule["scope"] == "canon"
    ]
    active_rules.sort(key=lambda rule: (-rule["priority"], rule["id"]))

    return {
        "registry": registry,
        "active_rules": active_rules,
        "audit_rules": audit_rules,
        "errors": [],
    }


def _parse_rule_file(path: Path) -> Dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    first_index, header = _first_non_empty_line(lines, path)
    profile, caps, guard = _parse_header(header, path)

    metadata: Dict[str, str] = {}
    metadata_seen: Dict[str, int] = {}
    blocks: Dict[str, List[str]] = {name: [] for name in REQUIRED_BLOCKS}
    block_seen: Dict[str, int] = {}
    current_block: Optional[str] = None

    for line_number, raw_line in enumerate(lines[first_index + 1 :], start=first_index + 2):
        line = raw_line.strip()
        if not line:
            continue

        if current_block is not None:
            if line == "=end":
                current_block = None
                continue
            blocks[current_block].append(_parse_block_item(line))
            continue

        if line.startswith("@"):
            key, value = _parse_metadata_line(line, path, line_number)
            if key in metadata_seen:
                raise APRuleLoadError(
                    f"Duplicate @{key} in {path} at line {line_number}; "
                    f"first seen at line {metadata_seen[key]}"
                )
            metadata_seen[key] = line_number
            metadata[key] = value
            continue

        if line.startswith("="):
            block_name = line[1:]
            if block_name == "end":
                raise APRuleLoadError(f"Unexpected =end in {path} at line {line_number}")
            if block_name not in REQUIRED_BLOCKS:
                raise APRuleLoadError(
                    f"Unknown block ={block_name} in {path} at line {line_number}"
                )
            if block_name in block_seen:
                raise APRuleLoadError(
                    f"Duplicate ={block_name} block in {path} at line {line_number}; "
                    f"first seen at line {block_seen[block_name]}"
                )
            block_seen[block_name] = line_number
            current_block = block_name
            continue

        raise APRuleLoadError(f"Unexpected content in {path} at line {line_number}: {line}")

    if current_block is not None:
        raise APRuleLoadError(f"Block ={current_block} missing =end in {path}")

    _validate_required_metadata(metadata, path)
    _validate_required_blocks(block_seen, path)

    priority = _parse_priority(metadata["priority"], path)
    scope = metadata["scope"]
    status = metadata["status"]

    if scope not in VALID_SCOPES:
        raise APRuleLoadError(f"Invalid @scope in {path}: {scope}")
    if status not in VALID_STATUSES:
        raise APRuleLoadError(f"Invalid @status in {path}: {status}")

    _validate_scope_blocks(scope, blocks, path)

    return {
        "id": metadata["id"],
        "scope": scope,
        "status": status,
        "priority": priority,
        "requires": blocks["requires"],
        "read_set": blocks["read_set"],
        "write_set": blocks["write_set"],
        "effects": blocks["effects"],
        "source_path": _display_path(path),
        "profile": profile,
        "caps": caps,
        "guard": guard,
    }


def _first_non_empty_line(lines: List[str], path: Path) -> Tuple[int, str]:
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            return index, stripped
    raise APRuleLoadError(f"Empty AP rule file: {path}")


def _parse_header(header: str, path: Path) -> Tuple[str, Optional[str], Optional[str]]:
    parts = [part.strip() for part in header.split(";")]
    if not parts or parts[0] != f"#ZON {PROFILE}":
        raise APRuleLoadError(f"Invalid or missing AP profile header in {path}: {header}")

    caps: Optional[str] = None
    guard: Optional[str] = None
    for part in parts[1:]:
        if not part:
            continue
        if "=" not in part:
            raise APRuleLoadError(f"Invalid header metadata in {path}: {part}")
        key, value = [item.strip() for item in part.split("=", 1)]
        if key == "caps":
            caps = value
        elif key == "guard":
            guard = value
    return PROFILE, caps, guard


def _parse_metadata_line(line: str, path: Path, line_number: int) -> Tuple[str, str]:
    if ":" not in line:
        raise APRuleLoadError(f"Malformed metadata in {path} at line {line_number}: {line}")
    key, value = line[1:].split(":", 1)
    key = key.strip()
    value = value.strip()
    if not key or not value:
        raise APRuleLoadError(f"Malformed metadata in {path} at line {line_number}: {line}")
    return key, value


def _parse_block_item(line: str) -> str:
    if line.startswith("- "):
        return line[2:].strip()
    return line.strip()


def _validate_required_metadata(metadata: Dict[str, str], path: Path) -> None:
    missing = [key for key in REQUIRED_METADATA if key not in metadata]
    if missing:
        raise APRuleLoadError(f"Missing required metadata in {path}: {', '.join('@' + m for m in missing)}")


def _validate_required_blocks(block_seen: Dict[str, int], path: Path) -> None:
    missing = [name for name in REQUIRED_BLOCKS if name not in block_seen]
    if missing:
        raise APRuleLoadError(f"Missing required blocks in {path}: {', '.join('=' + m for m in missing)}")


def _parse_priority(value: str, path: Path) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise APRuleLoadError(f"Invalid @priority in {path}: {value}") from exc


def _validate_scope_blocks(scope: str, blocks: Dict[str, List[str]], path: Path) -> None:
    if scope == "style" and (blocks["write_set"] or blocks["effects"]):
        raise APRuleLoadError(
            f"Invalid style rule in {path}: write_set and effects must be empty"
        )
    if scope == "log" and blocks["effects"]:
        raise APRuleLoadError(f"Invalid log rule in {path}: effects must be empty")


def _validate_unique_ids(rules: List[Dict[str, Any]]) -> None:
    seen: Dict[str, str] = {}
    for rule in rules:
        rule_id = rule["id"]
        source_path = rule["source_path"]
        if rule_id in seen:
            raise APRuleLoadError(
                f"Duplicate AP rule id {rule_id}: {seen[rule_id]} and {source_path}"
            )
        seen[rule_id] = source_path


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    import json
    import sys

    registry_name = sys.argv[1] if len(sys.argv) > 1 else "runtime_mutation"
    print(json.dumps(load(registry_name), indent=2, sort_keys=True))
