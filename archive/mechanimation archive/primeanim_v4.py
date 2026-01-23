#!/usr/bin/env python3
"""
Mechanimation v0.4 - Biomechanical Animation System
Main Renderer script.
"""

import json
import math
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

# Import biomechanical layer
try:
    from biomechanical_constraints import BiomechanicalConstraints, BIOMECH_PRESETS
except ImportError:
    print("⚠️ Error: biomechanical_constraints.py not found.")
    sys.exit(1)

def load_biomech_rig(rig_path):
    with open(rig_path) as f:
        rig_data = json.load(f)
    
    parts_dir = Path(rig_path).parent / rig_data['parts_dir']
    
    def load_part_recursive(part_name, part_def, parent_path=""):
        full_path = f"{parent_path}/{part_name}" if parent_path else part_name
        
        img_path = parts_dir / part_def['image']
        img = Image.open(img_path).convert('RGBA') if img_path.exists() else None
        
        part = {
            'name': part_name,
            'path': full_path,
            'image': img,
            'pivot': tuple(part_def['pivot']),
            'socket': tuple(part_def['socket']) if part_def.get('socket') else None,
            'joint_type': part_def.get('joint_type', 'hinge'),
            'children': {}
        }
        
        if 'children' in part_def:
            for child_name, child_def in part_def['children'].items():
                part['children'][child_name] = load_part_recursive(child_name, child_def, full_path)
        
        return part
    
    root_name = list(rig_data['hierarchy'].keys())[0]
    root_def = rig_data['hierarchy'][root_name]
    return load_part_recursive(root_name, root_def)

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def interpolate_pose(keyframes, time):
    if not keyframes: return {}
    before = after = None
    for kf in keyframes:
        if kf['time'] <= time: before = kf
        if kf['time'] >= time and after is None: after = kf
    if not before: before = keyframes[0]
    if not after: after = keyframes[-1]
    if before['time'] == after['time']: return before['poses']
    
    t = (time - before['time']) / (after['time'] - before['time'])
    t_eased = ease_in_out_cubic(t)
    
    result = {}
    all_parts = set(before['poses'].keys()) | set(after['poses'].keys())
    for part in all_parts:
        b_rot = before['poses'].get(part, {}).get('rotation', 0)
        a_rot = after['poses'].get(part, {}).get('rotation', 0)
        result[part] = {'rotation': b_rot + (a_rot - b_rot) * t_eased}
    return result

def render_biomech_part(part, pose, canvas, world_x, world_y, parent_rotation=0,
                       debug=False, level=0):
    part_pose = pose.get(part['name'], {})
    local_rotation = part_pose.get('rotation', 0)
    tx = part_pose.get('translate_x', 0)
    ty = part_pose.get('translate_y', 0)
    
    total_rotation = parent_rotation + local_rotation
    
    # Apply translation
    wx = world_x + tx
    wy = world_y + ty
    
    img = part['image']
    pivot = part['pivot']
    
    if img:
        rotated = img.rotate(-total_rotation, expand=True, resample=Image.BICUBIC)
        
        rad = math.radians(total_rotation)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        
        cx, cy = img.width / 2, img.height / 2
        pdx, pdy = pivot[0] - cx, pivot[1] - cy
        
        rpdx = pdx * cos_a - pdy * sin_a
        rpdy = pdx * sin_a + pdy * cos_a
        
        px = int(wx - rotated.width / 2 - rpdx)
        py = int(wy - rotated.height / 2 - rpdy)
        
        canvas.paste(rotated, (px, py), rotated)
    
    # Children alignment
    for child_name, child_part in part['children'].items():
        if child_part.get('socket'):
            sx, sy = child_part['socket']
            sdx, sdy = sx - pivot[0], sy - pivot[1]
            
            # Use current total_rotation to place children
            rad = math.radians(total_rotation)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            rsdx = sdx * cos_a - sdy * sin_a
            rsdy = sdx * sin_a + sdy * cos_a
            
            cwx, cwy = wx + rsdx, wy + rsdy
            render_biomech_part(child_part, pose, canvas, cwx, cwy, total_rotation, debug, level + 1)
        else:
            render_biomech_part(child_part, pose, canvas, wx, wy, total_rotation, debug, level + 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['animate'])
    parser.add_argument('--rig', required=True)
    parser.add_argument('--anim', required=True)
    parser.add_argument('--frames', type=int, default=12)
    parser.add_argument('--cols', type=int, default=4)
    parser.add_argument('--size', type=int, default=512)
    parser.add_argument('--preset', default='human_walk')
    parser.add_argument('--ground', type=int, default=0)
    parser.add_argument('--out', required=True)
    parser.add_argument('--debug', action='store_true')
    
    args = parser.parse_args()
    
    if args.command == 'animate':
        rig = load_biomech_rig(args.rig)
        anim_data = json.load(open(args.anim))
        
        duration = anim_data['duration']
        keyframes = anim_data['keyframes']
        
        biomech = BiomechanicalConstraints(BIOMECH_PRESETS.get(args.preset))
        
        rows = (args.frames + args.cols - 1) // args.cols
        sheet = Image.new('RGBA', (args.cols * args.size, rows * args.size), (0, 0, 0, 0))
        
        for i in range(args.frames):
            t = (i / (args.frames - 1)) * duration if args.frames > 1 else 0
            intent_pose = interpolate_pose(keyframes, t)
            final_pose = biomech.apply_biomechanical_constraints(intent_pose, t, duration)
            
            frame = Image.new('RGBA', (args.size, args.size), (0, 0, 0, 0))
            render_biomech_part(rig, final_pose, frame, args.size//2, args.size//2)
            
            x = (i % args.cols) * args.size
            y = (i // args.cols) * args.size
            sheet.paste(frame, (x, y))
            
        sheet.save(args.out)
        print(f"✅ Spritesheet saved to {args.out}")

if __name__ == '__main__':
    main()
