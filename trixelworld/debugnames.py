#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, '.'); sys.path.insert(0, 'brushes')

from trixel_brush_adapter import AssetRegistry

reg = AssetRegistry()
reg.load_from_directory(Path('data'))

print("📋 EXACT REGISTRY KEYS:")
print("=" * 60)
for name in sorted(reg.shapes.keys()):
    shape = reg.shapes[name]
    print(f"  '{name}'  →  {shape.source_format:3s}  {shape.shape_kind}")

print("\n🔍 Looking for 'Star' and '1-pixel':")
print(f"  'Star' in registry:     {'Star' in reg.shapes}")
print(f"  '1-pixel' in registry:  {'1-pixel' in reg.shapes}")

# Show similar names
for name in reg.shapes.keys():
    if 'star' in name.lower() or 'pixel' in name.lower():
        print(f"  → Found: '{name}'")
