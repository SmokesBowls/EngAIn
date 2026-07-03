#!/usr/bin/env python3
"""
mrlore_preserve_entity_allowlist_registry_gate.py — validate narrative-owned preserve entity allowlist.

PURPOSE:
    Validate the narrative-owned registry of lore terms that should be preserved
    from entity noise filtering. This gate only proves that the registry is
    readable, schema-valid, authority-safe, and safe for the quality gate to
    consume. It does not accept canon and does not mutate claims.

INPUT:
    vault/.engain/mrlore/lexicon/preserve_entity_allowlist.json

OUTPUT:
    vault/.engain/manifests/preserve_entity_allowlist_registry_gate_manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ALLOWED_TERM_TYPES = {
    "character",
    "faction",
    "species",
    "place",
    "artifact",
    "title",
    "organization",
    "event",
    "concept",
    "unknown_lore_entity",
}
ALLOWED_STATUSES = {"ACTIVE", "PROPOSED", "DEPRECATED"}
CONSUMABLE_STATUSES = {"ACTIVE", "PROPOSED"}
EXPECTED_CONTRACT = "engain.mrlore_preserve_entity_allowlist.v1"
EXPECTED_REGISTRY_TYPE = "PRESERVE_ENTITY_ALLOWLIST"
EXPECTED_AUTHORITY_OWNER = "NARRATIVE_TEAM"


class PreserveEntityAllowlistRegistryError(RuntimeError):
    """Raised when the preserve entity allowlist registry is not consumable."""


def _find_engain_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(8):
        if (cur / "tier1").exists() and (cur / "tier2").exists() and (cur / "tier3").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return start.resolve()


_HERE = Path(__file__).resolve().parent
_ENGAIN_ROOT = _find_engain_root(_HERE)
_DEFAULT_SCHEMA_PATH = _HERE / "lexicon" / "preserve_entity_allowlist.schema.json"


def _default_manifest_path() -> Path:
    candidates = [
        _ENGAIN_ROOT / "tier1" / "engainos" / "assets" / "engain_manifest.json",
        _HERE.parent / "engainos" / "assets" / "engain_manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _resolve_engain_dir_from_manifest(manifest_path: Path) -> Path:
    if not manifest_path.exists():
        raise FileNotFoundError(f"engain_manifest.json not found: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = data.get("output_dir")
    active_vault = data.get("active_vault")
    if output_dir:
        return Path(output_dir)
    if active_vault:
        return Path(active_vault) / ".engain"
    raise ValueError("engain_manifest.json has no output_dir or active_vault")


def default_registry_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir_from_manifest(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "lexicon" / "preserve_entity_allowlist.json"


def _infer_engain_dir_from_registry_path(registry_path: Path) -> Path:
    resolved = registry_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def _default_gate_manifest_path(registry_path: Path) -> Path:
    return _infer_engain_dir_from_registry_path(registry_path) / "manifests" / "preserve_entity_allowlist_registry_gate_manifest.json"


def _normalize_term(term: Any) -> str:
    return " ".join(str(term or "").strip().split()).lower()


def _load_schema(schema_path: Path = _DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _schema_errors(registry: Any, schema_path: Path = _DEFAULT_SCHEMA_PATH) -> list[str]:
    schema = _load_schema(schema_path)
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(registry), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"schema violation at {path}: {error.message}")
    return errors


def _semantic_errors(registry: Any) -> tuple[list[str], list[str], bool]:
    if not isinstance(registry, dict):
        return ["registry must be a JSON object"], [], False

    errors: list[str] = []
    duplicates: list[str] = []

    if registry.get("contract") != EXPECTED_CONTRACT:
        errors.append(f"contract must be {EXPECTED_CONTRACT}")
    if registry.get("registry_type") != EXPECTED_REGISTRY_TYPE:
        errors.append(f"registry_type must be {EXPECTED_REGISTRY_TYPE}")
    if registry.get("authority_owner") != EXPECTED_AUTHORITY_OWNER:
        errors.append(f"authority_owner must be {EXPECTED_AUTHORITY_OWNER}")
    if registry.get("runtime_authority") is not False:
        errors.append("runtime_authority must be false")
    if registry.get("canon_authority") is not False:
        errors.append("canon_authority must be false")

    terms = registry.get("terms")
    if not isinstance(terms, list):
        return errors + ["terms must be an array"], duplicates, False

    normalized_terms: list[str] = []
    for index, entry in enumerate(terms):
        if not isinstance(entry, dict):
            errors.append(f"terms[{index}] must be an object")
            continue
        term = entry.get("term")
        normalized = _normalize_term(term)
        if not normalized:
            errors.append(f"blank term at terms[{index}]")
        else:
            normalized_terms.append(normalized)
        term_type = entry.get("term_type")
        if term_type not in ALLOWED_TERM_TYPES:
            errors.append(f"invalid term_type at terms[{index}]: {term_type}")
        status = entry.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"invalid status at terms[{index}]: {status}")

    counts = Counter(normalized_terms)
    duplicates = sorted(term for term, count in counts.items() if count > 1)
    for term in duplicates:
        errors.append(f"duplicate term: {term}")
    return errors, duplicates, bool(duplicates)


def _manifest_base(registry_path: Path, manifest_path: Path) -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_preserve_entity_allowlist_registry_gate_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(registry_path),
        "schema_path": str(_DEFAULT_SCHEMA_PATH),
        "manifest_path": str(manifest_path),
        "MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE": False,
        "REGISTRY_FOUND": registry_path.exists(),
        "REGISTRY_JSON_VALID": False,
        "REGISTRY_SCHEMA_VALID": False,
        "TERMS_LOADED": 0,
        "CONSUMABLE_TERMS_LOADED": 0,
        "DUPLICATE_TERMS_FOUND": False,
        "DUPLICATE_TERMS": [],
        "RUNTIME_AUTHORITY": None,
        "CANON_AUTHORITY": None,
        "QUALITY_GATE_CAN_CONSUME": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "CLAIMS_REJECTED": False,
        "CLAIMS_PROMOTED": False,
        "errors": [],
    }


def run_preserve_entity_allowlist_registry_gate(registry_path: Path | str) -> dict[str, Any]:
    registry_file = Path(registry_path).resolve()
    manifest_path = _default_gate_manifest_path(registry_file)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = _manifest_base(registry_file, manifest_path)

    if not registry_file.exists():
        manifest["errors"] = [f"registry not found: {registry_file}"]
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    try:
        registry = json.loads(registry_file.read_text(encoding="utf-8"))
        manifest["REGISTRY_JSON_VALID"] = True
    except json.JSONDecodeError as exc:
        manifest["errors"] = [f"invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"]
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return manifest

    schema_errors = _schema_errors(registry)
    semantic_errors, duplicate_terms, duplicates_found = _semantic_errors(registry)
    all_errors = schema_errors + semantic_errors

    terms = registry.get("terms") if isinstance(registry, dict) else []
    terms_list = terms if isinstance(terms, list) else []
    consumable_terms = []
    for entry in terms_list:
        if not isinstance(entry, dict):
            continue
        term = entry.get("term")
        if isinstance(term, str) and term.strip() and entry.get("status") in CONSUMABLE_STATUSES:
            consumable_terms.append(entry)

    manifest.update(
        {
            "REGISTRY_SCHEMA_VALID": not all_errors,
            "TERMS_LOADED": len(terms_list),
            "CONSUMABLE_TERMS_LOADED": len(consumable_terms),
            "DUPLICATE_TERMS_FOUND": duplicates_found,
            "DUPLICATE_TERMS": duplicate_terms,
            "RUNTIME_AUTHORITY": registry.get("runtime_authority") if isinstance(registry, dict) else None,
            "CANON_AUTHORITY": registry.get("canon_authority") if isinstance(registry, dict) else None,
            "errors": all_errors,
        }
    )
    complete = bool(manifest["REGISTRY_JSON_VALID"] and manifest["REGISTRY_SCHEMA_VALID"] and not duplicates_found)
    manifest["MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE"] = complete
    manifest["QUALITY_GATE_CAN_CONSUME"] = complete

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def load_consumable_preserve_terms(registry_path: Path | str, gate_manifest_path: Path | str | None = None) -> set[str]:
    registry_file = Path(registry_path).resolve()
    manifest_file = Path(gate_manifest_path).resolve() if gate_manifest_path else _default_gate_manifest_path(registry_file)
    if not manifest_file.exists():
        raise PreserveEntityAllowlistRegistryError(
            "Preserve entity allowlist registry gate manifest is missing. "
            "Run: PYTHONPATH=. python -m tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate"
        )
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreserveEntityAllowlistRegistryError(f"Preserve entity allowlist registry gate manifest is invalid JSON: {exc.msg}") from exc
    if manifest.get("registry_path") != str(registry_file):
        raise PreserveEntityAllowlistRegistryError("Preserve entity allowlist registry gate manifest does not match active registry path")
    if manifest.get("QUALITY_GATE_CAN_CONSUME") is not True:
        raise PreserveEntityAllowlistRegistryError("Preserve entity allowlist registry gate did not authorize quality-gate consumption")

    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    terms: set[str] = set()
    for entry in registry.get("terms", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("status") not in CONSUMABLE_STATUSES:
            continue
        term = entry.get("term")
        if isinstance(term, str) and term.strip():
            terms.add(" ".join(term.strip().split()))
    return terms


def main() -> int:
    parser = argparse.ArgumentParser(description="MrLore preserve entity allowlist registry gate.")
    parser.add_argument("--registry", default=None, help="Path to preserve_entity_allowlist.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    args = parser.parse_args()

    try:
        manifest_path = Path(args.manifest) if args.manifest else None
        engain_dir = Path(args.engain_dir) if args.engain_dir else None
        registry_path = Path(args.registry) if args.registry else default_registry_path(manifest_path, engain_dir)
        manifest = run_preserve_entity_allowlist_registry_gate(registry_path)
    except Exception as exc:
        print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] "
        f"MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE={manifest['MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE']}"
    )
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] REGISTRY_FOUND={manifest['REGISTRY_FOUND']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] REGISTRY_JSON_VALID={manifest['REGISTRY_JSON_VALID']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] REGISTRY_SCHEMA_VALID={manifest['REGISTRY_SCHEMA_VALID']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] TERMS_LOADED={manifest['TERMS_LOADED']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] DUPLICATE_TERMS_FOUND={manifest['DUPLICATE_TERMS_FOUND']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] RUNTIME_AUTHORITY={manifest['RUNTIME_AUTHORITY']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] CANON_AUTHORITY={manifest['CANON_AUTHORITY']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] QUALITY_GATE_CAN_CONSUME={manifest['QUALITY_GATE_CAN_CONSUME']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] MANIFEST={manifest['manifest_path']}")
    for error in manifest.get("errors", [])[:20]:
        print(f"[PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE] ERROR: {error}")
    return 0 if manifest["MRLORE_PRESERVE_ENTITY_ALLOWLIST_REGISTRY_GATE_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
