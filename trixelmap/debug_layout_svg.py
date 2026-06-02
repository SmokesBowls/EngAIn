#!/usr/bin/env python3
"""
trixelmap/debug_layout_svg.py
Pure functional visualizer: Reads solved layout + authority graph → debug SVG.
No external dependencies. Uses standard image coordinates (Y=0 top, Y increases down).
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple

def generate_debug_svg(layout_path: str, authority_path: str, output_path: str):
    layout = json.loads(Path(layout_path).read_text())
    authority = json.loads(Path(authority_path).read_text())
    
    regions = layout.get("regions", {})
    edges = authority.get("edges", [])
    grid_size = layout.get("grid_size", 100)
    
    scale = 6  # pixels per grid unit
    margin = 30
    svg_w = svg_h = grid_size * scale + margin * 2
    
    def to_svg(x: float, y: float) -> str:
        return f"{margin + x * scale},{margin + y * scale}"
    
    lines = [f'<svg width="{svg_w}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg">']
    lines.append(f'<rect width="{svg_w}" height="{svg_h}" fill="#f8f9fa"/>')
    lines.append(f'<rect x="{margin}" y="{margin}" width="{grid_size*scale}" height="{grid_size*scale}" fill="#ffffff" stroke="#dee2e6" stroke-width="2"/>')
    
    # Grid lines
    for i in range(0, grid_size + 1, 20):
        pos = margin + i * scale
        lines.append(f'<line x1="{pos}" y1="{margin}" x2="{pos}" y2="{margin+grid_size*scale}" stroke="#f1f3f5" stroke-width="1"/>')
        lines.append(f'<line x1="{margin}" y1="{pos}" x2="{margin+grid_size*scale}" y2="{pos}" stroke="#f1f3f5" stroke-width="1"/>')
        lines.append(f'<text x="{pos}" y="{margin-5}" font-size="9" fill="#868e96" text-anchor="middle">{i}</text>')
        lines.append(f'<text x="{margin-5}" y="{pos+3}" font-size="9" fill="#868e96" text-anchor="end">{i}</text>')
    
    # Draw regions
    colors = {"landmark": "#ffd43b", "valley": "#69db7c", "hills": "#ffa94d", "default": "#ced4da"}
    for rid, rdata in regions.items():
        c = rdata["centroid"]
        b = rdata["bounds"]
        cx, cy = c["x"], c["y"]
        color = colors.get(rdata.get("terrain_class", "default"), colors["default"])
        
        # Bounds rectangle
        lines.append(f'<rect x="{to_svg(b["x_min"], b["y_min"]).split(",")[0]}" y="{to_svg(b["x_min"], b["y_min"]).split(",")[1]}" '
                     f'width="{(b["x_max"]-b["x_min"])*scale}" height="{(b["y_max"]-b["y_min"])*scale}" '
                     f'fill="{color}" stroke="#343a40" stroke-width="1.5" rx="4"/>')
        
        # Centroid dot + label
        lines.append(f'<circle cx="{to_svg(cx, cy)}" r="4" fill="#e03131"/>')
        lines.append(f'<text x="{to_svg(cx, cy)}" y="{float(to_svg(cx, cy).split(",")[1])-8}" '
                     f'font-size="11" fill="#212529" text-anchor="middle" font-weight="bold">{rid.replace("_", " ")}</text>')
    
    # Draw relationship arrows
    for e in edges:
        a = regions.get(e["from"])
        b = regions.get(e["to"])
        if not a or not b: continue
        
        ca, cb = a["centroid"], b["centroid"]
        x1, y1 = float(to_svg(ca["x"], ca["y"]).split(",")[0]), float(to_svg(ca["x"], ca["y"]).split(",")[1])
        x2, y2 = float(to_svg(cb["x"], cb["y"]).split(",")[0]), float(to_svg(cb["x"], cb["y"]).split(",")[1])
        
        # Arrow styling based on relation type
        stroke = "#e03131" if "north" in e["relation"] or "above" in e["relation"] else "#1971c2"
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="2" marker-end="url(#arrow)"/>')
        
        # Label at midpoint
        mx, my = (x1+x2)/2, (y1+y2)/2
        lines.append(f'<text x="{mx}" y="{my-6}" font-size="9" fill="#495057" text-anchor="middle" '
                     f'font-style="italic">{e["relation"]} (s:{e.get("strength",0.5):.1f})</text>')
    
    lines.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#495057"/></marker></defs>')
    lines.append('</svg>')
    
    Path(output_path).write_text("\n".join(lines))
    print(f"[debug] SVG written to: {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4:
        generate_debug_svg(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("Usage: python debug_layout_svg.py <resolved_layout.json> <spatial_authority.json> <output.svg>")
