"""
module_gtp/parser.py — GIMP Tool Preset (.gtp) parser

Confirmed against: Pencil-Soft.gtp

Format: flat s-expression key-value, human-readable.

  # GIMP tool preset file
  (icon-name "gimp-tool-paintbrush")
  (name "Pencil Soft")
  (tool-options "GimpPaintOptions"
      (tool "gimp-paintbrush-tool")
      (foreground (color-rgb R G B))
      (opacity FLOAT)
      (brush "Brush Name")
      (dynamics "Dynamics Name")
      (gradient "Gradient Name")
      (brush-size FLOAT)
      (application-mode MODE)
      (use-jitter yes/no)
      (dynamics-enabled yes/no)
      (fade-length FLOAT)
      (fade-unit UNIT))
  (use-fg-bg yes/no)
  (use-brush yes/no)
  (use-dynamics yes/no)
  (use-gradient yes/no)
  (use-pattern yes/no)
  (use-palette yes/no)
  (use-font yes/no)
  # end of GIMP tool preset file

Parser returns a frozen ToolPreset dataclass.
Asset names (brush, dynamics, gradient) are stored as plain strings —
resolution is the adapter's job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RgbColor:
    r: float
    g: float
    b: float

    def to_dict(self) -> dict:
        return {"r": self.r, "g": self.g, "b": self.b}


@dataclass(frozen=True)
class ToolPreset:
    """
    Normalized GIMP tool preset.

    Asset references (brush_name, dynamics_name, gradient_name) are
    bare strings. Lookup into the actual asset tables is the caller's job.

    Slot flags (use_brush, use_dynamics, ...) reflect which asset slots
    are active for this preset.
    """
    name:             str
    icon_name:        Optional[str]
    tool:             Optional[str]          # e.g. 'gimp-paintbrush-tool'

    # Paint options
    foreground:       Optional[RgbColor]
    opacity:          Optional[float]        # 0.0 – 1.0
    brush_name:       Optional[str]
    dynamics_name:    Optional[str]
    gradient_name:    Optional[str]
    brush_size:       Optional[float]
    application_mode: Optional[str]          # e.g. 'incremental'
    use_jitter:       bool
    dynamics_enabled: bool
    fade_length:      Optional[float]
    fade_unit:        Optional[str]          # e.g. 'percent'

    # Slot flags
    use_fg_bg:        bool
    use_brush:        bool
    use_dynamics:     bool
    use_gradient:     bool
    use_pattern:      bool
    use_palette:      bool
    use_font:         bool

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "icon_name":        self.icon_name,
            "tool":             self.tool,
            "foreground":       self.foreground.to_dict() if self.foreground else None,
            "opacity":          self.opacity,
            "brush_name":       self.brush_name,
            "dynamics_name":    self.dynamics_name,
            "gradient_name":    self.gradient_name,
            "brush_size":       self.brush_size,
            "application_mode": self.application_mode,
            "use_jitter":       self.use_jitter,
            "dynamics_enabled": self.dynamics_enabled,
            "fade_length":      self.fade_length,
            "fade_unit":        self.fade_unit,
            "use_fg_bg":        self.use_fg_bg,
            "use_brush":        self.use_brush,
            "use_dynamics":     self.use_dynamics,
            "use_gradient":     self.use_gradient,
            "use_pattern":      self.use_pattern,
            "use_palette":      self.use_palette,
            "use_font":         self.use_font,
        }


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

def _str_val(key: str, text: str) -> Optional[str]:
    """Extract (key "value") — returns unquoted string or None."""
    m = re.search(r'\(' + re.escape(key) + r'\s+"([^"]+)"\)', text)
    return m.group(1) if m else None


def _float_val(key: str, text: str) -> Optional[float]:
    """Extract (key FLOAT)."""
    m = re.search(r'\(' + re.escape(key) + r'\s+([\d.]+)\)', text)
    return float(m.group(1)) if m else None


def _bool_val(key: str, text: str, default: bool = False) -> bool:
    """Extract (key yes/no)."""
    m = re.search(r'\(' + re.escape(key) + r'\s+(yes|no)\)', text)
    if not m:
        return default
    return m.group(1) == "yes"


def _word_val(key: str, text: str) -> Optional[str]:
    """Extract (key word) where word has no quotes."""
    m = re.search(r'\(' + re.escape(key) + r'\s+([^\s)]+)\)', text)
    return m.group(1) if m else None


def _color_rgb(text: str) -> Optional[RgbColor]:
    """Extract (foreground (color-rgb R G B))."""
    m = re.search(
        r'\(foreground\s+\(color-rgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\)\)',
        text
    )
    if not m:
        return None
    return RgbColor(float(m.group(1)), float(m.group(2)), float(m.group(3)))


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_gtp(path: Path) -> ToolPreset:
    """
    Parse a .gtp file and return a ToolPreset.

    Raises:
        ValueError: File does not contain the expected GIMP tool preset header.
    """
    text = path.read_text(encoding="utf-8", errors="replace")

    if "# GIMP tool preset file" not in text:
        raise ValueError(f"{path.name}: missing GIMP tool preset header")

    # Top-level fields
    icon_name = _str_val("icon-name", text)
    name      = _str_val("name", text) or path.stem

    # Extract tool-options block for inner fields
    opts_block = _extract_tool_options(text)

    tool             = _str_val("tool", opts_block)      if opts_block else None
    foreground       = _color_rgb(opts_block)             if opts_block else None
    opacity          = _float_val("opacity", opts_block)  if opts_block else None
    brush_name       = _str_val("brush", opts_block)      if opts_block else None
    dynamics_name    = _str_val("dynamics", opts_block)   if opts_block else None
    gradient_name    = _str_val("gradient", opts_block)   if opts_block else None
    brush_size       = _float_val("brush-size", opts_block) if opts_block else None
    application_mode = _word_val("application-mode", opts_block) if opts_block else None
    use_jitter       = _bool_val("use-jitter", opts_block)       if opts_block else False
    dynamics_enabled = _bool_val("dynamics-enabled", opts_block) if opts_block else False
    fade_length      = _float_val("fade-length", opts_block)     if opts_block else None
    fade_unit        = _word_val("fade-unit", opts_block)        if opts_block else None

    # Top-level slot flags (outside tool-options block)
    use_fg_bg    = _bool_val("use-fg-bg",    text)
    use_brush    = _bool_val("use-brush",    text)
    use_dynamics = _bool_val("use-dynamics", text)
    use_gradient = _bool_val("use-gradient", text)
    use_pattern  = _bool_val("use-pattern",  text)
    use_palette  = _bool_val("use-palette",  text)
    use_font     = _bool_val("use-font",     text)

    return ToolPreset(
        name=name,
        icon_name=icon_name,
        tool=tool,
        foreground=foreground,
        opacity=opacity,
        brush_name=brush_name,
        dynamics_name=dynamics_name,
        gradient_name=gradient_name,
        brush_size=brush_size,
        application_mode=application_mode,
        use_jitter=use_jitter,
        dynamics_enabled=dynamics_enabled,
        fade_length=fade_length,
        fade_unit=fade_unit,
        use_fg_bg=use_fg_bg,
        use_brush=use_brush,
        use_dynamics=use_dynamics,
        use_gradient=use_gradient,
        use_pattern=use_pattern,
        use_palette=use_palette,
        use_font=use_font,
    )


def _extract_tool_options(text: str) -> Optional[str]:
    """
    Pull out the (tool-options ...) block as a string.
    Returns None if not found.
    """
    start = text.find("(tool-options")
    if start == -1:
        return None
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
    return text[start:]


# ---------------------------------------------------------------------------
# Batch loader
# ---------------------------------------------------------------------------

def load_directory(directory: Path) -> list[ToolPreset]:
    """Load all .gtp files found recursively under directory."""
    presets = []
    for path in sorted(directory.rglob("*.gtp")):
        presets.append(parse_gtp(path))
    return presets


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    targets = [Path(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else []

    if not targets:
        print("Usage: python parser.py path/to/file.gtp [...]")
        sys.exit(0)

    for t in targets:
        if t.is_dir():
            results = load_directory(t)
            print(f"Loaded {len(results)} .gtp presets from {t}")
            for p in results:
                print(f"  {p.name!r:30s}  tool={p.tool}  "
                      f"brush={p.brush_name!r}  dyn={p.dynamics_name!r}")
        else:
            p = parse_gtp(t)
            print(json.dumps(p.to_dict(), indent=2))
