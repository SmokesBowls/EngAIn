#!/usr/bin/env python3
import math

class WalkConstraints:
    """
    Mechanimation v0.4 - Biomechanical IK Solver
    Enforces ground-locking and solves limb angles from the foot up.
    """
    def __init__(self, config=None):
        self.config = config or {}
        # Mechanical constants
        self.thigh_len = 50.0  # From rig: 58-8
        self.shin_len = 40.0   # From rig: 45-5
        
        # Tuning
        self.stride_width = self.config.get('stride_width', 60.0)
        self.step_height = self.config.get('step_height', 25.0)
        self.ground_y = self.config.get('ground_y', 110.0) # Relative to Hip
        self.pelvis_bob = self.config.get('pelvis_bob', 6.0)

    def solve_ik(self, tx, ty):
        """Standard 2D IK with Knee Plane Constraint"""
        dist_sq = tx*tx + ty*ty
        dist = math.sqrt(dist_sq)
        
        # Clamp distance to max reach
        max_reach = (self.thigh_len + self.shin_len) * 0.98
        if dist > max_reach:
            scale = max_reach / dist
            tx *= scale
            ty *= scale
            dist = max_reach
            dist_sq = dist*dist

        # Law of Cosines
        cos_knee = (self.thigh_len**2 + self.shin_len**2 - dist_sq) / (2 * self.thigh_len * self.shin_len)
        cos_knee = max(-1, min(1, cos_knee))
        knee_angle_rad = math.acos(cos_knee)
        
        base_angle_rad = math.atan2(tx, ty)
        
        cos_hip = (self.thigh_len**2 + dist_sq - self.shin_len**2) / (2 * self.thigh_len * dist)
        cos_hip = max(-1, min(1, cos_hip))
        hip_int_rad = math.acos(cos_hip)
        
        # CONSTRAINT: Knee Plane
        # We always want the knee to bend "right" (forward) in a side view
        # This is enforced by the sign of the internal hip angle
        thigh_deg = math.degrees(base_angle_rad - hip_int_rad)
        knee_deg = 180 - math.degrees(knee_angle_rad)
        
        # ANGLE CLAMP: Prevent hyper-extension or total collapse
        knee_deg = max(5, min(160, knee_deg))
        
        return thigh_deg, knee_deg

    def get_phase_name(self, phase):
        """Map phase 0.0-1.0 to human gait terminology"""
        if phase < 0.125: return "CONTACT"
        if phase < 0.25:  return "LOAD"
        if phase < 0.375: return "MID-STANCE"
        if phase < 0.5:   return "PUSH/OFF"
        if phase < 0.625: return "LIFT"
        if phase < 0.75:  return "SWING"
        if phase < 0.875: return "REACH"
        return "DECEL"

    def apply_walk_constraints(self, pose, t, duration, debug=False):
        p = (t / duration) % 1.0
        
        if debug:
            print(f"\n🚶 GAIT ANALYSIS: p={p:.2f} ({self.get_phase_name(p)})")
        
        # 1. ROOT MOTION
        # Double-bob (one peak per leg)
        bob = math.sin(p * 2 * math.pi * 2) * self.pelvis_bob
        pose['torso'] = {'translate_y': -abs(bob)}
        
        # 2. FOOT TARGETS
        for side, offset in [('left', 0.0), ('right', 0.5)]:
            phase = (p + offset) % 1.0
            phase_name = self.get_phase_name(phase)
            
            # Stance
            if phase < 0.5:
                t_stance = phase / 0.5
                target_x = self.stride_width * (0.5 - t_stance)
                target_y = self.ground_y
                foot_rot = 0
            # Swing
            else:
                t_swing = (phase - 0.5) / 0.5
                target_x = -self.stride_width * 0.5 + math.sin(t_swing * math.pi) * self.stride_width
                target_y = self.ground_y - math.sin(t_swing * math.pi) * self.step_height
                foot_rot = math.sin(t_swing * math.pi) * 20

            # 3. SOLVE IK
            thigh_rot, knee_flex = self.solve_ik(target_x, target_y)
            
            if debug and side == 'left':
                print(f"  L Leg [{phase_name}]: Target({target_x:.1f}, {target_y:.1f}) -> Thigh:{thigh_rot:.1f} Knee:{knee_flex:.1f}")

            pose[f'{side}_thigh'] = {'rotation': thigh_rot}
            pose[f'{side}_shin'] = {'rotation': knee_flex}
            pose[f'{side}_foot'] = {'rotation': -(thigh_rot + knee_flex) + foot_rot}

        # 4. ARMS
        arm_swing = math.sin(p * 2 * math.pi) * 20
        pose['left_arm'] = {'rotation': arm_swing}
        pose['right_arm'] = {'rotation': -arm_swing}
        
        return pose

def get_preset(name):
    # Standard human proportions
    return {
        'stride_width': 70.0,
        'step_height': 20.0,
        'ground_y': 95.0,
        'pelvis_bob': 5.0
    }
