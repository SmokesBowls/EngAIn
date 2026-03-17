# tools/patch_bridge_integration_upbge_coords_v1.py
#!/usr/bin/env python3
"""
Patch godotsim/bridge_integration.py:
- Add Godot->UPBGE coordinate conversion helpers
- Export:
    position_godot: original Godot position
    position: UPBGE/Blender position (converted)
    transform_upbge: converted transform (position + scale)
- Update bridge_entities_for_scene and _fallback_entity accordingly

Idempotent: safe to run multiple times (uses marker).
Creates timestamped backup.

Run from repo root:
  python3 tools/patch_bridge_integration_upbge_coords_v1.py
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

PATCH_MARKER = "# === COORD-CONVERT v1 (Godot->UPBGE) ==="

HELPERS_BLOCK = r'''
# === COORD-CONVERT v1 (Godot->UPBGE) ===
def _godot_to_upbge_pos(pos):
    """Convert Godot 3D position to UPBGE/Blender coords.

    Godot (common usage): x right, y up, z depth (forward is -z)
    UPBGE/Blender:        x right, y forward, z up

    Mapping:
      x' =  x
      y' = -z
      z' =  y
    """
    if not isinstance(pos, dict):
        return {"x": 0.0, "y": 0.0, "z": 0.0}
    x = float(pos.get("x", 0.0))
    y = float(pos.get("y", 0.0))
    z = float(pos.get("z", 0.0))
    return {"x": round(x, 4), "y": round(-z, 4), "z": round(y, 4)}


def _godot_to_upbge_scale(scale):
    """Convert axis-aligned scale from Godot to UPBGE/Blender axes."""
    if not isinstance(scale, dict):
        return {"x": 1.0, "y": 1.0, "z": 1.0}
    sx = float(scale.get("x", 1.0))
    sy = float(scale.get("y", 1.0))
    sz = float(scale.get("z", 1.0))
    # x->x, y(up)->z, z(depth)->y (sign irrelevant for scale)
    return {"x": round(sx, 4), "y": round(sz, 4), "z": round(sy, 4)}


def _godot_to_upbge_transform(transform):
    """Convert a Godot-style transform dict to UPBGE/Blender axes.

    Note: rotation conversion is NOT applied here (kept as-is) because
    proper handedness + basis conversion depends on your consumer.
    """
    if not isinstance(transform, dict):
        transform = {}
    pos_g = transform.get("position") or {"x": 0.0, "y": 0.0, "z": 0.0}
    rot = transform.get("rotation") or {"x": 0, "y": 0, "z": 0}
    scl_g = transform.get("scale") or {"x": 1.0, "y": 1.0, "z": 1.0}
    return {
        "position": _godot_to_upbge_pos(pos_g),
        "rotation": rot,
        "scale": _godot_to_upbge_scale(scl_g),
    }
# === END COORD-CONVERT v1 ===
'''.lstrip("\n")


NEW_FALLBACK_FUNC = r'''
def _fallback_entity(eid: str, ent: Dict, concept_type: str, index: int, total: int) -> Dict[str, Any]:
    """Produce minimal render data when the bridge isn't available.

    Output conventions:
      - "transform" is Godot-space (for Godot renderer).
      - "position" is UPBGE/Blender-space (for UPBGE spawners).
      - "position_godot" preserves the original Godot position.
      - "transform_upbge" provides a converted transform for UPBGE/Blender.
    """
    pos = _auto_layout_position(index, total)

    out = {
        "entity_id": eid,
        "name": str(ent.get("name") or eid),
        "zw_concept": concept_type,
        "inferred_type": concept_type,
        "ap_profile": "generic_static",
        "placeholder_mesh": "capsule",
        "skin_3d_id": None,
        "color": {"r": 1.0, "g": 0.0, "b": 1.0},
        "color_hex": "#ff00ff",
        "transform": {
            "position": pos,
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 0.5, "y": 1.8, "z": 0.5},
        },
        # position is overwritten below to be UPBGE/Blender-space
        "position": pos,
        "collision_role": "solid",
        "semantic_tags": ["fallback"],
        "is_placeholder": True,
        "source_data": {"raw_concept": concept_type},
    }

    # Export UPBGE-friendly coordinates without breaking Godot consumers.
    out["position_godot"] = out["transform"]["position"]
    out["position"] = _godot_to_upbge_pos(out["transform"]["position"])
    out["transform_upbge"] = _godot_to_upbge_transform(out["transform"])
    return out
'''.lstrip("\n")


def _repo_root_from_this_file() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent


def _find_top_level_block(text: str, start_pos: int) -> tuple[int, int]:
    m_next = re.search(r"^(?:def|class)\s+\w+\s*\(", text[start_pos + 1 :], flags=re.M)
    if not m_next:
        return (start_pos, len(text))
    end = start_pos + 1 + m_next.start()
    return (start_pos, end)


def main() -> int:
    root = _repo_root_from_this_file()
    target = root / "godotsim" / "bridge_integration.py"

    if not target.exists():
        print(f"[PATCH] ERROR: cannot find {target}")
        return 2

    raw = target.read_text(encoding="utf-8")

    if PATCH_MARKER in raw:
        print("[PATCH] bridge_integration.py already has COORD-CONVERT v1 marker. Nothing to do.")
        return 0

    patched = raw

    # 1) Insert helpers before _auto_layout_position()
    m_layout = re.search(r"^def\s+_auto_layout_position\s*\(", patched, flags=re.M)
    if not m_layout:
        print("[PATCH] ERROR: could not find def _auto_layout_position(...)")
        return 3
    patched = patched[: m_layout.start()] + HELPERS_BLOCK + "\n\n" + patched[m_layout.start() :]

    # 2) Replace the UPBGE compatibility assignment inside bridge_entities_for_scene
    #    from: result["position"] = result["transform"]["position"]
    #    to: add position_godot + converted position + transform_upbge
    def _replace_position_line(txt: str) -> str:
        pat = re.compile(
            r'^(?P<indent>[ \t]*)result\["position"\]\s*=\s*result\["transform"\]\["position"\]\s*$',
            flags=re.M,
        )
        m = pat.search(txt)
        if not m:
            print('[PATCH] ERROR: could not find line: result["position"] = result["transform"]["position"]')
            return txt

        indent = m.group("indent")
        repl = (
            f'{indent}godot_pos = (result.get("transform") or {{}}).get("position") or {{"x": 0.0, "y": 0.0, "z": 0.0}}\n'
            f'{indent}result["position_godot"] = godot_pos\n'
            f'{indent}result["position"] = _godot_to_upbge_pos(godot_pos)\n'
            f'{indent}result["transform_upbge"] = _godot_to_upbge_transform(result.get("transform") or {{}})\n'
        )
        return txt[: m.start()] + repl + txt[m.end() :]

    patched2 = _replace_position_line(patched)
    if patched2 == patched:
        # error already printed
        return 4
    patched = patched2

    # 3) Replace entire _fallback_entity(...) function with upgraded version
    m_fb = re.search(r"^def\s+_fallback_entity\s*\(", patched, flags=re.M)
    if not m_fb:
        print("[PATCH] ERROR: could not locate def _fallback_entity(...)")
        return 5

    fb_start, fb_end = _find_top_level_block(patched, m_fb.start())
    patched = patched[:fb_start] + NEW_FALLBACK_FUNC + "\n\n" + patched[fb_end:].lstrip("\n")

    # 4) Add marker so we can detect idempotence
    # (Already included in HELPERS_BLOCK)

    # Compile check
    try:
        compile(patched, str(target), "exec")
    except SyntaxError as e:
        print("[PATCH] ERROR: patch produced invalid Python. Aborting.")
        print("        ", e)
        return 6

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_suffix(target.suffix + f".bak.{ts}")
    backup.write_text(raw, encoding="utf-8")
    target.write_text(patched, encoding="utf-8")

    print("[PATCH] OK:", target)
    print("[PATCH] Backup:", backup)
    print("[PATCH] Verify with:")
    print("        grep -n \"COORD-CONVERT v1\" -n godotsim/bridge_integration.py")
    print("        grep -n \"position_godot\\|transform_upbge\" -n godotsim/bridge_integration.py | head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
