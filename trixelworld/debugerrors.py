#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, '.'); sys.path.insert(0, 'brushes')

from trixel_brush_adapter import AssetRegistry

reg = AssetRegistry()
reg.load_from_directory(Path('data/brushes'))

print(f"✅ Shapes: {len(reg.shapes)}")
print(f"⚠️  Errors: {len(reg.errors)}")
print()

if reg.errors:
    print("ERROR DETAILS:")
    for i, err in enumerate(reg.errors, 1):
        print(f"  {i}. {err}")
