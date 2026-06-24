# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING
# ---------------------------------------------------------------------------
# This file calls: obsidian/*.zw (source lore files)
#                  manifests/world_rules.json (target — enriched in place)
# This file is called by: start_button.py (step 2 compile pass)
#                          manually via: python3 mettaext/zw_world_rules_compiler.py
# ---------------------------------------------------------------------------
"""
zw_world_rules_compiler.py — ZW Obsidian → world_rules.json Compiler

Reads all .zw files from the obsidian/ directory and enriches world_rules.json
with canonical lore data: zw_tags, refined entity_type, and ap_constraints.

Replaces manual editing of world_rules.json for entities that have .zw coverage.
Entities without .zw coverage are left unchanged (hand-maintained entries survive).

Three output streams:
  world_rules.json     — enriched entity ontology (primary output)
  ap_rules.json        — compiled from ZW_WORLD_RULE blocks
  event_seeds.json     — compiled from ZW_EVENT_SEED blocks

Authority contract:
  ZW_CHARACTER_LAW + ZW_SPECIES_ORIGIN + ZW_CANON → world_rules.json
  ZW_WORLD_RULE                                    → ap_rules.json
  ZW_EVENT_SEED                                    → event_seeds.json
  Unknown block types                              → logged, not silently dropped

Public surface:
  compile(obsidian_dir, world_rules_path, output_dir)  → CompileResult
  parse_zw_file(path)                                  → List[ZWBlock]
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# TAG → ENTITY_TYPE RESOLUTION TABLE
# Priority order: first match wins. Add more specific rules higher up.
# ---------------------------------------------------------------------------

TAG_TO_ENTITY_TYPE: List[Tuple[str, str, str]] = [
    # (tag, entity_type, cardinality)
    ("aeon_keeper",     "aeon_keeper",      "individual"),
    ("giants",          "collective",       "species"),
    ("species",         "collective",       "species"),
    ("vrill",           "force",            "abstract"),
    ("celestial",       "celestial_body",   "abstract"),
    ("faction",         "faction",          "collective"),
    ("pre_matter",      "abstract_concept", "abstract"),
    ("cosmic",          "abstract_concept", "abstract"),
]

# Entities whose non-physical nature is confirmed by ZW_CANON
# Maps canonical_id → spawnable override
CANON_SPAWNABLE_OVERRIDES: Dict[str, bool] = {}


# ---------------------------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------------------------

@dataclass
class ZWBlock:
    block_type: str          # ZW_CHARACTER_LAW, ZW_CANON, etc.
    data: Dict               # parsed fields
    source_file: str         # originating .zw path
    raw: str                 # original text for debugging


@dataclass
class CompileResult:
    entities_enriched: int = 0
    entities_discovered: int = 0    # in ZW but not yet in world_rules.json
    ap_rules_written: int = 0
    event_seeds_written: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ZW PARSER
# Simple line-by-line parser — does not require PyYAML.
# Handles duplicate top-level block types (not valid YAML, but valid ZW).
# ---------------------------------------------------------------------------

def parse_zw_file(path: str) -> List[ZWBlock]:
    """
    Parse a .zw file into a list of ZWBlock objects.
    Splits on ZW_ block boundaries, parses each block's fields.
    """
    blocks = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        print(f"[zw_compiler] ERROR reading {path}: {e}", file=sys.stderr)
        return []

    # Split into raw block strings on lines starting with ZW_
    raw_blocks = re.split(r'(?=^ZW_[A-Z_]+:)', content, flags=re.MULTILINE)
    raw_blocks = [b.strip() for b in raw_blocks if b.strip()]

    for raw in raw_blocks:
        lines = raw.splitlines()
        if not lines:
            continue

        # First line: block type (e.g. "ZW_CHARACTER_LAW:")
        type_match = re.match(r'^(ZW_[A-Z_]+):\s*$', lines[0])
        if not type_match:
            continue
        block_type = type_match.group(1)

        data = _parse_block_fields(lines[1:])
        blocks.append(ZWBlock(
            block_type=block_type,
            data=data,
            source_file=path,
            raw=raw
        ))

    return blocks


def _parse_block_fields(lines: List[str]) -> Dict:
    """
    Parse indented key-value lines into a dict.
    Handles: scalar values, quoted strings, inline lists [a,b,c], block lists.
    """
    data = {}
    current_list_key = None
    current_list = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Block list item (starts with "- ")
        if stripped.startswith("- "):
            if current_list_key:
                current_list.append(stripped[2:].strip().strip('"'))
            continue

        # Flush pending list if we hit a non-list line
        if current_list_key and not stripped.startswith("- "):
            data[current_list_key] = current_list
            current_list_key = None
            current_list = []

        # Key: value line
        kv_match = re.match(r'^(\w+):\s*(.*)', stripped)
        if not kv_match:
            continue

        key = kv_match.group(1)
        value = kv_match.group(2).strip()

        if not value:
            # Next lines are a block list
            current_list_key = key
            current_list = []
        elif value.startswith('[') and value.endswith(']'):
            # Inline list [a, b, c]
            items = [v.strip().strip('"') for v in value[1:-1].split(',')]
            data[key] = [i for i in items if i]
        else:
            # Scalar — strip quotes
            data[key] = value.strip('"')

    # Flush trailing list
    if current_list_key:
        data[current_list_key] = current_list

    return data


# ---------------------------------------------------------------------------
# ENTITY RESOLUTION
# ---------------------------------------------------------------------------

def _resolve_entity_name(block: ZWBlock) -> Optional[str]:
    """Extract the primary entity name from a block, if any."""
    d = block.data
    for key in ("character", "species", "entity", "name"):
        if key in d:
            return str(d[key])
    return None


def _resolve_type_from_tags(tags: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Given a list of ZW tags, return the most specific (entity_type, cardinality).
    Returns (None, None) if no tag matches.
    """
    for tag in tags:
        for rule_tag, etype, cardinality in TAG_TO_ENTITY_TYPE:
            if tag.lower() == rule_tag.lower():
                return etype, cardinality
    return None, None


