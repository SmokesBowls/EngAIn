import bpy

for t in bpy.data.texts:
    fp = t.filepath.strip() if t.filepath else ""
    if fp:
        print(f"[EXTERNAL] {t.name} -> {fp}")
    else:
        print(f"[INTERNAL] {t.name}")
