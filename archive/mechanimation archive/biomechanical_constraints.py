#!/usr/bin/env python3
"""
Mechanimation v0.4.1 - Biomechanical Constraint System
With 'Controlled Error' (Intent Bias, Asymmetry, and Desync)
"""

import math
from enum import Enum

class JointType(Enum):
    BALL_SOCKET = 1
    HINGE = 2
    SLIDER = 3
    PIVOT = 4
    FIXED = 5

class BiomechanicalConstraints:
    def __init__(self, config=None):
        self.config = config or {}
        
        self.limits = self.config.get('limits', {
            'knee_min': 5,
            'knee_max': 160,
            'hip_flexion': 45,
            'hip_extension': -45
        })
        
        # CHANGE 3: Reduction of damping for pixel-art clarity
        self.damping = {
            'hip': 0.7,
            'knee': 0.6,
            'ankle': 0.5,
            'shoulder': 0.6,
            'elbow': 0.4,
            'spine': 0.65
        }
        
        self.thigh_len = 50.0
        self.shin_len = 40.0
        
        self.stride_width = self.config.get('stride_width', 70.0)
        self.step_height = self.config.get('step_height', 20.0)
        self.ground_y = self.config.get('ground_y', 95.0)
        self.pelvis_bob = self.config.get('pelvis_bob', 6.0)

    def solve_ik(self, tx, ty):
        dist_sq = tx*tx + ty*ty
        dist = math.sqrt(dist_sq)
        max_reach = (self.thigh_len + self.shin_len) * 0.98
        if dist > max_reach:
            scale = max_reach / dist
            tx *= scale; ty *= scale
            dist = max_reach; dist_sq = dist*dist
        cos_knee = (self.thigh_len**2 + self.shin_len**2 - dist_sq) / (2 * self.thigh_len * self.shin_len)
        cos_knee = max(-1, min(1, cos_knee))
        knee_angle_rad = math.acos(cos_knee)
        base_angle_rad = math.atan2(tx, ty)
        cos_hip = (self.thigh_len**2 + dist_sq - self.shin_len**2) / (2 * self.thigh_len * dist)
        cos_hip = max(-1, min(1, cos_hip))
        hip_int_rad = math.acos(cos_hip)
        thigh_deg = math.degrees(base_angle_rad - hip_int_rad)
        knee_deg = 180 - math.degrees(knee_angle_rad)
        knee_deg = max(self.limits.get('knee_min', 5), min(self.limits.get('knee_max', 160), knee_deg))
        return thigh_deg, knee_deg

    def apply_biomechanical_constraints(self, pose, t, duration, ground_height=0, debug=False):
        p = (t / duration) % 1.0
        
        # CHANGE 2: Breaking symmetry with Pelvis Noise
        bob = math.sin(p * 2 * math.pi * 2) * self.pelvis_bob
        bob += math.sin(p * 3 * math.pi + 0.3) * 0.8
        
        sway = math.sin(p * 2 * math.pi) * 3.0
        sway += math.sin(p * 4 * math.pi) * 1.2
        
        pose['torso'] = pose.get('torso', {})
        pose['torso']['translate_y'] = -abs(bob)
        pose['hip'] = pose.get('hip', {})
        pose['hip']['translate_x'] = sway * self.damping['hip']

        # 2. LEG IK (With Intent Bias and Phase-Aware Knees)
        for side, offset in [('left', 0.0), ('right', 0.5)]:
            phase = (p + offset) % 1.0
            
            if phase < 0.5:
                t_stance = phase / 0.5
                target_x = self.stride_width * (0.5 - t_stance)
                target_y = self.ground_y
                foot_rot = 0
                knee_scale = 1.0
            else:
                t_swing = (phase - 0.5) / 0.5
                target_x = -self.stride_width * 0.5 + math.sin(t_swing * math.pi) * self.stride_width
                target_y = self.ground_y - math.sin(t_swing * math.pi) * self.step_height
                foot_rot = math.sin(t_swing * math.pi) * 20
                # CHANGE 4: Phase-Aware Knee flex (variable depth)
                knee_scale = 0.82 + (math.sin(t_swing * math.pi) * 1.2)

            # Solve IK base solution
            thigh_rot, knee_flex = self.solve_ik(target_x, target_y)
            
            # CHANGE 1: Intent Bias (Let keyframe survival happen)
            intent_rot = pose.get(f'{side}_thigh', {}).get('rotation', 0)
            thigh_rot = (thigh_rot * 0.6) + (intent_rot * 0.4)
            
            # Apply knee characterization
            knee_flex *= knee_scale
            knee_flex = max(self.limits['knee_min'], min(self.limits['knee_max'], knee_flex))
            
            pose[f'{side}_thigh'] = {'rotation': thigh_rot}
            pose[f'{side}_shin'] = {'rotation': knee_flex}
            pose[f'{side}_foot'] = {'rotation': -(thigh_rot + knee_flex) + foot_rot}

        # 3. ARM PENDULUM (With Side-Specific Lag)
        arm_phase = (p + 0.5) % 1.0
        shoulder_swing = math.sin(arm_phase * 2 * math.pi) * 25.0
        
        # CHANGE 5: Side-Specific Arm Lag
        elbow_lags = {'left': 0.9, 'right': 1.1}
        
        for side in ['left', 'right']:
            p_mult = 1 if side == 'left' else -1
            curr_swing = shoulder_swing * p_mult
            # Elbow follows shoulder
            elbow_bend = -abs(curr_swing) * 0.4 * elbow_lags[side]
            
            pose[f'{side}_arm'] = {'rotation': curr_swing * self.damping['shoulder']}
            pose[f'{side}_wrist'] = {'rotation': elbow_bend}
            pose[f'{side}_hand'] = {'rotation': -elbow_bend * self.damping['ankle']}

        return pose

BIOMECH_PRESETS = {
    'human_walk': {
        'stride_width': 70.0,
        'step_height': 20.0,
        'ground_y': 95.0,
        'pelvis_bob': 5.0,
        'limits': {'knee_min': 5, 'knee_max': 160}
    },
    'heavy_commuter': {
        'stride_width': 40.0,
        'step_height': 10.0,
        'ground_y': 105.0,
        'pelvis_bob': 10.0,
        'limits': {'knee_min': 10, 'knee_max': 90}
    },
    'agile_scout': {
        'stride_width': 90.0,
        'step_height': 35.0,
        'ground_y': 85.0,
        'pelvis_bob': 2.0,
        'limits': {'knee_min': 5, 'knee_max': 170}
    }
}
