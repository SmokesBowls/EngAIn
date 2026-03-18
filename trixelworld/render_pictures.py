#!/usr/bin/env python3
import sys
import math
from pathlib import Path

sys.path.insert(0, '.')
sys.path.insert(0, 'brushes')

from trixel_brush_adapter import AssetRegistry
from brushes.engine_mr import SurfaceBuffer, stamp_recipe, stroke_to_events

print("🎨 TRIxel BRUSH RENDERER — REAL ENVIRONMENT TEST")
print("=" * 60)

registry = AssetRegistry()
registry.load_from_directory(Path('data'))

summary = registry.summary()
print(f"✅ Shapes loaded: {summary['shapes']}")
print(f"✅ Dynamics loaded: {summary['dynamics']}")
print()

# Create output directory (with parents=True)
out_dir = Path('test_results/real_env')
out_dir.mkdir(parents=True, exist_ok=True)

rendered = 0
for name, shape in list(registry.shapes.items())[:10]:
    try:
        recipe = registry.build_recipe_from_parts(name, None)
        if not recipe:
            print(f"⚠️  Skip {name}: recipe build failed")
            continue
        
        W, H = 400, 300
        buf = SurfaceBuffer.blank(W, H)
        
        pts = [(50 + i * 10, 150 + math.sin(i * 0.3) * 50) for i in range(30)]
        base_radius = shape.radius or 20 if shape.is_parametric() else (shape.width or 32) // 2
        spacing = shape.spacing_pct or 1.0
        
        events = stroke_to_events(pts, spacing_pct=spacing, base_radius=base_radius, pressure=0.8, seed=42)
        
        for idx, ev in enumerate(events):
            stamp_recipe(buf, recipe, ev, stroke_index=idx, colour=(50, 50, 50))
        
        out_path = out_dir / f"{rendered:03d}_{name.replace(' ', '_')}.pgm"
        out_path.write_bytes(buf.to_pgm())
        
        print(f"✅ [{rendered:02d}] {name:25s} → {out_path.name}")
        rendered += 1
        
    except Exception as e:
        print(f"❌ [{rendered:02d}] {name:25s} → ERROR: {e}")
        rendered += 1

print()
print("=" * 60)
print(f"🎉 RENDERED: {rendered} images to {out_dir}/")
print(f"📁 View with: eog {out_dir}/*.pgm")
