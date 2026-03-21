#!/usr/bin/env python3
"""
Mechanimation v0.5.2 - PROJECTIVE Biomechanical Constraints
Implements 'Foreshortened Shin' logic to prevent horizontal foot drift.
"""

import math
from pathlib import Path

class BiomechanicalConstraintsFixed:
    def __init__(self, config=None, rig_data=None):
        self.config = config or {}
        
        # Fallback to hardcoded values
        self.thigh_len, self.shin_len = 73.0, 48.0
        
        # ✅ AUTO-CALCULATE from rig if available
        if rig_data:
            t_len = self._get_bone_length(rig_data, 'left_thigh')
            s_len = self._get_bone_length(rig_data, 'left_shin')
            if t_len: self.thigh_len = t_len
            if s_len: self.shin_len = s_len
        
        # Damping & Tuning
        self.damping = {'hip': 0.7, 'knee': 0.6, 'shoulder': 0.6, 'elbow': 0.4}
        self.knee_multipliers = {'stance': 0.15, 'lift': 0.4, 'swing': 0.7}
        
        # Base locomotion params
        self.step_height = self.config.get('step_height', 28.0)
        # ✅ FIXED: Reduced from 105 to match actual leg length
        self.ground_y = self.config.get('ground_y', 85.0)
        self.pelvis_bob = self.config.get('pelvis_bob', 4.0)
        self.hip_sep = 9.0
        # ✅ FIXED: Configurable foot travel
        self.foot_travel = self.config.get('foot_travel', 12.0)

        self.last_stance = {'left': False, 'right': False}

    def _get_bone_length(self, rig_data, part_name):
        """Extract bone length with proper resource cleanup"""
        try:
            hierarchy = rig_data.get('hierarchy', {})
            # Navigate to the part
            for name, defn in self._flatten_hierarchy(hierarchy).items():
                if name == part_name:
                    # Get image path and read dimensions
                    parts_dir = Path(rig_data.get('parts_dir', '.'))
                    img_path = parts_dir / defn['image']
                    if img_path.exists():
                        from PIL import Image
                        with Image.open(img_path) as img:  # ✅ Context manager
                            return float(max(img.width, img.height))
        except Exception as e:
            print(f"⚠️ Could not calculate {part_name} length: {e}")
        return None

    def _flatten_hierarchy(self, hierarchy, parent=""):
        """Flatten nested hierarchy into dict"""
        result = {}
        for name, defn in hierarchy.items():
            path = f"{parent}/{name}" if parent else name
            result[path] = defn
            if 'children' in defn:
                result.update(self._flatten_hierarchy(defn['children'], path))
        return result

    def solve_ik(self, tx, ty):
        dist = math.sqrt(tx*tx + ty*ty)
        max_reach = (self.thigh_len + self.shin_len) * 0.98
        if dist > max_reach:
            tx *= max_reach/dist
            ty *= max_reach/dist
            dist = max_reach
        
        cos_knee = (self.thigh_len**2 + self.shin_len**2 - dist**2) / (2 * self.thigh_len * self.shin_len)
        knee_rad = math.acos(max(-1, min(1, cos_knee)))
        base_rad = math.atan2(tx, ty)
        cos_hip = (self.thigh_len**2 + dist**2 - self.shin_len**2) / (2 * self.thigh_len * dist)
        hip_rad = math.acos(max(-1, min(1, cos_hip)))
        
        return math.degrees(base_rad - hip_rad), 180 - math.degrees(knee_rad)

    def apply_biomechanical_constraints(self, pose, t, duration, debug=False):
        p = (t / duration) % 1.0
        rad_phase = p * 2 * math.pi
        
        # 1. Pelvis
        bob = math.sin(rad_phase * 2) * self.pelvis_bob
        pose['torso'] = {'translate_y': -abs(bob)}
        pose['hip'] = {'translate_x': 0}

        # ✅ CRITICAL FIX: Compute hip Y for foot-ground contact
        hip_y = pose.get('torso', {}).get('translate_y', 0)
        relative_ground = self.ground_y - hip_y

        # 2. Leg Patterns
        for side, offset in [('left', 0.0), ('right', 0.5)]:
            s_phase = (p + offset) % 1.0
            is_stance = s_phase < 0.5
            
            # Phase Labels
            if is_stance:
                phase_label = 'STANCE'
            elif s_phase < 0.7:
                phase_label = 'LIFT'
            else:
                phase_label = 'PASS'
            
            # Intent Foreshortening
            intent_rot = pose.get(f'{side}_thigh', {}).get('rotation', 0)
            intent_lift = abs(intent_rot) * 0.4

            # Lateral foot separation (prevent crossing)
            foot_offset = self.hip_sep / 2

            # Define target for BOTH stance and swing
            if is_stance:
                target_x = foot_offset * (1 if side == 'right' else -1)
                target_y = relative_ground  # ✅ FIXED: Accounts for pelvis bob
                knee_char = self.knee_multipliers['stance']
                foot_tilt = 0
            else:
                t_swing = (s_phase - 0.5) / 0.5
                base_x = foot_offset * (1 if side == 'right' else -1)
                # Horizontal arc during swing (forward then back)
                target_x = base_x + math.sin(t_swing * math.pi) * self.foot_travel * (1 if side == 'right' else -1)
                target_y = relative_ground - (math.sin(t_swing * math.pi) * self.step_height + intent_lift)  # ✅ FIXED
                knee_char = self.knee_multipliers['swing'] if phase_label == 'PASS' else self.knee_multipliers['lift']
                foot_tilt = math.sin(t_swing * math.pi) * 2.5
            
            # Solve IK AFTER target_x/target_y are defined
            thigh_rot, knee_flex = self.solve_ik(target_x, target_y)
            
            # Apply the IK solution
            final_knee = abs(knee_flex) * knee_char
            
            pose[f'{side}_thigh'] = {'rotation': thigh_rot}
            pose[f'{side}_shin'] = {'rotation': final_knee}
            pose[f'{side}_foot'] = {'rotation': -(thigh_rot + final_knee) + foot_tilt}
            
            # ✅ FIXED: Use thigh_rot instead of undefined outward_stabilizer
            if debug:
                print(f"| {side:5s} | φ={s_phase:.2f} | {phase_label:6s} | "
                      f"THIGH={thigh_rot:5.1f}° | KNEE={final_knee:5.1f}° | "
                      f"POS=({target_x:5.1f}, {target_y:5.1f}) |")
        
        # 3. Arms
        arm_p = (p + 0.5) % 1.0
        shoulder_out = math.sin(arm_p * 2 * math.pi) * 8.0
        for side in ['left', 'right']:
            p_mult = 1 if side == 'left' else -1
            curr_out = shoulder_out * p_mult
            elbow_bend = -abs(curr_out) * 0.4
            pose[f'{side}_arm'] = {'rotation': curr_out * self.damping['shoulder']}
            pose[f'{side}_wrist'] = {'rotation': elbow_bend * self.damping['elbow']}
            pose[f'{side}_hand'] = {'rotation': -elbow_bend * 0.3}

        return pose

# Unified Preset
BIOMECH_PRESETS = {
    "human_balanced": {
        "step_height": 28.0, "ground_y": 85.0, "pelvis_bob": 4.0, "foot_travel": 12.0
    }
}

def get_preset(name):
    return BIOMECH_PRESETS.get(name, BIOMECH_PRESETS["human_balanced"])
