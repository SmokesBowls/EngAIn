#!/usr/bin/env fish

cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/trixelworld; or exit 1

python3 trixel_brush_adapter.py data/brushes; or exit 1
python3 debugerrors.py; or exit 1
python3 debugnames.py; or exit 1
python3 test_spacing_ratio.py; or exit 1
python3 test_parse.py; or exit 1
python3 engine_debug_mr.py data /tmp/trixel_out; or exit 1
python3 trixel_demo_mr.py data /tmp/trixel_demo; or exit 1
python3 world_tree_mr.py data /tmp/trixel_trees; or exit 1
python3 stress_scene_mr.py data /tmp/trixel_stress; or exit 1
