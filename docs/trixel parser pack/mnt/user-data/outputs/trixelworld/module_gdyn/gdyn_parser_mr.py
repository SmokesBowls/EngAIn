"""
module_gdyn/parser.py — GIMP Dynamics (.gdyn) parser

Confirmed against: Pencil-Generic.gdyn, Random-Color.gdyn, Basic-Simple.gdyn

Format is a flat s-expression tree:
  (name "Name")
  (opacity-output
      (use-pressure yes/no)
      (use-velocity yes/no)
      (use-direction yes/no)
      (use-tilt yes/no)
      (use-wheel yes/no)
      (use-random yes/no)
      (use-fade yes/no)
      (pressure-curve (...)) (velocity-curve (...)) ...
  )
  ... repeated for each output channel ...

Key insight from diffing real files:
  - The 256-sample LUT is always present but only meaningful when the
    corresponding use-X flag is 'yes'.
  - Inactive curves are identity ramps (0/256, 1/256, 2/256 ...).
  - Trixel only needs the use-flags + the active curves.
    Inactive curve data is stored but not loaded by default.

Parser returns a frozen DynPreset dataclass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Input source names (order matches file)
# ---------------------------------------------------------------------------

INPUTS = ("pressure", "velocity", "direction", "tilt", "wheel", "random", "fade")

# Output channel names exactly as they appear in .gdyn files
OUTPUT_CHANNELS = (
    "opacity", "size", "angle", "color", "force",
    "hardness", "aspect_ratio", "spacing", "rate", "flow", "jitter",
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DynCurve:
    """
    A 256-point lookup table for one (output, input) pair.
    Stored as a tuple of floats in [0.0, 1.0].
    Only populated when the corresponding use-flag is True.
    """
    samples: tuple[float, ...]  # length 256

    def to_dict(self) -> dict:
        return {"samples": list(self.samples)}


@dataclass(frozen=True)
class DynOutput:
    """
    One output channel (e.g. 'opacity') with its set of active inputs
    and the corresponding LUT curves.

    active_inputs: frozenset of input names that are enabled (use-X = yes)
    curves: dict mapping input name → DynCurve, only for active inputs
    """
    channel:      str
    active_inputs: frozenset[str]
    curves:       dict[str, DynCurve]  # input_name → curve (active only)

    def is_active(self) -> bool:
        return len(self.active_inputs) > 0

    def to_dict(self) -> dict:
        return {
            "channel":       self.channel,
            "active_inputs": sorted(self.active_inputs),
            "curves":        {k: v.to_dict() for k, v in self.curves.items()},
        }


@dataclass(frozen=True)
class DynPreset:
    """
    Full dynamics preset, normalized from a .gdyn file.

    outputs: dict mapping channel name → DynOutput
             All 11 channels are always present; inactive ones have empty
             active_inputs and no curves.
    """
    name:    str
    outputs: dict[str, DynOutput]

    def active_channels(self) -> list[str]:
        """Return names of channels that have at least one active input."""
        return [ch for ch, out in self.outputs.items() if out.is_active()]

    def to_dict(self) -> dict:
        return {
            "name":    self.name,
            "outputs": {k: v.to_dict() for k, v in self.outputs.items()},
        }


# ---------------------------------------------------------------------------
# Parser internals
# ---------------------------------------------------------------------------

# Matches (key value) at the top of a block, e.g. (use-pressure yes)
_FLAG_RE = re.compile(r'\(use-(\w+)\s+(yes|no)\)')

# Matches the name line: (name "Some Name")
_NAME_RE = re.compile(r'\(name\s+"([^"]+)"\)')

# Matches the samples line: (samples 256 0.000000 0.003922 ...)
_SAMPLES_RE = re.compile(r'\(samples\s+(\d+)((?:\s+[\d.]+)+)\s*\)')

# Matches output-block opening: (opacity-output
_OUTPUT_START_RE = re.compile(
    r'\((' + '|'.join(ch.replace('_', '-') + r'-output' for ch in OUTPUT_CHANNELS) + r')'
)


def parse_gdyn(path: Path, load_inactive_curves: bool = False) -> DynPreset:
    """
    Parse a .gdyn file and return a DynPreset.

    Args:
        path: Path to the .gdyn file.
        load_inactive_curves: If True, parse and store LUT data even for
            inputs that are disabled (use-X = no). Default False — inactive
            curves are the identity ramp and cost ~2 KB each.

    Raises:
        ValueError: File does not start with expected GIMP dynamics header.
    """
    text = path.read_text(encoding="utf-8", errors="replace")

    if "# GIMP dynamics file" not in text:
        raise ValueError(f"{path.name}: missing GIMP dynamics header")

    name = _parse_name(text, path.name)
    outputs = _parse_outputs(text, path.name, load_inactive_curves)

    return DynPreset(name=name, outputs=outputs)


def _parse_name(text: str, filename: str) -> str:
    m = _NAME_RE.search(text)
    if not m:
        raise ValueError(f"{filename}: could not find (name ...) field")
    return m.group(1)


def _parse_outputs(text: str, filename: str,
                   load_inactive: bool) -> dict[str, DynOutput]:
    outputs: dict[str, DynOutput] = {}

    # Build canonical channel name map: 'opacity-output' → 'opacity'
    key_to_channel = {
        ch.replace("_", "-") + "-output": ch for ch in OUTPUT_CHANNELS
    }

    for raw_key, channel in key_to_channel.items():
        block = _extract_block(text, raw_key)
        if block is None:
            # Channel not present in file — treat as inactive/empty
            outputs[channel] = DynOutput(
                channel=channel,
                active_inputs=frozenset(),
                curves={},
            )
            continue

        active, curves = _parse_output_block(block, load_inactive)
        outputs[channel] = DynOutput(
            channel=channel,
            active_inputs=frozenset(active),
            curves=curves,
        )

    return outputs


def _extract_block(text: str, key: str) -> Optional[str]:
    """
    Extract the text of a top-level s-expression block by its key name.
    Returns None if the key is not found.
    """
    start_tag = f"({key}"
    start = text.find(start_tag)
    if start == -1:
        return None

    # Walk forward counting parentheses to find the matching close
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:]  # unterminated — return remainder


def _parse_output_block(block: str,
                        load_inactive: bool) -> tuple[list[str], dict[str, DynCurve]]:
    """Parse a single output block, return (active_input_names, curves)."""
    active: list[str] = []
    curves: dict[str, DynCurve] = {}

    # Find all use-X flags
    use_flags: dict[str, bool] = {}
    for m in _FLAG_RE.finditer(block):
        input_name = m.group(1)
        enabled    = m.group(2) == "yes"
        use_flags[input_name] = enabled
        if enabled:
            active.append(input_name)

    if not load_inactive and not active:
        return active, curves

    # Extract per-input curves
    for input_name in INPUTS:
        curve_key = f"{input_name}-curve"
        curve_block = _extract_block(block, curve_key)
        if curve_block is None:
            continue

        is_active = use_flags.get(input_name, False)
        if not is_active and not load_inactive:
            continue

        curve = _parse_samples(curve_block)
        if curve is not None:
            curves[input_name] = curve

    return active, curves


def _parse_samples(curve_block: str) -> Optional[DynCurve]:
    """Extract the 256-sample LUT from a curve block."""
    m = _SAMPLES_RE.search(curve_block)
    if not m:
        return None
    count = int(m.group(1))
    raw   = m.group(2).split()
    if len(raw) < count:
        return None
    samples = tuple(float(v) for v in raw[:count])
    return DynCurve(samples=samples)


# ---------------------------------------------------------------------------
# Batch loader
# ---------------------------------------------------------------------------

def load_directory(directory: Path,
                   load_inactive_curves: bool = False) -> list[DynPreset]:
    """Load all .gdyn files found recursively under directory."""
    presets = []
    for path in sorted(directory.rglob("*.gdyn")):
        presets.append(parse_gdyn(path, load_inactive_curves))
    return presets


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    targets = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else []

    if not targets:
        print("Usage: python parser.py path/to/file.gdyn [...]")
        sys.exit(0)

    for t in targets:
        if t.is_dir():
            results = load_directory(t)
            print(f"Loaded {len(results)} .gdyn presets from {t}")
            for p in results:
                active = p.active_channels()
                print(f"  {p.name!r:40s}  active={active}")
        else:
            p = parse_gdyn(t)
            print(f"Name: {p.name!r}")
            print(f"Active channels: {p.active_channels()}")
            for ch, out in p.outputs.items():
                if out.is_active():
                    print(f"  {ch:15s}  inputs={sorted(out.active_inputs)}")
