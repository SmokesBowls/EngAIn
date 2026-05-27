"""
trixel_render_bridge.py

Bridge between godotengain's scene_server pipeline and trixelcomposer's
render pipeline.

Zero changes to any existing file.

-- Wiring point (when ready) ----------------------------------------
In godotengain/engainos/core/scene_server.py, line 235:

    CURRENT:
        recipe = _build_art_recipe(scene_id, scene)

    REPLACE WITH:
        import sys, pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parents[3] / "trixelcomposer"))
        from trixel_render_bridge import compile_scene
        recipe = compile_scene(scene_id, scene)

    That is the entire change required. No other modification.
---------------------------------------------------------------------

Pipeline (this file):
    godotengain scene_data  (terrain_family, environment, entities)
          ↓  _translate()
    trixelcomposer scene_doc  (terrain, environment, entities)
          ↓  compile_recipe()
    recipe JSON
          ↓  execute_recipe()  [only when render=True or called from CLI]
    terrain PNG  +  entity_layer sidecar JSON
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Path resolution — bridge works whether imported or run as a script
# ---------------------------------------------------------------------------

_BRIDGE_DIR = Path(__file__).parent.resolve()
if str(_BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(_BRIDGE_DIR))

from scene_server import compile_recipe          # trixelcomposer/scene_server.py
from terminal_trixel import TerminalTrixelComposer  # trixelcomposer/terminal_trixel.py

# Default output directory for rendered tiles — override via TRIXEL_TILE_DIR env var
import os
DEFAULT_TILE_DIR = os.environ.get(
    "TRIXEL_TILE_DIR",
    str(_BRIDGE_DIR / ".zw" / "tiles"),
)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def _translate(scene_id: str, scene_data: Dict[str, Any]) -> Dict[str, Any]:
    """Translate godotengain scene_data to trixelcomposer scene_doc.

    Handles:
        terrain_family  → terrain   (godotengain uses terrain_family)
        environment     → environment (pass-through)
        entities        → entities  (same structure: list with position.x)
    """
    return {
        "scene_id":     scene_id,
        "terrain":      scene_data.get("terrain_family",
                                       scene_data.get("terrain", "default")),
        "environment":  scene_data.get("environment", "unknown"),
        "entity_count": len(scene_data.get("entities", [])),
        "entities":     scene_data.get("entities", []),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compile_scene(scene_id: str, scene_data: Dict[str, Any]) -> Dict[str, Any]:
    """Drop-in replacement for godotengain's _build_art_recipe().

    Same input signature. Same output structure (scene_id, terrain, passes, ...).
    Does NOT render to PNG — compile only.
    """
    scene_doc = _translate(scene_id, scene_data)
    return compile_recipe(scene_doc)


def render_scene(
    scene_id: str,
    scene_data: Dict[str, Any],
    out_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Compile recipe AND render to PNG + entity layer sidecar.

    Returns:
        {
            "recipe":       dict,           # compiled recipe
            "png":          str | None,     # absolute path to terrain PNG
            "entity_layer": str | None,     # absolute path to entity JSON sidecar
            "out_dir":      str,
        }
    """
    out_path = Path(out_dir or DEFAULT_TILE_DIR)
    scene_doc = _translate(scene_id, scene_data)
    recipe = compile_recipe(scene_doc)

    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, dir=_BRIDGE_DIR / ".zw"
    ) as f:
        json.dump(recipe, f)
        tmp = Path(f.name)

    try:
        composer = TerminalTrixelComposer()
        composer.execute_recipe(str(tmp), str(out_path))
    finally:
        tmp.unlink(missing_ok=True)

    # Locate outputs by naming convention from execute_recipe
    png_candidates = sorted(
        out_path.glob(f"trixel_{scene_id}_*.png"), reverse=True
    )
    entity_candidates = sorted(
        out_path.glob(f"entities_{scene_id}.json"), reverse=True
    )

    return {
        "recipe":       recipe,
        "png":          str(png_candidates[0])    if png_candidates    else None,
        "entity_layer": str(entity_candidates[0]) if entity_candidates else None,
        "out_dir":      str(out_path),
    }


# ---------------------------------------------------------------------------
# CLI  —  lets godotengain call this as a subprocess with no Python imports
#
#   python3 trixel_render_bridge.py --scene lava_pit_003 \
#       --data '{"terrain_family":"volcano","environment":"coastal"}' \
#       --out /tmp/tiles/
#
#   python3 trixel_render_bridge.py --scene shore_01 --compile-only
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="trixelcomposer render bridge — compile or render a scene tile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python3 trixel_render_bridge.py --scene lava_pit_003\n"
            "  python3 trixel_render_bridge.py --scene shore_01 "
            "--data '{\"terrain_family\":\"beach\",\"environment\":\"coastal\"}'\n"
            "  python3 trixel_render_bridge.py --scene grove_02 --out /tmp/tiles/ --compile-only"
        ),
    )
    parser.add_argument("--scene",        required=True,  help="scene_id")
    parser.add_argument("--data",         default="{}",   help="JSON scene_data string (godotengain format)")
    parser.add_argument("--out",          default=None,   help="Output directory for PNG + entity layer")
    parser.add_argument("--compile-only", action="store_true",
                        help="Compile recipe only — no PNG render")
    args = parser.parse_args()

    try:
        scene_data = json.loads(args.data)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid --data JSON: {exc}"}))
        sys.exit(1)

    try:
        if args.compile_only:
            result = {"recipe": compile_scene(args.scene, scene_data)}
        else:
            result = render_scene(args.scene, scene_data, args.out)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        import traceback
        print(json.dumps({"error": str(exc), "trace": traceback.format_exc()}))
        sys.exit(1)
