#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, '.')
sys.path.insert(0, 'brushes')

from trixel_brush_adapter import AssetRegistry
from brushes.engine_mr import SurfaceBuffer, stamp_recipe, stroke_to_events

print("🎨 Loading assets...")
reg = AssetRegistry()
reg.load_from_directory(Path('data'))
reg.load_from_directory(Path('Documentation/dynamics'))

print(f"   Shapes: {len(reg.shapes)}")
print(f"   Dynamics: {len(reg.dynamics)}")

# Build and render a test stroke
if reg.shapes and reg.dynamics:
    shape_name = next(iter(reg.shapes))
    dyn_name = next(iter(reg.dynamics))
    recipe = reg.build_recipe_from_parts(shape_name, dyn_name)
    
    if recipe:
        print(f"\n✅ Recipe: {recipe.recipe_id}")
        
        # Render to surface
        buf = SurfaceBuffer.blank(400, 300)
        pts = [(50 + i*10, 150) for i in range(30)]
        events = stroke_to_events(pts, spacing_pct=1.0, base_radius=20, seed=42)
        
        for idx, ev in enumerate(events):
            stamp_recipe(buf, recipe, ev, stroke_index=idx, colour=(50, 50, 50))
        
        Path('test_output.pgm').write_bytes(buf.to_pgm())
        print("✅ Rendered: test_output.pgm")
