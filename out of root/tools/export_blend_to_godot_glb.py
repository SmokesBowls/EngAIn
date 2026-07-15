import bpy
from pathlib import Path

SOURCE_BLEND = Path("/tmp/engain_biome_terrain.blend")
OUTPUT_GLB = Path("/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/assets/blender/engain_biome_terrain.glb")

if not SOURCE_BLEND.exists():
    raise FileNotFoundError(f"Missing source blend: {SOURCE_BLEND}")

OUTPUT_GLB.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))

# Remove everything that isn't WF_Terrain
bpy.ops.object.select_all(action="DESELECT")
for obj in list(bpy.context.scene.objects):
    if obj.name != "WF_Terrain":
        obj.hide_set(False)
        obj.select_set(True)
bpy.ops.object.delete()

# Select only WF_Terrain
bpy.ops.object.select_all(action="DESELECT")
selected_count = 0
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        selected_count += 1

print(f"[EXPORT] objects remaining: {[o.name for o in bpy.context.scene.objects]}")

if selected_count == 0:
    raise RuntimeError("No mesh objects found in blend file")

try:
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
except Exception:
    pass

# Convert Blender terrain plane to Godot ground plane:
# Blender: X/Y ground, Z height
# Godot target: X/Z ground, Y height
for obj in bpy.context.selected_objects:
    if obj.type == "MESH":
        obj.rotation_euler[0] = -1.57079632679  # +90 degrees
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

bpy.ops.export_scene.gltf(
    filepath=str(OUTPUT_GLB),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_animations=False,
)

print(f"[EXPORT] selected_meshes={selected_count}")
print(f"[EXPORT] wrote {OUTPUT_GLB}")
