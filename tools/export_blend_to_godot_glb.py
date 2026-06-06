import bpy
from pathlib import Path

SOURCE_BLEND = Path("/tmp/engain_biome_terrain.blend")
OUTPUT_GLB = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/assets/blender/engain_biome_terrain.glb")

if not SOURCE_BLEND.exists():
    raise FileNotFoundError(f"Missing source blend: {SOURCE_BLEND}")

OUTPUT_GLB.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))

bpy.ops.object.select_all(action="DESELECT")
selected_count = 0

for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        obj.select_set(True)
        selected_count += 1

if selected_count == 0:
    raise RuntimeError("No mesh objects found in blend file")

for obj in bpy.context.scene.objects:
    if obj.select_get():
        bpy.context.view_layer.objects.active = obj
        break

try:
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
except Exception:
    pass

bpy.ops.export_scene.gltf(
    filepath=str(OUTPUT_GLB),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_animations=False,
)

print(f"[EXPORT] selected_meshes={selected_count}")
print(f"[EXPORT] wrote {OUTPUT_GLB}")
