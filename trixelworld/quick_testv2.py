#!/usr/bin/env python3
import sys
import math
from pathlib import Path

sys.path.insert(0, '.')
sys.path.insert(0, 'brushes')

from trixel_brush_adapter import AssetRegistry
from brushes.engine_mr import SurfaceBuffer, stamp_recipe, stroke_to_events

DATA_DIR = Path('data')
OUTPUT_DIR = Path('test_results/pipeline_test')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Use ACTUAL registry keys (all GBR bitmap brushes)
TEST_CASES = [
    ("pixel", None, "bitmap"),
    ("Hatch-Pen-01", None, "bitmap"),
    ("Bristles-01", None, "bitmap"),
    ("Charcoal-01", None, "bitmap"),
]

print("🎨 TRIXEL PIPELINE TEST")
print("=" * 60)

registry = AssetRegistry()
registry.load_from_directory(DATA_DIR)

summary = registry.summary()
print(f"Loaded: {summary['shapes']} shapes, {summary['dynamics']} dynamics")
print(f"Errors: {len(registry.errors)}")
print()

passed = 0
failed = 0

for shape_name, dyn_name, expected_kind in TEST_CASES:
    try:
        recipe = registry.build_recipe_from_parts(shape_name, dyn_name)
        if not recipe:
            print(f"❌ {shape_name}: recipe build failed")
            failed += 1
            continue
        
        if recipe.shape.shape_kind != expected_kind:
            print(f"❌ {shape_name}: expected {expected_kind}, got {recipe.shape.shape_kind}")
            failed += 1
            continue
        
        buf = SurfaceBuffer.blank(400, 300)
        shape = recipe.shape
        
        base_radius = (shape.width or 32) // 2
        spacing = shape.spacing_pct or 1.0
        
        pts = [(50 + i * 10, 150 + math.sin(i * 0.3) * 50) for i in range(30)]
        events = stroke_to_events(pts, spacing_pct=spacing, base_radius=base_radius, seed=42)
        
        for idx, ev in enumerate(events):
            stamp_recipe(buf, recipe, ev, stroke_index=idx, colour=(50, 50, 50))
        
        out_path = OUTPUT_DIR / f"{shape_name.replace(' ', '_')}.pgm"
        out_path.write_bytes(buf.to_pgm())
        
        print(f"✅ {shape_name:20s} → {out_path.name}")
        passed += 1
        
    except Exception as e:
        print(f"❌ {shape_name:20s} → ERROR: {e}")
        failed += 1

print()
print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
print(f"Output: {OUTPUT_DIR}/")

sys.exit(0 if failed == 0 else 1)
