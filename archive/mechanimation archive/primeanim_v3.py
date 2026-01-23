#!/usr/bin/env python3
"""
Mechanimation v0.3.1 - PrimeAnim with Corrected Hierarchy
Fixed: Socket alignment and root translation bobbing
"""

import json
import math
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

# Import constraint solver
from walk_constraints import WalkConstraints, get_preset

# ==================== EASING FUNCTIONS ====================

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

# ==================== RIG LOADER ====================

def load_rig(rig_path):
    with open(rig_path) as f:
        rig_data = json.load(f)
    
    parts_dir = Path(rig_path).parent / rig_data['parts_dir']
    
    def load_part_recursive(part_name, part_def, parent_path=""):
        full_path = f"{parent_path}/{part_name}" if parent_path else part_name
        img_path = parts_dir / part_def['image']
        img = Image.open(img_path).convert('RGBA')
        
        part = {
            'name': part_name,
            'path': full_path,
            'image': img,
            'pivot': tuple(part_def['pivot']),
            'socket': tuple(part_def['socket']) if part_def.get('socket') else None,
            'children': {}
        }
        
        if 'children' in part_def:
            for child_name, child_def in part_def['children'].items():
                part['children'][child_name] = load_part_recursive(child_name, child_def, full_path)
        
        return part
    
    root_name = list(rig_data['hierarchy'].keys())[0]
    root_def = rig_data['hierarchy'][root_name]
    return load_part_recursive(root_name, root_def)

def interpolate_pose(keyframes, time):
    before_kf = after_kf = None
    for kf in keyframes:
        if kf['time'] <= time:
            before_kf = kf
        if kf['time'] >= time and after_kf is None:
            after_kf = kf
    if before_kf is None: before_kf = keyframes[0]
    if after_kf is None: after_kf = keyframes[-1]
    if before_kf['time'] == after_kf['time']: return before_kf['poses']
    
    t = (time - before_kf['time']) / (after_kf['time'] - before_kf['time'])
    t_eased = ease_in_out_cubic(t)
    
    interpolated = {}
    all_parts = set(before_kf['poses'].keys()) | set(after_kf['poses'].keys())
    for part in all_parts:
        b_rot = before_kf['poses'].get(part, {}).get('rotation', 0)
        a_rot = after_kf['poses'].get(part, {}).get('rotation', 0)
        interpolated[part] = {'rotation': b_rot + (a_rot - b_rot) * t_eased}
    
    return interpolated

# ==================== FIXED RENDERING ENGINE ====================

def render_part_recursive(part, pose, canvas, world_x, world_y, parent_rotation=0,
                         joints_canvas=None, debug=False):
    """
    Recursively renders character parts.
    Child parts are aligned to their parent's 'socket' points.
    """
    part_pose = pose.get(part['name'], {})
    local_rotation = part_pose.get('rotation', 0)
    
    # Translations (e.g. for root-bobbing or hip-sway)
    tx = part_pose.get('translate_x', 0)
    ty = part_pose.get('translate_y', 0)
    
    total_rotation = parent_rotation + local_rotation
    
    # Apply local translation
    wx = world_x + tx
    wy = world_y + ty
    
    img = part['image']
    pivot = part['pivot']
    
    # Rotate around center
    rotated = img.rotate(-total_rotation, expand=True, resample=Image.BICUBIC)
    
    rad = math.radians(total_rotation)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    
    # Offset from center to pivot
    cx, cy = img.width / 2, img.height / 2
    pdx, pdy = pivot[0] - cx, pivot[1] - cy
    
    # Rotate pivot offset
    rpdx = pdx * cos_a - pdy * sin_a
    rpdy = pdx * sin_a + pdy * cos_a
    
    # Final paste pos
    px = int(wx - rotated.width / 2 - rpdx)
    py = int(wy - rotated.height / 2 - rpdy)
    
    canvas.paste(rotated, (px, py), rotated)
    
    # Render children
    for child_name, child_part in part['children'].items():
        if child_part.get('socket'):
            # The child defines where it connects to THIS parent
            sx, sy = child_part['socket']
            
            # Vector from THIS part's pivot to the child's socket
            sdx, sdy = sx - pivot[0], sy - pivot[1]
            
            # Rotate that connection vector
            rsdx = sdx * cos_a - sdy * sin_a
            rsdy = sdx * sin_a + sdy * cos_a
            
            # World coordinate for the child's pivot
            cwx, cwy = wx + rsdx, wy + rsdy
            
            if joints_canvas:
                draw = ImageDraw.Draw(joints_canvas)
                r = 12
                draw.ellipse([cwx-r, cwy-r, cwx+r, cwy+r], fill='white')
            
            render_part_recursive(child_part, pose, canvas, cwx, cwy,
                                 total_rotation, joints_canvas, debug)
        else:
            # Fallback: Attach to parent pivot
            render_part_recursive(child_part, pose, canvas, wx, wy,
                                 total_rotation, joints_canvas, debug)

