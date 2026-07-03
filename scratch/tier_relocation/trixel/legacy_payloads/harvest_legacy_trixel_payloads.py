from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


LEGACY_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/conductor/legacy2beused")
ENGAIN_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")

# This is a Trixel-owned staging target, not conductor ownership.
DEST_ROOT = ENGAIN_ROOT / "trixel" / "1stlane_asset_authority" / "legacy_trixels_payload"

REPORT_DIR = ENGAIN_ROOT / "scratch" / "tier_relocation" / "trixel" / "legacy_payloads"
REPORT_JSON = REPORT_DIR / "LEGACY_TRIXEL_PAYLOAD_HARVEST_REPORT.json"
REPORT_MD = REPORT_DIR / "LEGACY_TRIXEL_PAYLOAD_HARVEST_REPORT.md"


@dataclass(frozen=True)
class GateResult:
    gate_name: str
    passed: bool
    message: str
    details: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file())


def classify_payload(path: Path) -> set[str]:
    """
    Classify likely usable Trixel payloads from old working Trixel folders.

    This is intentionally broad. The purpose is to catch atlas/recipe payloads
    and their immediate visual dependencies before anyone moves legacy2beused.
    """
    full = str(path).lower()
    name = path.name.lower()
    suffix = path.suffix.lower()

    tags: set[str] = set()

    if "atlas" in full or name in {"atlas_meta.json", "atlas_plan.json"}:
        tags.add("atlas_payload")

    if "recipe" in full or "brushrecipe" in full or "trixelcomposer_recipe" in full:
        tags.add("recipe_payload")

    if suffix == ".gpl" or "palette" in full:
        tags.add("palette_payload")

    if "skin" in full or name in {"sheet.png", "skin.xml", "palette.png"}:
        tags.add("skin_payload")

    if suffix in {".ase", ".aseprite"}:
        tags.add("sprite_source_payload")

    if suffix in {".png", ".ico"} and any(token in full for token in ["splash", "icon", "ase16", "ase32", "ase48", "ase64", "doc16", "doc32", "doc48", "doc64"]):
        tags.add("sprite_or_icon_payload")

    if "manifest" in full:
        tags.add("manifest_payload")

    if "provenance" in full:
        tags.add("provenance_payload")

    if suffix in {".json", ".yaml", ".yml", ".xml", ".toml"} and any(
        token in full
        for token in ["trixel", "libra", "libresprite", "atlas", "recipe", "skin", "palette", "sprite"]
    ):
        tags.add("config_payload")

    return tags


def should_copy(tags: set[str]) -> bool:
    # Minimum user demand: atlas and recipes. Also copy their likely immediate dependencies.
    copy_tags = {
        "atlas_payload",
        "recipe_payload",
        "palette_payload",
        "skin_payload",
        "sprite_source_payload",
        "manifest_payload",
        "provenance_payload",
        "config_payload",
    }
    return bool(tags & copy_tags)


def safe_copy(src: Path, dest_root: Path) -> Path:
    rel = src.relative_to(LEGACY_ROOT)
    dest = dest_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def gate_legacy_root_exists() -> GateResult:
    return GateResult(
        gate_name="LEGACY_ROOT_EXISTS",
        passed=LEGACY_ROOT.exists() and LEGACY_ROOT.is_dir(),
        message="legacy2beused exists and can be harvested." if LEGACY_ROOT.exists() else "legacy2beused is missing.",
        details={"legacy_root": str(LEGACY_ROOT)},
    )


def gate_atlas_or_recipe_found(records: list[dict[str, Any]]) -> GateResult:
    atlas_count = sum(1 for r in records if "atlas_payload" in r["tags"])
    recipe_count = sum(1 for r in records if "recipe_payload" in r["tags"])

    return GateResult(
        gate_name="ATLAS_OR_RECIPE_FOUND",
        passed=(atlas_count + recipe_count) > 0,
        message="Found atlas/recipe payload candidates." if (atlas_count + recipe_count) > 0 else "No atlas/recipe payload candidates found.",
        details={"atlas_count": atlas_count, "recipe_count": recipe_count},
    )


def gate_copy_mode_respected(copy_enabled: bool, copied_count: int) -> GateResult:
    if copy_enabled:
        passed = copied_count > 0
        message = "Copy mode enabled and payload files were copied." if passed else "Copy mode enabled but no files were copied."
    else:
        passed = copied_count == 0
        message = "Dry run mode respected. No files copied."

    return GateResult(
        gate_name="COPY_MODE_RESPECTED",
        passed=passed,
        message=message,
        details={"copy_enabled": copy_enabled, "copied_count": copied_count},
    )


