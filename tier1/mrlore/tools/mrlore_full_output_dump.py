from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn")
VAULT_ROOT = Path("/home/mytruelove/Downloads/obsidianburdenNov25")
ENGAIN_DIR = VAULT_ROOT / ".engain"

OUTPUT_DIR = ENGAIN_DIR / "mrlore" / "dumps"
MANIFEST_DIR = ENGAIN_DIR / "manifests"

GENERATED_AT = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
SAFE_STAMP = GENERATED_AT.replace(":", "").replace("-", "").replace("+", "_").replace(".", "_")

OUTPUT_PATH = OUTPUT_DIR / f"mrlore_full_output_dump_{SAFE_STAMP}.txt"


MODULE_RUNS = [
    (
        "PRESERVE ENTITY ALLOWLIST REGISTRY GATE",
        "tier1.mrlore.mrlore_preserve_entity_allowlist_registry_gate",
    ),
    (
        "PREDICATE COLLISION POLICY REGISTRY GATE",
        "tier1.mrlore.mrlore_predicate_collision_policy_registry_gate",
    ),
    (
        "TEMPORAL CLAIM CONTEXT ENRICHMENT",
        "tier1.mrlore.mrlore_temporal_claim_context_enrichment",
    ),
    (
        "TEMPORAL COLLISION CLASSIFICATION",
        "tier1.mrlore.mrlore_temporal_collision_classification",
    ),
    (
        "TEMPORAL-AWARE REVIEW QUEUE BUILDER",
        "tier1.mrlore.mrlore_temporal_aware_review_queue_builder",
    ),
    (
        "TEMPORAL-AWARE QUEUE SUMMARY",
        "tier1.mrlore.mrlore_temporal_aware_queue_summary",
    ),
    (
        "TEMPORAL-AWARE REVIEW BY CHAPTER VIEW",
        "tier1.mrlore.mrlore_temporal_aware_review_by_chapter_view",
    ),
    (
        "P3 SEQUENTIAL ENTITY SECOND-PASS QUALITY AUDIT",
        "tier1.mrlore.mrlore_p3_sequential_entity_second_pass_quality_audit",
    ),
    (
        "COMING CALENDAR REGISTRY GATE",
        "tier1.mrlore.mrlore_coming_calendar_registry_gate",
    ),
    (
        "COSMIC YEAR CONTEXT ENRICHMENT",
        "tier1.mrlore.mrlore_cosmic_year_context_enrichment",
    ),
    (
        "ENTITY CANDIDATE QUALITY GATE",
        "tier1.mrlore.mrlore_entity_candidate_quality_gate",
    ),
    (
        "QUALITY-AWARE REVIEW QUEUE BUILDER",
        "tier1.mrlore.mrlore_quality_aware_review_queue_builder",
    ),
    (
        "QUALITY-AWARE QUEUE SUMMARY",
        "tier1.mrlore.mrlore_quality_aware_queue_summary",
    ),
    (
        "REVIEW RAIL HEALTH RUNNER",
        "tier1.mrlore.mrlore_review_rail_health_runner",
    ),
]


MANIFESTS_TO_DUMP = [
    ("FULL HEALTH MANIFEST", "mrlore_review_rail_health_manifest.json"),
    ("ACCEPTED LORE PACKET SCHEMA MANIFEST", "accepted_lore_packet_schema_manifest.json"),
    ("PRESERVE ENTITY ALLOWLIST REGISTRY MANIFEST", "preserve_entity_allowlist_registry_gate_manifest.json"),
    ("PREDICATE COLLISION POLICY REGISTRY MANIFEST", "predicate_collision_policy_registry_gate_manifest.json"),
    ("TEMPORAL CLAIM CONTEXT MANIFEST", "mrlore_temporal_claim_context_manifest.json"),
    ("TEMPORAL COLLISION CLASSIFICATION MANIFEST", "mrlore_temporal_collision_classification_manifest.json"),
    ("TEMPORAL-AWARE REVIEW QUEUE MANIFEST", "mrlore_temporal_aware_review_queue_manifest.json"),
    ("TEMPORAL-AWARE REVIEW QUEUE SUMMARY", "temporal_aware_review_queue_summary.json"),
    ("TEMPORAL-AWARE REVIEW BY CHAPTER MANIFEST", "temporal_aware_review_by_chapter_manifest.json"),
    ("P3 SECOND-PASS QUALITY MANIFEST", "temporal_aware_p3_second_pass_quality_manifest.json"),
    ("COMING CALENDAR REGISTRY MANIFEST", "coming_calendar_registry_gate_manifest.json"),
    ("COSMIC YEAR CONTEXT MANIFEST", "mrlore_cosmic_year_context_manifest.json"),
    ("QUALITY-AWARE REVIEW QUEUE SUMMARY", "quality_aware_review_queue_summary.json"),
    ("PROPOSED CLAIM AUDIT SUMMARY", "proposed_claim_audit_summary.json"),
    ("CONTRADICTION CANDIDATE AUDIT SUMMARY", "mrlore_contradiction_candidate_audit_summary.json"),
    ("CLAIM SHAPE GATE MANIFEST", "claim_shape_gate_manifest.json"),
    ("HIGH CLAIM SCENE REVIEW MANIFEST", "high_claim_scene_review_manifest.json"),
    ("MANUAL REVIEW DECISION SCHEMA MANIFEST", "manual_review_decision_schema_manifest.json"),
    ("MANUAL REVIEW DECISION EXAMPLE MANIFEST", "manual_review_decision_example_manifest.json"),
]


