import bpy

def main():
    found = 0
    for obj in bpy.data.objects:
        game = getattr(obj, "game", None)
        if not game:
            continue
        controllers = getattr(game, "controllers", None)
        if not controllers:
            continue

        for c in controllers:
            if getattr(c, "type", None) != 'PYTHON':
                continue

            txt = getattr(c, "text", None)
            mod = getattr(c, "module", None)

            scr = None
            if txt is not None:
                scr = getattr(txt, "name", None)
            elif mod:
                scr = mod

            print(f"[PYCTRL] obj={obj.name} ctrl={c.name} script={scr}")
            found += 1

    if found == 0:
        print("[PYCTRL] none found (no Python controllers in this .blend)")

if __name__ == "__main__":
    main()
