import sys
from pathlib import Path
from lisp_parser_mr import parse_sexpr, find_node, get_value

text = """
# GIMP tool preset file
(icon-name "gimp-tool-paintbrush")
(name "Pencil Soft")
(tool-options "GimpPaintOptions"
    (tool "gimp-paintbrush-tool")
    (foreground (color-rgb 1.0 0.5 0.5))
    (opacity 0.8)
    (brush "Brush Name")
    (dynamics "Dynamics Name")
    (gradient "Gradient Name")
    (brush-size 15.0)
    (application-mode "incremental")
    (use-jitter yes)
    (dynamics-enabled yes)
    (fade-length 20.0)
    (fade-unit "percent"))
(use-fg-bg yes)
(use-brush yes)
(use-dynamics yes)
(use-gradient yes)
(use-pattern yes)
(use-palette yes)
(use-font yes)
# end of GIMP tool preset file
"""

tree = parse_sexpr(text)
opts = find_node(tree, "tool-options")
fg = get_value(opts, "foreground")
print("Tree:", tree)
print("Opts:", opts)
print("Foreground:", fg)