FILES_TO_SUMMARIZE = [
    ("PROPOSED CLAIMS", ENGAIN_DIR / "mrlore" / "claims" / "proposed_claims.jsonl"),
    ("TEMPORAL ENRICHED CLAIMS", ENGAIN_DIR / "mrlore" / "claims" / "proposed_claims.temporal_enriched.jsonl"),
    ("COSMIC ENRICHED CLAIMS", ENGAIN_DIR / "mrlore" / "claims" / "proposed_claims.cosmic_enriched.jsonl"),
    ("ENTITY QUALITY FLAGS", ENGAIN_DIR / "mrlore" / "claims" / "entity_candidate_quality_flags.jsonl"),
    ("CONTRADICTION CANDIDATES", ENGAIN_DIR / "mrlore" / "contradictions" / "contradiction_candidates.jsonl"),
    ("TEMPORAL COLLISION CLASSIFICATIONS", ENGAIN_DIR / "mrlore" / "contradictions" / "temporal_collision_classifications.jsonl"),
    ("TEMPORAL-AWARE REVIEW QUEUE", ENGAIN_DIR / "mrlore" / "review" / "temporal_aware_quality_review_queue.jsonl"),
    ("TEMPORAL-AWARE P3 SECOND-PASS FLAGS", ENGAIN_DIR / "mrlore" / "review" / "temporal_aware_p3_second_pass_quality_flags.jsonl"),
    ("BY-CHAPTER JSON VIEW", ENGAIN_DIR / "mrlore" / "review" / "by_chapter" / "temporal_aware_review_by_chapter.json"),
    ("BY-CHAPTER MARKDOWN VIEW", ENGAIN_DIR / "mrlore" / "review" / "by_chapter" / "temporal_aware_review_by_chapter.md"),
    ("COMING CALENDAR REGISTRY", ENGAIN_DIR / "mrlore" / "timeline" / "coming_calendar.json"),
]


def divider(title: str) -> str:
    return "\n" + "=" * 72 + f"\n{title}\n" + "=" * 72 + "\n"


