"""
engain_ops.py - Canonical Lore-Ops and Archetypes for the Burdens Reality Compiler
Maps narrative text concepts to executable engine constraints.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple

# --- LORE ARCHETYPES ---
# These map narrative roles to engine properties/flags

@dataclass(frozen=True)
class Archetype:
    name: str
    category: str # "character", "relic", "location", "phenomenon"
    default_flags: Dict[str, Any] = field(default_factory=dict)
    engine_constraints: List[str] = field(default_factory=list)

ENGAIN_ARCHETYPES = {
    "crimson_heir": Archetype(
        name="Crimson Heir",
        category="character",
        default_flags={"blood_type": "crimson", "star_needle_link": True},
        engine_constraints=["reality_integrity_cost"]
    ),
    "draco_vessel": Archetype(
        name="Draco Vessel",
        category="character",
        default_flags={"blood_type": "draco", "curse_host": "red_curse"},
        engine_constraints=["temporal_desync"]
    ),
    "anunnaki_queen": Archetype(
        name="Starbound Queen",
        category="character",
        default_flags={"pattern_sculpting": True, "gravity_authority": True},
        engine_constraints=["logic_override"]
    ),
    "star_needle": Archetype(
        name="Star Needle",
        category="location",
        default_flags={"monolithic": True, "curse_seal": True},
        engine_constraints=["geometric_resonance"]
    ),
    "relic_lost": Archetype(
        name="Timeline Relic",
        category="relic",
        default_flags={"integrity_drain": 5.0},
        engine_constraints=["mandela_effect"]
    )
}

# --- NARRATIVE CONSTRAINTS (from burdens_module.py) ---

MANDELA_CONSTRAINTS = {
    "TELESCOPE_TARGET": (15.0, 240.0, 0.0),
    "ENTROPY_CORRUPTION_THRESHOLD": 85.0,
    "MAX_DREAM_DEPTH": 3,
    "REALITY_INTEGRITY_MIN": 15.0
}

# --- JSONL OP TYPES ---
# The target format for the instruction tape

OPS = {
    "STATE_SHIFT": "shift_reality",     # Changes world-state (entropy/integrity)
    "ENTITY_META": "update_lore_flags", # Updates character flags (glowing eyes, etc)
    "DREAM_OP": "dream_command",        # Depth changes or corruption triggers
    "NARRATIVE_SYNC": "sync_narrative"  # Checkpoint for the event store
}