def render_frame(rig, pose, frame_size=512, draw_joints=False, debug=False):
    canvas = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
    joints_canvas = Image.new('RGB', (frame_size, frame_size), 'black') if draw_joints else None
    
    # Start root at center
    cx, cy = frame_size // 2, frame_size // 2
    render_part_recursive(rig, pose, canvas, cx, cy, joints_canvas=joints_canvas, debug=debug)
    
    return canvas, joints_canvas

# ==================== MAIN LOOP ====================

def generate_spritesheet(rig, anim_path, num_frames, cols, frame_size, draw_joints, 
                        preset=None, debug=False):
    with open(anim_path) as f:
        anim_data = json.load(f)
    
    dur = anim_data['duration']
    keyframes = anim_data['keyframes']
    
    constraints = WalkConstraints(get_preset(preset))
    
    rows = (num_frames + cols - 1) // cols
    sheet_w, sheet_h = cols * frame_size, rows * frame_size
    
    sheet = Image.new('RGBA', (sheet_w, sheet_h), (0, 0, 0, 0))
    joints_sheet = Image.new('RGB', (sheet_w, sheet_h), 'black') if draw_joints else None
    
    for i in range(num_frames):
        t = (i / (num_frames - 1)) * dur if num_frames > 1 else 0
        pose = interpolate_pose(keyframes, t)
        
        # APPLY PHYSICS
        pose = constraints.apply_walk_constraints(pose, t, dur, debug=(debug and i == 0))
        
        # RENDER
        frame, joints_frame = render_frame(rig, pose, frame_size, draw_joints, debug=(debug and i == 0))
        
        x = (i % cols) * frame_size
        y = (i // cols) * frame_size
        sheet.paste(frame, (x, y))
        if joints_sheet: joints_sheet.paste(joints_frame, (x, y))
        
    return sheet, joints_sheet, anim_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['render'])
    parser.add_argument('--rig', required=True)
    parser.add_argument('--anim', required=True)
    parser.add_argument('--frames', type=int, default=8)
    parser.add_argument('--cols', type=int, default=4)
    parser.add_argument('--size', type=int, default=512)
    parser.add_argument('--joints', action='store_true')
    parser.add_argument('--preset', default='human_balanced')
    parser.add_argument('--out', required=True)
    parser.add_argument('--meta')
    parser.add_argument('--debug', action='store_true')
    
    args = parser.parse_args()
    
    if args.command == 'render':
        rig = load_rig(args.rig)
        sheet, joints, anim = generate_spritesheet(rig, args.anim, args.frames, args.cols, args.size, args.joints, args.preset, args.debug)
        sheet.save(args.out)
        if joints: joints.save(args.out.replace('.png', '_jointmask.png'))
        if args.meta:
            with open(args.meta, 'w') as f:
                json.dump({"name": anim['name'], "preset": args.preset}, f, indent=2)
        print("✅ Render Success")

if __name__ == '__main__':
    main()
