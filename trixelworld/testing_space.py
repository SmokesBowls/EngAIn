#!/usr/bin/env python3
"""
Validate spacing conversion across different brush formats.
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
sys.path.insert(0, 'brushes')

from trixel_brush_adapter import AssetRegistry

registry = AssetRegistry()
registry.load_from_directory(Path('data/brushes'))

print("📏 SPACING VALIDATION")
print("=" * 60)

for name, shape in sorted(registry.shapes.items()):
    spacing = shape.spacing_pct
    kind = shape.shape_kind
    source = shape.source_format
    
    # Validate spacing is reasonable
    if spacing <= 0:
        print(f"⚠️  {name:25s} spacing={spacing} (INVALID)")
    elif spacing > 10:
        print(f"⚠️  {name:25s} spacing={spacing} (UNUSUAL)")
    else:
        print(f"✅ {name:25s} spacing={spacing:.2f} ({kind:10s} {source})")

print()
print(f"Total shapes: {len(registry.shapes)}")
