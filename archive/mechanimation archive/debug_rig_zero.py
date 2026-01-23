#!/usr/bin/env python3
"""
DEBUG TOOL: Phase 1 - Freeze EVERYTHING
Forces every joint to 0 rotation and 0 translation to verify raw rig alignment.
"""

import json
import math
import argparse
import sys
from pathlib import Path
from PIL import Image

def load_rig(rig_path):
    with open(rig_path) as f:
        rig_data = json.load(f)
    parts_dir = Path(rig_path).parent / rig_data['parts_dir']
    
    def load_part(name, defn, parent=""):
        path = f"{parent}/{name}" if parent else name
        img_path = parts_dir / defn['image']
        img = Image.open(img_path).convert('RGBA') if img_path.exists() else None
        
        part = {
            'name': name,
            'image': img,
            'pivot': tuple(defn['pivot']),
            'attach': tuple(defn.get('attach')) if defn.get('attach') else None,
            'children': {}
        }
        
        if 'children' in defn:
            for cname, cdef in defn['children'].items():
                part['children'][cname] = load_part(cname, cdef, path)
        return part
        
    root_name = list(rig_data['hierarchy'].keys())[0]
    return load_part(root_name, rig_data['hierarchy'][root_name])

def render_part(part, pose, canvas, wx, wy, prot=0):
    p_pose = pose.get(part['name'], {})
    lrot = p_pose.get('rotation', 0)
    tx, ty = p_pose.get('translate_x', 0), p_pose.get('translate_y', 0)
    trot = prot + lrot
    wx += tx; wy += ty
    
    img, piv = part['image'], part['pivot']
    if img:
        rot_img = img.rotate(-trot, expand=True, resample=Image.BICUBIC)
        rad = math.radians(trot)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        cx, cy = rot_img.width / 2, rot_img.height / 2
        pdx, pdy = piv[0] - img.width / 2, piv[1] - img.height / 2
        rpdx = pdx * cos_a - pdy * sin_a
        rpdy = pdx * sin_a + pdy * cos_a
        canvas.paste(rot_img, (int(wx-cx-rpdx), int(wy-cy-rpdy)), rot_img)
        
        # Children alignment
        for cname, cpart in part['children'].items():
            if cpart.get('attach'):
                sx, sy = cpart['attach']
                sdx, sdy = sx - piv[0], sy - piv[1]
                rsdx, rsdy = sdx * cos_a - sdy * sin_a, sdx * sin_a + sdy * cos_a
                render_part(cpart, pose, canvas, wx + rsdx, wy + rsdy, trot)
            else:
                render_part(cpart, pose, canvas, wx, wy, trot)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rig', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    
    rig = load_rig(args.rig)
    size = 512
    
    # 🔥 PHASE 1: HARD-OVERRIDE ZERO POSE
    # We create a dictionary covering every possible part name in the character v2 rig
    parts_list = [
        'torso', 'head', 'left_arm', 'left_wrist', 'left_hand', 
        'right_arm', 'right_wrist', 'right_hand', 'hip', 
        'left_thigh', 'left_shin', 'left_foot', 
        'right_thigh', 'right_shin', 'right_foot'
    ]
    zero_pose = {part: {'rotation': 0, 'translate_x': 0, 'translate_y': 0} for part in parts_list}
    
    # Create a single check frame
    frame = Image.new('RGBA', (size, size), (128, 128, 128, 255)) # Gray background for visibility
    render_part(rig, zero_pose, frame, size // 2, size // 2)
    
    frame.save(args.out)
    print(f"✅ ZERO-POSE Rendered to {args.out}")
    print("Check this image: If legs cross or appear misaligned, the RIG (JSON pivots/attach) is the culprit.")

if __name__ == '__main__':
    main()