# ---------------------------------------------------------------------------
# COMPILER CORE
# ---------------------------------------------------------------------------

def compile(
    obsidian_dir: str,
    world_rules_path: str,
    output_dir: Optional[str] = None,
) -> CompileResult:
    """
    Main compile entry point.

    Reads all .zw files from obsidian_dir, enriches world_rules.json,
    and writes ap_rules.json and event_seeds.json to output_dir.
    """
    result = CompileResult()
    obsidian_path = Path(obsidian_dir)
    rules_path = Path(world_rules_path)
    out_path = Path(output_dir) if output_dir else rules_path.parent

    # -- Load world_rules.json --
    if not rules_path.exists():
        result.errors.append(f"world_rules.json not found: {rules_path}")
        return result

    with open(rules_path, "r", encoding="utf-8") as f:
        world_rules = json.load(f)

    entities = world_rules.get("entities", {})

    # -- Collect all .zw files --
    zw_files = sorted(obsidian_path.glob("*.zw"))
    if not zw_files:
        result.warnings.append(f"No .zw files found in {obsidian_dir}")
        return result

    print(f"[zw_compiler] Found {len(zw_files)} .zw files")

    # -- Parse all blocks --
    all_blocks: List[ZWBlock] = []
    for zw_file in zw_files:
        blocks = parse_zw_file(str(zw_file))
        print(f"[zw_compiler]   {zw_file.name}: {len(blocks)} blocks")
        all_blocks.extend(blocks)

    ap_rules = []
    event_seeds = []

    # ------------------------------------------------------------------
    # PASS 1: Enrichment — CHARACTER_LAW, SPECIES_ORIGIN, side outputs
    # All entity tags and types must be fully set before canon runs.
    # ------------------------------------------------------------------
    canon_blocks = []

    for block in all_blocks:
        bt = block.block_type

        if bt == "ZW_WORLD_RULE":
            ap_rules.append({
                "id": block.data.get("id", "unknown"),
                "domain": block.data.get("domain", ""),
                "rule": block.data.get("rule", ""),
                "trigger": block.data.get("trigger", ""),
                "effects": block.data.get("effects", []),
                "constraints": block.data.get("constraints", []),
                "tags": block.data.get("tags", []),
                "source": Path(block.source_file).name,
            })
            result.ap_rules_written += 1
            continue

        if bt == "ZW_EVENT_SEED":
            event_seeds.append({
                "id": block.data.get("id", "unknown"),
                "era": block.data.get("era", ""),
                "description": block.data.get("description", ""),
                "trigger": block.data.get("trigger", ""),
                "tags": block.data.get("tags", []),
                "source": Path(block.source_file).name,
            })
            result.event_seeds_written += 1
            continue

        if bt == "ZW_CANON":
            # Defer — canon constraints run after all enrichment is complete
            canon_blocks.append(block)
            continue

        if bt in ("ZW_CHARACTER_LAW", "ZW_SPECIES_ORIGIN", "ZW_CHARACTER"):
            entity_name = _resolve_entity_name(block)
            if not entity_name:
                result.warnings.append(
                    f"[{Path(block.source_file).name}] {bt} has no entity name"
                )
                continue
            tags = block.data.get("tags", [])
            _apply_zw_to_entity(entities, entity_name, bt, block.data, tags, result)
            continue

        # Unknown block type — log but don't drop
        result.warnings.append(
            f"[{Path(block.source_file).name}] Unknown block type: {bt} (skipped)"
        )

    # ------------------------------------------------------------------
    # PASS 2: Canon constraint enforcement
    # All entity zw_tags are now fully populated.
    # Any entity tagged aeon_keeper gets non-physical enforcement.
    # ------------------------------------------------------------------
    print(f"[zw_compiler] Pass 2: applying {len(canon_blocks)} canon blocks")

    for block in canon_blocks:
        tags = block.data.get("tags", [])
        canon_id = block.data.get("id", "")

        if "aeon_keeper" in tags:
            # Apply to the faction entry
            _apply_canon_to_entity(
                entities, "Aeon Keepers",
                zw_tags=tags,
                confirmed_non_physical=True,
                canon_source=canon_id,
                result=result
            )
            # Apply to every entity whose zw_tags now include aeon_keeper
            for ename in list(entities.keys()):
                if "aeon_keeper" in entities[ename].get("zw_tags", []):
                    _apply_canon_to_entity(
                        entities, ename,
                        zw_tags=tags,
                        confirmed_non_physical=True,
                        canon_source=canon_id,
                        result=result
                    )

    # -- Write enriched world_rules.json --
    world_rules["entities"] = entities
    world_rules["_compiled_from"] = [str(f.name) for f in zw_files]

    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(world_rules, f, indent=2)
    print(f"[zw_compiler] world_rules.json written ({len(entities)} entities)")

    # -- Write ap_rules.json --
    if ap_rules:
        ap_path = out_path / "ap_rules.json"
        with open(ap_path, "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "rules": ap_rules}, f, indent=2)
        print(f"[zw_compiler] ap_rules.json written ({len(ap_rules)} rules)")

    # -- Write event_seeds.json --
    if event_seeds:
        ev_path = out_path / "event_seeds.json"
        with open(ev_path, "w", encoding="utf-8") as f:
            json.dump({"version": "1.0.0", "seeds": event_seeds}, f, indent=2)
        print(f"[zw_compiler] event_seeds.json written ({len(event_seeds)} seeds)")

    return result


def _apply_zw_to_entity(
    entities: Dict,
    name: str,
    block_type: str,
    data: Dict,
    tags: List[str],
    result: CompileResult,
) -> None:
    """Apply ZW block data to an entity entry, creating it if new."""
    # Case-insensitive lookup
    matched_key = None
    for key in entities:
        if key.lower() == name.lower():
            matched_key = key
            break

    if matched_key is None:
        # Discovered entity not yet in world_rules.json
        print(f"[zw_compiler] DISCOVERED: '{name}' from ZW — adding as candidate")
        entities[name] = {
            "canonical_name": name,
            "entity_type": "character",
            "cardinality": "individual",
            "spawnable": True,
            "render_as": "physical_actor",
            "runtime_projection": "physical",
            "_zw_candidate": True,
        }
        matched_key = name
        result.entities_discovered += 1

    entry = entities[matched_key]

    # Merge zw_tags
    existing_tags = set(entry.get("zw_tags", []))
    existing_tags.update(tags)
    entry["zw_tags"] = sorted(existing_tags)

    # Refine entity_type and cardinality from tags
    resolved_type, resolved_cardinality = _resolve_type_from_tags(tags)
    if resolved_type and entry.get("entity_type") in (None, "character", ""):
        entry["entity_type"] = resolved_type
        print(f"[zw_compiler]   {matched_key}: entity_type → {resolved_type}")

    if resolved_cardinality and entry.get("cardinality") in (None, "individual", ""):
        # Only upgrade cardinality — don't downgrade a species to individual
        if resolved_cardinality in ("species", "collective", "abstract"):
            entry["cardinality"] = resolved_cardinality

    # Store block-specific fields
    if block_type == "ZW_CHARACTER_LAW":
        laws = entry.get("zw_laws", [])
        law_text = data.get("law", "")
        if law_text and law_text not in laws:
            laws.append(law_text)
        entry["zw_laws"] = laws

    if block_type == "ZW_SPECIES_ORIGIN":
        entry["zw_origin"] = {
            "derived_from": data.get("derived_from", ""),
            "survival_mechanism": data.get("survival_mechanism", ""),
            "evolution_driver": data.get("evolution_driver", ""),
        }
        # Species are not individually spawnable
        entry["spawnable"] = False
        entry["render_as"] = "distributed_presence"
        entry["runtime_projection"] = "conditional"

    result.entities_enriched += 1


def _apply_canon_to_entity(
    entities: Dict,
    name: str,
    zw_tags: List[str],
    confirmed_non_physical: bool,
    canon_source: str,
    result: CompileResult,
) -> None:
    """Apply canon constraints to an existing entity."""
    matched_key = None
    for key in entities:
        if key.lower() == name.lower():
            matched_key = key
            break
    if not matched_key:
        return

    entry = entities[matched_key]

    existing_tags = set(entry.get("zw_tags", []))
    existing_tags.update(zw_tags)
    entry["zw_tags"] = sorted(existing_tags)

    if confirmed_non_physical:
        entry["spawnable"] = False
        entry["render_as"] = entry.get("render_as", "none")
        if entry.get("runtime_projection") == "physical":
            entry["runtime_projection"] = "excluded"

    sources = entry.get("zw_canon_sources", [])
    if canon_source not in sources:
        sources.append(canon_source)
    entry["zw_canon_sources"] = sources


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Compile .zw obsidian files into world_rules.json"
    )
    parser.add_argument(
        "--obsidian",
        default=os.path.join(os.path.dirname(__file__), "..", "obsidian"),
        help="Path to obsidian/ directory containing .zw files"
    )
    parser.add_argument(
        "--world-rules",
        default=os.path.join(os.path.dirname(__file__), "..", "manifests", "world_rules.json"),
        help="Path to world_rules.json"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for ap_rules.json and event_seeds.json (defaults to manifests/)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report without writing any files"
    )
    args = parser.parse_args()

    print(f"[zw_compiler] obsidian: {args.obsidian}")
    print(f"[zw_compiler] world_rules: {args.world_rules}")

    if args.dry_run:
        zw_files = sorted(Path(args.obsidian).glob("*.zw"))
        print(f"\nDry run — found {len(zw_files)} .zw files:")
        for f in zw_files:
            blocks = parse_zw_file(str(f))
            print(f"  {f.name}: {len(blocks)} blocks")
            for b in blocks:
                name = _resolve_entity_name(b)
                print(f"    {b.block_type} → entity={name or '(none)'} tags={b.data.get('tags', [])}")
        sys.exit(0)

    result = compile(
        obsidian_dir=args.obsidian,
        world_rules_path=args.world_rules,
        output_dir=args.output_dir,
    )

    print(f"\n[zw_compiler] === Compile Result ===")
    print(f"  Entities enriched:   {result.entities_enriched}")
    print(f"  Entities discovered: {result.entities_discovered}")
    print(f"  AP rules written:    {result.ap_rules_written}")
    print(f"  Event seeds written: {result.event_seeds_written}")

    if result.warnings:
        print(f"\n  Warnings ({len(result.warnings)}):")
        for w in result.warnings:
            print(f"    - {w}")

    if result.errors:
        print(f"\n  Errors ({len(result.errors)}):")
        for e in result.errors:
            print(f"    - {e}")
        sys.exit(1)

    print("\n[zw_compiler] Done.")
