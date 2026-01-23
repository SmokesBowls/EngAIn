#!/usr/bin/env python3
"""
DEBUG TOOL: Phase 2 - Move ONE variable at a time
Allows surgical testing of specific motion components.
"""

import json
import math
import argparse
import sys
from pathlib import Path
from PIL import Image
from biomechanical_constraints_fixed import BiomechanicalConstraintsFixed

def load_rig(rig_path):
    with open(rig_path) as f:
        rig_data = json.load(f)
    parts_dir = Path(rig_path).parent / rig_data['parts_dir']
    def load_part(name, defn, parent=""):
        path = f"{parent}/{name}" if parent else name
        img = Image.open(parts_dir / defn['image']).convert('RGBA')
        part = {'name': name, 'image': img, 'pivot': tuple(defn['pivot']),
                'attach': tuple(defn.get('attach')) if defn.get('attach') else None, 'children': {}}
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
    rot_img = img.rotate(-trot, expand=True, resample=Image.BICUBIC)
    rad = math.radians(trot)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    cx, cy = rot_img.width/2, rot_img.height/2
    pdx, pdy = piv[0] - img.width/2, piv[1] - img.height/2
    rpdx = pdx*cos_a - pdy*sin_a
    rpdy = pdx*sin_a + pdy*cos_a
    canvas.paste(rot_img, (int(wx-cx-rpdx), int(wy-cy-rpdy)), rot_img)
    for cname, cpart in part['children'].items():
        if cpart.get('attach'):
            sx, sy = cpart['attach']
            sdx, sdy = sx-piv[0], sy-piv[1]
            rsdx, rsdy = sdx*cos_a-sdy*sin_a, sdx*sin_a+sdy*cos_a
            render_part(cpart, pose, canvas, wx+rsdx, wy+rsdy, trot)
        else:
            render_part(cpart, pose, canvas, wx, wy, trot)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rig', required=True)
    parser.add_argument('--test', choices=['lift_only', 'rotation_only', 'ik_no_bias'], required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    
    rig = load_rig(args.rig)
    size = 512
    constraints = BiomechanicalConstraintsFixed()
    
    # We'll render 4 frames representing 25%, 50%, 75%, 100% of a motion 'event'
    sheet = Image.new('RGBA', (size * 4, size), (0, 0, 0, 0))
    
    for i in range(4):
        t = (i + 1) / 4.0
        pose = {}
        
        if args.test == 'lift_only':
            # Only lift the left leg straight up (Forward walk style)
            # We bypass the full constraint system and just call solve_ik
            target_y = constraints.ground_y - (t * 30) # Lift up to 30px
            thigh_rot, knee_flex = constraints.solve_ik(0, target_y)
            pose = {
                'left_thigh': {'rotation': thigh_rot},
                'left_shin': {'rotation': knee_flex},
                'left_foot': {'rotation': -(thigh_rot + knee_flex)}
            }
        
        elif args.test == 'rotation_only':
            # Only rotate the left thigh, no IK
            pose = {
                'left_thigh': {'rotation': t * 45} # Rotate up to 45 deg
            }
            
        elif args.test == 'ik_no_bias':
            # Pure IK without any intent-preservation interference
            # Left leg lifts, right leg stays flat
            p = t * 0.5 # Stride phase 0->0.5
            pose = constraints.apply_biomechanical_constraints({}, p, 1.0)
            # Force intent_weight to 0 by passing empty pose
            
        frame = Image.new('RGBA', (size, size), (128, 128, 128, 255))
        render_part(rig, pose, frame, size // 2, size // 2)
        sheet.paste(frame, (i * size, 0))
        
    sheet.save(args.out)
    print(f"✅ TEST '{args.test}' saved to {args.out}")

if __name__ == '__main__':
    main()
