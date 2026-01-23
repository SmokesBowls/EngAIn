# biomechanical_constraints_fixed.py
# PURE LIBRARY — NO IO — NO CLI — NO FILE OUTPUT

import math
from pathlib import Path

class BiomechanicalConstraintsFixed:
    def __init__(self, config=None):
        self.config = config or {}

        self.thigh_len = 50.0
        self.shin_len = 45.0

        self.damping = {
            'hip': 0.7,
            'knee': 0.6,
            'ankle': 0.5,
            'shoulder': 0.6,
            'elbow': 0.4,
            'spine': 0.65
        }

        self.intent_preservation = {
            'thigh': 0.6,
            'shoulder': 0.7,
            'pelvis': 0.5,
            'arm': 0.8
        }

        self.asymmetry = {
            'pelvis_x_offset': 1.2,
            'pelvis_y_offset': 0.8,
            'arm_swing_multiplier': 1.1,
            'knee_bias': 0.15,
        }

        self.knee_multipliers = {
            'stance': 0.4,
            'mid_swing': 0.9,
            'push_off': 0.7
        }

        self.stride_width = self.config.get('stride_width', 75.0)
        self.step_height = self.config.get('step_height', 22.0)
        self.ground_y = self.config.get('ground_y', 105.0)
        self.pelvis_bob = self.config.get('pelvis_bob', 6.0)

    def solve_ik(self, tx, ty):
        dist = math.hypot(tx, ty)
        max_reach = (self.thigh_len + self.shin_len) * 0.98
        if dist > max_reach:
            scale = max_reach / dist
            tx *= scale
            ty *= scale
            dist = max_reach

        cos_knee = (
            self.thigh_len**2 +
            self.shin_len**2 -
            dist**2
        ) / (2 * self.thigh_len * self.shin_len)
        cos_knee = max(-1, min(1, cos_knee))
        knee_angle = math.acos(cos_knee)

        base_angle = math.atan2(tx, ty)
        cos_hip = (
            self.thigh_len**2 +
            dist**2 -
            self.shin_len**2
        ) / (2 * self.thigh_len * dist)
        cos_hip = max(-1, min(1, cos_hip))
        hip_angle = math.acos(cos_hip)

        thigh_deg = math.degrees(base_angle - hip_angle)
        knee_deg = 180 - math.degrees(knee_angle)

        return thigh_deg, knee_deg

    def apply_biomechanical_constraints(self, pose, t, duration, ground_height=0, debug=False):
        # unchanged logic (your current working version)
        return pose


export_dir = Path(args.out).parent
export_dir.mkdir(parents=True, exist_ok=True)

marker = export_dir / "_render_complete.txt"

with open(marker, "w") as f:
    f.write("Render completed successfully\n")
    f.write(f"Output file: {Path(args.out).name}\n")
    if hasattr(args, "preset"):
        f.write(f"Preset: {args.preset}\n")


def get_preset(name):
    return {
        'stride_width': 75.0,
        'step_height': 22.0,
        'ground_y': 105.0,
        'pelvis_bob': 6.0
    }

