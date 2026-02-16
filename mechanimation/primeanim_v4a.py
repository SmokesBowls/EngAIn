#!/usr/bin/env python3
"""
Mechanimation v0.4.5 - Biomechanical Animation System
Main Renderer with Unified Preset Registry.
"""

import json
import math
import argparse
import sys
from pathlib import Path
from PIL import Image

# Import unified biomechanical layer
try:
    from biomechanical_constraints_fixed import BiomechanicalConstraintsFixed, get_preset, BIOMECH_PRESETS
except ImportError:
    print("⚠️ Error: biomechanical_constraints_fixed.py not found.")
    sys.exit(1)

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
    t_eased = 4*t*t*t if t < 0.5 else 1-pow(-2*t+2, 3)/2
    
    res = {}
    parts = set(before['poses'].keys()) | set(after['poses'].keys())
    for p in parts:
        b = before['poses'].get(p, {}).get('rotation', 0)
        a = after['poses'].get(p, {}).get('rotation', 0)
        res[p] = {'rotation': b + (a-b)*t_eased}
    return res

def collect_parts_with_transforms(part, pose, wx, wy, prot=0, parts_list=None):
    """Recursively collect all parts with their world transforms"""
    if parts_list is None:
        parts_list = []
    
    p_pose = pose.get(part['name'], {})
    lrot = p_pose.get('rotation', 0)
    tx, ty = p_pose.get('translate_x', 0), p_pose.get('translate_y', 0)
    trot = prot + lrot
    wx += tx; wy += ty
    
    # Store this part's info
    parts_list.append({
        'name': part['name'],
        'image': part['image'],
        'pivot': part['pivot'],
        'wx': wx,
        'wy': wy,
        'trot': trot
    })
    
    # Recurse into children
    piv = part['pivot']
    for cname, cpart in part['children'].items():
        if cpart.get('attach'):
            ax, ay = cpart['attach']
            sdx, sdy = ax - piv[0], ay - piv[1]
            rad = math.radians(trot)
            cos_a, sin_a = math.cos(rad), math.sin(rad)
            rsdx = sdx * cos_a - sdy * sin_a
            rsdy = sdx * sin_a + sdy * cos_a
            collect_parts_with_transforms(cpart, pose, wx + rsdx, wy + rsdy, trot, parts_list)
        else:
            collect_parts_with_transforms(cpart, pose, wx, wy, trot, parts_list)
    
    return parts_list

def render_part_at_position(part_info, canvas):
    """Render a single part at its world position"""
    img = part_info['image']
    if not img:
        return
    
    piv = part_info['pivot']
    wx, wy, trot = part_info['wx'], part_info['wy'], part_info['trot']
    
    rot_img = img.rotate(-trot, expand=True, resample=Image.BICUBIC)
    rad = math.radians(trot)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    cx, cy = rot_img.width / 2, rot_img.height / 2
    pdx, pdy = piv[0] - img.width / 2, piv[1] - img.height / 2
    rpdx = pdx * cos_a - pdy * sin_a
    rpdy = pdx * sin_a + pdy * cos_a
    canvas.paste(rot_img, (int(wx-cx-rpdx), int(wy-cy-rpdy)), rot_img)

def render_with_layers(rig, pose, canvas, wx, wy):
    """Render character with explicit z-order layers"""
    # Collect all parts with their transforms
    all_parts = collect_parts_with_transforms(rig, pose, wx, wy)
    
    # Define layer groups
    LAYER_1 = {'torso', 'left_wrist', 'right_wrist', 'left_foot', 'right_foot'}
    LAYER_2 = {'head', 'left_arm', 'right_arm', 'left_hand', 'right_hand', 'hip', 'left_shin', 'right_shin'}
    LAYER_3 = {'left_thigh', 'right_thigh'}
    
    # Render in REVERSE order (Layer 3 = back, Layer 1 = front)
    for part in all_parts:
        if part['name'] in LAYER_3:
            render_part_at_position(part, canvas)
    
    for part in all_parts:
        if part['name'] in LAYER_2:
            render_part_at_position(part, canvas)
    
    for part in all_parts:
        if part['name'] in LAYER_1:
            render_part_at_position(part, canvas)

def main():
    parser = argparse.ArgumentParser(description="Mechanimation v0.4.5 - Biomechanical Renderer")
    parser.add_argument('--rig', required=True, help="Path to rig JSON")
    parser.add_argument('--anim', required=True, help="Path to animation JSON")
    parser.add_argument('--frames', type=int, default=12, help="Number of frames")
    parser.add_argument('--cols', type=int, default=4, help="Columns in spritesheet")
    parser.add_argument('--size', type=int, default=512, help="Frame size")
    parser.add_argument('--preset', choices=BIOMECH_PRESETS.keys(), default="human_balanced", help="Locomotion preset")
    parser.add_argument('--out', required=True, help="Output spritesheet path")
    parser.add_argument('--debug', action='store_true', help="Output invariant truth lines")
    
    args = parser.parse_args()
    
    rig = load_rig(args.rig)
    anim = json.load(open(args.anim))
    dur, kfs = anim['duration'], anim['keyframes']
    
    # Initialize constraints with unified preset
    config = get_preset(args.preset)
    constraints = BiomechanicalConstraintsFixed(config)
    
    rows = (args.frames + args.cols - 1) // args.cols
    sheet = Image.new('RGBA', (args.cols * args.size, rows * args.size), (0, 0, 0, 0))
    
    print(f"🎬 Rendering {args.frames} frames using '{args.preset}' preset...")
    
    for i in range(args.frames):
        t = (i / (args.frames - 1)) * dur if args.frames > 1 else 0
        pose = interpolate_pose(kfs, t)
        pose = constraints.apply_biomechanical_constraints(pose, t, dur, debug=args.debug)
        
        frame = Image.new('RGBA', (args.size, args.size), (0, 0, 0, 0))
        render_with_layers(rig, pose, frame, args.size // 2, args.size // 2)
        sheet.paste(frame, ((i % args.cols) * args.size, (i // args.cols) * args.size))
    
    sheet.save(args.out)
    print(f"✅ Success: {args.out}")

if __name__ == '__main__':
    main()
