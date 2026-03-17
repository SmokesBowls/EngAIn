from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import bpy

from _common import load_params, ok, fail


def _clear_world_nodes(world: bpy.types.World) -> bpy.types.NodeTree:
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return nt


def _save_or_fail(result_json: Path) -> None:
    try:
        bpy.ops.wm.save_mainfile()
    except Exception as exc:
        fail(result_json, f"Failed to save .blend: {exc}")
        raise


def main() -> None:
    params, _meta, result_json = load_params()

    mode = str(params.get("mode", "solid"))
    hdri_path: Optional[str] = params.get("hdri_path")
    hdri_strength = float(params.get("hdri_strength", 1.0))
    hdri_rotation_deg = float(params.get("hdri_rotation_deg", 0.0))
    background_color = params.get("background_color") or [0.05, 0.05, 0.05, 1.0]

    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world

    nt = _clear_world_nodes(world)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (600, 0)

    result_payload = {"mode": mode}

    if mode == "transparent":
        scene.render.film_transparent = True
        bg = nt.nodes.new("ShaderNodeBackground")
        bg.inputs["Color"].default_value = tuple(background_color)
        bg.inputs["Strength"].default_value = 0.1
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
        result_payload["color"] = background_color

    elif mode == "solid":
        scene.render.film_transparent = False
        bg = nt.nodes.new("ShaderNodeBackground")
        bg.inputs["Color"].default_value = tuple(background_color)
        bg.inputs["Strength"].default_value = 1.0
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
        result_payload["color"] = background_color

    elif mode == "hdri":
        scene.render.film_transparent = False
        if not hdri_path:
            fail(result_json, "mode='hdri' requires hdri_path")
            return
        p = Path(hdri_path).expanduser().resolve()
        if not p.exists():
            fail(result_json, f"HDRI not found: {p}")
            return

        texcoord = nt.nodes.new("ShaderNodeTexCoord")
        texcoord.location = (-200, 0)
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.location = (50, 0)
        mapping.inputs["Rotation"].default_value[2] = math.radians(hdri_rotation_deg)
        tex = nt.nodes.new("ShaderNodeTexEnvironment")
        tex.location = (250, 0)
        tex.image = bpy.data.images.load(str(p), check_existing=True)
        bg = nt.nodes.new("ShaderNodeBackground")
        bg.location = (450, 0)
        bg.inputs["Strength"].default_value = hdri_strength

        nt.links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], bg.inputs["Color"])
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

        result_payload.update({"hdri": str(p), "strength": hdri_strength, "rotation_deg": hdri_rotation_deg})

    elif mode == "sky":
        scene.render.film_transparent = False
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.location = (0, 0)
        sky.sun_elevation = math.radians(float(params.get("sky_sun_elevation_deg", 45.0)))
        sky.sun_rotation = math.radians(float(params.get("sky_sun_rotation_deg", 0.0)))

        bg = nt.nodes.new("ShaderNodeBackground")
        bg.location = (250, 0)
        bg.inputs["Strength"].default_value = 1.0

        nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
        nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    else:
        fail(result_json, f"Unknown mode: {mode!r}")
        return

    try:
        _save_or_fail(result_json)
    except Exception:
        return

    ok(result_json, result=result_payload)


main()
