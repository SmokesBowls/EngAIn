#!/usr/bin/env python3
"""
Mechanimation v0.5.2 - PROJECTIVE Biomechanical Constraints
Implements 'Foreshortened Shin' logic to prevent horizontal foot drift.
"""

import math

class BiomechanicalConstraintsFixed:
    def __init__(self, config=None):
        self.config = config or {}
        self.thigh_len, self.shin_len = 50.0, 40.0
        
        # Damping & Tuning
        self.damping = {'hip': 0.7, 'knee': 0.6, 'shoulder': 0.6, 'elbow': 0.4}
        self.knee_multipliers = {'stance': 0.15, 'lift': 0.4, 'swing': 0.7}
        
        # Base locomotion params
        self.step_height = self.config.get('step_height', 28.0)
        self.ground_y = self.config.get('ground_y', 105.0)
        self.pelvis_bob = self.config.get('pelvis_bob', 4.0)
        self.hip_sep = 9.0  # Narrowed from 12 to match Canon.png
        
        self.last_stance = {'left': False, 'right': False}

    def solve_ik(self, tx, ty):
        dist = math.sqrt(tx*tx + ty*ty)
        max_reach = (self.thigh_len + self.shin_len) * 0.98
        if dist > max_reach:
            tx *= max_reach/dist; ty *= max_reach/dist; dist = max_reach
        
        cos_knee = (self.thigh_len**2 + self.shin_len**2 - dist**2) / (2 * self.thigh_len * self.shin_len)
        knee_rad = math.acos(max(-1, min(1, cos_knee)))
        base_rad = math.atan2(tx, ty)
        cos_hip = (self.thigh_len**2 + dist**2 - self.shin_len**2) / (2 * self.thigh_len * dist)
        hip_rad = math.acos(max(-1, min(1, cos_hip)))
        
        return math.degrees(base_rad - hip_rad), 180 - math.degrees(knee_rad)

    def apply_biomechanical_constraints(self, pose, t, duration, ground_height=0, debug=False):
        p = (t / duration) % 1.0
        rad_phase = p * 2 * math.pi
        
        # 1. Pelvis
        bob = math.sin(rad_phase * 2) * self.pelvis_bob
        pose['torso'] = {'translate_y': -abs(bob)}
        pose['hip'] = {'translate_x': 0}

        # 2. Leg Patterns (PROJECTIVE FIX)
        for side, offset in [('left', 0.0), ('right', 0.5)]:
            s_phase = (p + offset) % 1.0
            is_stance = s_phase < 0.5
            
            # Phase Labels
            if is_stance: phase_label = 'STANCE'
            elif s_phase < 0.7: phase_label = 'LIFT'
            else: phase_label = 'PASS'
            
            # Intent Foreshortening
            intent_rot = pose.get(f'{side}_thigh', {}).get('rotation', 0)
            intent_lift = abs(intent_rot) * 0.4
            
            # Target X is hard-locked to prevent crossing
            target_x = 0
            if is_stance:
                target_y = self.ground_y
                knee_char = self.knee_multipliers['stance']
                foot_tilt = 0
            else:
                t_swing = (s_phase - 0.5) / 0.5
                target_y = self.ground_y - (math.sin(t_swing * math.pi) * self.step_height + intent_lift)
                knee_char = self.knee_multipliers['swing'] if phase_label == 'PASS' else self.knee_multipliers['lift']
                foot_tilt = math.sin(t_swing * math.pi) * 2.5

            # Solve IK - this gives us the minimal rotation needed
            thigh_rot, knee_flex = self.solve_ik(target_x, target_y)
            
            # 🔥 CRITICAL FIX: Use the IK solution directly
            # No more outward_stabilizer override - let the solver keep feet centered
            final_knee = abs(knee_flex) * knee_char
            
            # Apply the natural IK solution
            pose[f'{side}_thigh'] = {'rotation': thigh_rot}
            pose[f'{side}_shin'] = {'rotation': final_knee}
            pose[f'{side}_foot'] = {'rotation': -(thigh_rot + final_knee) + foot_tilt}
            
            if debug:
                print(f"| {side:5s} | φ={s_phase:.2f} | T_ROT={outward_stabilizer:4.1f} | K_FLEX={final_knee:4.1f} |")

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
        "step_height": 28.0, "ground_y": 105.0, "pelvis_bob": 4.0
    }
}

def get_preset(name):
    return BIOMECH_PRESETS.get(name, BIOMECH_PRESETS["human_balanced"])
