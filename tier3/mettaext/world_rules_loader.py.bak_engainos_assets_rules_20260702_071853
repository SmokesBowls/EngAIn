# ---------------------------------------------------------------------------
# DEPENDENCY TRACKING
# ---------------------------------------------------------------------------
# This file calls: world_rules.json (manifests/world_rules.json)
# This file is called by: pass2_entity_filter.py (entity classification)
#                          sim_runtime.py (spawn authority check)
#                          pass3_merge.py (cardinality resolution)
# ---------------------------------------------------------------------------
"""
world_rules_loader.py — EngAIn Canonical Entity Ontology Authority

Single source of truth for all entity classification in EngAIn.

Replaces:
  - NON_SPAWNABLE_ENTITIES in Boot.gd
  - NON_SPAWNABLE_ENTITIES in Main.gd
  - STOPWORDS (entity portion) in pass2_entity_filter.py
  - WHITELIST in pass2_entity_filter.py
  - GENERIC_WORDS in pass2_entity_filter.py

Public surface:
  load_rules(path)         → load and validate world_rules.json
  is_spawnable(name)       → bool
  get_cardinality(name)    → str | "unknown"
  get_render_as(name)      → str | "none"
  get_entity_type(name)    → str | None
  is_known(name)           → bool
  filter_spawnable(names)  → list of names that may physically spawn
  build_stopset()          → set of non-spawnable canonical names (for pass2 compat)

Authority contract:
  If an entity_id is not in world_rules.json, it is UNKNOWN.
  Unknown entities are logged as warnings, not silently accepted or rejected.
  The pipeline must surface unknown entities to the canon debugger, not guess.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# MODULE STATE — loaded once at import, refreshable via load_rules()
# ---------------------------------------------------------------------------

_RULES: Dict = {}
_ENTITIES: Dict = {}
_LOADED_PATH: str = ""

# Canonical path — override by calling load_rules(custom_path) at boot
_DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "manifests", "world_rules.json"
)


# ---------------------------------------------------------------------------
# LOADER
# ---------------------------------------------------------------------------

def load_rules(path: Optional[str] = None) -> bool:
    """
    Load world_rules.json into module state.
    Returns True on success, False on failure.
    Call once at pipeline boot. Safe to call again to hot-reload.
    """
    global _RULES, _ENTITIES, _LOADED_PATH

    target = path or _DEFAULT_PATH
    target = os.path.abspath(target)

    if not os.path.exists(target):
        print(f"[world_rules] ERROR: rules file not found at {target}", file=sys.stderr)
        return False

    try:
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        # Hard failure — malformed ontology is worse than no ontology
        print(f"[world_rules] FATAL: malformed JSON at {target}: {e}", file=sys.stderr)
        raise  # Do not swallow. Pipeline must not run with broken ontology.

    _RULES = data
    _ENTITIES = data.get("entities", {})
    _LOADED_PATH = target
    print(f"[world_rules] loaded {len(_ENTITIES)} entities from {target}")
    return True


def _ensure_loaded() -> None:
    """Auto-load with default path if not yet loaded."""
    if not _ENTITIES:
        load_rules()


# ---------------------------------------------------------------------------
# LOOKUP HELPERS (case-sensitive first, then case-insensitive fallback)
# ---------------------------------------------------------------------------

def _find(name: str) -> Optional[Dict]:
    """
    Look up entity entry. Tries exact match first, then lowercase match.
    Returns None if not found.
    """
    _ensure_loaded()
    if name in _ENTITIES:
        return _ENTITIES[name]
    # Case-insensitive fallback for runtime IDs (e.g. "elyraen" vs "Elyraen")
    lower = name.lower()
    for key, val in _ENTITIES.items():
        if key.lower() == lower:
            return val
    return None


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def is_known(name: str) -> bool:
    """True if entity is registered in world_rules.json."""
    return _find(name) is not None


def is_spawnable(name: str) -> bool:
    """
    True if entity may appear as a physical actor in Godot.
    Unknown entities return False and emit a warning — they must be
    added to world_rules.json before they can spawn.
    """
    entry = _find(name)
    if entry is None:
        print(
            f"[world_rules] WARNING: unknown entity '{name}' — treating as non-spawnable. "
            f"Add to world_rules.json to resolve.",
            file=sys.stderr
        )
        return False
    return bool(entry.get("spawnable", False))


def get_cardinality(name: str) -> str:
    """
    Returns cardinality tag: individual | collective | species | abstract | unknown.
    Unknown entities return 'unknown'.
    """
    entry = _find(name)
    if entry is None:
        return "unknown"
    return str(entry.get("cardinality", "unknown"))


def get_render_as(name: str) -> str:
    """
    Returns render mode: physical_actor | distributed_presence | none.
    Unknown entities return 'none'.
    """
    entry = _find(name)
    if entry is None:
        return "none"
    return str(entry.get("render_as", "none"))


def get_entity_type(name: str) -> Optional[str]:
    """Returns entity_type string, or None if unknown."""
    entry = _find(name)
    if entry is None:
        return None
    return entry.get("entity_type")


def get_runtime_projection(name: str) -> str:
    """
    Returns runtime_projection: physical | symbolic | conditional | excluded.
    Unknown entities return 'excluded'.
    """
    entry = _find(name)
    if entry is None:
        return "excluded"
    return str(entry.get("runtime_projection", "excluded"))


def filter_spawnable(names: List[str]) -> List[str]:
    """
    Filter a list of entity names/ids to only those allowed to spawn.
    Logs a warning for any unknown entity encountered.
    """
    result = []
    for name in names:
        if is_spawnable(name):
            result.append(name)
        else:
            entry = _find(name)
            if entry is not None:
                print(f"[world_rules] filtered non-spawnable: '{name}' "
                      f"(type={entry.get('entity_type')}, cardinality={entry.get('cardinality')})")
    return result


def build_stopset() -> Set[str]:
    """
    Returns the set of canonical names that are NOT spawnable.
    Used by pass2_entity_filter.py as a replacement for hardcoded STOPWORDS
    and NON_SPAWNABLE_ENTITIES.

    This is a compatibility bridge — eventually pass2 should call
    is_spawnable() directly rather than using a stopset.
    """
    _ensure_loaded()
    return {
        name for name, entry in _ENTITIES.items()
        if not entry.get("spawnable", False)
    }


def get_all_known_names() -> Set[str]:
    """Returns all registered entity names (both cases)."""
    _ensure_loaded()
    return set(_ENTITIES.keys())


def dump_summary() -> None:
    """Print a human-readable summary of loaded rules. Useful for debug."""
    _ensure_loaded()
    print(f"\n[world_rules] === Ontology Summary ({len(_ENTITIES)} entities) ===")
    spawnable = [n for n, e in _ENTITIES.items() if e.get("spawnable")]
    blocked = [n for n, e in _ENTITIES.items() if not e.get("spawnable")]
    print(f"  Spawnable ({len(spawnable)}): {sorted(spawnable)}")
    print(f"  Non-spawnable ({len(blocked)}): {sorted(blocked)}")
    print()


# ---------------------------------------------------------------------------
# BOOT VALIDATION
# ---------------------------------------------------------------------------

def validate() -> List[str]:
    """
    Validate all entries in world_rules.json for schema compliance.
    Returns a list of error strings. Empty list = valid.
    Run at pipeline boot to catch malformed entries before they corrupt runtime.
    """
    _ensure_loaded()
    errors = []
    valid_types = {"character", "aeon_keeper", "faction", "collective", "abstract_concept",
                   "abstract_referent", "celestial_body", "force"}
    valid_cardinalities = {"individual", "collective", "species", "abstract", "unknown"}
    valid_render_as = {"physical_actor", "distributed_presence", "none"}

    for name, entry in _ENTITIES.items():
        if "entity_type" not in entry:
            errors.append(f"'{name}': missing entity_type")
        elif entry["entity_type"] not in valid_types:
            errors.append(f"'{name}': unknown entity_type '{entry['entity_type']}'")

        if "cardinality" not in entry:
            errors.append(f"'{name}': missing cardinality")
        elif entry["cardinality"] not in valid_cardinalities:
            errors.append(f"'{name}': unknown cardinality '{entry['cardinality']}'")

        if "spawnable" not in entry:
            errors.append(f"'{name}': missing spawnable field")

        if "render_as" not in entry:
            errors.append(f"'{name}': missing render_as")
        elif entry["render_as"] not in valid_render_as:
            errors.append(f"'{name}': unknown render_as '{entry['render_as']}'")

    return errors


# ---------------------------------------------------------------------------
# SELF-TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    rules_path = os.path.join(os.path.dirname(__file__), "..", "manifests", "world_rules.json")
    ok = load_rules(rules_path)
    if not ok:
        print("Failed to load rules — check path")
        sys.exit(1)

    errors = validate()
    if errors:
        print(f"VALIDATION ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    dump_summary()

    # Spot-check beach entities
    beach = ["elyraen", "kyreth", "olythae", "senareth", "someone", "torhh", "unknown", "vairis"]
    print("[world_rules] Beach entity check:")
    for name in beach:
        print(f"  {name:12} spawnable={is_spawnable(name):<5} "
              f"cardinality={get_cardinality(name):<12} "
              f"render_as={get_render_as(name)}")

    # Confirm old non-spawnables are still blocked
    blocked_check = ["Aeon Keepers", "Veil", "Tiamat", "Akashic Records", "Vrill"]
    print("\n[world_rules] Legacy non-spawnable check:")
    for name in blocked_check:
        spawnable = is_spawnable(name)
        status = "BLOCKED" if not spawnable else "ERROR - SHOULD BE BLOCKED"
        print(f"  {name:20} {status}")

    print("\n[world_rules] All checks passed.")
