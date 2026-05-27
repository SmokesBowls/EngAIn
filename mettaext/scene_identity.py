#!/usr/bin/env python3
"""Scene identity canonicalization for EngAIn.

Authority contract:
- Canonical scene IDs are stable, zero-padded, lowercase:
    scene.001_the_ethereal_vigil
- Legacy/alias forms remain readable, but are never authoritative.
"""

from __future__ import annotations

import re
from typing import Set

_EXT_RE = re.compile(r"(\.zonj\.json|\.json|\.zonj)$", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")
_MULTI_US_RE = re.compile(r"_+")


def _strip_artifact_suffixes(value: str) -> str:
    s = value.strip()
    s = _EXT_RE.sub("", s)
    s = re.sub(r"_with_semantics$", "", s, flags=re.IGNORECASE)
    return s


def _slugify(value: str) -> str:
    s = _WS_RE.sub("_", value.strip().lower())
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = _MULTI_US_RE.sub("_", s).strip("_")
    return s


def canonical_scene_id(raw: str) -> str:
    """Return canonical scene id.

    Examples:
      001_the_ethereal_vigil         -> scene.001_the_ethereal_vigil
      scene.01_the_ethereal_vigil    -> scene.001_the_ethereal_vigil
      02__molten_descent             -> scene.002_molten_descent
      scene.02_ molten_descent.zonj  -> scene.002_molten_descent
      04_the convergence             -> scene.004_the_convergence
    """
    if raw is None:
        return "scene.000_unknown"

    s = _strip_artifact_suffixes(str(raw))
    s = s.strip()
    if not s:
        return "scene.000_unknown"

    s = s.lower()
    if s.startswith("scene."):
        s = s[len("scene."):]

    s = _slugify(s)

    m = re.match(r"^(\d{1,4})[_\.-]?(.*)$", s)
    if m:
        num = int(m.group(1))
        tail = _slugify(m.group(2))
        if tail:
            return f"scene.{num:03d}_{tail}"
        return f"scene.{num:03d}"

    return f"scene.{s}"


def scene_id_aliases(raw: str) -> Set[str]:
    """Generate readable aliases for backward-compat lookup."""
    aliases: Set[str] = set()
    if raw is None:
        return aliases

    original = str(raw).strip()
    if not original:
        return aliases

    canonical = canonical_scene_id(original)
    aliases.add(canonical)

    stripped = _strip_artifact_suffixes(original)
    aliases.add(stripped)
    aliases.add(stripped.lower())

    if stripped.lower().startswith("scene."):
        no_prefix = stripped[len("scene."):]
        aliases.add(no_prefix)
        aliases.add(no_prefix.lower())
    else:
        aliases.add(f"scene.{stripped}")
        aliases.add(f"scene.{stripped.lower()}")

    slug = _slugify(stripped)
    aliases.add(slug)
    aliases.add(f"scene.{slug}")

    m = re.match(r"^(\d{1,4})[_\.-]?(.*)$", slug)
    if m:
        num = int(m.group(1))
        tail = _slugify(m.group(2))
        aliases.add(f"{num:03d}_{tail}" if tail else f"{num:03d}")
        aliases.add(f"scene.{num:03d}_{tail}" if tail else f"scene.{num:03d}")

    return {a for a in aliases if a}

def to_canonical_scene_id(raw: str) -> str:
    """Backward-compatible alias for canonical scene id normalization."""
    return canonical_scene_id(raw)
