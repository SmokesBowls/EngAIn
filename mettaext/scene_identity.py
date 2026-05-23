# mettaext/scene_identity.py
#
# Pure deterministic scene identity functions.
# No file scanning. No renaming. No side effects.
#
# Authority: EngAIn compiler and runtime use this to normalize
# scene identities internally, regardless of what the source
# filename or draft title looks like.

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical scene ID prefix
SCENE_PREFIX = "scene"

# Characters allowed in a slug (after normalization)
_SLUG_ALLOWED = re.compile(r"[^a-z0-9_]")

# A canonical scene ID: scene.NNN_slug  (e.g. scene.002_molten_descent)
_CANONICAL_PATTERN = re.compile(
    r"^scene\.\d{3}_[a-z][a-z0-9_]*$"
)

# Known file extensions to strip before processing
_STRIP_EXTENSIONS = (
    ".zonj.json", ".zon.json", ".json",
    ".zonj", ".zon",
    ".md", ".txt",
)

# Compound suffixes to strip from the slug (after extension removal)
_STRIP_SUFFIXES = (
    "_with_semantics",
)

# Known typo aliases to normalize in slugs
_TYPO_ALIASES = {
    "fist_contact": "first_contact",
    "sacrafice": "sacrifice",
    "assesment": "assessment",
    "convergance": "convergence",
}

# Words to collapse during slug normalization
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "on", "at",
    "to", "for", "with", "by",
})


# ---------------------------------------------------------------------------
# Core: normalize_slug
# ---------------------------------------------------------------------------

def normalize_slug(text: str) -> str:
    """
    Convert any arbitrary text to a clean lowercase underscore slug.

    Examples:
        "Molten Descent With Semantics" -> "molten_descent"
        "002_molten-descent.zonj.json"  -> "002_molten_descent"
        "  The Forgotten City  "        -> "the_forgotten_city"
    """
    s = text.strip()

    # Strip known file extensions
    for ext in _STRIP_EXTENSIONS:
        if s.lower().endswith(ext):
            s = s[: -len(ext)]

    # Lowercase
    s = s.lower()

    # Replace hyphens and spaces with underscore
    s = re.sub(r"[-\s]+", "_", s)

    # Remove all non-allowed characters
    s = _SLUG_ALLOWED.sub("", s)

    # Collapse repeated underscores
    s = re.sub(r"_+", "_", s)

    # Strip leading/trailing underscores
    s = s.strip("_")

    # Strip known compound suffixes (e.g., _with_semantics)
    for suffix in _STRIP_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            s = s.rstrip("_")  # Clean up any trailing underscore left behind

    # Normalize known typo aliases
    for typo, correction in _TYPO_ALIASES.items():
        # Use word boundary-like replacement for underscore-separated slugs
        # Replace typo when it appears as a whole segment or at start/end
        s = re.sub(r"(^|_)" + re.escape(typo) + r"($|_)", r"\1" + correction + r"\2", s)

    # Final cleanup: collapse underscores again and strip
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")

    return s


# ---------------------------------------------------------------------------
# Core: to_canonical_scene_id
# ---------------------------------------------------------------------------

def to_canonical_scene_id(raw: str, sequence: int | None = None) -> str:
    """
    Derive a canonical scene ID from any raw input string.

    The canonical form is: scene.NNN_slug
        NNN = zero-padded 3-digit sequence number
        slug = normalized lowercase underscore identifier

    `raw` can be:
        - A filename:   "002_molten_descent_with_semantics.zonj.json"
        - A title:      "Molten Descent"
        - A scene ID:   "scene.002_molten_descent"
        - A ZON @id:    "scene.002_molten_descent"
        - A chapter:    "chapter_43_the_hub_falls.zonj.json"

    `sequence` overrides any number extracted from `raw`.
    If no number is found and none is provided, sequence defaults to 0.

    Examples:
        to_canonical_scene_id("002_molten_descent_with_semantics.zonj.json")
            -> "scene.002_molten_descent"

        to_canonical_scene_id("chapter_43_the_hub_falls.zonj.json")
            -> "scene.043_the_hub_falls"

        to_canonical_scene_id("Molten Descent", sequence=2)
            -> "scene.002_molten_descent"

        to_canonical_scene_id("scene.007_the_vault")
            -> "scene.007_the_vault"
    """
    # Already canonical — verify and return
    if _CANONICAL_PATTERN.match(raw.strip()):
        return raw.strip()

    # Strip the scene. prefix if present before processing
    working = raw.strip()
    if working.lower().startswith(f"{SCENE_PREFIX}."):
        working = working[len(SCENE_PREFIX) + 1:]

    slug = normalize_slug(working)

    # Strip a leading 'scene_' prefix if the slug accidentally starts with it
    # (e.g. "SCENE_004_RUINS" normalizes to "scene_004_ruins")
    slug = re.sub(r"^scene[_.]", "", slug)

    # Extract leading sequence number from slug if present
    extracted_seq: int | None = None
    
    # Check for chapter_NN_ pattern first
    chapter_match = re.match(r"^chapter_(\d+)_(.+)$", slug)
    if chapter_match:
        extracted_seq = int(chapter_match.group(1))
        slug = chapter_match.group(2)
    else:
        # Check for standard leading number pattern
        seq_match = re.match(r"^(\d+)_(.+)$", slug)
        if seq_match:
            extracted_seq = int(seq_match.group(1))
            slug = seq_match.group(2)

    # Resolve final sequence number
    final_seq = sequence if sequence is not None else (extracted_seq if extracted_seq is not None else 0)

    return f"{SCENE_PREFIX}.{final_seq:03d}_{slug}"


