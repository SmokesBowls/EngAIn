#!/usr/bin/env python3

# pass2_entity_filter.py
# STRICT entity filter for narrative → runtime pipeline
#
# Authority split:
#   - world_rules.json owns ontology truth.
#   - world_rules_loader.py decides known/spawnable/renderable status.
#   - This file only handles extraction-noise filtering.
#
# Replaces local STOPWORDS / GENERIC_WORDS / WHITELIST entity authority.

import re
from typing import Dict

from .pass2_enhanced import Character
from .. import world_rules_loader


# Abstract suffix filtering remains extraction-noise handling, not ontology.
ABSTRACT_SUFFIXES = (
    "ness", "tion", "ment", "ity", "ship", "ance", "ence"
)

# Common words remain extraction-noise handling, not ontology authority.
COMMON_WORDS = {
    "will", "part", "deep", "since", "earth", "life", "realm",
    "world", "system", "process", "records", "physical",
    "the", "they", "then", "there", "this", "that", "their",
    "when", "where", "what", "which", "each", "some", "many",
    "one", "three", "she", "he", "her", "his", "them", "it", "yes",
    "volcanic", "tongue"
}


def is_mid_sentence_cap(word: str, context: str) -> bool:
    """True if 'word' looks like a capitalised common word, not a proper name."""
    return (
        bool(word)
        and word[0].isupper()
        and not word.isupper()
        and re.match(r"^[A-Z][a-z]+$", word) is not None
        and not context.startswith(word)
    )


def _is_runtime_renderable(clean: str) -> bool:
    """
    Runtime render permission comes only from world_rules.json.
    An entity must be known, spawnable, and not render_as=none.
    """
    if not world_rules_loader.is_known(clean):
        return False

    if not world_rules_loader.is_spawnable(clean):
        return False

    if world_rules_loader.get_render_as(clean) == "none":
        return False

    return True


def filter_entities(characters: Dict[str, Character]) -> Dict[str, Character]:
    world_rules_loader.load_rules()
    errors = world_rules_loader.validate()
    if errors:
        joined = "\n".join(f"  - {err}" for err in errors)
        raise RuntimeError(f"world_rules.json validation failed:\n{joined}")

    filtered: Dict[str, Character] = {}

    for name, char in characters.items():
        clean = name.strip()
        if clean == "":
            continue

        word_lower = clean.lower()

        # Known ontology entity: world_rules.json has final authority.
        if world_rules_loader.is_known(clean):
            if _is_runtime_renderable(clean):
                filtered[clean] = char
            continue

        # Unknown entity: apply extraction-noise rules.
        # Unknowns are not allowed to spawn unless added to world_rules.json.
        if len(clean) < 4:
            continue

        if not clean[0].isupper():
            continue

        if any(word_lower.endswith(suffix) for suffix in ABSTRACT_SUFFIXES):
            continue

        if word_lower in COMMON_WORDS:
            continue

        # Weak frequency filter stays. This is noise suppression, not ontology.
        if char.mentions < 3:
            continue

        print(
            f"[pass2_entity_filter] UNKNOWN ENTITY BLOCKED: '{clean}' "
            f"(mentions={char.mentions}). Add to manifests/world_rules.json if intentional."
        )

    return filtered
