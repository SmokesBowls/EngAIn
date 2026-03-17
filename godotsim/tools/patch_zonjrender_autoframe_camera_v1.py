#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import sys
import tempfile
import re


TARGET = Path("/home/burdens/burdens_of_a_forgotten_past/EngAIn/godotroot/zonjrender/SemanticRenderer.gd")
MARK = "# [PATCH auto-frame-camera V1]"


def backup(path: Path, s: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak.{ts}")
    b.write_text(s, encoding="utf-8")
    return b


def atomic_write(path: Path, s: str) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(s)
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing {TARGET}", file=sys.stderr)
        return 2

    s0 = TARGET.read_text(encoding="utf-8", errors="strict")
    if MARK in s0:
        print(f"OK: already patched: {TARGET}")
        return 0

    s = s0

    # 1) Add camera export knobs after enable_fast_transforms export
    needle = "@export var enable_fast_transforms: bool = true\n"
    if needle not in s:
        print("ERROR: expected enable_fast_transforms export not found.", file=sys.stderr)
        return 3

    insert = (
        needle +
        "\n" +
        f"{MARK}\n" +
        "@export var auto_frame_camera_on_spawn: bool = true\n" +
        "@export var camera_height: float = 10.0\n" +
        "@export var camera_distance: float = 18.0\n" +
        "@export var camera_look_at_y: float = 1.0\n"
    )
    s = s.replace(needle, insert, 1)

    # 2) After spawning entities, call frame function
    # Find the line: _spawn_entities(bridge_entities)
    m = re.search(r"^\s*_spawn_entities\(bridge_entities\)\s*$", s, flags=re.M)
    if not m:
        print("ERROR: could not find _spawn_entities(bridge_entities) call.", file=sys.stderr)
        return 4

    # Insert right after that line
    line_end = s.find("\n", m.end())
    if line_end == -1:
        line_end = len(s)

    indent = re.match(r"^(\s*)", m.group(0)).group(1)
    call = (
        "\n"
        f"{indent}if auto_frame_camera_on_spawn:\n"
        f"{indent}\t_frame_camera_to_entities(bridge_entities)\n"
    )
    s = s[:line_end] + call + s[line_end:]

    # 3) Append helper functions (only if missing)
    if "func _frame_camera_to_entities(" not in s:
        helpers = r'''
func _frame_camera_to_entities(ents: Array) -> void:
	# Compute centroid + radius from entity dicts (position or transform.position).
	if ents.is_empty():
		return

	var pts: Array[Vector3] = []
	for e in ents:
		if not (e is Dictionary):
			continue
		var posd: Dictionary = {}
		if e.has("position") and e.get("position") is Dictionary:
			posd = e.get("position")
		elif e.has("transform") and e.get("transform") is Dictionary:
			var tr: Dictionary = e.get("transform")
			if tr.has("position") and tr.get("position") is Dictionary:
				posd = tr.get("position")
		if posd.is_empty():
			continue
		var p := Vector3(
			float(posd.get("x", 0.0)),
			float(posd.get("y", 0.0)),
			float(posd.get("z", 0.0))
		)
		pts.append(p)

	if pts.is_empty():
		return

	var center := Vector3.ZERO
	for p in pts:
		center += p
	center /= float(pts.size())

	var radius := 1.0
	for p in pts:
		radius = max(radius, center.distance_to(p))

	var cam := _get_primary_camera()
	if cam == null:
		print("[SemanticRenderer] No Camera3D found to frame")
		return

	# Place camera at a stable offset behind and above.
	var look := center + Vector3(0.0, camera_look_at_y, 0.0)
	var dist := max(camera_distance, radius * 1.6)
	var h := max(camera_height, radius * 0.6 + 2.0)

	# Back along +Z by default (works with your grid layout), adjust if needed later.
	cam.global_position = look + Vector3(0.0, h, dist)
	cam.look_at(look, Vector3.UP)


func _get_primary_camera() -> Camera3D:
	# 1) active viewport camera
	var cam := get_viewport().get_camera_3d()
	if cam:
		return cam

	# 2) search current scene
	var root := get_tree().current_scene
	if root:
		var cams := root.find_children("*", "Camera3D", true, false)
		if cams.size() > 0 and cams[0] is Camera3D:
			return cams[0] as Camera3D

	# 3) search parents
	var p := get_parent()
	while p:
		if p is Camera3D:
			return p as Camera3D
		p = p.get_parent()

	return null
'''
        s = s.rstrip() + "\n\n" + helpers.strip("\n") + "\n"

    b = backup(TARGET, s0)
    atomic_write(TARGET, s)

    print(f"PATCHED: {TARGET}")
    print(f"BACKUP : {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