# ---------------------------------------------------------------------------
# Core: detect_identity_drift
# ---------------------------------------------------------------------------

@dataclass
class IdentityDrift:
    """Result of comparing a source name against its expected canonical form."""
    source: str                   # The input that was checked
    canonical: str                # What it should be
    has_drift: bool               # True if source != canonical
    drift_reasons: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.has_drift

    def summary(self) -> str:
        if not self.has_drift:
            return f"OK  {self.source}"
        reasons = "; ".join(self.drift_reasons)
        return f"DRIFT  {self.source!r}  →  {self.canonical!r}  ({reasons})"


def detect_identity_drift(
    source: str,
    scene_id: str | None = None,
    sequence: int | None = None,
) -> IdentityDrift:
    """
    Detect whether `source` (a filename, title, or raw ID) drifts from
    its canonical scene identity.

    If `scene_id` is provided, it is used as the authoritative canonical ID.
    Otherwise, the canonical ID is derived from `source` itself.

    Returns an IdentityDrift describing what's wrong (if anything).

    Examples:
        detect_identity_drift("002_molten_descent_with_semantics.zonj.json")
        # canonical = "scene.002_molten_descent"
        # has_drift = True (missing scene. prefix, has extension)

        detect_identity_drift("scene.002_molten_descent")
        # has_drift = False

        detect_identity_drift(
            "MoltenDescent.json",
            scene_id="scene.002_molten_descent"
        )
        # has_drift = True (slug differs from scene_id)
    """
    canonical = scene_id if scene_id else to_canonical_scene_id(source, sequence)
    reasons: list[str] = []

    # --- Check 1: Does it match the canonical ID directly? ---
    source_as_canonical = to_canonical_scene_id(source, sequence)
    if source_as_canonical != canonical:
        reasons.append(f"slug mismatch: derived '{source_as_canonical}' != expected '{canonical}'")

    # --- Check 2: Has a bare file extension? ---
    for ext in _STRIP_EXTENSIONS:
        if source.lower().endswith(ext):
            reasons.append(f"has extension '{ext}'")
            break

    # --- Check 3: Missing scene. prefix? ---
    if not source.strip().startswith(f"{SCENE_PREFIX}."):
        reasons.append("missing 'scene.' prefix")

    # --- Check 4: Has uppercase? ---
    if source != source.lower():
        reasons.append("contains uppercase")

    # --- Check 5: Has hyphens or spaces? ---
    if re.search(r"[-\s]", source):
        reasons.append("contains hyphens or spaces")

    # --- Check 6: Not a valid canonical pattern? ---
    if not _CANONICAL_PATTERN.match(source.strip()):
        if "missing 'scene.' prefix" not in reasons:
            reasons.append("does not match canonical pattern scene.NNN_slug")

    has_drift = bool(reasons)
    return IdentityDrift(
        source=source,
        canonical=canonical,
        has_drift=has_drift,
        drift_reasons=reasons,
    )


# ---------------------------------------------------------------------------
# Batch helper
# ---------------------------------------------------------------------------

def audit_names(names: list[str], sequence_hint: int | None = None) -> list[IdentityDrift]:
    """
    Run detect_identity_drift over a list of names.
    Returns one IdentityDrift per name.
    """
    return [detect_identity_drift(n, sequence=sequence_hint) for n in names]


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        "scene.002_molten_descent",
        "002_molten_descent_with_semantics.zonj.json",
        "Molten Descent",
        "007_the_forgotten_city.zon.json",
        "scene.007_the_forgotten_city",
        "The Vault of Stars.md",
        "vault-of-stars",
        "SCENE_004_RUINS",
        "03_Fist_contact.zonj.json",
        "chapter_43_the _hub_falls.zonj.json",
    ]

    print("=== scene_identity smoke test ===\n")
    for name in test_cases:
        drift = detect_identity_drift(name)
        print(drift.summary())
    print()

    # Canonical derivation
    print("=== to_canonical_scene_id ===\n")
    for name in test_cases:
        print(f"  {name!r:50s}  ->  {to_canonical_scene_id(name)}")