def gate_authority_preserved() -> GateResult:
    return GateResult(
        gate_name="AUTHORITY_PRESERVED",
        passed=True,
        message="Harvest target is Trixel 1stlane asset authority; legacy source remains unmoved.",
        details={
            "source_status": "WORKING_TRIXEL_PAYLOAD_SOURCE",
            "tier_authority": "TRIXEL_TIER1",
            "lane": "trixel_1stlane_asset_authority",
            "legacy_root_moved": False,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Actually copy harvested payloads into the Trixel 1stlane staging target.",
    )
    args = parser.parse_args()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    files = iter_files(LEGACY_ROOT)

    records: list[dict[str, Any]] = []
    copied_records: list[dict[str, Any]] = []

    for path in files:
        tags = sorted(classify_payload(path))
        if not tags:
            continue

        record: dict[str, Any] = {
            "source_path": str(path),
            "relative_path": str(path.relative_to(LEGACY_ROOT)),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "tags": tags,
            "copy_candidate": should_copy(set(tags)),
            "copied_to": None,
        }

        if args.copy and record["copy_candidate"]:
            copied_path = safe_copy(path, DEST_ROOT)
            record["copied_to"] = str(copied_path)
            copied_records.append(record)

        records.append(record)

    tag_counts: dict[str, int] = {}
    for record in records:
        for tag in record["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    gates = [
        gate_legacy_root_exists(),
        gate_atlas_or_recipe_found(records),
        gate_copy_mode_respected(args.copy, len(copied_records)),
        gate_authority_preserved(),
    ]

    all_gates = all(g.passed for g in gates)

    report = {
        "report_id": "LEGACY_TRIXEL_PAYLOAD_HARVEST",
        "source_root": str(LEGACY_ROOT),
        "destination_root": str(DEST_ROOT),
        "copy_enabled": args.copy,
        "legacy_root_moved": False,
        "authority": {
            "tier": "TRIXEL_TIER1",
            "lane": "trixel_1stlane_asset_authority",
            "source_status": "WORKING_TRIXEL_PAYLOAD_SOURCE",
        },
        "summary": {
            "total_files_scanned": len(files),
            "payload_candidates": len(records),
            "copy_candidates": sum(1 for r in records if r["copy_candidate"]),
            "copied_count": len(copied_records),
            "tag_counts": tag_counts,
        },
        "records": records,
        "gates": [asdict(g) for g in gates],
        "acceptance": "ACCEPTED" if all_gates else "REJECTED",
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# LEGACY TRIXEL PAYLOAD HARVEST REPORT",
        "",
        f"SOURCE_ROOT: `{LEGACY_ROOT}`",
        f"DESTINATION_ROOT: `{DEST_ROOT}`",
        f"COPY_ENABLED: `{args.copy}`",
        "LEGACY_ROOT_MOVED: `False`",
        "AUTHORITY: `TRIXEL_TIER1`",
        "LANE: `trixel_1stlane_asset_authority`",
        "",
        "## Summary",
        "",
        f"- total_files_scanned: {len(files)}",
        f"- payload_candidates: {len(records)}",
        f"- copy_candidates: {sum(1 for r in records if r['copy_candidate'])}",
        f"- copied_count: {len(copied_records)}",
        "",
        "## Tag Counts",
    ]

    for key in sorted(tag_counts):
        lines.append(f"- {key}: {tag_counts[key]}")

    lines.extend([
        "",
        "## Gates",
    ])

    for gate in gates:
        state = "TRUE" if gate.passed else "FALSE"
        lines.append(f"- [{state}] {gate.gate_name} — {gate.message}")

    lines.extend([
        "",
        "## Payload Candidates",
        "",
    ])

    for record in records[:300]:
        copied_to = record["copied_to"] or "NOT_COPIED"
        lines.append(
            f"- `{record['relative_path']}` tags={record['tags']} copied_to=`{copied_to}`"
        )

    if len(records) > 300:
        lines.append(f"- ... truncated in markdown; full list in `{REPORT_JSON}`")

    lines.extend([
        "",
        "## Verdict",
        "",
        "```text",
        "legacy2beused is a working Trixel payload source.",
        "It must not be moved until atlas/recipe/palette/skin payloads are harvested or remade.",
        "This report preserves source hashes and records what was copied.",
        "```",
        "",
        f"ACCEPTANCE: {report['acceptance']}",
        "",
    ])

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"[LEGACY_TRIXEL_PAYLOAD_HARVEST][REPORT_JSON] {REPORT_JSON}")
    print(f"[LEGACY_TRIXEL_PAYLOAD_HARVEST][REPORT_MD] {REPORT_MD}")

    for gate in gates:
        state = "PASS" if gate.passed else "FAIL"
        print(f"[LEGACY_TRIXEL_PAYLOAD_HARVEST][{gate.gate_name}] {state}: {gate.message}")

    print(f"[LEGACY_TRIXEL_PAYLOAD_HARVEST][ALL_GATES] {'true' if all_gates else 'false'}")

    return 0 if all_gates else 1


if __name__ == "__main__":
    raise SystemExit(main())
