#!/usr/bin/env python3
"""
mrlore_predicate_collision_policy_registry_gate.py — validate backend-owned predicate collision policy.

The registry is review-classification-only. It is not runtime authority, canon
authority, claim authority, or contradiction resolution authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_CLASSES = (
    "MULTI_VALUED_HINT",
    "TRANSIENT_STATE",
    "DURABLE_STATE",
    "EXCLUSIVE_STATE",
    "UNKNOWN_REVIEW",
)
REQUIRED_POLICY_EFFECT = "REVIEW_CLASSIFICATION_ONLY"
CONTRACT = "engain.mrlore_predicate_collision_policy.v1"


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
_SCHEMA_PATH = _HERE / "lexicon" / "predicate_collision_policy.schema.json"
_DEFAULT_POLICY_PATH = _HERE / "lexicon" / "default_predicate_collision_policy.json"


def _default_manifest_path() -> Path:
    candidates = [
        _ENGAIN_ROOT / "tier1" / "engainos" / "assets" / "engain_manifest.json",
        _HERE.parent / "engainos" / "assets" / "engain_manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _resolve_engain_dir(manifest_path: Path) -> Path:
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


def _infer_engain_dir_from_registry_path(registry_path: Path) -> Path:
    resolved = registry_path.resolve()
    for parent in resolved.parents:
        if parent.name == ".engain":
            return parent
    return resolved.parents[2]


def default_registry_path(manifest_path: Path | None = None, engain_dir: Path | None = None) -> Path:
    if engain_dir is None:
        engain_dir = _resolve_engain_dir(manifest_path or _default_manifest_path())
    return engain_dir / "mrlore" / "lexicon" / "predicate_collision_policy.json"


def default_policy_template_path() -> Path:
    return _DEFAULT_POLICY_PATH


def load_predicate_collision_policy(registry_path: Path | str) -> tuple[dict[str, str], dict[str, Any]]:
    """Load a validated registry into predicate -> class form.

    This intentionally requires the gate manifest beside the active .engain tree
    to have passed before a classifier can consume policy behavior.
    """
    registry_file = Path(registry_path).resolve()
    engain_dir = _infer_engain_dir_from_registry_path(registry_file)
    gate_manifest_path = engain_dir / "manifests" / "predicate_collision_policy_registry_gate_manifest.json"
    if not gate_manifest_path.exists():
        raise FileNotFoundError(f"predicate collision policy gate manifest not found: {gate_manifest_path}")
    gate_manifest = json.loads(gate_manifest_path.read_text(encoding="utf-8"))
    if not gate_manifest.get("MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE", False):
        raise ValueError("predicate collision policy gate manifest is not complete")
    if not gate_manifest.get("TEMPORAL_CLASSIFIER_CAN_CONSUME", False):
        raise ValueError("predicate collision policy is not consumable by temporal classifier")
    data = json.loads(registry_file.read_text(encoding="utf-8"))
    predicate_to_class: dict[str, str] = {}
    for class_name, predicates in data.get("predicate_classes", {}).items():
        for predicate in predicates:
            predicate_to_class[str(predicate)] = str(class_name)
    return predicate_to_class, data


def _base_manifest(registry_path: Path, manifest_path: Path) -> dict[str, Any]:
    return {
        "contract": "engain.mrlore_predicate_collision_policy_registry_gate_manifest.v1",
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "registry_path": str(registry_path),
        "schema_path": str(_SCHEMA_PATH),
        "manifest_path": str(manifest_path),
        "MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE": False,
        "REGISTRY_FOUND": registry_path.exists(),
        "REGISTRY_JSON_VALID": False,
        "REGISTRY_SCHEMA_VALID": False,
        "PREDICATES_LOADED": 0,
        "DUPLICATE_PREDICATES_FOUND": False,
        "POLICY_EFFECT": None,
        "RUNTIME_AUTHORITY": None,
        "CANON_AUTHORITY": None,
        "TEMPORAL_CLASSIFIER_CAN_CONSUME": False,
        "CANON_WRITTEN": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
        "errors": [],
        "errors_count": 0,
    }


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest["errors_count"] = len(manifest.get("errors", []))
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _schema_validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["registry root must be a JSON object"]
    expected_keys = {"contract", "policy_effect", "runtime_authority", "canon_authority", "predicate_classes"}
    missing = sorted(expected_keys - set(data))
    extra = sorted(set(data) - expected_keys)
    if missing:
        errors.append(f"registry missing required keys: {', '.join(missing)}")
    if extra:
        errors.append(f"registry has unsupported keys: {', '.join(extra)}")
    if data.get("contract") != CONTRACT:
        errors.append("contract must be engain.mrlore_predicate_collision_policy.v1")
    if data.get("policy_effect") != REQUIRED_POLICY_EFFECT:
        errors.append("policy_effect must be REVIEW_CLASSIFICATION_ONLY")
    if data.get("runtime_authority") is not False:
        errors.append("runtime_authority must be false")
    if data.get("canon_authority") is not False:
        errors.append("canon_authority must be false")
    predicate_classes = data.get("predicate_classes")
    if not isinstance(predicate_classes, dict):
        errors.append("predicate_classes must be an object")
        return errors
    missing_classes = sorted(set(ALLOWED_CLASSES) - set(predicate_classes))
    extra_classes = sorted(set(predicate_classes) - set(ALLOWED_CLASSES))
    if missing_classes:
        errors.append(f"predicate_classes missing allowed classes: {', '.join(missing_classes)}")
    if extra_classes:
        errors.append(f"predicate_classes contains unsupported classes: {', '.join(extra_classes)}")
    for class_name, predicates in predicate_classes.items():
        if class_name not in ALLOWED_CLASSES:
            continue
        if not isinstance(predicates, list):
            errors.append(f"{class_name} must be a list")
            continue
        seen_within: set[str] = set()
        for index, predicate in enumerate(predicates):
            if not isinstance(predicate, str) or not predicate.strip():
                errors.append(f"{class_name}[{index}] predicate name must be a non-empty string")
                continue
            if predicate in seen_within:
                errors.append(f"{class_name} duplicates predicate {predicate!r} within class")
            seen_within.add(predicate)
    return errors


def _duplicate_errors(predicate_classes: dict[str, Any]) -> tuple[bool, list[str]]:
    owner_by_predicate: dict[str, list[str]] = defaultdict(list)
    for class_name, predicates in predicate_classes.items():
        if class_name not in ALLOWED_CLASSES or not isinstance(predicates, list):
            continue
        for predicate in predicates:
            if isinstance(predicate, str) and predicate.strip():
                owner_by_predicate[predicate].append(class_name)
    duplicate_errors: list[str] = []
    for predicate, owners in sorted(owner_by_predicate.items()):
        distinct_owners = sorted(set(owners))
        if len(distinct_owners) > 1:
            duplicate_errors.append(f"predicate {predicate!r} appears in conflicting classes: {', '.join(distinct_owners)}")
    return bool(duplicate_errors), duplicate_errors


def _predicate_count(predicate_classes: dict[str, Any]) -> int:
    predicates: list[str] = []
    for class_name in ALLOWED_CLASSES:
        values = predicate_classes.get(class_name, [])
        if isinstance(values, list):
            predicates.extend(predicate for predicate in values if isinstance(predicate, str) and predicate.strip())
    return len(predicates)


def run_predicate_collision_policy_registry_gate(
    registry_path: Path | str,
    manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    registry_file = Path(registry_path).resolve()
    engain_dir = _infer_engain_dir_from_registry_path(registry_file)
    manifest_file = Path(manifest_path).resolve() if manifest_path else engain_dir / "manifests" / "predicate_collision_policy_registry_gate_manifest.json"
    manifest = _base_manifest(registry_file, manifest_file)

    if not registry_file.exists():
        manifest["errors"].append(f"predicate collision policy registry not found: {registry_file}")
        _write_manifest(manifest_file, manifest)
        return manifest

    try:
        data = json.loads(registry_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        manifest["errors"].append(f"registry JSON invalid: {exc.msg}")
        _write_manifest(manifest_file, manifest)
        return manifest

    manifest["REGISTRY_JSON_VALID"] = True
    if isinstance(data, dict):
        manifest["POLICY_EFFECT"] = data.get("policy_effect")
        manifest["RUNTIME_AUTHORITY"] = data.get("runtime_authority")
        manifest["CANON_AUTHORITY"] = data.get("canon_authority")

    schema_errors = _schema_validate(data)
    predicate_classes = data.get("predicate_classes", {}) if isinstance(data, dict) else {}
    duplicate_found, duplicate_errors = _duplicate_errors(predicate_classes if isinstance(predicate_classes, dict) else {})
    manifest["DUPLICATE_PREDICATES_FOUND"] = duplicate_found
    manifest["PREDICATES_LOADED"] = _predicate_count(predicate_classes if isinstance(predicate_classes, dict) else {})
    manifest["errors"].extend(schema_errors)
    manifest["errors"].extend(duplicate_errors)
    manifest["REGISTRY_SCHEMA_VALID"] = not schema_errors
    manifest["TEMPORAL_CLASSIFIER_CAN_CONSUME"] = (
        manifest["REGISTRY_FOUND"] is True
        and manifest["REGISTRY_JSON_VALID"] is True
        and manifest["REGISTRY_SCHEMA_VALID"] is True
        and not duplicate_found
        and manifest["POLICY_EFFECT"] == REQUIRED_POLICY_EFFECT
        and manifest["RUNTIME_AUTHORITY"] is False
        and manifest["CANON_AUTHORITY"] is False
    )
    manifest["MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE"] = bool(
        manifest["TEMPORAL_CLASSIFIER_CAN_CONSUME"]
    )
    _write_manifest(manifest_file, manifest)
    return manifest


def install_default_predicate_collision_policy(registry_path: Path | str) -> Path:
    registry_file = Path(registry_path).resolve()
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    registry_file.write_text(_DEFAULT_POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return registry_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MrLore predicate collision policy registry.")
    parser.add_argument("--registry", default=None, help="Path to predicate_collision_policy.json.")
    parser.add_argument("--manifest", default=None, help="Path to engain_manifest.json for active .engain discovery.")
    parser.add_argument("--engain-dir", default=None, help="Direct path to vault/.engain.")
    parser.add_argument("--install-default", action="store_true", help="Install repo default registry if the active registry does not exist.")
    args = parser.parse_args()

    try:
        engain_dir = Path(args.engain_dir).resolve() if args.engain_dir else None
        manifest_path = Path(args.manifest) if args.manifest else None
        registry_path = Path(args.registry).resolve() if args.registry else default_registry_path(manifest_path, engain_dir)
        if args.install_default and not registry_path.exists():
            install_default_predicate_collision_policy(registry_path)
        manifest = run_predicate_collision_policy_registry_gate(registry_path)
    except Exception as exc:
        print(f"[PREDICATE_COLLISION_POLICY_GATE] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE={manifest['MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE']}")
    print(f"REGISTRY_FOUND={manifest['REGISTRY_FOUND']}")
    print(f"REGISTRY_JSON_VALID={manifest['REGISTRY_JSON_VALID']}")
    print(f"REGISTRY_SCHEMA_VALID={manifest['REGISTRY_SCHEMA_VALID']}")
    print(f"PREDICATES_LOADED={manifest['PREDICATES_LOADED']}")
    print(f"DUPLICATE_PREDICATES_FOUND={manifest['DUPLICATE_PREDICATES_FOUND']}")
    print(f"POLICY_EFFECT={manifest['POLICY_EFFECT']}")
    print(f"RUNTIME_AUTHORITY={manifest['RUNTIME_AUTHORITY']}")
    print(f"CANON_AUTHORITY={manifest['CANON_AUTHORITY']}")
    print(f"TEMPORAL_CLASSIFIER_CAN_CONSUME={manifest['TEMPORAL_CLASSIFIER_CAN_CONSUME']}")
    print(f"CANON_WRITTEN={manifest['CANON_WRITTEN']}")
    print(f"RUNTIME_TOUCHED={manifest['RUNTIME_TOUCHED']}")
    print(f"GODOT_TOUCHED={manifest['GODOT_TOUCHED']}")
    print(f"ZONJ_COMPILED={manifest['ZONJ_COMPILED']}")
    print(f"errors_count={manifest['errors_count']}")
    print(f"MANIFEST={manifest['manifest_path']}")
    return 0 if manifest["MRLORE_PREDICATE_COLLISION_POLICY_REGISTRY_GATE_COMPLETE"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