def module_exists(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def run_module(module_name: str) -> dict:
    if not module_exists(module_name):
        return {
            "module": module_name,
            "skipped": True,
            "reason": "MODULE_NOT_FOUND",
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }

    result = subprocess.run(
        [sys.executable, "-m", module_name],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PYTHONPATH": str(REPO_ROOT), **dict()},
    )

    return {
        "module": module_name,
        "skipped": False,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def read_json_pretty(path: Path) -> str:
    if not path.exists():
        return f"[MISSING] {path}\n"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"[JSON_READ_ERROR] {path}\n{type(exc).__name__}: {exc}\n\nRAW:\n{path.read_text(encoding='utf-8', errors='replace')}\n"

    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def count_lines(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None

    total = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for _ in handle:
            total += 1
    return total


def file_summary(path: Path) -> dict:
    exists = path.exists()
    return {
        "path": str(path),
        "exists": exists,
        "is_file": path.is_file() if exists else False,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
        "line_count": count_lines(path) if exists and path.is_file() else None,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    chunks: list[str] = []

    chunks.append("=" * 72 + "\n")
    chunks.append("MRLORE FULL OUTPUT DUMP\n")
    chunks.append(f"GENERATED_AT={GENERATED_AT}\n")
    chunks.append(f"REPO={REPO_ROOT}\n")
    chunks.append(f"VAULT={VAULT_ROOT}\n")
    chunks.append(f"ENGAIN_DIR={ENGAIN_DIR}\n")
    chunks.append("=" * 72 + "\n")

    chunks.append(divider("0. GENERATOR POLICY"))
    chunks.append("This dump is inspection-only.\n")
    chunks.append("It does not write canon.\n")
    chunks.append("It does not promote claims.\n")
    chunks.append("It does not reject claims.\n")
    chunks.append("It does not resolve contradictions.\n")
    chunks.append("It does not touch runtime.\n")
    chunks.append("It does not touch Godot.\n")
    chunks.append("It does not compile ZONJ.\n")

    chunks.append(divider("1. MODULE RUN OUTPUTS"))
    module_failures = []
    module_skips = []

    for title, module_name in MODULE_RUNS:
        chunks.append(divider(f"RUN: {title}"))
        run = run_module(module_name)

        chunks.append(f"MODULE={run['module']}\n")
        chunks.append(f"SKIPPED={run['skipped']}\n")
        chunks.append(f"RETURNCODE={run['returncode']}\n")

        if run["skipped"]:
            module_skips.append(module_name)
            chunks.append(f"SKIP_REASON={run['reason']}\n")
            continue

        if run["returncode"] != 0:
            module_failures.append(module_name)

        chunks.append("\n--- STDOUT ---\n")
        chunks.append(run["stdout"] or "[NO STDOUT]\n")
        chunks.append("\n--- STDERR ---\n")
        chunks.append(run["stderr"] or "[NO STDERR]\n")

    chunks.append(divider("2. MANIFEST DUMPS"))
    for title, filename in MANIFESTS_TO_DUMP:
        path = MANIFEST_DIR / filename
        chunks.append(divider(title))
        chunks.append(f"PATH={path}\n")
        chunks.append(read_json_pretty(path))

    chunks.append(divider("3. OUTPUT FILE INVENTORY"))
    inventory = [file_summary(path) for _, path in FILES_TO_SUMMARIZE]
    chunks.append(json.dumps(inventory, indent=2, sort_keys=True, ensure_ascii=False))
    chunks.append("\n")

    chunks.append(divider("4. GIT STATUS"))
    git_status = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    chunks.append("--- git status --short ---\n")
    chunks.append(git_status.stdout or "[CLEAN OR NO OUTPUT]\n")
    if git_status.stderr:
        chunks.append("\n--- git status stderr ---\n")
        chunks.append(git_status.stderr)

    chunks.append(divider("5. DUMP GENERATOR SUMMARY"))
    summary = {
        "MRLORE_FULL_OUTPUT_DUMP_COMPLETE": len(module_failures) == 0,
        "GENERATED_AT": GENERATED_AT,
        "REPO": str(REPO_ROOT),
        "VAULT": str(VAULT_ROOT),
        "OUTPUT_PATH": str(OUTPUT_PATH),
        "MODULES_RUN": len(MODULE_RUNS) - len(module_skips),
        "MODULES_SKIPPED": len(module_skips),
        "MODULES_FAILED": len(module_failures),
        "MODULE_SKIP_LIST": module_skips,
        "MODULE_FAILURE_LIST": module_failures,
        "CANON_WRITTEN": False,
        "CLAIMS_PROMOTED": False,
        "CLAIMS_REJECTED": False,
        "CONTRADICTIONS_RESOLVED": False,
        "RUNTIME_TOUCHED": False,
        "GODOT_TOUCHED": False,
        "ZONJ_COMPILED": False,
    }
    chunks.append(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    chunks.append("\n")

    OUTPUT_PATH.write_text("".join(chunks), encoding="utf-8")

    print("MRLORE_FULL_OUTPUT_DUMP_COMPLETE=True" if not module_failures else "MRLORE_FULL_OUTPUT_DUMP_COMPLETE=False")
    print(f"OUTPUT={OUTPUT_PATH}")
    print(f"MODULES_RUN={summary['MODULES_RUN']}")
    print(f"MODULES_SKIPPED={summary['MODULES_SKIPPED']}")
    print(f"MODULES_FAILED={summary['MODULES_FAILED']}")
    print("CANON_WRITTEN=False")
    print("RUNTIME_TOUCHED=False")
    print("GODOT_TOUCHED=False")
    print("ZONJ_COMPILED=False")

    if module_failures:
        print("FAILED_MODULES=" + ",".join(module_failures))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
