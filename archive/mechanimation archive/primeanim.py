#!/usr/bin/env python3
"""
Mechanimation v0.2 - PrimeAnim Renderer
Renders sprite animation frames from rig + animation definitions
Generates joint masks for AI inpainting (TrixelComposer bridge)
"""

import json
import math
import argparse
from pathlib import Path
from PIL import Image, ImageDraw

# ==================== EASING FUNCTIONS ====================

def ease_in_out_cubic(t):
    """Smooth acceleration/deceleration"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

# ==================== RIG LOADER ====================

def load_rig(rig_path):
    """Load rig definition and all part images"""
    with open(rig_path) as f:
        rig_data = json.load(f)
    
    parts_dir = Path(rig_path).parent / rig_data['parts_dir']
    
    def load_part_recursive(part_name, part_def, parent_path=""):
        """Recursively load part images and build hierarchy"""
        full_path = f"{parent_path}/{part_name}" if parent_path else part_name
        
        img_path = parts_dir / part_def['image']
        img = Image.open(img_path).convert('RGBA')
        
        part = {
            'name': part_name,
            'path': full_path,
            'image': img,
            'pivot': tuple(part_def['pivot']),
            'socket': tuple(part_def['socket']) if part_def['socket'] else None,
            'children': {}
        }
        
        if 'children' in part_def:
            for child_name, child_def in part_def['children'].items():
                part['children'][child_name] = load_part_recursive(
                    child_name, child_def, full_path
                )
        
        return part
    
    root_name = list(rig_data['hierarchy'].keys())[0]
    root_def = rig_data['hierarchy'][root_name]
    
    return load_part_recursive(root_name, root_def)

# ==================== ANIMATION INTERPOLATION ====================

def interpolate_pose(keyframes, time):
    """Interpolate rotation values at given time"""
    # Find surrounding keyframes
    before_kf = None
    after_kf = None
    
    for kf in keyframes:
        if kf['time'] <= time:
            before_kf = kf
        if kf['time'] >= time and after_kf is None:
            after_kf = kf
    
    if before_kf is None:
        before_kf = keyframes[0]
    if after_kf is None:
        after_kf = keyframes[-1]
    
    # If exact match or at boundaries
    if before_kf['time'] == after_kf['time']:
        return before_kf['poses']
    
    # Interpolate
    t = (time - before_kf['time']) / (after_kf['time'] - before_kf['time'])
    t_eased = ease_in_out_cubic(t)
    
    interpolated = {}
    all_parts = set(before_kf['poses'].keys()) | set(after_kf['poses'].keys())
    
    for part in all_parts:
        before_rot = before_kf['poses'].get(part, {}).get('rotation', 0)
        after_rot = after_kf['poses'].get(part, {}).get('rotation', 0)
        
        interpolated[part] = {
            'rotation': before_rot + (after_rot - before_rot) * t_eased
        }
    
    return interpolated

# ==================== RENDERING ENGINE ====================

def render_part_recursive(part, pose, canvas, offset_x, offset_y, parent_rotation=0, joints_canvas=None):
    """Recursively render part and children with rotations"""
    
    # Get this part's rotation from pose
    part_pose = pose.get(part['name'], {})
    local_rotation = part_pose.get('rotation', 0)
    total_rotation = parent_rotation + local_rotation
    
    # Rotate image around pivot
    img = part['image']
    pivot = part['pivot']
    
    # Rotate image
    rotated = img.rotate(-total_rotation, expand=True, resample=Image.BICUBIC)
    
    # Calculate new pivot position after rotation
    angle_rad = math.radians(total_rotation)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Original pivot offset from center
    orig_cx, orig_cy = img.width / 2, img.height / 2
    pivot_offset_x = pivot[0] - orig_cx
    pivot_offset_y = pivot[1] - orig_cy
    
    # Rotated pivot offset
    new_pivot_x = pivot_offset_x * cos_a - pivot_offset_y * sin_a
    new_pivot_y = pivot_offset_x * sin_a + pivot_offset_y * cos_a
    
    # Position on canvas (accounting for expansion)
    paste_x = int(offset_x - rotated.width / 2 + new_pivot_x)
    paste_y = int(offset_y - rotated.height / 2 + new_pivot_y)
    
    # Composite onto canvas
    canvas.paste(rotated, (paste_x, paste_y), rotated)
    
    # Draw joint marker if joints canvas provided
    if joints_canvas and part['socket']:
        # Transform socket position
        socket_offset_x = part['socket'][0] - pivot[0]
        socket_offset_y = part['socket'][1] - pivot[1]
        
        rotated_socket_x = socket_offset_x * cos_a - socket_offset_y * sin_a
        rotated_socket_y = socket_offset_x * sin_a + socket_offset_y * cos_a
        
        joint_x = int(offset_x + rotated_socket_x)
        joint_y = int(offset_y + rotated_socket_y)
        
        # Draw white circle on joint mask
        draw = ImageDraw.Draw(joints_canvas)
        radius = 12
        draw.ellipse(
            [joint_x - radius, joint_y - radius, joint_x + radius, joint_y + radius],
            fill='white'
        )
    
    # Render children
    if part['socket']:
        # Transform socket position for children attachment
        socket_offset_x = part['socket'][0] - pivot[0]
        socket_offset_y = part['socket'][1] - pivot[1]
        
        child_offset_x = offset_x + socket_offset_x * cos_a - socket_offset_y * sin_a
        child_offset_y = offset_y + socket_offset_x * sin_a + socket_offset_y * cos_a
    else:
        child_offset_x, child_offset_y = offset_x, offset_y
    
    for child in part['children'].values():
        render_part_recursive(
            child, pose, canvas, child_offset_x, child_offset_y, 
            total_rotation, joints_canvas
        )

def render_frame(rig, pose, frame_size=512, draw_joints=False):
    """Render a single frame with given pose"""
    canvas = Image.new('RGBA', (frame_size, frame_size), (0, 0, 0, 0))
    joints_canvas = None
    
    if draw_joints:
        joints_canvas = Image.new('RGB', (frame_size, frame_size), 'black')
    
    # Start from center
    center_x, center_y = frame_size // 2, frame_size // 2
    
    render_part_recursive(rig, pose, canvas, center_x, center_y, joints_canvas=joints_canvas)
    
    return canvas, joints_canvas

# ==================== SPRITESHEET GENERATION ====================

def generate_spritesheet(rig, anim_path, num_frames, cols, frame_size, draw_joints):
    """Generate spritesheet with all frames"""
    
    with open(anim_path) as f:
        anim_data = json.load(f)
    
    duration = anim_data['duration']
    keyframes = anim_data['keyframes']
    
    rows = (num_frames + cols - 1) // cols
    sheet_width = cols * frame_size
    sheet_height = rows * frame_size
    
    sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    joints_sheet = None
    
    if draw_joints:
        joints_sheet = Image.new('RGB', (sheet_width, sheet_height), 'black')
    
    frames = []
    
    for i in range(num_frames):
        t = (i / (num_frames - 1)) * duration if num_frames > 1 else 0
        print(f"Rendering frame {i+1}/{num_frames} (t={t:.2f})")
        
        pose = interpolate_pose(keyframes, t)
        frame, joints_frame = render_frame(rig, pose, frame_size, draw_joints)
        
        frames.append(frame)
        
        row = i // cols
        col = i % cols
        x = col * frame_size
        y = row * frame_size
        
        sheet.paste(frame, (x, y))
        
        if joints_sheet and joints_frame:
            joints_sheet.paste(joints_frame, (x, y))
    
    return sheet, joints_sheet, anim_data

# ==================== CLI ====================

def main():
    parser = argparse.ArgumentParser(description='Mechanimation PrimeAnim Renderer')
    parser.add_argument('command', choices=['render'], help='Command to execute')
    parser.add_argument('--rig', required=True, help='Path to rig.json')
    parser.add_argument('--anim', required=True, help='Path to animation.json')
    parser.add_argument('--frames', type=int, default=8, help='Number of frames')
    parser.add_argument('--cols', type=int, default=4, help='Columns in spritesheet')
    parser.add_argument('--size', type=int, default=512, help='Frame size (pixels)')
    parser.add_argument('--joints', action='store_true', help='Generate joint mask')
    parser.add_argument('--out', required=True, help='Output spritesheet path')
    parser.add_argument('--meta', help='Output metadata JSON path')
    
    args = parser.parse_args()
    
    if args.command == 'render':
        # Load rig
        rig = load_rig(args.rig)
        
        # Generate spritesheet
        sheet, joints_sheet, anim_data = generate_spritesheet(
            rig, args.anim, args.frames, args.cols, args.size, args.joints
        )
        
        # Save spritesheet
        sheet.save(args.out)
        print(f"✅ Spritesheet saved to {args.out}")
        
        # Save joint mask if requested
        if joints_sheet:
            joints_path = args.out.replace('.png', '_jointmask.png')
            joints_sheet.save(joints_path)
            print(f"🎭 Joint mask saved to {joints_path}")
        
        # Save metadata
        if args.meta:
            meta = {
                'name': anim_data['name'],
                'frames': args.frames,
                'cols': args.cols,
                'frame_size': args.size,
                'fps': anim_data.get('fps', 12)
            }
            with open(args.meta, 'w') as f:
                json.dump(meta, f, indent=2)
            print(f"📄 Metadata saved to {args.meta}")

if __name__ == '__main__':
    main()
